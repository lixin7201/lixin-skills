from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from .storage import atomic_write_json, read_json


SHANGHAI = ZoneInfo("Asia/Shanghai")
CHECKPOINTS = (("30m", 30), ("2h", 120), ("24h", 1440))
UNAVAILABLE = "N/A_SUPPLIER_FIELD_UNAVAILABLE"


def enqueue_publication(
    queue_path: str | Path,
    *,
    publication_ref: str,
    published_at: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    target = Path(queue_path)
    queue = read_json(target) if target.exists() else {
        "schema_version": "post-publish-review-queue-v1",
        "items": [],
    }
    items = queue.get("items") if isinstance(queue.get("items"), list) else []
    published = _parse_time(published_at)
    existing = {
        (str(item.get("publication_ref") or ""), str(item.get("checkpoint") or ""))
        for item in items
        if isinstance(item, dict)
    }
    for checkpoint, minutes in CHECKPOINTS:
        key = (publication_ref, checkpoint)
        if key in existing:
            continue
        items.append(
            {
                "publication_ref": publication_ref,
                "checkpoint": checkpoint,
                "due_at": (published + timedelta(minutes=minutes)).isoformat(),
                "status": "PENDING",
                "metadata": dict(metadata),
            }
        )
    queue["items"] = items
    atomic_write_json(target, queue)
    return {"status": "QUEUED", "item_count": len(items)}


def dispatch_due_reviews(
    queue_path: str | Path,
    *,
    now: datetime,
    metrics_fetcher: Callable[[set[str]], dict[str, dict[str, Any]]],
    max_items: int = 10,
) -> dict[str, Any]:
    target = Path(queue_path)
    if not target.exists():
        return {"status": "EMPTY", "sampled_count": 0, "missed_count": 0}
    queue = read_json(target)
    current = now.astimezone(SHANGHAI)
    pending = [
        item
        for item in queue.get("items", [])
        if isinstance(item, dict)
        and item.get("status") == "PENDING"
        and _parse_time(str(item.get("due_at") or "")) <= current
    ]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in pending:
        grouped.setdefault(str(item.get("publication_ref") or ""), []).append(item)

    selected: list[dict[str, Any]] = []
    missed = 0
    for publication_ref in sorted(grouped)[:max_items]:
        rows = sorted(grouped[publication_ref], key=lambda item: _parse_time(str(item["due_at"])))
        for stale in rows[:-1]:
            stale["status"] = "MISSED_NO_SAMPLE"
            stale["resolved_at"] = current.isoformat()
            missed += 1
        selected.append(rows[-1])

    metrics = metrics_fetcher(
        {str(item.get("publication_ref") or "") for item in selected}
    ) if selected else {}
    evidence_root = target.parent / "post-publish-review-evidence"
    sampled = 0
    for item in selected:
        publication_ref = str(item.get("publication_ref") or "")
        checkpoint = str(item.get("checkpoint") or "")
        evidence_path = evidence_root / publication_ref / f"{checkpoint}.json"
        if evidence_path.exists():
            saved = read_json(evidence_path)
            item.update(saved.get("queue_update") or {})
            continue
        raw = metrics.get(publication_ref) if isinstance(metrics.get(publication_ref), dict) else {}
        normalized = {
            "read_count": raw.get("read_count", UNAVAILABLE),
            "reply_count": raw.get("reply_count", UNAVAILABLE),
            "non_vest_reply_count": raw.get("reply_count", UNAVAILABLE),
            "non_vest_unique_users": raw.get("non_vest_unique_users", UNAVAILABLE),
            "operator_exclusion_status": raw.get(
                "operator_exclusion_status", "N/A_OPERATOR_IDS_INCOMPLETE"
            ),
            "like_count": raw.get("like_count", UNAVAILABLE),
            "share_count": raw.get("share_count", UNAVAILABLE),
        }
        item.update(
            {
                "status": "COMPLETED",
                "observed_at": current.isoformat(),
                "lag_seconds": max(
                    0,
                    int((current - _parse_time(str(item["due_at"]))).total_seconds()),
                ),
                "metrics": normalized,
            }
        )
        if checkpoint == "24h":
            item["recommendations"] = _recommendations(normalized, item.get("metadata"))
        atomic_write_json(
            evidence_path,
            {
                "schema_version": "post-publish-review-checkpoint-v1",
                "publication_ref": publication_ref,
                "checkpoint": checkpoint,
                "queue_update": {
                    key: item[key]
                    for key in ("status", "observed_at", "lag_seconds", "metrics", "recommendations")
                    if key in item
                },
            },
        )
        sampled += 1
    atomic_write_json(target, queue)
    return {
        "status": "COMPLETED" if selected else "NOT_DUE",
        "sampled_count": sampled,
        "missed_count": missed,
        "qianfan_publish_called": False,
    }


def qianfan_reply_metrics_fetcher(
    client: Any, *, now: datetime, operator_vest_ids: set[str] | None = None
):
    current = now.astimezone(SHANGHAI)
    excluded = set(operator_vest_ids or ())

    def fetch(publication_refs: set[str]) -> dict[str, dict[str, Any]]:
        if not excluded:
            return {
                publication_ref: {
                    "reply_count": UNAVAILABLE,
                    "non_vest_unique_users": UNAVAILABLE,
                    "operator_exclusion_status": "N/A_OPERATOR_IDS_INCOMPLETE",
                }
                for publication_ref in publication_refs
            }
        rows = client.collect_reply_metrics(
            thread_ids=publication_refs,
            vest_ids=excluded,
            start_date=(current.date() - timedelta(days=2)).isoformat(),
            end_date=current.date().isoformat(),
        )
        return {
            str(row.get("thread_id") or ""): {
                "reply_count": row.get("non_vest_reply_count", UNAVAILABLE),
                "non_vest_unique_users": row.get("non_vest_unique_users", UNAVAILABLE),
                "operator_exclusion_status": "PASS",
            }
            for row in rows
            if isinstance(row, dict)
        }

    return fetch


def _recommendations(metrics: dict[str, Any], metadata: object) -> list[str]:
    if metrics.get("operator_exclusion_status") != "PASS":
        return ["运营账号剔除不完整，本节点禁止进入进化计算。"]
    replies = metrics.get("reply_count")
    if isinstance(replies, int) and replies > 0:
        return ["保留当前选题与人设组合，下一轮重点比较标题和篇幅对回复质量的影响。"]
    return ["当前可用互动信号不足，继续观察同类选题，不自动修改提示词或安全阈值。"]


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=SHANGHAI)
    return parsed.astimezone(SHANGHAI)
