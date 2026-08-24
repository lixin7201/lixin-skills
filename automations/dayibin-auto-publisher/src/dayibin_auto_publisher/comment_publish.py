from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Protocol
from urllib.parse import urlparse

from .storage import atomic_write_json, read_json


class CommentPublishError(RuntimeError):
    pass


class JsonAgent(Protocol):
    def run_json(self, prompt: str, *, session_id: str) -> dict[str, Any]: ...


class DirectReplyPublisher(Protocol):
    def publish_replies(self, **kwargs) -> dict[str, Any]: ...


def publish_comment_batch(
    agent: JsonAgent,
    business_date: date,
    profile: dict[str, Any],
    posts: list[dict[str, Any]],
    comments: list[dict[str, Any]],
    result_path: str | Path,
    *,
    round_id: str | None = None,
    publisher: DirectReplyPublisher | None = None,
) -> dict[str, Any]:
    if len(comments) > 5:
        raise CommentPublishError("qianfan comment batch accepts at most 5 replies")
    vest_name = str(profile.get("vest_name") or "").strip()
    if not vest_name:
        raise CommentPublishError(f"comment profile {profile.get('id')} is missing vest_name")
    expected_vest_id = str(profile.get("vest_id") or "").strip()
    if not expected_vest_id:
        raise CommentPublishError(f"comment profile {profile.get('id')} is missing vest_id")
    target = Path(result_path)
    payload = (
        read_json(target)
        if target.exists()
        else {"schema_version": 1, "business_date": business_date.isoformat(), "results": []}
    )
    results = payload.get("results")
    if not isinstance(results, list):
        raise CommentPublishError("comment publish results file is invalid")
    completed_post_keys = {
        str(item.get("post_key"))
        for item in results
        if isinstance(item, dict) and item.get("status") in {"published", "existing"}
    }
    post_map = {str(item.get("thread_id") or ""): item for item in posts}
    pending: list[dict[str, Any]] = []
    for comment in comments:
        if not comment.get("accepted"):
            raise CommentPublishError("only safety-accepted comments may be published")
        thread_id = str(comment.get("thread_id") or "")
        if thread_id not in post_map:
            raise CommentPublishError(f"comment references unknown thread_id: {thread_id}")
        target_reply_id = str(comment.get("target_reply_id") or "").strip()
        post_key = _post_key(business_date, thread_id, target_reply_id)
        if post_key in completed_post_keys:
            continue
        pending.append(
            {
                "thread_id": thread_id,
                "pid": str(post_map[thread_id].get("pid") or "0"),
                "fid": str(post_map[thread_id].get("fid") or ""),
                "title": str(post_map[thread_id].get("title") or ""),
                "url": str(post_map[thread_id].get("url") or ""),
                "comment": str(comment.get("comment") or ""),
                "target_reply_id": target_reply_id,
                "post_key": post_key,
            }
        )
    if not pending:
        return _finish_payload(payload)
    response = (
        publisher.publish_replies(
            vest_name=vest_name,
            vest_id=expected_vest_id,
            business_date=business_date,
            pending=pending,
        )
        if publisher is not None
        else agent.run_json(
            qianfan_reply_prompt(vest_name, expected_vest_id, pending),
            session_id=f"dayibin-comment-{business_date:%Y%m%d}-{round_id or 'batch'}-{_batch_hash(pending)[:10]}",
        )
    )
    raw_results = response.get("publish_results")
    if not isinstance(raw_results, list):
        raise CommentPublishError("qianfan result must contain publish_results array")
    expected_ids = {item["thread_id"] for item in pending}
    if len(raw_results) != len(pending):
        raise CommentPublishError("qianfan result count does not match requested comments")
    pending_map = {item["thread_id"]: item for item in pending}
    seen: set[str] = set()
    for raw in raw_results:
        normalized = _validate_result(raw, expected_ids, expected_vest_id)
        thread_id = normalized["thread_id"]
        if thread_id in seen:
            raise CommentPublishError("qianfan returned duplicate thread_id")
        seen.add(thread_id)
        request = pending_map[thread_id]
        canonical_url = request["url"]
        _validate_thread_url(canonical_url, thread_id, "source canonical")
        normalized["qianfan_url"] = normalized["url"]
        normalized["url"] = canonical_url
        normalized.update(
            {
                "business_date": business_date.isoformat(),
                "profile_id": str(profile.get("id") or ""),
                "vest_name": vest_name,
                "comment": request["comment"],
                "comment_sha256": _comment_hash(request["comment"]),
                "post_key": request["post_key"],
                "target_reply_id": request["target_reply_id"],
                "idempotency_key": _idempotency_key(
                    business_date,
                    thread_id,
                    normalized["vest_id"],
                    request["comment"],
                ),
                "round_id": round_id,
            }
        )
        results.append(normalized)
    payload["results"] = results
    payload = _finish_payload(payload)
    atomic_write_json(target, payload)
    return payload


def qianfan_reply_prompt(
    vest_name: str, vest_id: str, pending: list[dict[str, Any]]
) -> str:
    request = {"vest_name": vest_name, "vest_id": vest_id, "replies": pending}
    return f"""
使用 qianfan-skill 对大宜宾 APP 帖子执行一批运营回复。

必须严格执行：
1. 本批只有 {len(pending)} 条且不得扩展；qianfan 单批上限为 5 条。
2. 检查当前千帆配置和 Token；任何鉴权失败立即停止，不得登录重试或猜测成功。
3. vest_name 与 vest_id 是用户已确认的固定映射；必须原样使用请求中的 vest_id，禁止调用随机马甲列表后改用其他账号。若接口明确返回该账号禁用或异常则立即停止。
4. 每条回复前读取目标帖子详情，确认 thread_id、fid、title 和允许回复状态仍匹配。
5. 调用 /review/vest-reply/add；uid 与实时 vest_id 保持一致，content 使用 <p>评论正文</p>；有 target_reply_id 时 reply_id 必须使用该值，否则回复主帖。
6. 若同一马甲已经在该帖发布完全相同内容，返回 existing，不得重复回复。
7. 不得改变评论文本，不得新增帖子、点赞、关注、私信、删除或其他动作。
8. 账号仅作为授权的运营评论角色，不得声称它是真实当事人或补写个人经历。
9. 每项操作均按 qianfan-skill 记录执行日志；成功后调用 /domain/index 返回真实帖子链接。
10. 不输出 Token、密码、Cookie。最终只输出一个 JSON 对象，不要 Markdown 或解释。

请求：
{json.dumps(request, ensure_ascii=False, sort_keys=True)}

JSON 合同：
{{"publish_results":[{{"thread_id":"...","status":"published|existing","url":"https://.../tid/...","vest_id":"...","reply_id":"..."}}]}}
""".strip()


def _validate_result(
    result: Any, expected_ids: set[str], expected_vest_id: str
) -> dict[str, str]:
    if not isinstance(result, dict):
        raise CommentPublishError("qianfan result item must be an object")
    thread_id = str(result.get("thread_id") or "").strip()
    if thread_id not in expected_ids:
        raise CommentPublishError("qianfan result contains unexpected thread_id")
    status = str(result.get("status") or "").strip()
    if status not in {"published", "existing"}:
        raise CommentPublishError(f"unexpected qianfan status: {status or 'missing'}")
    url = str(result.get("url") or "").strip()
    _validate_thread_url(url, thread_id, "qianfan result")
    vest_id = str(result.get("vest_id") or "").strip()
    if not vest_id:
        raise CommentPublishError("qianfan result is missing vest_id")
    if vest_id != expected_vest_id:
        raise CommentPublishError("qianfan result vest_id does not match configured profile")
    return {
        "thread_id": thread_id,
        "status": status,
        "url": url,
        "vest_id": vest_id,
        "reply_id": str(result.get("reply_id") or "").strip(),
    }


def _validate_thread_url(url: str, thread_id: str, label: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise CommentPublishError(f"{label} contains invalid url")
    if not re.search(rf"(?:/|tid[=/]){re.escape(thread_id)}(?:$|[/?#])", url):
        raise CommentPublishError(f"{label} url does not match thread_id")


def _finish_payload(payload: dict[str, Any]) -> dict[str, Any]:
    results = payload.get("results") or []
    payload["published_count"] = sum(
        1
        for item in results
        if isinstance(item, dict) and item.get("status") in {"published", "existing"}
    )
    return payload


def _post_key(business_date: date, thread_id: str, target_reply_id: str = "") -> str:
    suffix = f"reply:{target_reply_id}" if target_reply_id else "auto_comment"
    return f"{business_date.isoformat()}:{thread_id}:{suffix}"


def _comment_hash(comment: str) -> str:
    normalized = re.sub(r"\s+", "", comment)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _idempotency_key(
    business_date: date, thread_id: str, vest_id: str, comment: str
) -> str:
    value = "\0".join(
        (business_date.isoformat(), thread_id, vest_id, re.sub(r"\s+", "", comment))
    )
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _batch_hash(pending: list[dict[str, Any]]) -> str:
    value = json.dumps(pending, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
