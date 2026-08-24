from __future__ import annotations

from datetime import UTC, datetime
import html
import re
from typing import Any, Iterable
from urllib.parse import urlparse


HIGH_RISK_PATTERNS = (
    r"政治|涉政|宗教|民族矛盾|涉军|国家机密",
    r"事故|灾害|伤亡|死亡|死伤|身亡|遇难|中毒|失踪|火灾|地震|坍塌|溺水|洪峰|洪水|暴雨|汛情|山洪|\d+死|多伤|受伤",
    r"未成年人|儿童|童年|小学|幼儿园|宝宝|娃娃|新生儿|婴儿|婴幼儿|学生|大学生|孩子|高考|学费|升学宴|校园欺凌",
    r"投诉|曝光|举报|维权|纠纷|欺诈|骗子|追责|定责|乱收费|退费|退款|违约金",
    r"诊断|治疗方案|用药|病情|医疗建议|医院|医师|医生|医务|护士|患者|病人|产检|孕检|孕期|孕妈|孕妇|乳糖不耐受|夜醒|喂水|黄疸|病理|对症|儿科学会|妇幼",
    r"法律责任|起诉|判刑|犯罪|违法认定",
    r"股票|基金|投资建议|理财|贷款|收益率",
    r"身份证|手机号码|电话号码|家庭住址|车牌(?:号|是|为|[:：])|人脸信息|1[3-9]\d{9}|微信号|二维码",
    r"捐款|紧急求助|群体事件|围攻|辱骂|被偷|被盗|盗窃|小偷|求.{0,12}(?:帮忙|留意|扩散)|帮忙留意|寻找线索",
    r"删帖申请|申请删帖|删除(?:帖子|内容)",
)

DISCUSSION_PATTERN = re.compile(r"[？?]|大家|你们|是否|更关心|怎么看|体验|选择|变化|影响")
PROMOTION_PATTERN = re.compile(
    r"招商|招租|整租|分割出租|洽谈合作|诚邀.{0,12}(?:考察|合作)|"
    r"联系电话|1[3-9]\d{9}|加微信|二维码|招聘|招工|找工作|月薪|薪资|工资"
)
LOCAL_SPECIFICITY_PATTERN = re.compile(
    r"宜宾|酒都|长江首城|三江新区|临港|五粮液|"
    r"翠屏(?:区)?|叙州(?:区)?|南溪(?:区)?|江安(?:县)?|长宁(?:县)?|"
    r"高县|珙县|筠连(?:县)?|兴文(?:县)?|屏山(?:县)?"
)
TAG_PATTERN = re.compile(r"<[^>]+>")
SPACE_PATTERN = re.compile(r"\s+")
CHINESE_ONLY = re.compile(r"[\u4e00-\u9fff]")
NOISE_ONLY_PATTERN = re.compile(
    r"^(?:如题|顶|顶一下|路过|打卡|支持|看看|有人吗|大家怎么看|来聊聊|水一贴|沙发|测试|test|[哈呵嘿]+)[。！？!?，,\s…]*$",
    re.IGNORECASE,
)
REPLY_NOISE_ONLY_PATTERN = re.compile(
    r"^(?:(?:知道了|晓得了|收到|了解|路过|打卡|支持|看看|没看过|不清楚|真有钱|"
    r"666|[哈呵嘿]+|[赞顶]+)[了啊哦哟呀哈呵嘿！!。,.，…\s]*)+$",
    re.IGNORECASE,
)
REPLY_VALUE_PATTERN = re.compile(
    r"[？?]|因为|所以|如果|建议|应该|需要|关键|重点|费用|费|价格|配套|服务|体验|影响|"
    r"方便|希望|担心|为什么|哪里|哪儿|能不能|是否|以后|但是|不过|未必|不一定"
)
ACTION_PATTERN = re.compile(
    r"新增|恢复|开放|调整|发布|举行|暂停|启动|正式|建成|投运|通车|上线|落地|加场|开工|完工|取消|变化|影响"
)
OBJECT_PATTERN = re.compile(
    r"[\u4e00-\u9fff]{2,16}(?:中心|公园|医院|学校|影院|电影院|车站|充电站|场馆|项目|线路|活动|会议|标准|服务|设施)"
)
SOURCE_PATTERN = re.compile(r"据悉|记者|官方|部门|委员会|研究院|发布会|公告|通知")
DATE_SIGNAL_PATTERN = re.compile(r"\d|今天|昨日|明日|本周|本月|\d+月\d+日")


def select_comment_candidates(
    posts: Iterable[dict[str, Any]],
    *,
    now: datetime,
    score_threshold: int,
    already_commented_thread_ids: set[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    commented = already_commented_thread_ids or set()
    seen: set[str] = set()
    eligible: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for raw in posts:
        normalized = _normalize_post(raw)
        thread_id = normalized["thread_id"]
        if thread_id in commented:
            skipped.append(_skip(normalized, "SKIP_ALREADY_COMMENTED"))
            continue
        if thread_id in seen:
            skipped.append(_skip(normalized, "SKIP_DUPLICATE"))
            continue
        seen.add(thread_id)
        if PROMOTION_PATTERN.search(f"{normalized['title']}\n{normalized['content']}"):
            skipped.append(_skip(normalized, "SKIP_PROMOTION"))
            continue
        if _high_risk(normalized):
            skipped.append(_skip(normalized, "SKIP_HIGH_RISK"))
            continue
        substance = assess_content_substance(normalized)
        normalized.update(substance)
        if substance["is_low_information"]:
            skipped.append(_skip(normalized, "SKIP_LOW_INFORMATION"))
            continue
        score, breakdown = _score(normalized, now)
        normalized["score"] = score
        normalized["score_breakdown"] = breakdown
        if score < score_threshold:
            skipped.append(_skip(normalized, "SKIP_LOW_SCORE"))
            continue
        if breakdown["local_specificity"] == 0:
            skipped.append(_skip(normalized, "SKIP_NON_LOCAL"))
            continue
        normalized["facts"] = _facts(normalized)
        eligible.append(normalized)
    return {"eligible": eligible, "skipped": skipped}


def _normalize_post(post: dict[str, Any]) -> dict[str, Any]:
    thread_id = str(post.get("thread_id") or post.get("tid") or "").strip()
    if not thread_id:
        raise ValueError("comment candidate is missing thread_id")
    title = _plain_text(post.get("title") or post.get("subject") or "")
    content = _plain_text(post.get("content") or post.get("summary") or "")
    return {
        "thread_id": thread_id,
        "pid": str(post.get("pid") or "").strip(),
        "fid": str(post.get("fid") or "").strip(),
        "forum": _plain_text(post.get("forum") or post.get("fname") or ""),
        "title": title,
        "content": content,
        "published_at": str(post.get("published_at") or post.get("dateline") or "").strip(),
        "url": str(post.get("url") or "").strip(),
    }


def _plain_text(value: Any) -> str:
    decoded = html.unescape(str(value or ""))
    return SPACE_PATTERN.sub(" ", TAG_PATTERN.sub(" ", decoded)).strip()


def _high_risk(post: dict[str, Any]) -> bool:
    text = f"{post['title']}\n{post['content']}"
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in HIGH_RISK_PATTERNS)


def _score(post: dict[str, Any], now: datetime) -> tuple[int, dict[str, int]]:
    text = f"{post['title']} {post['content']}"
    local = 20 if LOCAL_SPECIFICITY_PATTERN.search(text) else 0
    discussion = 25 if DISCUSSION_PATTERN.search(text) else 0
    incremental = 20 if (
        len(re.findall(r"[\u4e00-\u9fff]", post["content"])) >= 45
        or len(post.get("information_signals", [])) >= 2
    ) else 0
    timely = 15 if _within_hours(post["published_at"], now, 24) else 0
    parsed_url = urlparse(post["url"])
    complete = 10 if all((post["title"], post["content"], post["fid"], parsed_url.netloc)) else 0
    safety = 10
    breakdown = {
        "local_specificity": local,
        "discussion_space": discussion,
        "comment_increment": incremental,
        "timeliness": timely,
        "completeness": complete,
        "safety_margin": safety,
    }
    return sum(breakdown.values()), breakdown


def _within_hours(value: str, now: datetime, hours: int) -> bool:
    try:
        if value.isdigit():
            published = datetime.fromtimestamp(int(value), tz=UTC)
        else:
            published = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if published.tzinfo is None:
                published = published.replace(tzinfo=UTC)
        current = now if now.tzinfo else now.replace(tzinfo=UTC)
        age_seconds = (current.astimezone(UTC) - published.astimezone(UTC)).total_seconds()
        return 0 <= age_seconds <= hours * 3600
    except (ValueError, OverflowError):
        return False


def _facts(post: dict[str, Any]) -> list[dict[str, str]]:
    values = [post["title"]]
    values.extend(
        part.strip()
        for part in re.split(r"[。！？!?；;]", post["content"])
        if len(part.strip()) >= 6
    )
    unique: list[str] = []
    for value in values:
        if value and value not in unique:
            unique.append(value)
    return [
        {"id": f"F{index}", "text": value}
        for index, value in enumerate(unique[:5], start=1)
    ]


def assess_content_substance(post: dict[str, Any]) -> dict[str, Any]:
    title = str(post.get("title") or "").strip()
    body = str(post.get("content") or "").strip()
    chinese = CHINESE_ONLY.findall(body)
    body_chars = len(chinese)
    compact_body = "".join(chinese)
    compact_title = "".join(CHINESE_ONLY.findall(title))
    combined = f"{title}\n{body}"
    signals: list[str] = []
    for name, pattern in (
        ("local_object", LOCAL_SPECIFICITY_PATTERN),
        ("number_or_time", DATE_SIGNAL_PATTERN),
        ("action_or_change", ACTION_PATTERN),
        ("named_object", OBJECT_PATTERN),
        ("source_attribution", SOURCE_PATTERN),
    ):
        if pattern.search(combined):
            signals.append(name)
    if len([part for part in re.split(r"[。！？!?；;]", body) if len(part.strip()) >= 6]) >= 2:
        signals.append("structured_detail")

    reasons: list[str] = []
    if body_chars < 15:
        reasons.append("too_short_without_context")
    if NOISE_ONLY_PATTERN.fullmatch(body):
        reasons.append("noise_only")
    if compact_body and compact_title and body_chars < 60 and (
        compact_body == compact_title
        or compact_body in compact_title
        or compact_title in compact_body
    ):
        reasons.append("title_restatement")
    unique_ratio = len(set(chinese)) / body_chars if body_chars else 0.0
    if body_chars >= 15 and unique_ratio < 0.25:
        reasons.append("repetitive_noise")
    if body_chars < 60 and len(signals) < 2:
        reasons.append("insufficient_fact_signals")

    length_score = 40 if body_chars >= 60 else 25 if body_chars >= 30 else 10 if body_chars >= 15 else 0
    substance_score = min(100, length_score + 15 * len(signals))
    return {
        "is_low_information": bool(reasons),
        "low_information_reasons": reasons,
        "information_signals": signals,
        "substance_score": substance_score,
    }


def assess_reply_substance(value: Any) -> dict[str, Any]:
    text = _plain_text(value)
    chinese_chars = len(CHINESE_ONLY.findall(text))
    reasons: list[str] = []
    if chinese_chars < 5:
        reasons.append("too_short")
    if REPLY_NOISE_ONLY_PATTERN.fullmatch(text):
        reasons.append("acknowledgement_or_noise")
    if chinese_chars < 12 and not REPLY_VALUE_PATTERN.search(text):
        reasons.append("short_expression_only")
    if PROMOTION_PATTERN.search(text):
        reasons.append("promotion")
    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in HIGH_RISK_PATTERNS):
        reasons.append("high_risk")
    return {"eligible": not reasons, "text": text, "reasons": reasons}


def _skip(post: dict[str, Any], reason: str) -> dict[str, Any]:
    result = {"thread_id": post["thread_id"], "title": post["title"], "reason": reason}
    for key in ("substance_score", "information_signals", "low_information_reasons"):
        if key in post:
            result[key] = post[key]
    return result
