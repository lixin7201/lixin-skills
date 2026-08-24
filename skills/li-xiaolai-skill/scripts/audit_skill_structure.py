#!/usr/bin/env python3
"""Collect deterministic evidence for Darwin static dimensions and runtime gates."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
OUTPUT = ROOT / "references" / "validation" / "runs" / "train-v1" / "static-audit.json"

SOFT_PHRASES = ["建议", "可以考虑", "根据情况", "灵活把握", "视情况而定"]
RUNTIME_RED_FLAGS = [
    r"在 Claude Code",
    r"Claude Code skill",
    r"Claude Code 用户",
    r"Cursor only",
    r"Codex 中",
    r"~/\.claude/skills/[a-z]",
    r"/plugin install\b",
]


def main() -> None:
    text = SKILL.read_text(encoding="utf-8")
    frontmatter_match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not frontmatter_match:
        raise ValueError("missing frontmatter")
    frontmatter = frontmatter_match.group(1)
    name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.M)
    description_match = re.search(r"^description:\s*(.+)$", frontmatter, re.M)
    refs = sorted(set(re.findall(r"`((?:references/|原味指纹\.md|像不像对照样本\.md|去AI味保真补丁\.md)[^`]*)`", text)))
    ref_checks = []
    for raw in refs:
        if raw.startswith("references/") or raw.endswith(".md"):
            path = ROOT / raw
            ref_checks.append({"reference": raw, "exists": path.exists()})

    result = {
        "skill": str(SKILL),
        "line_count": len(text.splitlines()),
        "frontmatter": {
            "name": name_match.group(1) if name_match else None,
            "description_chars": len(description_match.group(1)) if description_match else 0,
            "only_name_description": len([line for line in frontmatter.splitlines() if ":" in line]) == 2,
        },
        "workflow_numbered_steps": len(re.findall(r"^###\s+\d+\.", text, re.M)),
        "fallback_rows": len(re.findall(r"^\|[^\n]+\|[^\n]+\|[^\n]+\|$", text[text.find("## 失败与 fallback"):text.find("## 终稿去 AI")], re.M)) - 2,
        "explicit_checkpoints": len(re.findall(r"终检|事实门|身份门|质量门", text)),
        "soft_phrase_hits": {phrase: text.count(phrase) for phrase in SOFT_PHRASES if phrase in text},
        "runtime_red_flags": [pattern for pattern in RUNTIME_RED_FLAGS if re.search(pattern, text)],
        "red_blacklist_bullets": len(re.findall(r"^- 不", text[text.find("## 红灯黑名单"):], re.M)),
        "reference_checks": ref_checks,
        "missing_references": [item["reference"] for item in ref_checks if not item["exists"]],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
