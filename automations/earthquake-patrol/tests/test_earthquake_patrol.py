import os
import tempfile
import unittest
import sqlite3
from pathlib import Path

os.environ.setdefault("EARTHQUAKE_PUBLISH_VEST_ID", "test-vest")
os.environ.setdefault("EARTHQUAKE_PUBLISH_VEST_NAME", "测试发布身份")
os.environ.setdefault("EARTHQUAKE_PUBLISH_FORUM_ID", "999")
os.environ.setdefault("EARTHQUAKE_PUBLISH_FORUM_NAME", "测试版块")

import earthquake_patrol as patrol
from earthquake_patrol import (
    Event,
    PatrolService,
    PublishOutcomeUnknown,
    StateStore,
    build_body_html,
    build_push_copy,
    format_body,
    format_title,
    is_yibin,
    redact_secrets,
)


CURRENT = {
    "id": 20260710140541,
    "uniEventId": "CC1783663541000",
    "oriTime": "2026-07-10 14:05:41",
    "locName": "四川宜宾市高县",
    "epiLon": 104.699997,
    "epiLat": 28.530001,
    "focDepth": 6.0,
    "magnitude": 3.2,
}

NEW_EVENT = {
    "id": 20260710180541,
    "uniEventId": "CC1783677941000",
    "oriTime": "2026-07-10 18:05:41",
    "locName": "四川宜宾市珙县",
    "epiLon": 104.71,
    "epiLat": 28.44,
    "focDepth": 8.0,
    "magnitude": 2.8,
}

LOW_PUSH_TITLE_TEMPLATES = (
    "刚刚，{short_location}发生{magnitude}级地震",
    "{short_location}地震预警，{magnitude}级",
    "【地震快讯】{city_location}初估{magnitude}级",
    "{short_location}地震预警，初估{magnitude}级",
    "{short_location}发生{magnitude}级地震",
    "刚刚！{short_location}{magnitude}级地震",
    "{magnitude}级！震中{city_location}",
    "{city_location}初估{magnitude}级地震",
)
LOW_PUSH_CONTENTS = (
    "预警首报，稍后更新",
    "初步定位，持续更新",
    "首报数据，稍后更新",
    "正式结果稍后更新",
    "初步测定，结果待定",
    "正式测定稍后更新",
    "参数初报，持续更新",
    "正式测定结果待更新",
)
HIGH_PUSH_TITLE_TEMPLATES = (
    "{magnitude}级！{short_location}发生地震",
    "刚刚，{short_location}发生{magnitude}级地震",
    "【地震快讯】{short_location}{magnitude}级",
    "{short_location}{magnitude}级地震！",
    "{city_location}发生{magnitude}级地震",
    "{magnitude}级地震！震中{short_location}",
    "{short_location}突发{magnitude}级地震",
    "{short_location}地震，初估{magnitude}级",
)
HIGH_PUSH_CONTENTS = (
    "请注意安全，谨慎避险",
    "保持冷静，注意避险",
    "正式测定结果稍后更新",
    "如有震感，请注意安全",
    "远离玻璃，注意落物",
    "参数初报，持续更新",
    "正式结果稍后更新",
)


def expected_push_titles(templates, magnitude, suffix="高县"):
    values = {
        "short_location": f"宜宾{suffix}",
        "city_location": f"宜宾市{suffix}",
        "magnitude": f"{magnitude:.1f}",
    }
    return {template.format(**values) for template in templates}


class FakeSources:
    def __init__(self, records):
        self.records = list(records)
        self.secondary_checks = 0

    def fetch_catalog(self):
        return list(self.records)

    def check_secondary(self):
        self.secondary_checks += 1
        return {"ok": True, "status": 200}


class FakeScreenshotter:
    def __init__(self, output: Path, fail=False):
        self.output = output
        self.fail = fail
        self.calls = 0

    def capture(self, event):
        self.calls += 1
        if self.fail:
            raise RuntimeError("screenshot failed")
        self.output.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 5000)
        return self.output


class FakeQianfan:
    def __init__(self, *, vest_enabled=True, duplicate=False, ambiguous=False):
        self.vest_enabled = vest_enabled
        self.duplicate = duplicate
        self.ambiguous = ambiguous
        self.duplicate_checks = 0
        self.uploads = 0
        self.publish_calls = 0
        self.update_calls = 0
        self.push_calls = 0
        self.push_image_urls = []
        self.update_image_urls = []
        self.resolved_forum_ids = []

    def assert_vest_enabled(self, vest_id, vest_name):
        if not self.vest_enabled:
            raise PermissionError(f"{vest_name}/{vest_id} unavailable")

    def resolve_forum(self, fid):
        self.resolved_forum_ids.append(fid)
        return {"fid": str(fid), "sid": 0, "name": patrol.PUBLISH_FORUM_NAME}

    def find_duplicate(self, event, title):
        self.duplicate_checks += 1
        return {"tid": "945552"} if self.duplicate else None

    def upload_image(self, path):
        self.uploads += 1
        return "https://pic.example/earthquake.png"

    def publish(self, event, title, body_html, image_url, forum):
        self.publish_calls += 1
        if self.ambiguous:
            raise PublishOutcomeUnknown("timeout")
        return {"tid": "999999"}

    def update_post(self, tid, event, title, body_html, image_url, forum):
        self.update_calls += 1
        self.update_image_urls.append(image_url)
        return {"tid": str(tid)}

    def push_post(self, tid, event, image_url):
        self.push_calls += 1
        self.push_image_urls.append(image_url)
        return {"id": "push-1"}


class FormattingTests(unittest.TestCase):
    def test_yibin_scope_requires_official_yibin_prefix(self):
        self.assertTrue(is_yibin(Event.from_record(CURRENT)))
        outside = dict(CURRENT, locName="四川泸州市江阳区")
        self.assertFalse(is_yibin(Event.from_record(outside)))

    def test_reference_style_copy_is_deterministic(self):
        event = Event.from_record(CURRENT)
        self.assertEqual(format_title(event), "14点05分！宜宾高县发生3.2级地震！")
        self.assertEqual(
            format_body(event),
            "中国地震台网正式测定：7月10日14时05分在四川宜宾市高县（北纬28.53度，东经104.70度）发生3.2级地震，震源深度6千米。",
        )
        html = build_body_html(event, "https://pic.example/map.png")
        self.assertIn("<img", html)
        self.assertIn("来源：中国地震台网中心", html)

    def test_redaction_removes_passwords_and_tokens(self):
        text = 'password=secret token="abc.def" Authorization: Bearer xyz'
        redacted = redact_secrets(text)
        self.assertNotIn("secret", redacted)
        self.assertNotIn("abc.def", redacted)
        self.assertNotIn("Bearer xyz", redacted)

    def test_preliminary_weibo_copy_is_explicitly_uncertain(self):
        preliminary = dict(
            NEW_EVENT,
            focDepth=None,
            isPreliminary=True,
            _source="weibo",
        )
        event = Event.from_record(preliminary)
        self.assertEqual(format_title(event), "18点05分！宜宾珙县发生2.8级左右地震！")
        body = format_body(event)
        self.assertIn("自动测定", body)
        self.assertIn("最终结果以正式速报为准", body)
        self.assertNotIn("震源深度", body)

    def test_push_uses_approved_copy_pools_at_four_point_zero_boundary(self):
        cases = (
            (3.9, LOW_PUSH_TITLE_TEMPLATES, set(LOW_PUSH_CONTENTS)),
            (4.0, HIGH_PUSH_TITLE_TEMPLATES, set(HIGH_PUSH_CONTENTS)),
        )
        for magnitude, title_templates, contents in cases:
            with self.subTest(magnitude=magnitude):
                event = Event.from_record(
                    dict(
                        NEW_EVENT,
                        uniEventId=f"BOUNDARY-{round(magnitude * 10)}",
                        oriTime="2026-07-10 19:48:00",
                        locName="四川宜宾市高县",
                        magnitude=magnitude,
                        focDepth=None,
                        isPreliminary=True,
                        _source="weibo",
                    )
                )
                title, content = build_push_copy(event)
                self.assertIn(
                    title,
                    expected_push_titles(title_templates, magnitude),
                )
                self.assertIn(content, contents)
                self.assertNotIn("四川", title)
                self.assertLessEqual(len(title), 20)
                self.assertLessEqual(len(content), 10)

        high_title, high_content = build_push_copy(
            Event.from_record(
                dict(
                    NEW_EVENT,
                    uniEventId="HIGH-CONTENT-GATE",
                    locName="四川宜宾市高县",
                    magnitude=5.2,
                    focDepth=None,
                    isPreliminary=True,
                    _source="weibo",
                )
            )
        )
        self.assertIn(high_title, expected_push_titles(HIGH_PUSH_TITLE_TEMPLATES, 5.2))
        self.assertIn(high_content, HIGH_PUSH_CONTENTS)
        self.assertNotEqual(high_content, "请勿乘坐电梯")

    def test_push_title_and_content_pools_combine_independently_and_stably(self):
        cases = (
            (3.6, LOW_PUSH_TITLE_TEMPLATES, set(LOW_PUSH_CONTENTS)),
            (5.2, HIGH_PUSH_TITLE_TEMPLATES, set(HIGH_PUSH_CONTENTS)),
        )
        for magnitude, title_templates, expected_contents in cases:
            with self.subTest(magnitude=magnitude):
                expected_titles = expected_push_titles(title_templates, magnitude)
                observed_titles = set()
                observed_contents = set()
                observed_pairs = set()
                for index in range(4096):
                    event = Event.from_record(
                        dict(
                            NEW_EVENT,
                            uniEventId=f"POOL-{round(magnitude * 10)}-{index:04d}",
                            locName="四川宜宾市高县",
                            magnitude=magnitude,
                            focDepth=None,
                            isPreliminary=True,
                            _source="weibo",
                        )
                    )
                    pair = build_push_copy(event)
                    self.assertEqual(build_push_copy(event), pair)
                    observed_titles.add(pair[0])
                    observed_contents.add(pair[1])
                    observed_pairs.add(pair)
                    if (
                        observed_titles == expected_titles
                        and observed_contents == expected_contents
                        and len(observed_pairs) > 8
                    ):
                        break

                self.assertEqual(observed_titles, expected_titles)
                self.assertEqual(observed_contents, expected_contents)
                self.assertGreater(len(observed_pairs), 8)

    def test_wolfx_push_strips_sichuan_and_uses_approved_copy(self):
        event = Event.from_record(
            dict(
                NEW_EVENT,
                uniEventId="WX202608031300_0001",
                oriTime="2026-08-03 13:00:46",
                locName="四川宜宾市高县",
                magnitude=4.2,
                focDepth=0,
                isPreliminary=True,
                preciseLocation="四川宜宾市高县",
                _source="wolfx_cenc",
            )
        )

        first = build_push_copy(event)
        self.assertEqual(build_push_copy(event), first)
        self.assertIn(first[0], expected_push_titles(HIGH_PUSH_TITLE_TEMPLATES, 4.2))
        self.assertIn(first[1], HIGH_PUSH_CONTENTS)
        self.assertIn("宜宾", first[0])
        self.assertNotIn("四川", first[0])
        self.assertNotIn("附近", first[0])
        self.assertLessEqual(len(first[0]), 20)
        self.assertLessEqual(len(first[1]), 10)

    def test_wolfx_body_is_clearly_preliminary_and_adds_safety_copy(self):
        event = Event.from_record(
            dict(
                NEW_EVENT,
                uniEventId="WX202608031300_0001",
                oriTime="2026-08-03 13:00:46",
                locName="四川宜宾市高县",
                magnitude=4.2,
                focDepth=0,
                isPreliminary=True,
                preciseLocation="胜天镇",
                _source="wolfx_cenc",
            )
        )

        body = format_body(event)
        html = build_body_html(event, "https://pic.example/map.png")

        self.assertIn("地震预警系统初步测算", body)
        self.assertIn("最终以中国地震台网正式测定为准", body)
        self.assertIn("来源：Wolfx 地震预警数据", html)
        self.assertIn("室内就近伏低、遮挡、抓牢", html)
        self.assertIn("室外到开阔处", html)


class PatrolTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.store = StateStore(root / "state.sqlite3")
        self.shot = FakeScreenshotter(root / "shot.png")

    def tearDown(self):
        self.store.close()
        self.tempdir.cleanup()

    def service(
        self,
        sources,
        qianfan,
        screenshotter=None,
        push_enabled=False,
        geocoder=None,
    ):
        return PatrolService(
            sources=sources,
            qianfan=qianfan,
            screenshotter=screenshotter or self.shot,
            store=self.store,
            vest_id="24505",
            vest_name="Luck",
            forum_id=patrol.PUBLISH_FORUM_ID,
            push_enabled=push_enabled,
            geocoder=geocoder,
        )

    def test_runtime_push_is_enabled(self):
        self.assertTrue(patrol.PUSH_ENABLED)

    def test_runtime_forum_uses_environment_config(self):
        self.assertEqual(getattr(patrol, "PUBLISH_FORUM_ID", None), 999)
        self.assertEqual(getattr(patrol, "PUBLISH_FORUM_NAME", None), "测试版块")

    def test_state_store_migrates_existing_database_without_losing_rows(self):
        path = Path(self.tempdir.name) / "legacy.sqlite3"
        connection = sqlite3.connect(str(path))
        connection.executescript(
            """
            CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE events (
                event_key TEXT PRIMARY KEY,
                catalog_id TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                location TEXT NOT NULL,
                magnitude REAL NOT NULL,
                status TEXT NOT NULL,
                post_tid TEXT,
                error TEXT,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE observed_events (
                event_key TEXT PRIMARY KEY,
                observed_at TEXT NOT NULL
            );
            INSERT INTO events VALUES (
                'legacy', '20260710140541', 'fingerprint',
                '2026-07-10 14:05:41', '四川宜宾市高县', 3.2,
                'published', '123456', NULL, '2026-07-10T14:06:00'
            );
            """
        )
        connection.commit()
        connection.close()

        migrated = StateStore(path)
        columns = {
            row["name"]
            for row in migrated.connection.execute("PRAGMA table_info(events)")
        }
        row = migrated.connection.execute(
            "SELECT event_key, post_tid FROM events WHERE event_key='legacy'"
        ).fetchone()
        migrated.close()

        self.assertIn("image_url", columns)
        self.assertIn("precise_location", columns)
        self.assertEqual(dict(row), {"event_key": "legacy", "post_tid": "123456"})

    def test_push_policy_uses_magnitude_within_six_hour_window(self):
        self.store.record_push("945764", 3.8, now=1000)

        self.assertFalse(self.store.can_push(3.8, now=1001))
        self.assertFalse(self.store.can_push(4.7, now=1001))
        self.assertTrue(self.store.can_push(4.8, now=1001))
        self.assertTrue(self.store.can_push(3.7, now=22601))

    def test_push_is_disabled_without_blocking_post_publication(self):
        baseline = dict(CURRENT, locName="四川泸州市江阳区")
        sources = FakeSources([baseline])
        qianfan = FakeQianfan()
        service = self.service(sources, qianfan, push_enabled=False)
        service.run_once()
        sources.records.insert(0, dict(NEW_EVENT, isPreliminary=True, _source="weibo"))

        result = service.run_once()

        self.assertEqual(result["events"][0]["status"], "published_preliminary")
        self.assertEqual(result["events"][0]["push_status"], "disabled")
        self.assertEqual(qianfan.push_calls, 0)
        self.assertEqual(qianfan.resolved_forum_ids, [999])

    def test_first_run_seeds_current_catalog_without_publishing(self):
        sources = FakeSources([CURRENT])
        qianfan = FakeQianfan()
        result = self.service(sources, qianfan).run_once()
        self.assertEqual(result["status"], "baseline_seeded")
        self.assertEqual(qianfan.publish_calls, 0)
        self.assertEqual(self.store.event_status("CC1783663541000"), "baseline")

        second = self.service(sources, qianfan).run_once()
        self.assertEqual(second["processed"], 0)
        self.assertEqual(qianfan.publish_calls, 0)

    def test_observed_event_key_is_not_reprocessed_without_event_row(self):
        event = Event.from_record(NEW_EVENT)
        self.store.mark_observed(event.key)
        self.assertFalse(self.store.should_process(event))

    def test_existing_dayibin_post_skips_before_screenshot(self):
        sources = FakeSources([CURRENT])
        qianfan = FakeQianfan(duplicate=True)
        service = self.service(sources, qianfan)
        service.run_once()
        sources.records.insert(0, NEW_EVENT)

        result = service.run_once()
        self.assertEqual(result["events"][0]["status"], "skipped_existing")
        self.assertEqual(self.shot.calls, 0)
        self.assertEqual(qianfan.publish_calls, 0)

    def test_disabled_luck_blocks_before_screenshot_or_upload(self):
        sources = FakeSources([CURRENT])
        qianfan = FakeQianfan(vest_enabled=False)
        service = self.service(sources, qianfan)
        service.run_once()
        sources.records.insert(0, NEW_EVENT)

        result = service.run_once()
        self.assertEqual(result["events"][0]["status"], "blocked_vest")
        self.assertEqual(self.shot.calls, 0)
        self.assertEqual(qianfan.uploads, 0)
        self.assertEqual(qianfan.publish_calls, 0)

    def test_screenshot_failure_blocks_upload_and_publish(self):
        sources = FakeSources([CURRENT])
        qianfan = FakeQianfan()
        failing = FakeScreenshotter(Path(self.tempdir.name) / "bad.png", fail=True)
        service = self.service(sources, qianfan, failing)
        service.run_once()
        sources.records.insert(0, NEW_EVENT)

        result = service.run_once()
        self.assertEqual(result["events"][0]["status"], "screenshot_failed")
        self.assertEqual(qianfan.uploads, 0)
        self.assertEqual(qianfan.publish_calls, 0)

    def test_ambiguous_publish_is_reconciled_without_retry(self):
        sources = FakeSources([CURRENT])
        qianfan = FakeQianfan(ambiguous=True, duplicate=False)
        service = self.service(sources, qianfan)
        service.run_once()
        sources.records.insert(0, NEW_EVENT)

        result = service.run_once()
        self.assertEqual(result["events"][0]["status"], "manual_review")
        self.assertEqual(qianfan.publish_calls, 1)
        self.assertEqual(qianfan.duplicate_checks, 2)

    def test_formal_weibo_updates_matching_preliminary_post(self):
        baseline = dict(CURRENT, locName="四川泸州市江阳区")
        sources = FakeSources([baseline])
        qianfan = FakeQianfan()
        service = self.service(sources, qianfan, push_enabled=True)
        service.run_once()

        preliminary = dict(
            NEW_EVENT,
            focDepth=None,
            isPreliminary=True,
            _source="weibo",
        )
        sources.records.insert(0, preliminary)
        first = service.run_once()
        self.assertEqual(first["events"][0]["status"], "published_preliminary")
        self.assertEqual(
            qianfan.push_image_urls,
            ["https://pic.example/earthquake.png"],
        )

        formal = dict(
            NEW_EVENT,
            id=20260710180559,
            uniEventId="WBFORMAL1783677959000",
            oriTime="2026-07-10 18:05:59",
            focDepth=9.0,
            magnitude=2.9,
            isPreliminary=False,
            _source="weibo",
        )
        sources.records.insert(0, formal)
        second = service.run_once()
        self.assertEqual(second["events"][0]["status"], "updated_formal")
        self.assertEqual(qianfan.publish_calls, 1)
        self.assertEqual(qianfan.update_calls, 1)
        self.assertEqual(qianfan.push_calls, 1)

    def test_formal_weibo_update_reuses_wolfx_map_without_new_screenshot(self):
        class FakeGeocoder:
            def reverse(self, latitude, longitude):
                return "胜天镇"

        baseline = dict(CURRENT, locName="四川泸州市江阳区")
        sources = FakeSources([baseline])
        qianfan = FakeQianfan()
        service = self.service(
            sources,
            qianfan,
            push_enabled=True,
            geocoder=FakeGeocoder(),
        )
        service.run_once()

        wolfx = dict(
            NEW_EVENT,
            id=20260803130046,
            uniEventId="WX202608031300_0001",
            oriTime="2026-08-03 13:00:46",
            locName="四川宜宾市高县",
            epiLon=104.668,
            epiLat=28.55,
            magnitude=4.2,
            focDepth=0,
            isPreliminary=True,
            _source="wolfx_cenc",
        )
        sources.records.insert(0, wolfx)
        first = service.run_once()
        self.assertEqual(first["events"][0]["status"], "published_preliminary")
        self.assertEqual(self.shot.calls, 1)
        self.assertEqual(qianfan.uploads, 1)

        automatic = dict(
            wolfx,
            id=20260803130052,
            uniEventId="WBAUTO20260803130052",
            epiLon=104.67,
            epiLat=28.56,
            magnitude=4.1,
            focDepth=None,
            isPreliminary=True,
            _source="weibo",
        )
        sources.records.insert(0, automatic)
        second = service.run_once()

        self.assertEqual(second["events"][0]["status"], "updated_preliminary")
        self.assertEqual(self.shot.calls, 1)
        self.assertEqual(qianfan.uploads, 1)
        self.assertEqual(qianfan.publish_calls, 1)
        self.assertEqual(qianfan.update_calls, 1)

        formal = dict(
            automatic,
            id=20260803130059,
            uniEventId="WBFORMAL20260803130059",
            magnitude=4.0,
            focDepth=5,
            isPreliminary=False,
        )
        sources.records.insert(0, formal)
        third = service.run_once()

        self.assertEqual(third["events"][0]["status"], "updated_formal")
        self.assertEqual(self.shot.calls, 1)
        self.assertEqual(qianfan.uploads, 1)
        self.assertEqual(
            qianfan.update_image_urls,
            [
                "https://pic.example/earthquake.png",
                "https://pic.example/earthquake.png",
            ],
        )
        self.assertEqual(qianfan.push_calls, 1)

    def test_wolfx_uses_county_name_when_reverse_geocoder_is_unavailable(self):
        class FailingGeocoder:
            calls = 0

            def reverse(self, latitude, longitude):
                self.calls += 1
                raise RuntimeError("APP 服务被禁用")

        baseline = dict(CURRENT, locName="四川泸州市江阳区")
        sources = FakeSources([baseline])
        qianfan = FakeQianfan()
        service = self.service(
            sources,
            qianfan,
            push_enabled=True,
            geocoder=FailingGeocoder(),
        )
        service.run_once()
        sources.records.insert(
            0,
            dict(
                NEW_EVENT,
                uniEventId="WXCOUNTYFALLBACK1",
                locName="四川宜宾市高县附近",
                isPreliminary=True,
                _source="wolfx_cenc",
            ),
        )

        result = service.run_once()

        self.assertEqual(result["events"][0]["status"], "published_preliminary")
        self.assertEqual(result["events"][0]["push_status"], "pushed")
        row = self.store.connection.execute(
            "SELECT location, precise_location FROM events "
            "WHERE event_key='WXCOUNTYFALLBACK1'"
        ).fetchone()
        self.assertEqual(row["location"], "四川宜宾市高县")
        self.assertEqual(row["precise_location"], "四川宜宾市高县")
        self.assertEqual(qianfan.publish_calls, 1)
        self.assertEqual(qianfan.push_calls, 1)
        self.assertEqual(service.geocoder.calls, 0)

    def test_two_posts_within_six_hours_only_push_once(self):
        baseline = dict(CURRENT, locName="四川泸州市江阳区")
        sources = FakeSources([baseline])
        qianfan = FakeQianfan()
        service = self.service(sources, qianfan, push_enabled=True)
        service.run_once()

        first = dict(NEW_EVENT, isPreliminary=True, _source="weibo")
        sources.records.insert(0, first)
        service.run_once()

        second = dict(
            NEW_EVENT,
            id=20260710190500,
            uniEventId="WBAUTO1783681500000",
            oriTime="2026-07-10 19:05:00",
            locName="四川宜宾市高县",
            isPreliminary=True,
            _source="weibo",
        )
        sources.records.insert(0, second)
        result = service.run_once()

        self.assertEqual(result["events"][0]["push_status"], "cooldown")
        self.assertEqual(qianfan.publish_calls, 2)
        self.assertEqual(qianfan.push_calls, 1)

    def test_event_one_magnitude_higher_within_six_hours_pushes_again(self):
        baseline = dict(CURRENT, locName="四川泸州市江阳区")
        sources = FakeSources([baseline])
        qianfan = FakeQianfan()
        service = self.service(sources, qianfan, push_enabled=True)
        service.run_once()

        first = dict(NEW_EVENT, magnitude=2.8, isPreliminary=True, _source="weibo")
        sources.records.insert(0, first)
        service.run_once()

        second = dict(
            NEW_EVENT,
            id=20260710190500,
            uniEventId="WBAUTO1783681500000",
            oriTime="2026-07-10 19:05:00",
            locName="四川宜宾市高县",
            magnitude=3.8,
            isPreliminary=True,
            _source="weibo",
        )
        sources.records.insert(0, second)
        result = service.run_once()

        self.assertEqual(result["events"][0]["push_status"], "pushed")
        self.assertEqual(qianfan.publish_calls, 2)
        self.assertEqual(qianfan.push_calls, 2)


if __name__ == "__main__":
    unittest.main()
