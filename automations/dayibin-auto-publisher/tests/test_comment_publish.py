from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dayibin_auto_publisher.comment_publish import (
    CommentPublishError,
    publish_comment_batch,
)


POST = {
    "thread_id": "100",
    "pid": "900",
    "fid": "75",
    "title": "宜宾叙州区新增公交站，通勤线路有变化",
    "url": "https://dayibin.cn/wap/thread/view-thread/tid/100",
}
COMMENT = {
    "thread_id": "100",
    "profile_id": "observer",
    "comment": "叙州区新增公交站后通勤会有变化，大家最想先改善哪一段换乘距离？",
    "post_fact_refs": ["F1", "F2"],
    "accepted": True,
    "rejection_reasons": [],
}
PROFILE = {"id": "observer", "role": "社区观察员", "vest_name": "观察号", "vest_id": "88"}


class FakeAgent:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
        self.calls.append((prompt, session_id))
        return {
            "publish_results": [
                {
                    "thread_id": "100",
                    "status": "published",
                    "url": "https://dayibin.cn/wap/thread/view-thread/tid/100",
                    "vest_id": "88",
                    "reply_id": "991",
                }
            ]
        }


class FakeDirectPublisher:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def publish_replies(self, **kwargs) -> dict[str, object]:
        self.calls.append(kwargs)
        item = kwargs["pending"][0]
        return {
            "publish_results": [
                {
                    "thread_id": item["thread_id"],
                    "status": "published",
                    "url": item["url"],
                    "vest_id": kwargs["vest_id"],
                    "reply_id": "direct-991",
                }
            ]
        }


class CommentPublishTests(unittest.TestCase):
    def test_saves_real_result_and_reuses_post_level_idempotency(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "publish-results.json"
            agent = FakeAgent()

            first = publish_comment_batch(
                agent,
                date(2026, 8, 19),
                PROFILE,
                [POST],
                [COMMENT],
                path,
            )
            second = publish_comment_batch(
                agent,
                date(2026, 8, 19),
                PROFILE,
                [POST],
                [COMMENT],
                path,
            )

            self.assertEqual(len(agent.calls), 1)
            self.assertIn("/review/vest-reply/add", agent.calls[0][0])
            self.assertIn('"vest_id": "88"', agent.calls[0][0])
            self.assertIn("禁止调用随机马甲列表后改用其他账号", agent.calls[0][0])
            self.assertEqual(first["results"][0]["vest_id"], "88")
            self.assertEqual(first["results"][0]["url"], POST["url"])
            self.assertEqual(len(first["results"][0]["idempotency_key"]), 64)
            self.assertEqual(second["published_count"], 1)

    def test_rejects_missing_vest_mapping_and_batch_over_five(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "publish-results.json"
            with self.assertRaisesRegex(CommentPublishError, "vest_name"):
                publish_comment_batch(
                    FakeAgent(),
                    date(2026, 8, 19),
                    {"id": "observer", "vest_name": ""},
                    [POST],
                    [COMMENT],
                    path,
                )
            with self.assertRaisesRegex(CommentPublishError, "at most 5"):
                publish_comment_batch(
                    FakeAgent(),
                    date(2026, 8, 19),
                    PROFILE,
                    [{**POST, "thread_id": str(index)} for index in range(6)],
                    [{**COMMENT, "thread_id": str(index)} for index in range(6)],
                    path,
                )

    def test_rejects_result_without_real_url_or_matching_thread(self) -> None:
        class BadAgent(FakeAgent):
            def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
                return {
                    "publish_results": [
                        {
                            "thread_id": "999",
                            "status": "published",
                            "url": "not-a-url",
                            "vest_id": "88",
                        }
                    ]
                }

        with TemporaryDirectory() as tmp:
            with self.assertRaises(CommentPublishError):
                publish_comment_batch(
                    BadAgent(),
                    date(2026, 8, 19),
                    PROFILE,
                    [POST],
                    [COMMENT],
                    Path(tmp) / "publish-results.json",
                )

    def test_preserves_qianfan_url_but_reports_source_canonical_url(self) -> None:
        class LegacyUrlAgent(FakeAgent):
            def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
                return {
                    "publish_results": [
                        {
                            "thread_id": "100",
                            "status": "published",
                            "url": "https://dayibin.cn/wap/thread/view-thread/tid/100",
                            "vest_id": "88",
                            "reply_id": "991",
                        }
                    ]
                }

        canonical_post = {
            **POST,
            "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=100",
        }
        with TemporaryDirectory() as tmp:
            result = publish_comment_batch(
                LegacyUrlAgent(),
                date(2026, 8, 19),
                PROFILE,
                [canonical_post],
                [COMMENT],
                Path(tmp) / "publish-results.json",
            )

        self.assertEqual(result["results"][0]["url"], canonical_post["url"])
        self.assertEqual(
            result["results"][0]["qianfan_url"],
            "https://dayibin.cn/wap/thread/view-thread/tid/100",
        )

    def test_floor_reply_uses_target_pid_and_is_idempotent(self) -> None:
        floor_comment = {**COMMENT, "target_reply_id": "555"}
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "reply-results.json"
            agent = FakeAgent()
            first = publish_comment_batch(
                agent,
                date(2026, 8, 19),
                PROFILE,
                [POST],
                [floor_comment],
                path,
            )
            publish_comment_batch(
                agent,
                date(2026, 8, 19),
                PROFILE,
                [POST],
                [floor_comment],
                path,
            )

        self.assertEqual(len(agent.calls), 1)
        self.assertIn('"target_reply_id": "555"', agent.calls[0][0])
        self.assertEqual(first["results"][0]["target_reply_id"], "555")

    def test_uses_direct_publisher_without_agent_script(self) -> None:
        with TemporaryDirectory() as tmp:
            agent = FakeAgent()
            publisher = FakeDirectPublisher()
            result = publish_comment_batch(
                agent,
                date(2026, 8, 19),
                PROFILE,
                [POST],
                [COMMENT],
                Path(tmp) / "publish-results.json",
                publisher=publisher,
            )

        self.assertEqual(agent.calls, [])
        self.assertEqual(len(publisher.calls), 1)
        self.assertEqual(result["results"][0]["reply_id"], "direct-991")


if __name__ == "__main__":
    unittest.main()
