from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
import fcntl
import hashlib
import json
from pathlib import Path
import random
import re
from typing import Any, Callable
from zoneinfo import ZoneInfo

from .storage import atomic_write_json, atomic_write_text, read_json


SHANGHAI = ZoneInfo("Asia/Shanghai")
BATCH_ID_PATTERN = re.compile(r"^BATCH-(\d{8})-\d{4}-[0-9a-f]{8}$")
QUEUE_SCHEMA = "dayibin-production-publish-queue-v1"
AWAITING = "AWAITING_HUMAN_SCHEDULE_CONFIRMATION"
SCHEDULED = "SCHEDULED"


class ProductionScheduleError(RuntimeError):
    pass


def build_daily_operations_review(
    data_dir: str | Path,
    *,
    business_date: str,
    target: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(data_dir)
    queue_path = root / "production-publish-queue.json"
    queue = read_json(queue_path) if queue_path.exists() else {"items": []}
    items = [
        item for item in queue.get("items", [])
        if isinstance(item, dict) and str(item.get("scheduled_at") or "").startswith(business_date)
    ]
    published = [item for item in items if item.get("status") == "PUBLISHED_VERIFIED"]
    failed = [item for item in items if str(item.get("status") or "").startswith("STOPPED")]
    expired = [item for item in items if item.get("status") in {"EXPIRED", "NEEDS_REVALIDATION"}]
    vest_lines = [
        f"- {item.get('vest_name') or '未分配'} / {item.get('persona') or 'N/A'}：{item.get('assignment_reason') or 'N/A'}"
        for item in published
    ] or ["- 当日尚无已发布内容"]
    channel_counts = {
        channel: sum(1 for item in items if item.get("channel") == channel)
        for channel in ("HOT_NOW", "RISING_WATCH", "DAILY_VALUE")
    }
    review_queue_path = root / "post-publish-review-queue.json"
    review_queue = read_json(review_queue_path) if review_queue_path.exists() else {"items": []}
    detail_lines, has_real_interaction = _daily_review_details(items, review_queue.get("items", []))
    next_day = (
        "- 保留当日真实评论较高的题材与人设组合，下一轮只比较标题和篇幅。"
        if has_real_interaction
        else "- N/A（没有可用的真实互动数据，不能据此生成次日优化建议）"
    )
    text = "\n".join(
        [
            f"# 大宜宾每日运营复盘卡｜{business_date}",
            "",
            "## 今日计划 / 已发布 / 失败 / 作废",
            "",
            f"- 计划：{len(items)}",
            f"- 已发布：{len(published)}",
            f"- 失败：{len(failed)}",
            f"- 作废或待重验：{len(expired)}",
            "",
            "## 5 个马甲实际分布及分配理由",
            "",
            *vest_lines,
            "",
            "## 三通道",
            "",
            f"- HOT_NOW：{channel_counts['HOT_NOW']}",
            f"- RISING_WATCH：{channel_counts['RISING_WATCH']}",
            f"- DAILY_VALUE：{channel_counts['DAILY_VALUE']}",
            "",
            "## 互动数据",
            "",
            "- 阅读：N/A（供应商当前未提供可靠字段）",
            "- 点赞：N/A（供应商当前未提供可靠字段）",
            "- 转发：N/A（供应商当前未提供可靠字段）",
            "- 评论：以帖子复盘队列真实采集为准；自动评论必须剔除",
            "",
            "## 单篇事实明细",
            "",
            "| 题材 | 锁定角度 | 写稿 Skill | 文章篇幅 | 发布时间 | 真实互动 | 数据缺失原因 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *detail_lines,
            "",
            "## 次日建议",
            "",
            next_day,
        ]
    ) + "\n"
    output = Path(target or root / business_date / "daily-operations-review.md")
    atomic_write_text(output, text)
    return {
        "status": "DAILY_REVIEW_READY",
        "business_date": business_date,
        "path": str(output),
        "planned_count": len(items),
        "published_count": len(published),
        "qianfan_called": False,
    }


def _daily_review_details(
    items: list[dict[str, Any]], review_items: object
) -> tuple[list[str], bool]:
    completed = [
        item for item in review_items
        if isinstance(item, dict) and item.get("status") == "COMPLETED"
    ] if isinstance(review_items, list) else []
    latest: dict[str, dict[str, Any]] = {}
    for item in completed:
        ref = str(item.get("publication_ref") or "")
        if ref and str(item.get("observed_at") or "") >= str(latest.get(ref, {}).get("observed_at") or ""):
            latest[ref] = item
    lines: list[str] = []
    has_real_interaction = False
    for item in items:
        ref = str(item.get("publication_ref") or "")
        review = latest.get(ref, {})
        metrics = review.get("metrics") if isinstance(review.get("metrics"), dict) else {}
        labels = {
            "read_count": "阅读", "reply_count": "评论",
            "like_count": "点赞", "share_count": "转发",
        }
        interaction: list[str] = []
        missing: list[str] = []
        for key, label in labels.items():
            value = metrics.get(key)
            if isinstance(value, (int, float)):
                interaction.append(f"{label} {value}")
                has_real_interaction = True
            else:
                interaction.append(f"{label} N/A")
                if value == "N/A_SUPPLIER_FIELD_UNAVAILABLE":
                    missing.append(f"{label}供应商字段不可用")
        if not review:
            missing.append("尚未发布" if item.get("status") != "PUBLISHED_VERIFIED" else "复盘采样尚未完成")
        published_at = item.get("published_at") or ("N/A（尚未发布）" if item.get("status") != "PUBLISHED_VERIFIED" else "N/A（发布时间缺失）")
        lines.append(
            "| " + " | ".join(
                str(value).replace("|", "\\|")
                for value in (
                    item.get("title") or "N/A（题材缺失）",
                    item.get("locked_angle_id") or "N/A（锁定角度缺失）",
                    item.get("selected_writing_skill") or "N/A（写稿 Skill 缺失）",
                    item.get("visible_char_count") or "N/A（篇幅缺失）",
                    published_at,
                    "；".join(interaction),
                    "；".join(missing) or "N/A（无缺失）",
                )
            ) + " |"
        )
    return lines or ["| N/A（当日无排期） | N/A | N/A | N/A | N/A | N/A | 当日无排期数据 |"], has_real_interaction


def confirm_batch_schedule(
    data_dir: str | Path,
    *,
    batch_id: str,
    confirmation_phrase: str,
    queue_path: str | Path | None = None,
    now: datetime | None = None,
    rng: random.Random | None = None,
    settings: Any | None = None,
    daily_hard_cap: int = 15,
) -> dict[str, Any]:
    root = Path(data_dir)
    batch_dir = _batch_dir(root, batch_id)
    batch_path = batch_dir / "batch.json"
    batch = read_json(batch_path)
    expected = f"确认本批排期：{batch_id}"
    queue_target = Path(queue_path or root / "production-publish-queue.json")
    current = (now or datetime.now(UTC)).astimezone(SHANGHAI)
    generator = rng or random.SystemRandom()

    if confirmation_phrase != expected or batch.get("schedule_confirmation_phrase") != expected:
        raise ProductionScheduleError("schedule confirmation phrase does not match exactly")
    if batch.get("batch_id") != batch_id:
        raise ProductionScheduleError("batch_id does not match batch file")
    if batch.get("status") not in {AWAITING, SCHEDULED}:
        raise ProductionScheduleError("batch is not awaiting schedule confirmation")
    drafts = _validated_drafts(batch, batch_dir)

    lock_path = queue_target.with_suffix(queue_target.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ProductionScheduleError("production schedule queue is busy") from error
        queue = read_json(queue_target) if queue_target.exists() else {
            "schema_version": QUEUE_SCHEMA,
            "items": [],
        }
        items = queue.get("items")
        if queue.get("schema_version") != QUEUE_SCHEMA or not isinstance(items, list):
            raise ProductionScheduleError("production schedule queue is invalid")
        existing = [item for item in items if isinstance(item, dict) and item.get("batch_id") == batch_id]
        if existing:
            return _schedule_result(batch_id, existing)

        ordered = _interleave_vests(drafts)
        active_items = [
            item for item in items
            if isinstance(item, dict)
            and item.get("status") in {SCHEDULED, "PUBLISHING", "PUBLISHED", "PUBLISHED_VERIFIED"}
        ]
        current_day_count = sum(
            1
            for item in active_items
            if str(item.get("scheduled_at") or item.get("published_at") or "")[:10]
            == current.date().isoformat()
        )
        if current_day_count + len(drafts) > daily_hard_cap:
            raise ProductionScheduleError("daily hard cap would be exceeded")
        occupied = [item for item in active_items if item.get("scheduled_at")]
        schedule_day = current.date()
        if current.timetz().replace(tzinfo=None) > time(22, 30):
            schedule_day += timedelta(days=1)
        active_start = _parse_clock(getattr(settings, "active_start", "08:20"))
        active_end = _parse_clock(getattr(settings, "active_end", "22:30"))
        global_min = int(getattr(settings, "global_interval_min_minutes", 45))
        global_max = int(getattr(settings, "global_interval_max_minutes", 120))
        same_vest_min = int(getattr(settings, "same_vest_interval_minutes", 150))
        created: list[dict[str, Any]] = []
        if ordered and all(draft.get("channel") == "DAILY_VALUE" for draft in ordered):
            created = _plan_daily_value_batch(
                batch_id, ordered, occupied, current, generator,
                active_start, active_end, global_min, global_max, same_vest_min,
                daily_hard_cap,
            )
            if not created:
                raise ProductionScheduleError("batch does not fit the next operating day")
            items.extend(created)
            occupied.extend(created)
            ordered = []
        for draft in list(ordered):
            if draft.get("channel") != "HOT_NOW":
                continue
            slot = next(
                (
                    item for item in sorted(occupied, key=lambda row: str(row["scheduled_at"]))
                    if item.get("channel") == "DAILY_VALUE"
                    and datetime.fromisoformat(str(item["scheduled_at"])) >= current
                    and _vest_slot_is_clear(
                        occupied,
                        str(draft["vest_name"]),
                        datetime.fromisoformat(str(item["scheduled_at"])),
                        same_vest_min,
                        excluded=item,
                    )
                ),
                None,
            )
            if slot is None:
                continue
            old_slot = datetime.fromisoformat(str(slot["scheduled_at"]))
            latest = max(datetime.fromisoformat(str(item["scheduled_at"])) for item in occupied)
            moved = latest + timedelta(minutes=generator.randint(global_min, global_max))
            previous_same = max(
                (
                    datetime.fromisoformat(str(item["scheduled_at"]))
                    for item in occupied
                    if item is not slot and item.get("vest_name") == slot.get("vest_name")
                ),
                default=None,
            )
            if previous_same is not None:
                moved = max(moved, previous_same + timedelta(minutes=same_vest_min))
            moved = _fit_active_window(moved, active_start, active_end)
            if moved.date() != schedule_day:
                continue
            slot["scheduled_at"] = moved.isoformat()
            slot["displaced_by_hot_now"] = f"{batch_id}:{draft['content_id']}"
            hot_item = _freeze_queue_item(batch_id, draft, old_slot, current)
            created.append(hot_item)
            items.append(hot_item)
            occupied.append(hot_item)
            ordered.remove(draft)

        cursor = _initial_cursor(schedule_day, current, generator, active_start)
        last_by_vest = _last_times_by_vest(occupied)
        if occupied:
            cursor = max(cursor, max(datetime.fromisoformat(str(item["scheduled_at"])) for item in occupied) + timedelta(minutes=generator.randint(global_min, global_max)))

        for draft in ordered:
            vest = str(draft["vest_name"])
            previous_vest = last_by_vest.get(vest)
            if previous_vest is not None:
                cursor = max(cursor, previous_vest + timedelta(minutes=same_vest_min))
            cursor = _fit_active_window(cursor, active_start, active_end)
            if cursor.date() != schedule_day:
                raise ProductionScheduleError("batch does not fit the current operating day")
            item = _freeze_queue_item(batch_id, draft, cursor, current)
            created.append(item)
            items.append(item)
            last_by_vest[vest] = cursor
            cursor += timedelta(minutes=generator.randint(global_min, global_max))

        queue["updated_at"] = current.isoformat()
        atomic_write_json(queue_target, queue)
        batch.update(
            {
                "status": SCHEDULED,
                "scheduled_at": current.isoformat(),
                "schedule_queue_path": str(queue_target),
                "qianfan_called": bool(batch.get("qianfan_called")),
            }
        )
        atomic_write_json(batch_path, batch)
        return _schedule_result(batch_id, created)


def dispatch_due_publications(
    queue_path: str | Path,
    *,
    now: datetime | None = None,
    no_send: bool = False,
    publisher: Callable[[dict[str, Any], bool], dict[str, Any]],
) -> dict[str, Any]:
    target = Path(queue_path)
    current = (now or datetime.now(UTC)).astimezone(SHANGHAI)
    if not target.is_file():
        return {"status": "QUEUE_NOT_READY", "processed_count": 0, "qianfan_called": False}
    lock_path = target.with_suffix(target.suffix + ".dispatch.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"status": "SKIPPED_OVERLAP", "processed_count": 0, "qianfan_called": False}
        queue = read_json(target)
        items = queue.get("items")
        if queue.get("schema_version") != QUEUE_SCHEMA or not isinstance(items, list):
            raise ProductionScheduleError("production schedule queue is invalid")

        crossed = False
        for item in items:
            if not isinstance(item, dict) or item.get("status") != SCHEDULED:
                continue
            scheduled = datetime.fromisoformat(str(item.get("scheduled_at") or ""))
            if scheduled.astimezone(SHANGHAI).date() < current.date():
                item["status"] = "NEEDS_REVALIDATION" if item.get("evergreen") is True else "EXPIRED"
                item["updated_at"] = current.isoformat()
                crossed = True
        if crossed:
            queue["updated_at"] = current.isoformat()
            atomic_write_json(target, queue)
            return {"status": "CROSS_DAY_HELD", "processed_count": 0, "qianfan_called": False}

        due = sorted(
            (
                item for item in items
                if isinstance(item, dict)
                and item.get("status") == SCHEDULED
                and datetime.fromisoformat(str(item.get("scheduled_at") or "")) <= current
            ),
            key=lambda item: str(item["scheduled_at"]),
        )
        if not due:
            return {"status": "NOT_DUE", "processed_count": 0, "qianfan_called": False}
        item = due[0]
        try:
            result = publisher(item, no_send)
        except Exception as error:
            item.update(
                {
                    "status": "STOPPED_AFTER_FAILURE",
                    "failure_type": type(error).__name__,
                    "updated_at": current.isoformat(),
                }
            )
            queue["updated_at"] = current.isoformat()
            atomic_write_json(target, queue)
            raise ProductionScheduleError("scheduled publication stopped after failure") from error

        qianfan_called = bool(result.get("qianfan_called"))
        if no_send:
            return {
                "status": "DUE_NO_SEND",
                "processed_count": 1,
                "queue_id": item.get("queue_id"),
                "qianfan_called": False,
                "publisher_result": result,
            }
        already_published = bool(result.get("already_published"))
        if result.get("status") != "PUBLISHED_VERIFIED" or (not qianfan_called and not already_published):
            item.update({"status": "STOPPED_RESULT_UNKNOWN", "updated_at": current.isoformat()})
            queue["updated_at"] = current.isoformat()
            atomic_write_json(target, queue)
            raise ProductionScheduleError("scheduled publication stopped after unknown result")
        item.update(
            {
                "status": "PUBLISHED_VERIFIED",
                "published_at": result.get("published_at") or current.isoformat(),
                "publication_ref": result.get("tid") or result.get("publication_ref"),
                "updated_at": current.isoformat(),
            }
        )
        queue["updated_at"] = current.isoformat()
        atomic_write_json(target, queue)
        return {
            "status": "PUBLISHED_VERIFIED",
            "processed_count": 1,
            "queue_id": item.get("queue_id"),
            "qianfan_called": qianfan_called,
            "already_published": already_published,
        }


def _batch_dir(data_dir: Path, batch_id: str) -> Path:
    matched = BATCH_ID_PATTERN.fullmatch(batch_id)
    if matched is None:
        raise ProductionScheduleError("invalid batch_id")
    raw = matched.group(1)
    target = data_dir / f"{raw[:4]}-{raw[4:6]}-{raw[6:]}" / "pending-batches" / batch_id
    if not target.joinpath("batch.json").is_file():
        raise ProductionScheduleError("batch does not exist")
    return target


def _validated_drafts(batch: dict[str, Any], batch_dir: Path) -> list[dict[str, Any]]:
    drafts = batch.get("drafts")
    if not isinstance(drafts, list) or not 1 <= len(drafts) <= 3:
        raise ProductionScheduleError("batch must contain 1-3 drafts")
    required = {
        "content_id", "event_id", "channel", "title", "html", "source_url",
        "vest_name", "persona", "assignment_reason", "risk_result", "locked_angle_id",
        "article_form", "document_type", "selected_writing_skill",
        "writing_skill_contract_proof", "editor_name", "editor_dna_path",
        "editor_selection_reason", "editor_dna_read_proof", "writing_session_id",
        "soft_audit", "review",
        "title_hash", "body_hash", "image_hashes", "material_hash", "frozen_contract_hash",
    }
    scheduled: list[dict[str, Any]] = []
    for draft in drafts:
        if not isinstance(draft, dict) or not required.issubset(draft):
            raise ProductionScheduleError("draft is missing production-chain fields")
        if draft.get("channel") not in {"HOT_NOW", "DAILY_VALUE"} or draft.get("risk_result") != "PASS":
            raise ProductionScheduleError("draft channel or risk gate is invalid")
        if draft.get("soft_audit", {}).get("status") != "PASS" or draft.get("review", {}).get("verdict") != "approved":
            raise ProductionScheduleError("draft review chain is incomplete")
        expected_binding = review_binding_hashes(draft)
        for evidence in (draft["soft_audit"], draft["review"]):
            if any(evidence.get(key) != value for key, value in expected_binding.items()):
                raise ProductionScheduleError("draft review binding changed after approval")
        if draft.get("images") and len(draft.get("image_plan") or []) != len(draft["images"]):
            raise ProductionScheduleError("draft body image plan is incomplete")
        if batch.get("schema_version") == "dayibin-pending-batch-v3":
            if draft.get("contract_version") != "daily-8-to-12-v1":
                raise ProductionScheduleError("draft production contract version is invalid")
            if not draft.get("images") and not all(
                str(draft.get(key) or "").strip()
                for key in ("no_image_reason", "no_image_policy_proof")
            ):
                raise ProductionScheduleError("no-image draft is missing forum policy evidence")
        if draft["frozen_contract_hash"] != frozen_contract_hash(draft):
            raise ProductionScheduleError("draft contract changed after confirmation card creation")
        from .batch_publish import BatchPublishError, _draft_plan, _validate_scheduled_draft
        try:
            _validate_scheduled_draft(draft, batch_dir)
            _draft_plan(draft, batch_dir)
        except BatchPublishError as error:
            raise ProductionScheduleError("draft contract changed after confirmation card creation") from error
        if draft.get("publish_action") == "EDIT_EXISTING":
            if not str(draft.get("edit_target_id") or "") or draft.get("edit_status") != "EDITED_VERIFIED":
                raise ProductionScheduleError("existing-post edit must be verified before batch scheduling")
            continue
        scheduled.append(draft)
    return scheduled


def frozen_contract_hash(draft: dict[str, Any]) -> str:
    fields = {
        key: draft.get(key)
        for key in (
            "content_id", "event_id", "channel", "source_url", "vest_name", "persona",
            "assignment_reason", "forum", "title_hash", "body_hash", "image_hashes", "material_hash",
            "article_form", "document_type", "selected_writing_skill", "writing_skill_contract_proof",
            "editor_name", "editor_dna_path", "editor_selection_reason", "editor_dna_read_proof",
            "writing_session_id",
            "locked_angle_id", "locked_angle", "writing_route", "image_manifest",
            "contract_version", "no_image_reason", "no_image_policy_proof",
            "soft_audit", "review",
        )
    }
    canonical = json.dumps(fields, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def review_binding_hashes(draft: dict[str, Any]) -> dict[str, str]:
    route = draft.get("writing_route")
    if not isinstance(route, dict):
        route = {
            key: draft.get(key)
            for key in (
                "article_form", "document_type", "selected_writing_skill",
                "writing_skill_contract_proof", "editor_name", "editor_dna_path",
                "editor_selection_reason", "editor_dna_read_proof", "writing_session_id",
            )
        }
    angle = draft.get("locked_angle")
    if not isinstance(angle, dict):
        angle = {"angle_id": draft.get("locked_angle_id")}
    values = {
        "reviewed_title_hash": str(draft.get("title") or ""),
        "reviewed_body_hash": str(draft.get("html") or ""),
        "reviewed_image_manifest_hash": draft.get("image_manifest") or [],
        "reviewed_writing_route_hash": route,
        "reviewed_locked_angle_hash": angle,
    }
    return {
        key: hashlib.sha256(
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        for key, value in values.items()
    }


def preview_daily_batch_schedules(
    data_dir: str | Path,
    batch_ids: list[str],
    *,
    queue_path: str | Path | None = None,
    now: datetime | None = None,
    rng: random.Random | None = None,
    settings: Any | None = None,
    daily_hard_cap: int = 15,
) -> dict[str, Any]:
    """Plan all confirmation-card batches without mutating a batch or queue."""
    root = Path(data_dir)
    queue_target = Path(queue_path or root / "production-publish-queue.json")
    queue = read_json(queue_target) if queue_target.exists() else {"schema_version": QUEUE_SCHEMA, "items": []}
    items = queue.get("items")
    if queue.get("schema_version") != QUEUE_SCHEMA or not isinstance(items, list):
        raise ProductionScheduleError("production schedule queue is invalid")
    active_statuses = {"PUBLISHED", "PUBLISHED_VERIFIED", "PUBLISHING", SCHEDULED}
    active_items = [
        item for item in items
        if isinstance(item, dict) and item.get("status") in active_statuses
    ]
    occupied = [
        item for item in active_items if item.get("scheduled_at")
    ]
    current = (now or datetime.now(UTC)).astimezone(SHANGHAI)
    batches: list[tuple[str, list[dict[str, Any]]]] = []
    for batch_id in batch_ids:
        batch_dir = _batch_dir(root, batch_id)
        batch = read_json(batch_dir / "batch.json")
        drafts = [draft for draft in _validated_drafts(batch, batch_dir) if draft.get("publish_action") != "EDIT_EXISTING"]
        batches.append((batch_id, drafts))
    current_day_occupied = [
        item for item in active_items
        if str(item.get("scheduled_at") or item.get("published_at") or "")[:10] == current.date().isoformat()
    ]
    if len(current_day_occupied) + sum(len(drafts) for _, drafts in batches) > daily_hard_cap:
        raise ProductionScheduleError("daily hard cap would be exceeded")

    generator = rng or random.SystemRandom()
    active_start = _parse_clock(getattr(settings, "active_start", "08:20"))
    active_end = _parse_clock(getattr(settings, "active_end", "22:30"))
    global_min = int(getattr(settings, "global_interval_min_minutes", 45))
    global_max = int(getattr(settings, "global_interval_max_minutes", 120))
    same_vest_min = int(getattr(settings, "same_vest_interval_minutes", 150))
    planned_batches = []
    for batch_id, drafts in batches:
        planned = _plan_daily_value_batch(
            batch_id, _interleave_vests(drafts), occupied, current, generator,
            active_start, active_end, global_min, global_max, same_vest_min,
            daily_hard_cap,
        )
        if planned is None:
            raise ProductionScheduleError(f"batch does not fit cumulative schedule: {batch_id}")
        occupied.extend(planned)
        planned_batches.append({"batch_id": batch_id, "items": _schedule_result(batch_id, planned)["items"]})
    return {"status": "PREVIEW_READY_NO_WRITE", "qianfan_called": False, "batches": planned_batches}


def _interleave_vests(drafts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    remaining = list(drafts)
    ordered: list[dict[str, Any]] = []
    previous = None
    while remaining:
        index = next((i for i, item in enumerate(remaining) if item.get("vest_name") != previous), 0)
        selected = remaining.pop(index)
        ordered.append(selected)
        previous = selected.get("vest_name")
    return ordered


def _plan_daily_value_batch(
    batch_id: str,
    drafts: list[dict[str, Any]],
    occupied: list[dict[str, Any]],
    current: datetime,
    generator: random.Random,
    active_start: time,
    active_end: time,
    global_min: int,
    global_max: int,
    same_vest_min: int,
    daily_hard_cap: int,
) -> list[dict[str, Any]] | None:
    schedule_day = current.date()
    if current.timetz().replace(tzinfo=None) > active_end:
        schedule_day += timedelta(days=1)
    for day in (schedule_day, schedule_day + timedelta(days=1)):
        day_count = sum(
            1
            for item in occupied
            if datetime.fromisoformat(str(item["scheduled_at"])).astimezone(SHANGHAI).date() == day
        )
        if day_count + len(drafts) > daily_hard_cap:
            if day == schedule_day:
                raise ProductionScheduleError("daily hard cap would be exceeded")
            continue
        planned = _plan_daily_batch(
            batch_id, drafts, occupied, day, current, generator,
            active_start, active_end, global_min, global_max, same_vest_min,
        )
        if planned:
            return planned
        if day != current.date():
            break
    return None


def _initial_cursor(day: date, now: datetime, rng: random.Random, active_start: time) -> datetime:
    opening = datetime.combine(day, active_start, SHANGHAI)
    floor = max(opening, now.replace(second=0, microsecond=0))
    if floor.minute in {0, 30}:
        floor += timedelta(minutes=7)
    return floor + timedelta(minutes=rng.randint(0, 14))


def _fit_active_window(value: datetime, active_start: time, active_end: time) -> datetime:
    opening = datetime.combine(value.date(), active_start, SHANGHAI)
    closing = datetime.combine(value.date(), active_end, SHANGHAI)
    if value < opening:
        return opening
    if value <= closing:
        return value
    return datetime.combine(value.date() + timedelta(days=1), active_start, SHANGHAI)


def _parse_clock(value: str) -> time:
    try:
        return time.fromisoformat(value)
    except ValueError as error:
        raise ProductionScheduleError("production active window is invalid") from error


def _last_times_by_vest(items: list[dict[str, Any]]) -> dict[str, datetime]:
    result: dict[str, datetime] = {}
    for item in items:
        vest = str(item.get("vest_name") or "")
        scheduled = datetime.fromisoformat(str(item.get("scheduled_at") or ""))
        if vest and (vest not in result or scheduled > result[vest]):
            result[vest] = scheduled
    return result


def _vest_slot_is_clear(
    items: list[dict[str, Any]],
    vest_name: str,
    scheduled_at: datetime,
    minimum_minutes: int,
    *,
    excluded: dict[str, Any],
) -> bool:
    return all(
        item is excluded
        or item.get("vest_name") != vest_name
        or abs((datetime.fromisoformat(str(item["scheduled_at"])) - scheduled_at).total_seconds())
        >= minimum_minutes * 60
        for item in items
    )


def _freeze_queue_item(
    batch_id: str, draft: dict[str, Any], scheduled_at: datetime, created_at: datetime
) -> dict[str, Any]:
    title = str(draft["title"]).strip()
    html = str(draft["html"]).strip()
    images = [str(value) for value in draft.get("images") or []]
    title_hash = hashlib.sha256(title.encode()).hexdigest()
    body_hash = hashlib.sha256(html.encode()).hexdigest()
    material_hash = str(draft.get("material_hash") or hashlib.sha256("\0".join([title_hash, body_hash, *images]).encode()).hexdigest())
    content_id = str(draft["content_id"])
    return {
        "queue_id": hashlib.sha256(f"{batch_id}|{content_id}".encode()).hexdigest(),
        "batch_id": batch_id,
        "content_id": content_id,
        "event_id": str(draft["event_id"]),
        "channel": str(draft["channel"]),
        "status": SCHEDULED,
        "scheduled_at": scheduled_at.isoformat(),
        "created_at": created_at.isoformat(),
        "vest_name": str(draft["vest_name"]),
        "persona": str(draft["persona"]),
        "assignment_reason": str(draft["assignment_reason"]),
        "title": title,
        "locked_angle_id": str(draft.get("locked_angle_id") or ""),
        "selected_writing_skill": str(draft.get("selected_writing_skill") or ""),
        "article_form": str(draft.get("article_form") or ""),
        "visible_char_count": len(re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", html))),
        "title_hash": title_hash,
        "body_hash": body_hash,
        "material_hash": material_hash,
        "frozen_contract_hash": draft.get("frozen_contract_hash"),
        "evergreen": draft.get("evergreen") is True,
    }


def _plan_daily_batch(
    batch_id: str,
    drafts: list[dict[str, Any]],
    occupied: list[dict[str, Any]],
    schedule_day: date,
    current: datetime,
    generator: random.Random,
    active_start: time,
    active_end: time,
    global_min: int,
    global_max: int,
    same_vest_min: int,
) -> list[dict[str, Any]] | None:
    day_items = [
        item for item in occupied
        if datetime.fromisoformat(str(item["scheduled_at"])).astimezone(SHANGHAI).date() == schedule_day
    ]
    cursor = _initial_cursor(schedule_day, current, generator, active_start)
    if day_items:
        cursor = max(
            cursor,
            max(datetime.fromisoformat(str(item["scheduled_at"])) for item in day_items)
            + timedelta(minutes=generator.randint(global_min, global_max)),
        )
    last_by_vest = _last_times_by_vest(day_items)
    planned: list[dict[str, Any]] = []
    for draft in drafts:
        vest = str(draft["vest_name"])
        if vest in last_by_vest:
            cursor = max(cursor, last_by_vest[vest] + timedelta(minutes=same_vest_min))
        cursor = _fit_active_window(cursor, active_start, active_end)
        if cursor.date() != schedule_day:
            return None
        item = _freeze_queue_item(batch_id, draft, cursor, current)
        planned.append(item)
        last_by_vest[vest] = cursor
        cursor += timedelta(minutes=generator.randint(global_min, global_max))
    return planned


def _schedule_result(batch_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": SCHEDULED,
        "batch_id": batch_id,
        "qianfan_called": False,
        "items": [
            {
                key: item.get(key)
                for key in ("queue_id", "content_id", "channel", "vest_name", "scheduled_at", "status")
            }
            for item in items
        ],
    }
