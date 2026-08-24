from __future__ import annotations

from datetime import UTC, datetime
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import unittest

from dayibin_auto_publisher.weather_shadow import (
    _fallback_draft,
    merge_observations,
    parse_cap_payload,
    parse_nmc_payload,
    parse_weather_alarm_payload,
    run_weather_shadow,
    validate_weather_publish_response,
    validate_weather_preflight,
    weather_publish_plan,
    weather_publish_prompt,
)


NOW = datetime(2026, 8, 23, 9, 10, tzinfo=UTC)


def cap_item(
    identifier: str,
    *,
    headline: str = "筠连县气象台发布暴雨橙色预警信号[II级/严重]",
    description: str = (
        "筠连县气象台2026年08月23日17时08分发布暴雨橙色预警信号："
        "大雪山镇、联合苗族乡3小时降雨量将达50毫米以上。请注意防范。"
    ),
    message_type: str = "Alert",
    references: str = "",
    severity: str = "orange",
) -> dict[str, object]:
    return {
        "identifier": identifier,
        "description": description,
        "effective": "2026-08-23 17:08:00.0",
        "eventType": "11B03",
        "eventTypeCN": "暴雨事件",
        "expires": "2026-08-24 17:08:00.0",
        "headline": headline,
        "msgType": message_type,
        "note": "",
        "referencesInfo": references,
        "sender": "筠连县气象台",
        "severity": severity,
    }


class WeatherShadowTests(unittest.TestCase):
    def test_cap_parser_keeps_full_yibin_alert_contract(self) -> None:
        identifier = "51152741600000_20260823170800"

        items = parse_cap_payload(json.dumps([cap_item(identifier)]), observed_at=NOW)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["identifier"], identifier)
        self.assertEqual(items[0]["source_id"], "gjzwfw-cma-cap")
        self.assertEqual(items[0]["issuer"], "筠连县气象台")
        self.assertEqual(items[0]["event_type"], "暴雨")
        self.assertEqual(items[0]["severity"], "orange")
        self.assertEqual(items[0]["message_type"], "Alert")
        self.assertEqual(items[0]["area_scope"], ["筠连县"])
        self.assertTrue(items[0]["body_complete"])
        self.assertIn("50毫米", items[0]["description"])

    def test_weather_alarm_parser_filters_to_yibin_and_preserves_identifier(self) -> None:
        payload = {
            "count": "2",
            "data": [
                [
                    "四川省宜宾市筠连县",
                    "101271109-20260823170800-0203.html",
                    "104.51",
                    "28.16",
                    "51152741600000_20260823170800",
                    "51152741600000_20260823170800",
                    "四川省宜宾市筠连县发布暴雨橙色预警信号",
                ],
                [
                    "四川省乐山市犍为县",
                    "101271402-20260823170800-0203.html",
                    "103.94",
                    "29.21",
                    "51112341600000_20260823170800",
                    "51112341600000_20260823170800",
                    "四川省乐山市犍为县发布暴雨橙色预警信号",
                ],
            ],
        }

        items = parse_weather_alarm_payload(
            f"var alarminfo={json.dumps(payload, ensure_ascii=False)};",
            observed_at=NOW,
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["identifier"], "51152741600000_20260823170800")
        self.assertEqual(items[0]["severity"], "orange")
        self.assertEqual(items[0]["event_type"], "暴雨")
        self.assertFalse(items[0]["body_complete"])

    def test_nmc_parser_filters_to_yibin(self) -> None:
        payload = {
            "data": {
                "page": {
                    "list": [
                        {
                            "alertid": "51152741600000_20260823170800",
                            "issuetime": "2026/08/23 17:08",
                            "title": "四川省宜宾市筠连县气象台发布暴雨橙色预警信号",
                            "url": "/publish/alarm/51152741600000_20260823170800.html",
                        },
                        {
                            "alertid": "51112341600000_20260823170800",
                            "issuetime": "2026/08/23 17:08",
                            "title": "四川省乐山市犍为县气象台发布暴雨橙色预警信号",
                            "url": "/publish/alarm/51112341600000_20260823170800.html",
                        },
                    ]
                }
            }
        }

        items = parse_nmc_payload(json.dumps(payload), observed_at=NOW)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["source_id"], "nmc-sichuan-alert")
        self.assertEqual(items[0]["identifier"], "51152741600000_20260823170800")

    def test_merge_uses_cap_body_and_preserves_each_source_first_seen(self) -> None:
        identifier = "51152741600000_20260823170800"
        cap = parse_cap_payload(json.dumps([cap_item(identifier)]), observed_at=NOW)
        weather_payload = {
            "count": "1",
            "data": [[
                "四川省宜宾市筠连县",
                "101271109-20260823170800-0203.html",
                "104.51",
                "28.16",
                identifier,
                identifier,
                "四川省宜宾市筠连县发布暴雨橙色预警信号",
            ]],
        }
        weather = parse_weather_alarm_payload(
            f"var alarminfo={json.dumps(weather_payload, ensure_ascii=False)};",
            observed_at=datetime(2026, 8, 23, 9, 9, 30, tzinfo=UTC),
        )

        merged = merge_observations([*cap, *weather])[identifier]

        self.assertTrue(merged["body_complete"])
        self.assertEqual(merged["description"], cap[0]["description"])
        self.assertEqual(
            set(merged["source_first_seen_at"]),
            {"gjzwfw-cma-cap", "weather-com-cn-alarm"},
        )
        self.assertEqual(merged["first_seen_at"], "2026-08-23T09:09:30+00:00")
        self.assertFalse(merged["has_source_conflict"])

    def test_merge_holds_conflicting_severity(self) -> None:
        identifier = "51152741600000_20260823170800"
        cap = parse_cap_payload(json.dumps([cap_item(identifier)]), observed_at=NOW)
        conflict = {**cap[0], "source_id": "conflict", "severity": "red"}

        merged = merge_observations([*cap, conflict])[identifier]

        self.assertTrue(merged["has_source_conflict"])
        self.assertIn("severity", merged["source_conflicts"])

    def test_first_run_bootstraps_without_cards_and_second_run_creates_one_card(self) -> None:
        old_id = "51152741600000_20260823165508"
        new_id = "51152741600000_20260823170800"
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)

            first = run_weather_shadow(
                data_dir=data_dir,
                now=NOW,
                source_fetchers={
                    "gjzwfw-cma-cap": lambda _now: parse_cap_payload(
                        json.dumps([cap_item(old_id)]), observed_at=NOW
                    )
                },
            )
            second = run_weather_shadow(
                data_dir=data_dir,
                now=NOW,
                source_fetchers={
                    "gjzwfw-cma-cap": lambda _now: parse_cap_payload(
                        json.dumps([cap_item(old_id), cap_item(new_id)]), observed_at=NOW
                    )
                },
            )

            self.assertEqual(first["status"], "BOOTSTRAPPED")
            self.assertEqual(first["confirmation_card_count"], 0)
            self.assertEqual(second["status"], "SHADOW_COMPLETE")
            self.assertEqual(second["confirmation_card_count"], 1)
            self.assertFalse(second["qianfan_called"])
            self.assertFalse(second["production_queue_write"])
            cards = list((data_dir / "confirmation-cards").glob("*.json"))
            self.assertEqual(len(cards), 1)
            card = json.loads(cards[0].read_text(encoding="utf-8"))
            self.assertEqual(card["identifier"], new_id)
            self.assertEqual(card["suggested_vest_name"], "forever21")
            self.assertEqual(card["document_type"], "突发应急安全")
            self.assertEqual(card["editor_route"], "采采呀")
            self.assertIn("筠连县", card["draft"]["title"])
            self.assertIn("50毫米", card["draft"]["html"])
            self.assertFalse((data_dir / "production-publish-queue.json").exists())

    def test_update_or_cancel_without_known_reference_is_held(self) -> None:
        update_id = "51152741600000_20260823170800"
        update = cap_item(
            update_id,
            headline="筠连县气象台更新暴雨橙色预警信号[II级/严重]",
            description="筠连县气象台2026年08月23日17时08分更新暴雨橙色预警信号。",
            message_type="Update",
            references="51152741600000_20260823165508",
        )
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            run_weather_shadow(
                data_dir=data_dir,
                now=NOW,
                source_fetchers={"gjzwfw-cma-cap": lambda _now: []},
            )

            result = run_weather_shadow(
                data_dir=data_dir,
                now=NOW,
                source_fetchers={
                    "gjzwfw-cma-cap": lambda _now: parse_cap_payload(
                        json.dumps([update]), observed_at=NOW
                    )
                },
            )

            self.assertEqual(result["confirmation_card_count"], 0)
            self.assertEqual(result["held_count"], 1)
            self.assertIn("missing_reference", result["held_reasons"])

    def test_one_source_failure_does_not_block_successful_source(self) -> None:
        identifier = "51152741600000_20260823170800"

        def failed(_now: datetime) -> list[dict[str, object]]:
            raise RuntimeError("network down")

        with tempfile.TemporaryDirectory() as temporary:
            result = run_weather_shadow(
                data_dir=Path(temporary),
                now=NOW,
                source_fetchers={
                    "gjzwfw-cma-cap": lambda _now: parse_cap_payload(
                        json.dumps([cap_item(identifier)]), observed_at=NOW
                    ),
                    "nmc-sichuan-alert": failed,
                },
            )

        self.assertEqual(result["successful_source_count"], 1)
        self.assertEqual(result["failed_source_count"], 1)
        self.assertFalse(result["qianfan_called"])

    def test_concurrent_duplicate_alert_creates_only_one_card(self) -> None:
        identifier = "51152741600000_20260823170800"
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            run_weather_shadow(
                data_dir=data_dir,
                now=NOW,
                source_fetchers={"gjzwfw-cma-cap": lambda _now: []},
            )

            def run_once() -> dict[str, object]:
                return run_weather_shadow(
                    data_dir=data_dir,
                    now=NOW,
                    source_fetchers={
                        "gjzwfw-cma-cap": lambda _now: parse_cap_payload(
                            json.dumps([cap_item(identifier)]), observed_at=NOW
                        )
                    },
                )

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(lambda _value: run_once(), range(2)))

            self.assertEqual(sum(result["confirmation_card_count"] for result in results), 1)
            self.assertEqual(len(list((data_dir / "confirmation-cards").glob("*.json"))), 1)

    def test_header_only_alert_becomes_card_when_cap_body_arrives(self) -> None:
        identifier = "51152741600000_20260823170800"
        weather_payload = {
            "count": "1",
            "data": [[
                "四川省宜宾市筠连县",
                "101271109-20260823170800-0203.html",
                "104.51",
                "28.16",
                identifier,
                identifier,
                "四川省宜宾市筠连县发布暴雨橙色预警信号",
            ]],
        }
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            run_weather_shadow(
                data_dir=data_dir,
                now=NOW,
                source_fetchers={"gjzwfw-cma-cap": lambda _now: []},
            )
            held = run_weather_shadow(
                data_dir=data_dir,
                now=NOW,
                source_fetchers={
                    "weather-com-cn-alarm": lambda _now: parse_weather_alarm_payload(
                        f"var alarminfo={json.dumps(weather_payload, ensure_ascii=False)};",
                        observed_at=NOW,
                    )
                },
            )
            ready = run_weather_shadow(
                data_dir=data_dir,
                now=NOW,
                source_fetchers={
                    "gjzwfw-cma-cap": lambda _now: parse_cap_payload(
                        json.dumps([cap_item(identifier)]), observed_at=NOW
                    )
                },
            )

            self.assertEqual(held["held_reasons"], ["incomplete_body"])
            self.assertEqual(ready["confirmation_card_count"], 1)

    def test_auto_publish_arms_then_publishes_only_a_future_alert_once(self) -> None:
        old_id = "51152741600000_20260823165508"
        new_id = "51152741600000_20260823170800"
        calls: list[dict[str, object]] = []

        def publisher(card: dict[str, object]) -> dict[str, object]:
            calls.append(card)
            return {
                "status": "PUBLISHED_VERIFIED",
                "tid": "950001",
                "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=950001",
                "vest_name": "forever21",
                "forum_name": "大美宜宾",
                "type_name": "无",
                "published_at": "2026-08-23T17:11:00+08:00",
            }

        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            run_weather_shadow(
                data_dir=data_dir,
                now=NOW,
                source_fetchers={
                    "gjzwfw-cma-cap": lambda _now: parse_cap_payload(
                        json.dumps([cap_item(old_id)]), observed_at=NOW
                    )
                },
            )
            armed = run_weather_shadow(
                data_dir=data_dir,
                now=NOW,
                source_fetchers={
                    "gjzwfw-cma-cap": lambda _now: parse_cap_payload(
                        json.dumps([cap_item(old_id)]), observed_at=NOW
                    )
                },
                publish=True,
                publisher=publisher,
            )
            published = run_weather_shadow(
                data_dir=data_dir,
                now=datetime(2026, 8, 23, 9, 11, tzinfo=UTC),
                source_fetchers={
                    "gjzwfw-cma-cap": lambda _now: parse_cap_payload(
                        json.dumps([cap_item(old_id), cap_item(new_id)]), observed_at=_now
                    )
                },
                publish=True,
                publisher=publisher,
            )
            repeated = run_weather_shadow(
                data_dir=data_dir,
                now=datetime(2026, 8, 23, 9, 12, tzinfo=UTC),
                source_fetchers={
                    "gjzwfw-cma-cap": lambda _now: parse_cap_payload(
                        json.dumps([cap_item(old_id), cap_item(new_id)]), observed_at=_now
                    )
                },
                publish=True,
                publisher=publisher,
            )

            self.assertEqual(armed["status"], "AUTO_PUBLISH_ARMED")
            self.assertEqual(len(calls), 1)
            self.assertEqual(published["published_count"], 1)
            self.assertTrue(published["qianfan_called"])
            self.assertFalse(published["push_called"])
            self.assertEqual(repeated["published_count"], 0)
            rows = {
                row["identifier"]: row
                for row in (
                    json.loads(line)
                    for line in (data_dir / "alert-ledger.jsonl").read_text().splitlines()
                )
            }
            self.assertEqual(rows[old_id]["shadow_state"], "BASELINED")
            self.assertEqual(rows[new_id]["shadow_state"], "PUBLISHED_VERIFIED")
            self.assertEqual(rows[new_id]["tid"], "950001")

    def test_unknown_publish_result_is_never_automatically_retried(self) -> None:
        identifier = "51152741600000_20260823170800"
        calls = 0

        def uncertain(_card: dict[str, object]) -> dict[str, object]:
            nonlocal calls
            calls += 1
            raise RuntimeError("connection closed after request")

        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            run_weather_shadow(
                data_dir=data_dir,
                now=NOW,
                source_fetchers={"gjzwfw-cma-cap": lambda _now: []},
                publish=True,
                publisher=uncertain,
            )
            first = run_weather_shadow(
                data_dir=data_dir,
                now=datetime(2026, 8, 23, 9, 11, tzinfo=UTC),
                source_fetchers={
                    "gjzwfw-cma-cap": lambda _now: parse_cap_payload(
                        json.dumps([cap_item(identifier)]), observed_at=_now
                    )
                },
                publish=True,
                publisher=uncertain,
            )
            second = run_weather_shadow(
                data_dir=data_dir,
                now=datetime(2026, 8, 23, 9, 12, tzinfo=UTC),
                source_fetchers={
                    "gjzwfw-cma-cap": lambda _now: parse_cap_payload(
                        json.dumps([cap_item(identifier)]), observed_at=_now
                    )
                },
                publish=True,
                publisher=uncertain,
            )

            self.assertEqual(calls, 1)
            self.assertEqual(first["publish_unknown_count"], 1)
            self.assertEqual(second["publish_unknown_count"], 0)
            row = json.loads((data_dir / "alert-ledger.jsonl").read_text().splitlines()[0])
            self.assertEqual(row["shadow_state"], "PUBLISH_RESULT_UNKNOWN")
            self.assertFalse(first["push_called"])

    def test_reenable_rearms_without_publishing_cards_created_while_paused(self) -> None:
        identifier = "51152741600000_20260823170800"
        calls = 0

        def publisher(_card: dict[str, object]) -> dict[str, object]:
            nonlocal calls
            calls += 1
            return {}

        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            run_weather_shadow(
                data_dir=data_dir,
                now=NOW,
                source_fetchers={"gjzwfw-cma-cap": lambda _now: []},
                publish=True,
                publisher=publisher,
            )
            run_weather_shadow(
                data_dir=data_dir,
                now=datetime(2026, 8, 23, 9, 11, tzinfo=UTC),
                source_fetchers={
                    "gjzwfw-cma-cap": lambda _now: parse_cap_payload(
                        json.dumps([cap_item(identifier)]), observed_at=_now
                    )
                },
            )
            rearmed = run_weather_shadow(
                data_dir=data_dir,
                now=datetime(2026, 8, 23, 9, 12, tzinfo=UTC),
                source_fetchers={
                    "gjzwfw-cma-cap": lambda _now: parse_cap_payload(
                        json.dumps([cap_item(identifier)]), observed_at=_now
                    )
                },
                publish=True,
                publisher=publisher,
            )

            self.assertEqual(rearmed["status"], "AUTO_PUBLISH_ARMED")
            self.assertEqual(rearmed["published_count"], 0)
            self.assertEqual(calls, 0)

    def test_cancel_fallback_title_cannot_masquerade_as_new_alert(self) -> None:
        event = parse_cap_payload(
            json.dumps([
                cap_item(
                    "51152741600000_20260823170800",
                    headline="筠连县气象台解除暴雨橙色预警信号",
                    description="筠连县气象台解除暴雨橙色预警信号。",
                    message_type="Cancel",
                    references="51152741600000_20260823165508",
                )
            ]),
            observed_at=NOW,
        )[0]

        draft = _fallback_draft(event)

        self.assertIn("解除", draft["title"])
        self.assertNotIn("发布", draft["title"])

    def test_publish_contract_forbids_push_and_requires_live_metadata(self) -> None:
        identifier = "51152741600000_20260823170800"
        card = {
            "identifier": identifier,
            "draft": {
                "title": "刚刚！筠连县发布暴雨橙色预警！",
                "html": "<p>筠连县气象台发布暴雨橙色预警。</p>",
            },
        }
        plan = weather_publish_plan(card)
        preflight = validate_weather_preflight({identifier: {
            "vest_name": "forever21",
            "vest_unique": True,
            "vest_enabled": True,
            "vest_id_present": True,
            "forum_name": "大美宜宾",
            "forum_unique": True,
            "forum_id_present": True,
            "type_required": False,
            "type_name": "无",
            "type_id_present": False,
        }}, identifier)
        prompt = weather_publish_prompt(card, preflight)
        response = {"publish_result": {
            "status": "published",
            "tid": "950001",
            "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=950001",
            "vest_name": "forever21",
            "forum_name": "大美宜宾",
            "type_name": "无",
            "title_verified": True,
            "body_verified": True,
            "vest_verified": True,
            "public_http_ok": True,
            "published_at": "2026-08-23T17:11:00+08:00",
            "push_called": False,
        }}
        metadata = {
            "tid": "950001",
            "title": card["draft"]["title"],
            "vest_name": "forever21",
            "forum_name": "大美宜宾",
            "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=950001",
            "published_at": "2026-08-23T17:11:00+08:00",
        }

        result = validate_weather_publish_response(response, card, preflight, metadata)

        self.assertEqual(plan["forum_hint"], "大美宜宾")
        self.assertIn('"push": false', prompt)
        self.assertIn("不得调用 Push", prompt)
        self.assertEqual(result["status"], "PUBLISHED_VERIFIED")


if __name__ == "__main__":
    unittest.main()
