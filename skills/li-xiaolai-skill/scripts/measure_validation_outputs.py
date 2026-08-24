#!/usr/bin/env python3
"""Measure reproducible paragraph, rhythm, and surface AI-trace metrics."""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from pathlib import Path


AI_PHRASES = [
    "在这个", "在当今", "飞速发展", "首先", "其次", "最后", "总而言之",
    "综上所述", "让我们一起", "携手并进", "开启新篇章", "赋能", "闭环",
    "有专家指出", "研究表明", "众所周知", "业内普遍认为",
]


def visible_length(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def percentile(values: list[int], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return float(ordered[low])
    return ordered[low] * (high - index) + ordered[high] * (index - low)


def max_short_run(lengths: list[int], threshold: int = 20) -> int:
    best = current = 0
    for length in lengths:
        current = current + 1 if length <= threshold else 0
        best = max(best, current)
    return best


def measure(text: str) -> dict[str, object]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    prose = [
        block for block in blocks
        if not block.startswith("#")
        and not block.startswith("|")
        and not re.match(r"^(?:[-*+] |\d+[.)] )", block)
    ]
    lengths = [visible_length(block) for block in prose]
    chars = visible_length(text)
    number_tokens = re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?%?", text)
    return {
        "visible_chars": chars,
        "all_blocks": len(blocks),
        "prose_paragraphs": len(prose),
        "paragraphs_per_1000_chars": round(len(prose) * 1000 / chars, 3) if chars else 0.0,
        "paragraph_length_median": statistics.median(lengths) if lengths else 0,
        "paragraph_length_p90": round(percentile(lengths, 0.9), 3),
        "short_paragraph_ratio_le_20": round(sum(v <= 20 for v in lengths) / len(lengths), 3) if lengths else 0.0,
        "max_consecutive_short_paragraphs_le_20": max_short_run(lengths),
        "section_count": len(re.findall(r"^#{1,6}\s+", text, re.M)),
        "list_item_count": len(re.findall(r"^(?:[-*+] |\d+[.)] )", text, re.M)),
        "question_mark_count": len(re.findall(r"[？?]", text)),
        "em_dash_char_count": text.count("—"),
        "ellipsis_char_count": text.count("…"),
        "ai_phrase_hits": {phrase: text.count(phrase) for phrase in AI_PHRASES if phrase in text},
        "ai_phrase_total": sum(text.count(phrase) for phrase in AI_PHRASES),
        "number_tokens": number_tokens,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    files = sorted(args.run_dir.glob("t*.md"))
    if not files:
        raise SystemExit(f"no t*.md files in {args.run_dir}")
    result = {path.stem: measure(path.read_text(encoding="utf-8")) for path in files}
    output = args.output or args.run_dir / "metrics.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"measured: {len(result)}")
    print(f"output: {output}")


if __name__ == "__main__":
    main()
