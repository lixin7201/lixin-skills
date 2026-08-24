from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
from pathlib import Path
import sqlite3
from typing import Any
from urllib.parse import urlparse

from .storage import atomic_write_json


class CollectorError(RuntimeError):
    pass


@dataclass(frozen=True)
class SnapshotOptions:
    lookback_hours: int = 48
    min_body_chars: int = 120
    max_items: int = 200


def collect_snapshot(
    db_path: str | Path,
    output_path: str | Path,
    options: SnapshotOptions,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    source_path = Path(db_path).expanduser().resolve()
    target_path = Path(output_path).expanduser().resolve()
    current = _aware_utc(now or datetime.now(UTC))
    cutoff = current - timedelta(hours=options.lookback_hours)
    if not source_path.is_file():
        raise CollectorError(f"source database not found: {source_path}")

    rows = _read_rows(source_path, cutoff, current, options)
    items = _normalize_and_dedupe(rows, options.max_items)
    snapshot = {
        "schema_version": 1,
        "generated_at": _iso(current),
        "source_db": str(source_path),
        "lookback_hours": options.lookback_hours,
        "min_body_chars": options.min_body_chars,
        "item_count": len(items),
        "items": items,
    }
    atomic_write_json(target_path, snapshot)
    return snapshot


def _read_rows(
    db_path: Path,
    cutoff: datetime,
    now: datetime,
    options: SnapshotOptions,
) -> list[sqlite3.Row]:
    uri = f"file:{db_path.as_posix()}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=5)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id,source_id,canonical_url,title,summary,raw_text,author,
                   published_at,first_seen_at,last_seen_at,geo_scope,
                   source_nature,verification_state,content_hash,dedupe_key
            FROM raw_items
            WHERE is_noise=0
              AND length(trim(COALESCE(raw_text,''))) >= ?
              AND COALESCE(published_at,first_seen_at) >= ?
              AND COALESCE(published_at,first_seen_at) <= ?
            ORDER BY COALESCE(published_at,first_seen_at) DESC, first_seen_at DESC
            LIMIT ?
            """,
            (
                options.min_body_chars,
                _iso(cutoff),
                _iso(now),
                max(options.max_items * 4, options.max_items),
            ),
        ).fetchall()
    except sqlite3.Error as error:
        raise CollectorError(f"could not read raw_items: {error}") from error
    finally:
        if "conn" in locals():
            conn.close()
    return rows


def _normalize_and_dedupe(rows: list[sqlite3.Row], limit: int) -> list[dict[str, Any]]:
    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    for row in rows:
        url = str(row["canonical_url"] or "").strip()
        if not _safe_http_url(url):
            continue
        body = str(row["raw_text"] or "").strip()
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        identity = str(row["content_hash"] or "").strip() or digest or url
        if identity in seen:
            continue
        seen.add(identity)
        items.append(
            {
                "id": str(row["id"]),
                "source_id": str(row["source_id"]),
                "source_url": url,
                "title": str(row["title"]).strip(),
                "summary": str(row["summary"] or "").strip(),
                "body": body,
                "author": str(row["author"] or "").strip(),
                "published_at": row["published_at"],
                "first_seen_at": row["first_seen_at"],
                "last_seen_at": row["last_seen_at"],
                "geo_scope": row["geo_scope"],
                "source_nature": row["source_nature"],
                "verification_state": row["verification_state"],
                "content_sha256": digest,
            }
        )
        if len(items) >= limit:
            break
    return items


def _safe_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise CollectorError("now must be timezone-aware")
    return value.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
