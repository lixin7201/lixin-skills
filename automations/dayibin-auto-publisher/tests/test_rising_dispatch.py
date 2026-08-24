from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from dayibin_auto_publisher.config import PipelineConfig
from dayibin_auto_publisher.rising_dispatch import (
    RisingDispatchError,
    _assign_profiles,
    _claim_key,
    _generate_reviewed_drafts,
    _maybe_create_batch,
    _quality_incident_candidates,
    _select_watch_target,
    _validate_angle_cards,
    _validate_draft,
    _validate_route,
    _validate_soft_audit,
    _review_binding_hashes,
    _recover_stale_claims,
    _sync_claims_with_batch_statuses,
    _watch_query,
    dispatch_rising,
)
from dayibin_auto_publisher.xyuqing_source import XyuqingAuthRequired


class FakeAgent:
    def __init__(self, response: dict[str, object] | list[dict[str, object]]) -> None:
        self.responses = list(response) if isinstance(response, list) else [response]
        self.calls: list[tuple[str, str]] = []

    def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
        self.calls.append((prompt, session_id))
        return self.responses.pop(0)


class RisingDispatchTests(unittest.TestCase):
    def test_title_only_material_is_rejected_before_agent_call_even_without_level_field(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._config(root)
            monitor = root / "data" / "2026-08-22" / "rising-monitor"
            monitor.mkdir(parents=True)
            monitor.joinpath("business-channels.json").write_text(json.dumps({
                "hot_now": [], "daily_value": [{
                    "content_id": "title-only", "title": "宜宾项目有新进展",
                    "body_snapshot": "视频新闻：宜宾项目有新进展。来源：宜宾新闻。官方详情未提供文字正文。",
                    "source_url": "https://e/title-only", "channel": "DAILY_VALUE",
                    "ready_status": "READY_FOR_ANGLE", "locality_state": "direct",
                    "risk_state": "LOW_RISK", "fact_check": {"status": "PASS"}, "images": [],
                }],
            }), encoding="utf-8")
            agent = FakeAgent([])

            result = _maybe_create_batch(
                config, day="2026-08-22", now=datetime(2026, 8, 22, 4, 0, tzinfo=UTC),
                agent=agent, daily_pool=True,
            )

            self.assertEqual(result["draft_count"], 0)
            self.assertEqual(result["reason"], "TITLE_LEVEL_REQUIRES_SUPPLEMENT")
            self.assertEqual(agent.calls, [])

    def test_legacy_candidate_title_only_material_is_rejected_before_agent_call(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._config(root)
            monitor = root / "data" / "2026-08-22" / "rising-monitor"
            monitor.mkdir(parents=True)
            monitor.joinpath("rising-candidates.json").write_text(json.dumps({
                "candidates": [{
                    "content_id": "legacy-title-only", "title": "宜宾视频新闻有新进展",
                    "body_snapshot": "视频新闻：宜宾视频新闻有新进展。官方详情未提供文字正文。",
                    "source_url": "https://e/legacy", "locality_state": "direct",
                    "risk_state": "LOW_RISK", "fact_check": {"status": "PASS"}, "images": [],
                }],
                "fast_track": [],
            }), encoding="utf-8")
            agent = FakeAgent([])

            result = _maybe_create_batch(
                config, day="2026-08-22", now=datetime(2026, 8, 22, 4, 0, tzinfo=UTC),
                agent=agent, daily_pool=True,
            )

            self.assertEqual(result["draft_count"], 0)
            self.assertEqual(result["reason"], "TITLE_LEVEL_REQUIRES_SUPPLEMENT")
            self.assertEqual(agent.calls, [])

    def test_stale_ready_ugc_is_rechecked_before_claiming(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._config(root)
            monitor = root / "data" / "2026-08-22" / "rising-monitor"
            monitor.mkdir(parents=True)
            text = "宜宾有两个蛆，三江蛆，叙州蛆，请问你们在哪个蛆。"
            monitor.joinpath("business-channels.json").write_text(json.dumps({
                "hot_now": [], "daily_value": [{
                    "content_id": "unsafe-ugc", "title": text, "body_snapshot": text,
                    "content_mode": "UGC_DISCUSSION", "source_url": "https://e/unsafe",
                    "channel": "DAILY_VALUE", "ready_status": "READY_FOR_ANGLE",
                    "risk_state": "LOW_RISK", "fact_check": {"status": "NO_MATCH"},
                    "images": [],
                }],
            }), encoding="utf-8")

            result = _maybe_create_batch(
                config, day="2026-08-22", now=datetime(2026, 8, 22, 4, 0, tzinfo=UTC),
                agent=None, daily_pool=True,
            )

            self.assertEqual(result["draft_count"], 0)
            self.assertFalse((root / "data" / "rising-dispatch-ledger.json").exists())

    def test_superseded_batch_claims_follow_batch_status_without_poisoning_kept_batch(self) -> None:
        with TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            kept = data_dir / "2026-08-23" / "pending-batches" / "BATCH-kept"
            rejected = data_dir / "2026-08-23" / "pending-batches" / "BATCH-rejected"
            scheduled = data_dir / "2026-08-23" / "pending-batches" / "BATCH-scheduled"
            kept.mkdir(parents=True)
            rejected.mkdir(parents=True)
            scheduled.mkdir(parents=True)
            kept.joinpath("batch.json").write_text(json.dumps({
                "status": "AWAITING_HUMAN_SCHEDULE_CONFIRMATION"
            }), encoding="utf-8")
            rejected.joinpath("batch.json").write_text(json.dumps({
                "status": "SUPERSEDED_DUPLICATE_RACE"
            }), encoding="utf-8")
            scheduled.joinpath("batch.json").write_text(json.dumps({
                "status": "SCHEDULED"
            }), encoding="utf-8")
            claims = [
                {"batch_id": "BATCH-kept", "status": "SUPERSEDED_DUPLICATE_RACE"},
                {"batch_id": "BATCH-rejected", "status": "AWAITING_HUMAN_SCHEDULE_CONFIRMATION"},
                {"batch_id": "BATCH-scheduled", "status": "AWAITING_HUMAN_SCHEDULE_CONFIRMATION"},
            ]

            _sync_claims_with_batch_statuses(
                claims, data_dir=data_dir, day="2026-08-23"
            )

            self.assertEqual(claims[0]["status"], "AWAITING_HUMAN_SCHEDULE_CONFIRMATION")
            self.assertEqual(claims[1]["status"], "SUPERSEDED_DUPLICATE_RACE")
            self.assertEqual(claims[2]["status"], "SCHEDULED")

    def test_active_content_id_blocks_duplicate_when_event_claim_key_changes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._config(root)
            monitor = root / "data" / "2026-08-22" / "rising-monitor"
            monitor.mkdir(parents=True)
            monitor.joinpath("business-channels.json").write_text(json.dumps({
                "hot_now": [], "daily_value": [{
                    "content_id": "same-content", "event_id": "new-event", "title": "宜宾独立事实",
                    "source_url": "https://e/new", "channel": "DAILY_VALUE",
                    "ready_status": "READY_FOR_ANGLE", "risk_state": "LOW_RISK",
                    "fact_check": {"status": "PASS"}, "images": [],
                }],
            }), encoding="utf-8")
            (root / "data" / "rising-dispatch-ledger.json").write_text(json.dumps({
                "schema_version": "rising-dispatch-ledger-v1", "claims": [{
                    "content_id": "same-content", "claim_key": "old-event-key",
                    "status": "AWAITING_HUMAN_SCHEDULE_CONFIRMATION",
                    "claimed_at": "2026-08-22T11:00:00+08:00",
                }],
            }), encoding="utf-8")

            result = _maybe_create_batch(
                config, day="2026-08-22", now=datetime(2026, 8, 22, 4, 0, tzinfo=UTC),
                agent=None, daily_pool=True,
            )

            self.assertEqual(result["draft_count"], 0)

    def test_no_draft_claim_is_migrated_to_auditable_cooldown(self) -> None:
        claims = [{
            "status": "NO_DRAFT", "claimed_at": "2026-08-22T12:00:00+08:00",
            "retry_count": 0,
        }]

        _recover_stale_claims(
            claims, now=datetime(2026, 8, 22, 4, 10, tzinfo=UTC), timeout_seconds=900
        )

        self.assertEqual(claims[0]["status"], "GENERATION_FAILED")
        self.assertEqual(claims[0]["stage"], "no_draft_after_route")
        self.assertEqual(claims[0]["retry_count"], 1)
        self.assertTrue(claims[0]["cooldown_until"])

    def test_collect_only_never_enters_generation(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._config(root)
            with patch(
                "dayibin_auto_publisher.rising_dispatch._maybe_create_batch"
            ) as generate:
                result = dispatch_rising(
                    config,
                    evidence_dir=root / "evidence",
                    now=datetime(2026, 8, 22, 4, 0, tzinfo=UTC),
                    bundle_fetcher=lambda: {},
                    round_runner=lambda *_args, **_kwargs: {"status": "READY"},
                    collect_only=True,
                )

            generate.assert_not_called()
            self.assertTrue(result["collect_only"])
            self.assertEqual(result["draft_count"], 0)
            self.assertFalse(result["qianfan_called"])

    def test_reuse_latest_collect_only_never_enters_generation(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._config(root)
            with (
                patch(
                    "dayibin_auto_publisher.rising_dispatch.rebuild_business_outputs",
                    return_value={"event_count": 1, "daily_value": [], "hot_now": [], "rising_watch": []},
                ),
                patch("dayibin_auto_publisher.rising_dispatch.load_fact_rows", return_value=[]),
                patch("dayibin_auto_publisher.rising_dispatch._maybe_create_batch") as generate,
            ):
                result = dispatch_rising(
                    config, now=datetime(2026, 8, 22, 4, 0, tzinfo=UTC),
                    reuse_latest=True, collect_only=True,
                )

            generate.assert_not_called()
            self.assertTrue(result["collect_only"])
            self.assertEqual(result["draft_count"], 0)

    def test_one_candidate_failure_isolated_and_enters_auditable_cooldown(self) -> None:
        class IsolatingAgent:
            def __init__(self) -> None:
                self.calls: list[str] = []

            def run_json(self, prompt: str, *, session_id: str):
                self.calls.append(session_id)
                if "-1-angle-" in session_id:
                    raise RuntimeError("candidate one failed")
                if "angle" in session_id:
                    return {"angle_cards": {"content_id": "c-2", "angles": [
                        {"angle_id": f"A{i}", "status": "READY", "score": 90 - i,
                         "core_question": f"问题{i}", "judgment": f"判断{i}",
                         "reader_benefit": f"收益{i}", "evidence_path": f"证据{i}",
                         "knockout_reasons": []}
                        for i in range(1, 4)
                    ], "locked_angle_id": "A1", "fact_ledger": {"FACT": [], "INFERENCE": [], "UNKNOWN": [], "FORBIDDEN_CLAIM": []}}}
                if "route" in session_id:
                    return {"writing_route": {
                        "content_id": "c-2", "locked_angle_id": "A1", "article_form": "APP_SHORT",
                        "document_type": "本地生活文旅", "material_grade": "medium", "material_action": "WRITE",
                        "target_min_chars": 300, "target_max_chars": 900, "selected_writing_skill": "app-skill",
                        "skill_selection_reason": "本地生活短稿", "editor_name": "泡泡呀",
                        "editor_dna_path": "/Users/REPLACE_ME/.openclaw/workspace/skills/app-skill/references/小编风格/泡泡呀-DNA.md",
                        "editor_selection_reason": "生活化表达", "reason": "短稿足够"}}
                if "soft-audit" in session_id:
                    return {"soft_audit": {"content_id": "c-2", "status": "PASS", "issues": [], "author_skill": "app-skill"}}
                if "review" in session_id:
                    return {"review": {"content_id": "c-2", "verdict": "approved", "score": 8.5,
                        "issues": [], "ai_tone": "PASS", "length_fit": "PASS", "template_overlap": "PASS"}}
                return {"draft": {"content_id": "c-2", "title": "宜宾李庄活动有了新安排",
                    "html": "<p>" + "这次活动的时间和地点已经明确，出行前可以按自己的安排作判断。" * 12 + "</p>",
                    "source_url": "https://e/2", "persona": "", "vest_name": "", "forum": "大宜宾APP",
                    "category": "DAILY_VALUE", "images": [], "risk_result": "PASS", "facts_complete": True,
                    "length_decision": "WITHIN_REFERENCE", "short_length_reason": ""}}

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._config(root)
            monitor = root / "data" / "2026-08-22" / "rising-monitor"
            monitor.mkdir(parents=True)
            monitor.joinpath("business-channels.json").write_text(json.dumps({
                "hot_now": [], "daily_value": [
                    {"content_id": "c-1", "event_id": "e-1", "title": "宜宾活动一", "source_url": "https://e/1",
                     "channel": "DAILY_VALUE", "ready_status": "READY_FOR_ANGLE", "risk_state": "LOW_RISK",
                     "fact_check": {"status": "PASS"}, "images": [], "body_snapshot": "宜宾活动一公布了完整时间地点和参与安排。"},
                    {"content_id": "c-2", "event_id": "e-2", "title": "宜宾李庄活动上新", "source_url": "https://e/2",
                     "channel": "DAILY_VALUE", "ready_status": "READY_FOR_ANGLE", "risk_state": "LOW_RISK",
                     "fact_check": {"status": "PASS"}, "images": [], "body_snapshot": "宜宾李庄活动已公布完整时间、地点和参与安排。"},
                ]}), encoding="utf-8")
            agent = IsolatingAgent()

            result = _maybe_create_batch(
                config, day="2026-08-22", now=datetime(2026, 8, 22, 4, 0, tzinfo=UTC),
                agent=agent, daily_pool=True,
            )

            self.assertEqual(result["draft_count"], 1)
            ledger = json.loads((root / "data" / "rising-dispatch-ledger.json").read_text(encoding="utf-8"))
            failed = next(item for item in ledger["claims"] if item["content_id"] == "c-1")
            self.assertEqual(failed["status"], "GENERATION_FAILED")
            self.assertEqual(failed["stage"], "angle_to_freeze")
            self.assertEqual(failed["retry_count"], 1)
            self.assertTrue(failed["cooldown_until"])

    def test_review_binding_hashes_change_with_every_reviewed_object(self) -> None:
        draft = {"title": "标题", "html": "<p>正文</p>", "image_manifest": []}
        route = {"selected_writing_skill": "app-skill", "editor_dna_path": "N/A"}
        angle = {"angle_id": "A1", "judgment": "判断"}
        baseline = _review_binding_hashes(draft, route, angle)
        variants = (
            ({**draft, "title": "新标题"}, route, angle),
            ({**draft, "html": "<p>新正文</p>"}, route, angle),
            ({**draft, "image_manifest": [{"local_path": "/tmp/a.jpg"}]}, route, angle),
            (draft, {**route, "selected_writing_skill": "wechat-writing-skill"}, angle),
            (draft, route, {**angle, "angle_id": "A2"}),
        )
        for current_draft, current_route, current_angle in variants:
            self.assertNotEqual(_review_binding_hashes(current_draft, current_route, current_angle), baseline)

    def test_business_chain_failures_are_not_cleared_by_a_successful_collection(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._config(root)
            with patch(
                "dayibin_auto_publisher.rising_dispatch._maybe_create_batch",
                side_effect=RuntimeError("freeze failed"),
            ):
                for minute in (0, 30):
                    with self.assertRaises(RisingDispatchError):
                        dispatch_rising(
                            config,
                            evidence_dir=root / "evidence",
                            now=datetime(2026, 8, 22, 4, minute, tzinfo=UTC),
                            bundle_fetcher=lambda: {},
                            round_runner=lambda *_args, **_kwargs: {"status": "READY"},
                        )

            state = json.loads((root / "evidence" / "dispatcher-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "STOPPED_FAIL")
            self.assertEqual(state["consecutive_failures"], 2)

    def test_quality_incident_reroute_keeps_published_revision_and_dedupes_pending_event(self) -> None:
        drafts = [
            {
                "content_id": "published",
                "event_id": "music",
                "fact_material": {"title": "长江公园落日音乐会", "material_excerpt": "音乐会事实"},
            },
            {
                "content_id": "brief",
                "event_id": "charge-brief",
                "fact_material": {
                    "title": "宜宾首个符合3C标准的兆瓦级综合充电站即将上岗",
                    "material_excerpt": "即将投用",
                },
            },
            {
                "content_id": "complete",
                "event_id": "charge-complete",
                "fact_material": {
                    "title": "2026世界动力电池大会丨重卡闪充！宜宾首个符合3C标准兆瓦级综合充电站即将上岗",
                    "material_excerpt": "三江新区东部产业园能源港，2台960kW设备、8个接口，预计月底投用。",
                },
            },
        ]
        queue = [
            {"content_id": "published", "quality_incident": "QUALITY_INCIDENT", "publication_ref": "948582"},
            {"content_id": "brief", "status": "PAUSED_QUALITY_INCIDENT"},
            {"content_id": "complete", "status": "PAUSED_QUALITY_INCIDENT"},
        ]

        selected, dropped = _quality_incident_candidates(
            drafts, queue, now=datetime(2026, 8, 23, 9, 0, tzinfo=UTC)
        )

        self.assertEqual([item["content_id"] for item in selected], ["quality-republish-948582", "complete"])
        self.assertEqual(dropped, ["brief"])
        self.assertEqual(selected[0]["replaces_publication_ref"], "948582")

    def test_review_can_return_once_to_the_same_writer_and_must_pass_second_review(self) -> None:
        body = "<p>" + "宜宾本地活动信息清楚，读者可以按公开安排判断是否前往。" * 14 + "</p>"
        draft = {
            "content_id": "c-1", "title": "宜宾活动安排", "html": body,
            "source_url": "https://example.com/c-1", "persona": "城市观察室型",
            "vest_name": "", "forum": "大宜宾APP", "category": "DAILY_VALUE",
            "images": [], "risk_result": "PASS", "facts_complete": True,
            "length_decision": "WITHIN_REFERENCE", "short_length_reason": "",
        }
        agent = FakeAgent([
            {"angle_cards": {"content_id": "c-1", "angles": [
                {"angle_id": f"A{i}", "status": "READY", "score": 90 - i,
                 "core_question": f"问题{i}", "judgment": f"判断{i}",
                 "reader_benefit": f"收益{i}", "evidence_path": f"证据{i}", "knockout_reasons": []}
                for i in range(1, 4)
            ], "locked_angle_id": "A1", "fact_ledger": {"FACT": [], "INFERENCE": [], "UNKNOWN": [], "FORBIDDEN_CLAIM": []}}},
            {"writing_route": {"content_id": "c-1", "locked_angle_id": "A1", "article_form": "APP_SHORT",
             "document_type": "本地生活文旅", "material_grade": "medium",
             "material_action": "WRITE", "target_min_chars": 300, "target_max_chars": 900,
             "selected_writing_skill": "app-skill", "skill_selection_reason": "APP生活短稿",
             "editor_name": "泡泡呀",
             "editor_dna_path": "/Users/REPLACE_ME/.openclaw/workspace/skills/app-skill/references/小编风格/泡泡呀-DNA.md",
             "editor_selection_reason": "生活感受轻讨论", "reason": "短稿足够"}},
            {"draft": draft},
            {"soft_audit": {"content_id": "c-1", "status": "PASS", "issues": [], "author_skill": "app-skill"}},
            {"review": {"content_id": "c-1", "verdict": "changes_requested", "score": 7.0, "issues": ["收束互动"],
             "ai_tone": "PASS", "length_fit": "PASS", "template_overlap": "PASS", "image_plan": "PASS"}},
            {"content_id": "c-1", "title": "宜宾活动安排，去前先看这几点"},
            {"soft_audit": {"content_id": "c-1", "status": "PASS", "issues": [], "author_skill": "app-skill"}},
            {"review": {"content_id": "c-1", "verdict": "approved", "score": 8.5, "issues": [],
             "ai_tone": "PASS", "length_fit": "PASS", "template_overlap": "PASS", "image_plan": "PASS"}},
        ])

        result = _generate_reviewed_drafts(
            agent,
            [{"content_id": "c-1", "source_url": "https://example.com/c-1", "images": [], "image_plan": [],
              "body_snapshot": "宜宾活动已公布完整时间、地点、参与方式和现场安排。"}],
            mode="DAILY_VALUE",
            session_prefix="test",
            allowed_vests=set(),
        )

        self.assertEqual(result[0]["review"]["verdict"], "approved")
        self.assertIn("review_rejected", [item["stage"] for item in result[0]["execution_trace"]])
        self.assertEqual(len(agent.calls), 8)

    def test_writer_must_preserve_approved_body_image_plan(self) -> None:
        candidate = {
            "content_id": "c-1",
            "source_url": "https://example.com/c-1",
            "images": ["/tmp/fact-card.png"],
            "image_plan": [{"path": "/tmp/fact-card.png", "placement": "首段后", "credit": "原创事实信息图"}],
        }
        route = {"target_min_chars": 1, "target_max_chars": 900}
        row = {
            "content_id": "c-1", "title": "标题", "html": "<p>正文</p>",
            "source_url": "https://example.com/c-1", "persona": "城市观察室型",
            "vest_name": "", "forum": "大宜宾APP", "category": "DAILY_VALUE",
            "images": [], "risk_result": "PASS",
            "facts_complete": True, "length_decision": "WITHIN_REFERENCE", "short_length_reason": "",
        }
        with self.assertRaisesRegex(RisingDispatchError, "preserve"):
            _validate_draft({"draft": row}, candidate, route, allowed_vests=set())
        normalized = _validate_draft(
            {"draft": {**row, "html": '<p>正文</p><img src="/tmp/fact-card.png">', "images": candidate["image_plan"]}},
            candidate,
            route,
            allowed_vests=set(),
        )
        self.assertEqual(normalized["images"], candidate["images"])

    def test_writer_must_embed_approved_images_without_placeholders(self) -> None:
        image = "/tmp/fact-card.png"
        candidate = {
            "content_id": "c-1",
            "source_url": "https://example.com/c-1",
            "images": [image],
            "image_plan": [{"path": image, "placement": "首段后", "credit": "原创事实信息图"}],
        }
        route = {"target_min_chars": 1, "target_max_chars": 900}
        base = {
            "content_id": "c-1", "title": "标题", "source_url": candidate["source_url"],
            "persona": "城市观察室型", "vest_name": "", "forum": "大宜宾APP",
            "category": "DAILY_VALUE", "images": [image], "risk_result": "PASS",
            "facts_complete": True, "length_decision": "WITHIN_REFERENCE", "short_length_reason": "",
        }
        for html in ("<p>【配图1】事实卡</p>", "<p>正文</p>"):
            with self.subTest(html=html), self.assertRaises(RisingDispatchError):
                _validate_draft({"draft": {**base, "html": html}}, candidate, route, allowed_vests=set())

        accepted = _validate_draft(
            {"draft": {**base, "html": f'<p>正文</p><img src="{image}">'}},
            candidate,
            route,
            allowed_vests=set(),
        )
        self.assertIn("<img", accepted["html"])

    def test_angle_gate_rejects_fewer_than_three_or_missing_unique_lock(self) -> None:
        candidate = {"content_id": "c-1"}
        base = {
            "content_id": "c-1",
            "angles": [
                {
                    "angle_id": f"A{index}", "status": "READY", "score": 85,
                    "core_question": f"问题{index}", "judgment": f"判断{index}",
                    "reader_benefit": f"收益{index}", "evidence_path": f"证据{index}",
                    "knockout_reasons": [],
                }
                for index in range(1, 4)
            ],
            "locked_angle_id": "A1",
            "fact_ledger": {"FACT": [], "INFERENCE": [], "UNKNOWN": [], "FORBIDDEN_CLAIM": []},
        }
        with self.assertRaisesRegex(RisingDispatchError, "at least three"):
            _validate_angle_cards({"angle_cards": {**base, "angles": base["angles"][:2]}}, candidate)
        with self.assertRaisesRegex(RisingDispatchError, "locked angle"):
            _validate_angle_cards({"angle_cards": {**base, "locked_angle_id": "A9"}}, candidate)
        bundle, locked = _validate_angle_cards(
            {"angle_cards": {**base, "fact_ledger": {**base["fact_ledger"], "UNKNOWN": ["不影响锁定角度的场次细节"]}}},
            candidate,
        )
        self.assertEqual(bundle["locked_angle_id"], locked["angle_id"])

    def test_route_accepts_certified_skill_independent_of_article_form(self) -> None:
        candidate = {"content_id": "c-1"}
        locked = {"angle_id": "A1"}
        route = {
            "content_id": "c-1", "locked_angle_id": "A1", "article_form": "WECHAT_LONG",
            "document_type": "产业机制", "material_grade": "strong",
            "target_min_chars": 1000, "target_max_chars": 1600,
            "material_action": "WRITE", "selected_writing_skill": "liurun-skill",
            "skill_selection_reason": "产业机制需要解释效率和运营约束",
            "editor_name": "刘润", "editor_dna_path": "/not-a-real-editor-dna.md",
            "editor_selection_reason": "固定作者风格",
            "reason": "强素材需要长文解释",
        }
        validated = _validate_route({"writing_route": route}, candidate, locked)
        self.assertEqual(validated["selected_writing_skill"], "liurun-skill")
        self.assertEqual(validated["editor_name"], "N/A")
        self.assertEqual(validated["editor_dna_path"], "N/A")
        self.assertEqual(validated["editor_dna_read_proof"]["status"], "N/A")

    def test_title_level_material_requires_supplement_or_drop_before_writing(self) -> None:
        candidate = {"content_id": "c-1", "material_level": "TITLE_LEVEL"}
        locked = {"angle_id": "A1"}
        route = {
            "content_id": "c-1", "locked_angle_id": "A1", "article_form": "WECHAT_LONG",
            "document_type": "项目进展", "material_grade": "weak",
            "target_min_chars": 300, "target_max_chars": 900,
            "material_action": "WRITE", "selected_writing_skill": "liurun-skill",
            "skill_selection_reason": "解释项目", "editor_name": "刘润",
            "editor_dna_path": "N/A", "editor_selection_reason": "固定风格",
            "reason": "项目说明",
        }
        with self.assertRaisesRegex(RisingDispatchError, "requires supplementation"):
            _validate_route({"writing_route": route}, candidate, locked)

        accepted = _validate_route({"writing_route": {
            **route, "material_action": "SUPPLEMENT_REQUIRED",
        }}, candidate, locked)
        self.assertEqual(accepted["material_action"], "SUPPLEMENT_REQUIRED")

    def test_route_must_read_exactly_one_editor_dna_to_eof(self) -> None:
        candidate = {"content_id": "c-1"}
        locked = {"angle_id": "A1"}
        dna_path = "/Users/REPLACE_ME/.openclaw/workspace/skills/app-skill/references/小编风格/泡泡呀-DNA.md"
        route = {
            "content_id": "c-1", "locked_angle_id": "A1", "article_form": "APP_SHORT",
            "document_type": "本地生活文旅", "material_grade": "medium",
            "target_min_chars": 300, "target_max_chars": 900,
            "material_action": "WRITE", "selected_writing_skill": "app-skill",
            "skill_selection_reason": "本地轻讨论适合 APP 多小编路线",
            "editor_name": "泡泡呀", "editor_dna_path": dna_path,
            "editor_selection_reason": "文旅体验和生活感受轻讨论",
            "reason": "事实适合短稿",
        }
        validated = _validate_route({"writing_route": route}, candidate, locked)
        proof = validated["editor_dna_read_proof"]
        self.assertEqual(proof["status"], "READ_FULL_EOF")
        self.assertEqual(proof["path"], dna_path)
        self.assertEqual(len(proof["sha256"]), 64)

        with self.assertRaisesRegex(RisingDispatchError, "editor DNA"):
            _validate_route(
                {"writing_route": {**route, "editor_name": "N/A", "editor_dna_path": "N/A"}},
                candidate,
                locked,
            )

    def test_deterministic_ai_phrase_gate_overrides_review_self_pass(self) -> None:
        candidate = {"content_id": "c-1", "source_url": "https://example.com/c-1", "images": []}
        route = {"target_min_chars": 1, "target_max_chars": 900}
        draft = {
            "content_id": "c-1", "title": "宜宾有个新变化", "html": "<p>根据素材，值得关注的是这个变化。</p>",
            "source_url": candidate["source_url"], "persona": "城市观察室型", "vest_name": "",
            "forum": "大宜宾APP", "category": "DAILY_VALUE", "images": [], "risk_result": "PASS",
            "facts_complete": True, "length_decision": "WITHIN_REFERENCE", "short_length_reason": "",
        }
        with self.assertRaisesRegex(RisingDispatchError, "deterministic"):
            _validate_draft({"draft": draft}, candidate, route, allowed_vests=set())

    def test_reference_length_allows_296_chars_when_facts_are_complete(self) -> None:
        candidate = {"content_id": "c-1", "source_url": "https://example.com/c-1", "images": []}
        route = {"target_min_chars": 300, "target_max_chars": 900}
        draft = {
            "content_id": "c-1", "title": "宜宾短讯", "html": f"<p>{'宜' * 296}</p>",
            "source_url": candidate["source_url"], "persona": "城市观察室型", "vest_name": "",
            "forum": "大宜宾APP", "category": "DAILY_VALUE", "images": [], "risk_result": "PASS",
            "facts_complete": True, "length_decision": "SHORTER_FACTS_COMPLETE",
            "short_length_reason": "",
        }
        accepted = _validate_draft({"draft": draft}, candidate, route, allowed_vests=set())
        self.assertEqual(accepted["length_decision"], "SHORTER_FACTS_COMPLETE")
        self.assertIn("不为达到参考字数补写", accepted["short_length_reason"])

    def test_reference_length_does_not_reject_a_complete_longer_article(self) -> None:
        candidate = {"content_id": "c-1", "source_url": "https://example.com/c-1", "images": []}
        route = {"target_min_chars": 300, "target_max_chars": 900}
        draft = {
            "content_id": "c-1", "title": "宜宾深度稿", "html": f"<p>{'宜' * 1200}</p>",
            "source_url": candidate["source_url"], "persona": "城市观察室型", "vest_name": "",
            "forum": "大宜宾APP", "category": "DAILY_VALUE", "images": [], "risk_result": "PASS",
            "facts_complete": True, "length_decision": "WITHIN_REFERENCE", "short_length_reason": "",
        }
        accepted = _validate_draft({"draft": draft}, candidate, route, allowed_vests=set())
        self.assertEqual(accepted["length_decision"], "LONGER_FACTS_COMPLETE")

    def test_writer_cannot_override_account_profile_assignment(self) -> None:
        candidate = {
            "content_id": "c-1", "source_url": "https://example.com/c-1", "images": [],
            "assigned_profile": {
                "profile_id": "city", "vest_name": "forever21",
                "persona": "城市观察室型", "assignment_reason": "城建题材匹配",
            },
        }
        draft = {
            "content_id": "c-1", "title": "宜宾城建短讯", "html": "<p>宜宾城建项目公布了新的公开进度。</p>",
            "source_url": candidate["source_url"], "persona": "模型擅自改的人设", "vest_name": "模型擅自改的马甲",
            "forum": "大宜宾APP", "category": "DAILY_VALUE", "images": [], "risk_result": "PASS",
            "facts_complete": True, "length_decision": "WITHIN_REFERENCE", "short_length_reason": "",
        }

        accepted = _validate_draft(
            {"draft": draft}, candidate, {"target_min_chars": 1, "target_max_chars": 900},
            allowed_vests={"forever21"},
        )

        self.assertEqual(accepted["vest_name"], "forever21")
        self.assertEqual(accepted["persona"], "城市观察室型")

    def test_soft_audit_cannot_rewrite_or_change_author_skill(self) -> None:
        draft = {"content_id": "c-1"}
        route = {"selected_writing_skill": "app-skill"}
        with self.assertRaises(RisingDispatchError):
            _validate_soft_audit(
                {"soft_audit": {"content_id": "c-1", "status": "PASS", "issues": [], "author_skill": "wechat-writing-skill"}},
                draft,
                route,
            )
        with self.assertRaisesRegex(RisingDispatchError, "must not rewrite"):
            _validate_soft_audit(
                {"soft_audit": {"content_id": "c-1", "status": "PASS", "issues": [], "author_skill": "app-skill", "html": "改写"}},
                draft,
                route,
            )

    def test_profile_assignment_prefers_topic_fit_without_even_quota(self) -> None:
        profiles = (
            {"id": "city", "persona": "城市观察室型", "topics": ["城建", "交通"], "vest_name": "forever21"},
            {"id": "weekend", "persona": "周末计划型", "topics": ["文旅", "美食"], "vest_name": "心空空情空空"},
        )
        assigned = _assign_profiles(
            [{"title": "宜宾城建交通新变化"}, {"title": "宜宾又一城建项目"}, {"title": "周末文旅美食活动"}],
            profiles,
        )
        self.assertEqual([item["assigned_profile"]["vest_name"] for item in assigned], ["forever21", "forever21", "心空空情空空"])

    def test_claim_key_deduplicates_event_aliases(self) -> None:
        first = {"event_id": "event-one", "content_id": "a", "source_url": "https://a", "title": "标题A"}
        second = {"event_id": "event-one", "content_id": "b", "source_url": "https://b", "title": "标题B"}
        self.assertEqual(_claim_key(first), _claim_key(second))

    def test_watch_query_uses_short_event_or_project_phrase(self) -> None:
        self.assertEqual(_watch_query("这款宜宾五粮液集团公司的新品"), "这款宜宾五粮液集")
        self.assertEqual(_watch_query("宜宾中渡口片区启动更新建设"), "宜宾中渡口片区启")

    def test_watch_target_carries_only_hashed_stable_aliases(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "2026-08-22" / "rising-monitor"
            target.mkdir(parents=True)
            target.joinpath("state.json").write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "title": "宜宾中渡口片区启动更新建设",
                                "locality_state": "direct",
                                "risk_state": "LOW_RISK",
                                "identity_aliases": ["a" * 64, "raw-id"],
                                "snapshots": [{"like_count": 1}],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            selected = _select_watch_target(root, "2026-08-22")

            self.assertEqual(selected["identity_aliases"], ["a" * 64])
            self.assertNotIn("raw-id", json.dumps(selected))

    def test_no_fast_track_runs_one_round_without_model(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._config(root)
            agent = FakeAgent({})
            calls: list[int] = []

            def runner(bundle, **kwargs):
                calls.append(kwargs["round_number"])
                self._write_candidates(root, "2026-08-22", [])
                return {"status": "RISING_MONITOR_CALIBRATION", "fast_track_ready_count": 0}

            result = dispatch_rising(
                config,
                evidence_dir=root / "evidence",
                now=datetime(2026, 8, 22, 4, 0, tzinfo=UTC),
                bundle_fetcher=lambda: {"fact_rows": []},
                round_runner=runner,
                agent=agent,
            )

            self.assertEqual(result["round_number"], 1)
            self.assertEqual(result["draft_count"], 0)
            self.assertEqual(calls, [1])
            self.assertEqual(agent.calls, [])

    def test_same_half_hour_slot_never_runs_twice(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._config(root)
            calls = 0

            def runner(bundle, **kwargs):
                nonlocal calls
                calls += 1
                self._write_candidates(root, "2026-08-22", [])
                return {"status": "RISING_MONITOR_CALIBRATION"}

            dispatch_rising(
                config,
                evidence_dir=root / "evidence",
                now=datetime(2026, 8, 22, 4, 1, tzinfo=UTC),
                bundle_fetcher=lambda: {},
                round_runner=runner,
            )
            skipped = dispatch_rising(
                config,
                evidence_dir=root / "evidence",
                now=datetime(2026, 8, 22, 4, 20, tzinfo=UTC),
                bundle_fetcher=lambda: {},
                round_runner=runner,
            )

            self.assertEqual(skipped["status"], "SKIPPED_SLOT_ALREADY_RUN")
            self.assertEqual(calls, 1)

    def test_fast_track_creates_one_unpublished_batch_and_repeat_is_idempotent(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._config(root)
            old_batch = root / "data" / "2026-08-22" / "pending-batches" / "BATCH-20260822-0300-deadbeef"
            old_batch.mkdir(parents=True)
            old_batch.joinpath("batch.json").write_text(
                json.dumps({"batch_id": old_batch.name, "status": "AWAITING_HUMAN_SCHEDULE_CONFIRMATION"}),
                encoding="utf-8",
            )
            body = "<p>" + "宜宾中渡口更新后，附近居民最关心公共空间怎么用。" * 55 + "</p>"
            agent = FakeAgent(
                [
                    {
                        "angle_cards": {
                            "content_id": "c-1",
                            "angles": [
                                {
                                    "angle_id": "A1",
                                    "status": "READY",
                                    "score": 91,
                                    "core_question": "更新后公共空间为谁服务",
                                    "judgment": "城市更新要用日常使用率衡量",
                                    "reader_benefit": "看懂规划与自己生活的关系",
                                    "evidence_path": "规划用途与周边居民需求",
                                    "knockout_reasons": [],
                                },
                                {
                                    "angle_id": "A2",
                                    "status": "READY",
                                    "score": 84,
                                    "core_question": "老城记忆如何留下",
                                    "judgment": "保留记忆不等于保留全部旧貌",
                                    "reader_benefit": "形成城市文化讨论",
                                    "evidence_path": "片区历史与更新节点",
                                    "knockout_reasons": [],
                                },
                                {
                                    "angle_id": "A3",
                                    "status": "KNOCKOUT",
                                    "score": 62,
                                    "core_question": "项目会不会带来商业机会",
                                    "judgment": "商业判断缺少经营数据",
                                    "reader_benefit": "避免空泛投资想象",
                                    "evidence_path": "现有素材没有招商数据",
                                    "knockout_reasons": ["证据不足"],
                                },
                            ],
                            "locked_angle_id": "A1",
                            "fact_ledger": {"FACT": ["中渡口片区启动更新"], "INFERENCE": [], "UNKNOWN": [], "FORBIDDEN_CLAIM": []},
                        }
                    },
                    {
                        "writing_route": {
                            "content_id": "c-1",
                            "locked_angle_id": "A1",
                            "article_form": "WECHAT_LONG",
                            "document_type": "城建交通", "material_grade": "strong",
                            "material_action": "WRITE",
                            "target_min_chars": 1200,
                            "target_max_chars": 1800,
                            "selected_writing_skill": "wechat-writing-skill",
                            "skill_selection_reason": "强城建素材需要完整解释",
                            "editor_name": "大艳",
                            "editor_dna_path": "/Users/REPLACE_ME/.openclaw/workspace/skills/wechat-writing-skill/references/小编风格/大艳-DNA.md",
                            "editor_selection_reason": "当前动作和现实影响优先",
                            "reason": "城建变化需要把事实和居民关系写厚",
                        }
                    },
                    {
                        "draft": {
                            "content_id": "c-1",
                            "title": "宜宾中渡口更新，最值得留下什么",
                            "html": body,
                            "source_url": "https://example.com/c-1",
                            "persona": "城市观察室型",
                            "vest_name": "",
                            "forum": "城市更新",
                            "category": "N/A",
                            "images": [],
                            "risk_result": "PASS",
                            "facts_complete": True,
                            "length_decision": "WITHIN_REFERENCE",
                            "short_length_reason": "",
                        }
                    },
                    {
                        "soft_audit": {
                            "content_id": "c-1",
                            "status": "PASS",
                            "issues": [],
                            "author_skill": "wechat-writing-skill",
                        }
                    },
                    {
                        "review": {
                            "content_id": "c-1",
                            "verdict": "approved",
                            "score": 8.4,
                            "issues": [],
                            "ai_tone": "PASS",
                            "length_fit": "PASS",
                            "template_overlap": "PASS",
                        }
                    },
                ]
            )

            def runner(bundle, **kwargs):
                self._write_candidates(
                    root,
                    "2026-08-22",
                    [{"content_id": "c-1", "status": "FAST_TRACK_READY"}],
                    candidates=[
                        {
                            "content_id": "c-1",
                            "title": "宜宾中渡口更新",
                            "source_url": "https://example.com/c-1",
                            "body_snapshot": "宜宾中渡口片区城市更新项目已公布施工范围、时间与建设内容。",
                            "risk_state": "LOW_RISK",
                            "fact_check": {"status": "PASS"},
                        }
                    ],
                )
                return {"status": "FAST_TRACK_READY", "fast_track_ready_count": 1}

            first = dispatch_rising(
                config,
                evidence_dir=root / "evidence",
                now=datetime(2026, 8, 22, 4, 0, tzinfo=UTC),
                bundle_fetcher=lambda: {},
                round_runner=runner,
                agent=agent,
            )
            second = dispatch_rising(
                config,
                evidence_dir=root / "evidence",
                now=datetime(2026, 8, 22, 4, 30, tzinfo=UTC),
                bundle_fetcher=lambda: {},
                round_runner=runner,
                agent=agent,
            )

            self.assertEqual(first["draft_count"], 1)
            self.assertEqual(first["qianfan_called"], False)
            self.assertTrue(Path(first["batch_card_path"]).is_file())
            self.assertEqual(second["draft_count"], 0)
            self.assertEqual(len(agent.calls), 5)
            self.assertEqual(len({session_id for _, session_id in agent.calls}), 5)
            self.assertIn("/skill dayibin-topic-angle-engine", agent.calls[0][0])
            self.assertIn("/skill dayibin-writing-orchestrator", agent.calls[1][0])
            self.assertNotIn("dayibin-topic-angle-engine", agent.calls[1][0])
            self.assertIn("/skill wechat-writing-skill", agent.calls[2][0])
            self.assertIn("/skill human-writing-soft-audit", agent.calls[3][0])
            self.assertIn("/skill dayibin-content-review", agent.calls[4][0])
            batch = json.loads(
                Path(first["batch_card_path"]).with_name("batch.json").read_text()
            )
            draft = batch["drafts"][0]
            self.assertEqual(draft["locked_angle_id"], "A1")
            self.assertEqual(draft["article_form"], "WECHAT_LONG")
            self.assertEqual(draft["selected_writing_skill"], "wechat-writing-skill")
            self.assertEqual(draft["soft_audit"]["status"], "PASS")
            self.assertEqual(draft["review"]["verdict"], "approved")
            self.assertEqual(
                [item["stage"] for item in draft["execution_trace"]],
                ["angle", "route", "write", "soft_audit", "review"],
            )
            self.assertTrue(all(len(item["response_sha256"]) == 64 for item in draft["execution_trace"]))
            artifact_root = Path(first["batch_card_path"]).parent / "artifacts" / "c-1"
            self.assertTrue(artifact_root.joinpath("angle-cards.json").is_file())
            self.assertTrue(artifact_root.joinpath("locked-angle.json").is_file())
            self.assertTrue(artifact_root.joinpath("writing-route.json").is_file())
            route_artifact = json.loads(artifact_root.joinpath("writing-route.json").read_text())
            self.assertEqual(route_artifact["execution"]["stage"], "route")

    def test_unreviewed_single_pass_draft_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._config(root)
            agent = FakeAgent(
                {
                    "drafts": [
                        {
                            "content_id": "c-1",
                            "title": "模板短稿",
                            "html": "<p>这类项目最值得看的一点。</p>",
                            "source_url": "https://example.com/c-1",
                            "angle": "泛泛价值",
                            "writer_skill": "dayibin-app-writing",
                            "persona": "城市观察室型",
                            "vest_name": "",
                            "forum": "城市更新",
                            "category": "N/A",
                            "images": [],
                            "risk_result": "PASS",
                        }
                    ]
                }
            )

            self._write_candidates(
                root,
                "2026-08-22",
                [{"content_id": "c-1", "status": "FAST_TRACK_READY"}],
                candidates=[
                    {
                        "content_id": "c-1",
                        "title": "宜宾项目",
                        "body_snapshot": "宜宾项目已公布完整时间、地点、建设内容和实施安排。",
                        "source_url": "https://example.com/c-1",
                        "risk_state": "LOW_RISK",
                        "fact_check": {"status": "PASS"},
                    }
                ],
            )

            with self.assertRaises(RisingDispatchError):
                dispatch_rising(
                    config,
                    evidence_dir=root / "evidence",
                    now=datetime(2026, 8, 22, 4, 0, tzinfo=UTC),
                    bundle_fetcher=lambda: {},
                    round_runner=lambda bundle, **kwargs: {
                        "status": "FAST_TRACK_READY",
                        "fast_track_ready_count": 1,
                    },
                    agent=agent,
                )

            self.assertEqual(len(agent.calls), 1)

    def test_two_consecutive_failures_trip_persistent_circuit(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._config(root)
            calls = 0

            def failing_fetcher():
                nonlocal calls
                calls += 1
                raise RuntimeError("supplier failure")

            for minute in (0, 30):
                with self.assertRaises(RisingDispatchError):
                    dispatch_rising(
                        config,
                        evidence_dir=root / "evidence",
                        now=datetime(2026, 8, 22, 4, minute, tzinfo=UTC),
                        bundle_fetcher=failing_fetcher,
                    )

            with self.assertRaisesRegex(RisingDispatchError, "STOPPED_FAIL"):
                dispatch_rising(
                    config,
                    evidence_dir=root / "evidence",
                    now=datetime(2026, 8, 22, 5, 0, tzinfo=UTC),
                    bundle_fetcher=failing_fetcher,
                )
            self.assertEqual(calls, 2)

    def test_auth_failure_trips_circuit_immediately(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._config(root)

            with self.assertRaises(RisingDispatchError):
                dispatch_rising(
                    config,
                    evidence_dir=root / "evidence",
                    now=datetime(2026, 8, 22, 4, 0, tzinfo=UTC),
                    bundle_fetcher=lambda: (_ for _ in ()).throw(
                        XyuqingAuthRequired("XYUQING_AUTH_REQUIRED")
                    ),
                )

            with self.assertRaisesRegex(RisingDispatchError, "STOPPED_FAIL"):
                dispatch_rising(
                    config,
                    evidence_dir=root / "evidence",
                    now=datetime(2026, 8, 22, 4, 30, tzinfo=UTC),
                    bundle_fetcher=lambda: {},
                )

    @staticmethod
    def _config(root: Path) -> PipelineConfig:
        return PipelineConfig(
            source_db=root / "facts.db",
            data_dir=root / "data",
            agent_id="writer",
            model="model",
        )

    @staticmethod
    def _write_candidates(
        root: Path,
        day: str,
        fast_track: list[dict[str, object]],
        *,
        candidates: list[dict[str, object]] | None = None,
    ) -> None:
        target = root / "data" / day / "rising-monitor" / "rising-candidates.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {"candidates": candidates or [], "fast_track": fast_track},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
