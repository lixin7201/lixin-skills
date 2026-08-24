#!/usr/bin/env python3
"""Zero-model Yibin earthquake patrol and Dayibin publisher."""

from __future__ import annotations

import argparse
import base64
import fcntl
import html
import json
import mimetypes
import os
import re
import sqlite3
import ssl
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from wolfx_support import (
    WOLFX_MAX_EVENT_AGE_SECONDS,
    build_wolfx_push_copy,
    parse_wolfx_payload,
    wolfx_location_fallback,
)


CENC_LOCATION_PREFIX = "四川宜宾市"
CENC_CATALOG_URL = (
    "https://www.cenc.ac.cn/prodlaunch-web-backend/open/data/catalogsPage"
)
EARTHQUAKE_CN_URL = "https://data.earthquake.cn/index.html"
QINIU_UPLOAD_URL = "https://up.qiniup.com/"
PUBLISH_VEST_ID = os.environ.get("EARTHQUAKE_PUBLISH_VEST_ID", "")
PUBLISH_VEST_NAME = os.environ.get("EARTHQUAKE_PUBLISH_VEST_NAME", "")
PUBLISH_FORUM_ID = int(os.environ.get("EARTHQUAKE_PUBLISH_FORUM_ID", "0"))
PUBLISH_FORUM_NAME = os.environ.get("EARTHQUAKE_PUBLISH_FORUM_NAME", "")
PUSH_ENABLED = True
REPUSH_MAGNITUDE_DELTA = 1.0
SAFETY_REMINDER = (
    "如遇明显震感，请保持冷静：室内就近伏低、遮挡、抓牢，远离玻璃和悬挂物；"
    "室外到开阔处，避开高楼、电线杆和广告牌。震动停止后再有序撤离。"
)


class PublishOutcomeUnknown(RuntimeError):
    """The publish request may have reached the server, so it must not be retried."""


@dataclass(frozen=True)
class Event:
    catalog_id: str
    uni_event_id: str
    occurred_at: datetime
    location: str
    longitude: float
    latitude: float
    depth_km: Optional[float]
    magnitude: float
    preliminary: bool = False
    source: str = "cenc"
    precise_location: Optional[str] = None

    @property
    def key(self) -> str:
        return self.uni_event_id or self.catalog_id

    @property
    def fingerprint(self) -> str:
        return "|".join(
            [
                self.occurred_at.strftime("%Y-%m-%d %H:%M:%S"),
                self.location,
                f"{self.latitude:.2f}",
                f"{self.longitude:.2f}",
                f"{self.magnitude:.1f}",
                "preliminary" if self.preliminary else "formal",
            ]
        )

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "Event":
        required = (
            "id",
            "oriTime",
            "locName",
            "epiLon",
            "epiLat",
            "magnitude",
        )
        if not record.get("isPreliminary"):
            required += ("focDepth",)
        missing = [name for name in required if record.get(name) is None]
        if missing:
            raise ValueError("CENC event missing fields: " + ", ".join(missing))

        location = str(record["locName"]).strip()
        if not location or len(location) > 100:
            raise ValueError("invalid CENC location")

        occurred_at = datetime.strptime(
            str(record["oriTime"]), "%Y-%m-%d %H:%M:%S"
        )
        catalog_id = str(record["id"])
        uni_event_id = str(record.get("uniEventId") or catalog_id)
        if not re.fullmatch(r"[A-Za-z0-9_-]{4,64}", uni_event_id):
            raise ValueError("invalid CENC event id")

        event = cls(
            catalog_id=catalog_id,
            uni_event_id=uni_event_id,
            occurred_at=occurred_at,
            location=location,
            longitude=float(record["epiLon"]),
            latitude=float(record["epiLat"]),
            depth_km=(
                float(record["focDepth"])
                if record.get("focDepth") is not None
                else None
            ),
            magnitude=float(record["magnitude"]),
            preliminary=bool(record.get("isPreliminary")),
            source=str(record.get("_source") or "cenc"),
            precise_location=(
                str(record.get("preciseLocation") or "").strip() or None
            ),
        )
        if not (-180 <= event.longitude <= 180 and -90 <= event.latitude <= 90):
            raise ValueError("invalid CENC coordinates")
        if event.depth_km is not None and not (0 <= event.depth_km <= 800):
            raise ValueError("invalid CENC depth")
        if not (0 <= event.magnitude <= 10):
            raise ValueError("invalid CENC depth or magnitude")
        return event


def is_yibin(event: Event) -> bool:
    return event.location.startswith(CENC_LOCATION_PREFIX)


def _short_location(event: Event) -> str:
    suffix = event.location[len(CENC_LOCATION_PREFIX) :].strip()
    return suffix or "境内"


def _number(value: float, decimals: int = 1) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.{decimals}f}"


def format_title(event: Event) -> str:
    qualifier = "级左右地震" if event.preliminary else "级地震"
    return (
        f"{event.occurred_at:%H}点{event.occurred_at:%M}分！"
        f"宜宾{_short_location(event)}发生{event.magnitude:.1f}{qualifier}！"
    )


def format_body(event: Event) -> str:
    timestamp = event.occurred_at
    if event.source.startswith("wolfx_"):
        prefix = "地震预警系统初步测算："
    else:
        prefix = (
            "中国地震台网自动测定："
            if event.preliminary
            else "中国地震台网正式测定："
        )
    magnitude = (
        f"发生{event.magnitude:.1f}级左右地震"
        if event.preliminary
        else f"发生{event.magnitude:.1f}级地震"
    )
    depth = (
        f"，震源深度{_number(event.depth_km)}千米"
        if event.depth_km is not None
        else ""
    )
    if event.source.startswith("wolfx_"):
        ending = "，当前参数可能调整，最终以中国地震台网正式测定为准。"
    else:
        ending = "，最终结果以正式速报为准。" if event.preliminary else "。"
    return (
        prefix
        +
        f"{timestamp.month}月{timestamp.day}日{timestamp.hour}时{timestamp:%M}分"
        f"在{event.location}（北纬{event.latitude:.2f}度，"
        f"东经{event.longitude:.2f}度）{magnitude}{depth}{ending}"
    )


def build_body_html(event: Event, image_url: str) -> str:
    parsed = urlparse(image_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("image URL must use https")
    body = html.escape(format_body(event))
    image = html.escape(image_url, quote=True)
    if event.source.startswith("wolfx_"):
        source = "Wolfx 地震预警数据"
    elif event.source == "weibo":
        source = "中国地震台网速报"
    else:
        source = "中国地震台网中心"
    return (
        f"{body}<br />"
        f'<div style="text-align: center;"><img src="{image}" /></div>'
        f"<br /><br />安全提醒：{html.escape(SAFETY_REMINDER)}"
        f"<br /><br />来源：{source}<br />"
    )


def build_push_copy(event: Event) -> Tuple[str, str]:
    copy_event = (
        event
        if event.precise_location
        else replace(event, precise_location=event.location)
    )
    return build_wolfx_push_copy(copy_event)


def build_push_title(event: Event) -> str:
    return build_push_copy(event)[0]


def prepare_wolfx_location(event: Event) -> Event:
    """Use Wolfx's own Yibin name; Baidu is only used for the map image."""
    precise_location = wolfx_location_fallback(event.location)
    prepared = replace(
        event,
        location=precise_location,
        precise_location=precise_location,
    )
    build_wolfx_push_copy(prepared)
    return prepared


def build_push_content(event: Event) -> str:
    return build_push_copy(event)[1]


def redact_secrets(text: str) -> str:
    patterns = [
        (r"(?i)(password\s*[=:]\s*)([^\s,}\"]+|\"[^\"]*\")", r"\1[REDACTED]"),
        (r"(?i)(token\s*[=:]\s*)([^\s,}]+)", r"\1[REDACTED]"),
        (r"(?i)(authorization\s*:\s*bearer\s+)[^\s,}]+", r"\1[REDACTED]"),
    ]
    result = str(text)
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)
    return result


class HttpTransport:
    def __init__(self, timeout: int = 20):
        self.timeout = int(timeout)
        self.ssl_context = ssl.create_default_context()

    def request_json(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        if params:
            query = urlencode(params)
            url = f"{url}{'&' if '?' in url else '?'}{query}"
        request_headers = {
            "Accept": "application/json",
            "User-Agent": "DayibinEarthquakePatrol/1.0",
        }
        request_headers.update(headers or {})
        body = None
        if json_body is not None:
            body = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        elif method.upper() == "POST":
            body = b""

        raw = self._open(
            Request(url, data=body, headers=request_headers, method=method.upper()),
            timeout=timeout,
        )
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("external service returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("external service returned non-object JSON")
        return parsed

    def get_text(
        self,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> Tuple[int, str]:
        request_headers = {
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "DayibinEarthquakePatrol/1.0",
        }
        request_headers.update(headers or {})
        raw = self._open(
            Request(url, headers=request_headers, method="GET"), timeout=timeout
        )
        return 200, raw.decode("utf-8", errors="replace")

    def post_multipart(
        self,
        url: str,
        *,
        fields: Dict[str, str],
        file_path: Path,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        file_path = Path(file_path)
        if not file_path.is_file() or file_path.stat().st_size > 5 * 1024 * 1024:
            raise ValueError("upload image must exist and be at most 5MB")
        boundary = "----DayibinPatrol" + uuid.uuid4().hex
        chunks: List[bytes] = []
        for name, value in fields.items():
            chunks.extend(
                [
                    f"--{boundary}\r\n".encode(),
                    f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                    str(value).encode("utf-8"),
                    b"\r\n",
                ]
            )
        mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    'Content-Disposition: form-data; name="file"; '
                    f'filename="{file_path.name}"\r\n'
                ).encode(),
                f"Content-Type: {mime}\r\n\r\n".encode(),
                file_path.read_bytes(),
                b"\r\n",
                f"--{boundary}--\r\n".encode(),
            ]
        )
        request = Request(
            url,
            data=b"".join(chunks),
            headers={
                "Accept": "application/json",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": "DayibinEarthquakePatrol/1.0",
            },
            method="POST",
        )
        raw = self._open(request, timeout=timeout)
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("upload service returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("upload service returned non-object JSON")
        return parsed

    def _open(self, request: Request, timeout: Optional[int] = None) -> bytes:
        try:
            with urlopen(
                request,
                timeout=timeout or self.timeout,
                context=self.ssl_context,
            ) as response:
                return response.read(8 * 1024 * 1024)
        except HTTPError as exc:
            detail = exc.read(512).decode("utf-8", errors="replace")
            raise RuntimeError(
                f"HTTP {exc.code}: {redact_secrets(detail)}"
            ) from exc
        except (TimeoutError, URLError) as exc:
            if isinstance(exc, TimeoutError) or "timed out" in str(exc).lower():
                raise TimeoutError("external request timed out") from exc
            raise RuntimeError(f"external request failed: {redact_secrets(str(exc))}") from exc


def parse_weibo_post(post: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    text = str(post.get("text_raw") or "")
    if "中国地震台网" not in text or "测定" not in text:
        return None
    pattern = re.compile(
        r"(?P<mode>自动|正式)测定：(?P<month>\d{2})月(?P<day>\d{2})日"
        r"(?P<hour>\d{2})时(?P<minute>\d{2})分在"
        r"(?P<location>四川宜宾市[^（(]+)"
        r"[（(]北纬(?P<lat>\d+(?:\.\d+)?)度，东经(?P<lon>\d+(?:\.\d+)?)度[）)]"
        r"发生(?P<mag>\d+(?:\.\d+)?)级(?:左右)?地震"
        r"(?:，震源深度(?P<depth>\d+(?:\.\d+)?)千米)?"
    )
    match = pattern.search(text)
    if not match:
        return None
    year_match = re.search(r"\b(20\d{2})\b", str(post.get("created_at") or ""))
    year = int(year_match.group(1)) if year_match else datetime.now().year
    occurred_at = datetime(
        year,
        int(match.group("month")),
        int(match.group("day")),
        int(match.group("hour")),
        int(match.group("minute")),
    )
    post_id = str(post.get("idstr") or "")
    if not post_id.isdigit():
        return None
    location = match.group("location").strip()
    if location.endswith("附近"):
        location = location[:-2]
    preliminary = match.group("mode") == "自动"
    return {
        "id": occurred_at.strftime("%Y%m%d%H%M%S"),
        "uniEventId": "WB" + post_id,
        "oriTime": occurred_at.strftime("%Y-%m-%d %H:%M:%S"),
        "locName": location,
        "epiLon": float(match.group("lon")),
        "epiLat": float(match.group("lat")),
        "focDepth": (
            float(match.group("depth")) if match.group("depth") is not None else None
        ),
        "magnitude": float(match.group("mag")),
        "isPreliminary": preliminary,
        "_source": "weibo",
    }


class WeiboSource:
    def __init__(self, project_root: Path, runner: Any = subprocess.run):
        self.project_root = Path(project_root)
        self.runner = runner
        self.status: Dict[str, Any] = {"status": "not_checked"}

    def fetch_records(self) -> List[Dict[str, Any]]:
        script = self.project_root / "scripts" / "weibo-latest.js"
        profile = self.project_root / "data" / "weibo-profile"
        completed = self.runner(
            ["node", str(script), str(profile)],
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        if completed.returncode == 3:
            self.status = {"status": "login_required"}
            return []
        if completed.returncode != 0:
            raise RuntimeError(redact_secrets(completed.stderr or "Weibo read failed"))
        payload = json.loads(completed.stdout)
        if payload.get("status") != "ok" or payload.get("uid") != "1904228041":
            raise RuntimeError("unexpected Weibo source response")
        records = [parse_weibo_post(post) for post in payload.get("posts", [])]
        filtered = [record for record in records if record is not None]
        self.status = {"status": "ok", "yibin_posts": len(filtered)}
        return filtered


class SourcesClient:
    def __init__(self, transport: HttpTransport, weibo_source: Optional[WeiboSource] = None):
        self.transport = transport
        self.weibo_source = weibo_source
        self.cenc_catalog_health: Optional[Dict[str, Any]] = None

    def _fetch_cenc_catalog(self) -> List[Dict[str, Any]]:
        payload = self.transport.request_json("GET", CENC_CATALOG_URL)
        data = payload.get("data")
        records = data.get("records") if isinstance(data, dict) else None
        if not isinstance(records, list):
            raise RuntimeError("CENC catalog response has no records")
        if len(records) > 1000 or not all(isinstance(item, dict) for item in records):
            raise RuntimeError("CENC catalog response is invalid")
        self.cenc_catalog_health = {"ok": True, "records": len(records)}
        return records

    def fetch_catalog(self) -> List[Dict[str, Any]]:
        if not self.weibo_source:
            return self._fetch_cenc_catalog()
        try:
            records = self.weibo_source.fetch_records()
        except Exception as exc:
            self.weibo_source.status = {
                "status": "error",
                "error": redact_secrets(str(exc)),
            }
            raise RuntimeError(
                "Weibo publish trigger unavailable: "
                + self.weibo_source.status["error"]
            ) from exc
        status = str(self.weibo_source.status.get("status") or "unknown")
        if status != "ok":
            raise RuntimeError(f"Weibo publish trigger unavailable: {status}")
        return records

    def check_secondary(self) -> Dict[str, Any]:
        if self.cenc_catalog_health is None:
            try:
                self._fetch_cenc_catalog()
            except Exception as exc:
                self.cenc_catalog_health = {
                    "ok": False,
                    "error": redact_secrets(str(exc)),
                }
        status, body = self.transport.get_text(EARTHQUAKE_CN_URL)
        ok = status == 200 and (
            "中国地震台网" in body or "earthquake" in body.lower()
        )
        result = {
            "ok": ok,
            "status": status,
            "bytes": len(body.encode("utf-8")),
            "cenc_catalog": dict(self.cenc_catalog_health),
        }
        if self.weibo_source:
            result["weibo"] = self.weibo_source.status
        return result

    def fetch_event(self, catalog_id: str) -> Dict[str, Any]:
        if not re.fullmatch(r"\d{14}", str(catalog_id)):
            raise ValueError("invalid CENC catalog id")
        url = (
            "https://www.cenc.ac.cn/prodlaunch-web-backend/open/data/"
            f"{catalog_id}/summarize"
        )
        payload = self.transport.request_json("GET", url)
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        info = data.get("info")
        if not isinstance(info, dict):
            raise RuntimeError("CENC event response has no info")
        return info


class MapScreenshotter:
    def __init__(self, project_root: Path, runner: Any = subprocess.run):
        self.project_root = Path(project_root).resolve()
        self.runner = runner

    def capture(self, event: Event) -> Path:
        if not re.fullmatch(r"\d{14}", event.catalog_id):
            raise ValueError("invalid CENC catalog id for screenshot")
        script = self.project_root / "scripts" / "screenshot-map.js"
        if not script.is_file():
            raise RuntimeError("map screenshot helper is missing")
        output = self.project_root / "data" / "screenshots" / f"{event.catalog_id}.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        event_payload = json.dumps(
            {
                "catalogId": event.catalog_id,
                "occurredAt": event.occurred_at.strftime("%Y-%m-%d %H:%M:%S"),
                "location": event.location,
                "longitude": event.longitude,
                "latitude": event.latitude,
                "depthKm": event.depth_km,
                "magnitude": event.magnitude,
            },
            ensure_ascii=False,
        )
        completed = self.runner(
            ["node", str(script), event_payload, str(output)],
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
            timeout=55,
            check=False,
        )
        if completed.returncode != 0:
            detail = redact_secrets(completed.stderr or completed.stdout or "unknown error")
            raise RuntimeError(f"map screenshot failed: {detail[:500]}")
        _validate_png(output)
        return output


class QianfanClient:
    def __init__(self, config_path: Path, transport: HttpTransport):
        self.config_path = Path(config_path).expanduser()
        self.transport = transport
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.domain = str(config.get("domain") or "").rstrip("/")
        self.token = str(config.get("token") or "")
        parsed = urlparse(self.domain)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or not parsed.hostname.endswith(".manager.qianfanyun.com")
        ):
            raise ValueError("qianfan domain is not allowed")
        if not self.token:
            raise ValueError("qianfan token is missing")

    @property
    def headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            raise ValueError("qianfan API path must be absolute")
        return self.domain + path

    def _ok(self, payload: Dict[str, Any]) -> bool:
        if payload.get("status") is False or payload.get("success") is False:
            return False
        code = payload.get("code")
        ret = payload.get("ret")
        return (code in (None, 0, 200, "0", "200")) and (
            ret in (None, 0, "0")
        )

    def _message(self, payload: Dict[str, Any]) -> str:
        return redact_secrets(str(payload.get("msg") or payload.get("message") or "unknown error"))

    def _persist_token(self, token: str) -> None:
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        config["token"] = token
        config["token_updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        config.pop("token_expire_at", None)
        config.pop("token_expire_text", None)
        try:
            encoded = token.split(".")[1]
            encoded += "=" * (-len(encoded) % 4)
            claims = json.loads(base64.urlsafe_b64decode(encoded).decode("utf-8"))
            expires_at = int(claims.get("exp") or 0)
            if expires_at > 0:
                config["token_expire_at"] = str(expires_at)
                config["token_expire_text"] = datetime.fromtimestamp(
                    expires_at
                ).astimezone().strftime("%Y-%m-%d %H:%M:%S")
        except (IndexError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
            pass

        temporary_path = self.config_path.with_name(self.config_path.name + ".tmp")
        temporary_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.chmod(0o600)
        temporary_path.replace(self.config_path)

    def _refresh_token(self) -> None:
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        username = str(config.get("username") or "")
        password = str(config.get("password") or "")
        if not username or not password:
            raise RuntimeError("qianfan credentials are missing; token refresh is unavailable")
        payload = self.transport.request_json(
            "POST",
            self._url("/index/login"),
            json_body={"username": username, "password": password},
        )
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        token = str(data.get("token") or payload.get("token") or "")
        if not self._ok(payload) or not token:
            raise RuntimeError(f"qianfan login failed: {self._message(payload)}")
        self.token = token
        self._persist_token(token)

    def _request_with_auth_retry(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            return self.transport.request_json(
                method,
                self._url(path),
                headers=self.headers,
                **kwargs,
            )
        except RuntimeError as exc:
            message = str(exc).lower()
            if "http 401" not in message and "invalid credentials" not in message:
                raise
        self._refresh_token()
        return self.transport.request_json(
            method,
            self._url(path),
            headers=self.headers,
            **kwargs,
        )

    def _log(
        self,
        title: str,
        description: str,
        action_type: str,
        result: bool,
        summary: str,
        inputs: Dict[str, Any],
        started_at: float,
    ) -> None:
        payload = {
            "title": title,
            "description": description,
            "skill_name": "qianfan-skill",
            "action_type": action_type,
            "site_domain": self.domain,
            "execution_result": 1 if result else 0,
            "execution_platform": "OpenClaw command cron",
            "model": "none",
            "output_summary": redact_secrets(summary)[:500],
            "duration_ms": int((time.monotonic() - started_at) * 1000),
            "input_params": inputs,
        }
        self.transport.request_json(
            "POST",
            self._url("/system/skill-execution-log/create"),
            headers=self.headers,
            json_body=payload,
            timeout=10,
        )

    def assert_vest_enabled(self, vest_id: str, vest_name: str) -> None:
        started = time.monotonic()
        inputs = {"name": vest_name, "type": 1}
        try:
            payload = self._request_with_auth_retry(
                "GET",
                "/helper/admin/search-vest-option",
                params=inputs,
            )
            data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
            rows = data.get("list") if isinstance(data.get("list"), list) else []
            match = next(
                (
                    row
                    for row in rows
                    if str(row.get("id")) == str(vest_id)
                    and str(row.get("name")) == vest_name
                ),
                None,
            )
            enabled = self._ok(payload) and bool(match) and int(match.get("enable", 0)) == 1
            detail = str((match or {}).get("desc") or data.get("msg") or "马甲不可用")
            self._log(
                "核验地震巡逻发布马甲",
                f"检查 {vest_name}/{vest_id} 是否可用",
                "query",
                enabled,
                "马甲可用" if enabled else detail,
                inputs,
                started,
            )
            if not enabled:
                raise PermissionError(detail)
        except PermissionError:
            raise
        except Exception as exc:
            try:
                self._log(
                    "核验地震巡逻发布马甲",
                    f"检查 {vest_name}/{vest_id} 是否可用",
                    "query",
                    False,
                    str(exc),
                    inputs,
                    started,
                )
            except Exception:
                pass
            raise

    def resolve_forum(self, fid: int) -> Dict[str, Any]:
        started = time.monotonic()
        inputs = {"fid": int(fid)}
        payload = self.transport.request_json(
            "GET",
            self._url("/review/vest-publish/init"),
            headers=self.headers,
            params=inputs,
        )
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        forum_type = (
            data.get("forum_type") if isinstance(data.get("forum_type"), dict) else {}
        )
        required = int(forum_type.get("required") or 0)
        types = forum_type.get("types") if isinstance(forum_type.get("types"), list) else []
        if required:
            chosen = next(
                (item for item in types if str(item.get("typename")) in {"社会万象", "话题"}),
                types[0] if types else None,
            )
            sid = int(chosen.get("typeid")) if chosen else -1
        else:
            sid = 0
        valid = self._ok(payload) and bool(data.get("forum_name")) and sid >= 0
        self._log(
            "核验地震巡逻发帖版块",
            f"初始化 fid={fid} 的发帖配置",
            "query",
            valid,
            f"forum={data.get('forum_name')}, sid={sid}",
            inputs,
            started,
        )
        if not valid:
            raise RuntimeError(self._message(payload))
        return {"fid": str(fid), "sid": sid, "name": str(data["forum_name"])}

    def find_duplicate(self, event: Event, title: str) -> Optional[Dict[str, Any]]:
        date = event.occurred_at.strftime("%Y-%m-%d")
        for filter_value in (2, 0):
            started = time.monotonic()
            params = {
                "page": 1,
                "perPage": 100,
                "filter": filter_value,
                "startTime": date,
                "endTime": date,
            }
            payload = self.transport.request_json(
                "GET",
                self._url("/review/thread/index"),
                headers=self.headers,
                params=params,
            )
            data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
            rows = data.get("list") if isinstance(data.get("list"), list) else []
            valid = self._ok(payload)
            self._log(
                "查询地震巡逻重复帖子",
                f"查询 {date} filter={filter_value} 的帖子",
                "query",
                valid,
                f"返回 {len(rows)} 条",
                params,
                started,
            )
            if not valid:
                raise RuntimeError(self._message(payload))
            for row in rows:
                subject = str(row.get("subject") or "")
                content = re.sub(r"<[^>]+>", "", str(row.get("content") or ""))
                facts_match = (
                    event.location in content
                    and f"{event.magnitude:.1f}级" in content
                    and event.occurred_at.strftime("%H时%M分") in content
                )
                if subject == title or facts_match:
                    return row
        return None

    def upload_image(self, path: Path) -> str:
        sign_started = time.monotonic()
        sign = self.transport.request_json(
            "POST",
            self._url("/system/qiniu/upload-sign"),
            headers=self.headers,
        )
        sign_data = sign.get("data") if isinstance(sign.get("data"), dict) else {}
        upload_token = str(
            sign.get("token")
            or sign_data.get("upload_token")
            or sign_data.get("token")
            or ""
        )
        self._log(
            "获取地震截图上传凭证",
            "请求七牛上传凭证",
            "upload",
            bool(upload_token),
            "已获取上传凭证" if upload_token else "上传凭证为空",
            {"file_type": "image/png"},
            sign_started,
        )
        if not upload_token:
            raise RuntimeError("qiniu upload token is missing")

        upload_started = time.monotonic()
        uploaded = self.transport.post_multipart(
            QINIU_UPLOAD_URL, fields={"token": upload_token}, file_path=Path(path)
        )
        image_url = str(uploaded.get("name") or uploaded.get("url") or "")
        parsed = urlparse(image_url)
        valid = parsed.scheme == "https" and bool(parsed.netloc)
        self._log(
            "上传地震位置截图",
            "上传官方地震位置截图到七牛",
            "upload",
            valid,
            "截图上传成功" if valid else "上传响应缺少图片地址",
            {"file_type": "image/png", "file_size": Path(path).stat().st_size},
            upload_started,
        )
        if not valid:
            raise RuntimeError("qiniu upload did not return an https URL")
        return image_url

    def publish(
        self,
        event: Event,
        title: str,
        body_html: str,
        image_url: str,
        forum: Dict[str, Any],
    ) -> Dict[str, Any]:
        started = time.monotonic()
        request_body = {
            "target_type": 0,
            "publish_id": 0,
            "target_id": 0,
            "target_fid": str(forum["fid"]),
            "target_sid": int(forum["sid"]),
            "attaches": [{"url": image_url}],
            "title": title,
            "summary": "",
            "allow_reply": 1,
            "allow_like": 1,
            "music": [],
            "show_type": 0,
            "pay_read_enable": 0,
            "attach_files": [],
            "pay_read_fee": "0.01",
            "show_range": 0,
            "items_data": [
                {"content": body_html, "type": 7, "attaches": [{"url": image_url}]}
            ],
            "vest_id": PUBLISH_VEST_ID,
            "minutes": "0",
            "publish_ip": "",
            "is_share": False,
            "address": "",
            "lat": "",
            "lng": "",
            "watermark": 0,
            "mark_id": 0,
        }
        log_inputs = {
            "event_key": event.key,
            "vest_id": PUBLISH_VEST_ID,
            "target_fid": str(forum["fid"]),
            "target_sid": int(forum["sid"]),
            "title": title,
        }
        try:
            payload = self.transport.request_json(
                "POST",
                self._url("/review/vest-publish/add"),
                headers=self.headers,
                json_body=request_body,
                timeout=30,
            )
        except TimeoutError as exc:
            try:
                self._log(
                    "发布宜宾地震简报",
                    f"使用 {PUBLISH_VEST_NAME} 发布地震文字简报和位置截图",
                    "马甲发帖",
                    False,
                    "发布结果不确定，禁止盲目重试",
                    log_inputs,
                    started,
                )
            finally:
                raise PublishOutcomeUnknown(str(exc)) from exc

        success = self._ok(payload)
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        self._log(
            "发布宜宾地震简报",
            f"使用 {PUBLISH_VEST_NAME} 发布地震文字简报和位置截图",
            "马甲发帖",
            success,
            "发布成功" if success else self._message(payload),
            log_inputs,
            started,
        )
        if not success:
            raise RuntimeError(self._message(payload))
        tid = data.get("tid") or data.get("target_id") or payload.get("tid")
        if not tid:
            duplicate = self.find_duplicate(event, title)
            tid = (duplicate or {}).get("tid")
        return {
            "tid": tid,
            "id": data.get("id") or payload.get("id"),
        }

    def update_post(
        self,
        tid: str,
        event: Event,
        title: str,
        body_html: str,
        image_url: str,
        forum: Dict[str, Any],
    ) -> Dict[str, Any]:
        info_started = time.monotonic()
        params = {"target_type": 0, "target_id": int(tid)}
        info_payload = self.transport.request_json(
            "GET",
            self._url("/review/vest-publish/info"),
            headers=self.headers,
            params=params,
        )
        detail = (
            info_payload.get("data")
            if isinstance(info_payload.get("data"), dict)
            else info_payload
        )
        items = detail.get("items_data") if isinstance(detail.get("items_data"), list) else []
        valid = self._ok(info_payload) and bool(detail.get("id")) and bool(items)
        self._log(
            "读取待更新地震帖子",
            f"读取 tid={tid} 的发布记录",
            "query",
            valid,
            "已读取帖子编辑数据" if valid else "帖子编辑数据不完整",
            params,
            info_started,
        )
        if not valid:
            raise RuntimeError("qianfan post detail is incomplete")

        existing_item = items[0]
        request_body = {
            "target_type": 0,
            "publish_id": int(detail["id"]),
            "target_id": str(tid),
            "target_fid": str(forum["fid"]),
            "target_sid": int(forum["sid"]),
            "attaches": [{"url": image_url}],
            "title": title,
            "summary": "",
            "allow_reply": 1,
            "allow_like": 1,
            "music": [],
            "show_type": 0,
            "pay_read_enable": 0,
            "attach_files": [],
            "pay_read_fee": "0.01",
            "show_range": 0,
            "items_data": [
                {
                    "id": existing_item.get("id"),
                    "publish_id": int(detail["id"]),
                    "content": body_html,
                    "type": 7,
                    "attaches": [{"url": image_url}],
                }
            ],
            "vest_id": PUBLISH_VEST_ID,
            "minutes": "0",
            "is_share": False,
            "watermark": 0,
        }
        started = time.monotonic()
        inputs = {"target_id": str(tid), "event_key": event.key, "title": title}
        try:
            payload = self.transport.request_json(
                "POST",
                self._url("/review/vest-publish/add"),
                headers=self.headers,
                json_body=request_body,
                timeout=30,
            )
        except TimeoutError as exc:
            try:
                self._log(
                    "更新宜宾地震简报",
                    f"用后续测定数据更新 tid={tid}",
                    "马甲编辑",
                    False,
                    "更新结果不确定，禁止盲目重试",
                    inputs,
                    started,
                )
            finally:
                raise PublishOutcomeUnknown(str(exc)) from exc
        success = self._ok(payload)
        self._log(
            "更新宜宾地震简报",
            f"用后续测定数据更新 tid={tid}",
            "马甲编辑",
            success,
            "更新成功" if success else self._message(payload),
            inputs,
            started,
        )
        if not success:
            raise RuntimeError(self._message(payload))
        return {"tid": str(tid)}

    def _validate_push_target(self, tid: str, event: Event) -> None:
        started = time.monotonic()
        params = {"target_type": 0, "target_id": int(tid)}
        try:
            payload = self.transport.request_json(
                "GET",
                self._url("/review/vest-publish/info"),
                headers=self.headers,
                params=params,
            )
            detail = (
                payload.get("data")
                if isinstance(payload.get("data"), dict)
                else payload
            )
            items = (
                detail.get("items_data")
                if isinstance(detail.get("items_data"), list)
                else []
            )
            if not self._ok(payload) or not detail.get("id") or not items:
                raise RuntimeError("push target post detail is incomplete")

            subject = html.unescape(str(detail.get("title") or ""))
            body = html.unescape(
                re.sub(r"<[^>]+>", "", str(items[0].get("content") or ""))
            )
            combined = subject + "\n" + body
            occurred_at = (
                f"{event.occurred_at.month}月{event.occurred_at.day}日"
                f"{event.occurred_at.hour}时{event.occurred_at:%M}分"
            )
            magnitudes = [
                float(value)
                for value in re.findall(r"发生(\d+(?:\.\d+)?)级", combined)
            ]
            mismatches = []
            if occurred_at not in combined:
                mismatches.append("occurred_at")
            if event.location not in combined:
                mismatches.append("location")
            if not magnitudes or any(
                abs(value - event.magnitude) >= 0.05 for value in magnitudes
            ):
                mismatches.append("magnitude")
            if mismatches:
                raise RuntimeError(
                    "push target does not match event: " + ", ".join(mismatches)
                )
        except Exception as exc:
            try:
                self._log(
                    "校验地震 Push 目标帖子",
                    f"核对 tid={tid} 的时间、地点和震级",
                    "query",
                    False,
                    str(exc),
                    {"target_id": str(tid), "event_key": event.key},
                    started,
                )
            finally:
                raise
        self._log(
            "校验地震 Push 目标帖子",
            f"核对 tid={tid} 的时间、地点和震级",
            "query",
            True,
            "Push 目标帖子与地震事件一致",
            {"target_id": str(tid), "event_key": event.key},
            started,
        )

    def push_post(
        self, tid: str, event: Event, image_url: str
    ) -> Dict[str, Any]:
        parsed_image = urlparse(image_url)
        if parsed_image.scheme != "https" or not parsed_image.netloc:
            raise ValueError("push image URL must use https")
        self._validate_push_target(tid, event)
        check_started = time.monotonic()
        can_use_payload = self.transport.request_json(
            "GET",
            self._url("/push/can-use"),
            headers=self.headers,
        )
        data = (
            can_use_payload.get("data")
            if isinstance(can_use_payload.get("data"), dict)
            else {}
        )
        can_use = (
            self._ok(can_use_payload)
            and int(data.get("can_use") or 0) == 1
            and int(data.get("broadcast_over_limit") or 0) == 0
        )
        self._log(
            "核验地震帖子 Push 可用状态",
            "检查 Push 权限和当日额度",
            "query",
            can_use,
            "Push 可用" if can_use else "Push 不可用或已达当日上限",
            {"target_id": str(tid)},
            check_started,
        )
        if not can_use:
            raise RuntimeError("qianfan push is unavailable or over daily limit")

        body = {
            "target_value": str(tid),
            "target_type": "10",
            "title": build_push_title(event),
            "content": build_push_content(event),
            "image": image_url,
            "platform": "0",
            "cast_type": "0",
            "method": "0",
            "start_at": 0,
            "scene": "0",
            "formName": "all",
        }
        started = time.monotonic()
        try:
            payload = self.transport.request_json(
                "POST",
                self._url("/push/create"),
                headers=self.headers,
                json_body=body,
                timeout=30,
            )
        except Exception as exc:
            try:
                self._log(
                    "Push 宜宾地震帖子",
                    f"向全部平台 Push tid={tid}",
                    "APP推送",
                    False,
                    str(exc),
                    {"target_id": str(tid), "target_type": "10", "platform": "0"},
                    started,
                )
            finally:
                raise
        success = self._ok(payload)
        self._log(
            "Push 宜宾地震帖子",
            f"向全部平台 Push tid={tid}",
            "APP推送",
            success,
            "Push 创建成功" if success else self._message(payload),
            {"target_id": str(tid), "target_type": "10", "platform": "0"},
            started,
        )
        if not success:
            raise RuntimeError(self._message(payload))
        push_data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        return {"id": push_data.get("id") or payload.get("id")}


class StateStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.path))
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                event_key TEXT PRIMARY KEY,
                catalog_id TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                location TEXT NOT NULL,
                magnitude REAL NOT NULL,
                status TEXT NOT NULL,
                post_tid TEXT,
                image_url TEXT,
                precise_location TEXT,
                error TEXT,
                updated_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_events_fingerprint
                ON events(fingerprint);
            CREATE TABLE IF NOT EXISTS observed_events (
                event_key TEXT PRIMARY KEY,
                observed_at TEXT NOT NULL
            );
            """
        )
        columns = {
            str(row["name"])
            for row in self.connection.execute("PRAGMA table_info(events)")
        }
        if "image_url" not in columns:
            self.connection.execute("ALTER TABLE events ADD COLUMN image_url TEXT")
        if "precise_location" not in columns:
            self.connection.execute(
                "ALTER TABLE events ADD COLUMN precise_location TEXT"
            )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def is_initialized(self) -> bool:
        row = self.connection.execute(
            "SELECT value FROM meta WHERE key = ?", ("initialized_at",)
        ).fetchone()
        return row is not None

    def mark_initialized(self) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            ("initialized_at", datetime.now().isoformat(timespec="seconds")),
        )
        self.connection.commit()

    def has_event(self, event: Event) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM events WHERE event_key = ? OR fingerprint = ? LIMIT 1",
            (event.key, event.fingerprint),
        ).fetchone()
        return row is not None

    def should_process(self, event: Event) -> bool:
        row = self.connection.execute(
            "SELECT status FROM events WHERE event_key = ? OR fingerprint = ? LIMIT 1",
            (event.key, event.fingerprint),
        ).fetchone()
        if row is None:
            observed = self.connection.execute(
                "SELECT 1 FROM observed_events WHERE event_key = ?", (event.key,)
            ).fetchone()
            return observed is None
        return str(row["status"]) in {
            "blocked_vest",
            "forum_failed",
            "duplicate_check_failed",
            "screenshot_failed",
            "geocode_failed",
            "upload_failed",
            "publish_failed",
        }

    def mark_observed(self, event_key: str) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO observed_events(event_key, observed_at) VALUES (?, ?)",
            (event_key, datetime.now().isoformat(timespec="seconds")),
        )
        self.connection.commit()

    def record_event(
        self,
        event: Event,
        status: str,
        *,
        post_tid: Optional[str] = None,
        image_url: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        safe_error = redact_secrets(error or "")[:1000] or None
        self.connection.execute(
            """
            INSERT INTO events(
                event_key, catalog_id, fingerprint, occurred_at, location,
                magnitude, status, post_tid, image_url, precise_location,
                error, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_key) DO UPDATE SET
                status=excluded.status,
                post_tid=COALESCE(excluded.post_tid, events.post_tid),
                image_url=COALESCE(excluded.image_url, events.image_url),
                precise_location=COALESCE(
                    excluded.precise_location, events.precise_location
                ),
                error=excluded.error,
                updated_at=excluded.updated_at
            """,
            (
                event.key,
                event.catalog_id,
                event.fingerprint,
                event.occurred_at.isoformat(sep=" "),
                event.location,
                event.magnitude,
                status,
                post_tid,
                image_url,
                event.precise_location,
                safe_error,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        self.connection.commit()
        self.mark_observed(event.key)

    def event_status(self, event_key: str) -> Optional[str]:
        row = self.connection.execute(
            "SELECT status FROM events WHERE event_key = ?", (event_key,)
        ).fetchone()
        return str(row["status"]) if row else None

    def find_related_preliminary(self, event: Event) -> Optional[Dict[str, str]]:
        row = self.connection.execute(
            """
            SELECT event_key, post_tid, image_url, precise_location FROM events
            WHERE status IN ('published_preliminary', 'updated_preliminary')
              AND substr(occurred_at, 1, 16) = ?
              AND location = ?
              AND post_tid IS NOT NULL
            ORDER BY updated_at DESC LIMIT 1
            """,
            (event.occurred_at.strftime("%Y-%m-%d %H:%M"), event.location),
        ).fetchone()
        return dict(row) if row else None

    def mark_superseded(self, event_key: str) -> None:
        self.connection.execute(
            "UPDATE events SET status='superseded', updated_at=? WHERE event_key=?",
            (datetime.now().isoformat(timespec="seconds"), event_key),
        )
        self.connection.commit()

    def can_push(
        self,
        magnitude: float,
        now: Optional[float] = None,
        cooldown_seconds: int = 21600,
    ) -> bool:
        pushed_at_row = self.connection.execute(
            "SELECT value FROM meta WHERE key='last_push_at'"
        ).fetchone()
        if pushed_at_row is None:
            return True
        if (now or time.time()) - float(pushed_at_row["value"]) >= cooldown_seconds:
            return True
        magnitude_row = self.connection.execute(
            "SELECT value FROM meta WHERE key='last_push_magnitude'"
        ).fetchone()
        if magnitude_row is None:
            return False
        current_tenths = round(float(magnitude) * 10)
        previous_tenths = round(float(magnitude_row["value"]) * 10)
        required_tenths = round(REPUSH_MAGNITUDE_DELTA * 10)
        return current_tenths - previous_tenths >= required_tenths

    def record_push(
        self, tid: str, magnitude: float, now: Optional[float] = None
    ) -> None:
        pushed_at = now or time.time()
        self.connection.executemany(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            [
                ("last_push_at", str(pushed_at)),
                ("last_push_tid", str(tid)),
                ("last_push_magnitude", str(float(magnitude))),
            ],
        )
        self.connection.commit()


class PatrolService:
    def __init__(
        self,
        *,
        sources: Any,
        qianfan: Any,
        screenshotter: Any,
        store: StateStore,
        vest_id: str,
        vest_name: str,
        forum_id: int,
        push_enabled: bool = False,
        geocoder: Optional[Any] = None,
    ):
        self.sources = sources
        self.qianfan = qianfan
        self.screenshotter = screenshotter
        self.store = store
        self.vest_id = str(vest_id)
        self.vest_name = str(vest_name)
        self.forum_id = int(forum_id)
        self.push_enabled = bool(push_enabled)
        self.geocoder = geocoder

    def run_once(self) -> Dict[str, Any]:
        records = self.sources.fetch_catalog()
        try:
            secondary = self.sources.check_secondary()
        except Exception as exc:  # Secondary source is a health signal, not facts.
            secondary = {"ok": False, "error": redact_secrets(str(exc))}
        events = [Event.from_record(record) for record in records]
        events.sort(key=lambda item: item.occurred_at)

        if not self.store.is_initialized():
            for event in events:
                self.store.record_event(event, "baseline")
            self.store.mark_initialized()
            return {
                "status": "baseline_seeded",
                "seeded": len(events),
                "processed": 0,
                "secondary": secondary,
                "events": [],
            }

        results = []
        for event in events:
            if not self.store.should_process(event):
                continue
            if not is_yibin(event):
                self.store.record_event(event, "ignored_non_yibin")
                continue
            results.append(self._process_event(event))

        return {
            "status": "ok",
            "processed": len(results),
            "secondary": secondary,
            "events": results,
        }

    def _result(
        self,
        event: Event,
        status: str,
        *,
        post_tid: Optional[str] = None,
        image_url: Optional[str] = None,
        error: Optional[Exception] = None,
    ) -> Dict[str, Any]:
        message = redact_secrets(str(error)) if error else None
        self.store.record_event(
            event,
            status,
            post_tid=post_tid,
            image_url=image_url,
            error=message,
        )
        result: Dict[str, Any] = {"event_key": event.key, "status": status}
        if post_tid:
            result["post_tid"] = post_tid
        if message:
            result["error"] = message
        return result

    def _process_event(self, event: Event) -> Dict[str, Any]:
        if event.source.startswith("wolfx_") and not event.precise_location:
            try:
                event = prepare_wolfx_location(event)
            except Exception as exc:
                return self._result(event, "geocode_failed", error=exc)

        title = format_title(event)
        try:
            self.qianfan.assert_vest_enabled(self.vest_id, self.vest_name)
        except PermissionError as exc:
            return self._result(event, "blocked_vest", error=exc)
        except Exception as exc:
            return self._result(event, "blocked_vest", error=exc)

        try:
            forum = self.qianfan.resolve_forum(self.forum_id)
        except Exception as exc:
            return self._result(event, "forum_failed", error=exc)

        preliminary = (
            self.store.find_related_preliminary(event)
            if event.source == "weibo" or not event.preliminary
            else None
        )
        if preliminary is None:
            try:
                duplicate = self.qianfan.find_duplicate(event, title)
            except Exception as exc:
                return self._result(event, "duplicate_check_failed", error=exc)
            if duplicate:
                return self._result(
                    event,
                    "skipped_existing",
                    post_tid=str(duplicate.get("tid") or ""),
                )

        if preliminary is not None:
            image_url = str(preliminary.get("image_url") or "")
            parsed_image = urlparse(image_url)
            if parsed_image.scheme != "https" or not parsed_image.netloc:
                return self._result(
                    event,
                    "publish_failed",
                    error=RuntimeError("preliminary post image URL is unavailable"),
                )
            body_html = build_body_html(event, image_url)
            try:
                updated = self.qianfan.update_post(
                    preliminary["post_tid"],
                    event,
                    title,
                    body_html,
                    image_url,
                    forum,
                )
            except PublishOutcomeUnknown as exc:
                return self._result(event, "manual_review", error=exc)
            except Exception as exc:
                return self._result(event, "publish_failed", error=exc)
            self.store.mark_superseded(preliminary["event_key"])
            return self._result(
                event,
                "updated_preliminary" if event.preliminary else "updated_formal",
                post_tid=str(updated.get("tid") or preliminary["post_tid"]),
                image_url=image_url,
            )

        try:
            screenshot_path = Path(self.screenshotter.capture(event))
            _validate_png(screenshot_path)
        except Exception as exc:
            return self._result(event, "screenshot_failed", error=exc)

        try:
            image_url = self.qianfan.upload_image(screenshot_path)
        except Exception as exc:
            return self._result(event, "upload_failed", error=exc)

        body_html = build_body_html(event, image_url)
        try:
            published = self.qianfan.publish(
                event, title, body_html, image_url, forum
            )
        except PublishOutcomeUnknown as exc:
            try:
                duplicate = self.qianfan.find_duplicate(event, title)
            except Exception:
                duplicate = None
            if duplicate:
                result = self._result(
                    event,
                    "published_reconciled",
                    post_tid=str(duplicate.get("tid") or ""),
                    image_url=image_url,
                )
                return self._push_if_due(event, result, image_url)
            return self._result(event, "manual_review", error=exc)
        except Exception as exc:
            return self._result(event, "publish_failed", error=exc)

        result = self._result(
            event,
            "published_preliminary" if event.preliminary else "published",
            post_tid=str(published.get("tid") or published.get("id") or ""),
            image_url=image_url,
        )
        return self._push_if_due(event, result, image_url)

    def _push_if_due(
        self, event: Event, result: Dict[str, Any], image_url: str
    ) -> Dict[str, Any]:
        if not self.push_enabled:
            result["push_status"] = "disabled"
            return result
        tid = str(result.get("post_tid") or "")
        if not tid:
            result["push_status"] = "missing_tid"
            return result
        if not self.store.can_push(event.magnitude):
            result["push_status"] = "cooldown"
            return result
        try:
            pushed = self.qianfan.push_post(tid, event, image_url)
        except Exception as exc:
            result["push_status"] = "failed"
            result["push_error"] = redact_secrets(str(exc))
            return result
        self.store.record_push(tid, event.magnitude)
        result["push_status"] = "pushed"
        result["push_id"] = pushed.get("id")
        return result


def _validate_png(path: Path) -> None:
    if not path.is_file():
        raise ValueError("screenshot file missing")
    if path.stat().st_size < 1024:
        raise ValueError("screenshot file is too small")
    with path.open("rb") as handle:
        if handle.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError("screenshot is not a PNG")


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_STATE_PATH = PROJECT_ROOT / "data" / "state.sqlite3"
DEFAULT_CONFIG_PATH = Path.home() / ".qianfan-admin" / "config.json"


def _runtime() -> Tuple[SourcesClient, QianfanClient, MapScreenshotter]:
    transport = HttpTransport()
    return (
        SourcesClient(transport, WeiboSource(PROJECT_ROOT)),
        QianfanClient(DEFAULT_CONFIG_PATH, transport),
        MapScreenshotter(PROJECT_ROOT),
    )


def _print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _run_command() -> int:
    lock_path = PROJECT_ROOT / "data" / "patrol.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            _print_json({"status": "skipped_locked"})
            return 0

        sources, qianfan, screenshotter = _runtime()
        store = StateStore(DEFAULT_STATE_PATH)
        try:
            service = PatrolService(
                sources=sources,
                qianfan=qianfan,
                screenshotter=screenshotter,
                store=store,
                vest_id=PUBLISH_VEST_ID,
                vest_name=PUBLISH_VEST_NAME,
                forum_id=PUBLISH_FORUM_ID,
                push_enabled=PUSH_ENABLED,
            )
            result = service.run_once()
        finally:
            store.close()
        _print_json(result)
        failure_states = {
            "blocked_vest",
            "forum_failed",
            "duplicate_check_failed",
            "screenshot_failed",
            "upload_failed",
            "publish_failed",
            "manual_review",
        }
        return 2 if any(item.get("status") in failure_states for item in result.get("events", [])) else 0


def _check_command() -> int:
    sources, qianfan, screenshotter = _runtime()
    result: Dict[str, Any] = {"status": "ok", "checks": {}}
    records = sources.fetch_catalog()
    events = [Event.from_record(record) for record in records]
    yibin_events = sorted(
        (event for event in events if is_yibin(event)),
        key=lambda event: event.occurred_at,
        reverse=True,
    )
    secondary = sources.check_secondary()
    result["checks"]["cenc_catalog"] = secondary.pop("cenc_catalog")
    result["checks"]["earthquake_cn"] = secondary

    if yibin_events:
        latest = yibin_events[0]
        screenshot = screenshotter.capture(latest)
        result["checks"]["map_screenshot"] = {
            "ok": True,
            "event_key": latest.key,
            "path": str(screenshot),
            "bytes": screenshot.stat().st_size,
        }
    else:
        result["checks"]["map_screenshot"] = {"ok": False, "reason": "no Yibin event"}

    try:
        qianfan.assert_vest_enabled(PUBLISH_VEST_ID, PUBLISH_VEST_NAME)
        result["checks"]["vest"] = {
            "ok": True,
            "id": PUBLISH_VEST_ID,
            "name": PUBLISH_VEST_NAME,
        }
    except Exception as exc:
        result["checks"]["vest"] = {
            "ok": False,
            "id": PUBLISH_VEST_ID,
            "name": PUBLISH_VEST_NAME,
            "error": redact_secrets(str(exc)),
        }

    try:
        forum = qianfan.resolve_forum(PUBLISH_FORUM_ID)
        if forum["name"] != PUBLISH_FORUM_NAME:
            raise RuntimeError(
                f"forum mismatch: expected {PUBLISH_FORUM_NAME}, got {forum['name']}"
            )
        result["checks"]["forum"] = {"ok": True, **forum}
    except Exception as exc:
        result["checks"]["forum"] = {
            "ok": False,
            "error": redact_secrets(str(exc)),
        }

    failures = [
        name
        for name, check in result["checks"].items()
        if isinstance(check, dict) and check.get("ok") is False
    ]
    if failures:
        result["status"] = "blocked"
        result["failures"] = failures
    _print_json(result)
    return 2 if failures else 0


def _replay_command(catalog_id: str) -> int:
    sources, qianfan, screenshotter = _runtime()
    event = Event.from_record(sources.fetch_event(catalog_id))
    if not is_yibin(event):
        raise RuntimeError("replay event is not in Yibin")
    title = format_title(event)
    duplicate = qianfan.find_duplicate(event, title)
    screenshot = screenshotter.capture(event)
    result = {
        "status": "would_skip_existing" if duplicate else "would_publish",
        "event_key": event.key,
        "title": title,
        "duplicate_tid": str((duplicate or {}).get("tid") or "") or None,
        "screenshot": str(screenshot),
        "screenshot_bytes": screenshot.stat().st_size,
        "published": False,
    }
    _print_json(result)
    return 0 if duplicate else 3


def _weibo_check_command() -> int:
    profile = PROJECT_ROOT / "data" / "weibo-profile"
    completed = subprocess.run(
        ["node", str(PROJECT_ROOT / "scripts" / "weibo-latest.js"), str(profile)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=55,
        check=False,
    )
    if completed.stdout.strip():
        print(completed.stdout.strip())
    if completed.stderr.strip():
        print(redact_secrets(completed.stderr.strip()), file=sys.stderr)
    return completed.returncode


def _wolfx_event_command(*, publish: bool, allow_stale: bool) -> int:
    raw = sys.stdin.read(65537)
    if not raw.strip() or len(raw) > 65536:
        raise ValueError("Wolfx event input must be a JSON object under 64KB")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("Wolfx event input must be a JSON object")
    try:
        record = parse_wolfx_payload(
            payload,
            max_age_seconds=(31536000 if allow_stale else WOLFX_MAX_EVENT_AGE_SECONDS),
        )
    except ValueError as exc:
        if "stale Wolfx event" in str(exc):
            _print_json({"status": "ignored_stale", "published": False})
            return 0
        raise
    event = Event.from_record(record)
    if not is_yibin(event):
        _print_json({"status": "ignored_non_yibin", "published": False})
        return 0

    transport = HttpTransport()
    def prepare() -> Event:
        return prepare_wolfx_location(event)

    if not publish:
        try:
            prepared = prepare()
        except Exception as exc:
            _print_json(
                {
                    "status": "blocked_precise_location",
                    "event_key": event.key,
                    "error": redact_secrets(str(exc)),
                    "published": False,
                }
            )
            return 3
        screenshotter = MapScreenshotter(PROJECT_ROOT)
        screenshot = screenshotter.capture(prepared)
        push_title, push_content = build_push_copy(prepared)
        _print_json(
            {
                "status": "shadow_ready",
                "event_key": prepared.key,
                "precise_location": prepared.precise_location,
                "push_title": push_title,
                "push_content": push_content,
                "post_title": format_title(prepared),
                "post_body": format_body(prepared),
                "screenshot": str(screenshot),
                "screenshot_bytes": screenshot.stat().st_size,
                "published": False,
            }
        )
        return 0

    lock_path = PROJECT_ROOT / "data" / "patrol.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            _print_json({"status": "skipped_locked", "published": False})
            return 75

        store = StateStore(DEFAULT_STATE_PATH)
        try:
            if not store.is_initialized():
                raise RuntimeError("earthquake patrol state is not initialized")
            if not store.should_process(event):
                _print_json(
                    {
                        "status": "ignored_duplicate",
                        "event_key": event.key,
                        "published": False,
                    }
                )
                return 0
            try:
                prepared = prepare()
            except Exception as exc:
                service = PatrolService(
                    sources=None,
                    qianfan=None,
                    screenshotter=None,
                    store=store,
                    vest_id=PUBLISH_VEST_ID,
                    vest_name=PUBLISH_VEST_NAME,
                    forum_id=PUBLISH_FORUM_ID,
                    push_enabled=PUSH_ENABLED,
                )
                result = service._result(event, "geocode_failed", error=exc)
                _print_json({"status": "blocked", "event": result, "published": False})
                return 76
            qianfan = QianfanClient(DEFAULT_CONFIG_PATH, transport)
            service = PatrolService(
                sources=None,
                qianfan=qianfan,
                screenshotter=MapScreenshotter(PROJECT_ROOT),
                store=store,
                vest_id=PUBLISH_VEST_ID,
                vest_name=PUBLISH_VEST_NAME,
                forum_id=PUBLISH_FORUM_ID,
                push_enabled=PUSH_ENABLED,
            )
            result = service._process_event(prepared)
        finally:
            store.close()
    failure_states = {
        "blocked_vest",
        "forum_failed",
        "duplicate_check_failed",
        "geocode_failed",
        "screenshot_failed",
        "upload_failed",
        "publish_failed",
        "manual_review",
    }
    failed = result.get("status") in failure_states
    published = result.get("status") in {
        "published_preliminary",
        "published",
        "published_reconciled",
    }
    _print_json(
        {
            "status": "blocked" if failed else "ok",
            "event": result,
            "published": published,
        }
    )
    return 2 if failed else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("run", help="run one production patrol cycle")
    subparsers.add_parser("check", help="run live read-only prerequisites")
    replay = subparsers.add_parser("replay", help="safely replay an event without publishing")
    replay.add_argument("event_id")
    subparsers.add_parser("weibo-check", help="check the optional authenticated Weibo source")
    wolfx = subparsers.add_parser(
        "wolfx-event", help="validate one Wolfx WebSocket message from stdin"
    )
    wolfx.add_argument("--publish", action="store_true")
    wolfx.add_argument("--allow-stale", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.command == "run":
            return _run_command()
        if args.command == "check":
            return _check_command()
        if args.command == "replay":
            return _replay_command(args.event_id)
        if args.command == "weibo-check":
            return _weibo_check_command()
        if args.command == "wolfx-event":
            return _wolfx_event_command(
                publish=bool(args.publish), allow_stale=bool(args.allow_stale)
            )
    except Exception as exc:
        _print_json({"status": "error", "error": redact_secrets(str(exc))})
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
