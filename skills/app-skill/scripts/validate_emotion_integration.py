#!/usr/bin/env python3
"""Deterministic guard for the isolated emotion long/short route."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TYPE_DIR = ROOT / "references" / "文稿类型"
EMOTION_FILES = (
    "情感婚恋互动DNA.md",
    "情感婚恋互动.md",
    "情感婚恋互动-内容机制.md",
    "情感婚恋互动-短帖DNA.md",
    "情感婚恋互动-长文DNA.md",
    "情感婚恋互动-原创安全.md",
)
NON_EMOTION_TYPES = (
    "网友曝光热议",
    "城建交通更新",
    "综合本地新闻",
    "政务公告党建",
    "招聘求职信息",
    "突发应急安全",
    "本地生活文旅",
    "公益求助人物",
    "民生服务提醒",
    "体育赛事服务",
)
EDITORS = (
    "流浪啊",
    "大宜宾雯雯",
    "练团长",
    "泡泡呀",
    "采采呀",
    "双双呀",
    "大宜宾-梦竹",
    "馋猫0a6",
    "酒言酒语久久久",
)
EMOTION_ONLY_MARKERS = (
    "【情感讨论·虚构情境】",
    "情感故事长文",
    "700–1600",
    "一对夫妻、一对情侣",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    main_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for name in EMOTION_FILES:
        require((TYPE_DIR / name).is_file(), f"missing emotion file: {name}")

    for phrase in ("情感故事长文", "180–500", "700–1600", "非情感任务禁止读取"):
        require(phrase in main_skill, f"main route missing: {phrase}")

    for type_name in NON_EMOTION_TYPES:
        if type_name != "体育赛事服务":
            require(type_name in main_skill, f"main type route lost: {type_name}")
        text = (TYPE_DIR / f"{type_name}DNA.md").read_text(encoding="utf-8")
        require(not any(marker in text for marker in EMOTION_ONLY_MARKERS), f"emotion leakage: {type_name}")

    editor_dir = ROOT / "references" / "小编风格"
    for editor in EDITORS:
        require(editor in main_skill, f"main editor route lost: {editor}")
        text = (editor_dir / f"{editor}-DNA.md").read_text(encoding="utf-8")
        require(not any(marker in text for marker in EMOTION_ONLY_MARKERS), f"emotion leakage: {editor}")

    tests = json.loads((ROOT / "test-prompts.json").read_text(encoding="utf-8"))
    ids = [item["id"] for item in tests]
    require(len(ids) == len(set(ids)), "duplicate test id")
    require(len(tests) >= 37, "emotion regression tests missing")
    require(sum("情感" in item["route_expected"] for item in tests) >= 8, "emotion routes under-tested")
    require(sum("非情感" in item["route_expected"] for item in tests) >= 2, "non-emotion guards under-tested")

    runtime_text = "\n".join((TYPE_DIR / name).read_text(encoding="utf-8") for name in EMOTION_FILES)
    require("/Users/" not in runtime_text, "private source path leaked")
    require("Documents/" not in runtime_text, "private document path leaked")
    require(".docx" not in runtime_text.lower(), "source document leaked")

    print(json.dumps({
        "status": "PASS",
        "tests": len(tests),
        "emotion_files": len(EMOTION_FILES),
        "non_emotion_types_checked": len(NON_EMOTION_TYPES),
        "editor_dna_checked": len(EDITORS),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
