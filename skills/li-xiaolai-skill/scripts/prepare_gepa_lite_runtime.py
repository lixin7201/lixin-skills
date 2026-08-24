#!/usr/bin/env python3
"""Prepare the frozen answer-key-free GEPA-lite runtime packet."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "references" / "validation"
BLIND_TRAIN = VALIDATION / "blind-packets" / "runtime-prompts.json"
HOLDOUT = VALIDATION / "holdout-prompts.json"
SUPPLEMENT = Path(
    "/Users/REPLACE_ME/.codex/skills/distillation-orchestrator/builds/"
    "li-xiaolai-skill/soul-v2-staging/soul-supplement-prompts.json"
)
OUTPUT_DIR = VALIDATION / "gepa-lite"
OUTPUT = OUTPUT_DIR / "runtime-prompts.json"
COMMON = OUTPUT_DIR / "common-runtime-files.json"
FREEZE = OUTPUT_DIR / "GEPA_INPUT_FREEZE.sha256"
TRAIN_FREEZE = VALIDATION / "TRAINING_FREEZE.sha256"

TRAIN_IDS = [
    "t01-new-draft", "t02-rewrite", "t11-two-angles", "t12-where-unlike",
    "t16-blind-ab", "t17-cross-topic", "t18-anti-template",
    "t19-de-ai-preservation", "t20-original-flavor-contrast",
    "t21-thinking-transfer", "t22-protected-quirk", "t27-impersonation",
]
SUPPLEMENT_IDS = ["t29-personal-fact-grounding", "t30-soul-ablation"]
HOLDOUT_IDS = ["h01", "h02", "h03", "h06", "h08", "h10", "h11"]
PRIVATE_KEYS = {"expected_style_traits", "forbidden_outputs", "scoring_focus"}

COMMON_FILES = [
    ROOT / "SKILL.md",
    ROOT / "references/cognition/认知操作系统.md",
    ROOT / "references/cognition/诚实边界.md",
    ROOT / "references/cognition/决策启发式.md",
    ROOT / "references/methods/方法路由图-v2.md",
    ROOT / "references/writing/Writing-DNA.md",
    ROOT / "references/writing/写稿判断框架.md",
    ROOT / "references/writing/写稿流程操作手册.md",
    ROOT / "references/writing/像不像判别器.md",
    ROOT / "references/writing/标题DNA.md",
    ROOT / "references/writing/开头模板.md",
    ROOT / "references/writing/正文结构模板.md",
    ROOT / "references/writing/语言DNA.md",
    ROOT / "references/writing/素材使用规则.md",
    ROOT / "references/writing/转折与推进规则.md",
    ROOT / "references/writing/结尾模板.md",
    ROOT / "references/writing/视觉风格指南.md",
    ROOT / "原味指纹.md",
    ROOT / "像不像对照样本.md",
    ROOT / "去AI味保真补丁.md",
    ROOT / "第一人称与身份边界.md",
    ROOT / "个人事实与经历库.md",
    Path("/Users/REPLACE_ME/.openclaw/workspace/skills/de-ai-preserve-voice/SKILL.md"),
]
FIXTURE = VALIDATION / "fixtures" / "synthetic-fixtures.md"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_v1_freeze() -> None:
    for line in TRAIN_FREEZE.read_text(encoding="utf-8").splitlines():
        expected, rel = line.split("  ", 1)
        if digest(ROOT / rel) != expected:
            raise ValueError(f"v1 freeze drift: {rel}")


def normalize(item: dict[str, object]) -> dict[str, object]:
    result = {
        "id": item["id"],
        "source": "train",
        "prompt": item["prompt"],
        "input_materials": item["input_materials"],
    }
    for key in ("fixture_file", "fixture_section"):
        if key in item:
            result[key] = item[key]
    return result


def main() -> None:
    verify_v1_freeze()
    blind = {item["id"]: item for item in json.loads(BLIND_TRAIN.read_text(encoding="utf-8"))}
    supplements = {item["id"]: item for item in json.loads(SUPPLEMENT.read_text(encoding="utf-8"))}
    holdouts = {item["id"]: item for item in json.loads(HOLDOUT.read_text(encoding="utf-8"))}

    packet = [normalize(blind[item_id]) for item_id in TRAIN_IDS]
    packet.extend(normalize(supplements[item_id]) for item_id in SUPPLEMENT_IDS)
    packet.extend({
        "id": holdouts[item_id]["id"],
        "source": "holdout",
        "prompt": holdouts[item_id]["task"],
        "input_materials": holdouts[item_id]["sanitized_input_materials"],
        "constraints": holdouts[item_id]["constraints"],
    } for item_id in HOLDOUT_IDS)

    ids = [item["id"] for item in packet]
    if len(packet) != 21 or len(set(ids)) != 21:
        raise ValueError(f"expected 21 unique items, got {len(packet)}/{len(set(ids))}")
    serialized = json.dumps(packet, ensure_ascii=False, indent=2) + "\n"
    if any(key in serialized for key in PRIVATE_KEYS):
        raise ValueError("answer-key field leaked")
    holdout_text = json.dumps([item for item in packet if item["source"] == "holdout"], ensure_ascii=False)
    for marker in ("source_id", "source_path", "body_sha256", "archive:", "http://", "https://"):
        if marker in holdout_text:
            raise ValueError(f"holdout identifier leaked: {marker}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(serialized, encoding="utf-8")
    common = [{"file": str(path), "sha256": digest(path)} for path in COMMON_FILES]
    common.append({
        "file": str(FIXTURE),
        "sha256": digest(FIXTURE),
        "allowed_ranges": {
            "t12-where-unlike": "35-94",
            "t18-anti-template": "95-120",
            "t19-de-ai-preservation": "121-156",
            "t20-original-flavor-contrast": "157-184",
            "t22-protected-quirk": "185-EOF",
        },
    })
    COMMON.write_text(json.dumps(common, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    frozen = [OUTPUT, COMMON, TRAIN_FREEZE, HOLDOUT, SUPPLEMENT]
    FREEZE.write_text("\n".join(f"{digest(path)}  {path}" for path in frozen) + "\n", encoding="utf-8")
    print(json.dumps({
        "items": len(packet),
        "train": sum(item["source"] == "train" for item in packet),
        "holdout": sum(item["source"] == "holdout" for item in packet),
        "common_records": len(common),
        "answer_key_fields": 0,
        "holdout_identifiers": 0,
        "output": str(OUTPUT),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
