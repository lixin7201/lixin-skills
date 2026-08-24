#!/usr/bin/env python3
"""Prepare the frozen three-item final de-AI certification inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "references" / "validation"
FINAL = VALIDATION / "final-de-ai-certification"
SOURCE_RUNTIME = VALIDATION / "gepa-lite" / "runtime-prompts.json"
SOURCE_COMMON = VALIDATION / "gepa-lite" / "common-runtime-files.json"
SOURCE_HOLDOUT_REFERENCE = VALIDATION / "evaluator-only" / "holdout-reference.json"
FIXTURE = VALIDATION / "fixtures" / "synthetic-fixtures.md"
TARGET_PATCH = ROOT / "去AI味保真补丁.md"
GENERIC_PATCH = Path("/Users/REPLACE_ME/.openclaw/workspace/skills/de-ai-preserve-voice/SKILL.md")

IDS = ("t19-de-ai-preservation", "t22-protected-quirk", "h06")
TREATMENT_PATHS = {str(TARGET_PATCH), str(GENERIC_PATCH)}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    FINAL.mkdir(parents=True, exist_ok=True)
    evaluator_only = FINAL / "evaluator-only"
    evaluator_only.mkdir(parents=True, exist_ok=True)

    source_items = {
        item["id"]: item
        for item in json.loads(SOURCE_RUNTIME.read_text(encoding="utf-8"))
    }
    runtime = [source_items[item_id] for item_id in IDS]
    runtime_path = FINAL / "runtime-prompts.json"
    runtime_path.write_text(
        json.dumps(runtime, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    source_common = json.loads(SOURCE_COMMON.read_text(encoding="utf-8"))
    core = []
    treatment = []
    for record in source_common:
        if record["file"] in TREATMENT_PATHS:
            treatment.append(record)
            continue
        if record["file"] == str(FIXTURE):
            record = dict(record)
            record["allowed_ranges"] = {
                "t19-de-ai-preservation": "121-156",
                "t22-protected-quirk": "185-EOF",
            }
        core.append(record)

    if len(core) != 22 or len(treatment) != 2:
        raise ValueError(f"unexpected core/treatment counts: {len(core)}/{len(treatment)}")
    for record in core + treatment:
        path = Path(record["file"])
        if digest(path) != record["sha256"]:
            raise ValueError(f"frozen file drift: {path}")

    core_path = FINAL / "core-files.json"
    treatment_path = FINAL / "treatment-files.json"
    core_path.write_text(json.dumps(core, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    treatment_path.write_text(
        json.dumps(treatment, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    holdout_reference = json.loads(SOURCE_HOLDOUT_REFERENCE.read_text(encoding="utf-8"))
    h06 = next(item for item in holdout_reference["items"] if item["id"] == "h06")
    h06_reference_path = evaluator_only / "h06-reference.json"
    h06_reference_path.write_text(
        json.dumps({"packet_version": "final-de-ai-v1", "item": h06}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    freeze_paths = [
        runtime_path,
        core_path,
        treatment_path,
        h06_reference_path,
        SOURCE_RUNTIME,
        SOURCE_COMMON,
        SOURCE_HOLDOUT_REFERENCE,
        FIXTURE,
        ROOT / "SKILL.md",
        TARGET_PATCH,
        GENERIC_PATCH,
    ]
    freeze_path = FINAL / "FINAL_INPUT_FREEZE.sha256"
    freeze_path.write_text(
        "\n".join(f"{digest(path)}  {path}" for path in freeze_paths) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "items": [item["id"] for item in runtime],
        "core_files": len(core),
        "treatment_files": len(treatment),
        "holdout_reference_items": 1,
        "soul": "inactive",
        "output": str(FINAL),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
