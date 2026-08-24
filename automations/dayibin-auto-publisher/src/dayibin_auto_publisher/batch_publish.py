from __future__ import annotations

from datetime import UTC, datetime
import fcntl
import hashlib
import json
from pathlib import Path
import re
import struct
from typing import Any, Callable, Protocol

from .openclaw import AgentError
from .post_publish_review import enqueue_publication
from .storage import atomic_write_json, read_json


BATCH_ID_PATTERN = re.compile(r"^BATCH-(\d{8})-\d{4}-[0-9a-f]{8}$")
AWAITING = "AWAITING_HUMAN_CONFIRMATION"
PUBLISHED = "PUBLISHED_VERIFIED"


class BatchPublishError(RuntimeError):
    pass


class JsonAgent(Protocol):
    def run_json(self, prompt: str, *, session_id: str) -> dict[str, Any]: ...


def publish_scheduled_item(
    config: Any,
    *,
    batch_id: str,
    content_id: str,
    agent: JsonAgent | None = None,
    no_send: bool = False,
    review_queue_path: str | Path | None = None,
    now: datetime | None = None,
    preflight_resolver: Callable[[list[dict[str, Any]]], dict[str, dict[str, Any]]] | None = None,
    published_metadata_resolver: Callable[[set[str]], dict[str, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    batch_dir = _batch_dir(Path(config.data_dir), batch_id)
    batch_path = batch_dir / "batch.json"
    batch = read_json(batch_path)
    if batch.get("status") != "SCHEDULED" or batch.get("schema_version") not in {
        "dayibin-pending-batch-v2", "dayibin-pending-batch-v3",
    }:
        raise BatchPublishError("scheduled batch is not ready")
    drafts = batch.get("drafts")
    if not isinstance(drafts, list):
        raise BatchPublishError("scheduled batch drafts are invalid")
    matches = [draft for draft in drafts if isinstance(draft, dict) and str(draft.get("content_id") or "") == content_id]
    if len(matches) != 1:
        raise BatchPublishError("scheduled content_id must match exactly one draft")
    draft = matches[0]
    _validate_scheduled_draft(draft, batch_dir)
    plan = _draft_plan(draft, batch_dir)
    state_path = batch_dir / "publish-state.json"
    state = read_json(state_path) if state_path.exists() else {
        "schema_version": "dayibin-batch-publish-state-v1",
        "batch_id": batch_id,
        "results": [],
    }
    results = state.get("results")
    if not isinstance(results, list):
        raise BatchPublishError("batch publish state is invalid")
    existing = next(
        (
            item for item in results
            if isinstance(item, dict)
            and item.get("content_id") == content_id
            and item.get("status") == PUBLISHED
        ),
        None,
    )
    if existing is not None:
        return {**existing, "qianfan_called": False, "already_published": True}
    if preflight_resolver is None:
        raise BatchPublishError("scheduled publish requires a live preflight resolver")
    raw = preflight_resolver([plan])
    preflight = _validate_preflight(
        {"preflight": raw.get(content_id)}, expected_vest=plan["vest_name"]
    )
    current = (now or datetime.now(UTC)).astimezone()
    atomic_write_json(
        batch_dir / f"qianfan-readonly-preflight-{hashlib.sha256(content_id.encode()).hexdigest()[:10]}.json",
        {
            "schema_version": "dayibin-batch-qianfan-preflight-v1",
            "batch_id": batch_id,
            "checked_at": current.isoformat(),
            "qianfan_publish_called": False,
            "items": [{"content_id": content_id, "title": plan["title"], **preflight}],
        },
    )
    if no_send:
        return {
            "status": "READY_TO_PUBLISH",
            "batch_id": batch_id,
            "content_id": content_id,
            "qianfan_called": False,
            "qianfan_readonly_preflight_called": True,
        }
    if agent is None:
        raise BatchPublishError("scheduled publish agent is required")
    try:
        normalized = _publish_one(agent, batch_id, plan, preflight)
        if published_metadata_resolver is not None:
            metadata = published_metadata_resolver({normalized["tid"]}).get(normalized["tid"])
            normalized = _apply_live_metadata(normalized, metadata, plan=plan, preflight=preflight)
    except (AgentError, BatchPublishError) as error:
        _upsert_result(
            results,
            {
                "content_id": content_id,
                "title": plan["title"],
                "status": "STOPPED_AFTER_FAILURE",
                "error": _safe_error(error),
                "recorded_at": current.isoformat(),
            },
        )
        state.update({"status": "STOPPED_AFTER_FAILURE", "results": results})
        atomic_write_json(state_path, state)
        raise
    saved = {
        "content_id": content_id,
        "title": plan["title"],
        "status": PUBLISHED,
        "source_status": normalized["status"],
        "tid": normalized["tid"],
        "url": normalized["url"],
        "vest_name": normalized["vest_name"],
        "forum_name": normalized["forum_name"],
        "type_name": normalized["type_name"],
        "published_at": normalized["published_at"],
        "title_hash": plan["title_hash"],
        "body_hash": plan["body_hash"],
        "material_hash": plan["material_hash"],
    }
    _upsert_result(results, saved)
    state.update({"status": "PUBLISHING", "results": results})
    atomic_write_json(state_path, state)
    enqueue_publication(
        Path(review_queue_path or Path(config.data_dir) / "post-publish-review-queue.json"),
        publication_ref=normalized["tid"],
        published_at=normalized["published_at"],
        metadata={
            "batch_id": batch_id,
            "content_id": content_id,
            "title": plan["title"],
            "vest_name": normalized["vest_name"],
            "persona": plan["persona"],
            "forum_name": normalized["forum_name"],
            "type_name": normalized["type_name"],
            "category": draft["channel"],
            "title_hash": plan["title_hash"],
            "body_hash": plan["body_hash"],
            "material_hash": plan["material_hash"],
        },
    )
    return {**saved, "qianfan_called": True}


def publish_batch(
    config: Any,
    *,
    batch_id: str,
    confirmation_phrase: str,
    agent: JsonAgent | None = None,
    dry_run: bool = False,
    no_send: bool = False,
    review_queue_path: str | Path | None = None,
    now: datetime | None = None,
    preflight_resolver: Callable[[list[dict[str, Any]]], dict[str, dict[str, Any]]] | None = None,
    published_metadata_resolver: Callable[[set[str]], dict[str, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    if dry_run and no_send:
        raise BatchPublishError("--dry-run and --no-send are mutually exclusive")
    batch_dir = _batch_dir(Path(config.data_dir), batch_id)
    lock_path = batch_dir / ".publish.lock"
    current = (now or datetime.now(UTC)).astimezone()

    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise BatchPublishError("batch publish is already running") from error

        batch_path = batch_dir / "batch.json"
        batch = read_json(batch_path)
        drafts = _validate_batch(batch, batch_id, confirmation_phrase, batch_dir)
        state_path = batch_dir / "publish-state.json"
        state = read_json(state_path) if state_path.exists() else {
            "schema_version": "dayibin-batch-publish-state-v1",
            "batch_id": batch_id,
            "results": [],
        }
        results = state.get("results")
        if not isinstance(results, list):
            raise BatchPublishError("batch publish state is invalid")
        verified = {
            str(item.get("content_id") or "")
            for item in results
            if isinstance(item, dict) and item.get("status") == PUBLISHED
        }
        plans = [_draft_plan(draft, batch_dir) for draft in drafts]
        queue_path = Path(
            review_queue_path or Path(config.data_dir) / "post-publish-review-queue.json"
        )

        if dry_run:
            return {
                "status": "DRY_RUN_READY",
                "batch_id": batch_id,
                "qianfan_called": False,
                "qianfan_readonly_preflight_called": False,
                "items": [
                    {
                        "content_id": plan["content_id"],
                        "title": plan["title"],
                        "vest_name": plan["vest_name"],
                        "resolution_status": "NOT_CALLED_DRY_RUN",
                    }
                    for plan in plans
                ],
            }

        if len(verified) == len(plans):
            _ensure_review_queue(results, queue_path)
            return _published_summary(batch_id, results)
        if agent is None and preflight_resolver is None:
            raise BatchPublishError("qianfan agent is required outside dry-run")

        pending_plans = [plan for plan in plans if plan["content_id"] not in verified]
        if preflight_resolver is not None:
            raw_preflights = preflight_resolver(pending_plans)
            preflights = {
                plan["content_id"]: _validate_preflight(
                    {"preflight": raw_preflights.get(plan["content_id"])},
                    expected_vest=plan["vest_name"],
                )
                for plan in pending_plans
            }
        else:
            assert agent is not None
            response = agent.run_json(
                _preflight_prompt(pending_plans),
                session_id=f"dayibin-batch-preflight-{batch_id}",
            )
            preflights = _validate_preflights(response, pending_plans)
        safe_preflight = {
            "schema_version": "dayibin-batch-qianfan-preflight-v1",
            "batch_id": batch_id,
            "checked_at": current.isoformat(),
            "qianfan_publish_called": False,
            "items": [
                {
                    "content_id": plan["content_id"],
                    "title": plan["title"],
                    **preflights.get(plan["content_id"], {"status": "ALREADY_PUBLISHED"}),
                }
                for plan in plans
            ],
        }
        atomic_write_json(batch_dir / "qianfan-readonly-preflight.json", safe_preflight)
        if no_send:
            return {
                "status": "READY_TO_PUBLISH",
                "batch_id": batch_id,
                "qianfan_called": False,
                "qianfan_readonly_preflight_called": True,
                "items": safe_preflight["items"],
            }

        if agent is None:
            raise BatchPublishError("qianfan publish agent is required")

        _ensure_review_queue(results, queue_path)
        for plan in plans:
            if plan["content_id"] in verified:
                continue
            preflight = preflights[plan["content_id"]]
            try:
                normalized = _publish_one(agent, batch_id, plan, preflight)
                if published_metadata_resolver is not None:
                    metadata = published_metadata_resolver({normalized["tid"]}).get(
                        normalized["tid"]
                    )
                    normalized = _apply_live_metadata(
                        normalized, metadata, plan=plan, preflight=preflight
                    )
            except (AgentError, BatchPublishError) as error:
                failure = {
                    "content_id": plan["content_id"],
                    "title": plan["title"],
                    "status": "STOPPED_AFTER_FAILURE",
                    "error": _safe_error(error),
                    "recorded_at": current.isoformat(),
                }
                _upsert_result(results, failure)
                state.update({"status": "STOPPED_AFTER_FAILURE", "results": results})
                atomic_write_json(state_path, state)
                raise BatchPublishError(
                    f"batch stopped after publish failure: {plan['content_id']}"
                ) from error

            saved = {
                "content_id": plan["content_id"],
                "title": plan["title"],
                "status": PUBLISHED,
                "source_status": normalized["status"],
                "tid": normalized["tid"],
                "url": normalized["url"],
                "vest_name": normalized["vest_name"],
                "forum_name": normalized["forum_name"],
                "type_name": normalized["type_name"],
                "published_at": normalized["published_at"],
                "title_hash": plan["title_hash"],
                "body_hash": plan["body_hash"],
                "material_hash": plan["material_hash"],
            }
            _upsert_result(results, saved)
            state.update({"status": "PUBLISHING", "results": results})
            atomic_write_json(state_path, state)
            enqueue_publication(
                queue_path,
                publication_ref=normalized["tid"],
                published_at=normalized["published_at"],
                metadata={
                    "batch_id": batch_id,
                    "content_id": plan["content_id"],
                    "title": plan["title"],
                    "vest_name": normalized["vest_name"],
                    "persona": plan["persona"],
                    "forum_name": normalized["forum_name"],
                    "type_name": normalized["type_name"],
                    "category": "DAILY_VALUE",
                    "title_hash": plan["title_hash"],
                    "body_hash": plan["body_hash"],
                    "material_hash": plan["material_hash"],
                },
            )
            verified.add(plan["content_id"])

        state.update({"status": PUBLISHED, "completed_at": current.isoformat(), "results": results})
        atomic_write_json(state_path, state)
        batch.update(
            {
                "status": PUBLISHED,
                "qianfan_called": True,
                "published_at": current.isoformat(),
            }
        )
        atomic_write_json(batch_path, batch)
        summary = _published_summary(batch_id, results)
        summary["qianfan_called"] = True
        return summary


def _batch_dir(data_dir: Path, batch_id: str) -> Path:
    matched = BATCH_ID_PATTERN.fullmatch(batch_id)
    if matched is None:
        raise BatchPublishError("invalid batch_id")
    date_text = matched.group(1)
    target = data_dir / f"{date_text[:4]}-{date_text[4:6]}-{date_text[6:]}" / "pending-batches" / batch_id
    if not (target / "batch.json").is_file():
        raise BatchPublishError("batch does not exist")
    return target


def _validate_batch(
    batch: dict[str, Any], batch_id: str, confirmation_phrase: str, batch_dir: Path
) -> list[dict[str, Any]]:
    expected = f"确认本批发布：{batch_id}"
    if batch.get("batch_id") != batch_id:
        raise BatchPublishError("batch_id does not match batch file")
    if batch.get("status") != AWAITING:
        raise BatchPublishError("batch status must be AWAITING_HUMAN_CONFIRMATION")
    if batch.get("publish_confirmation_phrase") != expected or confirmation_phrase != expected:
        raise BatchPublishError("confirmation phrase does not match exactly")
    drafts = batch.get("drafts")
    if not isinstance(drafts, list) or not 1 <= len(drafts) <= 3:
        raise BatchPublishError("batch must contain 1-3 drafts")
    for draft in drafts:
        if not isinstance(draft, dict) or draft.get("category") != "DAILY_VALUE":
            raise BatchPublishError("this batch must remain DAILY_VALUE")
        if draft.get("risk_result") != "PASS":
            raise BatchPublishError("draft risk gate is not PASS")
        for key in ("content_id", "title", "html", "vest_name", "persona"):
            if not str(draft.get(key) or "").strip():
                raise BatchPublishError(f"draft is missing {key}")
        for image in draft.get("images") or []:
            path = _image_path(batch_dir, image)
            if not path.is_file():
                raise BatchPublishError(f"draft image is missing: {path.name}")
    return drafts


def _validate_scheduled_draft(draft: dict[str, Any], batch_dir: Path) -> None:
    required = {
        "content_id", "event_id", "channel", "title", "html", "vest_name", "persona",
        "locked_angle_id", "article_form", "document_type", "selected_writing_skill",
        "writing_skill_contract_proof", "editor_name", "editor_dna_path",
        "editor_selection_reason", "editor_dna_read_proof", "writing_session_id",
        "soft_audit", "review",
    }
    if not required.issubset(draft):
        raise BatchPublishError("scheduled draft is missing production-chain fields")
    if draft.get("channel") not in {"HOT_NOW", "DAILY_VALUE"}:
        raise BatchPublishError("scheduled draft channel is invalid")
    if draft.get("risk_result") != "PASS":
        raise BatchPublishError("scheduled draft risk gate is not PASS")
    if draft.get("soft_audit", {}).get("status") != "PASS" or draft.get("review", {}).get("verdict") != "approved":
        raise BatchPublishError("scheduled draft review chain is incomplete")
    from .production_schedule import frozen_contract_hash, review_binding_hashes
    expected_binding = review_binding_hashes(draft)
    for evidence in (draft["soft_audit"], draft["review"]):
        if any(evidence.get(key) != value for key, value in expected_binding.items()):
            raise BatchPublishError("scheduled draft review binding changed")
    if draft.get("frozen_contract_hash") != frozen_contract_hash(draft):
        raise BatchPublishError("scheduled draft frozen contract changed")
    if draft.get("article_form") not in {"APP_SHORT", "WECHAT_LONG"}:
        raise BatchPublishError("scheduled draft writing route is invalid")
    if not all(str(draft.get(key) or "").strip() for key in (
        "document_type", "selected_writing_skill", "editor_name", "editor_dna_path",
        "editor_selection_reason", "writing_session_id",
    )):
        raise BatchPublishError("scheduled draft writing route is incomplete")
    contract_proof = draft.get("writing_skill_contract_proof")
    if not isinstance(contract_proof, dict) or contract_proof.get("status") != "CERTIFIED_ACTIVE_CONTRACT_COMPLETE":
        raise BatchPublishError("scheduled draft writing Skill is not certified")
    contract_path = Path(str(contract_proof.get("contract_path") or ""))
    if not contract_path.is_file() or hashlib.sha256(contract_path.read_bytes()).hexdigest() != contract_proof.get("contract_sha256"):
        raise BatchPublishError("scheduled draft writing Skill contract proof changed")
    dna_proof = draft.get("editor_dna_read_proof")
    if not isinstance(dna_proof, dict):
        raise BatchPublishError("scheduled draft editor DNA read proof is missing")
    if draft.get("editor_dna_path") == "N/A":
        if draft.get("editor_name") != "N/A" or dna_proof.get("status") != "N/A" or not dna_proof.get("reason"):
            raise BatchPublishError("scheduled draft fixed-style editor DNA N/A proof is invalid")
    else:
        dna_path = Path(str(draft["editor_dna_path"]))
        if (
            dna_proof.get("status") != "READ_FULL_EOF"
            or dna_proof.get("path") != str(dna_path)
            or not dna_path.is_file()
            or hashlib.sha256(dna_path.read_bytes()).hexdigest() != dna_proof.get("sha256")
        ):
            raise BatchPublishError("scheduled draft editor DNA proof changed")
    if draft.get("images") and len(draft.get("image_plan") or []) != len(draft["images"]):
        raise BatchPublishError("scheduled draft body image plan is incomplete")
    if draft.get("contract_version") == "daily-8-to-12-v1" and not draft.get("images"):
        if not all(str(draft.get(key) or "").strip() for key in ("no_image_reason", "no_image_policy_proof")):
            raise BatchPublishError("scheduled no-image draft is missing forum policy evidence")
    for image in draft.get("images") or []:
        path = _image_path(batch_dir, image)
        if not path.is_file():
            raise BatchPublishError(f"draft image is missing: {path.name}")


def _draft_plan(draft: dict[str, Any], batch_dir: Path) -> dict[str, Any]:
    images = [_image_path(batch_dir, image) for image in (draft.get("images") or [])]
    title = str(draft["title"]).strip()
    body = str(draft["html"]).strip()
    from .safety import scan_ai_writing_patterns
    ai_hits = scan_ai_writing_patterns(title, body)
    if ai_hits:
        raise BatchPublishError(f"draft failed deterministic AI phrase gate: {', '.join(ai_hits)}")
    _validate_body_images(body, [str(value) for value in draft.get("images") or []], batch_dir)
    _validate_image_manifest(draft, images)
    title_hash = hashlib.sha256(title.encode()).hexdigest()
    body_hash = hashlib.sha256(body.encode()).hexdigest()
    image_hashes = [hashlib.sha256(path.read_bytes()).hexdigest() for path in images]
    material_hash = hashlib.sha256("\0".join([title_hash, body_hash, *image_hashes]).encode()).hexdigest()
    for key, actual in (
        ("title_hash", title_hash),
        ("body_hash", body_hash),
        ("material_hash", material_hash),
    ):
        frozen = str(draft.get(key) or "")
        if frozen and frozen != actual:
            raise BatchPublishError(f"draft {key} changed after confirmation card creation")
    if "image_hashes" in draft and draft["image_hashes"] != image_hashes:
        raise BatchPublishError("draft image_hashes changed after confirmation card creation")
    return {
        "content_id": str(draft["content_id"]),
        "title": title,
        "html": body,
        "vest_name": str(draft["vest_name"]).strip(),
        "persona": str(draft["persona"]).strip(),
        "forum_hint": str(draft.get("forum") or "大宜宾APP").strip(),
        "images": [str(path.resolve()) for path in images],
        "title_hash": title_hash,
        "body_hash": body_hash,
        "material_hash": material_hash,
        "image_hashes": image_hashes,
        "content_hash": material_hash,
    }


def _validate_image_manifest(draft: dict[str, Any], images: list[Path]) -> None:
    if not images:
        if draft.get("image_manifest") not in (None, []):
            raise BatchPublishError("draft image manifest does not match images")
        return
    manifest = draft.get("image_manifest")
    if not isinstance(manifest, list) or len(manifest) != len(images):
        raise BatchPublishError("draft image manifest is missing or incomplete")
    required = {
        "local_path", "sha256", "width", "height", "usage_type",
        "rights_status", "credit", "license_or_authorization",
    }
    for entry, image in zip(manifest, images):
        if not isinstance(entry, dict) or not required.issubset(entry):
            raise BatchPublishError("draft image manifest is missing production rights fields")
        local_path = str(entry.get("local_path") or "")
        if local_path.startswith(("http://", "https://")) or Path(local_path).resolve() != image.resolve():
            raise BatchPublishError("draft image manifest local path is invalid")
        if not entry.get("source_url") and not entry.get("generation_record"):
            raise BatchPublishError("draft image manifest source evidence is missing")
        if str(entry.get("rights_status") or "") in {"", "UNKNOWN", "UNVERIFIED", "SOURCE_MEDIA_REQUIRES_LOCALIZATION"}:
            raise BatchPublishError("draft image manifest rights are unverified")
        if not all(str(entry.get(key) or "").strip() for key in ("usage_type", "credit", "license_or_authorization")):
            raise BatchPublishError("draft image manifest rights evidence is incomplete")
        if hashlib.sha256(image.read_bytes()).hexdigest() != entry.get("sha256"):
            raise BatchPublishError("draft image manifest hash changed")
        if _image_dimensions(image) != (entry.get("width"), entry.get("height")):
            raise BatchPublishError("draft image manifest dimensions changed")


def _image_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if data[:3] == b"GIF" and len(data) >= 10:
        return struct.unpack("<HH", data[6:10])
    if data.startswith(b"\xff\xd8"):
        offset = 2
        while offset + 9 < len(data):
            if data[offset] != 0xFF:
                offset += 1
                continue
            marker = data[offset + 1]
            if marker in range(0xC0, 0xC4):
                height, width = struct.unpack(">HH", data[offset + 5 : offset + 9])
                return width, height
            length = struct.unpack(">H", data[offset + 2 : offset + 4])[0]
            offset += 2 + max(length, 2)
    raise BatchPublishError("draft image manifest dimensions cannot be verified")


def _validate_body_images(body: str, images: list[str], batch_dir: Path | None) -> None:
    if re.search(r"【\s*配图|配图\s*[0-9一二三四五六七八九十]+", body, re.IGNORECASE):
        raise BatchPublishError("draft body contains an image placeholder")
    sources = set(re.findall(r'<img\b[^>]*\bsrc=["\']([^"\']+)["\']', body, re.IGNORECASE))
    for image in images:
        resolved = str(_image_path(batch_dir, image).resolve()) if batch_dir is not None else image
        if image not in sources and resolved not in sources:
            raise BatchPublishError("approved body image is not embedded in draft html")


def _image_path(batch_dir: Path, value: object) -> Path:
    raw = Path(str(value))
    if raw.is_absolute():
        return raw
    parts = raw.parts
    if "images" in parts:
        raw = Path(*parts[parts.index("images") :])
    return batch_dir / raw


def _preflight_prompt(plans: list[dict[str, Any]]) -> str:
    request = [
        {
            "content_id": plan["content_id"],
            **{
                key: plan[key]
                for key in ("title", "html", "vest_name", "persona", "forum_hint")
            },
        }
        for plan in plans
    ]
    return f"""
使用 qianfan-skill 对以下 DAILY_VALUE 帖子做一次批量只读预检，禁止发布、上传或编辑任何内容。

必须执行：
1. 用 /helper/admin/search-vest-option 按昵称实时精确查询，规范化空白后仍须唯一同名、enable=1、desc为空且真实ID存在；不得输出ID。
2. 实时读取 /bbs/forum/forum-list。forum_hint=大宜宾APP 只是平台提示，不是板块名；请根据标题和正文选择一个真实存在且唯一匹配的合法板块，不得输出ID。
3. 对选中板块调用 /review/vest-publish/init；若 required=1，只能从实时types选择最匹配分类并确认真实ID存在；若required=0，分类为“无”。
4. 按 qianfan-skill 合同记录本次查询审计日志。不得输出Token、Cookie、Authorization、vest_id、forum_id或type_id。
5. 最终只输出JSON，不要Markdown。

请求：{json.dumps(request, ensure_ascii=False)}

JSON合同：
{{"preflights":[{{"content_id":"...","vest_name":"...","vest_unique":true,"vest_enabled":true,"vest_id_present":true,"forum_name":"...","forum_unique":true,"forum_id_present":true,"type_required":false,"type_name":"无","type_id_present":false}}]}}
""".strip()


def _validate_preflights(
    response: dict[str, Any], plans: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    if len(plans) == 1 and isinstance(response.get("preflight"), dict):
        rows = [{"content_id": plans[0]["content_id"], **response["preflight"]}]
    else:
        rows = response.get("preflights")
    if not isinstance(rows, list) or len(rows) != len(plans):
        raise BatchPublishError("qianfan batch preflight response is incomplete")
    indexed = {
        str(row.get("content_id") or ""): row
        for row in rows
        if isinstance(row, dict)
    }
    if len(indexed) != len(plans):
        raise BatchPublishError("qianfan batch preflight content IDs are not unique")
    output: dict[str, dict[str, Any]] = {}
    for plan in plans:
        row = indexed.get(plan["content_id"])
        if row is None:
            raise BatchPublishError("qianfan batch preflight content ID is missing")
        output[plan["content_id"]] = _validate_preflight(
            {"preflight": row}, expected_vest=plan["vest_name"]
        )
    return output


def _validate_preflight(response: dict[str, Any], *, expected_vest: str) -> dict[str, Any]:
    item = response.get("preflight")
    if not isinstance(item, dict):
        raise BatchPublishError("qianfan preflight response is missing")
    required_true = (
        item.get("vest_unique") is True,
        item.get("vest_enabled") is True,
        item.get("vest_id_present") is True,
        item.get("forum_unique") is True,
        item.get("forum_id_present") is True,
    )
    if str(item.get("vest_name") or "").strip() != expected_vest or not all(required_true):
        raise BatchPublishError("qianfan preflight did not uniquely resolve vest/forum")
    forum_name = str(item.get("forum_name") or "").strip()
    type_required = item.get("type_required") is True
    type_name = str(item.get("type_name") or "").strip()
    if not forum_name or (type_required and (not type_name or item.get("type_id_present") is not True)):
        raise BatchPublishError("qianfan preflight did not resolve required category")
    if not type_required:
        type_name = "无"
    return {
        "status": "RESOLVED",
        "vest_name": expected_vest,
        "vest_unique": True,
        "vest_enabled": True,
        "vest_id_present": True,
        "forum_name": forum_name,
        "forum_unique": True,
        "forum_id_present": True,
        "type_required": type_required,
        "type_name": type_name,
        "type_id_present": item.get("type_id_present") is True,
    }


def _publish_one(
    agent: JsonAgent, batch_id: str, plan: dict[str, Any], preflight: dict[str, Any]
) -> dict[str, Any]:
    try:
        response = agent.run_json(
            _publish_prompt(plan, preflight),
            session_id=f"dayibin-batch-publish-{batch_id}-{plan['content_hash'][:10]}",
        )
        return _validate_publish_result(response, plan, preflight)
    except (AgentError, BatchPublishError) as original:
        checked = agent.run_json(
            _verify_prompt(plan, preflight),
            session_id=f"dayibin-batch-verify-{batch_id}-{plan['content_hash'][:10]}",
        )
        try:
            return _validate_publish_result(checked, plan, preflight)
        except BatchPublishError:
            raise original


def _publish_prompt(plan: dict[str, Any], preflight: dict[str, Any]) -> str:
    request = {
        "title": plan["title"],
        "html": plan["html"],
        "images": plan["images"],
        "expected_body_image_count": len(plan["images"]),
        "vest_name": plan["vest_name"],
        "forum_name": preflight["forum_name"],
        "type_name": preflight["type_name"],
        "title_hash": plan["title_hash"],
        "body_hash": plan["body_hash"],
        "material_hash": plan["material_hash"],
    }
    return f"""
使用 qianfan-skill 发布这一篇已经人工确认的 DAILY_VALUE 帖子，只允许一次发布。

必须执行：
1. 再次实时精确解析唯一启用马甲、唯一合法板块和该板块实时分类；不得使用旧ID或猜ID，解析结果必须与请求中的名称一致。
2. 发布前查询已通过和待审核帖子；若同一马甲已有完全相同标题和正文，返回existing，不重复发布。标题相同但正文不同则停止。
3. 逐张上传请求中的本地图片，最多3张；上传后的每张图既可加入attaches作封面，也必须用 `lazy qf-slider`、`style="width:100%;"`、真实 `data-scale` 作为正文`<img>`节点分散插入items_data[].content。严禁 `width="0"` 或 `height="0"`；只有attaches、正文无图或零尺寸图均视为失败。
4. 仅调用一次 /review/vest-publish/add。响应不明确时先只读查重，禁止盲目重发。
5. 发布后用 /review/vest-publish/info 核对帖子ID、完整标题、纯文字正文、马甲和正文`<img>`数量；逐张访问正文图片确认HTTP成功，再访问公开帖子确认正文中可见、`qf-slider`数量等于正文图数且零尺寸图片为0。任何一项不符都不得返回成功。
6. 按qianfan-skill合同记录执行日志。不得输出任何内部ID、Token、Cookie或Authorization值。
7. 最终只输出JSON，不要Markdown。

请求：{json.dumps(request, ensure_ascii=False)}

JSON合同：
{{"publish_result":{{"status":"published|existing","tid":"...","url":"https://...","vest_name":"...","forum_name":"...","type_name":"...","title_verified":true,"body_verified":true,"vest_verified":true,"body_images_verified":true,"body_image_count":0,"qf_slider_count":0,"zero_size_img_count":0,"public_http_ok":true,"published_at":"ISO-8601"}}}}
其中 body_image_count 和 qf_slider_count 必须返回实际整数并等于 expected_body_image_count，zero_size_img_count 必须为0。
""".strip()


def _verify_prompt(plan: dict[str, Any], preflight: dict[str, Any]) -> str:
    request = {
        "title": plan["title"],
        "html": plan["html"],
        "expected_body_image_count": len(plan["images"]),
        "vest_name": plan["vest_name"],
        "forum_name": preflight["forum_name"],
        "type_name": preflight["type_name"],
    }
    return f"""
使用 qianfan-skill 只读查重核验一次可能结果不明确的发帖，禁止发布、编辑、上传或重试。
只在同一马甲、完整标题、纯文字正文和正文图片数量全部一致，并且公开页 `qf-slider` 数量一致、零尺寸正文图片为0、正文图片及公开链接可访问时返回existing；否则返回not_found。不得输出内部ID或凭证，按Skill合同记录查询日志。
请求：{json.dumps(request, ensure_ascii=False)}
JSON合同：{{"publish_result":{{"status":"existing|not_found","tid":"...","url":"https://...","vest_name":"...","forum_name":"...","type_name":"...","title_verified":true,"body_verified":true,"vest_verified":true,"body_images_verified":true,"body_image_count":0,"qf_slider_count":0,"zero_size_img_count":0,"public_http_ok":true,"published_at":"ISO-8601"}}}}。body_image_count 和 qf_slider_count 必须等于 expected_body_image_count，zero_size_img_count 必须为0。
""".strip()


def _validate_publish_result(
    response: dict[str, Any], plan: dict[str, Any], preflight: dict[str, Any]
) -> dict[str, Any]:
    item = response.get("publish_result")
    if not isinstance(item, dict) or item.get("status") not in {"published", "existing"}:
        raise BatchPublishError("qianfan publish result is not verified")
    if any(
        item.get(key) is not True
        for key in ("title_verified", "body_verified", "vest_verified", "public_http_ok")
    ):
        raise BatchPublishError("qianfan public verification failed")
    if plan["images"] and (
        item.get("body_images_verified") is not True
        or item.get("body_image_count") != len(plan["images"])
        or item.get("qf_slider_count") != len(plan["images"])
        or item.get("zero_size_img_count") != 0
    ):
        raise BatchPublishError("qianfan body images are not publicly verified")
    expected = {
        "vest_name": plan["vest_name"],
        "forum_name": preflight["forum_name"],
        "type_name": preflight["type_name"],
    }
    if any(str(item.get(key) or "").strip() != value for key, value in expected.items()):
        raise BatchPublishError("qianfan published target does not match preflight")
    normalized = {key: str(item.get(key) or "").strip() for key in (
        "status", "tid", "url", "vest_name", "forum_name", "type_name", "published_at"
    )}
    if not all(normalized.values()) or not normalized["url"].startswith("https://"):
        raise BatchPublishError("qianfan publish result is incomplete")
    try:
        datetime.fromisoformat(normalized["published_at"].replace("Z", "+00:00"))
    except ValueError as error:
        raise BatchPublishError("qianfan published_at is invalid") from error
    return normalized


def _apply_live_metadata(
    result: dict[str, Any],
    metadata: dict[str, Any] | None,
    *,
    plan: dict[str, Any],
    preflight: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        raise BatchPublishError("qianfan post-publish metadata is missing")
    expected = {
        "tid": result["tid"],
        "title": plan["title"],
        "vest_name": plan["vest_name"],
        "forum_name": preflight["forum_name"],
    }
    if any(str(metadata.get(key) or "").strip() != value for key, value in expected.items()):
        raise BatchPublishError("qianfan post-publish metadata does not match")
    published_at = str(metadata.get("published_at") or "").strip()
    try:
        datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise BatchPublishError("qianfan live published_at is invalid") from error
    return {**result, "published_at": published_at}


def _upsert_result(results: list[dict[str, Any]], value: dict[str, Any]) -> None:
    content_id = str(value.get("content_id") or "")
    for index, item in enumerate(results):
        if isinstance(item, dict) and str(item.get("content_id") or "") == content_id:
            results[index] = value
            return
    results.append(value)


def _ensure_review_queue(results: list[dict[str, Any]], queue_path: Path) -> None:
    for item in results:
        if not isinstance(item, dict) or item.get("status") != PUBLISHED:
            continue
        if not all(str(item.get(key) or "") for key in ("tid", "published_at")):
            continue
        enqueue_publication(
            queue_path,
            publication_ref=str(item["tid"]),
            published_at=str(item["published_at"]),
            metadata={
                key: item[key]
                for key in (
                    "content_id", "title", "vest_name", "forum_name", "type_name",
                    "title_hash", "body_hash", "material_hash"
                )
                if key in item
            },
        )


def _published_summary(batch_id: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    published = [item for item in results if isinstance(item, dict) and item.get("status") == PUBLISHED]
    return {
        "status": PUBLISHED,
        "batch_id": batch_id,
        "qianfan_called": False,
        "published_count": len(published),
        "items": published,
    }


def _safe_error(error: Exception) -> str:
    text = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", str(error))
    return text[:300]
