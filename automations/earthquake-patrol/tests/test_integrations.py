import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

os.environ.setdefault("EARTHQUAKE_PUBLISH_VEST_ID", "test-vest")
os.environ.setdefault("EARTHQUAKE_PUBLISH_VEST_NAME", "测试发布身份")
os.environ.setdefault("EARTHQUAKE_PUBLISH_FORUM_ID", "999")
os.environ.setdefault("EARTHQUAKE_PUBLISH_FORUM_NAME", "测试版块")

from earthquake_patrol import (
    Event,
    MapScreenshotter,
    PUBLISH_FORUM_ID,
    PUBLISH_FORUM_NAME,
    PUBLISH_VEST_ID,
    PublishOutcomeUnknown,
    QianfanClient,
    SourcesClient,
    parse_wolfx_payload,
    parse_weibo_post,
)
from wolfx_support import ReverseGeocoder


EVENT_RECORD = {
    "id": 20260710140541,
    "uniEventId": "CC1783663541000",
    "oriTime": "2026-07-10 14:05:41",
    "locName": "四川宜宾市高县",
    "epiLon": 104.699997,
    "epiLat": 28.530001,
    "focDepth": 6.0,
    "magnitude": 3.2,
}


class FakeTransport:
    def __init__(self):
        self.responses = []
        self.calls = []

    def queue(self, response):
        self.responses.append(response)

    def request_json(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if not self.responses:
            raise AssertionError(f"no response queued for {method} {url}")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def get_text(self, url, **kwargs):
        self.calls.append(("GET_TEXT", url, kwargs))
        if not self.responses:
            raise AssertionError(f"no response queued for GET_TEXT {url}")
        return self.responses.pop(0)

    def post_multipart(self, url, **kwargs):
        self.calls.append(("MULTIPART", url, kwargs))
        if not self.responses:
            raise AssertionError(f"no response queued for MULTIPART {url}")
        return self.responses.pop(0)


class WolfxTests(unittest.TestCase):
    def test_sichuan_and_cenc_payloads_share_one_normalized_event_key(self):
        common = {
            "ReportTime": "2026-08-03 13:00:52",
            "ReportNum": 1,
            "OriginTime": "2026-08-03 13:00:46",
            "HypoCenter": "四川宜宾市高县",
            "Latitude": 28.55,
            "Longitude": 104.668,
            "Depth": 0,
            "MaxIntensity": 5.8,
        }
        sc = parse_wolfx_payload(
            {
                **common,
                "type": "sc_eew",
                "ID": 8178,
                "EventID": "202608031300.0001_1",
                "Magunitude": 4.2,
            },
            now=datetime(2026, 8, 3, 13, 1, 0),
        )
        cenc = parse_wolfx_payload(
            {
                **common,
                "type": "cenc_eew",
                "ID": "b35nhoykgqcyy",
                "EventID": "202608031300.0001",
                "Magnitude": 4.2,
            },
            now=datetime(2026, 8, 3, 13, 1, 0),
        )

        self.assertEqual(sc["uniEventId"], cenc["uniEventId"])
        self.assertEqual(sc["id"], "20260803130046")
        self.assertEqual(sc["magnitude"], 4.2)
        self.assertEqual(cenc["magnitude"], 4.2)
        self.assertTrue(sc["isPreliminary"])
        self.assertEqual(sc["_source"], "wolfx_sc")
        self.assertEqual(cenc["_source"], "wolfx_cenc")

    def test_stale_wolfx_snapshot_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "stale Wolfx event"):
            parse_wolfx_payload(
                {
                    "type": "cenc_eew",
                    "EventID": "202608031300.0001",
                    "ReportTime": "2026-08-03 13:00:46",
                    "ReportNum": 1,
                    "OriginTime": "2026-08-03 13:00:46",
                    "HypoCenter": "四川宜宾市高县",
                    "Latitude": 28.55,
                    "Longitude": 104.668,
                    "Magnitude": 4.2,
                    "Depth": 5,
                },
                now=datetime(2026, 8, 3, 13, 10, 0),
            )

    def test_wolfx_report_number_is_required(self):
        with self.assertRaisesRegex(ValueError, "report number"):
            parse_wolfx_payload(
                {
                    "type": "cenc_eew",
                    "EventID": "202608031300.0001",
                    "ReportTime": "2026-08-03 13:00:46",
                    "OriginTime": "2026-08-03 13:00:46",
                    "HypoCenter": "四川宜宾市高县",
                    "Latitude": 28.55,
                    "Longitude": 104.668,
                    "Magnitude": 4.2,
                    "Depth": 5,
                },
                now=datetime(2026, 8, 3, 13, 1, 0),
            )

    def test_reverse_geocoder_requires_yibin_and_returns_precise_name(self):
        transport = FakeTransport()
        transport.queue(
            {
                "status": 0,
                "result": {
                    "formatted_address_poi": "四川省宜宾市高县胜天镇流米村",
                    "addressComponent": {
                        "province": "四川省",
                        "city": "宜宾市",
                        "district": "高县",
                        "town": "胜天镇",
                        "village": "流米村",
                    },
                    "poiRegions": [],
                    "pois": [],
                },
            }
        )
        geocoder = ReverseGeocoder("test-ak", transport)

        self.assertEqual(geocoder.reverse(28.55, 104.668), "胜天镇流米村")
        call = transport.calls[0]
        self.assertTrue(call[1].endswith("/reverse_geocoding/v3/"))
        self.assertEqual(call[2]["params"]["coordtype"], "wgs84ll")
        self.assertEqual(call[2]["params"]["location"], "28.550000,104.668000")

    def test_reverse_geocoder_ignores_distant_poi_and_falls_back_to_county(self):
        transport = FakeTransport()
        transport.queue(
            {
                "status": 0,
                "result": {
                    "addressComponent": {
                        "province": "四川省",
                        "city": "宜宾市",
                        "district": "高县",
                        "town": "",
                        "village": "",
                        "street": "",
                    },
                    "poiRegions": [],
                    "pois": [{"name": "某学校", "distance": "200"}],
                },
            }
        )

        self.assertEqual(
            ReverseGeocoder("test-ak", transport).reverse(28.55, 104.668),
            "四川宜宾市高县",
        )

    def test_reverse_geocoder_removes_nearby_from_county_fallback(self):
        transport = FakeTransport()
        transport.queue(
            {
                "status": 0,
                "result": {
                    "addressComponent": {
                        "province": "四川省",
                        "city": "宜宾市",
                        "district": "高县附近",
                        "town": "",
                        "village": "",
                        "street": "",
                    },
                    "poiRegions": [],
                    "pois": [],
                },
            }
        )

        self.assertEqual(
            ReverseGeocoder("test-ak", transport).reverse(28.55, 104.668),
            "四川宜宾市高县",
        )


class WolfxListenerTests(unittest.TestCase):
    def test_listener_self_test_has_two_channels_and_safe_default(self):
        script = Path(__file__).parents[1] / "scripts" / "wolfx-listener.js"
        completed = subprocess.run(
            ["node", str(script), "--self-test"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertFalse(payload["publishEnabled"])
        self.assertEqual(
            {item["channel"] for item in payload["endpoints"]},
            {"sc_eew", "cenc_eew"},
        )
        self.assertEqual(payload["backoffSeconds"], [1, 2, 30])

class QianfanClientTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.config = Path(self.tempdir.name) / "config.json"
        self.config.write_text(
            json.dumps(
                {
                    "domain": "https://dayibin.manager.qianfanyun.com",
                    "username": "employee",
                    "password": "not-a-real-password",
                    "token": "test-token",
                }
            ),
            encoding="utf-8",
        )
        self.transport = FakeTransport()
        self.client = QianfanClient(self.config, self.transport)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_disabled_exact_vest_blocks_and_logs_operation(self):
        self.transport.queue(
            {
                "status": True,
                "code": 0,
                "data": {
                    "list": [
                        {
                            "id": "24505",
                            "name": "Luck",
                            "enable": 0,
                            "desc": "该马甲已被流浪本浪绑定",
                        }
                    ]
                },
            }
        )
        self.transport.queue({"status": True, "code": 0, "data": {"id": 1}})

        with self.assertRaisesRegex(PermissionError, "流浪本浪"):
            self.client.assert_vest_enabled("24505", "Luck")

        self.assertIn("/helper/admin/search-vest-option", self.transport.calls[0][1])
        self.assertIn("/system/skill-execution-log/create", self.transport.calls[1][1])
        logged = self.transport.calls[1][2]["json_body"]
        self.assertEqual(logged["execution_result"], 0)
        self.assertNotIn("not-a-real-password", json.dumps(logged))
        self.assertNotIn("test-token", json.dumps(logged))

    def test_expired_token_is_refreshed_once_before_vest_check(self):
        self.transport.queue(RuntimeError('HTTP 401: {"msg":"invalid credentials"}'))
        self.transport.queue(
            {
                "ret": 0,
                "msg": "登录成功",
                "data": {"token": "refreshed-token"},
            }
        )
        self.transport.queue(
            {
                "status": True,
                "code": 0,
                "data": {
                    "list": [
                        {
                            "id": PUBLISH_VEST_ID,
                            "name": "测试发布身份",
                            "enable": 1,
                        }
                    ]
                },
            }
        )
        self.transport.queue({"status": True, "code": 0, "data": {"id": 2}})

        self.client.assert_vest_enabled(PUBLISH_VEST_ID, "测试发布身份")

        urls = [call[1] for call in self.transport.calls]
        self.assertEqual(urls[:3], [
            "https://dayibin.manager.qianfanyun.com/helper/admin/search-vest-option",
            "https://dayibin.manager.qianfanyun.com/index/login",
            "https://dayibin.manager.qianfanyun.com/helper/admin/search-vest-option",
        ])
        saved = json.loads(self.config.read_text(encoding="utf-8"))
        self.assertEqual(saved["token"], "refreshed-token")
        self.assertEqual(self.client.token, "refreshed-token")
        retried_headers = self.transport.calls[2][2]["headers"]
        self.assertEqual(retried_headers["Authorization"], "Bearer refreshed-token")

    def test_forum_without_required_type_uses_sid_zero(self):
        self.transport.queue(
            {
                "status": True,
                "code": 0,
                "data": {
                    "forum_name": "测试版块",
                    "forum_type": {"required": 0, "types": []},
                },
            }
        )
        self.transport.queue({"status": True, "code": 0, "data": {"id": 2}})
        forum = self.client.resolve_forum(PUBLISH_FORUM_ID)
        self.assertEqual(
            forum,
            {"fid": "999", "sid": 0, "name": PUBLISH_FORUM_NAME},
        )

    def test_ambiguous_publish_logs_failure_and_never_retries(self):
        self.transport.queue(TimeoutError("timeout"))
        self.transport.queue({"status": True, "code": 0, "data": {"id": 3}})
        event = Event.from_record(EVENT_RECORD)

        with self.assertRaises(PublishOutcomeUnknown):
            self.client.publish(
                event,
                "title",
                "<p>body</p>",
                "https://pic.example/map.png",
                {"fid": "2", "sid": 0, "name": "今日宜宾"},
            )

        publish_calls = [
            call for call in self.transport.calls if "/review/vest-publish/add" in call[1]
        ]
        self.assertEqual(len(publish_calls), 1)
        self.assertEqual(publish_calls[0][2]["json_body"]["vest_id"], PUBLISH_VEST_ID)

    def test_upload_accepts_current_upload_token_field(self):
        image = Path(self.tempdir.name) / "map.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 5000)
        self.transport.queue(
            {
                "status": True,
                "code": 0,
                "data": {"upload_token": "qiniu-token"},
            }
        )
        self.transport.queue({"status": True, "code": 0, "data": {"id": 4}})
        self.transport.queue({"name": "https://pic.example/map.png"})
        self.transport.queue({"status": True, "code": 0, "data": {"id": 5}})

        uploaded = self.client.upload_image(image)

        self.assertEqual(uploaded, "https://pic.example/map.png")

    def test_push_post_checks_quota_then_creates_immediate_post_push(self):
        event = Event.from_record(EVENT_RECORD)
        self.transport.queue(
            {
                "status": True,
                "code": 0,
                "data": {
                    "id": 188203,
                    "title": "14点05分！宜宾高县发生3.2级地震！",
                    "items_data": [
                        {
                            "content": "中国地震台网正式测定：7月10日14时05分在四川宜宾市高县发生3.2级地震。"
                        }
                    ],
                },
            }
        )
        self.transport.queue({"status": True, "code": 0, "data": {"id": 5}})
        self.transport.queue(
            {"status": True, "code": 0, "data": {"broadcast_over_limit": 0, "can_use": 1}}
        )
        self.transport.queue({"status": True, "code": 0, "data": {"id": 6}})
        self.transport.queue({"status": True, "code": 0, "data": {"id": 9001}})
        self.transport.queue({"status": True, "code": 0, "data": {"id": 7}})

        result = self.client.push_post(
            "123456", event, "https://pic.example/map.png"
        )

        create = [call for call in self.transport.calls if call[1].endswith("/push/create")]
        self.assertEqual(len(create), 1)
        body = create[0][2]["json_body"]
        self.assertEqual(body["target_type"], "10")
        self.assertEqual(body["target_value"], "123456")
        self.assertEqual(body["method"], "0")
        self.assertIn(
            body["content"],
            {
                "预警首报，稍后更新",
                "初步定位，持续更新",
                "首报数据，稍后更新",
                "正式结果稍后更新",
                "初步测定，结果待定",
                "正式测定稍后更新",
                "参数初报，持续更新",
                "正式测定结果待更新",
            },
        )
        self.assertLessEqual(len(body["title"]), 20)
        self.assertLessEqual(len(body["content"]), 10)
        self.assertNotIn("四川", body["title"])
        self.assertEqual(body["image"], "https://pic.example/map.png")
        self.assertNotIn("limit_view_time", body)
        self.assertEqual(result["id"], 9001)

    def test_push_rejects_missing_or_non_https_image_before_api_calls(self):
        event = Event.from_record(EVENT_RECORD)

        for image_url in ("", "http://pic.example/map.png"):
            with self.subTest(image_url=image_url):
                with self.assertRaisesRegex(ValueError, "push image URL"):
                    self.client.push_post("123456", event, image_url)

        self.assertEqual(self.transport.calls, [])

    def test_push_rejects_target_post_with_wrong_magnitude(self):
        event = Event.from_record(EVENT_RECORD)
        self.transport.queue(
            {
                "status": True,
                "code": 0,
                "data": {
                    "id": 188203,
                    "title": "14点05分！宜宾高县发生3.9级地震！",
                    "items_data": [
                        {
                            "content": "中国地震台网正式测定：7月10日14时05分在四川宜宾市高县发生3.9级地震。"
                        }
                    ],
                },
            }
        )
        self.transport.queue({"status": True, "code": 0, "data": {"id": 8}})

        with self.assertRaisesRegex(RuntimeError, "magnitude"):
            self.client.push_post(
                "123456", event, "https://pic.example/map.png"
            )

        self.assertFalse(
            any(call[1].endswith("/push/create") for call in self.transport.calls)
        )
        self.assertFalse(
            any(call[1].endswith("/push/can-use") for call in self.transport.calls)
        )

    def test_push_rejects_target_post_with_wrong_time(self):
        event = Event.from_record(EVENT_RECORD)
        self.transport.queue(
            {
                "status": True,
                "code": 0,
                "data": {
                    "id": 188203,
                    "title": "15点05分！宜宾高县发生3.2级地震！",
                    "items_data": [
                        {
                            "content": "中国地震台网正式测定：7月10日15时05分在四川宜宾市高县发生3.2级地震。"
                        }
                    ],
                },
            }
        )
        self.transport.queue({"status": True, "code": 0, "data": {"id": 9}})

        with self.assertRaisesRegex(RuntimeError, "occurred_at"):
            self.client.push_post(
                "123456", event, "https://pic.example/map.png"
            )

        self.assertFalse(
            any(call[1].endswith("/push/create") for call in self.transport.calls)
        )

    def test_push_rejects_target_post_with_wrong_location(self):
        event = Event.from_record(EVENT_RECORD)
        self.transport.queue(
            {
                "status": True,
                "code": 0,
                "data": {
                    "id": 188203,
                    "title": "14点05分！宜宾珙县发生3.2级地震！",
                    "items_data": [
                        {
                            "content": "中国地震台网正式测定：7月10日14时05分在四川宜宾市珙县发生3.2级地震。"
                        }
                    ],
                },
            }
        )
        self.transport.queue({"status": True, "code": 0, "data": {"id": 10}})

        with self.assertRaisesRegex(RuntimeError, "location"):
            self.client.push_post(
                "123456", event, "https://pic.example/map.png"
            )

        self.assertFalse(
            any(call[1].endswith("/push/create") for call in self.transport.calls)
        )

    def test_push_http_failure_is_logged(self):
        event = Event.from_record(EVENT_RECORD)
        self.transport.queue(
            {
                "status": True,
                "code": 0,
                "data": {
                    "id": 188203,
                    "title": "14点05分！宜宾高县发生3.2级地震！",
                    "items_data": [
                        {
                            "content": "中国地震台网正式测定：7月10日14时05分在四川宜宾市高县发生3.2级地震。"
                        }
                    ],
                },
            }
        )
        self.transport.queue({"status": True, "code": 0, "data": {"id": 11}})
        self.transport.queue(
            {"status": True, "code": 0, "data": {"broadcast_over_limit": 0, "can_use": 1}}
        )
        self.transport.queue({"status": True, "code": 0, "data": {"id": 12}})
        self.transport.queue(RuntimeError("HTTP 422: validation failed"))
        self.transport.queue({"status": True, "code": 0, "data": {"id": 13}})

        with self.assertRaisesRegex(RuntimeError, "422"):
            self.client.push_post(
                "945582", event, "https://pic.example/map.png"
            )

        logs = [
            call[2]["json_body"]
            for call in self.transport.calls
            if call[1].endswith("/system/skill-execution-log/create")
        ]
        self.assertEqual(logs[-1]["action_type"], "APP推送")
        self.assertEqual(logs[-1]["execution_result"], 0)


class SourcesClientTests(unittest.TestCase):
    def test_weibo_is_the_only_publish_trigger_when_configured(self):
        transport = FakeTransport()
        transport.queue(
            {"success": True, "code": 200, "data": {"records": [EVENT_RECORD]}}
        )

        class FakeWeiboSource:
            status = {"status": "ok"}

            def fetch_records(self):
                return [dict(EVENT_RECORD, uniEventId="WB5199999999999999", _source="weibo")]

        records = SourcesClient(transport, FakeWeiboSource()).fetch_catalog()

        self.assertEqual([record["uniEventId"] for record in records], ["WB5199999999999999"])

    def test_cenc_403_does_not_block_the_weibo_publish_trigger(self):
        transport = FakeTransport()
        transport.queue(RuntimeError("HTTP 403: upstream protection page"))
        transport.queue((200, "中国地震台网中心"))

        class FakeWeiboSource:
            status = {"status": "ok"}

            def fetch_records(self):
                return [dict(EVENT_RECORD, uniEventId="WB5199999999999999", _source="weibo")]

        sources = SourcesClient(transport, FakeWeiboSource())

        records = sources.fetch_catalog()
        health = sources.check_secondary()

        self.assertEqual([record["uniEventId"] for record in records], ["WB5199999999999999"])
        self.assertFalse(health["cenc_catalog"]["ok"])
        self.assertIn("HTTP 403", health["cenc_catalog"]["error"])
        self.assertEqual(health["weibo"], {"status": "ok"})

    def test_weibo_read_failure_fails_instead_of_looking_like_no_new_event(self):
        transport = FakeTransport()

        class FailingWeiboSource:
            status = {"status": "not_checked"}

            def fetch_records(self):
                raise RuntimeError("browser session crashed")

        source = FailingWeiboSource()

        with self.assertRaisesRegex(RuntimeError, "Weibo publish trigger unavailable"):
            SourcesClient(transport, source).fetch_catalog()

        self.assertEqual(source.status["status"], "error")

    def test_weibo_login_required_fails_so_cron_alerts_can_fire(self):
        transport = FakeTransport()

        class LoggedOutWeiboSource:
            status = {"status": "not_checked"}

            def fetch_records(self):
                self.status = {"status": "login_required"}
                return []

        with self.assertRaisesRegex(RuntimeError, "login_required"):
            SourcesClient(transport, LoggedOutWeiboSource()).fetch_catalog()

    def test_catalog_and_secondary_are_both_polled(self):
        transport = FakeTransport()
        transport.queue(
            {"success": True, "code": 200, "data": {"records": [EVENT_RECORD]}}
        )
        transport.queue((200, "中国地震台网中心"))
        sources = SourcesClient(transport)

        records = sources.fetch_catalog()
        health = sources.check_secondary()

        self.assertEqual(records[0]["uniEventId"], "CC1783663541000")
        self.assertTrue(health["ok"])
        self.assertEqual(len(transport.calls), 2)

    def test_formal_yibin_weibo_is_converted_to_catalog_record(self):
        post = {
            "idstr": "5199999999999999",
            "created_at": "Fri Jul 10 17:40:00 +0800 2026",
            "text_raw": "#地震快讯#中国地震台网正式测定：07月10日17时38分在四川宜宾市高县（北纬28.52度，东经104.67度）发生3.3级地震，震源深度5千米。",
        }
        record = parse_weibo_post(post)
        self.assertEqual(record["uniEventId"], "WB5199999999999999")
        self.assertEqual(record["oriTime"], "2026-07-10 17:38:00")
        self.assertEqual(record["locName"], "四川宜宾市高县")
        self.assertEqual(record["epiLat"], 28.52)
        self.assertEqual(record["epiLon"], 104.67)

    def test_automatic_yibin_is_preliminary_and_non_yibin_is_ignored(self):
        automatic = {
            "idstr": "1",
            "created_at": "Fri Jul 10 17:39:00 +0800 2026",
            "text_raw": "#地震快讯#中国地震台网自动测定：07月10日17时38分在四川宜宾市高县附近（北纬28.52度，东经104.67度）发生3.3级左右地震，最终结果以正式速报为准。",
        }
        outside = {
            "idstr": "2",
            "created_at": "Fri Jul 10 17:40:00 +0800 2026",
            "text_raw": "#地震快讯#中国地震台网正式测定：07月10日17时38分在四川泸州市江阳区（北纬28.52度，东经105.44度）发生3.3级地震，震源深度5千米。",
        }
        record = parse_weibo_post(automatic)
        self.assertTrue(record["isPreliminary"])
        self.assertIsNone(record["focDepth"])
        self.assertIsNone(parse_weibo_post(outside))


class MapScreenshotterTests(unittest.TestCase):
    def test_static_map_preserves_wgs84_coordinates_at_local_zoom(self):
        script = Path(__file__).parents[1] / "scripts" / "screenshot-map.js"
        event = {
            "location": "四川宜宾市高县",
            "longitude": 104.699997,
            "latitude": 28.530001,
        }
        completed = subprocess.run(
            [
                "node",
                "-e",
                (
                    "const map = require(process.argv[1]);"
                    "const request = map.buildStaticMapRequest("
                    "JSON.parse(process.argv[2]));"
                    "process.stdout.write(JSON.stringify(request));"
                ),
                str(script),
                json.dumps(event, ensure_ascii=False),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        request = json.loads(completed.stdout)
        self.assertEqual(request["center"], "104.699997,28.530001")
        self.assertEqual(request["params"]["coordtype"], "wgs84ll")
        self.assertEqual(request["params"]["zoom"], "11")
        self.assertEqual(request["params"]["markerStyles"], "l,M,0xe64545")

    def test_capture_uses_allowlisted_cenc_event_url(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "scripts").mkdir()
            (root / "scripts" / "screenshot-map.js").write_text(
                "// test fixture", encoding="utf-8"
            )

            def fake_runner(command, **kwargs):
                output = Path(command[-1])
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 5000)

                class Result:
                    returncode = 0
                    stdout = '{"status":"ok"}'
                    stderr = ""

                return Result()

            screenshotter = MapScreenshotter(root, runner=fake_runner)
            path = screenshotter.capture(Event.from_record(EVENT_RECORD))

            self.assertTrue(path.is_file())
            self.assertIn("20260710140541", path.name)


if __name__ == "__main__":
    unittest.main()
