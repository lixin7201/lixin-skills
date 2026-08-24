from __future__ import annotations

from html import unescape
import re
from typing import Any


_NUMBER = re.compile(
    r"(?<![A-Za-z0-9])\d+(?:\.\d+)?(?:%|万|亿|元|人|条|家|个|月|日|天|小时|分钟)?"
)
_HTML_TAG = re.compile(r"<[^>]+>")
_FORBIDDEN_IDENTITY = (
    "我亲眼看到",
    "我采访了",
    "我在现场",
    "我家孩子亲历",
)
_PRODUCTION_PHRASES = ("据素材", "根据素材", "素材显示", "以下为正文")
_AI_WRITING_PATTERNS = (
    ("material_process", re.compile(r"(?:素材|资料|原文)(?:里|中)?(?:提到|显示|写到)|根据(?:这份)?素材")),
    ("thin_information", re.compile(r"现场的?确定信息(?:并)?不复杂|目前能确认的信息(?:并)?不算多")),
    (
        "material_boundary_exposure",
        re.compile(
            r"公开材料|(?:视频新闻)?题名|材料边界|"
            r"(?:这条|当前)(?:消息|信息|新闻)[^。！？]{0,18}(?:能支撑|边界)|"
            r"公开信息目前只有|"
            r"(?:现有|目前|当前)[^。！？]{0,12}(?:文字信息|公开内容)[^。！？]{0,12}(?:不多|有限|只有|标题级)|"
            r"(?:视频|新闻)[^。！？]{0,8}(?:没有同步|具体怎么展开|提到的)|"
            r"(?:现在|目前)(?:可以|能)?确认(?:的)?事实边界"
        ),
    ),
    ("not_but_template", re.compile(r"(?:这|它)?不(?:只)?是[^。！？]{1,50}而是")),
    ("ordinary_people_not_intuitive", re.compile(r"对(?:普通人|普通[^，。！？]{0,12})(?:来说)?[^。！？]{0,30}(?:可能只是|不直观|不好理解|难理解)")),
    ("put_in_context", re.compile(r"放(?:在|到)[^。！？]{1,30}(?:里|中)?(?:看|来看)")),
    ("generic_signal", re.compile(r"(?:是|算)一个比较实在的信号")),
    ("generic_connector", re.compile(r"值得关注的是|接下来就看|适合这几类人")),
    ("not_a_complete_guide", re.compile(r"(?:它|这)?不是(?:一份|一个)?完整(?:的)?攻略(?:稿|文)?")),
    (
        "secondary_source_marker",
        re.compile(
            r"公开信息显示"
            r"|"
            r"(?:据|根据)[^，。！？\n]{2,24}(?:报道|消息|发布|通报)"
            r"|[\u4e00-\u9fffA-Za-z0-9·]{2,20}(?:融媒|新闻网|电视台|日报|晚报)(?:报道|消息|发布|称)"
            r"|(?:来源|稿源)[:：]"
        ),
    ),
)


def scan_ai_writing_patterns(title: str, html: str) -> list[str]:
    text = _plain_text(f"{title}\n{html}")
    return [name for name, pattern in _AI_WRITING_PATTERNS if pattern.search(text)]


def validate_draft(draft: dict[str, Any], source_item: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    required_text = ("item_id", "profile_id", "title", "html", "editor_route")
    for key in required_text:
        if not isinstance(draft.get(key), str) or not str(draft[key]).strip():
            reasons.append(f"missing_field:{key}")
    if draft.get("item_id") != source_item.get("id"):
        reasons.append("item_id_mismatch")

    source_text = _plain_text(
        "\n".join(
            str(source_item.get(key) or "") for key in ("title", "summary", "body")
        )
    )
    draft_text = _plain_text(
        f"{draft.get('title') or ''}\n{draft.get('html') or ''}"
    )
    source_numbers = set(_NUMBER.findall(source_text))
    for number in sorted(set(_NUMBER.findall(draft_text)) - source_numbers):
        reasons.append(f"unsupported_number:{number}")

    fact_refs = draft.get("fact_refs")
    if not isinstance(fact_refs, list) or not fact_refs:
        reasons.append("missing_fact_refs")
    else:
        for index, reference in enumerate(fact_refs):
            if not isinstance(reference, dict):
                reasons.append(f"invalid_fact_ref:{index}")
                continue
            evidence = _plain_text(str(reference.get("evidence") or ""))
            if not evidence:
                reasons.append(f"missing_evidence:{index}")
            elif evidence not in source_text:
                reasons.append(f"evidence_not_in_source:{index}")

    for phrase in _FORBIDDEN_IDENTITY:
        if phrase in draft_text:
            reasons.append(f"forbidden_identity_claim:{phrase}")
    for phrase in _PRODUCTION_PHRASES:
        if phrase in draft_text:
            reasons.append(f"production_phrase:{phrase}")
    reasons.extend(f"ai_writing_pattern:{name}" for name in scan_ai_writing_patterns(
        str(draft.get("title") or ""), str(draft.get("html") or "")
    ))
    return reasons


def _plain_text(value: str) -> str:
    return " ".join(unescape(_HTML_TAG.sub(" ", value)).split())
