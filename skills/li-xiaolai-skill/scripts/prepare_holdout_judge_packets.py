#!/usr/bin/env python3
"""Build order-balanced blind A/B views from completed holdout runs."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "references" / "validation"
PROMPTS = VALIDATION / "holdout-prompts.json"
RUN_ROOT = VALIDATION / "runs" / "holdout-v1"
PACKET_ROOT = VALIDATION / "judge-packets" / "holdout-v1"
MAPPING = VALIDATION / "evaluator-only" / "holdout-ab-mapping.json"
FREEZE = PACKET_ROOT / "HOLDOUT_JUDGE_PACKET_FREEZE.sha256"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_response(run_dir: Path, item_id: str) -> Path:
    matches = sorted(run_dir.glob(f"{item_id}*.md"))
    if len(matches) != 1:
        raise ValueError(f"{run_dir}: expected one response for {item_id}, got {matches}")
    return matches[0]


def order_for(item_id: str) -> tuple[str, str]:
    bit = int(hashlib.sha256(f"li-xiaolai-holdout-v1:{item_id}".encode()).hexdigest(), 16) & 1
    return ("unassisted", "skill_assisted") if bit == 0 else ("skill_assisted", "unassisted")


def main() -> None:
    if PACKET_ROOT.exists():
        raise FileExistsError(f"refusing to overwrite frozen packet: {PACKET_ROOT}")
    prompts = json.loads(PROMPTS.read_text(encoding="utf-8"))
    if len(prompts) != 11:
        raise ValueError(f"expected 11 holdout prompts, got {len(prompts)}")

    run_dirs = {
        "unassisted": RUN_ROOT / "baseline",
        "skill_assisted": RUN_ROOT / "skill",
    }
    mapping: dict[str, dict[str, dict[str, str]]] = {"judge_a": {}, "judge_b": {}}
    frozen: list[Path] = []

    for item in prompts:
        item_id = item["id"]
        texts = {
            condition: find_response(run_dir, item_id).read_text(encoding="utf-8")
            for condition, run_dir in run_dirs.items()
        }
        a_order = order_for(item_id)
        for view, order in {"judge_a": a_order, "judge_b": (a_order[1], a_order[0])}.items():
            pair_dir = PACKET_ROOT / view / item_id
            pair_dir.mkdir(parents=True, exist_ok=False)
            task = pair_dir / "task.json"
            task.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            frozen.append(task)
            for label, condition in zip(("A", "B"), order):
                response = pair_dir / f"{label}.md"
                response.write_text(texts[condition], encoding="utf-8")
                frozen.append(response)
                mapping[view].setdefault(item_id, {})[label] = condition

    MAPPING.parent.mkdir(parents=True, exist_ok=True)
    MAPPING.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    frozen.append(MAPPING)
    FREEZE.parent.mkdir(parents=True, exist_ok=True)
    FREEZE.write_text(
        "\n".join(f"{digest(path)}  {os.path.relpath(path, PACKET_ROOT)}" for path in sorted(frozen)) + "\n",
        encoding="utf-8",
    )
    print(f"holdout pairs per judge: {len(prompts)}")
    print("order balance: complementary")
    print(f"packet: {PACKET_ROOT}")


if __name__ == "__main__":
    main()
