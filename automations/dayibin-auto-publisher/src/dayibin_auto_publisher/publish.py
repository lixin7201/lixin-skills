from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlparse

from .storage import atomic_write_json, read_json


class PublishError(RuntimeError):
    pass


class JsonAgent(Protocol):
    def run_json(self, prompt: str, *, session_id: str) -> dict[str, Any]: ...


def publish_drafts(
    agent: JsonAgent,
    business_date: date,
    drafts_payload: dict[str, Any],
    profiles: tuple[dict[str, Any], ...],
    result_path: str | Path,
    *,
    limit: int,
) -> dict[str, Any]:
    target = Path(result_path)
    payload = (
        read_json(target)
        if target.exists()
        else {"schema_version": 1, "business_date": business_date.isoformat(), "results": []}
    )
    results = payload.get("results")
    if not isinstance(results, list):
        raise PublishError("publish results file is invalid")
    successful = {
        str(result.get("idempotency_key"))
        for result in results
        if isinstance(result, dict) and result.get("status") in {"published", "existing"}
    }
    profile_map = {str(profile.get("id")): profile for profile in profiles}

    processed = 0
    for draft in drafts_payload.get("drafts", []):
        if processed >= limit:
            break
        if not isinstance(draft, dict) or not draft.get("accepted"):
            continue
        profile_id = str(draft.get("profile_id") or "")
        profile = profile_map.get(profile_id)
        if profile is None:
            raise PublishError(f"profile not configured: {profile_id}")
        vest_name = _required_profile_text(profile, "vest_name")
        forum_id = _required_profile_text(profile, "forum_id")
        idempotency_key = _idempotency_key(draft, vest_name, forum_id)
        if idempotency_key in successful:
            continue
        response = agent.run_json(
            _publish_prompt(draft, profile, idempotency_key),
            session_id=f"dayibin-publish-{business_date:%Y%m%d}-{idempotency_key[:12]}",
        )
        result = response.get("publish_result")
        if not isinstance(result, dict):
            raise PublishError("qianfan result must contain publish_result object")
        normalized = _validate_result(result)
        normalized.update(
            {
                "item_id": draft.get("item_id"),
                "profile_id": profile_id,
                "title": draft.get("title"),
                "idempotency_key": idempotency_key,
            }
        )
        results.append(normalized)
        successful.add(idempotency_key)
        processed += 1
        payload["results"] = results
        atomic_write_json(target, payload)

    payload["published_count"] = sum(
        1
        for result in results
        if isinstance(result, dict) and result.get("status") in {"published", "existing"}
    )
    atomic_write_json(target, payload)
    return payload


def _publish_prompt(
    draft: dict[str, Any], profile: dict[str, Any], idempotency_key: str
) -> str:
    request = {
        "vest_name": profile["vest_name"],
        "forum_id": str(profile["forum_id"]),
        "preferred_type_name": profile.get("type_name"),
        "title": draft["title"],
        "html": draft["html"],
        "source_url": draft.get("source_url"),
        "idempotency_key": idempotency_key,
    }
    return f"""
使用 qianfan-skill 发布一篇大宜宾 APP 帖子。

必须严格执行：
1. 检查当前千帆配置和 Token；失败就停止，不得猜测成功。
2. 实时获取马甲列表，按 vest_name 精确匹配并确认 enable=1，发帖时使用实际 vest_id。
3. 使用指定 forum_id，发帖前调用 /review/vest-publish/init 查询是否强制主题分类，并从实时 types 中选择匹配分类；不得写死旧 target_sid。
4. 发帖前查询该马甲近期帖子；若已存在完全相同标题和正文，返回 existing，不重复发布。
5. 发布后调用 /domain/index 生成真实帖子链接，并按 qianfan-skill 要求记录执行日志。
6. 不输出 Token、密码、Cookie 或其他凭据。
7. 最终只输出一个 JSON 对象，不要 Markdown、解释或代码围栏。

请求：
{json.dumps(request, ensure_ascii=False)}

JSON 合同：
{{"publish_result":{{"status":"published|existing","tid":"...","url":"https://...","vest_id":"...","forum_id":"...","type_id":"..."}}}}
""".strip()


def _required_profile_text(profile: dict[str, Any], key: str) -> str:
    value = profile.get(key)
    if value is None or not str(value).strip():
        raise PublishError(f"profile {profile.get('id')} is missing {key}")
    return str(value).strip()


def _idempotency_key(draft: dict[str, Any], vest_name: str, forum_id: str) -> str:
    value = "\0".join(
        (
            str(draft.get("item_id") or ""),
            str(draft.get("title") or ""),
            str(draft.get("html") or ""),
            vest_name,
            forum_id,
        )
    )
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_result(result: dict[str, Any]) -> dict[str, str]:
    status = str(result.get("status") or "")
    if status not in {"published", "existing"}:
        raise PublishError(f"unexpected qianfan status: {status or 'missing'}")
    required = ("tid", "url", "vest_id", "forum_id", "type_id")
    normalized = {"status": status}
    for key in required:
        value = str(result.get(key) or "").strip()
        if not value:
            raise PublishError(f"qianfan result is missing {key}")
        normalized[key] = value
    parsed = urlparse(normalized["url"])
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise PublishError("qianfan result contains invalid url")
    return normalized
