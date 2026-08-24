from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import random
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from dayibin_auto_publisher.production_schedule import (
    ProductionScheduleError,
    build_daily_operations_review,
    confirm_batch_schedule,
    dispatch_due_publications,
    frozen_contract_hash,
    preview_daily_batch_schedules,
    review_binding_hashes,
)


DAY = "2026-08-22"
BATCH_ONE = "BATCH-20260822-0800-aaaaaaaa"
BATCH_TWO = "BATCH-20260822-0805-bbbbbbbb"
APP_SKILL_PATH = Path("/Users/REPLACE_ME/.openclaw/workspace/skills/app-skill/SKILL.md")
APP_EDITOR_PATH = Path("/Users/REPLACE_ME/.openclaw/workspace/skills/app-skill/references/小编风格/泡泡呀-DNA.md")


def _app_writing_route() -> dict:
    skill_bytes = APP_SKILL_PATH.read_bytes()
    editor_bytes = APP_EDITOR_PATH.read_bytes()
    return {
        "document_type": "本地生活文旅",
        "selected_writing_skill": "app-skill",
        "writing_skill_contract_proof": {
            "status": "CERTIFIED_ACTIVE_CONTRACT_COMPLETE",
            "contract_path": str(APP_SKILL_PATH),
            "contract_sha256": hashlib.sha256(skill_bytes).hexdigest(),
        },
        "editor_name": "泡泡呀",
        "editor_dna_path": str(APP_EDITOR_PATH),
        "editor_selection_reason": "本地生活题材与泡泡呀的生活化表达匹配",
        "editor_dna_read_proof": {
            "status": "READ_FULL_EOF",
            "path": str(APP_EDITOR_PATH),
            "bytes": len(editor_bytes),
            "sha256": hashlib.sha256(editor_bytes).hexdigest(),
        },
        "writing_session_id": "writing-test-session",
    }


class ProductionScaleTests(unittest.TestCase):
    def test_missing_queue_is_safe_and_never_calls_publisher(self) -> None:
        with TemporaryDirectory() as tmp:
            calls = []
            result = dispatch_due_publications(
                Path(tmp) / "missing.json",
                publisher=lambda item, no_send: calls.append(item) or {},
            )
            self.assertEqual(result["status"], "QUEUE_NOT_READY")
            self.assertFalse(result["qianfan_called"])
            self.assertEqual(calls, [])

    def test_daily_review_is_operator_readable_and_marks_missing_metrics_na(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            day_root = root / DAY
            day_root.mkdir(parents=True)
            root.joinpath("production-publish-queue.json").write_text(
                json.dumps(
                    {
                        "schema_version": "dayibin-production-publish-queue-v1",
                        "items": [
                            {
                                "queue_id": "q1", "status": "PUBLISHED_VERIFIED",
                                "channel": "DAILY_VALUE", "vest_name": "forever21",
                                "persona": "城市观察室型", "assignment_reason": "城建匹配",
                                "title": "中渡口更新怎么影响日常通行",
                                "locked_angle_id": "A2",
                                "selected_writing_skill": "app-skill",
                                "visible_char_count": 688,
                                "publication_ref": "948529",
                                "scheduled_at": "2026-08-22T09:10:00+08:00",
                                "published_at": "2026-08-22T09:12:00+08:00",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            root.joinpath("post-publish-review-queue.json").write_text(
                json.dumps(
                    {
                        "schema_version": "post-publish-review-queue-v1",
                        "items": [{
                            "publication_ref": "948529", "checkpoint": "2h",
                            "status": "COMPLETED", "observed_at": "2026-08-22T11:12:00+08:00",
                            "metrics": {
                                "read_count": "N/A_SUPPLIER_FIELD_UNAVAILABLE",
                                "reply_count": 4,
                                "like_count": "N/A_SUPPLIER_FIELD_UNAVAILABLE",
                                "share_count": "N/A_SUPPLIER_FIELD_UNAVAILABLE",
                            },
                        }],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            target = day_root / "daily-operations-review.md"

            result = build_daily_operations_review(root, business_date=DAY, target=target)

            text = target.read_text(encoding="utf-8")
            self.assertEqual(result["status"], "DAILY_REVIEW_READY")
            self.assertIn("今日计划 / 已发布 / 失败 / 作废", text)
            self.assertIn("阅读：N/A", text)
            self.assertIn("点赞：N/A", text)
            self.assertIn("转发：N/A", text)
            self.assertIn("中渡口更新怎么影响日常通行", text)
            self.assertIn("A2", text)
            self.assertIn("app-skill", text)
            self.assertIn("688", text)
            self.assertIn("评论 4", text)
            self.assertIn("供应商字段不可用", text)
            self.assertIn("次日建议", text)

    def _batch(
        self,
        root: Path,
        batch_id: str,
        *,
        channels: tuple[str, ...] = ("DAILY_VALUE", "DAILY_VALUE", "DAILY_VALUE"),
        vests: tuple[str, ...] = ("forever21", "forever21", "无敌wu"),
    ) -> Path:
        batch_dir = root / DAY / "pending-batches" / batch_id
        batch_dir.mkdir(parents=True)
        drafts = []
        for index, (channel, vest) in enumerate(zip(channels, vests), 1):
            title = f"宜宾生产排期稿{index}"
            html = f"<p>这是第{index}篇已经完成全部审核的正文。</p>"
            drafts.append(
                {
                    "content_id": f"content-{batch_id[-4:]}-{index}",
                    "event_id": f"event-{batch_id[-4:]}-{index}",
                    "channel": channel,
                    "category": channel,
                    "title": title,
                    "html": html,
                    "source_url": f"https://example.com/{batch_id}/{index}",
                    "vest_name": vest,
                    "persona": "城市观察室型" if vest == "forever21" else "生活算盘型",
                    "assignment_reason": "题材与人设匹配",
                    "forum": "大宜宾APP",
                    "images": [],
                    "risk_result": "PASS",
                    "locked_angle_id": f"A{index}",
                    "winner_score": 88,
                    "article_form": "APP_SHORT",
                    "target_min_chars": 300,
                    "target_max_chars": 900,
                    "base_writing_skill": "app-skill",
                    **_app_writing_route(),
                    "soft_audit": {"status": "PASS", "issues": []},
                    "review": {"verdict": "approved", "score": 8.8},
                    "evergreen": channel == "DAILY_VALUE",
                }
            )
            draft = drafts[-1]
            draft["title_hash"] = hashlib.sha256(title.encode()).hexdigest()
            draft["body_hash"] = hashlib.sha256(html.encode()).hexdigest()
            draft["image_hashes"] = []
            draft["material_hash"] = hashlib.sha256(
                "\0".join([draft["title_hash"], draft["body_hash"]]).encode()
            ).hexdigest()
            binding = review_binding_hashes(draft)
            draft["soft_audit"].update(binding)
            draft["review"].update(binding)
            draft["frozen_contract_hash"] = frozen_contract_hash(draft)
        payload = {
            "schema_version": "dayibin-pending-batch-v2",
            "batch_id": batch_id,
            "status": "AWAITING_HUMAN_SCHEDULE_CONFIRMATION",
            "mode": "+".join(sorted(set(channels))),
            "schedule_confirmation_phrase": f"确认本批排期：{batch_id}",
            "drafts": drafts,
            "qianfan_called": False,
        }
        batch_dir.joinpath("batch.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
        return batch_dir

    def test_confirmation_persists_random_schedule_without_restart_drift(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch_dir = self._batch(root, BATCH_ONE)
            queue = root / "production-publish-queue.json"
            phrase = f"确认本批排期：{BATCH_ONE}"

            first = confirm_batch_schedule(
                root,
                batch_id=BATCH_ONE,
                confirmation_phrase=phrase,
                queue_path=queue,
                now=datetime(2026, 8, 22, 0, 0, tzinfo=UTC),
                rng=random.Random(7),
            )
            second = confirm_batch_schedule(
                root,
                batch_id=BATCH_ONE,
                confirmation_phrase=phrase,
                queue_path=queue,
                now=datetime(2026, 8, 22, 0, 5, tzinfo=UTC),
                rng=random.Random(999),
            )

            self.assertEqual(first["items"], second["items"])
            scheduled = [datetime.fromisoformat(item["scheduled_at"]) for item in first["items"]]
            self.assertTrue(all(value.date().isoformat() == DAY for value in scheduled))
            self.assertTrue(all((value.hour, value.minute) >= (8, 20) for value in scheduled))
            self.assertTrue(all((value.hour, value.minute) <= (22, 30) for value in scheduled))
            self.assertTrue(all(45 <= (b - a).total_seconds() / 60 <= 120 for a, b in zip(scheduled, scheduled[1:])))
            forever = [value for item, value in zip(first["items"], scheduled) if item["vest_name"] == "forever21"]
            self.assertGreaterEqual((forever[1] - forever[0]).total_seconds() / 60, 150)
            saved_batch = json.loads(batch_dir.joinpath("batch.json").read_text(encoding="utf-8"))
            self.assertEqual(saved_batch["status"], "SCHEDULED")
            self.assertFalse(saved_batch["qianfan_called"])

    def test_verified_existing_post_edit_is_not_enqueued_as_a_new_post(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch_dir = self._batch(root, BATCH_ONE)
            batch_path = batch_dir / "batch.json"
            batch = json.loads(batch_path.read_text(encoding="utf-8"))
            batch["drafts"][0].update({
                "publish_action": "EDIT_EXISTING",
                "edit_target_id": "948582",
                "edit_status": "EDITED_VERIFIED",
            })
            batch_path.write_text(json.dumps(batch, ensure_ascii=False), encoding="utf-8")

            result = confirm_batch_schedule(
                root,
                batch_id=BATCH_ONE,
                confirmation_phrase=f"确认本批排期：{BATCH_ONE}",
                queue_path=root / "queue.json",
                now=datetime(2026, 8, 22, 0, 0, tzinfo=UTC),
                rng=random.Random(7),
            )

            self.assertEqual(len(result["items"]), 2)
            self.assertNotIn(batch["drafts"][0]["content_id"], {item["content_id"] for item in result["items"]})

    def test_old_or_inexact_confirmation_phrase_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._batch(root, BATCH_ONE)
            for phrase in (f"确认本批发布：{BATCH_ONE}", f"确认本批排期：{BATCH_ONE} "):
                with self.subTest(phrase=phrase), self.assertRaises(ProductionScheduleError):
                    confirm_batch_schedule(
                        root,
                        batch_id=BATCH_ONE,
                        confirmation_phrase=phrase,
                        queue_path=root / "queue.json",
                        now=datetime(2026, 8, 22, 0, 0, tzinfo=UTC),
                    )

    def test_confirmation_rejects_draft_changed_after_freeze(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch_dir = self._batch(root, BATCH_ONE)
            batch_path = batch_dir / "batch.json"
            batch = json.loads(batch_path.read_text(encoding="utf-8"))
            batch["drafts"][0]["title"] += "（已被改动）"
            batch_path.write_text(json.dumps(batch, ensure_ascii=False), encoding="utf-8")

            with self.assertRaisesRegex(ProductionScheduleError, "review binding|contract changed"):
                confirm_batch_schedule(
                    root,
                    batch_id=BATCH_ONE,
                    confirmation_phrase=f"确认本批排期：{BATCH_ONE}",
                    queue_path=root / "queue.json",
                    now=datetime(2026, 8, 22, 0, 0, tzinfo=UTC),
                )

    def test_review_pass_cannot_be_reused_after_refreezing_changed_content(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch_dir = self._batch(root, BATCH_ONE)
            batch_path = batch_dir / "batch.json"
            batch = json.loads(batch_path.read_text(encoding="utf-8"))
            draft = batch["drafts"][0]
            draft["title"] += "新版本"
            draft["title_hash"] = hashlib.sha256(draft["title"].encode()).hexdigest()
            draft["material_hash"] = hashlib.sha256(
                "\0".join([draft["title_hash"], draft["body_hash"]]).encode()
            ).hexdigest()
            draft["frozen_contract_hash"] = frozen_contract_hash(draft)
            batch_path.write_text(json.dumps(batch, ensure_ascii=False), encoding="utf-8")

            with self.assertRaisesRegex(ProductionScheduleError, "review binding"):
                confirm_batch_schedule(
                    root,
                    batch_id=BATCH_ONE,
                    confirmation_phrase=f"确认本批排期：{BATCH_ONE}",
                    queue_path=root / "queue.json",
                    now=datetime(2026, 8, 22, 0, 0, tzinfo=UTC),
                )

    def test_cumulative_preview_is_no_write_and_enforces_daily_hard_cap(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._batch(root, BATCH_ONE, channels=("DAILY_VALUE",), vests=("forever21",))
            self._batch(root, BATCH_TWO, channels=("DAILY_VALUE",), vests=("无敌wu",))
            queue = root / "queue.json"
            queue.write_text(json.dumps({
                "schema_version": "dayibin-production-publish-queue-v1",
                "items": [
                    {"queue_id": f"q-{index}", "status": "PUBLISHED_VERIFIED", "vest_name": "forever21",
                     "scheduled_at": f"{DAY}T{8 + index // 2:02d}:{20 + (index % 2) * 45:02d}:00+08:00"}
                    for index in range(14)
                ],
            }), encoding="utf-8")
            before = queue.read_bytes()

            with self.assertRaisesRegex(ProductionScheduleError, "hard cap"):
                preview_daily_batch_schedules(
                    root, [BATCH_ONE, BATCH_TWO], queue_path=queue,
                    now=datetime(2026, 8, 22, 0, 0, tzinfo=UTC), daily_hard_cap=15,
                    rng=random.Random(3),
                )

            self.assertEqual(queue.read_bytes(), before)

    def test_cumulative_preview_moves_whole_daily_batches_to_next_operating_day(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._batch(root, BATCH_ONE)
            self._batch(root, BATCH_TWO)
            queue = root / "queue.json"

            result = preview_daily_batch_schedules(
                root,
                [BATCH_ONE, BATCH_TWO],
                queue_path=queue,
                now=datetime(2026, 8, 22, 13, 30, tzinfo=UTC),
                rng=random.Random(7),
            )

            scheduled = [
                datetime.fromisoformat(item["scheduled_at"])
                for batch in result["batches"]
                for item in batch["items"]
            ]
            self.assertEqual(result["status"], "PREVIEW_READY_NO_WRITE")
            self.assertTrue(all(value.date().isoformat() == "2026-08-23" for value in scheduled))
            self.assertFalse(queue.exists())

    def test_confirmation_rejects_placeholder_even_when_contract_is_refrozen(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch_dir = self._batch(root, BATCH_ONE)
            batch_path = batch_dir / "batch.json"
            batch = json.loads(batch_path.read_text(encoding="utf-8"))
            draft = batch["drafts"][0]
            draft["html"] = "<p>配图1：待补图</p>"
            draft["body_hash"] = hashlib.sha256(draft["html"].encode()).hexdigest()
            draft["material_hash"] = hashlib.sha256(
                "\0".join([draft["title_hash"], draft["body_hash"]]).encode()
            ).hexdigest()
            draft["frozen_contract_hash"] = frozen_contract_hash(draft)
            batch_path.write_text(json.dumps(batch, ensure_ascii=False), encoding="utf-8")

            with self.assertRaisesRegex(ProductionScheduleError, "review binding|contract changed"):
                confirm_batch_schedule(
                    root,
                    batch_id=BATCH_ONE,
                    confirmation_phrase=f"确认本批排期：{BATCH_ONE}",
                    queue_path=root / "queue.json",
                    now=datetime(2026, 8, 22, 0, 0, tzinfo=UTC),
                )

    def test_daily_batch_moves_whole_to_next_operating_day_when_today_cannot_fit(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._batch(root, BATCH_ONE)
            queue = root / "queue.json"

            result = confirm_batch_schedule(
                root,
                batch_id=BATCH_ONE,
                confirmation_phrase=f"确认本批排期：{BATCH_ONE}",
                queue_path=queue,
                now=datetime(2026, 8, 22, 13, 30, tzinfo=UTC),
                rng=random.Random(7),
            )

            scheduled = [datetime.fromisoformat(item["scheduled_at"]) for item in result["items"]]
            self.assertTrue(all(value.date().isoformat() == "2026-08-23" for value in scheduled))
            self.assertTrue(all((value.hour, value.minute) >= (8, 20) for value in scheduled))
            self.assertTrue(all((value.hour, value.minute) <= (22, 30) for value in scheduled))
            self.assertTrue(all(45 <= (b - a).total_seconds() / 60 <= 120 for a, b in zip(scheduled, scheduled[1:])))

    def test_failed_whole_batch_plan_does_not_partially_change_existing_queue(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._batch(root, BATCH_ONE)
            queue = root / "queue.json"
            original = {
                "schema_version": "dayibin-production-publish-queue-v1",
                "items": [{
                    "queue_id": "existing", "status": "SCHEDULED", "channel": "DAILY_VALUE",
                    "vest_name": "无敌wu", "scheduled_at": "2026-08-23T08:20:00+08:00",
                }],
            }
            queue.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")
            settings = SimpleNamespace(
                active_start="08:20", active_end="08:21",
                global_interval_min_minutes=45, global_interval_max_minutes=120,
                same_vest_interval_minutes=150,
            )

            with self.assertRaisesRegex(ProductionScheduleError, "does not fit"):
                confirm_batch_schedule(
                    root,
                    batch_id=BATCH_ONE,
                    confirmation_phrase=f"确认本批排期：{BATCH_ONE}",
                    queue_path=queue,
                    now=datetime(2026, 8, 22, 13, 30, tzinfo=UTC),
                    rng=random.Random(7),
                    settings=settings,
                )

            self.assertEqual(json.loads(queue.read_text(encoding="utf-8")), original)

    def test_multiple_pending_batches_can_be_scheduled_into_one_queue(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._batch(root, BATCH_ONE, channels=("DAILY_VALUE",), vests=("forever21",))
            self._batch(root, BATCH_TWO, channels=("DAILY_VALUE",), vests=("无敌wu",))
            queue = root / "queue.json"
            for batch_id in (BATCH_ONE, BATCH_TWO):
                confirm_batch_schedule(
                    root,
                    batch_id=batch_id,
                    confirmation_phrase=f"确认本批排期：{batch_id}",
                    queue_path=queue,
                    now=datetime(2026, 8, 22, 0, 0, tzinfo=UTC),
                    rng=random.Random(3),
                )

            payload = json.loads(queue.read_text(encoding="utf-8"))
            self.assertEqual({item["batch_id"] for item in payload["items"]}, {BATCH_ONE, BATCH_TWO})

    def test_hot_now_preempts_one_future_daily_slot_without_reshuffling_others(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._batch(root, BATCH_ONE, channels=("DAILY_VALUE", "DAILY_VALUE"), vests=("forever21", "无敌wu"))
            self._batch(root, BATCH_TWO, channels=("HOT_NOW",), vests=("南屿nanyu",))
            queue = root / "queue.json"
            first = confirm_batch_schedule(
                root,
                batch_id=BATCH_ONE,
                confirmation_phrase=f"确认本批排期：{BATCH_ONE}",
                queue_path=queue,
                now=datetime(2026, 8, 22, 0, 0, tzinfo=UTC),
                rng=random.Random(2),
            )
            original = [item["scheduled_at"] for item in first["items"]]

            hot = confirm_batch_schedule(
                root,
                batch_id=BATCH_TWO,
                confirmation_phrase=f"确认本批排期：{BATCH_TWO}",
                queue_path=queue,
                now=datetime(2026, 8, 22, 0, 10, tzinfo=UTC),
                rng=random.Random(4),
            )

            saved = json.loads(queue.read_text(encoding="utf-8"))["items"]
            daily = [item for item in saved if item["batch_id"] == BATCH_ONE]
            self.assertIn(hot["items"][0]["scheduled_at"], original)
            self.assertEqual(sum(item["scheduled_at"] != before for item, before in zip(daily, original)), 1)
            self.assertEqual(sum("displaced_by_hot_now" in item for item in daily), 1)

    def test_dispatch_processes_at_most_one_due_item_and_no_send_stays_zero(self) -> None:
        with TemporaryDirectory() as tmp:
            queue = Path(tmp) / "queue.json"
            queue.write_text(
                json.dumps(
                    {
                        "schema_version": "dayibin-production-publish-queue-v1",
                        "items": [
                            {"queue_id": "q1", "status": "SCHEDULED", "scheduled_at": "2026-08-22T08:20:00+08:00"},
                            {"queue_id": "q2", "status": "SCHEDULED", "scheduled_at": "2026-08-22T08:25:00+08:00"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            calls = []

            result = dispatch_due_publications(
                queue,
                now=datetime(2026, 8, 22, 0, 30, tzinfo=UTC),
                no_send=True,
                publisher=lambda item, no_send: calls.append((item["queue_id"], no_send)) or {"status": "READY_TO_PUBLISH", "qianfan_called": False},
            )

            self.assertEqual(calls, [("q1", True)])
            self.assertEqual(result["processed_count"], 1)
            self.assertFalse(result["qianfan_called"])

    def test_dispatch_accepts_verified_idempotent_replay_without_second_call(self) -> None:
        with TemporaryDirectory() as tmp:
            queue = Path(tmp) / "queue.json"
            queue.write_text(
                json.dumps(
                    {
                        "schema_version": "dayibin-production-publish-queue-v1",
                        "items": [
                            {"queue_id": "q1", "status": "SCHEDULED", "scheduled_at": "2026-08-22T08:20:00+08:00"}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = dispatch_due_publications(
                queue,
                now=datetime(2026, 8, 22, 0, 30, tzinfo=UTC),
                publisher=lambda item, no_send: {
                    "status": "PUBLISHED_VERIFIED",
                    "already_published": True,
                    "qianfan_called": False,
                },
            )
            self.assertEqual(result["status"], "PUBLISHED_VERIFIED")
            self.assertTrue(result["already_published"])
            self.assertFalse(result["qianfan_called"])

    def test_failure_stops_current_item_without_catch_up(self) -> None:
        with TemporaryDirectory() as tmp:
            queue = Path(tmp) / "queue.json"
            queue.write_text(
                json.dumps(
                    {
                        "schema_version": "dayibin-production-publish-queue-v1",
                        "items": [
                            {"queue_id": "q1", "status": "SCHEDULED", "scheduled_at": "2026-08-22T08:20:00+08:00"},
                            {"queue_id": "q2", "status": "SCHEDULED", "scheduled_at": "2026-08-22T08:25:00+08:00"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            calls = []

            with self.assertRaisesRegex(ProductionScheduleError, "stopped"):
                dispatch_due_publications(
                    queue,
                    now=datetime(2026, 8, 22, 0, 30, tzinfo=UTC),
                    publisher=lambda item, no_send: calls.append(item["queue_id"]) or (_ for _ in ()).throw(RuntimeError("unknown result")),
                )

            saved = json.loads(queue.read_text(encoding="utf-8"))
            self.assertEqual(calls, ["q1"])
            self.assertEqual(saved["items"][0]["status"], "STOPPED_AFTER_FAILURE")
            self.assertEqual(saved["items"][1]["status"], "SCHEDULED")

    def test_cross_day_items_require_revalidation_instead_of_catch_up(self) -> None:
        with TemporaryDirectory() as tmp:
            queue = Path(tmp) / "queue.json"
            queue.write_text(
                json.dumps(
                    {
                        "schema_version": "dayibin-production-publish-queue-v1",
                        "items": [
                            {"queue_id": "q1", "status": "SCHEDULED", "scheduled_at": "2026-08-22T22:20:00+08:00", "evergreen": True},
                            {"queue_id": "q2", "status": "SCHEDULED", "scheduled_at": "2026-08-22T22:25:00+08:00", "evergreen": False},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = dispatch_due_publications(
                queue,
                now=datetime(2026, 8, 23, 0, 30, tzinfo=UTC),
                publisher=lambda item, no_send: self.fail("cross-day item must not publish"),
            )

            saved = json.loads(queue.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "CROSS_DAY_HELD")
            self.assertEqual([item["status"] for item in saved["items"]], ["NEEDS_REVALIDATION", "EXPIRED"])


if __name__ == "__main__":
    unittest.main()
