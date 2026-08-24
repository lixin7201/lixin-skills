from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any
from zoneinfo import ZoneInfo

from .storage import atomic_write_json, read_json


RUNTIME_READONLY_ENDPOINTS = frozenset(
    {
        ("POST", "/service/rank/rank"),
        ("POST", "/service/rank/cy_list"),
        ("POST", "/service/search/post_list"),
    }
)
OPTIONAL_METADATA_ENDPOINTS = frozenset(
    {("GET", "/service/rank/hot_search_city_list")}
)

_YIBIN_TERMS = (
    "宜宾",
    "翠屏",
    "叙州",
    "南溪",
    "江安",
    "长宁",
    "高县",
    "筠连",
    "珙县",
    "兴文",
    "屏山",
    "三江新区",
    "临港",
    "高新区",
)
_EXTERNAL_EVENT_TERMS = (
    "成都", "泸州", "乐山", "马边", "旺苍", "广元", "绵阳", "德阳", "遂宁",
    "内江", "资阳", "眉山", "雅安", "自贡", "攀枝花", "达州", "巴中", "南充",
    "广安", "阿坝", "甘孜", "凉山", "重庆", "牡丹江", "黑龙江",
    "广西", "隆安",
)
_LOCAL_SOURCE_PATTERN = re.compile(
    r"宜宾(?:市)?(?:人民政府|融媒体中心|广播电视台|发布|日报|新闻网)|大宜宾"
)
_METADATA_MARKERS = (
    "命中词：", "命中地域：", "信息属性：", "信息类型：", "账号昵称：", "用户ID：",
    "用户平台号：", "来源平台：", "发文来源：", "发文日期：", "发文时间：", "信息链接：",
    "联系电话：",
)


class XyuqingSourceError(RuntimeError):
    pass


class XyuqingAuthRequired(XyuqingSourceError):
    pass


class XyuqingEndpointNotAllowed(XyuqingSourceError):
    pass


class XyuqingSchemaError(XyuqingSourceError):
    pass


class XyuqingNetworkError(XyuqingSourceError):
    pass


class XyuqingRateLimited(XyuqingSourceError):
    pass


class XyuqingUiUnavailable(XyuqingSourceError):
    pass


def assert_endpoint_allowed(method: str, path: str, *, purpose: str = "runtime") -> None:
    endpoint = (method.upper(), path)
    allowed = RUNTIME_READONLY_ENDPOINTS if purpose == "runtime" else OPTIONAL_METADATA_ENDPOINTS
    if purpose not in {"runtime", "metadata"} or endpoint not in allowed:
        raise XyuqingEndpointNotAllowed(f"xyuqing endpoint is not allowed: {method.upper()} {path}")


def require_auth_ok(
    *, token_present: bool, http_status: int, payload: object
) -> None:
    code = payload.get("code") if isinstance(payload, dict) else None
    if not token_present or http_status in {401, 403} or code in {20001, "20001"}:
        raise XyuqingAuthRequired("XYUQING_AUTH_REQUIRED")


def classify_locality(item: dict[str, Any]) -> str:
    title = _event_location_text(item.get("title"))
    content = _event_location_text(item.get("content"))
    poi = _event_location_text(item.get("poi_name"))
    source = str(item.get("source_name") or "")
    event_evidence = " ".join((title, content, poi))
    if any(term in title for term in _EXTERNAL_EVENT_TERMS):
        return "rejected"
    external = {term for term in _EXTERNAL_EVENT_TERMS if term in event_evidence}
    local = {term for term in _YIBIN_TERMS if term in event_evidence}
    if external and not local:
        return "rejected"
    if external and local:
        return "needs_verification"
    if local or _LOCAL_SOURCE_PATTERN.search(source):
        return "direct"
    if "四川" in event_evidence:
        return "rejected"
    return "needs_verification"


def _event_location_text(value: object) -> str:
    text = " ".join(str(value or "").split())
    if "摘要：" in text:
        text = text.rsplit("摘要：", 1)[-1]
    marker_positions = [text.find(marker) for marker in _METADATA_MARKERS if marker in text]
    if marker_positions:
        text = text[: min(marker_positions)]
    text = re.sub(
        r"(?:📍|IP属地[:：]?|账号定位[:：]?|定位[:：]?)\s*(?:四川省?)?\s*宜宾市?\s*$",
        "",
        text,
    )
    return text.strip()


def deduplicate_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    output: list[dict[str, Any]] = []
    for item in items:
        key = next(
            (
                (name, str(item[name]))
                for name in ("unique_id", "unity_id", "similar_id", "url", "content_hash")
                if item.get(name)
            ),
            None,
        )
        if key is not None and key in seen:
            continue
        if key is not None:
            seen.add(key)
        output.append(item)
    return output


def parse_rank_response(payload: object) -> list[dict[str, Any]]:
    value = _require_json_object(payload)
    groups = _require_list(value, "post")
    output: list[dict[str, Any]] = []
    for group in groups:
        if not isinstance(group, dict):
            raise XyuqingSchemaError("rank post group must be an object")
        rows = group.get("list")
        if not isinstance(rows, list):
            raise XyuqingSchemaError("rank post group list must be an array")
        if not all(isinstance(row, dict) for row in rows):
            raise XyuqingSchemaError("rank post item must be an object")
        output.extend(rows)
    return output


def parse_cy_list_response(payload: object) -> list[dict[str, Any]]:
    value = _require_json_object(payload)
    rows = _require_list(value, "list")
    if not all(isinstance(row, dict) for row in rows):
        raise XyuqingSchemaError("cy_list item must be an object")
    return rows


def parse_post_list_response(payload: object, *, return_type: int) -> list[dict[str, Any]]:
    if return_type != 1:
        raise XyuqingSchemaError("post_list summary cannot be used as a content list")
    value = _require_json_object(payload)
    rows = _require_list(value, "list")
    if not all(isinstance(row, dict) for row in rows):
        raise XyuqingSchemaError("post_list item must be an object")
    return rows


def normalize_signal(
    item: dict[str, Any],
    *,
    access_path: str,
    city_requested: str,
    collected_at: str,
) -> dict[str, Any]:
    if access_path not in {"bearer", "ego_ui"}:
        raise ValueError("access_path must be bearer or ego_ui")
    topic = str(item.get("title") or "").strip()
    if not topic:
        raise XyuqingSchemaError("rank item is missing title")
    platform = str(item.get("platform") or item.get("platform_en") or "unknown")
    first_seen_at = (
        str(item.get("first_seen_at"))
        if isinstance(item.get("first_seen_at"), str) and item.get("first_seen_at")
        else _timestamp(item.get("strtotime"), collected_at)
    )
    signal_id = hashlib.sha256(
        f"{platform}|{' '.join(topic.split()).lower()}|{first_seen_at}".encode("utf-8")
    ).hexdigest()
    return {
        "signal_id": signal_id,
        "source_id": "signal-xyuqing-yibin",
        "source_tier": "P3_SIGNAL",
        "topic": topic,
        "platform": platform,
        "city_requested": city_requested,
        "locality_state": classify_locality(item),
        "locality_evidence": [term for term in _YIBIN_TERMS if term in topic],
        "current_rank": item.get("rank"),
        "peak_rank": item.get("rank"),
        "heat": item.get("score"),
        "first_seen_at": first_seen_at,
        "last_seen_at": first_seen_at,
        "on_list_duration_seconds": item.get("duration") or 0,
        "search_url": str(item.get("kw_url") or ""),
        "related_source_urls": [],
        "access_path": access_path,
        "write_eligibility": "signal_only",
        "collected_at": collected_at,
    }


def redact_sensitive_text(value: str) -> str:
    value = re.sub(r"(?i)(authorization\s*:\s*bearer\s+)\S+", r"\1[REDACTED]", value)
    return re.sub(r"(?im)^(cookie\s*:\s*).+$", r"\1[REDACTED]", value)


def write_round_bundle(
    bundle: dict[str, Any],
    *,
    data_dir: str | Path,
    business_date: str,
    collected_at: str,
) -> dict[str, Any]:
    access_path = str(bundle.get("access_path") or "bearer")
    if access_path == "ego_ui":
        validate_ui_bundle(bundle)
    elif access_path != "bearer":
        raise XyuqingSchemaError("xyuqing bundle has unknown access path")
    auth_status = bundle.get("auth_status")
    if auth_status == "AUTH_REQUIRED":
        raise XyuqingAuthRequired("XYUQING_AUTH_REQUIRED")
    if auth_status == "RATE_LIMITED":
        raise XyuqingRateLimited("XYUQING_RATE_LIMITED")
    if auth_status == "NETWORK_ERROR":
        raise XyuqingNetworkError("XYUQING_NETWORK_ERROR")
    if auth_status != "AUTH_OK":
        raise XyuqingSchemaError("xyuqing bundle has unknown auth status")
    requests = bundle.get("requests")
    if not isinstance(requests, list):
        raise XyuqingSchemaError("xyuqing bundle requests must be an array")
    safe_requests: list[dict[str, Any]] = []
    for request in requests:
        if not isinstance(request, dict):
            raise XyuqingSchemaError("xyuqing request evidence must be an object")
        method = str(request.get("method") or "")
        path = str(request.get("path") or "")
        assert_endpoint_allowed(method, path)
        status = request.get("http_status")
        if status == 429:
            raise XyuqingSourceError("XYUQING_RATE_LIMITED")
        if status in {401, 403}:
            raise XyuqingAuthRequired("XYUQING_AUTH_REQUIRED")
        safe_requests.append({"method": method.upper(), "path": path, "http_status": status})

    rank_items = parse_rank_response(bundle.get("rank"))
    city_rows = parse_cy_list_response(bundle.get("cy_list"))
    related_by_rank: dict[str, list[str]] = {}
    related = bundle.get("related")
    if not isinstance(related, list):
        raise XyuqingSchemaError("xyuqing bundle related must be an array")
    for entry in related:
        if not isinstance(entry, dict):
            raise XyuqingSchemaError("xyuqing related entry must be an object")
        rank_id = str(entry.get("rank_id") or "")
        rows = parse_post_list_response(entry.get("response"), return_type=1)
        related_by_rank[rank_id] = list(
            dict.fromkeys(
                str(row.get("url"))
                for row in rows
                if isinstance(row.get("url"), str)
                and str(row.get("url")).startswith(("http://", "https://"))
            )
        )

    direct_items = [item for item in rank_items if classify_locality(item) == "direct"]
    signals: list[dict[str, Any]] = []
    for item in direct_items:
        signal = normalize_signal(
            item,
            access_path=access_path,
            city_requested="四川 - 宜宾",
            collected_at=collected_at,
        )
        signal["related_source_urls"] = related_by_rank.get(str(item.get("id") or ""), [])
        signals.append(signal)

    root = Path(data_dir) / business_date
    signals_path = root / "xyuqing-signals.json"
    report_path = root / "xyuqing-run-report.json"
    existing = read_json(signals_path).get("signals", []) if signals_path.exists() else []
    if not isinstance(existing, list) or not all(isinstance(item, dict) for item in existing):
        raise XyuqingSchemaError("existing xyuqing signals must be an array of objects")
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for item in existing:
        key = _signal_topic_key(item)
        if key in merged:
            merged[key] = _merge_signal(merged[key], item)
        else:
            merged[key] = item
    for signal in signals:
        key = _signal_topic_key(signal)
        if key in merged:
            merged[key] = _merge_signal(merged[key], signal)
        else:
            merged[key] = signal

    signals_payload = {
        "schema_version": 1,
        "business_date": business_date,
        "signals": list(merged.values()),
    }
    report_payload = {
        "schema_version": 1,
        "business_date": business_date,
        "collected_at": collected_at,
        "access_path": access_path,
        "auth_status": "AUTH_OK",
        "duration_ms": bundle.get("duration_ms"),
        "request_count": len(safe_requests),
        "requests": safe_requests,
        "raw_rank_count": len(rank_items),
        "city_option_count": len(city_rows),
        "locality_pass_count": len(direct_items),
        "locality_rejected_count": len(rank_items) - len(direct_items),
        "related_search_count": len(related),
        "signal_count": len(merged),
        "circuit_open": False,
    }
    if access_path == "ego_ui":
        report_payload["ui_actions"] = bundle.get("ui_actions", [])
        report_payload["viewport"] = bundle.get("viewport")
    atomic_write_json(signals_path, signals_payload)
    atomic_write_json(report_path, report_payload)
    return {
        "signals_path": str(signals_path),
        "report_path": str(report_path),
        "signal_count": len(merged),
    }


def validate_ui_bundle(bundle: dict[str, Any]) -> None:
    viewport = bundle.get("viewport")
    if (
        not isinstance(viewport, list)
        or len(viewport) != 2
        or not all(isinstance(value, (int, float)) and value > 0 for value in viewport)
    ):
        raise XyuqingUiUnavailable("UI viewport is zero")
    expected = {
        "selected_tab": "同城热榜",
        "city_selected": "四川 - 宜宾",
        "time_selected": "近24h",
    }
    for key, value in expected.items():
        if bundle.get(key) != value:
            raise XyuqingUiUnavailable(f"UI fixed page state is invalid: {key}")


def run_round_with_fallback(
    *,
    primary_fetch,
    ui_fetch,
    data_dir: str | Path,
    business_date: str,
    collected_at: str,
) -> dict[str, Any]:
    try:
        return write_round_bundle(
            primary_fetch(),
            data_dir=data_dir,
            business_date=business_date,
            collected_at=collected_at,
        )
    except (XyuqingAuthRequired, XyuqingRateLimited, XyuqingEndpointNotAllowed):
        raise
    except (XyuqingSchemaError, XyuqingNetworkError) as primary_error:
        primary_failure = (
            "SCHEMA_ERROR" if isinstance(primary_error, XyuqingSchemaError) else "NETWORK_ERROR"
        )

    root = Path(data_dir) / business_date
    report_path = root / "xyuqing-run-report.json"
    previous = read_json(report_path) if report_path.exists() else {}
    if previous.get("circuit_open") is True:
        raise XyuqingUiUnavailable("UI fallback circuit is open")
    current = datetime.fromisoformat(collected_at)
    last_text = previous.get("ui_last_attempt_at")
    if isinstance(last_text, str):
        last = datetime.fromisoformat(last_text)
        if (current - last).total_seconds() < 3600:
            raise XyuqingUiUnavailable("UI fallback hourly limit is active")

    failures = int(previous.get("ui_consecutive_failures") or 0)
    try:
        ui_bundle = ui_fetch()
        validate_ui_bundle(ui_bundle)
        result = write_round_bundle(
            ui_bundle,
            data_dir=data_dir,
            business_date=business_date,
            collected_at=collected_at,
        )
    except XyuqingSourceError as ui_error:
        failures += 1
        atomic_write_json(
            report_path,
            {
                "schema_version": 1,
                "business_date": business_date,
                "collected_at": collected_at,
                "access_path": "ego_ui",
                "auth_status": "AUTH_OK",
                "primary_failure": primary_failure,
                "ui_fallback_used": True,
                "ui_last_attempt_at": collected_at,
                "ui_consecutive_failures": failures,
                "ui_failure": type(ui_error).__name__,
                "circuit_open": failures >= 2,
            },
        )
        raise

    report = read_json(result["report_path"])
    report.update(
        {
            "primary_failure": primary_failure,
            "ui_fallback_used": True,
            "ui_last_attempt_at": collected_at,
            "ui_consecutive_failures": 0,
            "circuit_open": False,
        }
    )
    atomic_write_json(result["report_path"], report)
    return result


_EGO_SENTINEL = "XYUQING_RESULT_JSON="


def parse_ego_result(stdout: str) -> dict[str, Any]:
    if re.search(r"(?i)authorization\s*:\s*bearer\s+\S+", stdout):
        raise XyuqingSourceError("ego output contained an authorization value")
    if re.search(r"(?im)^cookie\s*:\s*\S+", stdout):
        raise XyuqingSourceError("ego output contained a cookie value")
    if re.search(r'(?i)["\'](?:token|password|secret|authorization|cookie)["\']\s*:', stdout):
        raise XyuqingSourceError("ego output contained a credential field")
    line = next(
        (line for line in reversed(stdout.splitlines()) if line.startswith(_EGO_SENTINEL)),
        None,
    )
    if line is None:
        raise XyuqingSourceError("ego output did not contain the result sentinel")
    try:
        payload = json.loads(line[len(_EGO_SENTINEL) :])
    except json.JSONDecodeError as error:
        raise XyuqingSourceError("ego result was not valid JSON") from error
    if not isinstance(payload, dict):
        raise XyuqingSourceError("ego result must be an object")
    return payload


def fetch_live_bundle(
    *,
    task_space: str = "xyuqing-x3-bearer",
    ego_executable: str = "ego-browser",
    timeout_seconds: int = 90,
) -> dict[str, Any]:
    return _run_ego_script(
        _ego_script(task_space),
        ego_executable=ego_executable,
        timeout_seconds=timeout_seconds,
    )


def fetch_ui_bundle(
    *,
    task_space: str = "xyuqing-x4-ui",
    ego_executable: str = "ego-browser",
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    return _run_ego_script(
        _ego_ui_script(task_space),
        ego_executable=ego_executable,
        timeout_seconds=timeout_seconds,
    )


def _run_ego_script(
    script: str,
    *,
    ego_executable: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [ego_executable, "nodejs"],
            input=script,
            capture_output=True,
            text=True,
            shell=False,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise XyuqingNetworkError(
            f"ego browser failed: {redact_sensitive_text(str(error))}"
        ) from error
    if result.returncode != 0:
        detail = redact_sensitive_text((result.stderr or result.stdout or "").strip())
        raise XyuqingNetworkError(f"ego browser exited with {result.returncode}: {detail[:300]}")
    return parse_ego_result("\n".join(part for part in (result.stdout, result.stderr) if part))


def run_live_round(
    *,
    data_dir: str | Path,
    business_date: str,
    collected_at: str,
    task_space: str = "xyuqing-x3-bearer",
    ui_task_space: str = "xyuqing-x4-ui",
    ego_executable: str = "ego-browser",
    simulate_primary_schema_failure: bool = False,
) -> dict[str, Any]:
    def primary_fetch() -> dict[str, Any]:
        if simulate_primary_schema_failure:
            raise XyuqingSchemaError("simulated primary schema failure")
        return fetch_live_bundle(task_space=task_space, ego_executable=ego_executable)

    return run_round_with_fallback(
        primary_fetch=primary_fetch,
        ui_fetch=lambda: fetch_ui_bundle(
            task_space=ui_task_space,
            ego_executable=ego_executable,
        ),
        data_dir=data_dir,
        business_date=business_date,
        collected_at=collected_at,
    )


def _ego_script(task_space: str) -> str:
    task_name = json.dumps(task_space)
    return f"""
const startedAt = Date.now()
const task = await useOrCreateTaskSpace({task_name})
await openOrReuseTab('https://www.xyuqing.com/monitor/hotsearch', {{wait:true, timeout:30}})
await waitForNetworkIdle({{timeout:15}}).catch(() => {{}})
await js(String.raw`(()=>{{
  window.__xyuqingX3Done = false
  window.__xyuqingX3Result = null
  ;(async()=>{{
  const allowed = new Set([
    '/service/rank/rank',
    '/service/rank/cy_list',
    '/service/search/post_list',
  ])
  const requests = []
  const token = localStorage.getItem('token')
  if (!token) return {{auth_status:'AUTH_REQUIRED', requests, rank:{{}}, cy_list:{{}}, related:[]}}
  const headers = {{Accept:'application/json','Content-Type':'application/json',Authorization:'Bearer '+token}}
  const call = async (path, body) => {{
    if (!allowed.has(path)) throw new Error('endpoint not allowed')
    try {{
      const response = await fetch('https://api.xyuqing.com'+path, {{
        method:'POST', headers, body:JSON.stringify(body), credentials:'omit', redirect:'follow'
      }})
      const finalUrl = new URL(response.url)
      if (finalUrl.hostname !== 'api.xyuqing.com') throw new Error('unexpected redirect')
      const text = await response.text()
      let payload
      try {{ payload = JSON.parse(text) }} catch {{ payload = {{__non_json__:true}} }}
      requests.push({{method:'POST', path, http_status:response.status}})
      return {{http_status:response.status, payload}}
    }} catch (error) {{
      return {{network_error:true, error_class:error?.name || 'Error'}}
    }}
  }}
  const end = new Date()
  const start = new Date(end.getTime() - 24*60*60*1000)
  const rankBody = {{
    date:'now', keyword:'', city:'宜宾', time:[start.toISOString(), end.toISOString()],
    rank_type:3, platform:'', hot_search_kw_type:''
  }}
  const rankCall = await call('/service/rank/rank', rankBody)
  const cityCall = await call('/service/rank/cy_list', rankBody)
  const calls = [rankCall, cityCall]
  if (calls.some(x => x.network_error))
    return {{auth_status:'NETWORK_ERROR', requests, rank:{{}}, cy_list:{{}}, related:[]}}
  if (calls.some(x => x.http_status === 429))
    return {{auth_status:'RATE_LIMITED', requests, rank:{{}}, cy_list:{{}}, related:[]}}
  if (calls.some(x => [401,403].includes(x.http_status) || x.payload?.code === 20001))
    return {{auth_status:'AUTH_REQUIRED', requests, rank:{{}}, cy_list:{{}}, related:[]}}
  const localTerms = ['宜宾','翠屏','叙州','南溪','江安','长宁','高县','筠连','珙县','兴文','屏山','三江新区','临港','高新区']
  const rankItems = (rankCall.payload?.data?.post || []).flatMap(group => Array.isArray(group?.list) ? group.list : [])
  const safeRank = {{
    code:rankCall.payload?.code,
    message:rankCall.payload?.message,
    data:{{post:(rankCall.payload?.data?.post || []).map(group => ({{
      platform:group?.platform,
      update_time:group?.update_time,
      list:(Array.isArray(group?.list) ? group.list : []).map(item => ({{
        id:item?.id, title:item?.title, platform:item?.platform, platform_en:item?.platform_en,
        rank:item?.rank, score:item?.score, strtotime:item?.strtotime, kw_url:item?.kw_url,
        duration:item?.duration, date_updateAt:item?.date_updateAt
      }}))
    }}))}}
  }}
  const safeCity = {{
    code:cityCall.payload?.code,
    message:cityCall.payload?.message,
    data:{{list:(Array.isArray(cityCall.payload?.data?.list) ? cityCall.payload.data.list : []).map(item => ({{name:item?.name,value:item?.value}}))}}
  }}
  const topics = rankItems.filter(item => localTerms.some(term => String(item?.title || '').includes(term))).slice(0,5)
  const related = []
  for (const item of topics) {{
    const postBody = {{
      word:String(item.title || ''), hit_field:['content','title','cover_ocr','ocr','asr','nickname','poi','last_poi'],
      post_category:0, image_url:'', date:'24h', page_size:50, reduce_noise:0, discrimination:0,
      mini_word_field:'all', miniWord:[], page:1, direct_id:'', industry_filter:'',
      platform:['douyin','weibo','weixin','toutiao','xiaohongshu','web','app','bbs','enews','jingwai','shipin'],
      platform_name_exact:[], source_type:[], retweeted_type:0, comment_type:0, merge:0, is_read:0,
      media:[0,1,2], is_ai_content:-1, have_topic:0, have_at:0, have_mcn:0,
      source_level:['央级','省级','地市','区县','境外','商业','中小','行业门户','其他'],
      exclude_gov:0, undeleted:0, industry_name:[], water_army:[], scene:[], poi:[],
      verify:['政务认证','机构认证','企业认证','个人认证','未认证'], verify_weibo:[1,2,3,4,5,6,7],
      scene_name:[], duration:[',15','15,30','30,60','60,'], respond_field_type:'like_count',
      defineDataRange:[], respond_field_num:'', fans_count:'', sentiment:['非敏感','敏感','中性'],
      original:[0,1,2], save_filter:0, return_type:1
    }}
    const relatedCall = await call('/service/search/post_list', postBody)
    if (relatedCall.network_error)
      return {{auth_status:'NETWORK_ERROR', requests, rank:safeRank, cy_list:safeCity, related}}
    if (relatedCall.http_status === 429)
      return {{auth_status:'RATE_LIMITED', requests, rank:safeRank, cy_list:safeCity, related}}
    if ([401,403].includes(relatedCall.http_status) || relatedCall.payload?.code === 20001)
      return {{auth_status:'AUTH_REQUIRED', requests, rank:safeRank, cy_list:safeCity, related}}
    related.push({{
      rank_id:String(item.id || ''),
      response:{{
        code:relatedCall.payload?.code,
        message:relatedCall.payload?.message,
        data:{{list:(Array.isArray(relatedCall.payload?.data?.list) ? relatedCall.payload.data.list : []).map(row => ({{
          unique_id:row?.unique_id, unity_id:row?.unity_id, similar_id:row?.similar_id, url:row?.url
        }}))}}
      }}
    }})
  }}
  return {{auth_status:'AUTH_OK', requests, rank:safeRank, cy_list:safeCity, related}}
  }})().then(result => {{
    window.__xyuqingX3Result = result
    window.__xyuqingX3Done = true
  }}).catch(error => {{
    window.__xyuqingX3Result = {{auth_status:'NETWORK_ERROR', requests:[], rank:{{}}, cy_list:{{}}, related:[], error_class:error?.name || 'Error'}}
    window.__xyuqingX3Done = true
  }})
  return true
}})()`)
let bundle = null
for (let attempt = 0; attempt < 60; attempt++) {{
  await wait(1)
  const state = await js(String.raw`(()=>({{done:Boolean(window.__xyuqingX3Done),result:window.__xyuqingX3Result}}))()`)
  if (state.done) {{
    bundle = state.result
    break
  }}
}}
if (!bundle) bundle = {{auth_status:'NETWORK_ERROR', requests:[], rank:{{}}, cy_list:{{}}, related:[], error_class:'Timeout'}}
bundle.task_space_id = task.id
bundle.duration_ms = Date.now() - startedAt
cliLog('XYUQING_RESULT_JSON=' + JSON.stringify(bundle))
"""


def _ego_ui_script(task_space: str) -> str:
    task_name = json.dumps(task_space)
    return f"""
const startedAt = Date.now()
const task = await useOrCreateTaskSpace({task_name})
let bundle
try {{
  await openOrReuseTab('https://www.xyuqing.com/monitor/hotsearch', {{wait:true, timeout:30}})
  await waitForNetworkIdle({{timeout:15}}).catch(() => {{}})
  await wait(2)
  let info = await pageInfo()
  if (!info.w || !info.h) throw new Error('viewport is zero')
  const loggedOut = await js(String.raw`Boolean(document.querySelector('input[type=password]'))`)
  if (loggedOut) {{
    bundle = {{auth_status:'AUTH_REQUIRED', access_path:'ego_ui', viewport:[info.w,info.h], selected_tab:'', city_selected:'', time_selected:'', requests:[], rank:{{}}, cy_list:{{}}, related:[]}}
  }} else {{
    await waitForElement("xpath=//*[@role='tab' and normalize-space(.)='同城热榜']", {{timeout:10}})
    await click("xpath=//*[@role='tab' and normalize-space(.)='同城热榜']", {{label:'open city hotlist'}})
    await wait(2)
    let selected = await js(String.raw`(()=>[...document.querySelectorAll('.ant-select-selection-item')].map(e=>(e.innerText||e.textContent||'').trim()).filter(Boolean))()`)
    if (!selected.includes('四川 - 宜宾')) {{
      await click("xpath=//*[contains(@class,'ant-select-selection-item') and contains(normalize-space(.),' - ')]", {{label:'open city selector'}})
      await wait(1)
      await click("xpath=//*[@role='option' and normalize-space(.)='四川 - 宜宾']", {{label:'select yibin city'}})
      await wait(2)
    }}
    const checkedTime = await js(String.raw`(()=>[...document.querySelectorAll('label.ant-radio-button-wrapper')].find(e=>e.querySelector('input')?.checked)?.innerText?.trim()||'')()`)
    if (checkedTime !== '近24h') {{
      await click("xpath=//label[normalize-space(.)='近24h']", {{label:'select last 24 hours'}})
      await wait(4)
    }}
    info = await pageInfo()
    const snapshot = await js(String.raw`(() => {{
      const selectedTab=[...document.querySelectorAll('[role=tab][aria-selected=true]')].map(e=>(e.innerText||'').trim())[0]||''
      const selections=[...document.querySelectorAll('.ant-select-selection-item')].map(e=>(e.innerText||e.textContent||'').trim()).filter(Boolean)
      const city=selections.find(value=>value.includes(' - '))||''
      const time=[...document.querySelectorAll('label.ant-radio-button-wrapper')].find(e=>e.querySelector('input')?.checked)?.innerText?.trim()||''
      const table=[...document.querySelectorAll('.ant-table')].find(t=>[...t.querySelectorAll('thead th')].some(th=>(th.innerText||'').trim()==='热搜内容'))
      if(!table)return{{ui_error:'target table missing',selectedTab,city,time,rows:[]}}
      const number=value=>{{const text=String(value||'').replace(/,/g,'').trim();const match=text.match(/[0-9.]+/);if(!match)return null;const n=Number(match[0]);return text.includes('万')?Math.round(n*10000):n}}
      const duration=value=>{{const text=String(value||'');const day=Number(text.match(/([0-9]+)天/)?.[1]||0);const hour=Number(text.match(/([0-9]+)小时/)?.[1]||0);const minute=Number(text.match(/([0-9]+)分/)?.[1]||0);const second=Number(text.match(/([0-9]+)秒/)?.[1]||0);return day*86400+hour*3600+minute*60+second}}
      const now=Date.now()
      const rows=[...table.querySelectorAll('tbody tr')].map(row=>[...row.querySelectorAll('td')].map(cell=>(cell.innerText||'').trim())).filter(cells=>cells.length>=6&&cells[1])
      return{{selectedTab,city,time,ui_error:null,rows:rows.map(cells=>{{const seconds=duration(cells[3]);const title=cells[1];return{{id:'ui-'+cells[0]+'-'+title,title,platform:'douyin_city',rank:number(cells[0]),score:number(cells[2]),duration:seconds,first_seen_at:new Date(now-seconds*1000).toISOString(),kw_url:'https://www.xyuqing.com/search/info?word='+encodeURIComponent(title),source_name:cells[4]}}}})}}
    }})()`)
    if (snapshot.ui_error) throw new Error(snapshot.ui_error)
    bundle = {{
      auth_status:'AUTH_OK', access_path:'ego_ui', viewport:[info.w,info.h],
      selected_tab:snapshot.selectedTab, city_selected:snapshot.city, time_selected:snapshot.time,
      ui_actions:['open city hotlist','ensure 四川 - 宜宾','select 近24h'], requests:[],
      rank:{{code:0,message:'ui',data:{{post:[{{platform:'douyin_city',update_time:new Date().toISOString(),list:snapshot.rows}}]}}}},
      cy_list:{{code:0,message:'ui',data:{{list:[{{name:snapshot.city,value:'宜宾'}}]}}}}, related:[]
    }}
  }}
}} catch (error) {{
  const info = await pageInfo().catch(() => ({{w:0,h:0}}))
  bundle = {{auth_status:'AUTH_OK', access_path:'ego_ui', viewport:[info.w||0,info.h||0], selected_tab:'', city_selected:'', time_selected:'', ui_error_class:error?.name||'Error', requests:[], rank:{{}}, cy_list:{{}}, related:[]}}
}}
bundle.task_space_id = task.id
bundle.duration_ms = Date.now() - startedAt
cliLog('XYUQING_RESULT_JSON=' + JSON.stringify(bundle))
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one read-only Xiaoying signal round")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--business-date")
    parser.add_argument("--task-space", default="xyuqing-x3-bearer")
    parser.add_argument("--ui-task-space", default="xyuqing-x4-ui")
    parser.add_argument("--ego-executable", default="ego-browser")
    parser.add_argument("--simulate-primary-schema-failure", action="store_true")
    args = parser.parse_args(argv)
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    business_date = args.business_date or now.date().isoformat()
    try:
        result = run_live_round(
            data_dir=args.data_dir,
            business_date=business_date,
            collected_at=now.isoformat(),
            task_space=args.task_space,
            ui_task_space=args.ui_task_space,
            ego_executable=args.ego_executable,
            simulate_primary_schema_failure=args.simulate_primary_schema_failure,
        )
    except XyuqingSourceError as error:
        print(json.dumps({"status": "error", "error": redact_sensitive_text(str(error))}))
        return 1
    print(json.dumps({"status": "ok", **result}, ensure_ascii=False))
    return 0


def _require_json_object(payload: object) -> dict[str, Any]:
    if isinstance(payload, str):
        if "<html" in payload.lower() or "type='password'" in payload.lower():
            raise XyuqingAuthRequired("XYUQING_AUTH_REQUIRED")
        raise XyuqingSchemaError("xyuqing response must be JSON")
    if not isinstance(payload, dict):
        raise XyuqingSchemaError("xyuqing response must be an object")
    require_auth_ok(token_present=True, http_status=200, payload=payload)
    data = payload.get("data")
    if not isinstance(data, dict):
        raise XyuqingSchemaError("xyuqing response data must be an object")
    return data


def _require_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise XyuqingSchemaError(f"xyuqing response data.{key} must be an array")
    return value


def _timestamp(value: object, fallback: str) -> str:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=UTC).isoformat()
    return fallback


def _signal_topic_key(signal: dict[str, Any]) -> tuple[str, str]:
    platform = str(signal.get("platform") or "").strip().lower()
    topic = " ".join(str(signal.get("topic") or "").split()).lower()
    if not platform or not topic:
        raise XyuqingSchemaError("signal is missing platform or topic")
    return platform, topic


def _merge_signal(existing: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    merged = {**existing, **current}
    merged["signal_id"] = existing["signal_id"]
    merged["first_seen_at"] = min(
        str(existing.get("first_seen_at") or current.get("first_seen_at")),
        str(current.get("first_seen_at") or existing.get("first_seen_at")),
    )
    merged["last_seen_at"] = str(
        current.get("collected_at") or current.get("last_seen_at") or existing.get("last_seen_at")
    )
    old_peak = existing.get("peak_rank")
    new_rank = current.get("current_rank")
    if isinstance(old_peak, (int, float)) and isinstance(new_rank, (int, float)):
        merged["peak_rank"] = min(old_peak, new_rank)
    merged["related_source_urls"] = list(
        dict.fromkeys(
            [
                *existing.get("related_source_urls", []),
                *current.get("related_source_urls", []),
            ]
        )
    )
    return merged


if __name__ == "__main__":
    raise SystemExit(main())
