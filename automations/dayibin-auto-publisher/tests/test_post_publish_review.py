from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dayibin_auto_publisher.post_publish_review import (
    dispatch_due_reviews,
    enqueue_publication,
    qianfan_reply_metrics_fetcher,
)


class PostPublishReviewTests(unittest.TestCase):
    def test_qianfan_metrics_use_only_non_operator_replies(self) -> None:
        class Client:
            def __init__(self) -> None:
                self.vest_ids = None

            def collect_reply_metrics(self, **kwargs):
                self.vest_ids = kwargs["vest_ids"]
                return [{"thread_id": "948529", "total_reply_count": 9,
                         "non_vest_reply_count": 4, "non_vest_unique_users": 3}]

        client = Client()
        metrics = qianfan_reply_metrics_fetcher(
            client, now=datetime(2026, 8, 22, 2, 0, tzinfo=UTC),
            operator_vest_ids={"posting-1", "comment-1"},
        )({"948529"})

        self.assertEqual(client.vest_ids, {"posting-1", "comment-1"})
        self.assertEqual(metrics["948529"]["reply_count"], 4)
        self.assertEqual(metrics["948529"]["non_vest_unique_users"], 3)
    def test_enqueue_creates_three_unique_checkpoints(self) -> None:
        with TemporaryDirectory() as tmp:
            queue = Path(tmp) / "queue.json"
            enqueue_publication(
                queue,
                publication_ref="948529",
                published_at="2026-08-22T10:00:00+08:00",
                metadata={"topic": "城市更新", "persona": "城市观察室型"},
            )
            enqueue_publication(
                queue,
                publication_ref="948529",
                published_at="2026-08-22T10:00:00+08:00",
                metadata={"topic": "城市更新", "persona": "城市观察室型"},
            )

            payload = json.loads(queue.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["items"]), 3)
            self.assertEqual(
                [item["checkpoint"] for item in payload["items"]],
                ["30m", "2h", "24h"],
            )

    def test_dispatch_samples_only_latest_due_checkpoint_and_marks_older_missed(self) -> None:
        with TemporaryDirectory() as tmp:
            queue = Path(tmp) / "queue.json"
            enqueue_publication(
                queue,
                publication_ref="948529",
                published_at="2026-08-21T08:00:00+08:00",
                metadata={"topic": "城市更新", "persona": "城市观察室型"},
            )
            calls: list[set[str]] = []

            def fetcher(refs: set[str]):
                calls.append(refs)
                return {"948529": {"reply_count": 7}}

            result = dispatch_due_reviews(
                queue,
                now=datetime(2026, 8, 22, 2, 0, tzinfo=UTC),
                metrics_fetcher=fetcher,
            )

            self.assertEqual(result["sampled_count"], 1)
            self.assertEqual(result["missed_count"], 2)
            self.assertEqual(calls, [{"948529"}])
            payload = json.loads(queue.read_text(encoding="utf-8"))
            statuses = {item["checkpoint"]: item["status"] for item in payload["items"]}
            self.assertEqual(statuses, {"30m": "MISSED_NO_SAMPLE", "2h": "MISSED_NO_SAMPLE", "24h": "COMPLETED"})
            completed = next(item for item in payload["items"] if item["checkpoint"] == "24h")
            self.assertEqual(completed["metrics"]["reply_count"], 7)
            self.assertEqual(completed["metrics"]["read_count"], "N/A_SUPPLIER_FIELD_UNAVAILABLE")
            self.assertEqual(completed["metrics"]["like_count"], "N/A_SUPPLIER_FIELD_UNAVAILABLE")
            self.assertEqual(completed["metrics"]["share_count"], "N/A_SUPPLIER_FIELD_UNAVAILABLE")
            self.assertTrue(completed["recommendations"])


if __name__ == "__main__":
    unittest.main()
