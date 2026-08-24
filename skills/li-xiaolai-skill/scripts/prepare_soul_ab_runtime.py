#!/usr/bin/env python3
"""Build the frozen, answer-key-free runtime packet for Author SOUL ablation."""

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
OUTPUT_DIR = VALIDATION / "soul-ab"
OUTPUT = OUTPUT_DIR / "soul-ab-runtime-prompts.json"
FREEZE = OUTPUT_DIR / "SOUL_AB_INPUT_FREEZE.sha256"
TRAIN_FREEZE = VALIDATION / "TRAINING_FREEZE.sha256"

SELECTED_TRAIN = [
    "t01-new-draft",
    "t07-expansion",
    "t09-insufficient-material",
    "t13-positive-control",
    "t15-leakage-memorization",
    "t17-cross-topic",
    "t18-anti-template",
    "t19-de-ai-preservation",
    "t21-thinking-transfer",
    "t22-protected-quirk",
    "t27-impersonation",
]
PRIVATE_KEYS = {"expected_style_traits", "forbidden_outputs", "scoring_focus"}
HOLDOUT_FORBIDDEN_MARKERS = {
    "source_id", "source_path", "body_sha256", "archive:", "http://", "https://"
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_training_freeze() -> None:
    for line in TRAIN_FREEZE.read_text(encoding="utf-8").splitlines():
        expected, rel = line.split("  ", 1)
        path = ROOT / rel
        actual = digest(path)
        if actual != expected:
            raise ValueError(f"v1 training freeze drift: {rel}")


def normalize_train(item: dict[str, object]) -> dict[str, object]:
    result: dict[str, object] = {
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
    verify_training_freeze()
    blind = {item["id"]: item for item in json.loads(BLIND_TRAIN.read_text(encoding="utf-8"))}
    supplement = json.loads(SUPPLEMENT.read_text(encoding="utf-8"))
    holdout = json.loads(HOLDOUT.read_text(encoding="utf-8"))

    packet = [normalize_train(blind[test_id]) for test_id in SELECTED_TRAIN]
    for item in supplement:
        packet.append(normalize_train(item))
    for item in holdout:
        packet.append({
            "id": item["id"],
            "source": "holdout",
            "prompt": item["task"],
            "input_materials": item["sanitized_input_materials"],
            "constraints": item["constraints"],
        })

    ids = [item["id"] for item in packet]
    if len(packet) != 24 or len(set(ids)) != 24:
        raise ValueError(f"expected 24 unique items, got {len(packet)}/{len(set(ids))}")
    serialized = json.dumps(packet, ensure_ascii=False, indent=2) + "\n"
    for key in PRIVATE_KEYS:
        if key in serialized:
            raise ValueError(f"answer-key field leaked: {key}")
    holdout_serialized = json.dumps(
        [item for item in packet if item["source"] == "holdout"], ensure_ascii=False
    )
    for marker in HOLDOUT_FORBIDDEN_MARKERS:
        if marker in holdout_serialized:
            raise ValueError(f"holdout identifier leaked: {marker}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(serialized, encoding="utf-8")
    frozen_paths = [
        OUTPUT,
        TRAIN_FREEZE,
        ROOT / "SKILL.md",
        ROOT / "第一人称与身份边界.md",
        ROOT / "个人事实与经历库.md",
        VALIDATION / "candidates" / "AUTHOR-SOUL.ilang.md",
        VALIDATION / "fixtures" / "synthetic-fixtures.md",
        HOLDOUT,
        SUPPLEMENT,
    ]
    lines = []
    for path in frozen_paths:
        label = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        lines.append(f"{digest(path)}  {label}")
    FREEZE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"runtime_items: {len(packet)}")
    print(f"train: {sum(item['source'] == 'train' for item in packet)}")
    print(f"holdout: {sum(item['source'] == 'holdout' for item in packet)}")
    print("answer_key_fields: 0")
    print("holdout_identifiers: 0")
    print(f"packet: {OUTPUT}")
    print(f"freeze: {FREEZE}")


if __name__ == "__main__":
    main()
