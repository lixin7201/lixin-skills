from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from statistics import median
from typing import Any
from zoneinfo import ZoneInfo

from .storage import atomic_write_json, atomic_write_text, read_json
from .xyuqing_source import (
    XyuqingAuthRequired,
    XyuqingNetworkError,
    XyuqingRateLimited,
    XyuqingSchemaError,
    _run_ego_script,
    classify_locality,
    parse_post_list_response,
    redact_sensitive_text,
)


PLAN_NAME = "宜宾热点监控"
SHANGHAI = ZoneInfo("Asia/Shanghai")
SCHEMA_VERSION = "rising-monitor-state-v1"
POLICY_VERSION = "hotspot-policy-v1"
HOT_NOW_THRESHOLDS = {
    "comment_count": 5,
    "like_count": 20,
    "share_count": 3,
    "view_count": 1000,
}
DEFAULT_FACT_DB = Path("/Users/REPLACE_ME/.openclaw/workspace/hotspot-radar/data/v3/radar.db")
METRIC_FIELDS = (
    "like_count",
    "comment_count",
    "share_count",
    "respond_count",
    "view_count",
    "collect_count",
    "repost_count",
)
IDENTITY_FIELDS = {
    "nickname",
    "user_id",
    "unique_user_id",
    "avatar",
    "user_url",
    "short_id",
}
CREDENTIAL_FIELDS = {
    "authorization", "cookie", "token", "password", "api_key", "apikey", "secret",
}
LOCATION_TERMS = {
    "宜宾", "翠屏", "叙州", "南溪", "江安", "长宁", "高县", "筠连", "珙县", "兴文", "屏山", "李庄",
    "三江新区", "临港", "中渡口", "马边", "旺苍", "成都", "泸州", "乐山", "广元",
}
YIBIN_LOCATION_TERMS = {
    "宜宾", "翠屏", "叙州", "南溪", "江安", "长宁", "高县", "筠连", "珙县", "兴文", "屏山",
    "李庄", "三江新区", "临港", "高新区", "中渡口",
}
LOW_RISK_HOLD_PATTERN = re.compile(
    r"事故|意外|伤亡|受伤|死亡|遇难|\d+死|\d+伤|未成年|儿童|孩子|学生|校园|"
    r"暴雨|强降雨|雷电|大风|气象台|预警|山洪|洪水|水灾|灾情|被淹|淹没|内涝|救援|垮塌|坍塌|塌方|房屋安全|升学宴|求助|投诉|举报|爆料|维权|"
    r"医疗|医院|医生|护士|疾病|病残|津贴|药品|手术|驼背|法律|法治|法院|律师|公安|拘留|行政处罚|违法|罚款|"
    r"金融|贷款|负债|投资|理财|借钱不还|欠钱|请认准这个人|隐私|失踪|诈骗|纠纷|小孩|"
    r"强奸|性侵|抑郁|烈士|被盗|被偷|噪音扰民|地震|震感|恐慌|焦虑|"
    r"落水|溺水|营救|乱流|惨剧|要了命|酒席|亲子鉴定|DNA|骗|骗局|"
    r"(?:[0-9一二三四五六七八九十]{1,3})岁|小学|中学|高中|高考|升学|生学宴|低保"
)
UGC_DISALLOWED_PATTERN = re.compile(
    r"\[REDACTED_PHONE\]|广告|软文|SEO|咨询热线|微信同号|二维码|小程序|线上预约|机构合集|"
    r"求带\s*ID|身份证|快手号|抖音号|关注获赞|大促|娱乐圈|代言|黑粉|脱粉|粉丝|艺人|演员|"
    r"离婚|单身汉|小少妇|蛆|老公|家政|注册资本|法定代表人|股权|成立新公司|中国政府网|节气|处暑|"
    r"(?:路|街|巷|大道)\d{1,5}号|"
    r"寻找.{0,30}(?:女士|先生|小姐|个人|这个人)|"
    r"(?<!\d)1[3-9]\d{2}\*{2,}\d{0,4}(?!\d)|"
    r"\d{1,3}°\d{1,2}['′]\d{1,2}(?:[\"″])?[NSEW]?"
)
TRAILING_LOCATION_PATTERN = re.compile(
    r"(?:📍|IP属地[:：]?|账号定位[:：]?|定位[:：]?)[^。！？\n]{0,50}$"
)
UGC_SOURCE_FOOTER_PATTERN = re.compile(
    r"(?:来源|编辑|责编|下载|扫码|(?:嗨)?[\u4e00-\u9fffA-Za-z0-9]{1,16}APP)[:：]?[^。！？\n]{0,100}$",
    re.IGNORECASE,
)
FACT_EVENT_GROUPS = {
    "weather": ("暴雨", "强降雨", "洪水", "水灾", "山洪", "内涝", "气象", "预警", "被淹"),
    "relic": ("文物", "石刻", "造像", "佛子岩", "被盗"),
    "medical": ("医疗", "医院", "医生", "庸医", "疾病", "药品", "就诊", "肝"),
    "consumption": ("消费", "商场", "价格", "购物", "促销"),
    "construction": ("施工", "建设", "更新", "项目", "启动", "片区", "改造"),
    "accident": ("事故", "坍塌", "垮塌", "伤亡", "死亡", "受伤", "女儿墙", "升学宴"),
    "activity": ("活动", "音乐会", "上新", "举办", "开幕", "启幕"),
    "transport": ("公交", "交通", "道路", "高铁", "车站", "充电站"),
}
GENERIC_FACT_TERMS = {"施工", "建设", "项目", "交通", "道路", "活动", "发布", "启动", "更新"}
EMBEDDED_IDENTITY_PATTERN = re.compile(
    r"(?:账号昵称|用户ID|用户平台号|联系电话|手机号|微信号)[:：]"
)
PHONE_PATTERN = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")


class RisingMonitorError(RuntimeError):
    pass


def parse_plan_list(payload: object, *, plan_name: str = PLAN_NAME) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise RisingMonitorError("plan/list response root must be an object")
    if payload.get("code") in {20001, "20001"}:
        raise XyuqingAuthRequired("XYUQING_AUTH_REQUIRED")
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise RisingMonitorError("plan/list response data must be an array")
    matches = [plan for plan in _iter_plans(rows) if str(plan.get("name") or "") == plan_name]
    if len(matches) != 1:
        raise RisingMonitorError(f"expected exactly one plan named {plan_name}, got {len(matches)}")
    plan = matches[0]
    plan_id = str(plan.get("id") or "").strip()
    plan_id_hash = str(plan.get("plan_id_hash") or "").strip().lower()
    if plan_id_hash and not re.fullmatch(r"[0-9a-f]{64}", plan_id_hash):
        raise RisingMonitorError("matched plan has invalid id hash")
    if not plan_id and not plan_id_hash:
        raise RisingMonitorError("matched plan is missing id hash")
    query_text = _first_text(plan, ("word", "word_combination", "analyze_word", "name")) or plan_name
    return {
        "name": plan_name,
        "plan_id_hash": plan_id_hash or _sha256(plan_id),
        "query_hash": _sha256(query_text),
        "metadata_fields": sorted(
            key for key in plan.keys() if key not in IDENTITY_FIELDS and not key.endswith("_id")
        ),
    }


def sanitize_content_item(row: dict[str, Any], *, collected_at: str) -> dict[str, Any]:
    title = _sanitize_persisted_text(row.get("title") or row.get("desc") or "")
    content = _sanitize_persisted_text(row.get("content") or row.get("copy_text") or row.get("desc") or "")
    platform = _clean_text(row.get("platform") or row.get("platform_name") or "unknown")
    source_url = _clean_text(row.get("url") or "")
    stable = _first_text(row, ("unique_id", "unity_id", "similar_id", "url", "post_id"))
    identity = "|".join((platform, stable or title or content, source_url))
    evidence = {
        "title": title,
        "content": content,
        "poi_name": row.get("poi_name"),
        "location": row.get("location"),
        "ip_location": row.get("ip_location"),
        "source_name": row.get("source_name"),
    }
    metrics = {field: _number_or_none(row.get(field)) for field in METRIC_FIELDS}
    risk_text = " ".join((title, content))
    return {
        "content_id": _sha256(identity),
        "identity_aliases": _identity_aliases(row),
        "title": title[:160],
        "content_excerpt": content[:240],
        "body_snapshot": content,
        "body_hash": _sha256(content) if content else "",
        "author_type": _clean_text(row.get("author_type") or "UNKNOWN"),
        "platform": platform,
        "platform_name": _clean_text(row.get("platform_name") or ""),
        "poi_name": _sanitize_persisted_text(row.get("poi_name") or ""),
        "source_name": _sanitize_persisted_text(row.get("source_name") or ""),
        "source_url": source_url,
        "images": _image_urls(row),
        "published_at": _clean_text(row.get("post_create_time") or row.get("create_time") or ""),
        "collected_at": collected_at,
        "locality_state": classify_locality(evidence),
        "risk_state": _classify_risk(risk_text),
        "age_bucket": _age_bucket(row, collected_at),
        "metrics": metrics,
        "policy_version": POLICY_VERSION,
    }


def sanitize_comment_item(row: dict[str, Any]) -> dict[str, Any]:
    comment = row.get("comment") if isinstance(row.get("comment"), dict) else {}
    origin = row.get("origin") if isinstance(row.get("origin"), dict) else {}
    content = _sanitize_persisted_text(row.get("content") or comment.get("content") or "")
    origin_aliases = _identity_aliases(origin)
    return {
        "comment_id": _sha256(_first_text(row, ("unique_id", "url", "post_id")) or content),
        "content_excerpt": content[:160],
        "source_url": _clean_text(row.get("url") or comment.get("url") or ""),
        "origin_aliases": origin_aliases,
        "origin_event_id": _sha256("|".join(origin_aliases)) if origin_aliases else "",
        "origin_title": _sanitize_persisted_text(origin.get("title") or "")[:160],
        "signal_role": "AUDIENCE_SIGNAL_ONLY",
    }


def associate_comments_by_content(
    items: list[dict[str, Any]], comments: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    output = {str(item["content_id"]): [] for item in items}
    alias_to_content: dict[str, set[str]] = {}
    for item in items:
        content_id = str(item["content_id"])
        for alias in item.get("identity_aliases", []):
            alias_to_content.setdefault(str(alias), set()).add(content_id)
    for comment in comments:
        matches = {
            content_id
            for alias in comment.get("origin_aliases", [])
            if str(alias) in alias_to_content
            for content_id in alias_to_content[str(alias)]
        }
        if len(matches) == 1:
            output[next(iter(matches))].append(comment)
        elif comment.get("origin_event_id"):
            output.setdefault(str(comment["origin_event_id"]), []).append(comment)
    return output


def update_watchlist(
    state: dict[str, Any],
    items: list[dict[str, Any]],
    *,
    collected_at: str,
    max_items: int = 200,
    window_hours: int = 6,
) -> dict[str, Any]:
    now = _parse_time(collected_at)
    cutoff = now - timedelta(hours=window_hours)
    by_id: dict[str, dict[str, Any]] = {
        str(item.get("content_id")): item
        for item in state.get("items", [])
        if isinstance(item, dict) and item.get("content_id")
    }
    for item in items:
        content_id = str(item["content_id"])
        current = by_id.get(content_id)
        snapshot = {"collected_at": collected_at, **item["metrics"]}
        if current is None:
            current = {
                key: item.get(key)
                for key in (
                    "content_id",
                    "identity_aliases",
                    "title",
                    "content_excerpt",
                    "body_snapshot",
                    "body_hash",
                    "author_type",
                    "platform",
                    "platform_name",
                    "poi_name",
                    "source_name",
                    "source_url",
                    "images",
                    "published_at",
                    "locality_state",
                    "risk_state",
                    "age_bucket",
                    "policy_version",
                )
            }
            current["first_seen_at"] = collected_at
            current["snapshots"] = []
            by_id[content_id] = current
        current["last_seen_at"] = collected_at
        for key in (
            "title",
            "content_excerpt",
            "body_snapshot",
            "body_hash",
            "author_type",
            "identity_aliases",
            "platform",
            "platform_name",
            "poi_name",
            "source_name",
            "source_url",
            "images",
            "published_at",
            "locality_state",
            "risk_state",
            "age_bucket",
            "policy_version",
        ):
            current[key] = item.get(key)
        snapshots = [
            snap
            for snap in current.get("snapshots", [])
            if isinstance(snap, dict) and _parse_time(str(snap.get("collected_at"))) >= cutoff
        ]
        if not snapshots or snapshots[-1].get("collected_at") != collected_at:
            snapshots.append(snapshot)
        else:
            snapshots[-1] = snapshot
        current["snapshots"] = snapshots
    for current in by_id.values():
        _reapply_current_policy(current, collected_at=collected_at)
    kept = [
        item
        for item in by_id.values()
        if _parse_time(str(item.get("last_seen_at") or collected_at)) >= cutoff
    ]
    kept.sort(key=_watchlist_sort_key, reverse=True)
    kept = kept[:max_items]
    return {
        "schema_version": SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "updated_at": collected_at,
        "watchlist_count": len(kept),
        "items": kept,
    }


def detect_rising_candidates(state: dict[str, Any]) -> list[dict[str, Any]]:
    items = [item for item in state.get("items", []) if isinstance(item, dict)]
    deltas = {str(item.get("content_id")): _interaction_delta(item) for item in items}
    groups: dict[tuple[str, str], list[float]] = {}
    for item in items:
        delta = deltas.get(str(item.get("content_id")))
        if delta is None:
            continue
        groups.setdefault(
            (str(item.get("platform") or ""), str(item.get("age_bucket") or "")), []
        ).append(delta)

    candidates: list[dict[str, Any]] = []
    for item in items:
        content_id = str(item.get("content_id") or "")
        delta = deltas.get(content_id)
        score = 0
        reasons: list[str] = []
        if item.get("locality_state") == "direct":
            score += 30
            reasons.append("YIBIN_DIRECT")
        if item.get("risk_state") != "LOW_RISK":
            candidates.append(_candidate(item, "HOLD", score, delta, ["RISK_HOLD"]))
            continue
        if delta is None:
            candidates.append(_candidate(item, "CALIBRATION_ONLY", score, delta, reasons))
            continue
        peers = groups.get((str(item.get("platform") or ""), str(item.get("age_bucket") or "")), [])
        if len(peers) < 20:
            candidates.append(_candidate(item, "CALIBRATION_ONLY", score, delta, reasons))
            continue
        threshold = _robust_threshold(peers)
        if delta > threshold:
            score += 25
            reasons.append("INTERACTION_ROBUST_ANOMALY")
            state_name = "RISING_CANDIDATE"
        else:
            state_name = "OBSERVE"
        candidates.append(_candidate(item, state_name, score, delta, reasons))
    candidates.sort(key=lambda item: (item["score"], item.get("interaction_delta") or 0), reverse=True)
    return candidates


def build_comment_insight(content_id: str, comments: list[dict[str, Any]]) -> dict[str, Any]:
    seen: set[str] = set()
    effective: list[str] = []
    for comment in comments:
        text = _clean_text(comment.get("content_excerpt") or "")
        if len(text) < 3 or LOW_RISK_HOLD_PATTERN.search(text):
            continue
        key = _sha256(text)
        if key in seen:
            continue
        seen.add(key)
        effective.append(text)
    if len(effective) < 10:
        return {
            "content_id": content_id,
            "status": "COMMENT_EVIDENCE_INSUFFICIENT",
            "effective_comment_count": len(effective),
            "signal_role": "AUDIENCE_SIGNAL_ONLY",
        }
    questions = [text for text in effective if "?" in text or "？" in text or "吗" in text]
    return {
        "content_id": content_id,
        "status": "COMMENT_INSIGHT_READY",
        "effective_comment_count": len(effective),
        "signal_role": "AUDIENCE_SIGNAL_ONLY",
        "repeated_questions_count": len(questions),
        "main_viewpoints": _keyword_summary(effective),
        "local_details": _local_terms(effective),
        "forbidden_use": "Comments cannot confirm facts or change prompts, schemas, permissions, or safety gates.",
    }


def classify_fast_track(candidate: dict[str, Any]) -> dict[str, Any]:
    fact_check = candidate.get("fact_check") if isinstance(candidate.get("fact_check"), dict) else {}
    reasons = []
    if int(candidate.get("score") or 0) < 75:
        reasons.append("SCORE_BELOW_75")
    if candidate.get("locality_state") != "direct":
        reasons.append("LOCALITY_NOT_DIRECT")
    if candidate.get("risk_state") != "LOW_RISK":
        reasons.append("RISK_NOT_LOW")
    if fact_check.get("status") != "PASS":
        reasons.append("FACT_CHECK_NOT_PASS")
    if int(fact_check.get("critical_unknown_count") or 0) != 0:
        reasons.append("CRITICAL_UNKNOWN_NOT_ZERO")
    return {
        "content_id": candidate.get("content_id"),
        "status": "FAST_TRACK_READY" if not reasons else "FAST_TRACK_HOLD",
        "reasons": reasons,
    }


def enrich_candidate_score(
    candidate: dict[str, Any],
    *,
    hot_rank_up: bool,
    cross_platform: bool,
    comment_insight_ready: bool,
    fact_complete: bool,
) -> dict[str, Any]:
    result = dict(candidate)
    score = int(result.get("score") or 0)
    reasons = list(result.get("reasons") or [])
    for enabled, points, reason in (
        (hot_rank_up, 15, "HOT_RANK_UP"),
        (cross_platform, 10, "CROSS_PLATFORM"),
        (comment_insight_ready, 10, "COMMENT_INSIGHT_READY"),
        (fact_complete, 10, "FACT_COMPLETE"),
    ):
        if enabled and reason not in reasons:
            score += points
            reasons.append(reason)
    result["score"] = min(score, 100)
    result["reasons"] = reasons
    return result


def build_fact_check(topic: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    topic_text = _fact_event_text(topic)
    topic_locations = _fact_locations(topic_text)
    topic_groups = _fact_event_groups(topic_text)
    topic_core = _fact_core_terms(topic_text, topic_groups)
    if not topic_locations or not topic_groups or not topic_core:
        return {"status": "NO_MATCH", "critical_unknown_count": 1, "evidence": []}
    matches = []
    for row in rows:
        if row.get("source_tier") not in {"P0", "P1", "P2"} or not row.get("source_url"):
            continue
        row_title = _fact_event_text(row.get("title", ""))
        haystack = _fact_event_text(f"{row.get('title', '')} {row.get('summary', '')}")
        shared_locations = topic_locations & _fact_locations(haystack)
        shared_groups = topic_groups & _fact_event_groups(haystack)
        shared_core = topic_core & _fact_core_terms(haystack, shared_groups)
        if not shared_locations or not shared_groups or not shared_core:
            continue
        distinctive = topic_core - GENERIC_FACT_TERMS
        if distinctive and not distinctive.intersection(
            _fact_core_terms(row_title, _fact_event_groups(row_title))
        ):
            continue
        if _longest_common_subject(topic_text, haystack) < 5:
            continue
        matches.append(
            {
                "raw_item_id": str(row.get("raw_item_id") or ""),
                "source_id": str(row.get("source_id") or ""),
                "source_tier": str(row.get("source_tier") or ""),
                "source_url": str(row.get("source_url") or ""),
            }
        )
    return {
        "status": "PASS" if matches else "NO_MATCH",
        "critical_unknown_count": 0 if matches else 1,
        "evidence": matches[:5],
    }


def build_daily_summary(
    *,
    collected_count: int,
    new_count: int,
    anomaly_count: int,
    comment_insight_count: int,
    draft_count: int,
    awaiting_confirmation_count: int,
    no_draft_reasons: list[str],
) -> str:
    reasons = "、".join(sorted(set(no_draft_reasons))) or "无"
    return (
        "# T0 每日运营摘要\n\n"
        f"- 采集数：{collected_count}\n"
        f"- 新增数：{new_count}\n"
        f"- 异常数：{anomaly_count}\n"
        f"- 评论洞察数：{comment_insight_count}\n"
        f"- 稿件数：{draft_count}\n"
        f"- 等待确认数：{awaiting_confirmation_count}\n"
        f"- 无稿原因：{reasons}\n"
    )


def build_operator_hotspot_board(
    candidates: list[dict[str, Any]],
    state: dict[str, Any],
    *,
    collected_at: str,
    limit: int = 20,
) -> str:
    state_by_id = {
        str(item.get("content_id")): item
        for item in state.get("items", [])
        if isinstance(item, dict) and item.get("content_id")
    }
    lines = [
        "# 宜宾起势热点看板",
        "",
        f"采集时间：{collected_at}",
        f"风险策略：{POLICY_VERSION}",
        "",
        "说明：互动变化必须来自至少两个真实快照；不足时明确标记“样本不足”。",
    ]
    reason_labels = {
        "YIBIN_DIRECT": "宜宾强相关",
        "INTERACTION_ROBUST_ANOMALY": "互动增速异常",
        "HOT_RANK_UP": "热榜上升",
        "CROSS_PLATFORM": "跨平台出现",
        "COMMENT_INSIGHT_READY": "评论洞察可用",
        "FACT_COMPLETE": "已有事实来源匹配",
        "RISK_HOLD": "风险题材暂停",
    }
    for index, candidate in enumerate(candidates[:limit], start=1):
        item = state_by_id.get(str(candidate.get("content_id")), {})
        title = str(candidate.get("title") or "（无标题）").replace("\n", " ")
        effective_candidate = candidate
        snapshots = [row for row in item.get("snapshots", []) if isinstance(row, dict)]
        latest = snapshots[-1] if snapshots else {}
        current = "、".join(
            (
                f"阅读{_metric_display(latest.get('view_count'))}",
                f"点赞{_metric_display(latest.get('like_count'))}",
                f"评论{_metric_display(latest.get('comment_count'))}",
                f"转发{_metric_display(_first_metric(latest, 'repost_count', 'share_count'))}",
            )
        )
        if len(snapshots) < 2:
            change = "样本不足"
        else:
            previous = snapshots[-2]
            change = "、".join(
                (
                    f"阅读{_metric_change(previous.get('view_count'), latest.get('view_count'))}",
                    f"点赞{_metric_change(previous.get('like_count'), latest.get('like_count'))}",
                    f"评论{_metric_change(previous.get('comment_count'), latest.get('comment_count'))}",
                    f"转发{_metric_change(_first_metric(previous, 'repost_count', 'share_count'), _first_metric(latest, 'repost_count', 'share_count'))}",
                )
            )
        selected = "入选" if classify_fast_track(effective_candidate)["status"] == "FAST_TRACK_READY" else "未入选"
        reason_codes = list(candidate.get("reasons", []))
        reasons = "、".join(reason_labels.get(str(reason), str(reason)) for reason in reason_codes) or "暂无正向信号"
        current_state = candidate.get("rising_state") or "OBSERVE"
        if selected == "未入选":
            reasons = f"{reasons}；当前{current_state}"
        lines.extend(
            [
                "",
                f"## {index}. {title}",
                "",
                f"- 来源平台：{candidate.get('platform') or '未知'}",
                f"- 发布时间：{item.get('published_at') or '供应商未提供'}",
                f"- 原文链接：{candidate.get('source_url') or '供应商未提供'}",
                f"- 当前互动：{current}",
                f"- 本轮变化量：{change}",
                f"- 本地相关性：{candidate.get('locality_state') or '未知'}",
                f"- 热点/选题评分：{int(candidate.get('score') or 0)}",
                f"- 当前状态：{current_state}",
                f"- 筛选结论：{selected}；{reasons}",
            ]
        )
    return "\n".join(lines) + "\n"


def load_fact_rows(db_path: str | Path, *, limit: int = 5000) -> list[dict[str, Any]]:
    source = Path(db_path).expanduser().resolve()
    if not source.is_file():
        return []
    uri = f"file:{source.as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT r.id AS raw_item_id,r.source_id,r.canonical_url AS source_url,
                   r.title,r.summary,r.raw_text,r.published_at,r.first_seen_at,s.scope,s.layer
            FROM raw_items r
            JOIN sources s ON s.id=r.source_id
            WHERE r.is_noise=0
              AND s.enabled=1 AND s.configured=1 AND s.can_confirm_fact=1
              AND s.layer IN ('official_fact','authoritative_media')
              AND s.scope IN ('yibin','sichuan','national','mixed')
              AND COALESCE(r.published_at,r.first_seen_at) >= datetime('now','-7 days')
            ORDER BY COALESCE(r.published_at,r.first_seen_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        connection.close()
    tier = {"yibin": "P0", "sichuan": "P1", "national": "P2", "mixed": "P2"}
    return [
        {
            "raw_item_id": str(row["raw_item_id"]),
            "source_id": str(row["source_id"]),
            "source_tier": tier.get(str(row["scope"]), "P2"),
            "title": _clean_text(row["title"]),
            "summary": _clean_text(row["summary"]),
            "raw_text": _clean_text(row["raw_text"]),
            "published_at": _clean_text(row["published_at"] or row["first_seen_at"]),
            "source_url": _clean_text(row["source_url"]),
        }
        for row in rows
    ]


def run_round(
    bundle: dict[str, Any],
    *,
    data_dir: str | Path,
    business_date: str,
    evidence_dir: str | Path,
    round_number: int,
    collected_at: str,
    hotspot_policy: Any | None = None,
) -> dict[str, Any]:
    evidence_path = Path(evidence_dir) / "rounds" / f"round-{round_number:03d}.json"
    if evidence_path.exists():
        raise RisingMonitorError(f"round evidence already exists: round-{round_number:03d}.json")
    if bundle.get("auth_status") == "AUTH_REQUIRED":
        raise XyuqingAuthRequired("XYUQING_AUTH_REQUIRED")
    if bundle.get("auth_status") == "RATE_LIMITED":
        raise XyuqingRateLimited("XYUQING_RATE_LIMITED")
    if bundle.get("auth_status") == "NETWORK_ERROR":
        raise XyuqingNetworkError("XYUQING_NETWORK_ERROR")
    if bundle.get("auth_status") not in {None, "AUTH_OK"}:
        raise XyuqingSchemaError("rising monitor bundle has unknown auth status")
    plan = parse_plan_list(bundle.get("plan_list"))
    discovery_payload = bundle.get("discovery_content") or bundle.get("content")
    watch_payload = bundle.get("watch_content", {"code": 0, "data": {"list": []}})
    discovery_rows = parse_post_list_response(discovery_payload, return_type=1)
    watch_degraded_reasons: list[str] = []
    try:
        watch_rows = parse_post_list_response(watch_payload, return_type=1)
    except XyuqingSchemaError:
        watch_rows = []
        watch_degraded_reasons.append("WATCH_SCHEMA_DEGRADED")
    watch_contract = bundle.get("contract", {}).get("watch_query", {})
    if isinstance(watch_contract, dict) and watch_contract.get("provided") and not watch_contract.get("valid"):
        watch_degraded_reasons.append("WATCH_QUERY_DEGRADED")
    discovery_items = _deduplicate_sanitized(
        [sanitize_content_item(row, collected_at=collected_at) for row in discovery_rows]
    )
    watch_items = _deduplicate_sanitized(
        [sanitize_content_item(row, collected_at=collected_at) for row in watch_rows]
    )
    items = _deduplicate_sanitized([*discovery_items, *watch_items])

    root = Path(data_dir) / business_date / "rising-monitor"
    state_path = root / "state.json"
    previous_state = read_json(state_path) if state_path.exists() else _previous_day_state(
        Path(data_dir), business_date
    )
    previous_ids = {
        str(item.get("content_id"))
        for item in previous_state.get("items", [])
        if isinstance(item, dict) and item.get("content_id")
    }
    overlap_ids = {str(item["content_id"]) for item in items} & previous_ids
    state = update_watchlist(previous_state, items, collected_at=collected_at)
    candidates = detect_rising_candidates(state)
    latest_payload = {
        "schema_version": "rising-monitor-latest-v1",
        "policy_version": POLICY_VERSION,
        "business_date": business_date,
        "collected_at": collected_at,
        "plan": plan,
        "candidate_count": len(items),
        "items": items,
    }
    try:
        comment_rows = parse_post_list_response(
            bundle.get("comments", {"code": 0, "data": {"list": []}}), return_type=1
        )
    except XyuqingSchemaError:
        comment_rows = []
        watch_degraded_reasons.append("COMMENT_SCHEMA_DEGRADED")
    comments = [sanitize_comment_item(row) for row in comment_rows]
    state_items = [item for item in state.get("items", []) if isinstance(item, dict)]
    comments_by_content = associate_comments_by_content(state_items, comments)
    state_ids = {str(item.get("content_id")) for item in state_items}
    top_ids = [
        str(candidate["content_id"])
        for candidate in candidates
        if candidate.get("locality_state") == "direct"
        and candidate.get("risk_state") == "LOW_RISK"
    ][:5]
    insights = [
        build_comment_insight(content_id, comments_by_content.get(content_id, []))
        for content_id in top_ids
    ]
    insights_by_id = {str(item["content_id"]): item for item in insights}
    fact_rows = bundle.get("fact_rows") if isinstance(bundle.get("fact_rows"), list) else []
    hot_signals = _load_hot_signals(Path(data_dir) / business_date / "xyuqing-signals.json")
    enriched_candidates = []
    for candidate in candidates:
        candidate["fact_check"] = build_fact_check(str(candidate.get("title") or ""), fact_rows)
        enriched_candidates.append(
            enrich_candidate_score(
                candidate,
                hot_rank_up=_has_hot_signal(candidate, hot_signals),
                cross_platform=_has_cross_platform(candidate, candidates),
                comment_insight_ready=insights_by_id.get(str(candidate["content_id"]), {}).get("status") == "COMMENT_INSIGHT_READY",
                fact_complete=candidate["fact_check"]["status"] == "PASS",
            )
        )
    for row in fact_rows:
        daily_candidate = _daily_fact_candidate(row, collected_at)
        if daily_candidate is not None:
            enriched_candidates.append(daily_candidate)
    candidates = sorted(enriched_candidates, key=lambda item: (item["score"], item.get("interaction_delta") or 0), reverse=True)
    _attach_editorial_images(candidates, Path(data_dir), business_date)
    channels_payload = build_business_channels(
        candidates,
        collected_at=collected_at,
        watch_degraded_reasons=watch_degraded_reasons,
        active_history=_active_history_events(Path(data_dir)),
        hotspot_policy=hotspot_policy,
    )
    daily_pool_candidates = channels_payload["daily_value"]
    daily_pool_payload = {
        "schema_version": "rising-daily-candidate-pool-v1",
        "policy_version": POLICY_VERSION,
        "business_date": business_date,
        "collected_at": collected_at,
        "candidate_count": len(daily_pool_candidates),
        "target_range": [8, 12],
        "shortage_reason": (
            None
            if len(daily_pool_candidates) >= 8
            else "质量门后不足8条，不凑数、不降低事实或风险门"
        ),
        "candidates": daily_pool_candidates,
    }
    rising_payload = {
        "schema_version": "rising-monitor-candidates-v2",
        "policy_version": POLICY_VERSION,
        "business_date": business_date,
        "collected_at": collected_at,
        "candidates": candidates,
        "fast_track": [classify_fast_track(candidate) for candidate in candidates],
    }
    insight_payload = {
        "schema_version": "rising-monitor-comment-insights-v1",
        "policy_version": POLICY_VERSION,
        "business_date": business_date,
        "collected_at": collected_at,
        "insights": insights,
    }
    fast_ready = [
        item for item in rising_payload["fast_track"] if item["status"] == "FAST_TRACK_READY"
    ]
    run_report = {
        "schema_version": "rising-monitor-run-report-v1",
        "policy_version": POLICY_VERSION,
        "business_date": business_date,
        "round_number": round_number,
        "collected_at": collected_at,
        "status": "RISING_MONITOR_NO_GO" if not items else "CALIBRATION_NO_AUTO_PUBLISH",
        "request_count": len(bundle.get("requests", [])),
        "requests": _safe_requests(bundle.get("requests", [])),
        "plan_name": plan["name"],
        "plan_id_hash": plan["plan_id_hash"],
        "latest_count": len(items),
        "discovery_count": len(discovery_items),
        "watch_refresh_count": len(watch_items),
        "overlap_count": len(overlap_ids),
        "new_count": sum(1 for item in items if item["content_id"] not in previous_ids),
        "comment_count": len(comments),
        "origin_grouped_comment_count": sum(len(rows) for rows in comments_by_content.values()),
        "candidate_origin_match_count": sum(
            len(rows) for content_id, rows in comments_by_content.items() if content_id in state_ids
        ),
        "anonymous_event_group_count": sum(
            1 for content_id, rows in comments_by_content.items() if content_id not in state_ids and rows
        ),
        "watchlist_count": state["watchlist_count"],
        "rising_candidate_count": sum(
            1 for item in candidates if item["rising_state"] == "RISING_CANDIDATE"
        ),
        "interaction_delta_count": sum(
            1 for item in candidates if item.get("interaction_delta") is not None
        ),
        "positive_interaction_delta_count": sum(
            1 for item in candidates if float(item.get("interaction_delta") or 0) > 0
        ),
        "calibration_only_count": sum(
            1 for item in candidates if item["rising_state"] == "CALIBRATION_ONLY"
        ),
        "comment_insight_ready_count": sum(
            1 for item in insights if item["status"] == "COMMENT_INSIGHT_READY"
        ),
        "fast_track_ready_count": len(fast_ready),
        "fact_check_pass_count": sum(1 for item in candidates if item["fact_check"]["status"] == "PASS"),
        "daily_pool_candidate_count": len(daily_pool_candidates),
        "hot_now_candidate_count": len(channels_payload["hot_now"]),
        "rising_watch_candidate_count": len(channels_payload["rising_watch"]),
        "event_count": int(channels_payload["event_count"]),
        "merged_event_count": int(channels_payload["merged_event_count"]),
        "watch_status": "WATCH_DEGRADED" if watch_degraded_reasons else "WATCHING",
        "watch_degraded_reasons": sorted(set(watch_degraded_reasons)),
        "qianfan_called": False,
        "x5_heartbeat_modified": False,
        "auto_comment_modified": False,
        "credential_or_identity_leak": False,
    }
    leak_paths = _forbidden_identity_paths(
        {"latest": latest_payload, "rising": rising_payload, "insights": insight_payload}
    )
    run_report["credential_or_identity_leak"] = bool(leak_paths)
    draft_count, awaiting_confirmation_count = _daily_content_counts(
        Path(data_dir), business_date
    )
    run_report["draft_count"] = draft_count
    run_report["awaiting_confirmation_count"] = awaiting_confirmation_count
    if run_report["credential_or_identity_leak"]:
        raise RisingMonitorError(
            "credential or identity leak detected in persisted payload: "
            + ",".join(leak_paths[:5])
        )
    atomic_write_json(state_path, state)
    atomic_write_json(root / "latest-candidates.json", latest_payload)
    atomic_write_json(root / "rising-candidates.json", rising_payload)
    atomic_write_json(root / "business-channels.json", channels_payload)
    atomic_write_json(root / "daily-candidate-pool.json", daily_pool_payload)
    atomic_write_json(root / "comment-insights.json", insight_payload)
    atomic_write_json(root / "run-report.json", run_report)
    no_draft_reasons = sorted(
        {
            reason
            for item in rising_payload["fast_track"]
            for reason in item.get("reasons", [])
        }
    )
    atomic_write_text(
        root / "daily-operations-summary.md",
        build_daily_summary(
            collected_count=len(items),
            new_count=run_report["new_count"],
            anomaly_count=run_report["rising_candidate_count"],
            comment_insight_count=run_report["comment_insight_ready_count"],
            draft_count=draft_count,
            awaiting_confirmation_count=awaiting_confirmation_count,
            no_draft_reasons=no_draft_reasons,
        ),
    )
    atomic_write_text(
        root / "operator-hotspot-board.md",
        build_operator_hotspot_board(candidates, state, collected_at=collected_at),
    )
    atomic_write_json(
        evidence_path,
        {
            "schema_version": "rising-monitor-round-evidence-v1",
            "business_date": business_date,
            "round_number": round_number,
            "collected_at": collected_at,
            "plan_metadata": plan,
            "contract": bundle.get("contract", {}),
            "run_report": run_report,
        },
    )
    return run_report


def fetch_live_bundle(
    *,
    task_space: str = "rising-monitor-t0",
    ego_executable: str = "ego-browser",
    timeout_seconds: int = 120,
    watch_target: dict[str, str] | None = None,
) -> dict[str, Any]:
    return _run_ego_script(
        _ego_script(task_space, watch_target=watch_target),
        ego_executable=ego_executable,
        timeout_seconds=timeout_seconds,
    )


def _iter_plans(groups: list[Any]):
    for group in groups:
        if not isinstance(group, dict):
            continue
        children = group.get("children")
        if isinstance(children, list):
            for child in children:
                if isinstance(child, dict):
                    yield child
        elif group.get("name"):
            yield group


def _candidate(
    item: dict[str, Any],
    state: str,
    score: int,
    delta: float | None,
    reasons: list[str],
) -> dict[str, Any]:
    latest = item.get("snapshots", [])[-1] if item.get("snapshots") else {}
    return {
        "content_id": item.get("content_id"),
        "title": item.get("title"),
        "platform": item.get("platform"),
        "source_url": item.get("source_url"),
        "images": item.get("images", []),
        "body_snapshot": item.get("body_snapshot", ""),
        "body_hash": item.get("body_hash", ""),
        "author_type": item.get("author_type", "UNKNOWN"),
        "snapshots": item.get("snapshots", []),
        "published_at": item.get("published_at"),
        "current_metrics": {
            field: latest.get(field) for field in METRIC_FIELDS if latest.get(field) is not None
        },
        "locality_state": item.get("locality_state"),
        "risk_state": item.get("risk_state"),
        "age_bucket": item.get("age_bucket"),
        "interaction_delta": delta,
        "rising_state": state,
        "score": score,
        "reasons": reasons,
        "fact_check": {"status": "MISSING", "critical_unknown_count": 0},
        "policy_version": item.get("policy_version") or POLICY_VERSION,
    }


def build_business_channels(
    candidates: list[dict[str, Any]],
    *,
    collected_at: str,
    watch_degraded_reasons: list[str] | None = None,
    active_history: list[dict[str, Any]] | None = None,
    hotspot_policy: Any | None = None,
) -> dict[str, Any]:
    # ponytail: candidate pools are capped at 200; pairwise grouping is clearer than
    # a second semantic service. Upgrade only if this bound grows materially.
    groups: list[list[dict[str, Any]]] = []
    for candidate in candidates:
        group = next(
            (
                existing for existing in groups
                if _same_user_event(candidate, existing[0], collected_at)
            ),
            None,
        )
        if group is None:
            groups.append([candidate])
        else:
            group.append(candidate)

    events: list[dict[str, Any]] = []
    for sources in groups:
        sources = sorted(sources, key=_source_priority, reverse=True)
        primary = dict(sources[0])
        source_images = _non_synthetic_images(sources)
        if source_images:
            primary["images"] = source_images
            primary["source_media_state"] = "RESOLVED_WITH_IMAGES"
            primary["image_plan"] = [
                {
                    "path": path,
                    "placement": "正文段落之间",
                    "credit": "同事件公开现场图，发布前核验并本地化",
                    "rights": "SOURCE_MEDIA_REQUIRES_LOCALIZATION",
                }
                for path in source_images
            ]
        event_id = _event_id(primary, collected_at)
        risk_order = {"LOW_RISK": 0, "VERIFY_FIRST": 1, "HOLD": 2, "HARD_HOLD": 3}
        strictest_risk = max(
            (str(item.get("risk_state") or "HARD_HOLD") for item in sources),
            key=lambda value: risk_order.get(value, 3),
        )
        localities = {str(item.get("locality_state") or "unknown") for item in sources}
        risk_reasons = sorted({
            str(reason)
            for item in sources
            for reason in (item.get("risk_reasons") or [])
            if str(reason)
        })
        platforms = sorted({str(item.get("platform") or "unknown") for item in sources})
        platform_max: dict[str, dict[str, float]] = {}
        for source in sources:
            platform = str(source.get("platform") or "unknown")
            metrics = source.get("current_metrics") if isinstance(source.get("current_metrics"), dict) else {}
            maximum = platform_max.setdefault(platform, {})
            for field, value in metrics.items():
                number = _number_or_none(value)
                if number is not None:
                    maximum[field] = max(float(maximum.get(field, number)), float(number))
        event = {
            **primary,
            "event_id": event_id,
            "risk_state": strictest_risk,
            "risk_reasons": risk_reasons,
            "locality_state": "conflict" if len(localities) > 1 else next(iter(localities)),
            "source_count": len(sources),
            "platform_count": len(platforms),
            "platforms": platforms,
            "platform_max_metrics": platform_max,
            "source_aliases": [
                {
                    "content_id": item.get("content_id"),
                    "title": item.get("title"),
                    "platform": item.get("platform"),
                    "source_url": item.get("source_url"),
                }
                for item in sources
            ],
        }
        events.append(event)

    history = [item for item in (active_history or []) if isinstance(item, dict)]
    before_history = len(events)
    events = [
        event for event in events
        if not any(
            _same_user_event(event, old, collected_at)
            or (
                old.get("_explicit_exclusion") is True
                and str(event.get("event_id") or "")
                == str(old.get("event_id") or "")
            )
            for old in history
        )
    ]

    peer_totals: dict[tuple[str, str], list[float]] = {}
    for event in events:
        peer_totals.setdefault(
            (str(event.get("platform") or ""), str(event.get("age_bucket") or "")), []
        ).append(_current_interaction(event))

    hot_now: list[dict[str, Any]] = []
    daily_value: list[dict[str, Any]] = []
    rising_watch: list[dict[str, Any]] = []
    ignored: list[dict[str, Any]] = []
    degraded = sorted(set(watch_degraded_reasons or []))
    for event in events:
        fact_ready = (
            isinstance(event.get("fact_check"), dict)
            and event["fact_check"].get("status") == "PASS"
        )
        body_snapshot = str(event.get("body_snapshot") or "")
        ugc_ready = bool(
            body_snapshot
            and event.get("body_hash") == _sha256(body_snapshot)
            and event.get("risk_state") == "LOW_RISK"
            and _ugc_discussion_ready(event)
        )
        eligible = (
            event.get("locality_state") == "direct"
            and event.get("risk_state") == "LOW_RISK"
            and (fact_ready or ugc_ready)
            and event.get("source_media_state") != "UNRESOLVED_SOURCE_MEDIA"
        )
        current = _current_interaction(event)
        peers = sorted(
            peer_totals.get(
                (str(event.get("platform") or ""), str(event.get("age_bucket") or "")),
                [],
            ),
            reverse=True,
        )
        rank = peers.index(current) + 1 if current in peers else len(peers) + 1
        peer_head = (
            current > 0
            and len(peers) >= 5
            and rank <= min(3, max(1, (len(peers) + 9) // 10))
        )
        hot_reasons = []
        if "HOT_RANK_UP" in event.get("reasons", []):
            hot_reasons.append("LOCAL_HOTLIST_HEAD")
        if peer_head:
            hot_reasons.append("PLATFORM_TIME_PEER_HEAD")
        if int(event.get("platform_count") or 0) >= 2 and current > 0:
            hot_reasons.append("CROSS_PLATFORM_WITH_INTERACTION")
        thresholds = {
            field: int(getattr(hotspot_policy, field, default))
            for field, default in HOT_NOW_THRESHOLDS.items()
        }
        threshold_evidence = _hot_now_threshold_evidence(event, thresholds)
        rising = classify_two_hour_rising(
            event.get("snapshots") or [],
            sample_points=int(getattr(hotspot_policy, "snapshot_points", 5)),
            interval_minutes=int(getattr(hotspot_policy, "snapshot_interval_minutes", 30)),
            positive_intervals=int(getattr(hotspot_policy, "rising_positive_intervals", 3)),
        )
        material_level = (
            "TITLE_LEVEL"
            if (
                not body_snapshot
                or "官方详情未提供文字正文" in body_snapshot
                or event.get("material_source") == "SUMMARY_FALLBACK"
            )
            else "BODY_LEVEL"
        )
        common = {
            "content_mode": "VERIFIED_FACT" if fact_ready else "UGC_DISCUSSION",
            "ready_status": (
                "SUPPLEMENT_REQUIRED" if material_level == "TITLE_LEVEL" else "READY_FOR_ANGLE"
            ),
            "material_level": material_level,
        }
        if eligible and hot_reasons and threshold_evidence:
            hot_now.append({
                **event, **common, "channel": "HOT_NOW", "origin_channel": "HOT_NOW",
                "channel_reasons": hot_reasons, "hot_now_threshold_evidence": threshold_evidence,
            })
        elif eligible and rising["status"] == "RISING_CONFIRMED":
            hot_now.append({
                **event, **common, "channel": "HOT_NOW", "origin_channel": "TWO_HOUR_RISING",
                "channel_reasons": ["TWO_HOUR_RISING"], "rising_evidence": rising,
                "hot_now_threshold_evidence": {},
            })
        elif eligible:
            daily_value.append(
                {
                    **event, **common, "channel": "DAILY_VALUE",
                    "origin_channel": "DAILY_VALUE" if fact_ready else "UGC_DISCUSSION_READY",
                    "channel_reasons": ["LOCAL_FACT_LOW_RISK" if fact_ready else "UGC_DISCUSSION_READY"],
                }
            )
        elif event.get("locality_state") == "direct" and event.get("risk_state") == "LOW_RISK":
            rising_watch.append(
                {
                    **event,
                    "channel": "RISING_WATCH",
                    "watch_status": "WATCH_DEGRADED" if degraded else "WATCHING",
                    "channel_reasons": (
                        ["SOURCE_MEDIA_UNRESOLVED"]
                        if event.get("source_media_state") == "UNRESOLVED_SOURCE_MEDIA"
                        else degraded or ["FACT_OR_TREND_CALIBRATION"]
                    ),
                }
            )
        else:
            reasons = []
            if event.get("locality_state") != "direct":
                reasons.append("LOCALITY_NOT_DIRECT")
            if event.get("risk_state") != "LOW_RISK":
                reasons.append("RISK_HOLD")
            ignored.append({**event, "channel": "IGNORE", "channel_reasons": reasons or ["LOW_VALUE"]})

    key = lambda item: (_current_interaction(item), int(item.get("source_count") or 0), int(item.get("score") or 0))
    hot_now.sort(key=key, reverse=True)
    daily_value.sort(
        key=lambda item: (
            int(item.get("score") or 0),
            str(item.get("published_at") or ""),
            int(item.get("source_count") or 0),
        ),
        reverse=True,
    )
    rising_watch.sort(key=key, reverse=True)
    ignored.sort(key=key, reverse=True)
    ready_for_angle = [
        item
        for item in hot_now + daily_value
        if item.get("ready_status") == "READY_FOR_ANGLE"
    ]
    return {
        "schema_version": "rising-business-channels-v1",
        "policy_version": POLICY_VERSION,
        "collected_at": collected_at,
        "status": "CALIBRATION_NO_AUTO_PUBLISH",
        "event_count": len(events),
        "independent_local_event_count": sum(
            1 for event in events if event.get("locality_state") == "direct"
        ),
        "ready_for_angle_count": len(ready_for_angle),
        "merged_event_count": sum(1 for event in events if int(event.get("source_count") or 0) > 1),
        "history_excluded_count": before_history - len(events),
        "watch_degraded_reasons": degraded,
        "ready_for_angle": ready_for_angle,
        "hot_now": hot_now[:10],
        "daily_value": daily_value[:20],
        "rising_watch": rising_watch[:20],
        "ignore_top10": ignored[:10],
    }


def rebuild_business_outputs(
    *,
    data_dir: str | Path,
    business_date: str,
    fact_rows: list[dict[str, Any]],
    collected_at: str,
    watch_degraded_reasons: list[str] | None = None,
    hotspot_policy: Any | None = None,
) -> dict[str, Any]:
    """Reclassify the latest persisted observation without another supplier call."""
    root = Path(data_dir) / business_date / "rising-monitor"
    state_path = root / "state.json"
    if not state_path.exists():
        raise RisingMonitorError("persisted rising-monitor state is missing")
    state = update_watchlist(read_json(state_path), [], collected_at=collected_at)
    candidates = detect_rising_candidates(state)
    hot_signals = _load_hot_signals(Path(data_dir) / business_date / "xyuqing-signals.json")
    enriched = []
    for candidate in candidates:
        candidate["fact_check"] = build_fact_check(str(candidate.get("title") or ""), fact_rows)
        enriched.append(
            enrich_candidate_score(
                candidate,
                hot_rank_up=_has_hot_signal(candidate, hot_signals),
                cross_platform=_has_cross_platform(candidate, candidates),
                comment_insight_ready=False,
                fact_complete=candidate["fact_check"]["status"] == "PASS",
            )
        )
    for row in fact_rows:
        candidate = _daily_fact_candidate(row, collected_at)
        if candidate is not None:
            enriched.append(candidate)
    candidates = sorted(
        enriched,
        key=lambda item: (int(item.get("score") or 0), item.get("interaction_delta") or 0),
        reverse=True,
    )
    _attach_editorial_images(candidates, Path(data_dir), business_date)
    channels = build_business_channels(
        candidates,
        collected_at=collected_at,
        watch_degraded_reasons=watch_degraded_reasons,
        active_history=_active_history_events(Path(data_dir)),
        hotspot_policy=hotspot_policy,
    )
    rising = {
        "schema_version": "rising-monitor-candidates-v2",
        "policy_version": POLICY_VERSION,
        "business_date": business_date,
        "collected_at": collected_at,
        "candidates": candidates,
        "fast_track": [classify_fast_track(candidate) for candidate in candidates],
    }
    daily = {
        "schema_version": "rising-daily-candidate-pool-v1",
        "policy_version": POLICY_VERSION,
        "business_date": business_date,
        "collected_at": collected_at,
        "candidate_count": len(channels["daily_value"]),
        "target_range": [8, 12],
        "shortage_reason": None if len(channels["daily_value"]) >= 8 else "质量门后不足8条，不凑数",
        "candidates": channels["daily_value"],
    }
    atomic_write_json(state_path, state)
    atomic_write_json(root / "rising-candidates.json", rising)
    atomic_write_json(root / "business-channels.json", channels)
    atomic_write_json(root / "daily-candidate-pool.json", daily)
    atomic_write_text(
        root / "operator-hotspot-board.md",
        build_operator_hotspot_board(candidates, state, collected_at=collected_at),
    )
    report_path = root / "run-report.json"
    if report_path.exists():
        report = read_json(report_path)
        report.update(
            {
                "status": "CALIBRATION_NO_AUTO_PUBLISH",
                "hot_now_candidate_count": len(channels["hot_now"]),
                "daily_pool_candidate_count": len(channels["daily_value"]),
                "rising_watch_candidate_count": len(channels["rising_watch"]),
                "event_count": channels["event_count"],
                "merged_event_count": channels["merged_event_count"],
                "watch_status": "WATCH_DEGRADED" if watch_degraded_reasons else "WATCHING",
                "watch_degraded_reasons": sorted(set(watch_degraded_reasons or [])),
                "qianfan_called": False,
            }
        )
        draft_count, awaiting = _daily_content_counts(Path(data_dir), business_date)
        report["draft_count"] = draft_count
        report["awaiting_confirmation_count"] = awaiting
        atomic_write_json(report_path, report)
    return channels


def _attach_editorial_images(
    candidates: list[dict[str, Any]], data_dir: Path, business_date: str
) -> None:
    image_root = data_dir / business_date / "editorial-images"
    for candidate in candidates:
        if candidate.get("images"):
            continue
        if candidate.get("source_media_state") == "UNRESOLVED_SOURCE_MEDIA":
            continue
        content_id = str(candidate.get("content_id") or "")
        image = image_root / content_id / "fact-card.png"
        if not content_id or not image.is_file():
            continue
        path = str(image.resolve())
        candidate["images"] = [path]
        candidate["image_plan"] = [{
            "path": path,
            "placement": "首段后",
            "credit": "大宜宾原创事实信息图",
            "rights": "ORIGINAL_EDITORIAL_GRAPHIC",
            "sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
        }]


def _non_synthetic_images(sources: list[dict[str, Any]]) -> list[str]:
    output: list[str] = []
    for source in sources:
        synthetic = {
            str(item.get("path") or "")
            for item in source.get("image_plan", [])
            if isinstance(item, dict) and item.get("rights") == "ORIGINAL_EDITORIAL_GRAPHIC"
        }
        for image in source.get("images", []):
            path = str(image or "")
            if path and path not in synthetic and path not in output:
                output.append(path)
    return output[:3]


def _active_history_events(data_dir: Path) -> list[dict[str, Any]]:
    active = {
        "PUBLISHED", "PUBLISHED_VERIFIED", "AWAITING_HUMAN_CONFIRMATION",
        "AWAITING_HUMAN_SCHEDULE_CONFIRMATION", "CONFIRMED", "SCHEDULED",
        "PUBLISHING", "GENERATING", "QUALITY_INCIDENT", "PAUSED_QUALITY_INCIDENT",
    }
    events: list[dict[str, Any]] = []
    queue_path = data_dir / "production-publish-queue.json"
    if queue_path.exists():
        for item in read_json(queue_path).get("items", []):
            if isinstance(item, dict) and str(item.get("status") or "") in active:
                events.append(item)
    for batch_path in data_dir.glob("????-??-??/pending-batches/*/batch.json"):
        batch = read_json(batch_path)
        if str(batch.get("status") or "") not in active:
            continue
        events.extend(item for item in batch.get("drafts", []) if isinstance(item, dict))
    explicit = data_dir / "excluded-events.json"
    if explicit.exists():
        events.extend(
            {**item, "_explicit_exclusion": True}
            for item in read_json(explicit).get("events", [])
            if isinstance(item, dict)
        )
    return events


def _daily_fact_candidate(row: dict[str, Any], collected_at: str) -> dict[str, Any] | None:
    title = _sanitize_persisted_text(row.get("title"))
    summary = _sanitize_persisted_text(row.get("summary"))
    raw_text = _sanitize_persisted_text(row.get("raw_text"))
    body_text = raw_text or summary
    if not title or not row.get("source_url"):
        return None
    try:
        published = _parse_time(str(row.get("published_at") or ""))
        if _parse_time(collected_at) - published > timedelta(hours=72):
            return None
    except (ValueError, TypeError):
        return None
    evidence = {
        "title": title,
        "content": body_text if row.get("source_tier") == "P0" else "",
        "poi_name": "",
        "source_name": "",
    }
    if classify_locality(evidence) != "direct" or _classify_risk(f"{title} {body_text}") != "LOW_RISK":
        return None
    value_terms = (
        "建设", "更新", "改造", "投用", "开放", "开业", "公园", "景区", "文旅",
        "音乐", "活动", "交通", "消费", "市场", "商业", "充电站", "社区", "展览",
        "工业", "经济", "农业", "农事", "秋粮", "民生", "公共服务", "交付", "价格",
        "听证", "婚姻登记", "石海", "旅游", "摊区", "污水处理", "水环境",
    )
    if not any(term in f"{title} {body_text}" for term in value_terms):
        return None
    if (
        re.search(r"会议|培训|调研|督导|整治|法治|纪委|人大常委|专题工作", title)
        and not re.search(r"项目(?:建设|改造|施工|进度)|道路拓宽|大桥", f"{title} {body_text}")
    ):
        return None
    value_score = 55 if re.search(r"开放|开业|投用|文旅|景区|公园|音乐|活动|充电站|城市更新", f"{title} {body_text}") else 45
    source_id = str(row.get("source_id") or "")
    source_images = _image_urls(row)
    source_media_state = (
        "RESOLVED_WITH_IMAGES"
        if source_images
        else "UNRESOLVED_SOURCE_MEDIA"
        if source_id == "yibin-yryb"
        else "NO_SOURCE_MEDIA_DECLARED"
    )
    return {
        "content_id": f"fact-{row.get('raw_item_id')}",
        "title": title,
        "platform": source_id or "权威来源",
        "source_url": str(row.get("source_url") or ""),
        "images": source_images,
        "source_media_state": source_media_state,
        "material_source": "RAW_TEXT" if raw_text else "SUMMARY_FALLBACK",
        "body_snapshot": body_text,
        "body_hash": _sha256(body_text) if body_text else "",
        "content_mode": "VERIFIED_FACT",
        "published_at": str(row.get("published_at") or ""),
        "current_metrics": {},
        "material_excerpt": body_text[:1200],
        "locality_state": "direct",
        "risk_state": "LOW_RISK",
        "age_bucket": _age_bucket({"post_create_time": row.get("published_at")}, collected_at),
        "interaction_delta": None,
        "rising_state": "DAILY_VALUE",
        "score": value_score,
        "reasons": ["YIBIN_DIRECT", "FACT_COMPLETE"],
        "fact_check": {
            "status": "PASS",
            "critical_unknown_count": 0,
            "evidence": [
                {
                    "raw_item_id": str(row.get("raw_item_id") or ""),
                    "source_id": str(row.get("source_id") or ""),
                    "source_tier": str(row.get("source_tier") or ""),
                    "source_url": str(row.get("source_url") or ""),
                }
            ],
        },
        "policy_version": POLICY_VERSION,
    }


def _event_id(candidate: dict[str, Any], collected_at: str) -> str:
    title = _fact_event_text(candidate.get("title"))
    locations = sorted(_fact_locations(title), key=len, reverse=True)
    location = locations[0] if locations else "UNKNOWN_PLACE"
    actions = (
        "启动", "施工", "更新", "改造", "建成", "开放", "开业", "举办", "发布",
        "举行", "落地", "竣工", "通车", "投用", "上岗", "停运", "恢复",
        "涨价", "降价", "上新", "回应", "被淹", "坍塌",
    )
    action = next((word for word in actions if word in title), "OTHER_ACTION")
    objects = re.findall(
        r"[\u4e00-\u9fffA-Za-z0-9]{2,18}(?:集团|公司|片区|项目|景区|公园|商场|车站|大桥|活动|大会|赛事|学校|医院)",
        title,
    )
    subject = max(objects, key=len) if objects else re.sub(
        r"宜宾|四川|启动|施工|更新|改造|建成|开放|举办|发布|投用",
        "",
        title,
    )[:12]
    published = str(candidate.get("published_at") or "")[:10]
    date_bucket = published if re.fullmatch(r"\d{4}-\d{2}-\d{2}", published) else collected_at[:10]
    return "event-" + _sha256("|".join((location, subject or "UNKNOWN_SUBJECT", action, date_bucket)))[:16]


def _same_user_event(
    first: dict[str, Any], second: dict[str, Any], collected_at: str
) -> bool:
    if first is second:
        return True
    first_content_id = str(first.get("content_id") or "")
    second_content_id = str(second.get("content_id") or "")
    if first_content_id and first_content_id == second_content_id:
        return True
    first_title = _fact_event_text(first.get("title"))
    second_title = _fact_event_text(second.get("title"))
    if not first_title or not second_title:
        return False
    if first_title == second_title:
        return True
    first_groups = {
        name for name, terms in FACT_EVENT_GROUPS.items()
        if any(term in first_title for term in terms)
    }
    second_groups = {
        name for name, terms in FACT_EVENT_GROUPS.items()
        if any(term in second_title for term in terms)
    }
    if not first_groups.intersection(second_groups):
        return False
    first_locations = _fact_locations(
        _fact_event_text(f"{first.get('title') or ''} {first.get('material_excerpt') or ''}")
    )
    second_locations = _fact_locations(
        _fact_event_text(f"{second.get('title') or ''} {second.get('material_excerpt') or ''}")
    )
    if first_locations and second_locations and not first_locations.intersection(second_locations):
        return False
    first_day = _event_day(first, collected_at)
    second_day = _event_day(second, collected_at)
    if abs((first_day - second_day).days) > 3:
        return False
    match = SequenceMatcher(None, first_title, second_title, autojunk=False).find_longest_match()
    return match.size >= 10 and match.size / min(len(first_title), len(second_title)) >= 0.5


def _event_day(candidate: dict[str, Any], collected_at: str) -> datetime:
    raw = str(candidate.get("published_at") or "")[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        raw = collected_at[:10]
    return datetime.fromisoformat(raw)


def _source_priority(candidate: dict[str, Any]) -> tuple[int, int, int, float]:
    return (
        1 if candidate.get("fact_check", {}).get("status") == "PASS" else 0,
        1 if candidate.get("source_url") else 0,
        len(str(candidate.get("material_excerpt") or "")),
        _current_interaction(candidate),
    )


def _current_interaction(candidate: dict[str, Any]) -> float:
    metrics = candidate.get("current_metrics") if isinstance(candidate.get("current_metrics"), dict) else {}
    granular = [metrics.get(field) for field in ("like_count", "comment_count", "share_count", "view_count")]
    numbers = [float(value) for value in granular if isinstance(value, (int, float))]
    if numbers:
        return max(numbers)
    value = metrics.get("respond_count")
    return float(value) if isinstance(value, (int, float)) else 0.0


def _hot_now_threshold_evidence(
    event: dict[str, Any], thresholds: dict[str, int] | None = None
) -> dict[str, int | float]:
    limits = thresholds or HOT_NOW_THRESHOLDS
    observed: dict[str, float] = {}
    metrics = event.get("current_metrics") if isinstance(event.get("current_metrics"), dict) else {}
    for field in limits:
        value = _number_or_none(metrics.get(field))
        if value is not None:
            observed[field] = float(value)
    for platform_metrics in (event.get("platform_max_metrics") or {}).values():
        if not isinstance(platform_metrics, dict):
            continue
        for field in limits:
            value = _number_or_none(platform_metrics.get(field))
            if value is not None:
                observed[field] = max(observed.get(field, float(value)), float(value))
    return {
        field: int(value) if value.is_integer() else value
        for field, value in observed.items()
        if value >= limits[field]
    }


def classify_two_hour_rising(
    snapshots: list[dict[str, Any]],
    *,
    sample_points: int = 5,
    interval_minutes: int = 30,
    positive_intervals: int = 3,
) -> dict[str, Any]:
    rows = [row for row in snapshots if isinstance(row, dict)][-sample_points:]
    if len(rows) != sample_points or any(not row.get("collected_at") for row in rows):
        return {"status": "INSUFFICIENT_SAMPLES", "sample_count": len(rows)}
    try:
        times = [_parse_time(str(row["collected_at"])) for row in rows]
    except ValueError:
        return {"status": "INSUFFICIENT_SAMPLES", "sample_count": len(rows)}
    if any((right - left) != timedelta(minutes=interval_minutes) for left, right in zip(times, times[1:])):
        return {"status": "INSUFFICIENT_SAMPLES", "sample_count": len(rows)}
    fields = ("view_count", "like_count", "comment_count", "share_count")
    any_growth = False
    positive_count = 0
    for before, after in zip(rows, rows[1:]):
        interval_positive = False
        for field in fields:
            left, right = before.get(field), after.get(field)
            if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
                continue
            if right < left:
                return {"status": "DATA_QUALITY_HOLD", "sample_count": 5, "field": field}
            if right > left:
                interval_positive = True
                any_growth = True
        positive_count += int(interval_positive)
    return {
        "status": "RISING_CONFIRMED" if any_growth and positive_count >= positive_intervals else "NOT_RISING",
        "sample_count": sample_points,
        "positive_intervals": positive_count,
    }


def _deduplicate_sanitized(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for item in items:
        content_id = str(item.get("content_id") or "")
        if not content_id or content_id in seen:
            continue
        seen.add(content_id)
        output.append(item)
    return output


def _interaction_delta(item: dict[str, Any]) -> float | None:
    snapshots = [snap for snap in item.get("snapshots", []) if isinstance(snap, dict)]
    if len(snapshots) < 2:
        return None
    previous, latest = snapshots[-2], snapshots[-1]
    total = 0.0
    has_value = False
    granular_fields = tuple(field for field in METRIC_FIELDS if field != "respond_count")
    fields = granular_fields if any(
        isinstance(previous.get(field), (int, float)) and isinstance(latest.get(field), (int, float))
        for field in granular_fields
    ) else ("respond_count",)
    for field in fields:
        before = previous.get(field)
        after = latest.get(field)
        if isinstance(before, (int, float)) and isinstance(after, (int, float)):
            total += max(0.0, float(after) - float(before))
            has_value = True
    return total if has_value else None


def _robust_threshold(values: list[float]) -> float:
    center = median(values)
    deviations = [abs(value - center) for value in values]
    mad = median(deviations)
    return center + (3 * mad)


def _watchlist_sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
    return (
        1 if item.get("locality_state") == "direct" else 0,
        1 if item.get("risk_state") == "LOW_RISK" else 0,
        str(item.get("last_seen_at") or ""),
    )


def _age_bucket(row: dict[str, Any], collected_at: str) -> str:
    published = _first_text(row, ("post_create_time", "create_time"))
    if not published:
        return "unknown"
    try:
        age_seconds = (_parse_time(collected_at) - _parse_time(published)).total_seconds()
    except ValueError:
        return "unknown"
    if age_seconds < 3600:
        return "0-1h"
    if age_seconds < 3 * 3600:
        return "1-3h"
    if age_seconds < 6 * 3600:
        return "3-6h"
    return "6h+"


def _keyword_summary(texts: list[str]) -> list[str]:
    buckets = {
        "停车/交通": ("停车", "车位", "交通", "公交", "路线"),
        "价格/消费": ("价格", "多少钱", "贵", "便宜", "消费"),
        "游玩/体验": ("好玩", "去过", "推荐", "朋友", "外地"),
    }
    output = []
    joined = "\n".join(texts)
    for label, words in buckets.items():
        if any(word in joined for word in words):
            output.append(label)
    return output or ["一般讨论"]


def _local_terms(texts: list[str]) -> list[str]:
    joined = "\n".join(texts)
    terms = ("宜宾", "翠屏", "叙州", "南溪", "江安", "长宁", "高县", "李庄", "三江新区")
    return [term for term in terms if term in joined]


def _safe_requests(requests: object) -> list[dict[str, Any]]:
    if not isinstance(requests, list):
        return []
    output = []
    for request in requests:
        if isinstance(request, dict):
            output.append(
                {
                    "method": str(request.get("method") or "").upper(),
                    "path": str(request.get("path") or ""),
                    "http_status": request.get("http_status"),
                }
            )
    return output


def _forbidden_identity_paths(payload: object) -> list[str]:
    human_text_fields = {
        "title", "content", "content_excerpt", "body_snapshot", "text", "origin_title",
        "summary", "source_name", "poi_name", "evidence",
    }
    reasons: list[str] = []

    def scan(value: object, *, key: str = "", path: str = "root") -> None:
        if isinstance(value, dict):
            for child_key, child in value.items():
                normalized = str(child_key).lower()
                child_path = f"{path}.{normalized}"
                if normalized in IDENTITY_FIELDS:
                    reasons.append(f"{child_path}:identity_key")
                    continue
                if normalized in CREDENTIAL_FIELDS:
                    reasons.append(f"{child_path}:credential_key")
                    continue
                scan(child, key=normalized, path=child_path)
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                scan(child, key=key, path=f"{path}[{index}]")
            return
        if not isinstance(value, str):
            return
        if key in human_text_fields and re.search(
            r"authorization\s*[:=]|bearer\s+\S+|cookie\s*[:=]|token\s*[:=]|password\s*[:=]",
            value,
            re.IGNORECASE,
        ):
            reasons.append(f"{path}:credential_term")
        elif key in human_text_fields and EMBEDDED_IDENTITY_PATTERN.search(value):
            reasons.append(f"{path}:embedded_identity")
        elif key in human_text_fields and PHONE_PATTERN.search(value):
            reasons.append(f"{path}:phone")

    scan(payload)
    return reasons


def _contains_forbidden_identity(payload: object) -> bool:
    return bool(_forbidden_identity_paths(payload))


def _first_text(row: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return ""


def _identity_aliases(row: dict[str, Any]) -> list[str]:
    aliases = []
    for key in ("unique_id", "unity_id", "similar_id", "url", "post_id"):
        value = _first_text(row, (key,))
        if value:
            aliases.append(_sha256(f"{key}:{value}"))
    return sorted(set(aliases))


def _topic_terms(topic: str) -> list[str]:
    text = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", topic)
    locations = [term for term in LOCATION_TERMS if term in text]
    chunks = [text[index:index + 4] for index in range(0, max(0, len(text) - 3), 2)]
    return sorted(set(locations + [chunk for chunk in chunks if len(chunk) >= 4]), key=len, reverse=True)


def _load_hot_signals(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = read_json(path)
    return [row for row in payload.get("signals", []) if isinstance(row, dict)]


def _has_hot_signal(candidate: dict[str, Any], signals: list[dict[str, Any]]) -> bool:
    terms = _topic_terms(str(candidate.get("title") or ""))
    return any(
        terms and any(term in _clean_text(signal.get("topic")) for term in terms)
        for signal in signals
    )


def _has_cross_platform(candidate: dict[str, Any], candidates: list[dict[str, Any]]) -> bool:
    terms = _topic_terms(str(candidate.get("title") or ""))
    platform = str(candidate.get("platform") or "")
    return any(
        other is not candidate
        and str(other.get("platform") or "") != platform
        and terms
        and any(term in _clean_text(other.get("title")) for term in terms)
        for other in candidates
    )


def _number_or_none(value: object) -> int | float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return float(value.replace(",", ""))
        except ValueError:
            return None
    return None


def _image_urls(row: dict[str, Any]) -> list[str]:
    values = row.get("images") if isinstance(row.get("images"), list) else []
    output: list[str] = []
    for value in [*values, row.get("cover_url")]:
        url = value.get("url") if isinstance(value, dict) else value
        text = _clean_text(url)
        if text.startswith(("https://", "http://")) and text not in output:
            output.append(text)
    return output[:3]


def _metric_display(value: object) -> str:
    number = _number_or_none(value)
    return "未知" if number is None else str(int(number) if float(number).is_integer() else number)


def _first_metric(row: dict[str, Any], primary: str, fallback: str) -> object:
    return row.get(primary) if _number_or_none(row.get(primary)) is not None else row.get(fallback)


def _metric_change(before: object, after: object) -> str:
    start = _number_or_none(before)
    end = _number_or_none(after)
    if start is None or end is None:
        return "未知"
    delta = float(end) - float(start)
    rendered = str(int(delta)) if delta.is_integer() else str(delta)
    return f"+{rendered}" if delta >= 0 else rendered


def _previous_day_state(data_dir: Path, business_date: str) -> dict[str, Any]:
    try:
        previous_date = (datetime.fromisoformat(business_date) - timedelta(days=1)).date().isoformat()
    except ValueError:
        return {}
    path = data_dir / previous_date / "rising-monitor" / "state.json"
    return read_json(path) if path.exists() else {}


def _daily_content_counts(data_dir: Path, business_date: str) -> tuple[int, int]:
    path = data_dir / business_date / "functional-canary" / "active-confirmation-card.json"
    drafts = 0
    awaiting = 0
    if path.exists():
        card = read_json(path)
        drafts += 1
        awaiting += int(card.get("status") == "AWAITING_HUMAN_PUBLISH_CONFIRMATION")
    for batch_path in (data_dir / business_date / "pending-batches").glob("*/batch.json"):
        batch = read_json(batch_path)
        batch_drafts = batch.get("drafts") if isinstance(batch.get("drafts"), list) else []
        if str(batch.get("status") or "").startswith("SUPERSEDED_"):
            continue
        drafts += len(batch_drafts)
        if batch.get("status") in {
            "AWAITING_HUMAN_CONFIRMATION",
            "AWAITING_HUMAN_SCHEDULE_CONFIRMATION",
        }:
            awaiting += len(batch_drafts)
    return drafts, awaiting


def _classify_risk(text: object) -> str:
    return "HOLD" if LOW_RISK_HOLD_PATTERN.search(_clean_text(text)) else "LOW_RISK"


def _ugc_discussion_ready(event: dict[str, Any]) -> bool:
    body = _clean_text(event.get("body_snapshot"))
    title = _clean_text(event.get("title"))
    risk_text = f"{title} {body}"
    metrics = event.get("current_metrics")
    if not isinstance(metrics, dict):
        metrics = event.get("metrics") if isinstance(event.get("metrics"), dict) else {}
    if (
        len(body) < 20
        or int(metrics.get("comment_count") or 0) <= 0
        or LOW_RISK_HOLD_PATTERN.search(risk_text)
        or UGC_DISALLOWED_PATTERN.search(risk_text)
    ):
        return False
    explicit_text = " ".join(
        UGC_SOURCE_FOOTER_PATTERN.sub("", TRAILING_LOCATION_PATTERN.sub("", value))
        for value in (title, body)
    )
    explicit_text = re.sub(r"#[^#；;，,\s]+", "", explicit_text)
    return any(
        term in explicit_text for term in YIBIN_LOCATION_TERMS if term != "宜宾"
    ) or bool(re.search(
        r"(?:宜宾.{0,12}(?:社区|广场|公园|景区|车站|道路|街道|小区|公交|文旅)|"
        r"(?:社区|广场|公园|景区|车站|道路|街道|小区|公交|文旅).{0,12}宜宾)",
        explicit_text,
    ))


def _sanitize_persisted_text(value: object) -> str:
    text = _clean_text(value)
    if "摘要：" in text:
        text = text.rsplit("摘要：", 1)[-1]
    match = EMBEDDED_IDENTITY_PATTERN.search(text)
    if match:
        text = text[: match.start()]
    text = re.split(
        r"(?:命中词|命中地域|信息属性|信息类型|来源平台|发文来源|发文日期|发文时间|信息链接)[:：]",
        text,
        maxsplit=1,
    )[0]
    return PHONE_PATTERN.sub("[REDACTED_PHONE]", text).strip()


def _reapply_current_policy(item: dict[str, Any], *, collected_at: str) -> None:
    item["title"] = _sanitize_persisted_text(item.get("title"))[:160]
    item["content_excerpt"] = _sanitize_persisted_text(item.get("content_excerpt"))[:240]
    evidence = {
        "title": item.get("title"),
        "content": item.get("content_excerpt"),
        "poi_name": item.get("poi_name"),
        "source_name": item.get("source_name"),
    }
    item["locality_state"] = classify_locality(evidence)
    item["risk_state"] = _classify_risk(
        f"{item.get('title') or ''} {item.get('content_excerpt') or ''}"
    )
    published_at = str(item.get("published_at") or "")
    if published_at:
        item["age_bucket"] = _age_bucket(
            {"post_create_time": published_at}, collected_at
        )
    item["policy_version"] = POLICY_VERSION


def _fact_event_text(value: object) -> str:
    text = _sanitize_persisted_text(value)
    return re.sub(
        r"(?:📍|IP属地[:：]?|账号定位[:：]?|定位[:：]?)\s*(?:四川省?)?\s*宜宾市?\s*$",
        "",
        text,
    ).strip()


def _fact_locations(text: str) -> set[str]:
    return {term for term in LOCATION_TERMS if term in text}


def _fact_event_groups(text: str) -> set[str]:
    return {
        group
        for group, words in FACT_EVENT_GROUPS.items()
        if any(word in text for word in words)
    }


def _fact_core_terms(text: str, groups: set[str]) -> set[str]:
    return {
        word
        for group in groups
        for word in FACT_EVENT_GROUPS[group]
        if word in text
    }


def _longest_common_subject(left: str, right: str) -> int:
    left = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", left)
    right = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", right)
    previous = [0] * (len(right) + 1)
    longest = 0
    for left_char in left:
        current = [0]
        for index, right_char in enumerate(right, 1):
            value = previous[index - 1] + 1 if left_char == right_char else 0
            current.append(value)
            longest = max(longest, value)
        previous = current
    return longest


def _clean_text(value: object) -> str:
    return " ".join(str(value or "").split())


def _parse_time(value: str) -> datetime:
    text = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=SHANGHAI)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _ego_script(task_space: str, *, watch_target: dict[str, str] | None = None) -> str:
    task_name = json.dumps(task_space)
    plan_name = json.dumps(PLAN_NAME)
    safe_watch_target = json.dumps(
        {
            "title": str((watch_target or {}).get("title") or "")[:120],
            "query": str((watch_target or {}).get("query") or "")[:32],
            "identity_aliases": [
                str(value)
                for value in (watch_target or {}).get("identity_aliases", [])
                if re.fullmatch(r"[0-9a-f]{64}", str(value))
            ][:10],
        },
        ensure_ascii=False,
    )
    return f"""
const startedAt = Date.now()
const task = await useOrCreateTaskSpace({task_name})
const tabs = await listTabs()
const existing = tabs.find(tab => {{
  try {{ return new URL(tab.url).hostname === 'www.xyuqing.com' }} catch {{ return false }}
}})
if (existing) await switchTab(existing.targetId || existing.id)
else await openOrReuseTab('https://www.xyuqing.com/', {{wait:true, timeout:30}})
await waitForNetworkIdle({{timeout:15}}).catch(() => {{}})
await js(String.raw`(()=>{{
  window.__risingT0Done = false
  window.__risingT0Result = null
  ;(async()=>{{
    const pageStartedAt = Date.now()
    const requests = []
    const token = localStorage.getItem('token')
    if (!token) return {{auth_status:'AUTH_REQUIRED', requests, plan_list:{{}}, content:{{code:0,data:{{list:[]}}}}, comments:{{code:0,data:{{list:[]}}}}}}
    const headers = {{Accept:'application/json','Content-Type':'application/json',Authorization:'Bearer '+token}}
    const call = async (path, body) => {{
      if (!['/service/plan/list','/service/search/post_list'].includes(path)) throw new Error('endpoint not allowed')
      const response = await fetch('https://api.xyuqing.com'+path, {{method:'POST', headers, body:JSON.stringify(body), credentials:'omit', redirect:'follow'}})
      const finalUrl = new URL(response.url)
      if (finalUrl.hostname !== 'api.xyuqing.com') throw new Error('unexpected redirect')
      const text = await response.text()
      let payload
      try {{ payload = JSON.parse(text) }} catch {{ payload = {{__non_json__:true}} }}
      requests.push({{method:'POST', path, http_status:response.status}})
      return {{http_status:response.status, payload}}
    }}
    const planCall = await call('/service/plan/list', {{category:0}})
    if (planCall.http_status === 429) return {{auth_status:'RATE_LIMITED', requests, plan_list:{{}}, content:{{code:0,data:{{list:[]}}}}, comments:{{code:0,data:{{list:[]}}}}}}
    if ([401,403].includes(planCall.http_status) || planCall.payload?.code === 20001) return {{auth_status:'AUTH_REQUIRED', requests, plan_list:{{}}, content:{{code:0,data:{{list:[]}}}}, comments:{{code:0,data:{{list:[]}}}}}}
    const groups = Array.isArray(planCall.payload?.data) ? planCall.payload.data : []
    const plans = groups.flatMap(group => Array.isArray(group?.children) ? group.children : [group]).filter(Boolean)
    const matches = plans.filter(item => String(item?.name || '') === {plan_name})
    const plan = matches.length === 1 ? matches[0] : null
    if (!plan || String(plan.id || '').trim() === '') return {{auth_status:'AUTH_OK', requests, plan_list:{{code:0,data:[]}}, content:{{code:0,data:{{list:[]}}}}, comments:{{code:0,data:{{list:[]}}}}, contract:{{plan_match:false,plan_match_count:matches.length}}}}
    const planIdHash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(String(plan.id))))).map(value => value.toString(16).padStart(2, '0')).join('')
    const safePlanList = {{
      code:planCall.payload?.code, message:planCall.payload?.message,
      data:[{{name:plan?.name, plan_id_hash:planIdHash, word:plan?.word, word_combination:plan?.word_combination,
        analyze_word:plan?.analyze_word, category:plan?.category, status:plan?.status,
        updated_at:plan?.updated_at, created_at:plan?.created_at}}]
    }}
    const query = String(plan.word || plan.word_combination || plan.analyze_word || '')
    const watchTarget = {safe_watch_target}
    const baseBody = {{
      plan_id:String(plan.id), word:query, hit_field:['content','title','cover_ocr','ocr','asr','nickname','poi','last_poi'],
      post_category:0, image_url:'', date:'24h', page_size:50, reduce_noise:1, discrimination:1,
      mini_word_field:'all', miniWord:[], page:1, direct_id:'', industry_filter:'',
      platform:['douyin','weibo','weixin','toutiao','xiaohongshu','web','app','bbs','enews','jingwai','shipin'],
      platform_name_exact:[], source_type:[], retweeted_type:0, merge:1, is_read:0,
      media:[0,1,2], is_ai_content:-1, have_topic:0, have_at:0, have_mcn:0,
      source_level:['央级','省级','地市','区县','境外','商业','中小','行业门户','其他'],
      exclude_gov:0, undeleted:0, industry_name:[], water_army:[], scene:[], poi:[],
      verify:['政务认证','机构认证','企业认证','个人认证','未认证'], verify_weibo:[1,2,3,4,5,6,7],
      scene_name:[], duration:[',15','15,30','30,60','60,'], respond_field_type:'like_count',
      defineDataRange:[], respond_field_num:'', fans_count:'', sentiment:['非敏感','敏感','中性'],
      original:[1], save_filter:0, return_type:1
    }}
    const summaryCall = await call('/service/search/post_list', {{...baseBody, comment_type:0, return_type:2}})
    const maxPage = Math.max(1, Number(summaryCall.payload?.data?.max_page || summaryCall.payload?.data?.maxPage || 1))
    const discoveryCall = await call('/service/search/post_list', {{...baseBody, comment_type:0, page:1}})
    const watchTitle = String(watchTarget.title || '').trim()
    const watchWord = String(watchTarget.query || '').trim()
    const watchCall = watchTitle && watchWord
      ? await call('/service/search/post_list', {{...baseBody, word:watchWord, merge:0, comment_type:0, page:1}})
      : maxPage >= 2
      ? await call('/service/search/post_list', {{...baseBody, comment_type:0, page:2}})
      : {{http_status:200, payload:{{code:0,data:{{list:[]}}}}}}
    const platformRotation = ['douyin','weibo','weixin','toutiao','xiaohongshu']
    const platformTarget = platformRotation[Math.floor(Date.now() / 1800000) % platformRotation.length]
    const platformPage = 1 + (Math.floor(Date.now() / 1800000) % Math.min(maxPage, 2))
    const platformCall = await call('/service/search/post_list', {{...baseBody, comment_type:0, page:platformPage, platform:[platformTarget]}})
    const commentCall = await call('/service/search/post_list', {{...baseBody, word:watchWord || query, direct_id:'', comment_type:1, original:[0,1,2]}})
    for (const current of [summaryCall, discoveryCall, watchCall, platformCall, commentCall]) {{
      if (current.http_status === 429) return {{auth_status:'RATE_LIMITED', requests, plan_list:safePlanList, content:{{code:0,data:{{list:[]}}}}, comments:{{code:0,data:{{list:[]}}}}}}
      if ([401,403].includes(current.http_status) || current.payload?.code === 20001) return {{auth_status:'AUTH_REQUIRED', requests, plan_list:safePlanList, content:{{code:0,data:{{list:[]}}}}, comments:{{code:0,data:{{list:[]}}}}}}
    }}
    const safeRows = response => (Array.isArray(response?.payload?.data?.list) ? response.payload.data.list : []).map(row => ({{
      unique_id:row?.unique_id, unity_id:row?.unity_id, similar_id:row?.similar_id, post_id:row?.post_id,
      title:row?.title, content:row?.content, desc:row?.desc, copy_text:row?.copy_text,
      url:row?.url, platform:row?.platform, platform_name:row?.platform_name,
      images:row?.images, cover_url:row?.cover_url,
      post_create_time:row?.post_create_time, create_time:row?.create_time,
      like_count:row?.like_count, comment_count:row?.comment_count, share_count:row?.share_count,
      respond_count:row?.respond_count, view_count:row?.view_count, collect_count:row?.collect_count,
      repost_count:row?.repost_count, original:row?.original, merge_count:row?.merge_count,
      poi_name:row?.poi_name, location:row?.location, ip_location:row?.ip_location,
      origin: row?.origin ? {{unique_id:row.origin.unique_id, unity_id:row.origin.unity_id, post_id:row.origin.post_id, url:row.origin.url, title:row.origin.title, content:row.origin.content}} : undefined,
      comment: row?.comment ? {{content:row.comment.content, post_create_time:row.comment.post_create_time, unique_id:row.comment.unique_id}} : undefined
    }}))
    const platformAliases = {{douyin:['douyin','抖音'],weibo:['weibo','微博'],weixin:['weixin','微信'],toutiao:['toutiao','头条'],xiaohongshu:['xiaohongshu','小红书']}}
    const platformRows = safeRows(platformCall)
    const platformCanaryValid = platformRows.length > 0 && platformRows.every(row => platformAliases[platformTarget].some(alias => String(row.platform || '').toLowerCase().includes(alias)))
    const normalizeTitle = value => String(value || '').replace(/\\s+/g, '').replace(/[，。！？、：；,.!?;:]/g, '')
    const normalizedWatchTitle = normalizeTitle(watchTitle)
    const rawWatchRows = safeRows(watchCall)
    const targetAliases = new Set(Array.isArray(watchTarget.identity_aliases) ? watchTarget.identity_aliases : [])
    const aliasHashes = async row => {{
      const output = []
      for (const key of ['unique_id','unity_id','similar_id','url','post_id']) {{
        const value = String(row?.[key] || '').trim()
        if (!value) continue
        const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(key+':'+value))
        output.push(Array.from(new Uint8Array(digest)).map(byte => byte.toString(16).padStart(2,'0')).join(''))
      }}
      return output
    }}
    const watchRows = []
    for (const row of rawWatchRows) {{
      const hashes = await aliasHashes(row)
      const stableMatch = targetAliases.size > 0 && hashes.some(value => targetAliases.has(value))
      const title = normalizeTitle(row.title || row.desc)
      const titleMatch = targetAliases.size === 0 && normalizedWatchTitle.length >= 8 && (title.includes(normalizedWatchTitle) || normalizedWatchTitle.includes(title))
      if (stableMatch || titleMatch) watchRows.push(row)
    }}
    const watchCanaryValid = !watchTitle || watchRows.length > 0
    const discoveryRows = [...safeRows(discoveryCall), ...(platformCanaryValid ? platformRows : [])]
    return {{
      auth_status:'AUTH_OK', requests, duration_ms:Date.now()-pageStartedAt,
      plan_list:safePlanList,
      content:{{code:discoveryCall.payload?.code, message:discoveryCall.payload?.message, data:{{list:[...discoveryRows,...watchRows]}}}},
      discovery_content:{{code:discoveryCall.payload?.code, message:discoveryCall.payload?.message, data:{{list:discoveryRows}}}},
      watch_content:{{code:watchCall.payload?.code, message:watchCall.payload?.message, data:{{list:watchRows}}}},
      content_summary:{{code:summaryCall.payload?.code, data:{{max_page:maxPage,total:Number(summaryCall.payload?.data?.total || 0)}}}},
      comments:{{code:commentCall.payload?.code, message:'group by reported origin', data:{{list:safeRows(commentCall)}}}},
      contract:{{
        plan_match:true, plan_name:{plan_name}, plan_id_hash:planIdHash,
        request_policy:'plan/list metadata + discovery/platform pages + title-canary watch/comments filtered by runtime plan_id; comments grouped only by reported origin; plan_id remains browser-memory only',
        content_page_size:50, comment_page_size:50, original_preferred:true, merge_enabled:true,
        discovery_pages:[1], watch_pages:watchTitle ? [] : (maxPage >= 2 ? [2] : []), request_budget:6,
        watch_query:{{provided:Boolean(watchTitle && watchWord),valid:watchCanaryValid,match_count:watchRows.length,query_length:watchWord.length,stable_alias_count:targetAliases.size}},
        platform_canary:{{target:platformTarget,page:platformPage,valid:platformCanaryValid,count:platformRows.length}},
        identity_fields_removed:['nickname','user_id','unique_user_id','avatar','user_url','short_id'],
        platform_grouping:'post_list platform filter includes douyin,weibo,weixin,toutiao,xiaohongshu,web,app,bbs,enews,jingwai,shipin'
      }}
    }}
  }})().then(result => {{
    window.__risingT0Result = result
    window.__risingT0Done = true
  }}).catch(error => {{
    window.__risingT0Result = {{auth_status:'NETWORK_ERROR', requests:[], error_class:error?.name || 'Error', error:redactSensitive(String(error?.message || error))}}
    window.__risingT0Done = true
  }})
  function redactSensitive(text) {{ return String(text).replace(/Bearer\\s+\\S+/ig, 'Bearer [REDACTED]') }}
  return true
}})()`)
let bundle = null
for (let attempt = 0; attempt < 90; attempt++) {{
  await wait(1)
  const state = await js(String.raw`(()=>({{done:Boolean(window.__risingT0Done),result:window.__risingT0Result}}))()`)
  if (state.done) {{
    bundle = state.result
    break
  }}
}}
if (!bundle) bundle = {{auth_status:'NETWORK_ERROR', requests:[], error_class:'Timeout'}}
bundle.task_space_id = task.id
cliLog('XYUQING_RESULT_JSON=' + JSON.stringify(bundle))
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one read-only T0 rising monitor round")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--business-date")
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--fixture")
    parser.add_argument("--ego-executable", default="ego-browser")
    parser.add_argument("--fact-db", default=str(DEFAULT_FACT_DB))
    args = parser.parse_args(argv)
    now = datetime.now(SHANGHAI)
    business_date = args.business_date or now.date().isoformat()
    collected_at = now.isoformat()
    try:
        evidence_path = Path(args.evidence_dir) / "rounds" / f"round-{args.round:03d}.json"
        if evidence_path.exists():
            raise RisingMonitorError(f"round evidence already exists: round-{args.round:03d}.json")
        bundle = read_json(args.fixture) if args.fixture else fetch_live_bundle(ego_executable=args.ego_executable)
        bundle["fact_rows"] = load_fact_rows(args.fact_db)
        result = run_round(
            bundle,
            data_dir=args.data_dir,
            business_date=business_date,
            evidence_dir=args.evidence_dir,
            round_number=args.round,
            collected_at=collected_at,
        )
    except (RisingMonitorError, XyuqingSchemaError, XyuqingNetworkError, XyuqingAuthRequired, XyuqingRateLimited) as error:
        print(json.dumps({"status": "error", "error": redact_sensitive_text(str(error))}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "ok", **result}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
