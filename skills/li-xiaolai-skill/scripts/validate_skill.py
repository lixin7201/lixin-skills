#!/usr/bin/env python3
"""Deterministic structural validation for li-xiaolai-skill."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
BUILD = Path("/Users/REPLACE_ME/.codex/skills/distillation-orchestrator/builds/li-xiaolai-skill")
G04_BUILD = Path(
    "/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/qi-nian-jiu-shi-yi-bei-zi/"
    "world-first-focus-shift"
)
G04_INSTALLED = Path("/Users/REPLACE_ME/.codex/skills/world-first-focus-shift")
CODEX_INSTALL = Path("/Users/REPLACE_ME/.codex/skills/li-xiaolai-skill")


REQUIRED_FILES = [
    "SKILL.md",
    "agents/openai.yaml",
    "test-prompts.json",
    "原味指纹.md",
    "像不像对照样本.md",
    "去AI味保真补丁.md",
    "references/cognition/认知操作系统.md",
    "references/cognition/决策启发式.md",
    "references/cognition/价值观与反模式.md",
    "references/cognition/内在张力与演化.md",
    "references/cognition/智识谱系.md",
    "references/cognition/诚实边界.md",
    "references/methods/方法路由图-v2.md",
    "references/methods/方法增量审计-v2.md",
    "references/writing/语料质量报告.md",
    "references/writing/training-corpus-list.md",
    "references/writing/原味语料分层.md",
    "references/writing/写稿判断框架.md",
    "references/writing/选题判断清单.md",
    "references/writing/读者画像与默认立场.md",
    "references/writing/内容价值观.md",
    "references/writing/反模式与诚实边界.md",
    "references/writing/写稿流程操作手册.md",
    "references/writing/证据索引.md",
    "references/writing/标题DNA.md",
    "references/writing/开头模板.md",
    "references/writing/正文结构模板.md",
    "references/writing/语言DNA.md",
    "references/writing/素材使用规则.md",
    "references/writing/转折与推进规则.md",
    "references/writing/结尾模板.md",
    "references/writing/视觉风格指南.md",
    "references/writing/像不像判别器.md",
    "references/writing/Writing-DNA.md",
    "references/writing/结构与段落指标.md",
    "references/validation/holdout-eval-list.md",
]


def count(pattern: str, path: Path) -> int:
    return len(re.findall(pattern, path.read_text(encoding="utf-8"), re.MULTILINE))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("train", "final"), default="train")
    args = parser.parse_args()

    errors: list[str] = []
    checks: dict[str, object] = {}

    missing = [rel for rel in REQUIRED_FILES if not (ROOT / rel).is_file()]
    checks["required_files"] = {"expected": len(REQUIRED_FILES), "missing": missing}
    if missing:
        errors.append(f"missing required files: {missing}")

    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = skill_text.split("---", 2)[1]
    top_keys = re.findall(r"^([a-zA-Z0-9_-]+):", frontmatter, re.MULTILINE)
    checks["frontmatter_keys"] = top_keys
    if top_keys != ["name", "description"]:
        errors.append(f"frontmatter keys must be name,description: {top_keys}")
    if "## 终稿去 AI 味保真补丁" not in skill_text:
        errors.append("SKILL.md lacks final de-AI preservation hook")

    model_count = count(r"^## M[1-5]｜", ROOT / "references/cognition/认知操作系统.md")
    heuristic_count = count(r"^## H\d{2}｜", ROOT / "references/cognition/决策启发式.md")
    tension_count = count(r"^## \d+\. ", ROOT / "references/cognition/内在张力与演化.md")
    boundary_count = count(r"^\d+\. ", ROOT / "references/cognition/诚实边界.md")
    checks["cognition_counts"] = {
        "models": model_count,
        "heuristics": heuristic_count,
        "tensions": tension_count,
        "boundaries": boundary_count,
    }
    if (model_count, heuristic_count, tension_count, boundary_count) != (5, 9, 8, 20):
        errors.append("cognition counts differ from frozen 5/9/8/20")

    route_text = (ROOT / "references/methods/方法路由图-v2.md").read_text(encoding="utf-8")
    method_rows = re.findall(r"^\| `([^`]+)` \|", route_text, re.MULTILINE)
    base = json.loads((BUILD / "manifests/methods-v1.json").read_text(encoding="utf-8"))
    expected = {item["name"] for item in base["skills"]} | {"world-first-focus-shift"}
    checks["method_rows"] = {"count": len(method_rows), "unique": len(set(method_rows))}
    if len(method_rows) != 28 or set(method_rows) != expected:
        errors.append(
            "method router mismatch: "
            f"missing={sorted(expected-set(method_rows))}, extra={sorted(set(method_rows)-expected)}"
        )

    prompts = json.loads((ROOT / "test-prompts.json").read_text(encoding="utf-8"))
    prompt_fields = {
        "id", "prompt", "input_materials", "expected_style_traits",
        "forbidden_outputs", "scoring_focus",
    }
    prompt_ids = [item.get("id") for item in prompts]
    bad_schema = [item.get("id") for item in prompts if set(item) != prompt_fields]
    checks["test_prompts"] = {
        "count": len(prompts), "unique": len(set(prompt_ids)), "bad_schema": bad_schema,
    }
    if len(prompts) < 22 or len(prompt_ids) != len(set(prompt_ids)) or bad_schema:
        errors.append("test prompt count, uniqueness, or schema failed")

    curation = json.loads(
        (BUILD / "manifests/curated/curation-summary.json").read_text(encoding="utf-8")
    )
    checks["holdout_isolation"] = {
        "overlap": curation["overlap_train_holdout"],
        "manifest_has_body": curation["holdout_contains_body_text"],
    }
    if curation["overlap_train_holdout"] != 0 or curation["holdout_contains_body_text"]:
        errors.append("holdout isolation failed")

    g04_files = ["SKILL.md", "test-prompts.json", "test-results.md"]
    g04_missing = [name for name in g04_files if not (G04_BUILD / name).is_file()]
    checks["g04_build"] = {"missing": g04_missing}
    if g04_missing:
        errors.append(f"G04 build incomplete: {g04_missing}")

    if args.phase == "final":
        installed_missing = [name for name in g04_files if not (G04_INSTALLED / name).is_file()]
        checks["g04_install"] = {"missing": installed_missing}
        if installed_missing:
            errors.append(f"G04 installation incomplete: {installed_missing}")
        checks["codex_install"] = CODEX_INSTALL.is_dir()
        if not CODEX_INSTALL.is_dir():
            errors.append("Codex installation missing")

    result = {"phase": args.phase, "ok": not errors, "checks": checks, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
