from __future__ import annotations

from datetime import UTC, datetime, timedelta
import fcntl
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
from typing import Any, Callable, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from .safety import validate_draft
from .storage import atomic_write_json, atomic_write_text


SHANGHAI = ZoneInfo("Asia/Shanghai")
YIBIN_PREFIX = "5115"
CAP_SOURCE = "gjzwfw-cma-cap"
WEATHER_SOURCE = "weather-com-cn-alarm"
NMC_SOURCE = "nmc-sichuan-alert"
STYLE_ROOT = Path("/Users/REPLACE_ME/.openclaw/workspace/skills/app-skill")
STYLE_FILES = (
    STYLE_ROOT / "references/文稿类型/突发应急安全DNA.md",
    STYLE_ROOT / "references/小编风格/采采呀-DNA.md",
    STYLE_ROOT / "references/文章结构模板.md",
    STYLE_ROOT / "references/像不像判别器.md",
)

_SEVERITY_BY_CODE = {"01": "blue", "02": "yellow", "03": "orange", "04": "red"}
_SEVERITY_BY_CN = {"蓝色": "blue", "黄色": "yellow", "橙色": "orange", "红色": "red"}
_EVENT_BY_CODE = {
    "01": "台风", "02": "暴雨", "03": "暴雪", "04": "寒潮", "05": "大风",
    "06": "沙尘暴", "07": "高温", "08": "干旱", "09": "雷电", "10": "冰雹",
    "11": "霜冻", "12": "大雾", "13": "霾", "14": "道路结冰", "52": "雷暴大风",
    "58": "低温雨雪冰冻", "59": "强对流", "62": "强降雨", "63": "强降温",
    "65": "森林（草原）火险", "93": "雷雨大风",
}
_WARNING_RE = re.compile(
    r"(雷暴大风|雷雨大风|道路结冰|低温雨雪冰冻|森林（草原）火险|"
    r"强对流|强降雨|强降温|暴雨|暴雪|冰雹|大风|雷电|高温|寒潮|"
    r"台风|霜冻|大雾|沙尘暴|干旱|霾)(蓝色|黄色|橙色|红色)预警"
)


class WeatherShadowError(RuntimeError):
    pass


class WeatherPublishPreflightError(WeatherShadowError):
    pass


def live_source_fetchers() -> dict[str, Callable[[datetime], list[dict[str, Any]]]]:
    return {
        CAP_SOURCE: _fetch_cap,
        WEATHER_SOURCE: _fetch_weather_alarm,
        NMC_SOURCE: _fetch_nmc,
    }


def _fetch_cap(now: datetime) -> list[dict[str, Any]]:
    body = urlencode({
        "areaCode": "511500",
        "warnLevel": "RED,BLUE,YELLOW,Orange,UNKOWN",
        "warnEvent": "A",
    }).encode("ascii")
    payload = _request_text(
        "https://app.gjzwfw.gov.cn/fwmhapp/qixiang/interfaces/findWarnCapByElement.do",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return parse_cap_payload(payload, observed_at=now)


def _fetch_weather_alarm(now: datetime) -> list[dict[str, Any]]:
    payload = _request_text(
        "https://product.weather.com.cn/alarm/grepalarm_cn.php",
        headers={
            "Referer": "https://www.weather.com.cn/alarm/",
            "User-Agent": "Mozilla/5.0 weather-shadow/1.0",
        },
    )
    return parse_weather_alarm_payload(payload, observed_at=now)


def _fetch_nmc(now: datetime) -> list[dict[str, Any]]:
    query = urlencode({
        "pageNo": 1,
        "pageSize": 100,
        "province": "四川省",
        "signaltype": "",
        "signallevel": "",
    })
    payload = _request_text(
        f"https://www.nmc.cn/rest/findAlarm?{query}",
        headers={"User-Agent": "Mozilla/5.0 weather-shadow/1.0"},
    )
    return parse_nmc_payload(payload, observed_at=now)


def _request_text(
    url: str,
    *,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> str:
    request = Request(url, data=data, headers=headers or {}, method="POST" if data else "GET")
    with urlopen(request, timeout=10) as response:  # nosec: fixed official endpoints only
        body = response.read()
        charset = response.headers.get_content_charset()
    for encoding in (charset, "utf-8", "gb18030"):
        if not encoding:
            continue
        try:
            return body.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    raise WeatherShadowError(f"could not decode official weather response: {url}")


def parse_cap_payload(payload: str, *, observed_at: datetime) -> list[dict[str, Any]]:
    values = json.loads(payload)
    if not isinstance(values, list):
        raise ValueError("CAP response must be a list")
    items = []
    for value in values:
        if not isinstance(value, dict):
            continue
        identifier = str(value.get("identifier") or "").strip()
        if not identifier.startswith(YIBIN_PREFIX):
            continue
        sender = _text(value.get("sender"))
        headline = _text(value.get("headline"))
        description = _text(value.get("description"))
        event_type = _text(value.get("eventTypeCN")).removesuffix("事件")
        severity = _normalize_severity(value.get("severity"))
        if not event_type or not severity:
            parsed_type, parsed_severity = _warning_parts(headline)
            event_type = event_type or parsed_type
            severity = severity or parsed_severity
        items.append({
            "identifier": identifier,
            "source_id": CAP_SOURCE,
            "source_url": "https://app.gjzwfw.gov.cn/jmopen/webapp/html5/zhyjssxx/index.html",
            "observed_at": _iso(observed_at),
            "issuer": sender,
            "message_type": _message_type(value.get("msgType"), headline),
            "event_type": event_type,
            "severity": severity,
            "effective_at": _iso(_parse_local_datetime(value.get("effective"), identifier)),
            "expires_at": _iso(_parse_local_datetime(value.get("expires"), "")),
            "headline": headline,
            "description": description,
            "references_identifier": _text(value.get("referencesInfo")),
            "area_scope": _area_scope(sender),
            "body_complete": bool(description),
        })
    return items


def parse_weather_alarm_payload(
    payload: str, *, observed_at: datetime
) -> list[dict[str, Any]]:
    stripped = payload.strip()
    if stripped.startswith("var alarminfo="):
        stripped = stripped[len("var alarminfo=") :]
    stripped = stripped.rstrip(";\n ")
    root = json.loads(stripped)
    records = root.get("data") if isinstance(root, dict) else None
    if not isinstance(records, list):
        raise ValueError("weather alarm response has no data list")
    items = []
    for record in records:
        if not isinstance(record, list) or len(record) < 2:
            continue
        location = _text(record[0] if record else "")
        identifier = _text(record[4] if len(record) > 4 else "")
        if not identifier.startswith(YIBIN_PREFIX) and not location.startswith("四川省宜宾市"):
            continue
        link = _text(record[1])
        code_match = re.search(r"-([0-9]{4})\.html$", link)
        type_grade = code_match.group(1) if code_match else ""
        headline = _text(record[6] if len(record) > 6 else "")
        parsed_type, parsed_severity = _warning_parts(headline)
        event_type = parsed_type or _EVENT_BY_CODE.get(type_grade[:2], "")
        severity = parsed_severity or _SEVERITY_BY_CODE.get(type_grade[2:], "")
        if not identifier:
            continue
        items.append({
            "identifier": identifier,
            "source_id": WEATHER_SOURCE,
            "source_url": f"https://www.weather.com.cn/alarm/newalarmcontent.shtml?file={link}",
            "observed_at": _iso(observed_at),
            "issuer": _issuer_from_location(location),
            "message_type": _message_type("", headline),
            "event_type": event_type,
            "severity": severity,
            "effective_at": _iso(_parse_identifier_datetime(identifier)),
            "expires_at": "",
            "headline": headline,
            "description": "",
            "references_identifier": "",
            "area_scope": _area_scope(_issuer_from_location(location)),
            "body_complete": False,
        })
    return items


def parse_nmc_payload(payload: str, *, observed_at: datetime) -> list[dict[str, Any]]:
    root = json.loads(payload)
    data = root.get("data") if isinstance(root, dict) else None
    page = data.get("page") if isinstance(data, dict) else None
    records = page.get("list") if isinstance(page, dict) else None
    if not isinstance(records, list):
        raise ValueError("NMC response has no page list")
    items = []
    for record in records:
        if not isinstance(record, dict):
            continue
        identifier = _text(record.get("alertid"))
        if not identifier.startswith(YIBIN_PREFIX):
            continue
        headline = _text(record.get("title"))
        event_type, severity = _warning_parts(headline)
        relative_url = _text(record.get("url"))
        items.append({
            "identifier": identifier,
            "source_id": NMC_SOURCE,
            "source_url": f"https://www.nmc.cn{relative_url}" if relative_url.startswith("/") else relative_url,
            "observed_at": _iso(observed_at),
            "issuer": _issuer_from_title(headline),
            "message_type": _message_type("", headline),
            "event_type": event_type,
            "severity": severity,
            "effective_at": _iso(_parse_identifier_datetime(identifier)),
            "expires_at": "",
            "headline": headline,
            "description": "",
            "references_identifier": "",
            "area_scope": _area_scope(_issuer_from_title(headline)),
            "body_complete": False,
        })
    return items


def merge_observations(observations: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for observation in observations:
        identifier = _text(observation.get("identifier"))
        if identifier:
            grouped.setdefault(identifier, []).append(observation)
    merged = {}
    for identifier, values in grouped.items():
        canonical = max(
            values,
            key=lambda value: (
                bool(value.get("body_complete")),
                value.get("source_id") == CAP_SOURCE,
            ),
        )
        result = dict(canonical)
        first_seen: dict[str, str] = {}
        for value in values:
            source_id = _text(value.get("source_id"))
            observed = _text(value.get("observed_at"))
            if source_id and observed and (source_id not in first_seen or observed < first_seen[source_id]):
                first_seen[source_id] = observed
        conflicts = [
            field for field in ("event_type", "severity", "message_type")
            if len({_text(value.get(field)) for value in values if _text(value.get(field))}) > 1
        ]
        result.update({
            "source_first_seen_at": dict(sorted(first_seen.items())),
            "source_ids": sorted(first_seen),
            "first_seen_at": min(first_seen.values()) if first_seen else "",
            "has_source_conflict": bool(conflicts),
            "source_conflicts": conflicts,
        })
        merged[identifier] = result
    return merged


def run_weather_shadow(
    *,
    data_dir: Any,
    now: datetime,
    source_fetchers: dict[str, Callable[[datetime], list[dict[str, Any]]]],
    draft_runner: Callable[[str, str], dict[str, Any]] | None = None,
    publish: bool = False,
    publisher: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if publish and publisher is None:
        raise WeatherShadowError("auto publish requires a publisher")
    root = Path(data_dir)
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / "weather-shadow.lock"
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        return _run_locked(root, now, source_fetchers, draft_runner, publish, publisher)


def _run_locked(
    root: Path,
    now: datetime,
    source_fetchers: dict[str, Callable[[datetime], list[dict[str, Any]]]],
    draft_runner: Callable[[str, str], dict[str, Any]] | None,
    publish: bool,
    publisher: Callable[[dict[str, Any]], dict[str, Any]] | None,
) -> dict[str, Any]:
    ledger_path = root / "alert-ledger.jsonl"
    bootstrap = not ledger_path.exists()
    ledger = _read_ledger(ledger_path)
    policy_path = root / "auto-publish-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8")) if policy_path.exists() else {}
    auto_publish_armed = publish and (
        not policy_path.exists() or policy.get("enabled") is False
    )
    if auto_publish_armed:
        policy = {
            "enabled_at": _iso(now),
            "enabled": True,
            "vest_name": "forever21",
            "forum_name": "大美宜宾",
            "push_enabled": False,
        }
        atomic_write_json(policy_path, policy)
    elif not publish and policy_path.exists() and policy.get("enabled") is not False:
        policy.update({"enabled": False, "disabled_at": _iso(now)})
        atomic_write_json(policy_path, policy)
    observations: list[dict[str, Any]] = []
    source_errors: dict[str, str] = {}
    successful_sources = 0
    for source_id, fetcher in source_fetchers.items():
        try:
            observations.extend(fetcher(now))
            successful_sources += 1
        except Exception as error:  # source isolation is the safety boundary
            source_errors[source_id] = f"{type(error).__name__}: {error}"[:300]
    if not successful_sources:
        raise WeatherShadowError("all weather warning sources failed")

    merged = merge_observations(observations)
    held_reasons: list[str] = []
    card_paths: list[str] = []
    known_ids = set(ledger) | set(merged)
    for identifier, event in merged.items():
        previous = ledger.get(identifier)
        if previous:
            first_seen = dict(previous.get("source_first_seen_at") or {})
            for source_id, seen_at in (event.get("source_first_seen_at") or {}).items():
                if source_id not in first_seen or seen_at < first_seen[source_id]:
                    first_seen[source_id] = seen_at
            event["source_first_seen_at"] = dict(sorted(first_seen.items()))
            event["first_seen_at"] = min(first_seen.values()) if first_seen else ""
            for key in (
                "shadow_state", "hold_reason", "confirmation_card_path",
                "publish_attempted_at", "publish_error", "tid", "url",
                "vest_name", "forum_name", "type_name", "published_at",
            ):
                if key in previous:
                    event[key] = previous[key]

        reevaluate = not bootstrap and (
            previous is None or previous.get("shadow_state") == "HELD"
        )
        reason = _hold_reason(event, now, known_ids) if reevaluate else ""
        if reason:
            event["shadow_state"] = "HELD"
            event["hold_reason"] = reason
            held_reasons.append(reason)
        elif reevaluate:
            card = _confirmation_card(
                event, now, draft_runner, human_confirmation_required=not publish
            )
            path = root / "confirmation-cards" / f"{identifier}.json"
            atomic_write_json(path, card)
            card_paths.append(str(path))
            event["shadow_state"] = "CARD_READY"
            event["confirmation_card_path"] = str(path)
        else:
            event["shadow_state"] = "BASELINED" if bootstrap and not previous else str(
                previous.get("shadow_state") if previous else "OBSERVED"
            )
        event["last_seen_at"] = _iso(now)
        ledger[identifier] = event

    _write_ledger(ledger_path, ledger)
    published_results: list[dict[str, Any]] = []
    publish_unknown_count = 0
    qianfan_called = False
    if publish and not auto_publish_armed:
        enabled_at = _parse_iso(policy.get("enabled_at"))
        candidates = [
            event for event in ledger.values()
            if event.get("shadow_state") == "CARD_READY"
            and enabled_at is not None
            and (_parse_iso(event.get("first_seen_at")) or datetime.min.replace(tzinfo=UTC)) > enabled_at
        ]
        candidates.sort(
            key=lambda event: (
                event.get("severity") == "red",
                _text(event.get("effective_at")),
            ),
            reverse=True,
        )
        if candidates:
            event = candidates[0]
            identifier = str(event["identifier"])
            card = json.loads(Path(event["confirmation_card_path"]).read_text(encoding="utf-8"))
            event["shadow_state"] = "PUBLISHING"
            event["publish_attempted_at"] = _iso(now)
            ledger[identifier] = event
            _write_ledger(ledger_path, ledger)
            try:
                qianfan_called = True
                result = _validate_published_result(publisher(card) if publisher else {})
                event.update(result)
                event["shadow_state"] = "PUBLISHED_VERIFIED"
                published_results.append(result)
            except WeatherPublishPreflightError as error:
                qianfan_called = False
                event["shadow_state"] = "HELD"
                event["hold_reason"] = "qianfan_preflight_failed"
                event["publish_error"] = f"{type(error).__name__}: {error}"[:500]
                held_reasons.append("qianfan_preflight_failed")
            except Exception as error:
                event["shadow_state"] = "PUBLISH_RESULT_UNKNOWN"
                event["publish_error"] = f"{type(error).__name__}: {error}"[:500]
                publish_unknown_count = 1
            event["last_seen_at"] = _iso(now)
            ledger[identifier] = event
            _write_ledger(ledger_path, ledger)
    report = {
        "status": (
            "AUTO_PUBLISH_ARMED" if auto_publish_armed
            else "AUTO_PUBLISH_COMPLETE" if publish
            else "BOOTSTRAPPED" if bootstrap
            else "SHADOW_COMPLETE"
        ),
        "run_at": _iso(now),
        "successful_source_count": successful_sources,
        "failed_source_count": len(source_errors),
        "source_errors": source_errors,
        "observation_count": len(observations),
        "merged_alert_count": len(merged),
        "confirmation_card_count": len(card_paths),
        "confirmation_card_paths": card_paths,
        "held_count": len(held_reasons),
        "held_reasons": sorted(set(held_reasons)),
        "published_count": len(published_results),
        "published_results": published_results,
        "publish_unknown_count": publish_unknown_count,
        "qianfan_called": qianfan_called,
        "push_called": False,
        "production_queue_write": False,
    }
    _append_jsonl(root / "run-report.jsonl", report)
    return report


def _hold_reason(event: dict[str, Any], now: datetime, known_ids: set[str]) -> str:
    if event.get("has_source_conflict"):
        return "source_conflict"
    if not event.get("body_complete"):
        return "incomplete_body"
    if event.get("severity") not in {"orange", "red"}:
        return "below_orange"
    effective_at = _parse_iso(event.get("effective_at"))
    if effective_at is None or effective_at < now - timedelta(minutes=15):
        return "stale_alert"
    if effective_at > now + timedelta(minutes=5):
        return "future_effective_at"
    if event.get("message_type") in {"Update", "Cancel"}:
        reference = _text(event.get("references_identifier"))
        if not reference or reference not in known_ids:
            return "missing_reference"
    return ""


def _confirmation_card(
    event: dict[str, Any],
    now: datetime,
    draft_runner: Callable[[str, str], dict[str, Any]] | None,
    *,
    human_confirmation_required: bool = True,
) -> dict[str, Any]:
    source_item = {
        "id": event["identifier"],
        "title": event.get("headline") or "",
        "summary": event.get("description") or "",
        "body": event.get("description") or "",
    }
    draft = None
    draft_error = ""
    if draft_runner is not None:
        try:
            response = draft_runner(
                _weather_draft_prompt(event),
                f"weather-shadow-{event['identifier']}",
            )
            candidate = response.get("draft") if isinstance(response.get("draft"), dict) else response
            reasons = validate_draft(candidate, source_item)
            if reasons:
                draft_error = ",".join(reasons)
            else:
                draft = candidate
        except Exception as error:
            draft_error = f"{type(error).__name__}: {error}"[:500]
    if draft is None:
        draft = _fallback_draft(event)
    validation_reasons = validate_draft(draft, source_item)
    if validation_reasons:
        raise WeatherShadowError(f"weather draft validation failed: {validation_reasons}")
    return {
        "identifier": event["identifier"],
        "created_at": _iso(now),
        "suggested_vest_name": "forever21",
        "document_type": "突发应急安全",
        "editor_route": "采采呀",
        "source_ids": event.get("source_ids") or [],
        "source_first_seen_at": event.get("source_first_seen_at") or {},
        "source_url": event.get("source_url") or "",
        "draft": draft,
        "draft_fallback_reason": draft_error,
        "style_evidence": _style_evidence(),
        "qianfan_called": False,
        "production_queue_write": False,
        "human_confirmation_required": human_confirmation_required,
    }


def _fallback_draft(event: dict[str, Any]) -> dict[str, Any]:
    area = "、".join(event.get("area_scope") or []) or "宜宾"
    color = {"orange": "橙色", "red": "红色"}[event["severity"]]
    description = _text(event.get("description"))
    issuer = _text(event.get("issuer"))
    action = {"Alert": "发布", "Update": "更新", "Cancel": "解除"}.get(
        _text(event.get("message_type")), "发布"
    )
    title = f"刚刚！{area}{action}{event['event_type']}{color}预警！"
    html = f"<p>{escape(description)}</p><p>发布单位：{escape(issuer)}</p>"
    return {
        "item_id": event["identifier"],
        "profile_id": "forever21",
        "title": title,
        "html": html,
        "fact_refs": [{"claim": description, "evidence": description}],
        "editor_route": "采采呀",
    }


def weather_publish_plan(card: dict[str, Any]) -> dict[str, Any]:
    draft = card.get("draft") if isinstance(card.get("draft"), dict) else {}
    identifier = _text(card.get("identifier"))
    if not identifier or not _text(draft.get("title")) or not _text(draft.get("html")):
        raise WeatherPublishPreflightError("weather confirmation card is incomplete")
    return {
        "content_id": identifier,
        "vest_name": "forever21",
        "forum_hint": "大美宜宾",
        "persona": "公共服务天气预警",
        "title": draft["title"],
    }


def validate_weather_preflight(
    raw: dict[str, dict[str, Any]], identifier: str
) -> dict[str, Any]:
    item = raw.get(identifier)
    if not isinstance(item, dict):
        raise WeatherPublishPreflightError("weather qianfan preflight is missing")
    required_true = (
        "vest_unique", "vest_enabled", "vest_id_present", "forum_unique", "forum_id_present"
    )
    if any(item.get(key) is not True for key in required_true):
        raise WeatherPublishPreflightError("weather qianfan target is not uniquely available")
    if item.get("type_required") is True and item.get("type_id_present") is not True:
        raise WeatherPublishPreflightError("weather qianfan required type is unresolved")
    if _text(item.get("vest_name")) != "forever21" or _text(item.get("forum_name")) != "大美宜宾":
        raise WeatherPublishPreflightError("weather qianfan target changed")
    return item


def weather_publish_prompt(card: dict[str, Any], preflight: dict[str, Any]) -> str:
    request = {
        "identifier": card["identifier"],
        "title": card["draft"]["title"],
        "html": card["draft"]["html"],
        "vest_name": "forever21",
        "forum_name": "大美宜宾",
        "type_name": preflight.get("type_name") or "无",
        "push": False,
    }
    return f"""
使用 qianfan-skill 发布这一条已通过硬门的宜宾官方气象预警，只允许一次发帖。

必须执行：
1. 再次实时精确核验唯一启用马甲 forever21、唯一板块 大美宜宾 和实时主题分类；任何漂移立即停止。
2. 发布前查询已通过和待审核帖子；同一马甲已有完全相同标题和完整正文时返回 existing，标题相同但正文不同则停止。
3. 无图片发布：show_type=0、attaches=[]；不得上传图片，不得调用 Push、消息、私信、短信或任何站外推送接口。
4. 仅调用一次 /review/vest-publish/add；响应不明确时只读查重，严禁重发。
5. 发布后核对完整标题、正文、马甲、板块和公开页 HTTP 可访问；按 Skill 合同记录查询与发布日志。
6. 不输出内部 ID、Token、Cookie、Authorization 或其他凭据；最终只输出 JSON。

请求：{json.dumps(request, ensure_ascii=False)}

JSON合同：
{{"publish_result":{{"status":"published|existing","tid":"...","url":"https://...","vest_name":"forever21","forum_name":"大美宜宾","type_name":"...","title_verified":true,"body_verified":true,"vest_verified":true,"public_http_ok":true,"published_at":"ISO-8601","push_called":false}}}}
""".strip()


def validate_weather_publish_response(
    response: dict[str, Any],
    card: dict[str, Any],
    preflight: dict[str, Any],
    metadata: dict[str, Any] | None,
) -> dict[str, str]:
    item = response.get("publish_result")
    if not isinstance(item, dict) or item.get("status") not in {"published", "existing"}:
        raise WeatherShadowError("qianfan weather publish result is not verified")
    if any(
        item.get(key) is not True
        for key in ("title_verified", "body_verified", "vest_verified", "public_http_ok")
    ) or item.get("push_called") is not False:
        raise WeatherShadowError("qianfan weather public verification failed")
    expected = {
        "vest_name": "forever21",
        "forum_name": "大美宜宾",
        "type_name": _text(preflight.get("type_name")) or "无",
    }
    if any(_text(item.get(key)) != value for key, value in expected.items()):
        raise WeatherShadowError("qianfan weather published target does not match preflight")
    tid = _text(item.get("tid"))
    if not isinstance(metadata, dict) or any(
        _text(metadata.get(key)) != value
        for key, value in {
            "tid": tid,
            "title": _text(card["draft"]["title"]),
            "vest_name": "forever21",
            "forum_name": "大美宜宾",
        }.items()
    ):
        raise WeatherShadowError("qianfan weather post-publish metadata does not match")
    return _validate_published_result({
        "status": "PUBLISHED_VERIFIED",
        "tid": tid,
        "url": metadata.get("url") or item.get("url"),
        **expected,
        "published_at": metadata.get("published_at") or item.get("published_at"),
    })


def _validate_published_result(result: dict[str, Any]) -> dict[str, str]:
    if result.get("status") != "PUBLISHED_VERIFIED":
        raise WeatherShadowError("weather publish result is not verified")
    expected = {"vest_name": "forever21", "forum_name": "大美宜宾"}
    if any(_text(result.get(key)) != value for key, value in expected.items()):
        raise WeatherShadowError("weather publish target does not match preflight")
    normalized = {
        key: _text(result.get(key))
        for key in (
            "status", "tid", "url", "vest_name", "forum_name", "type_name", "published_at"
        )
    }
    if not all(normalized.values()) or not normalized["url"].startswith("https://"):
        raise WeatherShadowError("weather publish result is incomplete")
    try:
        datetime.fromisoformat(normalized["published_at"].replace("Z", "+00:00"))
    except ValueError as error:
        raise WeatherShadowError("weather published_at is invalid") from error
    return normalized


def _weather_draft_prompt(event: dict[str, Any]) -> str:
    return f"""
调用 app-skill 为大宜宾 APP 生成天气预警影子稿，只输出 JSON 对象。

固定路由：文稿类型“突发应急安全”，唯一小编路线“采采呀”，承载马甲“forever21”。
历史格式依据：app-skill 训练库中的同类天气/预警帖子；不得套用网友现场、灾情或亲历内容。
官方预警：{json.dumps(event, ensure_ascii=False)}

硬规则：
1. 只能使用官方预警字段中的事实和数字，不补充常识数字，不虚构现场。
2. 标题必须包含影响地区、预警类型、颜色级别；正文先说结论，再完整保留官方防范信息。
3. fact_refs.evidence 必须逐字来自 headline 或 description。
4. item_id 必须为 {event['identifier']}，profile_id 必须为 forever21，editor_route 必须为 采采呀。
5. 正文只用简单 HTML；不调用千帆，不发布。

JSON 合同：
{{"draft":{{"item_id":"{event['identifier']}","profile_id":"forever21","title":"...","html":"<p>...</p>","fact_refs":[{{"claim":"...","evidence":"官方原句"}}],"editor_route":"采采呀"}}}}
""".strip()


def _style_evidence() -> list[dict[str, Any]]:
    evidence = []
    for path in STYLE_FILES:
        content = path.read_bytes()
        evidence.append({
            "path": str(path),
            "bytes": len(content),
            "sha256": sha256(content).hexdigest(),
            "read_status": "READ_FULL_EOF",
        })
    return evidence


def _read_ledger(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    ledger = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        identifier = _text(record.get("identifier"))
        if identifier:
            ledger[identifier] = record
    return ledger


def _write_ledger(path: Path, ledger: dict[str, dict[str, Any]]) -> None:
    lines = [json.dumps(ledger[key], ensure_ascii=False, sort_keys=True) for key in sorted(ledger)]
    atomic_write_text(path, "\n".join(lines) + ("\n" if lines else ""))


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    atomic_write_text(path, existing + json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _message_type(value: Any, headline: str) -> str:
    normalized = _text(value).lower()
    if normalized == "cancel" or "解除" in headline:
        return "Cancel"
    if normalized == "update" or "更新" in headline or "继续" in headline:
        return "Update"
    return "Alert"


def _warning_parts(value: str) -> tuple[str, str]:
    match = _WARNING_RE.search(value)
    if not match:
        return "", ""
    return match.group(1), _SEVERITY_BY_CN[match.group(2)]


def _normalize_severity(value: Any) -> str:
    normalized = _text(value).lower()
    return {"blue": "blue", "yellow": "yellow", "orange": "orange", "red": "red"}.get(
        normalized, _SEVERITY_BY_CN.get(_text(value), "")
    )


def _issuer_from_location(value: str) -> str:
    local = value.removeprefix("四川省").removeprefix("宜宾市")
    return f"{local}气象台" if local else "宜宾市气象台"


def _issuer_from_title(value: str) -> str:
    match = re.search(r"(?:四川省)?(?:宜宾市)?([^发更解]{1,16}气象台)", value)
    return match.group(1) if match else ""


def _area_scope(issuer: str) -> list[str]:
    area = issuer.removesuffix("气象台").strip()
    return [area] if area else []


def _parse_local_datetime(value: Any, fallback_identifier: str) -> datetime | None:
    normalized = _text(value).removesuffix(".0")
    if normalized:
        try:
            return datetime.strptime(normalized, "%Y-%m-%d %H:%M:%S").replace(tzinfo=SHANGHAI)
        except ValueError:
            pass
    return _parse_identifier_datetime(fallback_identifier)


def _parse_identifier_datetime(identifier: str) -> datetime | None:
    suffix = identifier.rsplit("_", 1)[-1]
    try:
        return datetime.strptime(suffix, "%Y%m%d%H%M%S").replace(tzinfo=SHANGHAI)
    except ValueError:
        return None


def _parse_iso(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(_text(value))
    except ValueError:
        return None
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed


def _iso(value: datetime | None) -> str:
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat(timespec="seconds")


def _text(value: Any) -> str:
    return " ".join(str(value or "").split())
