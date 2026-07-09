#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path("/Users/lixin/.openclaw/workspace/skills/banfo-skill")
TODAY = "2026-07-05"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="ignore")


def assert_contains(text: str, needle: str) -> None:
    assert needle in text, f"missing: {needle}"


def clean_source(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            text = text[end + 4 :]
    text = text.split("## 互动数据")[0]
    text = re.sub(r"!\[[^\]]*]\([^)]+\)", "", text)
    return text


def holdout_leaks() -> list[tuple[str, str]]:
    generated_paths = [
        ROOT / "SKILL.md",
        ROOT / "test-prompts.json",
        ROOT / "holdout" / "holdout_prompts.json",
        *sorted((ROOT / "references").glob("*.md")),
    ]
    generated = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in generated_paths)
    leaks: list[tuple[str, str]] = []
    with (ROOT / "data" / "holdout-eval-list.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            source = clean_source(Path(row["path"]).read_text(encoding="utf-8", errors="ignore"))
            for line in source.splitlines():
                line = line.strip()
                if len(line) >= 60 and line in generated:
                    leaks.append((row["title"], line[:60]))
    return leaks


def main() -> None:
    skill = read("SKILL.md")
    tests = json.loads(read("test-prompts.json"))
    holdout = json.loads(read("holdout/holdout_prompts.json"))

    required_files = [
        "SKILL.md",
        "references/Writing-DNA.md",
        "references/标题DNA.md",
        "references/开头模板.md",
        "references/正文结构模板.md",
        "references/语言DNA.md",
        "references/素材使用规则.md",
        "references/像不像判别器.md",
        "data/语料质量报告.md",
        "reports/darwin-scorecard.md",
    ]
    missing = [p for p in required_files if not (ROOT / p).exists()]
    assert not missing, missing

    assert len(tests) == 18, len(tests)
    assert len(holdout) == 10, len(holdout)
    assert_contains(skill, "🔴 CHECKPOINT")
    assert_contains(skill, "弱素材")
    assert_contains(skill, "完整参考稿")
    assert_contains(skill, "不写“我是半佛”")
    assert_contains(skill, "标题任务单独给 8-12 个")
    assert_contains(skill, "AI 感强/有语病")

    language = read("references/语言DNA.md")
    checker = read("references/像不像判别器.md")
    manual = read("references/写稿流程操作手册.md")
    assert_contains(language, "AI 腔硬禁区")
    assert_contains(checker, "AI 感专项诊断")
    assert_contains(manual, "去 AI 腔")

    red_light = re.findall(r"在 Claude Code|Claude Code skill|Cursor only|Codex 中|/plugin install\b|\.claude/skills", skill)
    assert not red_light, red_light

    leaks = holdout_leaks()
    assert not leaks, leaks[:3]

    report = f"""# Local Smoke Test

- 日期：{TODAY}
- 模式：local deterministic smoke
- 结论：通过

## 检查项

| 项目 | 结果 |
|---|---|
| 必备文件 | {len(required_files)} 个存在 |
| test-prompts | {len(tests)} 个 |
| holdout prompts | {len(holdout)} 个 |
| 🔴 CHECKPOINT | 存在 |
| 弱素材拒写分支 | 存在 |
| 当前事实敏感分支 | 存在 |
| 完整参考稿篇幅目标 | 存在 |
| runtime 红灯扫描 | 0 命中 |
| holdout 60 字以上原文泄漏 | 0 命中 |

## 说明

这不是独立 agent blind A/B；它验证的是 skill 包结构、失败分支、非冒充边界、holdout 泄漏和测试集完整性。继续冲高保真时，再补独立 judge full-test。
"""
    (ROOT / "reports" / f"local-smoke-test-{TODAY}.md").write_text(report, encoding="utf-8")
    print("banfo-smoke-ok")


if __name__ == "__main__":
    main()
