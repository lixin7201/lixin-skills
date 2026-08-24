from __future__ import annotations

from datetime import date, datetime, timedelta
import html
import json
from pathlib import Path
import re
import socket
from typing import Any, Protocol
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import build_opener, ProxyHandler, Request
from zoneinfo import ZoneInfo

from .comment_selector import (
    HIGH_RISK_PATTERNS,
    LOCAL_SPECIFICITY_PATTERN,
    PROMOTION_PATTERN,
    assess_reply_substance,
)


SHANGHAI = ZoneInfo("Asia/Shanghai")


class QianfanError(RuntimeError):
    pass


class JsonTransport(Protocol):
    def request_json(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, object] | None = None,
        json_body: dict[str, object] | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]: ...


class UrlLibTransport:
    def __init__(self) -> None:
        self.opener = build_opener(ProxyHandler({}))

    def request_json(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, object] | None = None,
        json_body: dict[str, object] | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        if params:
            url = f"{url}?{urlencode(params)}"
        body = None
        if json_body is not None:
            body = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code == 401:
                raise QianfanError("qianfan authentication failed: HTTP 401") from error
            raise QianfanError(f"qianfan HTTP error: {error.code}") from error
        except (URLError, TimeoutError, socket.timeout, json.JSONDecodeError) as error:
            raise QianfanError(f"qianfan request failed: {type(error).__name__}") from error
        if not isinstance(payload, dict):
            raise QianfanError("qianfan response root must be an object")
        return payload


class QianfanClient:
    def __init__(
        self,
        *,
        domain: str,
        token: str,
        transport: JsonTransport | None = None,
    ) -> None:
        parsed = urlparse(domain)
        if parsed.scheme != "https" or not parsed.netloc:
            raise QianfanError("qianfan domain must be an https URL")
        if not token.strip():
            raise QianfanError("qianfan token is missing")
        self.domain = domain.rstrip("/")
        self.token = token.strip()
        self.transport = transport or UrlLibTransport()
        self._reply_rows_cache: dict[str, list[dict[str, Any]]] = {}

    @classmethod
    def from_config(
        cls,
        path: str | Path = "~/.qianfan-admin/config.json",
        *,
        transport: JsonTransport | None = None,
    ) -> "QianfanClient":
        config_path = Path(path).expanduser()
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise QianfanError(f"could not read qianfan config: {config_path}") from error
        if not isinstance(payload, dict):
            raise QianfanError("qianfan config root must be an object")
        return cls(
            domain=str(payload.get("domain") or ""),
            token=str(payload.get("token") or ""),
            transport=transport,
        )

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def fetch_approved_posts(
        self,
        *,
        now: datetime,
        lookback_hours: int,
        max_items: int,
    ) -> list[dict[str, Any]]:
        return self._fetch_approved_post_page(
            now=now,
            lookback_hours=lookback_hours,
            max_items=max_items,
            page=1,
            detail_limit=20,
            exclude_thread_ids=set(),
        )["posts"]

    def preflight_publish_targets(
        self, plans: list[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        if not 1 <= len(plans) <= 3:
            raise QianfanError("qianfan publish preflight accepts 1-3 items")
        vest_status: dict[str, dict[str, Any]] = {}
        for name in {str(plan.get("vest_name") or "").strip() for plan in plans}:
            data = self._request_value(
                "GET",
                "/helper/admin/search-vest-option",
                params={"name": name, "type": 1},
            )
            rows = data.get("list") if isinstance(data, dict) else None
            matches = [
                row
                for row in (rows if isinstance(rows, list) else [])
                if isinstance(row, dict)
                and self._normalized_name(row.get("name")) == self._normalized_name(name)
            ]
            enabled = [
                row
                for row in matches
                if int(row.get("enable") or 0) == 1
                and not str(row.get("desc") or "").strip()
                and str(row.get("id") or "").strip()
            ]
            self._log_query(
                result=len(matches) == 1 and len(enabled) == 1,
                summary=f"精确马甲匹配{len(matches)}，唯一启用匹配{len(enabled)}",
                params={"name": name, "type": 1},
                title="批量发帖马甲只读预检",
                description="实时精确核验固定马甲名称和启用状态",
            )
            vest_status[name] = {
                "vest_name": name,
                "vest_unique": len(matches) == 1,
                "vest_enabled": len(enabled) == 1,
                "vest_id_present": len(enabled) == 1,
            }

        forum_data = self._request_value("GET", "/bbs/forum/forum-list")
        forums = self._forum_nodes(forum_data)
        self._log_query(
            result=bool(forums),
            summary=f"读取合法板块{len(forums)}个",
            params={},
            title="批量发帖板块只读预检",
            description="实时读取发帖板块树",
        )
        output: dict[str, dict[str, Any]] = {}
        init_cache: dict[str, dict[str, Any]] = {}
        for plan in plans:
            content_id = str(plan.get("content_id") or "")
            vest_name = str(plan.get("vest_name") or "").strip()
            forum_matches = self._select_forum_matches(plan, forums)
            forum = forum_matches[0] if len(forum_matches) == 1 else {}
            fid = str(forum.get("fid") or "")
            init = init_cache.get(fid)
            if fid and init is None:
                value = self._request_value(
                    "GET", "/review/vest-publish/init", params={"fid": fid}
                )
                init = value if isinstance(value, dict) else {}
                init_cache[fid] = init
                self._log_query(
                    result=bool(init.get("forum_name")),
                    summary=f"初始化板块{str(init.get('forum_name') or '')[:80]}",
                    params={"forum_name": str(forum.get("fname") or "")},
                    title="批量发帖分类只读预检",
                    description="实时核验板块和必填主题分类",
                )
            forum_type = init.get("forum_type") if isinstance(init, dict) and isinstance(init.get("forum_type"), dict) else {}
            required = int(forum_type.get("required") or 0) == 1
            types = forum_type.get("types") if isinstance(forum_type.get("types"), list) else []
            selected_type = self._select_type(plan, types) if required else None
            output[content_id] = {
                **vest_status.get(
                    vest_name,
                    {
                        "vest_name": vest_name,
                        "vest_unique": False,
                        "vest_enabled": False,
                        "vest_id_present": False,
                    },
                ),
                "forum_name": str(forum.get("fname") or ""),
                "forum_unique": len(forum_matches) == 1,
                "forum_id_present": bool(fid),
                "type_required": required,
                "type_name": str((selected_type or {}).get("typename") or "无"),
                "type_id_present": bool(str((selected_type or {}).get("typeid") or "")),
            }
        return output

    def resolve_enabled_vest_ids(self, vest_names: set[str]) -> set[str]:
        """Resolve operator IDs for internal exclusion; callers must not persist them."""
        resolved: set[str] = set()
        for name in sorted(vest_names):
            data = self._request_value(
                "GET", "/helper/admin/search-vest-option", params={"name": name, "type": 1}
            )
            rows = data.get("list") if isinstance(data, dict) else None
            enabled = [
                row
                for row in (rows if isinstance(rows, list) else [])
                if isinstance(row, dict)
                and self._normalized_name(row.get("name")) == self._normalized_name(name)
                and int(row.get("enable") or 0) == 1
                and not str(row.get("desc") or "").strip()
                and str(row.get("id") or "").strip()
            ]
            if len(enabled) != 1:
                raise QianfanError(f"operator vest is not uniquely enabled: {name}")
            resolved.add(str(enabled[0]["id"]))
        if len(resolved) != len(vest_names):
            raise QianfanError("operator vest IDs are not unique")
        return resolved

    def fetch_published_thread_metadata(
        self, thread_ids: set[str]
    ) -> dict[str, dict[str, Any]]:
        if not thread_ids or len(thread_ids) > 3:
            raise QianfanError("qianfan publish verification accepts 1-3 thread IDs")
        today = datetime.now(SHANGHAI).date().isoformat()
        found: dict[str, dict[str, Any]] = {}
        for filter_value in (2, 0):
            data = self._request_data(
                "GET",
                "/review/thread/index",
                params={
                    "page": 1,
                    "perPage": 100,
                    "filter": filter_value,
                    "startTime": today,
                    "endTime": today,
                },
            )
            for row in data.get("list") or []:
                if not isinstance(row, dict):
                    continue
                tid = str(row.get("tid") or "")
                if tid not in thread_ids:
                    continue
                found[tid] = {
                    "tid": tid,
                    "title": str(row.get("subject") or "").strip(),
                    "vest_name": re.sub(r"(?:\[马甲\])+$", "", str(row.get("author") or "")).strip(),
                    "forum_name": str(row.get("fname") or "").strip(),
                    "published_at": self._published_time(row.get("dateline")),
                    "url": self._canonical_url(str(row.get("url") or ""), tid),
                }
        self._log_query(
            result=len(found) == len(thread_ids),
            summary=f"发布后核验{len(found)}/{len(thread_ids)}篇",
            params={"thread_count": len(thread_ids)},
            title="批量发帖发布后核验",
            description="只读核对帖子标题、马甲、板块和发布时间",
        )
        return found

    def fetch_history_posts(
        self,
        *,
        now: datetime,
        lookback_days: int,
        page: int,
        max_items: int,
        exclude_thread_ids: set[str],
    ) -> dict[str, Any]:
        return self._fetch_approved_post_page(
            now=now,
            lookback_hours=lookback_days * 24,
            max_items=max_items,
            page=page,
            detail_limit=10,
            exclude_thread_ids=exclude_thread_ids,
        )

    def _fetch_approved_post_page(
        self,
        *,
        now: datetime,
        lookback_hours: int,
        max_items: int,
        page: int,
        detail_limit: int,
        exclude_thread_ids: set[str],
    ) -> dict[str, Any]:
        if max_items < 1 or max_items > 30:
            raise QianfanError("qianfan approved-post max_items must be between 1 and 30")
        if page < 1:
            raise QianfanError("qianfan approved-post page must be positive")
        current = now.astimezone(SHANGHAI)
        start = (current - timedelta(hours=lookback_hours)).date().isoformat()
        end = current.date().isoformat()
        listed = self._request_data(
            "GET",
            "/review/thread/index",
            params={
                "page": page,
                "perPage": max_items,
                "filter": 2,
                "startTime": start,
                "endTime": end,
            },
        )
        rows = listed.get("list")
        if not isinstance(rows, list):
            raise QianfanError("qianfan thread list is missing data.list")
        candidates = [
            row
            for row in rows
            if isinstance(row, dict)
            and str(row.get("tid") or "") not in exclude_thread_ids
            and self._safe_local_summary(row)
        ][:detail_limit]
        posts: list[dict[str, Any]] = []
        detail_failures = 0
        for row in candidates:
            thread_id = str(row.get("tid") or "").strip()
            if not thread_id:
                continue
            try:
                detail = self._request_data(
                    "GET",
                    "/review/vest-publish/info",
                    params={"target_type": 0, "target_id": thread_id},
                )
            except QianfanError:
                detail_failures += 1
                continue
            if int(detail.get("allow_reply", 1) or 0) != 1:
                continue
            content = self._detail_content(detail)
            if not content:
                continue
            posts.append(
                {
                    "thread_id": thread_id,
                    "pid": str(row.get("pid") or "").strip(),
                    "fid": str(row.get("fid") or detail.get("target_fid") or "").strip(),
                    "forum": str(row.get("fname") or "").strip(),
                    "title": str(detail.get("title") or row.get("subject") or "").strip(),
                    "content": content,
                    "published_at": str(row.get("dateline") or "").strip(),
                    "url": self._canonical_url(str(row.get("url") or ""), thread_id),
                }
            )
        self._log_query(
            result=True,
            summary=f"列表{len(rows)}条，预筛{len(candidates)}条，详情成功{len(posts)}条，详情失败{detail_failures}条",
            params={
                "page": page,
                "perPage": max_items,
                "filter": 2,
                "detail_limit": detail_limit,
            },
        )
        return {
            "posts": posts,
            "page": page,
            "total_pages": max(1, int(listed.get("totalPage") or 1)),
        }

    def fetch_reply_candidates(
        self,
        *,
        thread_ids: set[str],
        vest_ids: set[str],
        already_replied_ids: set[str],
        start_date: str,
        end_date: str,
        max_items: int,
    ) -> list[dict[str, Any]]:
        if not thread_ids or max_items < 1:
            return []
        if max_items > 18:
            raise QianfanError("qianfan reply candidate max_items must not exceed 18")
        rows, pages_read = self._fetch_reply_rows(start_date, end_date)
        candidates: list[dict[str, Any]] = []
        seen_threads: set[str] = set()
        skipped = 0
        for row in rows:
            thread_id = str(row.get("tid") or "").strip()
            target_reply_id = str(row.get("pid") or "").strip()
            if (
                thread_id not in thread_ids
                or thread_id in seen_threads
                or not target_reply_id
                or target_reply_id in already_replied_ids
                or str(row.get("authorid") or "") in vest_ids
                or int(row.get("is_ai_reply") or 0) != 0
            ):
                continue
            subject = self._plain_text(row.get("subject"))
            substance = assess_reply_substance(row.get("content"))
            if not self._safe_local_summary({"subject": subject, "content": substance["text"]}) or not substance["eligible"]:
                skipped += 1
                continue
            try:
                detail = self._request_data(
                    "GET",
                    "/review/vest-publish/info",
                    params={"target_type": 0, "target_id": thread_id},
                )
            except QianfanError:
                skipped += 1
                continue
            post_content = self._detail_content(detail)
            if not post_content:
                skipped += 1
                continue
            candidates.append(
                {
                    "thread_id": thread_id,
                    "target_reply_id": target_reply_id,
                    "pid": str(row.get("pid") or ""),
                    "fid": str(row.get("fid") or ""),
                    "forum": self._plain_text(row.get("fname")),
                    "title": self._plain_text(detail.get("title")) or subject,
                    "content": post_content,
                    "target_comment": substance["text"],
                    "published_at": str(row.get("dateline") or ""),
                    "url": self._canonical_url(str(row.get("url") or ""), thread_id),
                    "facts": [
                        {"id": "F1", "text": subject},
                        {"id": "C1", "text": substance["text"]},
                    ],
                }
            )
            seen_threads.add(thread_id)
            if len(candidates) >= max_items:
                break
        self._log_query(
            result=True,
            summary=f"巡逻{pages_read}页网页评论，合格{len(candidates)}条，水评或风险跳过{skipped}条",
            params={
                "thread_count": len(thread_ids),
                "start_date": start_date,
                "end_date": end_date,
                "pages_read": pages_read,
                "max_items": max_items,
            },
        )
        return candidates

    def publish_replies(
        self,
        *,
        vest_name: str,
        vest_id: str,
        business_date: date,
        pending: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not 1 <= len(pending) <= 5:
            raise QianfanError("qianfan direct publish batch must contain 1-5 replies")
        if not vest_name.strip() or not vest_id.strip():
            raise QianfanError("qianfan direct publish requires fixed vest name and id")
        cache_key = business_date.isoformat()
        existing_rows = self._reply_rows_cache.get(cache_key)
        if existing_rows is None:
            existing_rows, _pages = self._fetch_reply_rows(cache_key, cache_key)
            self._reply_rows_cache[cache_key] = existing_rows
        results: list[dict[str, str]] = []
        for item in pending:
            thread_id = str(item.get("thread_id") or "").strip()
            fid = str(item.get("fid") or "").strip()
            title = str(item.get("title") or "").strip()
            comment = str(item.get("comment") or "").strip()
            target_reply_id = str(item.get("target_reply_id") or "0").strip() or "0"
            if not all((thread_id, fid, title, comment)):
                raise QianfanError("qianfan direct publish request is incomplete")
            detail = self._request_data(
                "GET",
                "/review/vest-publish/info",
                params={"target_type": 0, "target_id": thread_id},
            )
            if (
                str(detail.get("target_id") or "") != thread_id
                or str(detail.get("target_fid") or "") != fid
                or str(detail.get("title") or "").strip() != title
                or int(detail.get("allow_reply", 0) or 0) != 1
            ):
                raise QianfanError(f"qianfan target changed before reply: {thread_id}")
            existing_id = self._existing_reply_id(
                existing_rows, thread_id, vest_id, comment
            )
            status = "existing"
            reply_id = existing_id
            if not reply_id:
                published = self._request_data(
                    "POST",
                    "/review/vest-reply/add",
                    json_body={
                        "type": 1,
                        "sub_type": 1,
                        "target_content": title,
                        "fid": fid,
                        "title": title,
                        "uid": vest_id,
                        "reply_id": target_reply_id,
                        "id": thread_id,
                        "content": f"<p>{html.escape(comment)}</p>",
                        "attach_urls": [],
                        "minutes": "0",
                        "vest_id": vest_id,
                        "anonymous": 0,
                    },
                )
                reply_id = str(
                    published.get("pid")
                    or published.get("reply_id")
                    or published.get("id")
                    or ""
                ).strip()
                status = "published"
                if not reply_id:
                    fresh_rows, _pages = self._fetch_reply_rows(
                        cache_key, cache_key
                    )
                    self._reply_rows_cache[cache_key] = fresh_rows
                    existing_rows = fresh_rows
                    reply_id = self._existing_reply_id(
                        fresh_rows, thread_id, vest_id, comment
                    )
                if reply_id:
                    existing_rows.append(
                        {
                            "tid": thread_id,
                            "pid": reply_id,
                            "authorid": vest_id,
                            "content": comment,
                        }
                    )
            results.append(
                {
                    "thread_id": thread_id,
                    "status": status,
                    "url": str(item.get("url") or ""),
                    "vest_id": vest_id,
                    "reply_id": reply_id,
                }
            )
            self._log_query(
                result=True,
                summary=f"固定马甲{vest_name}回复帖子{thread_id}成功",
                params={
                    "thread_id": thread_id,
                    "vest_id": vest_id,
                    "target_reply_id": target_reply_id,
                },
                title="自动评论马甲回复",
                description="使用固定马甲ID发布一条已通过安全门的评论",
                action_type="马甲回复",
            )
        return {"publish_results": results}

    def collect_reply_metrics(
        self,
        *,
        thread_ids: set[str],
        vest_ids: set[str],
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        if not thread_ids:
            return []
        rows, pages_read = self._fetch_reply_rows(start_date, end_date)
        metrics = []
        for thread_id in sorted(thread_ids):
            matched = [
                item for item in rows if str(item.get("tid") or "") == thread_id
            ]
            non_vest = [
                item
                for item in matched
                if str(item.get("authorid") or "") not in vest_ids
            ]
            metrics.append(
                {
                    "thread_id": thread_id,
                    "total_reply_count": len(matched),
                    "non_vest_reply_count": len(non_vest),
                    "non_vest_unique_users": len(
                        {
                            str(item.get("authorid") or "")
                            for item in non_vest
                            if str(item.get("authorid") or "")
                        }
                    ),
                }
            )
        self._log_query(
            result=True,
            summary=f"回收{len(thread_ids)}个帖子的24小时聚合互动指标",
            params={
                "thread_count": len(thread_ids),
                "start_date": start_date,
                "end_date": end_date,
                "pages_read": pages_read,
            },
        )
        return metrics

    def _fetch_reply_rows(
        self, start_date: str, end_date: str
    ) -> tuple[list[dict[str, Any]], int]:
        rows: list[dict[str, Any]] = []
        pages_read = 0
        for page in range(1, 6):
            data = self._request_data(
                "GET",
                "/review/thread/reply",
                params={
                    "page": page,
                    "perPage": 100,
                    "filter": 2,
                    "startTime": start_date,
                    "endTime": end_date,
                },
            )
            page_rows = data.get("list")
            if not isinstance(page_rows, list):
                raise QianfanError("qianfan reply list is missing data.list")
            rows.extend(item for item in page_rows if isinstance(item, dict))
            pages_read = page
            if page >= int(data.get("totalPage") or 1):
                break
        return rows, pages_read

    def _existing_reply_id(
        self,
        rows: list[dict[str, Any]],
        thread_id: str,
        vest_id: str,
        comment: str,
    ) -> str:
        normalized = re.sub(r"\s+", "", self._plain_text(comment))
        for row in rows:
            if (
                str(row.get("tid") or "") == thread_id
                and str(row.get("authorid") or "") == vest_id
                and re.sub(r"\s+", "", self._plain_text(row.get("content"))) == normalized
            ):
                return str(row.get("pid") or "").strip()
        return ""

    def _request_data(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, object] | None = None,
        json_body: dict[str, object] | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        payload = self.transport.request_json(
            method,
            f"{self.domain}{path}",
            headers=self.headers,
            params=params,
            json_body=json_body,
            timeout=timeout,
        )
        if not (payload.get("status") is True or payload.get("code") == 0):
            message = str(payload.get("msg") or "qianfan operation failed")
            raise QianfanError(message[:200])
        data = payload.get("data")
        return data if isinstance(data, dict) else payload

    def _request_value(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, object] | None = None,
    ) -> Any:
        payload = self.transport.request_json(
            method,
            f"{self.domain}{path}",
            headers=self.headers,
            params=params,
            timeout=30,
        )
        if not (payload.get("status") is True or payload.get("code") == 0):
            raise QianfanError(str(payload.get("msg") or "qianfan operation failed")[:200])
        return payload.get("data", payload)

    def _forum_nodes(self, value: Any) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []

        def visit(node: Any) -> None:
            if isinstance(node, dict):
                if str(node.get("fid") or "") and str(node.get("fname") or "").strip():
                    found.append(node)
                for child in node.values():
                    visit(child)
            elif isinstance(node, list):
                for child in node:
                    visit(child)

        visit(value)
        unique: dict[tuple[str, str], dict[str, Any]] = {}
        for row in found:
            unique[(str(row.get("fid")), str(row.get("fname")).strip())] = row
        return list(unique.values())

    def _select_forum_matches(
        self, plan: dict[str, Any], forums: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        hint = str(plan.get("forum_hint") or "").strip()
        preferences = [hint] if hint and hint != "大宜宾APP" else self._forum_preferences(plan)
        for name in preferences:
            matches = [
                row
                for row in forums
                if self._normalized_name(row.get("fname")) == self._normalized_name(name)
            ]
            if matches:
                return matches
        return []

    def _forum_preferences(self, plan: dict[str, Any]) -> list[str]:
        text = f"{plan.get('persona') or ''}\n{plan.get('title') or ''}"
        if any(word in text for word in ("周末", "文旅", "竹海", "音乐", "熊猫")):
            return ["吃喝玩乐", "旅游户外", "文旅活动", "休闲娱乐", "灌水区"]
        return ["城市更新", "大美宜宾", "宜宾资讯", "灌水区"]

    def _select_type(
        self, plan: dict[str, Any], rows: list[Any]
    ) -> dict[str, Any] | None:
        candidates = [row for row in rows if isinstance(row, dict) and str(row.get("typeid") or "")]
        text = f"{plan.get('persona') or ''}\n{plan.get('title') or ''}"
        words = (
            ("旅游", "文旅", "活动", "休闲", "话题", "社会万象")
            if any(word in text for word in ("周末", "文旅", "竹海", "音乐", "熊猫"))
            else ("城市建设", "话题", "社会万象")
        )
        for word in words:
            matched = [row for row in candidates if word in str(row.get("typename") or "")]
            if len(matched) == 1:
                return matched[0]
        return None

    def _normalized_name(self, value: Any) -> str:
        return "".join(unicodedata.normalize("NFKC", str(value or "")).split())

    def _published_time(self, value: Any) -> str:
        text = str(value or "").strip()
        if text.isdigit():
            return datetime.fromtimestamp(int(text), SHANGHAI).isoformat()
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=SHANGHAI)
        return parsed.astimezone(SHANGHAI).isoformat()

    def _safe_local_summary(self, row: dict[str, Any]) -> bool:
        text = f"{row.get('subject') or ''}\n{row.get('content') or ''}"
        if not LOCAL_SPECIFICITY_PATTERN.search(text):
            return False
        if PROMOTION_PATTERN.search(text):
            return False
        return not any(
            re.search(pattern, text, flags=re.IGNORECASE)
            for pattern in HIGH_RISK_PATTERNS
        )

    def _detail_content(self, detail: dict[str, Any]) -> str:
        items = detail.get("items_data")
        if not isinstance(items, list):
            return ""
        return "\n".join(
            str(item.get("content") or "").strip()
            for item in items
            if isinstance(item, dict) and str(item.get("content") or "").strip()
        )

    def _plain_text(self, value: Any) -> str:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(value or ""))).strip()

    def _canonical_url(self, value: str, thread_id: str) -> str:
        url = urljoin("https://dayibin.cn/", value.strip())
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return f"https://dayibin.cn/forum.php?mod=viewthread&tid={thread_id}"
        return url

    def _log_query(
        self,
        *,
        result: bool,
        summary: str,
        params: dict[str, object],
        title: str = "读取自动评论候选帖子",
        description: str = "读取已通过帖子并执行本地低风险预筛",
        action_type: str = "查询列表",
    ) -> None:
        try:
            self.transport.request_json(
                "POST",
                f"{self.domain}/system/skill-execution-log/create",
                headers=self.headers,
                json_body={
                    "title": title,
                    "description": description,
                    "skill_name": "qianfan-skill",
                    "action_type": action_type,
                    "site_domain": urlparse(self.domain).netloc,
                    "execution_result": 1 if result else 0,
                    "execution_platform": "OpenClaw command cron",
                    "model": "none",
                    "output_summary": summary[:500],
                    "duration_ms": 0,
                    "input_params": params,
                },
                timeout=10,
            )
        except Exception:
            pass
