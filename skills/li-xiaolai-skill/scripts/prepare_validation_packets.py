#!/usr/bin/env python3
"""Create a blind runtime packet without Darwin answer-key fields."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SOURCE = SKILL_ROOT / "test-prompts.json"
OUTPUT_DIR = SKILL_ROOT / "references" / "validation" / "blind-packets"
OUTPUT = OUTPUT_DIR / "runtime-prompts.json"
FREEZE = OUTPUT_DIR / "PACKET_FREEZE.sha256"
FIXTURE = SKILL_ROOT / "references" / "validation" / "fixtures" / "synthetic-fixtures.md"

FIXTURE_SECTIONS = {
    "t08-compression": "t08-compression / 待压缩稿",
    "t12-where-unlike": "t12-where-unlike / 待诊断稿",
    "t18-anti-template": "t18-anti-template / 题目 A、B、C",
    "t19-de-ai-preservation": "t19-de-ai-preservation / 待去 AI 稿",
    "t20-original-flavor-contrast": "t20-original-flavor-contrast / 共享事实与版本 A—D",
    "t22-protected-quirk": "t22-protected-quirk / 真实试验过程与待恢复稿",
}

PRIVATE_KEYS = {"expected_style_traits", "forbidden_outputs", "scoring_focus"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    tests = json.loads(SOURCE.read_text(encoding="utf-8"))
    packet = []
    for test in tests:
        leaked = PRIVATE_KEYS.intersection(test)
        if leaked != PRIVATE_KEYS:
            raise ValueError(f"{test.get('id')}: incomplete source answer key: {sorted(leaked)}")
        item = {
            "id": test["id"],
            "prompt": test["prompt"],
            "input_materials": test["input_materials"],
        }
        if test["id"] in FIXTURE_SECTIONS:
            item["fixture_file"] = str(FIXTURE)
            item["fixture_section"] = FIXTURE_SECTIONS[test["id"]]
        packet.append(item)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(packet, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    serialized = OUTPUT.read_text(encoding="utf-8")
    for key in PRIVATE_KEYS:
        if key in serialized:
            raise ValueError(f"blind packet leaked private field: {key}")

    freeze_lines = [
        f"{sha256(OUTPUT)}  runtime-prompts.json",
        f"{sha256(FIXTURE)}  ../fixtures/synthetic-fixtures.md",
    ]
    FREEZE.write_text("\n".join(freeze_lines) + "\n", encoding="utf-8")
    print(f"blind prompts: {len(packet)}")
    print(f"private fields leaked: 0")
    print(f"packet: {OUTPUT}")
    print(f"freeze: {FREEZE}")


if __name__ == "__main__":
    main()
