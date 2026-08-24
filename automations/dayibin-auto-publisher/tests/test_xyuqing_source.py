import json
from pathlib import Path
import tempfile
import unittest

from dayibin_auto_publisher.xyuqing_source import (
    OPTIONAL_METADATA_ENDPOINTS,
    RUNTIME_READONLY_ENDPOINTS,
    XyuqingAuthRequired,
    XyuqingEndpointNotAllowed,
    XyuqingSchemaError,
    XyuqingSourceError,
    XyuqingUiUnavailable,
    assert_endpoint_allowed,
    classify_locality,
    deduplicate_items,
    normalize_signal,
    parse_ego_result,
    parse_cy_list_response,
    parse_post_list_response,
    parse_rank_response,
    redact_sensitive_text,
    require_auth_ok,
    run_round_with_fallback,
    validate_ui_bundle,
    write_round_bundle,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "xyuqing_source_contracts.json"


class XyuqingSourceContractTests(unittest.TestCase):
    def test_runtime_whitelist_is_exactly_three_post_endpoints(self) -> None:
        self.assertEqual(
            RUNTIME_READONLY_ENDPOINTS,
            frozenset(
                {
                    ("POST", "/service/rank/rank"),
                    ("POST", "/service/rank/cy_list"),
                    ("POST", "/service/search/post_list"),
                }
            ),
        )

    def test_city_metadata_is_optional_and_plan_list_is_always_rejected(self) -> None:
        self.assertEqual(
            OPTIONAL_METADATA_ENDPOINTS,
            frozenset({("GET", "/service/rank/hot_search_city_list")}),
        )
        assert_endpoint_allowed("GET", "/service/rank/hot_search_city_list", purpose="metadata")
        with self.assertRaises(XyuqingEndpointNotAllowed):
            assert_endpoint_allowed("GET", "/service/rank/hot_search_city_list", purpose="runtime")
        with self.assertRaises(XyuqingEndpointNotAllowed):
            assert_endpoint_allowed("POST", "/service/plan/list", purpose="runtime")

    def test_wrong_methods_and_unknown_paths_are_rejected(self) -> None:
        for method, path in (
            ("GET", "/service/rank/rank"),
            ("GET", "/service/search/post_list"),
            ("POST", "/service/rank/unknown"),
        ):
            with self.subTest(method=method, path=path):
                with self.assertRaises(XyuqingEndpointNotAllowed):
                    assert_endpoint_allowed(method, path, purpose="runtime")

    def test_missing_token_http_auth_errors_and_business_code_fail_closed(self) -> None:
        cases = (
            {"token_present": False, "http_status": 200, "payload": {"code": 0}},
            {"token_present": True, "http_status": 401, "payload": {}},
            {"token_present": True, "http_status": 403, "payload": {}},
            {"token_present": True, "http_status": 200, "payload": {"code": 20001}},
        )
        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(XyuqingAuthRequired):
                    require_auth_ok(**case)

    def test_chengdu_and_sichuan_only_noise_fail_the_yibin_gate(self) -> None:
        cases = (
            {"title": "成都商圈活动上新", "city_requested": "四川 - 宜宾"},
            {"title": "成都高新区活动上新", "city_requested": "四川 - 宜宾"},
            {"title": "四川文旅热度上升", "city_requested": "四川 - 宜宾"},
        )
        for item in cases:
            with self.subTest(item=item):
                self.assertEqual(classify_locality(item), "rejected")

    def test_yibin_district_poi_and_local_source_evidence_pass(self) -> None:
        cases = (
            {"title": "宜宾城区公交有调整"},
            {"title": "叙州区新增便民服务点"},
            {"title": "出行提示", "poi_name": "宜宾西站"},
            {"title": "城市更新", "source_name": "宜宾市融媒体中心"},
        )
        for item in cases:
            with self.subTest(item=item):
                self.assertEqual(classify_locality(item), "direct")

    def test_deduplicates_by_each_documented_stable_key(self) -> None:
        items = [
            {"id": "u1", "unique_id": "same-u"},
            {"id": "u2", "unique_id": "same-u"},
            {"id": "n1", "unity_id": "same-n"},
            {"id": "n2", "unity_id": "same-n"},
            {"id": "s1", "similar_id": "same-s"},
            {"id": "s2", "similar_id": "same-s"},
            {"id": "url1", "url": "https://example.invalid/post/1"},
            {"id": "url2", "url": "https://example.invalid/post/1"},
            {"id": "h1", "content_hash": "same-h"},
            {"id": "h2", "content_hash": "same-h"},
        ]

        self.assertEqual(
            [item["id"] for item in deduplicate_items(items)],
            ["u1", "n1", "s1", "url1", "h1"],
        )

    def test_missing_fields_and_type_changes_are_schema_errors(self) -> None:
        invalid = (
            {"code": 0, "data": {}},
            {"code": 0, "data": {"post": "not-an-array"}},
            {"code": 0, "data": {"post": [{"list": {}}]}},
        )
        for payload in invalid:
            with self.subTest(payload=payload):
                with self.assertRaises(XyuqingSchemaError):
                    parse_rank_response(payload)

    def test_cy_list_accepts_normal_and_empty_lists_and_rejects_invalid_lists(self) -> None:
        cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["parser_cases"]

        self.assertEqual(
            parse_cy_list_response(cases["cy_list_normal"]["response"]),
            [{"name": "synthetic-city-entry", "value": 1}],
        )
        self.assertEqual(parse_cy_list_response(cases["cy_list_empty"]["response"]), [])
        for name in ("cy_list_missing", "cy_list_wrong_type"):
            with self.subTest(name=name):
                with self.assertRaises(XyuqingSchemaError):
                    parse_cy_list_response(cases[name]["response"])

    def test_post_list_accepts_content_and_empty_lists_and_rejects_summary_or_invalid_lists(self) -> None:
        cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["parser_cases"]

        content = parse_post_list_response(cases["post_list_content"]["response"], return_type=1)
        self.assertEqual([item["unique_id"] for item in content], ["synthetic-post-1"])
        self.assertEqual(
            parse_post_list_response(cases["post_list_empty"]["response"], return_type=1),
            [],
        )
        for name, return_type in (
            ("post_list_summary", 2),
            ("post_list_missing", 1),
            ("post_list_wrong_type", 1),
        ):
            with self.subTest(name=name):
                with self.assertRaises(XyuqingSchemaError):
                    parse_post_list_response(cases[name]["response"], return_type=return_type)

    def test_html_login_page_is_an_auth_failure(self) -> None:
        with self.assertRaises(XyuqingAuthRequired):
            parse_rank_response("<html><input type='password'></html>")

    def test_bearer_and_ego_ui_normalize_to_the_same_source_unit_schema(self) -> None:
        item = {
            "id": "synthetic-rank-1",
            "title": "宜宾城区公交有调整",
            "platform": "douyin_city",
            "rank": 5,
            "score": 100,
            "strtotime": 1787187600,
            "kw_url": "https://example.invalid/search",
        }
        kwargs = {
            "city_requested": "四川 - 宜宾",
            "collected_at": "2026-08-20T12:00:00+08:00",
        }

        bearer = normalize_signal(item, access_path="bearer", **kwargs)
        ego_ui = normalize_signal(item, access_path="ego_ui", **kwargs)

        self.assertEqual(set(bearer), set(ego_ui))
        self.assertEqual(bearer["signal_id"], ego_ui["signal_id"])
        self.assertEqual(bearer["write_eligibility"], "signal_only")
        self.assertEqual({bearer["access_path"], ego_ui["access_path"]}, {"bearer", "ego_ui"})

    def test_redaction_removes_authorization_and_cookie_values(self) -> None:
        redacted = redact_sensitive_text("Authorization: Bearer x\nCookie: y")

        self.assertNotIn("Bearer x", redacted)
        self.assertNotIn("Cookie: y", redacted)

    def test_ego_stdout_accepts_only_sentinel_business_json_without_credentials(self) -> None:
        bundle = {"auth_status": "AUTH_OK", "requests": [], "rank": {}, "cy_list": {}, "related": []}

        self.assertEqual(
            parse_ego_result("ego startup\nXYUQING_RESULT_JSON=" + json.dumps(bundle)),
            bundle,
        )
        for output in (
            "Authorization: Bearer x\nXYUQING_RESULT_JSON={}",
            "Cookie: y\nXYUQING_RESULT_JSON={}",
            'XYUQING_RESULT_JSON={"token":"x"}',
            "missing sentinel",
        ):
            with self.subTest(output=output):
                with self.assertRaises(XyuqingSourceError):
                    parse_ego_result(output)

    def test_unobtainable_empty_states_are_explicitly_synthetic(self) -> None:
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(payload["fixture_origin"], "synthetic")
        self.assertTrue(payload["synthetic"])
        self.assertFalse(payload["live_response"])
        self.assertEqual(set(payload["cases"]), {"optional_city_metadata_empty", "excluded_plan_list_empty"})
        for case in payload["cases"].values():
            self.assertEqual(case["provenance"], "synthetic")
            self.assertTrue(case["synthetic"])
            self.assertFalse(case["live_response"])
            self.assertTrue(case["n_a_reason"])

    def test_round_bundle_writes_idempotent_signal_and_redacted_report(self) -> None:
        bundle = {
            "auth_status": "AUTH_OK",
            "duration_ms": 120,
            "requests": [
                {"method": "POST", "path": "/service/rank/rank", "http_status": 200},
                {"method": "POST", "path": "/service/rank/cy_list", "http_status": 200},
                {"method": "POST", "path": "/service/search/post_list", "http_status": 200},
            ],
            "rank": {
                "code": 0,
                "data": {
                    "post": [
                        {
                            "list": [
                                {
                                    "id": "rank-local",
                                    "title": "宜宾城区公交有调整",
                                    "platform": "douyin_city",
                                    "rank": 5,
                                    "score": 100,
                                    "strtotime": 1787187600,
                                    "kw_url": "https://example.invalid/search/local",
                                },
                                {
                                    "id": "rank-noise",
                                    "title": "成都商圈活动上新",
                                    "platform": "douyin_city",
                                    "rank": 6,
                                    "score": 90,
                                    "strtotime": 1787187600,
                                    "kw_url": "https://example.invalid/search/noise",
                                },
                            ]
                        }
                    ]
                },
            },
            "cy_list": {"code": 0, "data": {"list": [{"name": "synthetic", "value": 1}]}},
            "related": [
                {
                    "rank_id": "rank-local",
                    "response": {
                        "code": 0,
                        "data": {
                            "list": [
                                {
                                    "unique_id": "related-1",
                                    "url": "https://example.invalid/post/1",
                                }
                            ]
                        },
                    },
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            first = write_round_bundle(
                bundle,
                data_dir=Path(tmp),
                business_date="2026-08-20",
                collected_at="2026-08-20T14:30:00+08:00",
            )
            changed_bundle = json.loads(json.dumps(bundle))
            changed_item = changed_bundle["rank"]["data"]["post"][0]["list"][0]
            changed_item.update({"rank": 2, "score": 120, "strtotime": 1787189400})
            second = write_round_bundle(
                changed_bundle,
                data_dir=Path(tmp),
                business_date="2026-08-20",
                collected_at="2026-08-20T15:00:00+08:00",
            )
            signals = json.loads(Path(first["signals_path"]).read_text(encoding="utf-8"))
            report = json.loads(Path(first["report_path"]).read_text(encoding="utf-8"))

        self.assertEqual(len(signals["signals"]), 1)
        self.assertEqual(signals["signals"][0]["write_eligibility"], "signal_only")
        self.assertEqual(signals["signals"][0]["current_rank"], 2)
        self.assertEqual(signals["signals"][0]["related_source_urls"], ["https://example.invalid/post/1"])
        self.assertEqual(report["auth_status"], "AUTH_OK")
        self.assertEqual(report["locality_pass_count"], 1)
        self.assertEqual(second["signal_count"], 1)
        self.assertNotIn("token", json.dumps({"signals": signals, "report": report}).lower())

    def test_schema_failure_uses_ui_fallback_with_the_same_signal_schema(self) -> None:
        ui_calls = 0

        def primary():
            raise XyuqingSchemaError("simulated primary schema failure")

        def ui():
            nonlocal ui_calls
            ui_calls += 1
            return self._ui_bundle()

        with tempfile.TemporaryDirectory() as tmp:
            result = run_round_with_fallback(
                primary_fetch=primary,
                ui_fetch=ui,
                data_dir=Path(tmp),
                business_date="2026-08-20",
                collected_at="2026-08-20T15:00:00+08:00",
            )
            signals = json.loads(Path(result["signals_path"]).read_text(encoding="utf-8"))
            report = json.loads(Path(result["report_path"]).read_text(encoding="utf-8"))

        self.assertEqual(ui_calls, 1)
        self.assertEqual({signal["access_path"] for signal in signals["signals"]}, {"ego_ui"})
        self.assertTrue(report["ui_fallback_used"])
        self.assertEqual(report["primary_failure"], "SCHEMA_ERROR")

    def test_auth_failure_never_uses_ui_fallback(self) -> None:
        ui_calls = 0

        def primary():
            raise XyuqingAuthRequired("XYUQING_AUTH_REQUIRED")

        def ui():
            nonlocal ui_calls
            ui_calls += 1
            return self._ui_bundle()

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(XyuqingAuthRequired):
                run_round_with_fallback(
                    primary_fetch=primary,
                    ui_fetch=ui,
                    data_dir=Path(tmp),
                    business_date="2026-08-20",
                    collected_at="2026-08-20T15:00:00+08:00",
                )

        self.assertEqual(ui_calls, 0)

    def test_ui_fallback_is_hourly_and_opens_circuit_after_two_failures(self) -> None:
        ui_calls = 0

        def primary():
            raise XyuqingSchemaError("simulated primary schema failure")

        def ui():
            nonlocal ui_calls
            ui_calls += 1
            raise XyuqingUiUnavailable("simulated UI failure")

        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            with self.assertRaises(XyuqingUiUnavailable):
                run_round_with_fallback(
                    primary_fetch=primary,
                    ui_fetch=ui,
                    data_dir=data_dir,
                    business_date="2026-08-20",
                    collected_at="2026-08-20T15:00:00+08:00",
                )
            with self.assertRaisesRegex(XyuqingUiUnavailable, "hourly"):
                run_round_with_fallback(
                    primary_fetch=primary,
                    ui_fetch=ui,
                    data_dir=data_dir,
                    business_date="2026-08-20",
                    collected_at="2026-08-20T15:30:00+08:00",
                )
            with self.assertRaises(XyuqingUiUnavailable):
                run_round_with_fallback(
                    primary_fetch=primary,
                    ui_fetch=ui,
                    data_dir=data_dir,
                    business_date="2026-08-20",
                    collected_at="2026-08-20T16:01:00+08:00",
                )
            report = json.loads(
                (data_dir / "2026-08-20" / "xyuqing-run-report.json").read_text(encoding="utf-8")
            )

        self.assertEqual(ui_calls, 2)
        self.assertEqual(report["ui_consecutive_failures"], 2)
        self.assertTrue(report["circuit_open"])

    def test_ui_bundle_requires_nonzero_viewport_and_fixed_page_state(self) -> None:
        bundle = self._ui_bundle()
        validate_ui_bundle(bundle)
        for key, value in (
            ("viewport", [0, 0]),
            ("selected_tab", "综合热榜"),
            ("city_selected", "四川 - 成都"),
            ("time_selected", "今日"),
        ):
            invalid = {**bundle, key: value}
            with self.subTest(key=key):
                with self.assertRaises(XyuqingUiUnavailable):
                    validate_ui_bundle(invalid)

    @staticmethod
    def _ui_bundle() -> dict[str, object]:
        return {
            "auth_status": "AUTH_OK",
            "access_path": "ego_ui",
            "viewport": [1920, 1080],
            "selected_tab": "同城热榜",
            "city_selected": "四川 - 宜宾",
            "time_selected": "近24h",
            "requests": [],
            "rank": {
                "code": 0,
                "data": {
                    "post": [
                        {
                            "list": [
                                {
                                    "id": "ui-rank-1",
                                    "title": "宜宾城区公交有调整",
                                    "platform": "douyin_city",
                                    "rank": 5,
                                    "score": 100,
                                    "first_seen_at": "2026-08-20T14:00:00+08:00",
                                    "kw_url": "https://www.xyuqing.com/search/info?word=synthetic",
                                }
                            ]
                        }
                    ]
                },
            },
            "cy_list": {"code": 0, "data": {"list": [{"name": "四川 - 宜宾", "value": "宜宾"}]}},
            "related": [],
        }


if __name__ == "__main__":
    unittest.main()
