#!/usr/bin/env python3
"""Read-only expression metrics for the frozen Li Xiaolai writing training set.

The script deliberately accepts no holdout path. It reads the fixed training
manifest, the exact body files named by that manifest, and matching metadata
rows from the source ledger. Results are printed to stdout; no files are
created or modified.
"""

from __future__ import annotations

import hashlib
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path


BUILD_ROOT = Path(
    "/Users/REPLACE_ME/.codex/skills/distillation-orchestrator/builds/li-xiaolai-skill"
)
PROVIDED_WECHAT_ROOT = Path("/Users/REPLACE_ME/Documents/学习/重点学习公众号/李笑来")
TRAIN_MANIFEST = BUILD_ROOT / "manifests/curated/writing-train.jsonl"
SOURCE_LEDGER = BUILD_ROOT / "manifests/curated/source-ledger.jsonl"

EPOCH_ORDER = (
    "classic_pre_genai",
    "modern_pre_chatgpt",
    "ai_transition_era",
    "current_hybrid_era",
    "unknown",
)

SYNTHETIC_EXAMPLES = (
    "我猜，问题不在工具太少。至少在这件事上，工具越多，逃避真正练习的入口反而越多。",
    "你以为自己在“准备”，可若准备从不进入交付，它更准确的名字可能是拖延。",
    "为什么记了很多笔记，问题还是没解决？",
)

MARKERS = {
    "first_person": ("我们", "咱们", "本人", "我"),
    "second_person": ("你们", "你"),
    "transition": (
        "但是", "但", "不过", "可是", "然而", "所以", "于是", "因此",
        "反过来", "换句话说", "也就是说", "事实上", "其实", "更重要的是",
        "问题是", "不妨", "比如", "例如", "即便", "尽管", "既然", "否则",
        "首先", "其次", "最后",
    ),
    "certainty": (
        "一定", "必然", "显然", "当然", "肯定", "毫无疑问", "事实上",
        "就是", "根本", "从来", "永远", "绝对", "必须", "无非", "其实",
    ),
    "epistemic_softener": (
        "我猜", "我觉得", "我认为", "在我看来", "可能", "也许", "或许",
        "大概", "恐怕", "似乎", "某种意义上", "某种程度上",
    ),
    "example": ("比如", "例如", "举个例子", "举例", "不妨看看"),
    "definition": ("所谓", "指的是", "意思是", "换句话说", "也就是说"),
    "contrast_frame": ("不是", "而是", "并不是", "却", "反倒", "反过来"),
    "reader_directive": ("你可以", "你应该", "你必须", "你要", "不妨", "试试", "记住"),
    "colloquial_particle": ("啊", "吧", "嘛", "呢", "呗", "罢", "麽", "啦", "喽", "咯"),
    "humor_or_tease": (
        "哈哈", "呵呵", "好玩", "搞笑", "逗", "笑死", "乐了", "调侃",
        "扯淡", "胡说八道", "活该", "拉倒",
    ),
    "rough_or_sharp": (
        "傻", "笨", "蠢", "二货", "装逼", "撕逼", "放屁", "扯淡", "滚",
        "恶心", "可怜", "无耻", "混蛋", "狗屁", "屁话", "脑残", "白痴",
    ),
    "time_scene": (
        "今天", "昨天", "最近", "有一天", "前两天", "小时候", "很多年前",
        "早上", "晚上", "当年", "曾经", "后来", "当时",
    ),
    "call_to_action": ("不妨", "试试", "去做", "请", "别忘", "记住", "欢迎", "行动起来"),
}

PUNCTUATION = {
    "question": "？?",
    "exclamation": "！!",
    "colon": "：:",
    "semicolon": "；;",
    "ellipsis": "…",
    "em_dash": "—",
    "double_hyphen": "--",
    "open_quote": "“「『",
    "parenthesis": "（(",
    "slash": "/／",
}

MARKDOWN_HEADING_RE = re.compile(r"^#{1,6}\s+")
NUMBERED_HEADING_RE = re.compile(
    r"^(?:第[一二三四五六七八九十百0-9]+[章节部分篇]|"
    r"[一二三四五六七八九十]+[、.．]|"
    r"[（(][一二三四五六七八九十0-9]+[）)])"
)
LIST_RE = re.compile(
    r"^(?:[-*+]\s+|[•·▪◦]\s*|\d+[.)、．]\s*|"
    r"[（(]\d+[）)]\s*|[一二三四五六七八九十]+、\s*)"
)
BLOCKQUOTE_RE = re.compile(r"^>\s*")
IMAGE_RE = re.compile(
    r"!\[[^]]*]\([^)]*\)|\[(?:图片|图像|插图)[^]]*]|"
    r"(?:^|\s)(?:图片|图像|插图)\s*\d*\s*(?:$|[:：])|<img\b",
    re.IGNORECASE,
)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?；;])")
FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*(?:\n|\Z)", re.DOTALL)
MARKDOWN_IMAGE_LINE_RE = re.compile(r"^\s*!\[[^]]*]\([^)]*\)\s*$")
EXPORT_BYLINE_RE = re.compile(r"^>\s*[^\n]*·[^\n]*·\s*\d{4}-\d{2}-\d{2}")
EXPORT_LINK_RE = re.compile(r"^>\s*\[原文链接]\([^)]*\)\s*$")
ARCHIVE_HEADER_RE = re.compile(
    r"^(?:版权声明\s*)?本文首发自微信公共帐?号|"
    r"^无需授权即可转载|^转载时请务必注明作者"
)
ARCHIVE_RELATED_FOOTER_RE = re.compile(
    r"^以下是最近写过的《七年就是一辈子》中的内容"
)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def visible_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def quantile(values: list[int], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac


def term_count(text: str, terms: tuple[str, ...]) -> int:
    # Longest-first alternation avoids double counting 我 inside 我们, etc.
    pattern = re.compile("|".join(re.escape(term) for term in sorted(terms, key=len, reverse=True)))
    return len(pattern.findall(text))


def longest_micro_run(lengths: list[int], threshold: int = 30) -> int:
    best = current = 0
    for length in lengths:
        if length <= threshold:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def strip_markdown_inline(text: str) -> str:
    text = re.sub(r"!\[[^]]*]\([^)]*\)", "", text)
    text = re.sub(r"\[([^]]+)]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"(?:\*\*|__|`)", "", text)
    return text


def prepare_content(row: dict, raw_text: str) -> tuple[str, str, list[str]]:
    """Return plain prose, structural source text, and visible prose blocks.

    The provided WeChat files include export metadata and duplicated title/link
    wrappers. Those are not authorial prose. We remove them from prose metrics
    while retaining the remaining Markdown as structural evidence.
    """
    structural_text = raw_text
    if row.get("source_collection") == "provided_wechat_export":
        structural_text = FRONTMATTER_RE.sub("", structural_text, count=1)
        lines = structural_text.splitlines()
        if lines and re.match(r"^#\s+", lines[0]):
            lines = lines[1:]
        lines = [
            line for line in lines
            if not EXPORT_BYLINE_RE.search(line) and not EXPORT_LINK_RE.search(line)
        ]
        for index, line in enumerate(lines):
            if re.fullmatch(r"#{1,6}\s*互动数据\s*", line.strip()):
                lines = lines[:index]
                while lines and lines[-1].strip() in {"", "---"}:
                    lines.pop()
                break
        structural_text = "\n".join(lines)
    elif row.get("source_collection") == "xiaolai_co_archive":
        lines = structural_text.splitlines()
        while lines and (not lines[0].strip() or ARCHIVE_HEADER_RE.search(lines[0].strip())):
            lines.pop(0)
        for index, line in enumerate(lines):
            if ARCHIVE_RELATED_FOOTER_RE.search(line.strip()):
                lines = lines[:index]
                break
        structural_text = "\n".join(lines)

    prose_lines = [
        line for line in structural_text.splitlines()
        if not MARKDOWN_IMAGE_LINE_RE.fullmatch(line)
    ]
    prose_blocks = []
    for line in prose_lines:
        block = line.strip()
        if not block:
            continue
        block = re.sub(r"^#{1,6}\s+", "", block)
        block = re.sub(r"^>\s*", "", block)
        block = LIST_RE.sub("", block)
        block = strip_markdown_inline(block).strip()
        if block:
            prose_blocks.append(block)
    return "\n".join(prose_blocks), structural_text, prose_blocks


def body_path_for(row: dict) -> Path:
    rel = row["source_path"]
    if "holdout" in rel.lower():
        raise RuntimeError(f"Refusing holdout-like path in training manifest: {rel}")
    raw = Path(rel)
    path = (raw if raw.is_absolute() else BUILD_ROOT / raw).resolve()
    allowed_roots = (BUILD_ROOT.resolve(), PROVIDED_WECHAT_ROOT.resolve())
    if not any(root == path or root in path.parents for root in allowed_roots):
        raise RuntimeError(f"Training path escapes build root: {rel}")
    return path


def analyze_document(row: dict, ledger_row: dict) -> dict:
    path = body_path_for(row)
    text = path.read_text(encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if digest != row["body_sha256"]:
        raise RuntimeError(f"Body checksum mismatch: {row['source_id']}")
    if ledger_row.get("body_sha256") and ledger_row["body_sha256"] != digest:
        raise RuntimeError(f"Ledger checksum mismatch: {row['source_id']}")

    text, structural_text, blocks = prepare_content(row, text)
    structural_blocks = [line.strip() for line in structural_text.splitlines() if line.strip()]
    block_lengths = [visible_len(block) for block in blocks]
    sentences = [
        segment.strip()
        for segment in SENTENCE_SPLIT_RE.split(text)
        if visible_len(segment.strip())
    ]
    sentence_lengths = [visible_len(sentence) for sentence in sentences]
    chars = visible_len(text)
    opening = "".join(blocks[:3])[:300]
    closing = "".join(blocks[-3:])[-300:]
    title = row.get("title", "")

    marker_counts = {name: term_count(text, terms) for name, terms in MARKERS.items()}
    punctuation_counts = {
        name: text.count(charspec) if name == "double_hyphen" else sum(text.count(char) for char in charspec)
        for name, charspec in PUNCTUATION.items()
    }

    heading_blocks = sum(
        bool(MARKDOWN_HEADING_RE.search(block) or NUMBERED_HEADING_RE.search(block))
        for block in structural_blocks
    )
    list_blocks = sum(bool(LIST_RE.search(BLOCKQUOTE_RE.sub("", block))) for block in structural_blocks)
    blockquotes = sum(bool(BLOCKQUOTE_RE.search(block)) for block in structural_blocks)
    image_placeholders = len(IMAGE_RE.findall(structural_text))
    quote_spans = sum(text.count(char) for char in "“「『")
    colon_led_blocks = sum(block.endswith(("：", ":")) for block in blocks)
    standalone_punct_blocks = sum(bool(re.fullmatch(r"[：:；;，,。！？!?…—]+", block)) for block in blocks)

    opening_flags = {
        "question": any(char in opening for char in "？?"),
        "first_person": term_count(opening, MARKERS["first_person"]) > 0,
        "time_scene": term_count(opening, MARKERS["time_scene"]) > 0,
        "example": term_count(opening, MARKERS["example"]) > 0,
        "softened_claim": term_count(opening, MARKERS["epistemic_softener"]) > 0,
        "reader_address": term_count(opening, MARKERS["second_person"]) > 0,
    }
    closing_flags = {
        "question": any(char in closing for char in "？?"),
        "first_person": term_count(closing, MARKERS["first_person"]) > 0,
        "certainty": term_count(closing, MARKERS["certainty"]) > 0,
        "call_to_action": term_count(closing, MARKERS["call_to_action"]) > 0,
        "reader_address": term_count(closing, MARKERS["second_person"]) > 0,
        "exclamation": any(char in closing for char in "！!"),
    }
    title_flags = {
        "question": any(char in title for char in "？?"),
        "exclamation": any(char in title for char in "！!"),
        "colon": any(char in title for char in "：:"),
        "dash": any(char in title for char in "—-"),
        "bracket": any(char in title for char in "《》【】[]"),
        "digit": bool(re.search(r"\d", title)),
        "first_person": term_count(title, MARKERS["first_person"]) > 0,
        "second_person": term_count(title, MARKERS["second_person"]) > 0,
    }

    return {
        "source_id": row["source_id"],
        "epoch": row.get("epoch", "unknown"),
        "genre": row.get("genre", "unknown"),
        "source_collection": row.get("source_collection", "unknown"),
        "chars": chars,
        "blocks": len(blocks),
        "block_lengths": block_lengths,
        "sentences": len(sentences),
        "sentence_lengths": sentence_lengths,
        "micro_run": longest_micro_run(block_lengths),
        "marker_counts": marker_counts,
        "punctuation_counts": punctuation_counts,
        "heading_blocks": heading_blocks,
        "list_blocks": list_blocks,
        "blockquotes": blockquotes,
        "image_placeholders": image_placeholders,
        "quote_spans": quote_spans,
        "colon_led_blocks": colon_led_blocks,
        "standalone_punct_blocks": standalone_punct_blocks,
        "opening_flags": opening_flags,
        "closing_flags": closing_flags,
        "title_len": visible_len(title),
        "title_flags": title_flags,
        "latin_words": len(re.findall(r"\b[A-Za-z][A-Za-z0-9_+.-]*\b", text)),
        "number_tokens": len(re.findall(r"(?<!\w)\d+(?:[.,]\d+)?%?(?!\w)", text)),
    }


def aggregate(documents: list[dict]) -> dict:
    article_count = len(documents)
    total_chars = sum(doc["chars"] for doc in documents)
    total_blocks = sum(doc["blocks"] for doc in documents)
    total_sentences = sum(doc["sentences"] for doc in documents)
    block_lengths = [length for doc in documents for length in doc["block_lengths"]]
    sentence_lengths = [length for doc in documents for length in doc["sentence_lengths"]]
    micro_runs = [doc["micro_run"] for doc in documents]
    title_lengths = [doc["title_len"] for doc in documents]

    marker_metrics = {}
    for name in MARKERS:
        count = sum(doc["marker_counts"][name] for doc in documents)
        coverage = sum(doc["marker_counts"][name] > 0 for doc in documents)
        marker_metrics[name] = {
            "count": count,
            "per_1000_chars": round(count * 1000 / total_chars, 3) if total_chars else 0,
            "article_coverage_pct": round(coverage * 100 / article_count, 1) if article_count else 0,
        }

    punctuation_metrics = {}
    for name in PUNCTUATION:
        count = sum(doc["punctuation_counts"][name] for doc in documents)
        coverage = sum(doc["punctuation_counts"][name] > 0 for doc in documents)
        punctuation_metrics[name] = {
            "count": count,
            "per_1000_chars": round(count * 1000 / total_chars, 3) if total_chars else 0,
            "article_coverage_pct": round(coverage * 100 / article_count, 1) if article_count else 0,
        }

    def structural(field: str) -> dict:
        count = sum(doc[field] for doc in documents)
        coverage = sum(doc[field] > 0 for doc in documents)
        return {
            "count": count,
            "per_1000_chars": round(count * 1000 / total_chars, 3) if total_chars else 0,
            "article_coverage_pct": round(coverage * 100 / article_count, 1) if article_count else 0,
        }

    def lexical(field: str) -> dict:
        count = sum(doc[field] for doc in documents)
        coverage = sum(doc[field] > 0 for doc in documents)
        return {
            "count": count,
            "per_1000_chars": round(count * 1000 / total_chars, 3) if total_chars else 0,
            "article_coverage_pct": round(coverage * 100 / article_count, 1) if article_count else 0,
        }

    def flag_metrics(container: str) -> dict:
        keys = documents[0][container].keys() if documents else []
        return {
            key: {
                "articles": sum(doc[container][key] for doc in documents),
                "article_pct": round(sum(doc[container][key] for doc in documents) * 100 / article_count, 1)
                if article_count else 0,
            }
            for key in keys
        }

    return {
        "articles": article_count,
        "chars_no_whitespace": total_chars,
        "article_chars_mean": round(total_chars / article_count, 1) if article_count else 0,
        "article_chars_median": round(statistics.median([doc["chars"] for doc in documents]), 1) if documents else 0,
        "visible_blocks": total_blocks,
        "blocks_per_1000_chars": round(total_blocks * 1000 / total_chars, 2) if total_chars else 0,
        "block_length_mean": round(statistics.mean(block_lengths), 2) if block_lengths else 0,
        "block_length_median": round(statistics.median(block_lengths), 2) if block_lengths else 0,
        "block_length_p90": round(quantile(block_lengths, 0.9), 2),
        "blocks_le_20_pct": round(sum(length <= 20 for length in block_lengths) * 100 / len(block_lengths), 1)
        if block_lengths else 0,
        "blocks_le_30_pct": round(sum(length <= 30 for length in block_lengths) * 100 / len(block_lengths), 1)
        if block_lengths else 0,
        "micro_run_le_30_max": max(micro_runs, default=0),
        "micro_run_le_30_article_median": round(statistics.median(micro_runs), 1) if micro_runs else 0,
        "micro_run_le_30_article_p90": round(quantile(micro_runs, 0.9), 1),
        "sentences": total_sentences,
        "sentences_per_1000_chars": round(total_sentences * 1000 / total_chars, 2) if total_chars else 0,
        "sentence_length_mean": round(statistics.mean(sentence_lengths), 2) if sentence_lengths else 0,
        "sentence_length_median": round(statistics.median(sentence_lengths), 2) if sentence_lengths else 0,
        "sentence_length_p90": round(quantile(sentence_lengths, 0.9), 2),
        "title_length_mean": round(statistics.mean(title_lengths), 2) if title_lengths else 0,
        "title_length_median": round(statistics.median(title_lengths), 2) if title_lengths else 0,
        "markers": marker_metrics,
        "punctuation": punctuation_metrics,
        "structure": {
            name: structural(name)
            for name in (
                "heading_blocks", "list_blocks", "blockquotes", "image_placeholders",
                "quote_spans", "colon_led_blocks", "standalone_punct_blocks",
            )
        },
        "opening": flag_metrics("opening_flags"),
        "closing": flag_metrics("closing_flags"),
        "titles": flag_metrics("title_flags"),
        "lexical": {
            "latin_words": lexical("latin_words"),
            "number_tokens": lexical("number_tokens"),
        },
        "genres": dict(Counter(doc["genre"] for doc in documents)),
        "collections": dict(Counter(doc["source_collection"] for doc in documents)),
    }


def main() -> None:
    if "holdout" in str(TRAIN_MANIFEST).lower():
        raise RuntimeError("Training manifest path unexpectedly contains holdout")
    manifest = read_jsonl(TRAIN_MANIFEST)
    ids = [row["source_id"] for row in manifest]
    if len(ids) != 206 or len(set(ids)) != 206:
        raise RuntimeError(f"Expected 206 unique training rows, got {len(ids)} / {len(set(ids))}")

    # Read the permitted source ledger once, then retain only training IDs.
    id_set = set(ids)
    ledger = {
        row["source_id"]: row
        for row in read_jsonl(SOURCE_LEDGER)
        if row.get("source_id") in id_set
    }
    missing = id_set - set(ledger)
    if missing:
        raise RuntimeError(f"Missing {len(missing)} training IDs from source ledger")

    raw_training_texts = {
        row["source_id"]: body_path_for(row).read_text(encoding="utf-8")
        for row in manifest
    }
    documents = [analyze_document(row, ledger[row["source_id"]]) for row in manifest]
    by_epoch = defaultdict(list)
    by_genre = defaultdict(list)
    by_collection = defaultdict(list)
    for doc in documents:
        by_epoch[doc["epoch"]].append(doc)
        by_genre[doc["genre"]].append(doc)
        by_collection[doc["source_collection"]].append(doc)

    exact_marker_counts = {
        marker: sum(
            prepare_content(
                row,
                raw_training_texts[row["source_id"]],
            )[0].count(marker)
            for row in manifest
        )
        for marker in (
            "我猜", "我觉得", "我认为", "说实话", "其实", "事实上", "换句话说",
            "也就是说", "你可以", "你会发现", "我们", "你们", "大多数人",
            "绝大多数", "很多人", "少数人", "某种意义上", "某种程度上",
            "为什么", "怎么办", "问题是", "更重要的是", "不妨", "当然", "不过",
            "但是", "于是", "所以", "结果", "最终", "后来", "当时", "曾经",
            "比如", "例如", "不是", "而是", "首先", "其次", "最后",
        )
    }

    result = {
        "scope": {
            "manifest": str(TRAIN_MANIFEST),
            "ledger": str(SOURCE_LEDGER),
            "training_rows": len(manifest),
            "unique_source_ids": len(set(ids)),
            "all_body_hashes_verified": True,
            "holdout_opened": False,
            "paragraph_proxy": "non-empty visible source blocks after archive cleaning",
            "sentence_proxy": "segments ending in Chinese or ASCII sentence punctuation",
            "synthetic_examples_absent_from_training": all(
                example not in text
                for example in SYNTHETIC_EXAMPLES
                for text in raw_training_texts.values()
            ),
        },
        "overall": aggregate(documents),
        "by_epoch": {
            epoch: aggregate(by_epoch.get(epoch, []))
            for epoch in EPOCH_ORDER
        },
        "by_genre": {name: aggregate(docs) for name, docs in sorted(by_genre.items())},
        "by_collection": {name: aggregate(docs) for name, docs in sorted(by_collection.items())},
        "exact_discourse_marker_counts": exact_marker_counts,
        "diagnostic_outliers": {
            "largest_micro_runs": [
                {
                    "source_id": doc["source_id"],
                    "epoch": doc["epoch"],
                    "genre": doc["genre"],
                    "chars": doc["chars"],
                    "blocks": doc["blocks"],
                    "micro_run_le_30": doc["micro_run"],
                }
                for doc in sorted(documents, key=lambda item: item["micro_run"], reverse=True)[:10]
            ],
            "archive_boilerplate": {
                "leading_copyright_articles": sum(
                    any(ARCHIVE_HEADER_RE.search(line.strip()) for line in text.splitlines()[:4])
                    for text in raw_training_texts.values()
                ),
                "related_directory_footer_articles": sum(
                    any(ARCHIVE_RELATED_FOOTER_RE.search(line.strip()) for line in text.splitlines())
                    for text in raw_training_texts.values()
                ),
                "wechat_interaction_footer_articles": sum(
                    any(re.fullmatch(r"#{1,6}\s*互动数据\s*", line.strip()) for line in text.splitlines())
                    for text in raw_training_texts.values()
                ),
                "wechat_frontmatter_articles": sum(
                    bool(FRONTMATTER_RE.search(text))
                    for text in raw_training_texts.values()
                ),
            },
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=False))


if __name__ == "__main__":
    main()
