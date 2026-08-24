from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dayibin_auto_publisher.publish import PublishError, publish_drafts


class FakeAgent:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
        self.calls.append((prompt, session_id))
        return {
            "publish_result": {
                "status": "published",
                "tid": "12345",
                "url": "https://dayibin.cn/wap/thread/view-thread/tid/12345",
                "vest_id": "88",
                "forum_id": "107",
                "type_id": "11",
            }
        }


DRAFTS = {
    "schema_version": 1,
    "drafts": [
        {
            "item_id": "item-1",
            "profile_id": "city",
            "title": "宜宾新增公交线路，大家出门更方便",
            "html": "<p>宜宾新增公交线路。</p>",
            "fact_refs": [{"claim": "新增线路", "evidence": "新增线路"}],
            "editor_route": "练团长",
            "source_url": "https://example.com/1",
            "source_content_sha256": "a" * 64,
            "accepted": True,
            "rejection_reasons": [],
        }
    ],
}


class PublishTests(unittest.TestCase):
    def test_publish_drafts_saves_result_and_is_idempotent(self) -> None:
        with TemporaryDirectory() as tmp:
            result_path = Path(tmp) / "publish-results.json"
            profiles = (
                {
                    "id": "city",
                    "name": "宜宾路上见",
                    "vest_name": "路上见",
                    "forum_id": "107",
                },
            )
            agent = FakeAgent()

            first = publish_drafts(
                agent,
                date(2026, 8, 18),
                DRAFTS,
                profiles,
                result_path,
                limit=1,
            )
            second = publish_drafts(
                agent,
                date(2026, 8, 18),
                DRAFTS,
                profiles,
                result_path,
                limit=1,
            )

            self.assertEqual(first["published_count"], 1)
            self.assertEqual(second["published_count"], 1)
            self.assertEqual(len(agent.calls), 1)
            self.assertEqual(first["results"][0]["tid"], "12345")
            self.assertEqual(len(first["results"][0]["idempotency_key"]), 64)

    def test_publish_drafts_rejects_missing_vest_mapping(self) -> None:
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(PublishError, "vest_name"):
                publish_drafts(
                    FakeAgent(),
                    date(2026, 8, 18),
                    DRAFTS,
                    ({"id": "city", "forum_id": "107"},),
                    Path(tmp) / "publish-results.json",
                    limit=1,
                )


if __name__ == "__main__":
    unittest.main()
