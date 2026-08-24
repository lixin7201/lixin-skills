#!/usr/bin/env python3
"""Build two order-balanced blind A/B views from completed train runs."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "references" / "validation"
RUNTIME = VALIDATION / "blind-packets" / "runtime-prompts.json"
RUN_ROOT = VALIDATION / "runs" / "train-v1"
BASELINE = RUN_ROOT / "baseline"
SKILL = RUN_ROOT / "skill"
PACKET_ROOT = VALIDATION / "judge-packets" / "train-v1"
MAPPING = VALIDATION / "evaluator-only" / "train-ab-mapping.json"
FREEZE = PACKET_ROOT / "TRAIN_JUDGE_PACKET_FREEZE.sha256"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def response_path(run_dir: Path, test_id: str) -> Path:
    matches = sorted(run_dir.glob(f"{test_id}*.md"))
    if len(matches) != 1:
        raise ValueError(f"{run_dir}: expected one response for {test_id}, got {matches}")
    return matches[0]


def label_order(test_id: str) -> tuple[str, str]:
    bit = int(hashlib.sha256(f"li-xiaolai-darwin-v1:{test_id}".encode()).hexdigest(), 16) & 1
    return ("unassisted", "skill_assisted") if bit == 0 else ("skill_assisted", "unassisted")


def main() -> None:
    if PACKET_ROOT.exists():
        raise FileExistsError(f"refusing to overwrite frozen packet: {PACKET_ROOT}")
    prompts = json.loads(RUNTIME.read_text(encoding="utf-8"))
    if len(prompts) != 28:
        raise ValueError(f"expected 28 prompts, got {len(prompts)}")

    source_dirs = {"unassisted": BASELINE, "skill_assisted": SKILL}
    mapping: dict[str, dict[str, dict[str, str]]] = {"judge_a": {}, "judge_b": {}}
    freeze_paths: list[Path] = []

    for item in prompts:
        test_id = item["id"]
        source_text = {
            condition: response_path(directory, test_id).read_text(encoding="utf-8")
            for condition, directory in source_dirs.items()
        }
        a_order = label_order(test_id)
        views = {
            "judge_a": a_order,
            "judge_b": (a_order[1], a_order[0]),
        }
        for view, order in views.items():
            pair_dir = PACKET_ROOT / view / test_id
            pair_dir.mkdir(parents=True, exist_ok=False)
            task_path = pair_dir / "task.json"
            task_path.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            freeze_paths.append(task_path)
            for label, condition in zip(("A", "B"), order):
                response = pair_dir / f"{label}.md"
                response.write_text(source_text[condition], encoding="utf-8")
                freeze_paths.append(response)
                mapping[view].setdefault(test_id, {})[label] = condition

    MAPPING.parent.mkdir(parents=True, exist_ok=True)
    MAPPING.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    freeze_paths.append(MAPPING)

    lines = []
    for path in sorted(freeze_paths):
        lines.append(f"{sha256_bytes(path.read_bytes())}  {os.path.relpath(path, PACKET_ROOT)}")
    FREEZE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"pairs per judge: {len(prompts)}")
    print("order balance: complementary")
    print(f"packet: {PACKET_ROOT}")
    print(f"mapping: {MAPPING}")


if __name__ == "__main__":
    main()
