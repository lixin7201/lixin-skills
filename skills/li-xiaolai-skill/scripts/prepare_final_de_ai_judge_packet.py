#!/usr/bin/env python3
"""Build complementary blind packets for final before/after de-AI certification."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "references" / "validation" / "final-de-ai-certification"
RUNTIME = FINAL / "runtime-prompts.json"
INPUT_FREEZE = FINAL / "FINAL_INPUT_FREEZE.sha256"
CONDITIONS = ("before", "after")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_rows(manifest: dict[str, object]) -> list[dict[str, str]]:
    rows = manifest.get("outputs", manifest.get("items"))
    if not isinstance(rows, list):
        raise ValueError("manifest outputs/items must be a list")
    return rows


def validate_run(run_dir: Path, condition: str, expected_ids: set[str]) -> dict[str, object]:
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest_rows(manifest)
    if len(rows) != len(expected_ids) or {str(row["id"]) for row in rows} != expected_ids:
        raise ValueError(f"{run_dir}: output IDs mismatch")
    for row in rows:
        file_value = str(row.get("file", row.get("path", "")))
        if not file_value:
            raise ValueError(f"{run_dir}: output row lacks file/path")
        path = Path(file_value) if Path(file_value).is_absolute() else run_dir / file_value
        if digest(path) != row["sha256"]:
            raise ValueError(f"{run_dir}: output hash drift: {path.name}")
    soul = manifest.get("soul")
    soul_status = soul.get("status") if isinstance(soul, dict) else soul
    if soul_status != "inactive":
        raise ValueError(f"{run_dir}: Soul is not inactive")
    expected_treatment = condition == "after"
    if manifest.get("treatment_applied") is not expected_treatment:
        raise ValueError(f"{run_dir}: treatment flag mismatch")
    governing = manifest.get("governing_inputs", {})
    freeze = manifest.get("input_freeze", governing.get("input_freeze", {}))
    freeze_file = Path(str(freeze.get("file", freeze.get("path", ""))))
    if freeze_file != INPUT_FREEZE or freeze.get("sha256") != digest(INPUT_FREEZE):
        raise ValueError(f"{run_dir}: input freeze provenance mismatch")
    return manifest


def response(run_dir: Path, item_id: str) -> Path:
    path = run_dir / f"{item_id}.md"
    if not path.is_file() or not path.read_text(encoding="utf-8").strip():
        raise ValueError(f"missing response: {path}")
    return path


def order(item_id: str) -> tuple[str, str]:
    seed = f"li-xiaolai-final-de-ai-v1:{item_id}"
    bit = int(hashlib.sha256(seed.encode()).hexdigest(), 16) & 1
    return CONDITIONS if bit == 0 else (CONDITIONS[1], CONDITIONS[0])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before-dir", type=Path, required=True)
    parser.add_argument("--after-dir", type=Path, required=True)
    args = parser.parse_args()

    packet_root = FINAL / "judge-packets"
    mapping_path = FINAL / "evaluator-only" / "mapping.json"
    freeze_path = packet_root / "JUDGE_PACKET_FREEZE.sha256"
    if packet_root.exists() or mapping_path.exists():
        raise FileExistsError("refusing to overwrite final judge packet or mapping")

    runtime = json.loads(RUNTIME.read_text(encoding="utf-8"))
    expected_ids = {str(item["id"]) for item in runtime}
    run_dirs = {"before": args.before_dir, "after": args.after_dir}
    for condition, run_dir in run_dirs.items():
        validate_run(run_dir, condition, expected_ids)

    mapping: dict[str, dict[str, dict[str, str]]] = {"judge_a": {}, "judge_b": {}}
    frozen: list[Path] = []
    for item in runtime:
        item_id = str(item["id"])
        task_payload = {
            key: item[key]
            for key in ("id", "source", "prompt", "input_materials", "constraints")
            if key in item
        }
        texts = {
            condition: response(run_dir, item_id).read_text(encoding="utf-8")
            for condition, run_dir in run_dirs.items()
        }
        a_order = order(item_id)
        for judge, condition_order in {"judge_a": a_order, "judge_b": (a_order[1], a_order[0])}.items():
            pair_dir = packet_root / judge / item_id
            pair_dir.mkdir(parents=True, exist_ok=False)
            task_path = pair_dir / "task.json"
            task_path.write_text(
                json.dumps(task_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            frozen.append(task_path)
            for label, condition in zip(("A", "B"), condition_order):
                output_path = pair_dir / f"{label}.md"
                output_path.write_text(texts[condition], encoding="utf-8")
                frozen.append(output_path)
                mapping[judge].setdefault(item_id, {})[label] = condition

    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    frozen.append(mapping_path)
    freeze_path.parent.mkdir(parents=True, exist_ok=True)
    freeze_path.write_text(
        "\n".join(
            f"{digest(path)}  {os.path.relpath(path, packet_root)}"
            for path in sorted(frozen)
        ) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "items": len(runtime),
        "pairs_per_judge": len(runtime),
        "freeze_entries": len(frozen),
        "packet_root": str(packet_root),
        "mapping": str(mapping_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
