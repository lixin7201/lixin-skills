from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from dayibin_auto_publisher.batch_publish import (
    BatchPublishError,
    _draft_plan,
    _publish_prompt,
    _validate_publish_result,
    publish_batch,
    publish_scheduled_item,
)
from dayibin_auto_publisher.production_schedule import frozen_contract_hash, review_binding_hashes


VALID_BATCH_ID = "BATCH-20260822-1313-51caf16a"
VALID_PHRASE = f"确认本批发布：{VALID_BATCH_ID}"
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


class FakeAgent:
    def __init__(
        self,
        *,
        preflight: dict | None = None,
        preflights: list[dict] | None = None,
        publish: dict | None = None,
    ):
        self.preflight = preflight or {
            "preflight": {
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
            }
        }
        self.publish = publish or {
            "publish_result": {
                "status": "published",
                "tid": "900001",
                "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=900001",
                "vest_name": "forever21",
                "forum_name": "城市更新",
                "type_name": "无",
                "title_verified": True,
                "body_verified": True,
                "vest_verified": True,
                "public_http_ok": True,
                "published_at": "2026-08-22T14:00:00+08:00",
            }
        }
        self.preflights = preflights
        self.calls: list[str] = []

    def run_json(self, prompt: str, *, session_id: str) -> dict:
        self.calls.append(prompt)
        if "只读预检" in prompt:
            if self.preflights is not None:
                return {"preflights": self.preflights}
            return self.preflight
        if "发布这一篇" in prompt:
            return self.publish
        if "只读查重核验" in prompt:
            return {"publish_result": {"status": "not_found"}}
        raise AssertionError("unexpected agent prompt")


class ExplodingAgent:
    def run_json(self, prompt: str, *, session_id: str) -> dict:
        raise AssertionError("dry-run must not call qianfan agent")


class BatchPublishTests(unittest.TestCase):
    def test_freeze_rejects_image_placeholders_and_unembedded_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch_dir = Path(tmp)
            image = batch_dir / "fact-card.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8 + b"\x00\x00\x00\x01\x00\x00\x00\x01")
            draft = {
                "content_id": "content-1",
                "title": "标题",
                "html": "<p>【配图1】事实卡</p>",
                "vest_name": "forever21",
                "persona": "城市观察室型",
                "images": [str(image)],
            }

            with self.assertRaisesRegex(BatchPublishError, "placeholder"):
                _draft_plan(draft, batch_dir)

            draft["html"] = "<p>正文</p>"
            with self.assertRaisesRegex(BatchPublishError, "embedded"):
                _draft_plan(draft, batch_dir)

            draft["html"] = f'<p>正文</p><img src="{image}">'
            draft["image_manifest"] = [{
                "local_path": str(image), "source_url": "https://example.com/fact-card.png",
                "sha256": hashlib.sha256(image.read_bytes()).hexdigest(), "width": 1, "height": 1,
                "usage_type": "资料图", "rights_status": "AUTHORIZED", "credit": "测试来源",
                "license_or_authorization": "测试授权",
            }]
            self.assertEqual(_draft_plan(draft, batch_dir)["images"], [str(image.resolve())])

            draft["html"] = f'<p>目前能确认的信息不算多，接下来就看后续安排。</p><img src="{image}">'
            with self.assertRaisesRegex(BatchPublishError, "AI phrase"):
                _draft_plan(draft, batch_dir)

    def test_freeze_rejects_remote_or_unlicensed_image_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch_dir = Path(tmp)
            image = batch_dir / "photo.jpg"
            image.write_bytes(b"not-a-real-image")
            draft = {
                "content_id": "content-1", "title": "标题",
                "html": f'<p>正文</p><img src="{image}">', "vest_name": "forever21",
                "persona": "城市观察室型", "images": [str(image)],
                "image_manifest": [{"local_path": "https://cdn.example/photo.jpg"}],
            }
            with self.assertRaisesRegex(BatchPublishError, "image manifest"):
                _draft_plan(draft, batch_dir)

    def test_hot_now_and_daily_value_use_the_same_scheduled_publish_gate(self):
        for channel in ("HOT_NOW", "DAILY_VALUE"):
            for schema_version in ("dayibin-pending-batch-v2", "dayibin-pending-batch-v3"):
                with self.subTest(channel=channel, schema_version=schema_version), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    config, batch_dir = self._fixture(root)
                    batch = json.loads(batch_dir.joinpath("batch.json").read_text(encoding="utf-8"))
                    batch.update(
                        {
                            "schema_version": schema_version,
                            "status": "SCHEDULED",
                            "schedule_confirmation_phrase": f"确认本批排期：{VALID_BATCH_ID}",
                        }
                    )
                    batch.pop("publish_confirmation_phrase")
                    draft = batch["drafts"][0]
                    draft.update(
                        {
                            "event_id": "event-1",
                            "channel": channel,
                            "category": channel,
                            "locked_angle_id": "A1",
                            "article_form": "APP_SHORT",
                            "soft_audit": {"status": "PASS"},
                            "review": {"verdict": "approved"},
                            **_app_writing_route(),
                        }
                    )
                    binding = review_binding_hashes(draft)
                    draft["soft_audit"].update(binding)
                    draft["review"].update(binding)
                    draft["frozen_contract_hash"] = frozen_contract_hash(draft)
                    batch_dir.joinpath("batch.json").write_text(json.dumps(batch, ensure_ascii=False), encoding="utf-8")

                    result = publish_scheduled_item(
                        config,
                        batch_id=VALID_BATCH_ID,
                        content_id="fact-1",
                        no_send=True,
                        preflight_resolver=lambda plans: {
                            "fact-1": FakeAgent().preflight["preflight"]
                        },
                    )

                    self.assertEqual(result["status"], "READY_TO_PUBLISH")
                    self.assertFalse(result["qianfan_called"])

    def _fixture(
        self,
        root: Path,
        *,
        status: str = "AWAITING_HUMAN_CONFIRMATION",
        draft_count: int = 1,
    ):
        data_dir = root / "data"
        batch_dir = data_dir / "2026-08-22" / "pending-batches" / VALID_BATCH_ID
        batch_dir.mkdir(parents=True)
        batch = {
            "schema_version": "dayibin-pending-batch-v1",
            "batch_id": VALID_BATCH_ID,
            "status": status,
            "mode": "DAILY_VALUE",
            "publish_confirmation_phrase": VALID_PHRASE,
            "drafts": [
                {
                    "content_id": f"fact-{index}",
                    "category": "DAILY_VALUE",
                    "title": f"宜宾城市建设有了新变化{index}",
                    "html": "<p>这是经过审核的正文。</p>",
                    "vest_name": "forever21",
                    "persona": "城市观察室型",
                    "forum": "大宜宾APP",
                    "images": [],
                    "risk_result": "PASS",
                }
                for index in range(1, draft_count + 1)
            ],
        }
        (batch_dir / "batch.json").write_text(
            json.dumps(batch, ensure_ascii=False), encoding="utf-8"
        )
        return SimpleNamespace(data_dir=data_dir), batch_dir

    def test_wrong_confirmation_phrase_cannot_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            config, _ = self._fixture(Path(tmp))
            agent = FakeAgent()

            with self.assertRaisesRegex(BatchPublishError, "confirmation phrase"):
                publish_batch(
                    config,
                    batch_id=VALID_BATCH_ID,
                    confirmation_phrase="确认本批发布：错误批次",
                    agent=agent,
                )

            self.assertEqual(agent.calls, [])

    def test_superseded_batch_cannot_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            config, _ = self._fixture(Path(tmp), status="SUPERSEDED_DUPLICATE_SMOKE")
            agent = FakeAgent()

            with self.assertRaisesRegex(BatchPublishError, "AWAITING_HUMAN_CONFIRMATION"):
                publish_batch(
                    config,
                    batch_id=VALID_BATCH_ID,
                    confirmation_phrase=VALID_PHRASE,
                    agent=agent,
                )

            self.assertEqual(agent.calls, [])

    def test_non_unique_vest_or_forum_blocks_publish(self):
        for field in ("vest_unique", "forum_unique"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                config, _ = self._fixture(Path(tmp))
                preflight = FakeAgent().preflight
                preflight["preflight"][field] = False
                agent = FakeAgent(preflight=preflight)

                with self.assertRaisesRegex(BatchPublishError, "preflight"):
                    publish_batch(
                        config,
                        batch_id=VALID_BATCH_ID,
                        confirmation_phrase=VALID_PHRASE,
                        no_send=True,
                        agent=agent,
                    )

                self.assertFalse(any("发布这一篇" in prompt for prompt in agent.calls))

    def test_already_verified_article_is_not_published_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            config, batch_dir = self._fixture(Path(tmp))
            (batch_dir / "publish-state.json").write_text(
                json.dumps(
                    {
                        "schema_version": "dayibin-batch-publish-state-v1",
                        "batch_id": VALID_BATCH_ID,
                        "results": [
                            {
                                "content_id": "fact-1",
                                "status": "PUBLISHED_VERIFIED",
                                "tid": "900001",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            agent = FakeAgent()

            result = publish_batch(
                config,
                batch_id=VALID_BATCH_ID,
                confirmation_phrase=VALID_PHRASE,
                agent=agent,
            )

            self.assertEqual(result["status"], "PUBLISHED_VERIFIED")
            self.assertEqual(agent.calls, [])

    def test_dry_run_never_calls_qianfan(self):
        with tempfile.TemporaryDirectory() as tmp:
            config, _ = self._fixture(Path(tmp))

            result = publish_batch(
                config,
                batch_id=VALID_BATCH_ID,
                confirmation_phrase=VALID_PHRASE,
                dry_run=True,
                agent=ExplodingAgent(),
            )

            self.assertEqual(result["status"], "DRY_RUN_READY")
            self.assertFalse(result["qianfan_called"])
            self.assertEqual(result["items"][0]["resolution_status"], "NOT_CALLED_DRY_RUN")

    def test_publish_prompt_requires_images_inside_body_not_cover_only(self):
        plan = {
            "title": "标题", "html": "<p>正文</p>", "images": ["/tmp/one.jpg"],
            "vest_name": "forever21", "title_hash": "a", "body_hash": "b",
            "material_hash": "c",
        }
        prompt = _publish_prompt(plan, {"forum_name": "城市更新", "type_name": "无"})

        self.assertIn("作为正文`<img>`节点", prompt)
        self.assertIn("lazy qf-slider", prompt)
        self.assertIn('width="0"', prompt)

    def test_image_publish_result_requires_verified_body_images(self):
        plan = {"images": ["/tmp/one.jpg"], "vest_name": "forever21"}
        preflight = {"forum_name": "城市更新", "type_name": "无"}
        result = dict(FakeAgent().publish["publish_result"])

        with self.assertRaisesRegex(BatchPublishError, "body images"):
            _validate_publish_result({"publish_result": result}, plan, preflight)

        result.update({
            "body_images_verified": True,
            "body_image_count": 1,
            "qf_slider_count": 1,
            "zero_size_img_count": 0,
        })
        self.assertEqual(
            _validate_publish_result({"publish_result": result}, plan, preflight)["tid"],
            "900001",
        )

    def test_each_verified_publish_is_saved_and_enqueued(self):
        with tempfile.TemporaryDirectory() as tmp:
            config, batch_dir = self._fixture(Path(tmp))
            agent = FakeAgent()
            queue_path = config.data_dir / "post-publish-review-queue.json"

            result = publish_batch(
                config,
                batch_id=VALID_BATCH_ID,
                confirmation_phrase=VALID_PHRASE,
                agent=agent,
                review_queue_path=queue_path,
                now=datetime(2026, 8, 22, 6, 0, tzinfo=UTC),
            )

            saved = json.loads((batch_dir / "publish-state.json").read_text(encoding="utf-8"))
            queue = json.loads(queue_path.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "PUBLISHED_VERIFIED")
            self.assertEqual(saved["results"][0]["status"], "PUBLISHED_VERIFIED")
            self.assertEqual([item["checkpoint"] for item in queue["items"]], ["30m", "2h", "24h"])

    def test_no_send_preflights_three_drafts_in_one_agent_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            config, _ = self._fixture(Path(tmp), draft_count=3)
            items = []
            for index in range(1, 4):
                item = dict(FakeAgent().preflight["preflight"])
                item["content_id"] = f"fact-{index}"
                items.append(item)
            agent = FakeAgent(preflights=items)

            result = publish_batch(
                config,
                batch_id=VALID_BATCH_ID,
                confirmation_phrase=VALID_PHRASE,
                no_send=True,
                agent=agent,
            )

            self.assertEqual(result["status"], "READY_TO_PUBLISH")
            self.assertEqual(len(agent.calls), 1)


if __name__ == "__main__":
    unittest.main()
