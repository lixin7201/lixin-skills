from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Protocol

from .collector import SnapshotOptions, collect_snapshot
from .config import PipelineConfig
from .openclaw import AgentError
from .prompts import draft_prompt, selection_prompt
from .publish import PublishError, publish_drafts
from .safety import validate_draft
from .storage import atomic_write_json, read_json


class PipelineError(RuntimeError):
    pass


class JsonAgent(Protocol):
    def run_json(self, prompt: str, *, session_id: str) -> dict[str, Any]: ...


def run_day(
    config: PipelineConfig,
    agent: JsonAgent,
    *,
    business_date: date | None = None,
    now: datetime | None = None,
    publish: bool = False,
    publish_limit: int | None = None,
    selection_limit: int | None = None,
) -> dict[str, Any]:
    if publish and not config.publish_enabled:
        raise PipelineError("publisher.enabled must be true before --publish is allowed")
    current = now or datetime.now(UTC)
    effective_selection_limit = selection_limit or config.selection_limit
    day = business_date or current.date()
    day_dir = config.data_dir / day.isoformat()
    snapshot_path = day_dir / "hotspots.json"
    selected_path = day_dir / "selected.json"
    drafts_path = day_dir / "drafts.json"
    publish_path = day_dir / "publish-results.json"
    report_path = day_dir / "run-report.json"

    snapshot = (
        read_json(snapshot_path)
        if snapshot_path.exists()
        else collect_snapshot(
            config.source_db,
            snapshot_path,
            SnapshotOptions(
                lookback_hours=config.lookback_hours,
                min_body_chars=config.min_body_chars,
                max_items=config.snapshot_limit,
            ),
            now=current,
        )
    )
    if not config.profiles:
        raise PipelineError("at least one content profile is required")

    if selected_path.exists():
        selected_payload = read_json(selected_path)
    elif snapshot.get("items"):
        try:
            raw_selection = agent.run_json(
                selection_prompt(snapshot, config.profiles, effective_selection_limit),
                session_id=f"dayibin-select-{day:%Y%m%d}",
            )
            selected_payload = _validate_selection(
                raw_selection, snapshot, config.profiles, effective_selection_limit
            )
            atomic_write_json(selected_path, selected_payload)
        except (AgentError, PipelineError) as error:
            atomic_write_json(
                report_path,
                _failure_report(day, current, "selection", error, snapshot),
            )
            raise
    else:
        selected_payload = {"schema_version": 1, "selected": []}
        atomic_write_json(selected_path, selected_payload)

    if drafts_path.exists():
        drafts_payload = read_json(drafts_path)
    else:
        try:
            drafts_payload = _draft_selected(
                agent, day, snapshot, selected_payload, config.profiles
            )
            atomic_write_json(drafts_path, drafts_payload)
        except (AgentError, PipelineError) as error:
            atomic_write_json(
                report_path,
                _failure_report(
                    day,
                    current,
                    "drafting",
                    error,
                    snapshot,
                    selected_count=len(selected_payload.get("selected", [])),
                ),
            )
            raise

    accepted = sum(1 for item in drafts_payload.get("drafts", []) if item.get("accepted"))
    rejected = len(drafts_payload.get("drafts", [])) - accepted
    published = 0
    if publish:
        try:
            publish_payload = publish_drafts(
                agent,
                day,
                drafts_payload,
                config.profiles,
                publish_path,
                limit=publish_limit or effective_selection_limit,
            )
        except (AgentError, PublishError) as error:
            atomic_write_json(
                report_path,
                _failure_report(
                    day,
                    current,
                    "publishing",
                    error,
                    snapshot,
                    selected_count=len(selected_payload.get("selected", [])),
                    accepted_count=accepted,
                ),
            )
            raise
        published = int(publish_payload.get("published_count", 0))
    status = (
        "published"
        if publish and published
        else "ready_to_publish"
        if accepted
        else "no_candidates"
        if not selected_payload.get("selected")
        else "blocked"
    )
    report = {
        "schema_version": 1,
        "business_date": day.isoformat(),
        "generated_at": current.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "status": status,
        "snapshot_items": int(snapshot.get("item_count", 0)),
        "selected_items": len(selected_payload.get("selected", [])),
        "selection_limit": effective_selection_limit,
        "accepted_drafts": accepted,
        "rejected_drafts": rejected,
        "publish_requested": publish,
        "published_items": published,
        "paths": {
            "hotspots": str(snapshot_path),
            "selected": str(selected_path),
            "drafts": str(drafts_path),
            "publish_results": str(publish_path) if publish else None,
        },
    }
    atomic_write_json(report_path, report)
    return report


def _failure_report(
    day: date,
    current: datetime,
    stage: str,
    error: Exception,
    snapshot: dict[str, Any],
    *,
    selected_count: int = 0,
    accepted_count: int = 0,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "business_date": day.isoformat(),
        "generated_at": current.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "status": f"{stage}_failed",
        "failed_stage": stage,
        "error": str(error)[:500],
        "snapshot_items": int(snapshot.get("item_count", 0)),
        "selected_items": selected_count,
        "accepted_drafts": accepted_count,
        "publish_requested": stage == "publishing",
    }


def _validate_selection(
    payload: dict[str, Any],
    snapshot: dict[str, Any],
    profiles: tuple[dict[str, Any], ...],
    limit: int,
) -> dict[str, Any]:
    selected = payload.get("selected")
    if not isinstance(selected, list):
        raise PipelineError("selection result must contain selected array")
    if len(selected) > limit:
        raise PipelineError("selection result exceeds configured limit")
    item_ids = {str(item["id"]) for item in snapshot.get("items", [])}
    profile_ids = {str(profile.get("id")) for profile in profiles}
    seen: set[str] = set()
    normalized = []
    for index, item in enumerate(selected):
        if not isinstance(item, dict):
            raise PipelineError(f"selected[{index}] must be an object")
        item_id = str(item.get("item_id") or "")
        profile_id = str(item.get("profile_id") or "")
        if item_id not in item_ids:
            raise PipelineError(f"selected[{index}] has unknown item_id")
        if item_id in seen:
            raise PipelineError(f"selected[{index}] duplicates item_id")
        if profile_id not in profile_ids:
            raise PipelineError(f"selected[{index}] has unknown profile_id")
        angle = str(item.get("angle") or "").strip()
        reason = str(item.get("reason") or "").strip()
        if not angle or not reason:
            raise PipelineError(f"selected[{index}] needs angle and reason")
        seen.add(item_id)
        normalized.append(
            {
                "item_id": item_id,
                "profile_id": profile_id,
                "angle": angle,
                "reason": reason,
            }
        )
    return {"schema_version": 1, "selected": normalized}


def _draft_selected(
    agent: JsonAgent,
    day: date,
    snapshot: dict[str, Any],
    selected_payload: dict[str, Any],
    profiles: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    items = {str(item["id"]): item for item in snapshot.get("items", [])}
    profile_map = {str(profile.get("id")): profile for profile in profiles}
    drafts = []
    for selection in selected_payload.get("selected", []):
        item = items[selection["item_id"]]
        profile = profile_map[selection["profile_id"]]
        response = agent.run_json(
            draft_prompt(item, selection, profile),
            session_id=f"dayibin-draft-{day:%Y%m%d}-{selection['item_id'][:12]}",
        )
        draft = response.get("draft")
        if not isinstance(draft, dict):
            raise PipelineError("draft result must contain draft object")
        reasons = validate_draft(draft, item)
        drafts.append(
            {
                **draft,
                "source_url": item["source_url"],
                "source_content_sha256": item["content_sha256"],
                "accepted": not reasons,
                "rejection_reasons": reasons,
            }
        )
    return {"schema_version": 1, "drafts": drafts}
