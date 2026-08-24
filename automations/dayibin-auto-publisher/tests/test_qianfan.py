from datetime import UTC, date, datetime
import unittest

from dayibin_auto_publisher.qianfan import QianfanClient


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, object] | None]] = []
        self.json_bodies: list[dict[str, object]] = []

    def request_json(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, object] | None = None,
        json_body: dict[str, object] | None = None,
        timeout: int = 30,
    ) -> dict[str, object]:
        self.calls.append((method, url, params))
        if json_body is not None:
            self.json_bodies.append(json_body)
        if url.endswith("/review/thread/index"):
            return {
                "status": True,
                "code": 0,
                "data": {
                    "list": [
                        {
                            "tid": "1",
                            "pid": "11",
                            "fid": "49",
                            "fname": "大美宜宾",
                            "subject": "宜宾叙州区新增公交站",
                            "content": "叙州区通勤线路有变化，大家关心换乘距离。",
                            "dateline": "2026-08-19T07:00:00Z",
                            "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=1",
                        },
                        {
                            "tid": "2",
                            "pid": "22",
                            "fid": "49",
                            "fname": "大美宜宾",
                            "subject": "国家发布城市公共设施标准",
                            "content": "全国城市设施管理要求公开。",
                            "dateline": "2026-08-19T07:00:00Z",
                            "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=2",
                        },
                        {
                            "tid": "3",
                            "pid": "33",
                            "fid": "49",
                            "fname": "大美宜宾",
                            "subject": "宜宾某商家被曝光",
                            "content": "投诉商家欺诈并要求追责。",
                            "dateline": "2026-08-19T07:00:00Z",
                            "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=3",
                        },
                    ]
                },
            }
        if url.endswith("/review/vest-publish/info"):
            self.assert_detail_target(params)
            return {
                "status": True,
                "code": 0,
                "data": {
                    "target_id": 1,
                    "target_fid": 49,
                    "title": "宜宾叙州区新增公交站",
                    "allow_reply": 1,
                    "items_data": [
                        {
                            "type": 7,
                            "content": (
                                "<p>叙州区新增公交站后，早晚通勤的乘客会受到影响。</p>"
                                "<p>大家更关心换乘距离和高峰时段。</p>"
                            ),
                        }
                    ],
                },
            }
        if url.endswith("/review/thread/reply"):
            return {
                "status": True,
                "code": 0,
                "data": {
                    "totalPage": 1,
                    "list": [
                        {
                            "tid": "1",
                            "pid": "101",
                            "authorid": "88",
                            "subject": "宜宾新增一个充电站",
                            "content": "运营评论",
                            "fid": "67",
                            "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=1",
                            "dateline": "2026-08-20T07:00:00Z",
                        },
                        {
                            "tid": "1",
                            "pid": "102",
                            "authorid": "99",
                            "subject": "宜宾新增一个充电站",
                            "content": "服务费是重点",
                            "fid": "67",
                            "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=1",
                            "dateline": "2026-08-20T08:00:00Z",
                        },
                        {
                            "tid": "1",
                            "pid": "103",
                            "authorid": "100",
                            "subject": "宜宾新增一个充电站",
                            "content": "服务费价格是否公开？",
                            "fid": "67",
                            "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=1",
                            "dateline": "2026-08-20T08:10:00Z",
                        },
                        {
                            "tid": "2",
                            "pid": "201",
                            "authorid": "100",
                            "dateline": "2026-08-20T08:00:00Z",
                        },
                    ],
                },
            }
        if url.endswith("/system/skill-execution-log/create"):
            return {"status": True, "code": 0}
        if url.endswith("/review/vest-reply/add"):
            return {"status": True, "code": 0, "data": {"pid": "777"}}
        raise AssertionError(f"unexpected URL: {url}")

    def assert_detail_target(self, params: dict[str, object] | None) -> None:
        if params != {"target_type": 0, "target_id": "1"}:
            raise AssertionError(f"unexpected detail params: {params}")


class QianfanClientTests(unittest.TestCase):
    def test_publish_verification_uses_authoritative_list_timestamp(self) -> None:
        class MetadataTransport(FakeTransport):
            def request_json(self, method, url, **kwargs):
                if url.endswith("/review/thread/index"):
                    return {
                        "status": True,
                        "code": 0,
                        "data": {
                            "list": [
                                {
                                    "tid": "948545",
                                    "subject": "竹海周六有水上音乐，想避暑的可以看一眼",
                                    "author": "心空空情空空[马甲]",
                                    "fname": "吃喝玩乐",
                                    "dateline": "1787380089",
                                    "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=948545",
                                }
                            ]
                        },
                    }
                if url.endswith("/system/skill-execution-log/create"):
                    return {"status": True, "code": 0}
                raise AssertionError(url)

        client = QianfanClient(
            domain="https://manager.example.com",
            token="secret-token",
            transport=MetadataTransport(),
        )

        result = client.fetch_published_thread_metadata({"948545"})

        self.assertEqual(result["948545"]["vest_name"], "心空空情空空")
        self.assertEqual(result["948545"]["published_at"], "2026-08-22T14:28:09+08:00")

    def test_publish_preflight_resolves_live_vest_forum_and_optional_type(self) -> None:
        class PreflightTransport(FakeTransport):
            def request_json(self, method, url, **kwargs):
                self.calls.append((method, url, kwargs.get("params")))
                if url.endswith("/helper/admin/search-vest-option"):
                    return {
                        "status": True,
                        "code": 0,
                        "data": {
                            "list": [
                                {
                                    "id": "internal-only",
                                    "name": "forever21",
                                    "enable": 1,
                                    "desc": "",
                                }
                            ]
                        },
                    }
                if url.endswith("/bbs/forum/forum-list"):
                    return {
                        "status": True,
                        "code": 0,
                        "data": [{"fid": "49", "fname": "城市更新", "subforum": []}],
                    }
                if url.endswith("/review/vest-publish/init"):
                    return {
                        "status": True,
                        "code": 0,
                        "data": {
                            "forum_name": "城市更新",
                            "forum_type": {"required": 0, "types": []},
                        },
                    }
                if url.endswith("/system/skill-execution-log/create"):
                    return {"status": True, "code": 0}
                raise AssertionError(url)

        client = QianfanClient(
            domain="https://manager.example.com",
            token="secret-token",
            transport=PreflightTransport(),
        )

        result = client.preflight_publish_targets(
            [
                {
                    "content_id": "fact-1",
                    "title": "宜宾政务信息发布有了新变化",
                    "persona": "城市观察室型",
                    "vest_name": "forever21",
                    "forum_hint": "大宜宾APP",
                }
            ]
        )

        self.assertEqual(
            result["fact-1"],
            {
                "vest_name": "forever21",
                "vest_unique": True,
                "vest_enabled": True,
                "vest_id_present": True,
                "forum_name": "城市更新",
                "forum_unique": True,
                "forum_id_present": True,
                "type_required": False,
                "type_name": "无",
                "type_id_present": False,
            },
        )
        self.assertNotIn("internal-only", str(result))

    def test_fetches_first_page_and_details_only_safe_local_summaries(self) -> None:
        transport = FakeTransport()
        client = QianfanClient(
            domain="https://manager.example.com",
            token="secret-token",
            transport=transport,
        )

        posts = client.fetch_approved_posts(
            now=datetime(2026, 8, 19, 8, 0, tzinfo=UTC),
            lookback_hours=24,
            max_items=30,
        )

        self.assertEqual([post["thread_id"] for post in posts], ["1"])
        self.assertIn("早晚通勤", posts[0]["content"])
        list_call = transport.calls[0]
        self.assertEqual(list_call[2]["page"], 1)
        self.assertEqual(list_call[2]["perPage"], 30)
        detail_calls = [call for call in transport.calls if call[1].endswith("/review/vest-publish/info")]
        self.assertEqual(len(detail_calls), 1)

    def test_collects_aggregate_non_vest_reply_metrics_without_identities(self) -> None:
        transport = FakeTransport()
        client = QianfanClient(
            domain="https://manager.example.com",
            token="secret-token",
            transport=transport,
        )

        metrics = client.collect_reply_metrics(
            thread_ids={"1"},
            vest_ids={"88"},
            start_date="2026-08-19",
            end_date="2026-08-20",
        )

        self.assertEqual(
            metrics,
            [
                {
                    "thread_id": "1",
                    "total_reply_count": 3,
                    "non_vest_reply_count": 2,
                    "non_vest_unique_users": 2,
                }
            ],
        )
        self.assertNotIn("99", str(metrics))

    def test_fetches_only_unanswered_substantive_non_vest_replies(self) -> None:
        client = QianfanClient(
            domain="https://manager.example.com",
            token="secret-token",
            transport=FakeTransport(),
        )

        replies = client.fetch_reply_candidates(
            thread_ids={"1"},
            vest_ids={"88"},
            already_replied_ids=set(),
            start_date="2026-08-06",
            end_date="2026-08-20",
            max_items=18,
        )

        self.assertEqual([item["target_reply_id"] for item in replies], ["102"])
        self.assertEqual(replies[0]["target_comment"], "服务费是重点")
        self.assertIn("早晚通勤", replies[0]["content"])
        self.assertNotIn("authorid", replies[0])

        next_replies = client.fetch_reply_candidates(
                thread_ids={"1"},
                vest_ids={"88"},
                already_replied_ids={"102"},
                start_date="2026-08-06",
                end_date="2026-08-20",
                max_items=18,
            )
        self.assertEqual([item["target_reply_id"] for item in next_replies], ["103"])

    def test_direct_publish_uses_fixed_vest_and_target_reply_id(self) -> None:
        transport = FakeTransport()
        client = QianfanClient(
            domain="https://manager.example.com",
            token="secret-token",
            transport=transport,
        )

        result = client.publish_replies(
            vest_name="观察号",
            vest_id="88",
            business_date=date(2026, 8, 20),
            pending=[
                {
                    "thread_id": "1",
                    "fid": "49",
                    "title": "宜宾叙州区新增公交站",
                    "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=1",
                    "comment": "叙州区新增公交站值得关注。",
                    "target_reply_id": "555",
                }
            ],
        )

        self.assertEqual(result["publish_results"][0]["reply_id"], "777")
        body = next(
            body
            for body in transport.json_bodies
            if body.get("content") == "<p>叙州区新增公交站值得关注。</p>"
        )
        self.assertEqual(body["uid"], "88")
        self.assertEqual(body["vest_id"], "88")
        self.assertEqual(body["reply_id"], "555")

    def test_success_without_immediate_reply_id_is_recorded_without_retry(self) -> None:
        class DelayedReplyTransport(FakeTransport):
            def request_json(self, method, url, **kwargs):
                if url.endswith("/review/vest-reply/add"):
                    json_body = kwargs.get("json_body")
                    if json_body is not None:
                        self.json_bodies.append(json_body)
                    return {"status": True, "code": 0, "data": {}}
                return super().request_json(method, url, **kwargs)

        client = QianfanClient(
            domain="https://manager.example.com",
            token="secret-token",
            transport=DelayedReplyTransport(),
        )

        result = client.publish_replies(
            vest_name="观察号",
            vest_id="88",
            business_date=date(2026, 8, 20),
            pending=[
                {
                    "thread_id": "1",
                    "fid": "49",
                    "title": "宜宾叙州区新增公交站",
                    "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=1",
                    "comment": "叙州区新增公交站值得关注。",
                    "target_reply_id": "0",
                }
            ],
        )

        self.assertEqual(result["publish_results"][0]["status"], "published")
        self.assertEqual(result["publish_results"][0]["reply_id"], "")


if __name__ == "__main__":
    unittest.main()
