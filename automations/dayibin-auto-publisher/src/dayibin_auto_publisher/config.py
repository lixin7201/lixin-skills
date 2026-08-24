from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class CommenterConfig:
    enabled: bool = False
    all_profiles_each_round: bool = False
    profiles: tuple[dict[str, Any], ...] = ()
    active_start: str = "08:00"
    active_end: str = "23:00"
    interval_min_minutes: int = 90
    interval_max_minutes: int = 150
    daily_hard_cap: int = 72
    check_every_minutes: int = 15
    lookback_hours: int = 24
    fetch_max_items: int = 30
    score_threshold: int = 75
    research_enabled: bool = False
    research_max_posts: int = 3
    history_patrol_enabled: bool = False
    history_lookback_days: int = 14
    history_pages_per_round: int = 1
    history_new_posts_per_round: int = 1
    history_reply_enabled: bool = False
    history_reply_comments_per_round: int = 2
    publish_min_interval_seconds: int = 31
    batch_pause_min_seconds: int = 60
    batch_pause_max_seconds: int = 180


@dataclass(frozen=True)
class ProductionConfig:
    daily_soft_target: int = 10
    daily_regular_min: int = 8
    daily_regular_max: int = 12
    daily_hard_cap: int = 15
    max_pending_batches: int = 5
    batch_max_items: int = 3
    active_start: str = "08:20"
    active_end: str = "22:30"
    global_interval_min_minutes: int = 45
    global_interval_max_minutes: int = 120
    same_vest_interval_minutes: int = 150
    dispatcher_check_minutes: int = 5


@dataclass(frozen=True)
class HotspotPolicyConfig:
    comment_count: int = 5
    like_count: int = 20
    share_count: int = 3
    view_count: int = 1000
    snapshot_points: int = 5
    snapshot_interval_minutes: int = 30
    rising_positive_intervals: int = 3
    daily_lookback_hours: int = 72


@dataclass(frozen=True)
class PipelineConfig:
    source_db: Path
    data_dir: Path
    agent_id: str
    model: str
    openclaw_bin: str = "openclaw"
    agent_timeout_seconds: int = 900
    lookback_hours: int = 48
    min_body_chars: int = 120
    snapshot_limit: int = 200
    selection_limit: int = 5
    publish_enabled: bool = False
    profiles: tuple[dict[str, Any], ...] = ()
    production: ProductionConfig = ProductionConfig()
    hotspot_policy: HotspotPolicyConfig = HotspotPolicyConfig()
    commenter: CommenterConfig = CommenterConfig()


def load_config(path: str | Path) -> PipelineConfig:
    config_path = Path(path).expanduser().resolve()
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigError(f"config file not found: {config_path}") from error
    except json.JSONDecodeError as error:
        raise ConfigError(f"config is not valid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise ConfigError("config root must be an object")

    source_db = _required_text(payload, "source_db")
    data_dir = _required_text(payload, "data_dir")
    agent = payload.get("agent")
    if not isinstance(agent, dict):
        raise ConfigError("agent must be an object")
    agent_id = _required_text(agent, "id", prefix="agent.")
    model = _required_text(agent, "model", prefix="agent.")

    snapshot = payload.get("snapshot") or {}
    selection = payload.get("selection") or {}
    publisher = payload.get("publisher") or {}
    production = payload.get("production") or {}
    hotspot_policy = payload.get("hotspot_policy") or {}
    commenter = payload.get("commenter") or {}
    for name, value in (
        ("snapshot", snapshot),
        ("selection", selection),
        ("publisher", publisher),
        ("production", production),
        ("hotspot_policy", hotspot_policy),
        ("commenter", commenter),
    ):
        if not isinstance(value, dict):
            raise ConfigError(f"{name} must be an object")

    profiles = publisher.get("profiles") or []
    if not isinstance(profiles, list) or not all(isinstance(item, dict) for item in profiles):
        raise ConfigError("publisher.profiles must be an array of objects")

    return PipelineConfig(
        source_db=_resolve_path(config_path.parent, source_db),
        data_dir=_resolve_path(config_path.parent, data_dir),
        agent_id=agent_id,
        model=model,
        openclaw_bin=str(agent.get("executable") or "openclaw"),
        agent_timeout_seconds=_positive_int(agent, "timeout_seconds", 900),
        lookback_hours=_positive_int(snapshot, "lookback_hours", 48),
        min_body_chars=_positive_int(snapshot, "min_body_chars", 120),
        snapshot_limit=_positive_int(snapshot, "max_items", 200),
        selection_limit=_positive_int(selection, "max_items", 5),
        publish_enabled=bool(publisher.get("enabled", False)),
        profiles=tuple(profiles),
        production=_load_production(production),
        hotspot_policy=_load_hotspot_policy(hotspot_policy),
        commenter=_load_commenter(commenter),
    )


def _load_hotspot_policy(payload: dict[str, Any]) -> HotspotPolicyConfig:
    policy = HotspotPolicyConfig(
        comment_count=_positive_int(payload, "comment_count", 5),
        like_count=_positive_int(payload, "like_count", 20),
        share_count=_positive_int(payload, "share_count", 3),
        view_count=_positive_int(payload, "view_count", 1000),
        snapshot_points=_positive_int(payload, "snapshot_points", 5),
        snapshot_interval_minutes=_positive_int(payload, "snapshot_interval_minutes", 30),
        rising_positive_intervals=_positive_int(payload, "rising_positive_intervals", 3),
        daily_lookback_hours=_positive_int(payload, "daily_lookback_hours", 72),
    )
    if (
        policy.snapshot_points != 5
        or policy.snapshot_interval_minutes != 30
        or policy.rising_positive_intervals != 3
        or policy.daily_lookback_hours != 72
    ):
        raise ConfigError("hotspot_policy must use the approved first-day 5x30m/3 rising/72h contract")
    return policy


def _load_production(payload: dict[str, Any]) -> ProductionConfig:
    values = ProductionConfig(
        daily_soft_target=_positive_int(payload, "daily_soft_target", 10),
        daily_regular_min=_positive_int(payload, "daily_regular_min", 8),
        daily_regular_max=_positive_int(payload, "daily_regular_max", 12),
        daily_hard_cap=_positive_int(payload, "daily_hard_cap", 15),
        max_pending_batches=_positive_int(payload, "max_pending_batches", 5),
        batch_max_items=_positive_int(payload, "batch_max_items", 3),
        active_start=str(payload.get("active_start") or "08:20"),
        active_end=str(payload.get("active_end") or "22:30"),
        global_interval_min_minutes=_positive_int(payload, "global_interval_min_minutes", 45),
        global_interval_max_minutes=_positive_int(payload, "global_interval_max_minutes", 120),
        same_vest_interval_minutes=_positive_int(payload, "same_vest_interval_minutes", 150),
        dispatcher_check_minutes=_positive_int(payload, "dispatcher_check_minutes", 5),
    )
    if not (
        values.daily_regular_min
        <= values.daily_soft_target
        <= values.daily_regular_max
        <= values.daily_hard_cap
        <= 15
    ):
        raise ConfigError("production daily volume must satisfy min <= soft <= max <= hard <= 15")
    if values.batch_max_items > 3 or values.max_pending_batches > 5:
        raise ConfigError("production batches must stay within 3 items and 5 pending batches")
    if (values.active_start, values.active_end) != ("08:20", "22:30"):
        raise ConfigError("production active window must be 08:20-22:30")
    if not (
        45 <= values.global_interval_min_minutes
        <= values.global_interval_max_minutes
        <= 120
    ):
        raise ConfigError("production global interval must stay within 45-120 minutes")
    if values.same_vest_interval_minutes < 150 or values.dispatcher_check_minutes != 5:
        raise ConfigError("production same-vest interval must be >=150 and dispatcher check must be 5")
    return values


def _load_commenter(payload: dict[str, Any]) -> CommenterConfig:
    enabled = bool(payload.get("enabled", False))
    all_profiles_each_round = bool(payload.get("all_profiles_each_round", False))
    profiles = payload.get("profiles") or []
    schedule = payload.get("schedule") or {}
    selection = payload.get("selection") or {}
    research = payload.get("research") or {}
    history_patrol = payload.get("history_patrol") or {}
    publish = payload.get("publish") or {}
    for name, value in (
        ("commenter.profiles", profiles),
        ("commenter.schedule", schedule),
        ("commenter.selection", selection),
        ("commenter.research", research),
        ("commenter.history_patrol", history_patrol),
        ("commenter.publish", publish),
    ):
        expected = list if name.endswith("profiles") else dict
        if not isinstance(value, expected):
            raise ConfigError(f"{name} must be an {'array' if expected is list else 'object'}")
    if not all(isinstance(item, dict) for item in profiles):
        raise ConfigError("commenter.profiles must contain objects")
    expected_ids = ("observer", "helper", "counterpoint")
    profile_ids = tuple(str(item.get("id") or "") for item in profiles)
    if profiles and profile_ids != expected_ids:
        raise ConfigError("commenter.profiles must be observer, helper, counterpoint in order")
    if enabled and not profiles:
        raise ConfigError("commenter.profiles are required when commenter.enabled is true")
    vest_names = [str(item.get("vest_name") or "").strip() for item in profiles]
    if enabled and (any(not name for name in vest_names) or len(set(vest_names)) != 3):
        raise ConfigError("commenter profile vest_name values must be non-empty and unique")
    vest_ids = [str(item.get("vest_id") or "").strip() for item in profiles]
    if enabled and (any(not vest_id for vest_id in vest_ids) or len(set(vest_ids)) != 3):
        raise ConfigError("commenter profile vest_id values must be non-empty and unique")
    for profile in profiles:
        per_run_min = _nonnegative_int(profile, "per_run_min", 0)
        per_run_max = _positive_int(profile, "per_run_max", 6 if all_profiles_each_round else 9)
        allowed_max = 6 if all_profiles_each_round else 9
        if per_run_min > per_run_max or per_run_max > allowed_max:
            label = "exactly 6 or fewer" if all_profiles_each_round else "9 or fewer"
            raise ConfigError(f"commenter profile per_run_max must be {label} and >= per_run_min")
        _positive_int(profile, "rotation_weight", 1)

    active_start = str(schedule.get("active_start") or "08:00")
    active_end = str(schedule.get("active_end") or "23:00")
    if (active_start, active_end) != ("08:00", "23:00"):
        raise ConfigError("commenter active window must be 08:00-23:00")
    interval_min = _positive_int(schedule, "interval_min_minutes", 90)
    interval_max = _positive_int(schedule, "interval_max_minutes", 150)
    if interval_min < 90 or interval_max > 150 or interval_min > interval_max:
        raise ConfigError("commenter interval must stay within 90-150 minutes")
    daily_cap = _positive_int(schedule, "daily_hard_cap", 72)
    if daily_cap > 72:
        raise ConfigError("commenter daily_hard_cap must not exceed 72")
    check_every = _positive_int(schedule, "check_every_minutes", 15)
    if check_every != 15:
        raise ConfigError("commenter check_every_minutes must be 15")
    pause_min = _positive_int(publish, "batch_pause_min_seconds", 60)
    pause_max = _positive_int(publish, "batch_pause_max_seconds", 180)
    if pause_min < 60 or pause_max > 180 or pause_min > pause_max:
        raise ConfigError("commenter batch pause must stay within 60-180 seconds")
    publish_min_interval = _positive_int(
        publish, "min_comment_interval_seconds", 31
    )
    if publish_min_interval < 30 or publish_min_interval > 60:
        raise ConfigError(
            "commenter min_comment_interval_seconds must stay within 30-60 seconds"
        )
    forbidden = {"token", "password", "cookie", "api_key", "apikey", "secret"}
    if any(str(key).lower() in forbidden for key in _walk_keys(payload)):
        raise ConfigError("commenter config must not contain secrets")
    fetch_max_items = _positive_int(selection, "fetch_max_items", 30)
    if fetch_max_items > 30:
        raise ConfigError("commenter fetch_max_items must not exceed 30")
    research_max_posts = _positive_int(research, "max_posts_per_round", 3)
    if research_max_posts > 3:
        raise ConfigError("commenter research max_posts_per_round must not exceed 3")
    history_lookback_days = _positive_int(history_patrol, "lookback_days", 14)
    if history_lookback_days > 14:
        raise ConfigError("commenter history lookback_days must not exceed 14")
    history_pages = _positive_int(history_patrol, "pages_per_round", 1)
    if history_pages > 10:
        raise ConfigError("commenter history pages_per_round must not exceed 10")
    history_new_posts = _positive_int(history_patrol, "new_posts_per_round", 1)
    if history_new_posts > 18:
        raise ConfigError("commenter history new_posts_per_round must not exceed 18")
    history_replies = _positive_int(history_patrol, "reply_comments_per_round", 2)
    if history_replies > 18:
        raise ConfigError("commenter history reply_comments_per_round must not exceed 18")
    return CommenterConfig(
        enabled=enabled,
        all_profiles_each_round=all_profiles_each_round,
        profiles=tuple(profiles),
        active_start=active_start,
        active_end=active_end,
        interval_min_minutes=interval_min,
        interval_max_minutes=interval_max,
        daily_hard_cap=daily_cap,
        check_every_minutes=check_every,
        lookback_hours=_positive_int(selection, "lookback_hours", 24),
        fetch_max_items=fetch_max_items,
        score_threshold=_positive_int(selection, "score_threshold", 75),
        research_enabled=bool(research.get("enabled", False)),
        research_max_posts=research_max_posts,
        history_patrol_enabled=bool(history_patrol.get("enabled", False)),
        history_lookback_days=history_lookback_days,
        history_pages_per_round=history_pages,
        history_new_posts_per_round=history_new_posts,
        history_reply_enabled=bool(history_patrol.get("reply_enabled", False)),
        history_reply_comments_per_round=history_replies,
        publish_min_interval_seconds=publish_min_interval,
        batch_pause_min_seconds=pause_min,
        batch_pause_max_seconds=pause_max,
    )


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _required_text(payload: dict[str, Any], key: str, *, prefix: str = "") -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{prefix}{key} is required")
    return value.strip()


def _positive_int(payload: dict[str, Any], key: str, default: int) -> int:
    value = payload.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ConfigError(f"{key} must be a positive integer")
    return value


def _nonnegative_int(payload: dict[str, Any], key: str, default: int) -> int:
    value = payload.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ConfigError(f"{key} must be a non-negative integer")
    return value


def _resolve_path(base: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path).resolve()
