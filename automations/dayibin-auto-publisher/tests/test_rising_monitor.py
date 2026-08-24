import unittest
import hashlib
import sqlite3
from pathlib import Path
import json
import tempfile
from unittest.mock import patch

from dayibin_auto_publisher.xyuqing_source import XyuqingNetworkError

from dayibin_auto_publisher.rising_monitor import (
    RisingMonitorError,
    _ego_script,
    _attach_editorial_images,
    _contains_forbidden_identity,
    _interaction_delta,
    _daily_content_counts,
    _daily_fact_candidate,
    _previous_day_state,
    associate_comments_by_content,
    build_comment_insight,
    build_business_channels,
    build_daily_summary,
    build_operator_hotspot_board,
    build_fact_check,
    classify_two_hour_rising,
    classify_fast_track,
    detect_rising_candidates,
    enrich_candidate_score,
    load_fact_rows,
    parse_plan_list,
    run_round,
    sanitize_content_item,
    sanitize_comment_item,
    update_watchlist,
)


class RisingMonitorTests(unittest.TestCase):
    def test_daily_fact_pool_loads_and_uses_full_raw_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "radar.db"
            connection = sqlite3.connect(database)
            connection.executescript(
                """
                CREATE TABLE sources (
                    id TEXT PRIMARY KEY, scope TEXT, layer TEXT, enabled INTEGER,
                    configured INTEGER, can_confirm_fact INTEGER
                );
                CREATE TABLE raw_items (
                    id TEXT PRIMARY KEY, source_id TEXT, canonical_url TEXT,
                    title TEXT, summary TEXT, raw_text TEXT, published_at TEXT,
                    first_seen_at TEXT, is_noise INTEGER
                );
                INSERT INTO sources VALUES ('gongxian-gov','yibin','official_fact',1,1,1);
                INSERT INTO raw_items VALUES (
                    'gym','gongxian-gov','https://official.example/gym',
                    '县体育馆换新升级工程持续推进','工程持续推进',
                    '珙县体育馆改造工程已完成90%，正在进行水电施工，后续将安装座椅与显示屏。',
                    datetime('now'),datetime('now'),0
                );
                """
            )
            connection.commit()
            connection.close()

            rows = load_fact_rows(database)

        self.assertEqual(
            rows[0]["raw_text"],
            "珙县体育馆改造工程已完成90%，正在进行水电施工，后续将安装座椅与显示屏。",
        )
        candidate = _daily_fact_candidate(rows[0], rows[0]["published_at"])
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["body_snapshot"], rows[0]["raw_text"])
        self.assertEqual(candidate["body_hash"], hashlib.sha256(rows[0]["raw_text"].encode()).hexdigest())

        national = _daily_fact_candidate(
            {
                **rows[0],
                "raw_item_id": "national",
                "source_id": "national-media",
                "source_tier": "P2",
                "title": "国产工业叉车全球爆单",
                "raw_text": "浙江安吉一家企业的无人叉车正在运行。",
            },
            rows[0]["published_at"],
        )
        self.assertIsNone(national)

        summary_only = _daily_fact_candidate(
            {
                **rows[0],
                "raw_item_id": "summary-only",
                "title": "宜宾公共体育馆改造持续推进",
                "raw_text": "",
            },
            rows[0]["published_at"],
        )
        channels = build_business_channels(
            [summary_only], collected_at=rows[0]["published_at"]
        )
        self.assertEqual(channels["daily_value"][0]["ready_status"], "SUPPLEMENT_REQUIRED")

    def test_daily_fact_pool_accepts_broader_low_risk_local_value_but_holds_weather(self) -> None:
        base = {
            "source_url": "https://official.example/item", "source_id": "official",
            "published_at": "2026-08-22T08:00:00+08:00", "summary": "权威来源公布了最新数据。",
        }
        industrial = _daily_fact_candidate(
            {**base, "raw_item_id": "industry", "title": "1-7月宜宾规上工业增长6.3%"},
            "2026-08-23T14:00:00+08:00",
        )
        agriculture = _daily_fact_candidate(
            {**base, "raw_item_id": "farm", "title": "南溪农事服务全链条护航秋粮"},
            "2026-08-23T14:00:00+08:00",
        )
        environment = _daily_fact_candidate(
            {**base, "raw_item_id": "water", "title": "翠屏区14处污水处理厂站汛期稳定运行"},
            "2026-08-23T14:00:00+08:00",
        )
        infrastructure = _daily_fact_candidate(
            {
                **base,
                "raw_item_id": "roads",
                "source_tier": "P0",
                "title": "屏山专题督导交通重点项目建设推进工作",
                "raw_text": "屏山金沙江大道拓宽项目和岷江二桥及南连接线项目正在推进建设。",
            },
            "2026-08-23T14:00:00+08:00",
        )
        weather = _daily_fact_candidate(
            {**base, "raw_item_id": "weather", "title": "宜宾气象台发布雷电黄色预警"},
            "2026-08-23T14:00:00+08:00",
        )

        self.assertIsNotNone(industrial)
        self.assertIsNotNone(agriculture)
        self.assertIsNotNone(environment)
        self.assertIsNotNone(infrastructure)
        self.assertIsNone(weather)

    def test_yryb_fact_with_unresolved_structured_media_is_held_without_fact_card(self) -> None:
        candidate = _daily_fact_candidate(
            {
                "raw_item_id": "charging",
                "source_id": "yibin-yryb",
                "source_url": "https://m.ybtv.cc/cms/content/139543170",
                "published_at": "2026-08-22T08:00:00+08:00",
                "title": "宜宾兆瓦级重卡充电站即将投用",
                "summary": "三江新区能源港新增超充设备。",
            },
            "2026-08-23T14:00:00+08:00",
        )
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["source_media_state"], "UNRESOLVED_SOURCE_MEDIA")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fact_card = root / "2026-08-23" / "editorial-images" / candidate["content_id"] / "fact-card.png"
            fact_card.parent.mkdir(parents=True)
            fact_card.write_bytes(b"fallback")
            _attach_editorial_images([candidate], root, "2026-08-23")
        self.assertEqual(candidate["images"], [])

        channels = build_business_channels(
            [candidate],
            collected_at="2026-08-23T14:00:00+08:00",
        )
        self.assertEqual(channels["daily_value"], [])
        self.assertEqual(channels["rising_watch"][0]["channel_reasons"], ["SOURCE_MEDIA_UNRESOLVED"])

    def test_yryb_fact_preserves_resolved_source_images(self) -> None:
        candidate = _daily_fact_candidate(
            {
                "raw_item_id": "charging",
                "source_id": "yibin-yryb",
                "source_url": "https://m.ybtv.cc/cms/content/139543170",
                "published_at": "2026-08-22T08:00:00+08:00",
                "title": "宜宾兆瓦级重卡充电站即将投用",
                "summary": "三江新区能源港新增超充设备。",
                "images": ["https://alifile.yibinrm.cn/source.jpg"],
            },
            "2026-08-23T14:00:00+08:00",
        )
        self.assertEqual(candidate["images"], ["https://alifile.yibinrm.cn/source.jpg"])
        self.assertEqual(candidate["source_media_state"], "RESOLVED_WITH_IMAGES")

    def test_ugc_ready_rejects_privacy_ads_accidents_and_location_only_noise(self) -> None:
        texts = [
            "陈某求带ID，16岁，四川宜宾某中学，快手号4227555975。",
            "江安县居民阅读，亲子鉴定机构合集，咨询热线和微信同号，可线上预约。",
            "小女孩不慎落水，父亲营救时双双卷入乱流，情况紧急。📍四川省宜宾市",
            "办公室防火须知，电气故障可能引发危险。📍四川省宜宾市兴文县",
            "#精致女孩必备 #化妆镜；农村女孩考上大学的生学宴办成惨剧，这场要了命的酒席发生在长宁县。",
            "寻找宜宾的段守容女士，10年前在深圳上班，那时候你离婚了，现在在哪里？",
            "宜宾叙州区158***28，28°57'21\"N，035乡道，104°26'45\"E。",
            "宜宾宋家镇来的小少妇，开着SUV赶场卖鞋。",
            "宜宾有两个蛆，三江蛆，叙州蛆，请问你们在哪个蛆。",
            "组长能来接我上班不，俺车被偷了，宜宾房产日常搞笑。",
        ]
        candidates = [
            {
                "content_id": f"ugc-{index}", "title": text, "body_snapshot": text,
                "body_hash": hashlib.sha256(text.encode()).hexdigest(), "platform": "video",
                "source_url": f"https://e/{index}", "published_at": "2026-08-23T10:00:00+08:00",
                "locality_state": "direct", "risk_state": "LOW_RISK", "age_bucket": "1-3h",
                "fact_check": {"status": "NO_MATCH"}, "score": 40, "interaction_delta": None,
                "reasons": [], "current_metrics": {},
            }
            for index, text in enumerate(texts)
        ]
        safe = "宜宾叙州区一处社区广场傍晚新增了几张长椅，发帖人想问大家实际使用是否方便。"
        candidates.append({
            **candidates[0], "content_id": "ugc-safe", "title": safe, "body_snapshot": safe,
            "body_hash": hashlib.sha256(safe.encode()).hexdigest(), "source_url": "https://e/safe",
            "current_metrics": {"comment_count": 1},
        })
        footer_only = "今天随手记下几件生活小事，大家最近过得怎么样？嗨屏山APP"
        candidates.append({
            **candidates[0], "content_id": "ugc-footer-only", "title": "今天的生活随手记",
            "body_snapshot": footer_only, "body_hash": hashlib.sha256(footer_only.encode()).hexdigest(),
            "source_url": "https://e/footer-only", "current_metrics": {"comment_count": 1},
        })
        merchant = "在保质保量的情况下这5个菜卖168真的过份吗？南溪仙源街道德公路37号疯狂烧烤"
        candidates.append({
            **candidates[0], "content_id": "ugc-merchant-like-only", "title": merchant,
            "body_snapshot": merchant, "body_hash": hashlib.sha256(merchant.encode()).hexdigest(),
            "source_url": "https://e/merchant", "current_metrics": {"comment_count": 1},
        })
        like_only = "南溪社区最近新添了几张长椅，大家觉得实际使用方便吗？"
        candidates.append({
            **candidates[0], "content_id": "ugc-like-only", "title": like_only,
            "body_snapshot": like_only, "body_hash": hashlib.sha256(like_only.encode()).hexdigest(),
            "source_url": "https://e/like-only", "current_metrics": {"like_count": 1},
        })
        mismatched = "刚进门听朋友说起四川宜宾那边的事，具体情况还需要再核实。"
        candidates.append({
            **candidates[0], "content_id": "ugc-risky-title",
            "title": "四川5死17伤升学宴后续", "body_snapshot": mismatched,
            "body_hash": hashlib.sha256(mismatched.encode()).hexdigest(),
            "source_url": "https://e/risky-title",
        })

        with patch("dayibin_auto_publisher.rising_monitor._same_user_event", return_value=False):
            channels = build_business_channels(
                candidates, collected_at="2026-08-23T12:00:00+08:00"
            )

        self.assertEqual([item["content_id"] for item in channels["daily_value"]], ["ugc-safe"])

    def test_title_level_fact_is_marked_for_supplement_not_ready_for_angle(self) -> None:
        candidate = {
            "content_id": "title-only", "title": "高县高铁新区项目11月竣工有啥影响",
            "platform": "official", "source_url": "https://e/title-only",
            "published_at": "2026-08-23T10:00:00+08:00", "body_snapshot": "",
            "locality_state": "direct", "risk_state": "LOW_RISK", "age_bucket": "1-3h",
            "fact_check": {"status": "PASS", "critical_unknown_count": 0}, "score": 60,
            "interaction_delta": None, "reasons": [], "current_metrics": {},
        }

        channels = build_business_channels([candidate], collected_at="2026-08-23T12:00:00+08:00")

        self.assertEqual(channels["ready_for_angle_count"], 0)
        self.assertEqual(channels["ready_for_angle"], [])
        self.assertEqual(channels["daily_value"][0]["ready_status"], "SUPPLEMENT_REQUIRED")
        self.assertEqual(channels["daily_value"][0]["material_level"], "TITLE_LEVEL")

    def test_business_channels_keep_at_least_twelve_ready_candidates(self) -> None:
        candidates = [
            {
                "content_id": f"c-{index}", "title": f"宜宾本地独立事项{index}",
                "body_snapshot": f"宜宾本地独立事项{index}已公布完整时间、地点和具体安排。",
                "platform": "official", "source_url": f"https://e/{index}",
                "published_at": "2026-08-23T10:00:00+08:00",
                "locality_state": "direct", "risk_state": "LOW_RISK", "age_bucket": "1-3h",
                "fact_check": {"status": "PASS", "critical_unknown_count": 0},
                "score": 50 + index, "interaction_delta": None, "reasons": [],
                "current_metrics": {},
            }
            for index in range(12)
        ]

        with patch("dayibin_auto_publisher.rising_monitor._same_user_event", return_value=False):
            channels = build_business_channels(
                candidates, collected_at="2026-08-23T12:00:00+08:00"
            )

        self.assertEqual(channels["independent_local_event_count"], 12)
        self.assertEqual(channels["ready_for_angle_count"], 12)
        self.assertEqual(len(channels["daily_value"]), 12)

    def test_business_channels_expose_every_ready_candidate_for_audit(self) -> None:
        candidates = [
            {
                "content_id": f"c-{index}", "title": f"宜宾本地独立事项{index}",
                "body_snapshot": f"宜宾本地独立事项{index}已公布完整时间、地点和具体安排。",
                "platform": "official", "source_url": f"https://e/{index}",
                "published_at": "2026-08-23T10:00:00+08:00",
                "locality_state": "direct", "risk_state": "LOW_RISK", "age_bucket": "1-3h",
                "fact_check": {"status": "PASS", "critical_unknown_count": 0},
                "score": 50 + index, "interaction_delta": None, "reasons": [],
                "current_metrics": {},
            }
            for index in range(25)
        ]

        with patch("dayibin_auto_publisher.rising_monitor._same_user_event", return_value=False):
            channels = build_business_channels(
                candidates, collected_at="2026-08-23T12:00:00+08:00"
            )

        self.assertEqual(channels["ready_for_angle_count"], 25)
        self.assertEqual(len(channels["ready_for_angle"]), 25)
        self.assertEqual(len(channels["daily_value"]), 20)

    def test_hot_now_requires_a_real_minimum_interaction_threshold(self) -> None:
        base = {
            "title": "宜宾渝昆高铁建设迎来新进展",
            "published_at": "2026-08-23T10:00:00+08:00",
            "locality_state": "direct", "risk_state": "LOW_RISK", "age_bucket": "1-3h",
            "fact_check": {"status": "PASS", "critical_unknown_count": 0},
            "score": 80, "interaction_delta": None, "reasons": [],
        }
        candidates = [
            {**base, "content_id": f"c-{index}", "platform": "weibo", "source_url": f"https://e/{index}",
             "current_metrics": {"view_count": 207 if index == 0 else index, "like_count": 0,
                                 "comment_count": 0, "share_count": 0}}
            for index in range(6)
        ]

        channels = build_business_channels(candidates, collected_at="2026-08-23T12:00:00+08:00")

        self.assertEqual(channels["hot_now"], [])
        self.assertTrue(channels["daily_value"])

    def test_hot_now_records_the_threshold_that_was_really_met(self) -> None:
        candidate = {
            "content_id": "c-1", "title": "宜宾李庄活动上新", "platform": "toutiao",
            "source_url": "https://e/1", "published_at": "2026-08-23T10:00:00+08:00",
            "locality_state": "direct", "risk_state": "LOW_RISK", "age_bucket": "1-3h",
            "fact_check": {"status": "PASS", "critical_unknown_count": 0},
            "score": 80, "interaction_delta": None, "reasons": ["HOT_RANK_UP"],
            "current_metrics": {"view_count": 999, "like_count": 20, "comment_count": 0, "share_count": 0},
        }

        event = build_business_channels([candidate], collected_at="2026-08-23T12:00:00+08:00")["hot_now"][0]

        self.assertEqual(event["hot_now_threshold_evidence"], {"like_count": 20})

    def test_event_grouping_does_not_chain_merge_through_a_middle_alias(self) -> None:
        base = {
            "title": "宜宾本地活动", "platform": "weibo", "published_at": "2026-08-23T10:00:00+08:00",
            "locality_state": "direct", "risk_state": "LOW_RISK", "age_bucket": "1-3h",
            "fact_check": {"status": "PASS", "critical_unknown_count": 0}, "score": 50,
            "interaction_delta": None, "reasons": [], "current_metrics": {},
        }
        rows = [{**base, "content_id": key, "source_url": f"https://e/{key}"} for key in "ABC"]
        linked = {frozenset(("A", "B")), frozenset(("B", "C"))}

        with patch(
            "dayibin_auto_publisher.rising_monitor._same_user_event",
            side_effect=lambda a, b, _at: frozenset((a["content_id"], b["content_id"])) in linked,
        ):
            channels = build_business_channels(rows, collected_at="2026-08-23T12:00:00+08:00")

        self.assertEqual(channels["event_count"], 2)

    def test_same_umbrella_topic_with_different_core_actions_gets_different_event_ids(self) -> None:
        from dayibin_auto_publisher.rising_monitor import _event_id

        conference = {"title": "2026世界动力电池大会9月将在四川宜宾举行", "published_at": "2026-08-20"}
        robot = {"title": "首台宜宾造机器人即将落地 2026世界动力电池大会拓展新边界", "published_at": "2026-08-20"}

        self.assertNotEqual(
            _event_id(conference, "2026-08-23T12:00:00+08:00"),
            _event_id(robot, "2026-08-23T12:00:00+08:00"),
        )

    def test_history_exact_content_id_is_excluded_even_when_title_changes(self) -> None:
        candidate = {
            "content_id": "same", "title": "宜宾项目今天有新标题", "platform": "official",
            "source_url": "https://e/new", "published_at": "2026-08-23T10:00:00+08:00",
            "locality_state": "direct", "risk_state": "LOW_RISK", "age_bucket": "1-3h",
            "fact_check": {"status": "PASS", "critical_unknown_count": 0}, "score": 60,
            "interaction_delta": None, "reasons": [], "current_metrics": {},
        }
        history = [{**candidate, "title": "旧标题完全不同", "source_url": "https://e/old"}]

        channels = build_business_channels(
            [candidate], collected_at="2026-08-23T12:00:00+08:00", active_history=history
        )

        self.assertEqual(channels["ready_for_angle_count"], 0)
        self.assertEqual(channels["history_excluded_count"], 1)

    def test_merged_event_uses_strictest_risk_and_holds_locality_conflicts(self) -> None:
        base = {
            "title": "宜宾李庄活动上新", "platform": "weibo", "published_at": "2026-08-23T10:00:00+08:00",
            "locality_state": "direct", "age_bucket": "1-3h",
            "fact_check": {"status": "PASS", "critical_unknown_count": 0}, "score": 50,
            "interaction_delta": None, "reasons": [], "current_metrics": {},
        }
        rows = [
            {**base, "content_id": "safe", "source_url": "https://e/safe", "risk_state": "LOW_RISK"},
            {**base, "content_id": "hold", "source_url": "https://e/hold", "risk_state": "HARD_HOLD",
             "risk_reasons": ["PUBLIC_SAFETY"]},
        ]

        channels = build_business_channels(rows, collected_at="2026-08-23T12:00:00+08:00")
        event = channels["ignore_top10"][0]

        self.assertEqual(event["risk_state"], "HARD_HOLD")
        self.assertEqual(event["risk_reasons"], ["PUBLIC_SAFETY"])

    def test_guangxi_longan_pingshan_and_earthquake_anxiety_are_not_low_risk_local(self) -> None:
        row = sanitize_content_item(
            {"title": "广西隆安屏山家乡近况", "content": "当地生活记录", "url": "https://e/x"},
            collected_at="2026-08-23T12:00:00+08:00",
        )
        quake = sanitize_content_item(
            {"title": "宜宾地震5.5级传言引发焦虑", "content": "震感讨论", "url": "https://e/q"},
            collected_at="2026-08-23T12:00:00+08:00",
        )

        self.assertNotEqual(row["locality_state"], "direct")
        self.assertNotEqual(quake["risk_state"], "LOW_RISK")

    def test_two_hour_rising_requires_five_real_non_regressing_samples(self) -> None:
        snapshots = [
            {"collected_at": f"2026-08-23T{hour:02d}:{minute:02d}:00+08:00", "view_count": value}
            for (hour, minute), value in zip(((10, 0), (10, 30), (11, 0), (11, 30), (12, 0)), (10, 12, 12, 14, 15))
        ]
        self.assertEqual(classify_two_hour_rising(snapshots)["status"], "RISING_CONFIRMED")
        self.assertEqual(classify_two_hour_rising(snapshots[:-1])["status"], "INSUFFICIENT_SAMPLES")
        regressed = [*snapshots[:3], {**snapshots[3], "view_count": 11}, snapshots[4]]
        self.assertEqual(classify_two_hour_rising(regressed)["status"], "DATA_QUALITY_HOLD")

    def test_editorial_images_are_restored_before_business_output_rebuild(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root / "2026-08-22" / "editorial-images" / "content-1" / "fact-card.png"
            image.parent.mkdir(parents=True)
            image.write_bytes(b"approved-image")
            candidates = [{"content_id": "content-1", "images": []}]

            _attach_editorial_images(candidates, root, "2026-08-22")

            self.assertEqual(candidates[0]["images"], [str(image.resolve())])
            self.assertEqual(candidates[0]["image_plan"][0]["path"], str(image.resolve()))
            self.assertEqual(candidates[0]["image_plan"][0]["rights"], "ORIGINAL_EDITORIAL_GRAPHIC")

    def test_real_source_images_are_not_overwritten_by_fact_card(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root / "2026-08-22" / "editorial-images" / "content-1" / "fact-card.png"
            image.parent.mkdir(parents=True)
            image.write_bytes(b"fallback")
            candidates = [{"content_id": "content-1", "images": ["https://cdn.example/live.jpg"]}]

            _attach_editorial_images(candidates, root, "2026-08-22")

            self.assertEqual(candidates[0]["images"], ["https://cdn.example/live.jpg"])
            self.assertNotIn("image_plan", candidates[0])

    def test_network_error_bundle_is_not_mislabeled_as_schema_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(XyuqingNetworkError, "NETWORK_ERROR"):
                run_round(
                    {"auth_status": "NETWORK_ERROR"},
                    data_dir=Path(temporary) / "data",
                    business_date="2026-08-22",
                    evidence_dir=Path(temporary) / "evidence",
                    round_number=1,
                    collected_at="2026-08-22T16:30:00+08:00",
                )

    def test_hot_now_merges_same_event_without_waiting_for_delta(self) -> None:
        base = {
            "title": "宜宾中渡口片区启动更新建设",
            "published_at": "2026-08-22T09:00:00+08:00",
            "locality_state": "direct",
            "risk_state": "LOW_RISK",
            "age_bucket": "1-3h",
            "fact_check": {"status": "PASS", "critical_unknown_count": 0},
            "score": 40,
            "interaction_delta": None,
            "reasons": [],
        }
        channels = build_business_channels(
            [
                {**base, "content_id": "a", "platform": "weibo", "source_url": "https://a", "current_metrics": {"comment_count": 80}},
                {**base, "content_id": "b", "platform": "toutiao", "source_url": "https://b", "current_metrics": {"comment_count": 30}},
            ],
            collected_at="2026-08-22T12:00:00+08:00",
            watch_degraded_reasons=["WATCH_QUERY_DEGRADED"],
        )

        self.assertEqual(channels["event_count"], 1)
        self.assertEqual(channels["merged_event_count"], 1)
        self.assertEqual(len(channels["hot_now"]), 1)
        self.assertEqual(channels["hot_now"][0]["platform_count"], 2)
        self.assertIsNone(channels["hot_now"][0]["interaction_delta"])
        self.assertNotIn("total_interaction", channels["hot_now"][0])

    def test_music_event_uses_real_source_photos_instead_of_fact_card(self) -> None:
        base = {
            "title": "晚风遇乐章！宜宾长江公园落日音乐会氛围感拉满",
            "published_at": "2026-08-22T09:00:00+08:00",
            "locality_state": "direct", "risk_state": "LOW_RISK", "age_bucket": "1-3h",
            "fact_check": {"status": "PASS", "critical_unknown_count": 0},
            "score": 55, "interaction_delta": None, "reasons": [],
        }
        fallback = "/tmp/fact-card.png"
        channels = build_business_channels(
            [
                {**base, "content_id": "official", "platform": "yibin-yryb", "source_url": "https://official",
                 "images": [fallback], "image_plan": [{"path": fallback, "rights": "ORIGINAL_EDITORIAL_GRAPHIC"}]},
                {**base, "content_id": "social", "platform": "weibo", "source_url": "https://social",
                 "images": ["https://cdn.example/live.jpg"]},
            ],
            collected_at="2026-08-22T12:00:00+08:00",
        )

        merged = channels["daily_value"] + channels["hot_now"] + channels["rising_watch"]
        self.assertEqual(channels["event_count"], 1)
        self.assertEqual(merged[0]["images"], ["https://cdn.example/live.jpg"])
        self.assertEqual(merged[0]["image_plan"][0]["rights"], "SOURCE_MEDIA_REQUIRES_LOCALIZATION")

    def test_same_charging_event_merges_different_content_ids_and_keeps_complete_source(self) -> None:
        base = {
            "published_at": "2026-08-22T09:00:00+08:00", "locality_state": "direct",
            "risk_state": "LOW_RISK", "age_bucket": "1-3h",
            "fact_check": {"status": "PASS", "critical_unknown_count": 0},
            "score": 55, "interaction_delta": None, "reasons": [], "platform": "yibin-yryb",
        }
        channels = build_business_channels(
            [
                {**base, "content_id": "brief", "title": "宜宾首个符合3C标准的兆瓦级综合充电站即将上岗",
                 "source_url": "https://brief", "material_excerpt": "视频新闻，官方详情未提供文字正文。"},
                {**base, "content_id": "complete", "published_at": "2026-08-20T09:00:00+08:00",
                 "title": "2026世界动力电池大会丨重卡‘闪充’！宜宾首个符合3C标准兆瓦级综合充电站即将上岗",
                 "source_url": "https://complete", "material_excerpt": "三江新区东部产业园能源港新增2套960kW超充桩、8个接口，可同时服务40辆重卡，预计8月底投用。"},
            ],
            collected_at="2026-08-22T12:00:00+08:00",
        )
        merged = channels["daily_value"] + channels["hot_now"] + channels["rising_watch"]
        self.assertEqual(channels["event_count"], 1)
        self.assertEqual(merged[0]["content_id"], "complete")
        self.assertEqual(len(merged[0]["source_aliases"]), 2)

    def test_leak_scan_checks_human_text_but_not_opaque_fact_ids(self) -> None:
        self.assertFalse(
            _contains_forbidden_identity(
                {"fact_check": {"raw_item_id": "abc12345678901xyz"}}
            )
        )
        self.assertTrue(
            _contains_forbidden_identity(
                {"content_excerpt": "联系电话：13800138000"}
            )
        )
        self.assertFalse(
            _contains_forbidden_identity(
                {"images": ["https://cdn.example/image.jpg?token=public-signed-url"]}
            )
        )
        self.assertTrue(_contains_forbidden_identity({"token": "secret-value"}))
        self.assertTrue(
            _contains_forbidden_identity(
                {"content_excerpt": "Authorization: Bearer secret-value"}
            )
        )

    def test_fixture_is_synthetic_and_documents_empty_latest_page_boundary(self) -> None:
        fixture = json.loads(
            (Path(__file__).parent / "fixtures" / "rising_monitor_contracts.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertTrue(fixture["synthetic"])
        self.assertFalse(fixture["live_response"])
        self.assertEqual(fixture["empty_content_boundary"]["status"], "CALIBRATION_ONLY")

    def test_parse_plan_list_requires_exact_current_plan_name(self) -> None:
        payload = {
            "code": 0,
            "data": [
                {
                    "id": "group-1",
                    "name": "默认分组",
                    "children": [
                        {"id": "old-plan", "name": "别的方案", "user_id": "u1"},
                        {
                            "id": "plan-123",
                            "name": "宜宾热点监控",
                            "word": "宜宾",
                            "user_id": "u2",
                        },
                    ],
                }
            ],
        }

        plan = parse_plan_list(payload)

        self.assertEqual(plan["name"], "宜宾热点监控")
        self.assertIn("plan_id_hash", plan)
        self.assertNotIn("plan_id", plan)
        self.assertNotIn("user_id", plan)

    def test_live_query_contract_uses_runtime_plan_id_without_persisting_it(self) -> None:
        script = _ego_script("test-space")

        self.assertIn("plan_id:String(plan.id)", script)
        self.assertIn(
            "discovery/platform pages + title-canary watch/comments filtered by runtime plan_id",
            script,
        )
        self.assertIn("comments grouped only by reported origin", script)
        self.assertNotIn("plan_id:'", script)
        self.assertIn("plan_id_hash:planIdHash", script)
        self.assertIn("matches.length === 1", script)
        self.assertIn("String(plan.id || '').trim() === ''", script)
        self.assertIn("new URL(tab.url).hostname === 'www.xyuqing.com'", script)
        self.assertIn("switchTab(existing.targetId || existing.id)", script)
        self.assertNotIn("id:group?.id", script)
        self.assertNotIn("id:child?.id", script)

    def test_live_query_contract_uses_summary_paging_and_bounded_platform_canary(self) -> None:
        script = _ego_script("test-space")

        self.assertIn("return_type:2", script)
        self.assertIn("page:2", script)
        self.assertIn("platform_canary", script)
        self.assertIn("request_budget:6", script)
        self.assertNotIn("direct_id:String", script)

    def test_live_watch_query_uses_title_canary_and_never_guesses_direct_id(self) -> None:
        script = _ego_script(
            "test-space",
            watch_target={
                "title": "宜宾中渡口片区启动更新建设",
                "query": "中渡口",
                "identity_aliases": ["a" * 64],
            },
        )

        self.assertIn("word:watchWord", script)
        self.assertIn("word:watchWord, merge:0", script)
        self.assertIn('"query": "中渡口"', script)
        self.assertIn("watchCanaryValid", script)
        self.assertIn("match_count:watchRows.length", script)
        self.assertIn("key+':'+value", script)
        self.assertIn("targetAliases.has(value)", script)
        self.assertIn("stable_alias_count:targetAliases.size", script)
        self.assertIn("word:watchWord || query", script)
        self.assertNotIn("direct_id:String", script)

    def test_parse_plan_list_rejects_missing_or_duplicate_plan(self) -> None:
        with self.assertRaises(RisingMonitorError):
            parse_plan_list({"code": 0, "data": []})
        with self.assertRaises(RisingMonitorError):
            parse_plan_list(
                {
                    "code": 0,
                    "data": [
                        {
                            "children": [
                                {"id": "1", "name": "宜宾热点监控"},
                                {"id": "2", "name": "宜宾热点监控"},
                            ]
                        }
                    ],
                }
            )

    def test_content_and_comment_sanitizers_remove_identity_fields(self) -> None:
        content = sanitize_content_item(
            {
                "unique_id": "post-1",
                "title": "宜宾李庄活动上新",
                "content": "李庄古镇有新活动",
                "platform": "douyin",
                "url": "https://example.invalid/post/1",
                "nickname": "某用户",
                "user_id": "uid",
                "avatar": "https://example.invalid/a.jpg",
                "like_count": 3,
                "comment_count": 4,
            },
            collected_at="2026-08-20T10:00:00+08:00",
        )
        comment = sanitize_comment_item(
            {
                "unique_id": "comment-1",
                "content": "想知道停车方便不",
                "nickname": "某用户",
                "unique_user_id": "u1",
                "user_url": "https://example.invalid/user",
            }
        )

        serialized = repr({"content": content, "comment": comment})
        for forbidden in ("nickname", "user_id", "unique_user_id", "avatar", "user_url"):
            self.assertNotIn(forbidden, serialized)
        self.assertEqual(content["locality_state"], "direct")
        self.assertEqual(comment["signal_role"], "AUDIENCE_SIGNAL_ONLY")

    def test_content_sanitizer_keeps_only_three_public_image_urls(self) -> None:
        item = sanitize_content_item(
            {
                "unique_id": "image-post",
                "title": "宜宾中渡口更新",
                "platform": "微信",
                "images": [
                    {"url": "https://img.example/1.jpg"},
                    "https://img.example/2.jpg",
                    {"url": "javascript:alert(1)"},
                ],
                "cover_url": "https://img.example/3.jpg",
            },
            collected_at="2026-08-22T09:00:00+08:00",
        )

        self.assertEqual(
            item["images"],
            [
                "https://img.example/1.jpg",
                "https://img.example/2.jpg",
                "https://img.example/3.jpg",
            ],
        )

    def test_locality_rejects_external_event_place_even_with_yibin_profile_or_footer(self) -> None:
        cases = (
            {
                "unique_id": "mabian-flood",
                "title": "马边县城第二次遭水灾了",
                "content": "四川省宜宾市",
                "ip_location": "宜宾",
            },
            {
                "unique_id": "wangcang-relic",
                "title": "旺苍佛子岩文物石刻造像",
                "content": "文末定位 📍四川省宜宾市",
            },
            {
                "unique_id": "chengdu-consumption",
                "title": "成都商场消费观察",
                "content": "账号定位宜宾",
                "location": "宜宾",
            },
            {
                "unique_id": "luzhou-medical",
                "title": "泸州医院就诊经历",
                "content": "📍四川省宜宾市",
            },
        )
        for row in cases:
            item = sanitize_content_item(
                {**row, "platform": "抖音"},
                collected_at="2026-08-22T09:00:00+08:00",
            )
            self.assertEqual(item["locality_state"], "rejected", row["title"])

        generic = sanitize_content_item(
            {
                "unique_id": "generic-kindness",
                "title": "永远不要欺负善良厚道的人",
                "content": "凡事要守住善意 📍四川省宜宾市",
                "platform": "抖音",
            },
            collected_at="2026-08-22T09:00:00+08:00",
        )
        self.assertNotEqual(generic["locality_state"], "direct")

    def test_locality_accepts_event_text_or_poi_but_not_ip_location_alone(self) -> None:
        direct_text = sanitize_content_item(
            {
                "unique_id": "yibin-project",
                "title": "宜宾中渡口片区启动更新建设",
                "platform": "微信",
            },
            collected_at="2026-08-22T09:00:00+08:00",
        )
        direct_poi = sanitize_content_item(
            {
                "unique_id": "poi-project",
                "title": "片区项目正式启动",
                "poi_name": "宜宾中渡口",
                "platform": "抖音",
            },
            collected_at="2026-08-22T09:00:00+08:00",
        )
        ip_only = sanitize_content_item(
            {
                "unique_id": "ip-only",
                "title": "今天聊聊生活选择",
                "ip_location": "宜宾",
                "platform": "抖音",
            },
            collected_at="2026-08-22T09:00:00+08:00",
        )

        self.assertEqual(direct_text["locality_state"], "direct")
        self.assertEqual(direct_poi["locality_state"], "direct")
        self.assertEqual(ip_only["locality_state"], "needs_verification")

    def test_comments_are_associated_only_with_their_origin_content(self) -> None:
        first = sanitize_content_item(
            {"unique_id": "origin-1", "title": "宜宾活动一", "platform": "douyin"},
            collected_at="2026-08-21T10:00:00+08:00",
        )
        second = sanitize_content_item(
            {"unique_id": "origin-2", "title": "宜宾活动二", "platform": "douyin"},
            collected_at="2026-08-21T10:00:00+08:00",
        )
        comments = [
            sanitize_comment_item(
                {
                    "unique_id": "comment-1",
                    "content": "只属于活动一",
                    "origin": {"unique_id": "origin-1", "url": "https://example.invalid/1"},
                }
            )
        ]

        associated = associate_comments_by_content([first, second], comments)

        self.assertEqual(len(associated[first["content_id"]]), 1)
        self.assertEqual(associated[second["content_id"]], [])

        unmatched = sanitize_comment_item(
            {
                "unique_id": "comment-2",
                "content": "属于另一条原帖",
                "origin": {"unique_id": "origin-3"},
            }
        )
        separated = associate_comments_by_content([first, second], [unmatched])
        self.assertEqual(separated[first["content_id"]], [])
        self.assertEqual(separated[second["content_id"]], [])
        self.assertEqual(sum(len(rows) for rows in separated.values()), 1)

        colliding_first = {**first, "identity_aliases": ["shared"]}
        colliding_second = {**second, "identity_aliases": ["shared"]}
        ambiguous = {**comments[0], "origin_aliases": ["shared"], "origin_event_id": "anonymous"}
        collision = associate_comments_by_content(
            [colliding_first, colliding_second], [ambiguous]
        )
        self.assertEqual(collision[first["content_id"]], [])
        self.assertEqual(collision[second["content_id"]], [])
        self.assertEqual(len(collision["anonymous"]), 1)

    def test_update_watchlist_preserves_ugc_body_snapshot_and_hash(self) -> None:
        item = sanitize_content_item(
            {"title": "宜宾小区停车讨论", "content": "发帖人描述晚间停车位紧张，想讨论共享时段。",
             "url": "https://e/ugc", "platform": "头条"},
            collected_at="2026-08-23T10:00:00+08:00",
        )

        state = update_watchlist(
            {"items": []}, [item], collected_at="2026-08-23T10:00:00+08:00"
        )

        self.assertEqual(state["items"][0]["body_snapshot"], item["body_snapshot"])
        self.assertEqual(state["items"][0]["body_hash"], item["body_hash"])

    def test_update_watchlist_keeps_stable_identity_and_capped_recent_snapshots(self) -> None:
        first = sanitize_content_item(
            {
                "unique_id": "post-1",
                "title": "宜宾公交有调整",
                "platform": "douyin",
                "like_count": 1,
                "comment_count": 0,
            },
            collected_at="2026-08-20T10:00:00+08:00",
        )
        second = sanitize_content_item(
            {
                "unique_id": "post-1",
                "title": "宜宾公交有调整",
                "platform": "douyin",
                "like_count": 10,
                "comment_count": 2,
            },
            collected_at="2026-08-20T10:30:00+08:00",
        )

        state = update_watchlist({}, [first], collected_at="2026-08-20T10:00:00+08:00")
        state = update_watchlist(state, [second], collected_at="2026-08-20T10:30:00+08:00")

        self.assertEqual(state["watchlist_count"], 1)
        item = state["items"][0]
        self.assertEqual(item["first_seen_at"], "2026-08-20T10:00:00+08:00")
        self.assertEqual(item["last_seen_at"], "2026-08-20T10:30:00+08:00")
        self.assertEqual([snap["like_count"] for snap in item["snapshots"]], [1, 10])

    def test_watchlist_refreshes_age_and_risk_fields_each_round(self) -> None:
        first = sanitize_content_item(
            {"unique_id": "post-1", "title": "宜宾活动", "platform": "微信"},
            collected_at="2026-08-22T09:00:00+08:00",
        )
        second = {
            **first,
            "title": "宜宾活动发生坍塌",
            "age_bucket": "1-3h",
            "risk_state": "HOLD",
        }
        state = update_watchlist({}, [first], collected_at="2026-08-22T09:00:00+08:00")
        state = update_watchlist(state, [second], collected_at="2026-08-22T10:30:00+08:00")

        self.assertEqual(state["items"][0]["age_bucket"], "1-3h")
        self.assertEqual(state["items"][0]["risk_state"], "HOLD")

    def test_watchlist_reapplies_current_locality_and_risk_rules_to_entire_pool(self) -> None:
        stale = {
            "schema_version": "rising-monitor-state-v1",
            "items": [
                {
                    "content_id": "old-mabian-flood",
                    "title": "马边县城第二次遭水灾了",
                    "content_excerpt": "账号定位宜宾",
                    "platform": "抖音",
                    "platform_name": "抖音",
                    "source_url": "https://example.invalid/mabian",
                    "published_at": "2026-08-22T10:30:00+08:00",
                    "locality_state": "direct",
                    "risk_state": "LOW_RISK",
                    "age_bucket": "0-1h",
                    "first_seen_at": "2026-08-22T11:00:00+08:00",
                    "last_seen_at": "2026-08-22T11:00:00+08:00",
                    "snapshots": [{"collected_at": "2026-08-22T11:00:00+08:00"}],
                }
            ],
        }

        refreshed = update_watchlist(
            stale,
            [],
            collected_at="2026-08-22T11:30:00+08:00",
        )

        self.assertEqual(refreshed["items"][0]["locality_state"], "rejected")
        self.assertEqual(refreshed["items"][0]["risk_state"], "HOLD")

    def test_watchlist_resanitizes_embedded_identity_metadata_in_existing_pool(self) -> None:
        stale = {
            "items": [
                {
                    "content_id": "old-wrapped-row",
                    "title": "宜宾本地活动",
                    "content_excerpt": (
                        "摘要：宜宾本地活动 账号昵称：普通用户 用户ID：123456 "
                        "联系电话：13800138000 命中地域：宜宾市"
                    ),
                    "platform": "抖音",
                    "source_url": "https://example.invalid/local",
                    "published_at": "2026-08-22T10:30:00+08:00",
                    "last_seen_at": "2026-08-22T11:00:00+08:00",
                    "snapshots": [{"collected_at": "2026-08-22T11:00:00+08:00"}],
                }
            ]
        }

        refreshed = update_watchlist(stale, [], collected_at="2026-08-22T11:30:00+08:00")

        excerpt = refreshed["items"][0]["content_excerpt"]
        for forbidden in ("账号昵称", "用户ID", "联系电话", "13800138000"):
            self.assertNotIn(forbidden, excerpt)

    def test_interaction_delta_does_not_double_count_respond_total(self) -> None:
        item = {
            "snapshots": [
                {"like_count": 1, "comment_count": 2, "share_count": 3, "respond_count": 6},
                {"like_count": 2, "comment_count": 4, "share_count": 6, "respond_count": 12},
            ]
        }

        self.assertEqual(_interaction_delta(item), 6)

    def test_previous_day_state_preserves_cross_midnight_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "2026-08-21" / "rising-monitor"
            path.mkdir(parents=True)
            expected = {"items": [{"content_id": "post-1", "snapshots": [{"like_count": 1}]}]}
            (path / "state.json").write_text(json.dumps(expected), encoding="utf-8")

            self.assertEqual(_previous_day_state(Path(temporary), "2026-08-22"), expected)

    def test_existing_round_evidence_fails_before_any_daily_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            evidence = base / "evidence" / "rounds"
            evidence.mkdir(parents=True)
            (evidence / "round-001.json").write_text("{}", encoding="utf-8")

            with self.assertRaisesRegex(RisingMonitorError, "already exists"):
                run_round(
                    {},
                    data_dir=base / "data",
                    business_date="2026-08-22",
                    evidence_dir=base / "evidence",
                    round_number=1,
                    collected_at="2026-08-22T09:00:00+08:00",
                )

            self.assertFalse((base / "data").exists())

    def test_discovery_and_watch_pools_create_real_overlap_and_delta(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            state_root = base / "data" / "2026-08-22" / "rising-monitor"
            state_root.mkdir(parents=True)
            previous = sanitize_content_item(
                {
                    "unique_id": "stable-watch-item",
                    "title": "宜宾中渡口片区启动施工",
                    "platform": "微信",
                    "like_count": 10,
                    "comment_count": 2,
                },
                collected_at="2026-08-22T10:00:00+08:00",
            )
            previous_state = update_watchlist(
                {}, [previous], collected_at="2026-08-22T10:00:00+08:00"
            )
            (state_root / "state.json").write_text(
                json.dumps(previous_state, ensure_ascii=False), encoding="utf-8"
            )
            bundle = {
                "auth_status": "AUTH_OK",
                "plan_list": {
                    "code": 0,
                    "data": [{"name": "宜宾热点监控", "plan_id_hash": "a" * 64}],
                },
                "discovery_content": {
                    "code": 0,
                    "data": {
                        "list": [
                            {
                                "unique_id": "new-discovery-item",
                                "title": "宜宾李庄活动上新",
                                "platform": "抖音",
                                "like_count": 1,
                            }
                        ]
                    },
                },
                "watch_content": {
                    "code": 0,
                    "data": {
                        "list": [
                            {
                                "unique_id": "stable-watch-item",
                                "title": "宜宾中渡口片区启动施工",
                                "platform": "微信",
                                "like_count": 14,
                                "comment_count": 3,
                            }
                        ]
                    },
                },
                "comments": {"code": 0, "data": {"list": []}},
                "fact_rows": [
                    {
                        "raw_item_id": "fact-stable-watch",
                        "source_id": "yibin-gov",
                        "source_tier": "P0",
                        "title": "宜宾中渡口片区启动施工",
                        "summary": "中渡口片区启动建设",
                        "source_url": "https://example.invalid/fact-stable-watch",
                    }
                ],
                "requests": [],
            }

            report = run_round(
                bundle,
                data_dir=base / "data",
                business_date="2026-08-22",
                evidence_dir=base / "evidence",
                round_number=1,
                collected_at="2026-08-22T10:30:00+08:00",
            )

            self.assertEqual(report["discovery_count"], 1)
            self.assertEqual(report["watch_refresh_count"], 1)
            self.assertEqual(report["overlap_count"], 1)
            self.assertEqual(report["interaction_delta_count"], 1)
            pool = json.loads(
                (base / "data" / "2026-08-22" / "rising-monitor" / "daily-candidate-pool.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(pool["candidate_count"], 1)
            self.assertEqual(pool["target_range"], [8, 12])
            self.assertIn("不足8条", pool["shortage_reason"])
            self.assertIsNotNone(pool["shortage_reason"])

    def test_anonymous_comment_groups_never_become_candidate_insights(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            comments = [
                {
                    "unique_id": f"comment-{index}",
                    "content": f"第{index}条有效讨论，想知道后续安排",
                    "origin": {"unique_id": "unmatched-origin"},
                }
                for index in range(10)
            ]
            bundle = {
                "auth_status": "AUTH_OK",
                "plan_list": {
                    "code": 0,
                    "data": [{"name": "宜宾热点监控", "plan_id_hash": "a" * 64}],
                },
                "discovery_content": {
                    "code": 0,
                    "data": {
                        "list": [
                            {
                                "unique_id": "candidate",
                                "title": "宜宾中渡口片区启动施工",
                                "platform": "微信",
                            }
                        ]
                    },
                },
                "watch_content": {"code": 0, "data": {"list": []}},
                "comments": {"code": 0, "data": {"list": comments}},
                "fact_rows": [],
                "requests": [],
            }

            report = run_round(
                bundle,
                data_dir=base / "data",
                business_date="2026-08-22",
                evidence_dir=base / "evidence",
                round_number=1,
                collected_at="2026-08-22T10:30:00+08:00",
            )

            self.assertEqual(report["candidate_origin_match_count"], 0)
            self.assertEqual(report["comment_insight_ready_count"], 0)
            self.assertEqual(report["anonymous_event_group_count"], 1)

    def test_daily_counts_include_the_unique_active_confirmation_card(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "2026-08-22" / "functional-canary"
            path.mkdir(parents=True)
            (path / "active-confirmation-card.json").write_text(
                json.dumps({"status": "AWAITING_HUMAN_PUBLISH_CONFIRMATION"}),
                encoding="utf-8",
            )

            self.assertEqual(
                _daily_content_counts(Path(temporary), "2026-08-22"),
                (1, 1),
            )

    def test_daily_counts_exclude_every_superseded_batch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, status, count in (
                ("active", "AWAITING_HUMAN_SCHEDULE_CONFIRMATION", 3),
                ("old", "SUPERSEDED_DUPLICATE_SMOKE", 2),
                ("race", "SUPERSEDED_DUPLICATE_RACE", 2),
            ):
                path = root / "2026-08-22" / "pending-batches" / name
                path.mkdir(parents=True)
                (path / "batch.json").write_text(
                    json.dumps({"status": status, "drafts": [{}] * count}),
                    encoding="utf-8",
                )

            self.assertEqual(_daily_content_counts(root, "2026-08-22"), (3, 3))

    def test_detect_rising_candidates_triggers_only_after_two_snapshots_and_platform_peer_sample(self) -> None:
        items = []
        for index in range(20):
            like_count = 10 + index
            latest_like_count = like_count + (200 if index == 0 else 1)
            title = f"宜宾观察 {index}"
            items.append(
                {
                    "content_id": f"post-{index}",
                    "title": title,
                    "platform": "douyin",
                    "locality_state": "direct",
                    "risk_state": "LOW_RISK",
                    "age_bucket": "0-1h",
                    "first_seen_at": "2026-08-20T10:00:00+08:00",
                    "last_seen_at": "2026-08-20T10:30:00+08:00",
                    "snapshots": [
                        {"collected_at": "2026-08-20T10:00:00+08:00", "like_count": like_count},
                        {"collected_at": "2026-08-20T10:30:00+08:00", "like_count": latest_like_count},
                    ],
                }
            )
        state = {"schema_version": "rising-monitor-state-v1", "items": items}

        candidates = detect_rising_candidates(state)
        anomalous = next(item for item in candidates if item["content_id"] == "post-0")
        normal = next(item for item in candidates if item["content_id"] == "post-1")

        self.assertEqual(anomalous["rising_state"], "RISING_CANDIDATE")
        self.assertGreaterEqual(anomalous["score"], 55)
        self.assertEqual(normal["rising_state"], "OBSERVE")

    def test_detect_rising_candidates_marks_small_samples_as_calibration_only(self) -> None:
        state = {
            "items": [
                {
                    "content_id": "post-1",
                    "title": "宜宾李庄热度上升",
                    "platform": "douyin",
                    "locality_state": "direct",
                    "risk_state": "LOW_RISK",
                    "age_bucket": "0-1h",
                    "snapshots": [
                        {"collected_at": "2026-08-20T10:00:00+08:00", "like_count": 1},
                        {"collected_at": "2026-08-20T10:30:00+08:00", "like_count": 100},
                    ],
                }
            ]
        }

        self.assertEqual(detect_rising_candidates(state)[0]["rising_state"], "CALIBRATION_ONLY")

    def test_comment_insight_is_anonymous_and_requires_ten_effective_comments(self) -> None:
        comments = [
            sanitize_comment_item(
                {
                    "unique_id": f"c-{index}",
                    "content": f"想知道停车方便不，第{index}个朋友也想去看看",
                    "nickname": f"user-{index}",
                    "user_id": f"u-{index}",
                }
            )
            for index in range(10)
        ]

        insight = build_comment_insight("post-1", comments)
        serialized = repr(insight)

        self.assertEqual(insight["status"], "COMMENT_INSIGHT_READY")
        self.assertEqual(insight["signal_role"], "AUDIENCE_SIGNAL_ONLY")
        self.assertNotIn("nickname", serialized)
        self.assertNotIn("user_id", serialized)
        self.assertEqual(build_comment_insight("post-1", comments[:3])["status"], "COMMENT_EVIDENCE_INSUFFICIENT")

    def test_fast_track_requires_score_locality_low_risk_fact_check_and_zero_unknowns(self) -> None:
        base = {
            "content_id": "post-1",
            "score": 80,
            "locality_state": "direct",
            "risk_state": "LOW_RISK",
            "fact_check": {"status": "PASS", "critical_unknown_count": 0},
        }

        self.assertEqual(classify_fast_track(base)["status"], "FAST_TRACK_READY")
        for patch in (
            {"score": 74},
            {"locality_state": "needs_verification"},
            {"risk_state": "HOLD"},
            {"fact_check": {"status": "MISSING", "critical_unknown_count": 0}},
            {"fact_check": {"status": "PASS", "critical_unknown_count": 1}},
        ):
            candidate = {**base, **patch}
            self.assertNotEqual(classify_fast_track(candidate)["status"], "FAST_TRACK_READY")

    def test_complete_score_can_reach_fast_track_threshold(self) -> None:
        candidate = {
            "content_id": "post-1",
            "score": 55,
            "locality_state": "direct",
            "risk_state": "LOW_RISK",
            "reasons": ["YIBIN_DIRECT", "INTERACTION_ROBUST_ANOMALY"],
            "fact_check": {"status": "PASS", "critical_unknown_count": 0},
        }

        enriched = enrich_candidate_score(
            candidate,
            hot_rank_up=True,
            cross_platform=True,
            comment_insight_ready=True,
            fact_complete=True,
        )

        self.assertEqual(enriched["score"], 100)
        self.assertEqual(classify_fast_track(enriched)["status"], "FAST_TRACK_READY")

    def test_fact_check_uses_eligible_fact_rows_and_never_stays_missing(self) -> None:
        passed = build_fact_check(
            "宜宾李庄活动上新",
            [
                {
                    "raw_item_id": "fact-1",
                    "source_id": "yibin-gov",
                    "source_tier": "P0",
                    "title": "宜宾李庄活动上新公告",
                    "source_url": "https://example.invalid/fact",
                }
            ],
        )
        missing = build_fact_check("宜宾李庄活动上新", [])

        self.assertEqual(passed["status"], "PASS")
        self.assertEqual(passed["critical_unknown_count"], 0)
        self.assertEqual(missing["status"], "NO_MATCH")
        self.assertNotEqual(missing["status"], "MISSING")
        unrelated = build_fact_check(
            "宜宾",
            [
                {
                    "raw_item_id": "fact-2",
                    "source_id": "yibin-gov",
                    "source_tier": "P0",
                    "title": "完全无关公告",
                    "source_url": "https://example.invalid/unrelated",
                }
            ],
        )
        self.assertEqual(unrelated["status"], "NO_MATCH")

    def test_fact_check_requires_same_subject_place_and_core_event(self) -> None:
        weather_rows = [
            {
                "raw_item_id": "weather-1",
                "source_id": "weather-nmc-sichuan-alert",
                "source_tier": "P1",
                "title": "四川省宜宾市发布暴雨黄色预警",
                "summary": "部分地区有强降雨",
                "source_url": "https://example.invalid/weather",
            }
        ]
        for topic in (
            "旺苍佛子岩文物石刻造像被盗 📍四川省宜宾市",
            "永远不要欺负善良厚道的人 📍四川省宜宾市",
            "绝对是庸医，医生说我肝不好 📍四川省宜宾市",
        ):
            self.assertEqual(build_fact_check(topic, weather_rows)["status"], "NO_MATCH", topic)

        matching = build_fact_check(
            "宜宾中渡口片区正式启动施工",
            [
                {
                    "raw_item_id": "fact-project",
                    "source_id": "yibin-gov",
                    "source_tier": "P0",
                    "title": "宜宾中渡口片区正式启动施工",
                    "summary": "城市更新建设进入实施阶段",
                    "source_url": "https://example.invalid/project",
                }
            ],
        )
        self.assertEqual(matching["status"], "PASS")

    def test_high_speed_rail_claim_cannot_bind_traffic_control_or_photo_story(self) -> None:
        rows = [
            {"raw_item_id": "road", "source_id": "police", "source_tier": "P0",
             "title": "关于对叙州区田坝街部分路段实施临时交通管制的通告",
             "summary": "宜宾项目施工期间道路交通调整", "source_url": "https://e/road"},
            {"raw_item_id": "photo", "source_id": "media", "source_tier": "P1",
             "title": "光影落处便是家 世界摄影日海报特辑",
             "summary": "作品提到宜宾高铁建设", "source_url": "https://e/photo"},
        ]

        result = build_fact_check("渝昆高铁宜宾段通车时间和施工进度", rows)

        self.assertEqual(result["status"], "NO_MATCH")

        unrelated_activity = build_fact_check(
            "#YSL香港活动# 你的兵宜宾醉醉虾来啦",
            [
                {
                    "raw_item_id": "fact-activity",
                    "source_id": "yibin-official",
                    "source_tier": "P0",
                    "title": "宜宾中渡口片区更新建设活动启动",
                    "summary": "中渡口片区启动建设",
                    "source_url": "https://example.com/activity",
                }
            ],
        )
        self.assertEqual(unrelated_activity["status"], "NO_MATCH")

    def test_sanitizer_removes_embedded_identity_metadata_and_phone(self) -> None:
        item = sanitize_content_item(
            {
                "unique_id": "wrapped-post",
                "title": "宜宾城市更新有新进展",
                "content": (
                    "摘要：宜宾城市更新有新进展 "
                    "账号昵称：普通用户 用户ID：123456 用户平台号：abc123 "
                    "联系电话：13800138000 命中地域：宜宾市"
                ),
                "platform": "头条",
            },
            collected_at="2026-08-22T09:00:00+08:00",
        )

        excerpt = item["content_excerpt"]
        for forbidden in ("账号昵称", "用户ID", "用户平台号", "联系电话", "13800138000"):
            self.assertNotIn(forbidden, excerpt)

    def test_risk_gate_holds_user_excluded_topics(self) -> None:
        for title in (
            "宜宾学生校园爆料",
            "宜宾护士维权",
            "宜宾儿童疾病求助",
            "宜宾投资理财讨论",
            "宜宾噪音扰民被行政拘留",
            "四川宜宾驼背女孩筹手术费",
            "四川宜宾升学宴突发墙体坍塌",
            "5死17伤的悲剧",
            "马边县城遭水灾",
            "马边遭暴雨后县城被淹",
            "山洪导致城区内涝，救援正在进行",
        ):
            item = sanitize_content_item(
                {"unique_id": title, "title": title, "platform": "微信"},
                collected_at="2026-08-22T09:00:00+08:00",
            )
            self.assertEqual(item["risk_state"], "HOLD", title)

    def test_daily_summary_contains_required_operator_counts_and_no_draft_reason(self) -> None:
        summary = build_daily_summary(
            collected_count=50,
            new_count=12,
            anomaly_count=2,
            comment_insight_count=1,
            draft_count=0,
            awaiting_confirmation_count=0,
            no_draft_reasons=["FACT_CHECK_NOT_PASS"],
        )

        for label in ("采集数", "新增数", "异常数", "评论洞察数", "稿件数", "等待确认数", "无稿原因"):
            self.assertIn(label, summary)

    def test_operator_board_shows_real_business_fields_and_marks_insufficient_samples(self) -> None:
        board = build_operator_hotspot_board(
            [
                {
                    "content_id": "post-1",
                    "title": "宜宾周末文化活动上新",
                    "platform": "微信",
                    "source_url": "https://example.invalid/post/1",
                    "locality_state": "direct",
                    "score": 50,
                    "rising_state": "CALIBRATION_ONLY",
                    "interaction_delta": None,
                    "reasons": ["YIBIN_DIRECT", "FACT_COMPLETE"],
                }
            ],
            {
                "items": [
                    {
                        "content_id": "post-1",
                        "published_at": "2026-08-22T08:00:00+08:00",
                        "snapshots": [
                            {
                                "collected_at": "2026-08-22T09:00:00+08:00",
                                "view_count": 100,
                                "like_count": 8,
                                "comment_count": 2,
                                "share_count": 1,
                            }
                        ],
                    }
                ]
            },
            collected_at="2026-08-22T09:00:00+08:00",
        )

        for text in (
            "宜宾周末文化活动上新",
            "微信",
            "https://example.invalid/post/1",
            "2026-08-22T08:00:00+08:00",
            "阅读100",
            "点赞8",
            "评论2",
            "转发1",
            "样本不足",
            "50",
            "未入选",
        ):
            self.assertIn(text, board)


if __name__ == "__main__":
    unittest.main()
