from __future__ import annotations

import re
from typing import Any

from .comment_selector import HIGH_RISK_PATTERNS


CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]")
NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")
NAMED_ENTITY_PATTERN = re.compile(
    r"(?:宜宾|三江新区|临港|翠屏|叙州|南溪|江安|长宁|高县|珙县|筠连|兴文|屏山|五粮液)"
    r"[\u4e00-\u9fff]{0,10}(?:市|区|县|镇|乡|村|路|街|桥|站|商场|学校|医院|公园)"
)
FAKE_EXPERIENCE_PATTERN = re.compile(
    r"我(?:去过|吃过|买过|用过|住在|住过|亲眼|看见|听见|认识|朋友|家里|孩子|昨天|今天)|"
    r"我们家|我家|亲身经历|亲眼所见|身边朋友"
)
PRODUCTION_PATTERN = re.compile(r"AI|人工智能|模型|Skill|技能调用|马甲|运营|提示词|自动生成", re.IGNORECASE)
CONTACT_PATTERN = re.compile(r"https?://|www\.|微信|二维码|手机号|电话|私聊")
AI_TEMPLATE_PATTERN = re.compile(
    r"这个影响不小|我的判断是|不只是.{0,18}(?:更是|而是)|"
    r"更关键的变量|真正影响.{0,18}的是|你说.{0,18}这个判断是对的"
)
EDITORIAL_VOICE_PATTERN = re.compile(
    r"(?:这个|这种|这段|这处)?细节.{0,4}(?:挺|很|更)?真实|"
    r"听着像.{0,24}(?:落到|说到底|其实就是).{0,30}|"
    r"这种就.{0,10}在|"
    r"(?:这种)?画面比(?:单独|直接)?说.{0,24}更实在|"
    r"一个城市的.{0,12}有时候就是这么|"
    r"(?:这一前一后|这前后).{0,8}(?:挺|很)?有画面|"
    r"(?:这个点|这点|这个线|这条线).{0,6}(?:很具体|挺具体|是关键|还是关键)|"
    r"(?:这个|这种|这条|这).{0,4}(?:跨度|节奏).{0,10}(?:挺|很|确实|有点)"
)
FACT_PACKING_PATTERN = re.compile(r"(?:[^，。！？]{1,12}、){2,}")
GENERIC_FACT_BIGRAMS = {
    "宜宾",
    "大家",
    "我们",
    "你们",
    "他们",
    "一个",
    "这个",
    "那个",
    "现在",
    "开始",
    "可以",
    "可能",
    "情况",
    "问题",
    "相关",
    "进行",
    "已经",
    "表示",
    "记者",
    "今天",
    "目前",
    "后续",
}


def validate_comment(comment: dict[str, Any], post: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    text = str(comment.get("comment") or "").strip()
    if str(comment.get("thread_id") or "") != str(post.get("thread_id") or ""):
        reasons.append("THREAD_MISMATCH")
    facts = {
        str(item.get("id") or ""): str(item.get("text") or "")
        for item in post.get("facts", [])
        if isinstance(item, dict)
    }
    refs = comment.get("post_fact_refs")
    if not isinstance(refs, list) or not refs or any(str(ref) not in facts for ref in refs):
        reasons.append("UNKNOWN_FACT_REF")
        referenced_text = ""
    else:
        referenced_text = " ".join(facts[str(ref)] for ref in refs)
    understanding = str(comment.get("post_understanding") or "").strip()
    hook = str(comment.get("reply_hook") or "").strip()
    adds_value = str(comment.get("adds_value") or "").strip()
    if not understanding:
        reasons.append("UNDERSTANDING_REQUIRED")
    if not hook:
        reasons.append("REPLY_HOOK_REQUIRED")
    if referenced_text and not _shares_specific_phrase(
        f"{understanding} {hook}", referenced_text
    ):
        reasons.append("GROUNDING_REQUIRED")
    if not adds_value:
        reasons.append("VALUE_REQUIRED")
    source_text = " ".join((str(post.get("title") or ""), str(post.get("content") or ""), *facts.values()))
    if any(number not in source_text for number in NUMBER_PATTERN.findall(text)):
        reasons.append("NEW_NUMBER")
    if any(entity not in source_text for entity in NAMED_ENTITY_PATTERN.findall(text)):
        reasons.append("NEW_NAMED_ENTITY")
    if FAKE_EXPERIENCE_PATTERN.search(text):
        reasons.append("FAKE_EXPERIENCE")
    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in HIGH_RISK_PATTERNS):
        reasons.append("HIGH_RISK_CONTENT")
    if PRODUCTION_PATTERN.search(text):
        reasons.append("PRODUCTION_TERM")
    if CONTACT_PATTERN.search(text):
        reasons.append("CONTACT_OR_LINK")
    if AI_TEMPLATE_PATTERN.search(text):
        reasons.append("AI_TEMPLATE")
    if EDITORIAL_VOICE_PATTERN.search(text):
        reasons.append("EDITORIAL_VOICE")
    if FACT_PACKING_PATTERN.search(text):
        reasons.append("FACT_PACKING")
    if comment_quality_score(comment, post)["score"] < 60:
        reasons.append("GROUNDING_DEPTH_REQUIRED")
    risk_flags = comment.get("risk_flags")
    if not isinstance(risk_flags, list) or risk_flags:
        reasons.append("MODEL_RISK_FLAG")
    return _deduplicate(reasons)


def _shares_specific_phrase(comment: str, facts: str) -> bool:
    segments = re.findall(r"[\u4e00-\u9fff]+", facts)
    if any(
        segment[index : index + 3] in comment
        for segment in segments
        for index in range(max(0, len(segment) - 2))
    ):
        return True
    return any(
        phrase not in GENERIC_FACT_BIGRAMS and phrase in comment
        for segment in segments
        for index in range(max(0, len(segment) - 1))
        if len(phrase := segment[index : index + 2]) == 2
    )


def comment_quality_score(
    comment: dict[str, Any], post: dict[str, Any]
) -> dict[str, Any]:
    facts = {
        str(item.get("id") or ""): str(item.get("text") or "")
        for item in post.get("facts", [])
        if isinstance(item, dict)
    }
    refs = comment.get("post_fact_refs")
    referenced = " ".join(
        facts[str(ref)]
        for ref in refs
        if isinstance(refs, list) and str(ref) in facts
    ) if isinstance(refs, list) else ""
    understanding = str(comment.get("post_understanding") or "").strip()
    hook = str(comment.get("reply_hook") or "").strip()
    source = " ".join((str(post.get("title") or ""), str(post.get("content") or ""), *facts.values()))
    breakdown = {
        "understanding": 25 if understanding and _shares_specific_phrase(understanding, source) else 0,
        "reply_hook": 25 if hook and referenced and _shares_specific_phrase(f"{understanding} {hook}", referenced) else 0,
        "fact_refs": 25 if referenced else 0,
        "adds_value": 25 if str(comment.get("adds_value") or "").strip() else 0,
    }
    return {"score": min(100, sum(breakdown.values())), "breakdown": breakdown}


def _deduplicate(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
