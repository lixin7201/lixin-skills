from datetime import UTC, datetime, timedelta
import hashlib
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from dayibin_auto_publisher.collector import SnapshotOptions, collect_snapshot


RAW_ITEMS_SCHEMA = """
CREATE TABLE raw_items (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    canonical_url TEXT,
    title TEXT NOT NULL,
    summary TEXT,
    raw_text TEXT,
    author TEXT,
    published_at TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    geo_scope TEXT,
    source_nature TEXT,
    verification_state TEXT,
    content_hash TEXT,
    dedupe_key TEXT NOT NULL,
    is_noise INTEGER NOT NULL DEFAULT 0,
    noise_reason TEXT
)
"""


class CollectorTests(unittest.TestCase):
    def test_collect_snapshot_filters_and_deduplicates_without_writing_database(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "radar.db"
            output_path = root / "hotspots.json"
            now = datetime(2026, 8, 18, 9, 0, tzinfo=UTC)
            conn = sqlite3.connect(db_path)
            conn.execute(RAW_ITEMS_SCHEMA)
            rows = [
                self._row(
                    "valid-new",
                    "https://example.com/a",
                    "宜宾新变化",
                    "正文" * 100,
                    now - timedelta(hours=1),
                    "same-hash",
                ),
                self._row(
                    "duplicate-old",
                    "https://example.com/a-old",
                    "宜宾新变化旧稿",
                    "旧正文" * 100,
                    now - timedelta(hours=2),
                    "same-hash",
                ),
                self._row(
                    "empty-body",
                    "https://example.com/b",
                    "没有正文",
                    "",
                    now - timedelta(hours=1),
                    "empty",
                ),
                self._row(
                    "old",
                    "https://example.com/c",
                    "过期新闻",
                    "正文" * 100,
                    now - timedelta(hours=80),
                    "old",
                ),
                self._row(
                    "noise",
                    "https://example.com/d",
                    "噪声",
                    "正文" * 100,
                    now - timedelta(hours=1),
                    "noise",
                    is_noise=1,
                ),
                self._row(
                    "bad-url",
                    "javascript:alert(1)",
                    "坏链接",
                    "正文" * 100,
                    now - timedelta(hours=1),
                    "bad-url",
                ),
            ]
            conn.executemany(
                """
                INSERT INTO raw_items (
                    id,source_id,canonical_url,title,summary,raw_text,author,
                    published_at,first_seen_at,last_seen_at,geo_scope,
                    source_nature,verification_state,content_hash,dedupe_key,
                    is_noise,noise_reason
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                rows,
            )
            conn.commit()
            conn.close()
            before_hash = hashlib.sha256(db_path.read_bytes()).hexdigest()

            snapshot = collect_snapshot(
                db_path,
                output_path,
                SnapshotOptions(lookback_hours=48, min_body_chars=120, max_items=20),
                now=now,
            )

            after_hash = hashlib.sha256(db_path.read_bytes()).hexdigest()
            self.assertEqual(before_hash, after_hash)
            self.assertEqual(snapshot["item_count"], 1)
            self.assertEqual(snapshot["items"][0]["id"], "valid-new")
            self.assertEqual(len(snapshot["items"][0]["content_sha256"]), 64)
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8")), snapshot)

    @staticmethod
    def _row(
        item_id: str,
        url: str,
        title: str,
        body: str,
        published_at: datetime,
        content_hash: str,
        *,
        is_noise: int = 0,
    ) -> tuple[object, ...]:
        timestamp = published_at.isoformat().replace("+00:00", "Z")
        return (
            item_id,
            "source-1",
            url,
            title,
            title,
            body,
            "作者",
            timestamp,
            timestamp,
            timestamp,
            "yibin",
            "media",
            "verified",
            content_hash,
            item_id,
            is_noise,
            None,
        )


if __name__ == "__main__":
    unittest.main()
