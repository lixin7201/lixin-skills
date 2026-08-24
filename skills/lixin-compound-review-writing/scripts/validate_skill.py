#!/usr/bin/env python3
"""Minimal regression check for the personal writing Skill."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    oral = (ROOT / "references/李鑫口语DNA.md").read_text(encoding="utf-8")
    gate = (ROOT / "references/选题标题与日更交接门.md").read_text(encoding="utf-8")
    feishu = (ROOT / "references/飞书每日输入源.md").read_text(encoding="utf-8")
    weights = json.loads((ROOT / "references/dna-weights.json").read_text())
    prompts = json.loads((ROOT / "test-prompts.json").read_text())

    assert skill.startswith("---\nname: lixin-compound-review-writing\n")
    assert "dayibin-topic-angle-engine" in skill
    assert "oepnclaw2" in skill and "狐狸狐狸" in skill
    assert "KDGSwgn6fi2dP6khqOrcwQ2wnoW" in feishu
    assert "GW78dO1D8orQ41xQ8HCcUJsxnxb" in feishu
    assert "--as bot" in feishu and "has_content=false" in feishu
    assert "/Users/REPLACE_ME/AI code/openclaw/tools/lixin_feishu_daily_reader.py" in feishu
    assert "不要在 OpenClaw/Hermes 会话里直接调用裸 `lark-cli`" in feishu
    assert "不得额外运行 `lark-cli profile list`、`doctor`、`auth status`" in feishu
    assert "原话是可选证据" in skill
    assert "至少取得一条公开原话" not in skill
    assert "个人稿至少保留一条公开可用原话" not in oral
    assert "我之前说过一句话" in gate
    assert "注意力可以借，信任只能一篇篇还" in gate
    assert weights["version"] == "2.2.0-feishu-daily-inbox"
    assert all(sum(parts.values()) == 100 for parts in weights["dimensions"].values())
    assert len(prompts) == 33
    assert len({case["id"] for case in prompts}) == 33
    assert len(list((ROOT / "references/native-dna").glob("*/*"))) == 24
    print("LIXIN_WRITING_V22_VALID")


if __name__ == "__main__":
    main()
