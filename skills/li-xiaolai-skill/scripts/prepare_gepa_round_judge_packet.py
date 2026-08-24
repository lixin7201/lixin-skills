#!/usr/bin/env python3
"""Build complementary blind A/B packets for one GEPA-lite round."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "references" / "validation"
RUNTIME = VALIDATION / "gepa-lite" / "runtime-prompts.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(manifest: dict[str, object]) -> list[dict[str, str]]:
    value = manifest.get("outputs", manifest.get("items", []))
    if not isinstance(value, list):
        raise ValueError("manifest outputs/items must be a list")
    return value


def common(manifest: dict[str, object]) -> list[tuple[str, str]]:
    value = manifest.get("common_files", manifest.get("common_markdown_files", []))
    if not isinstance(value, list):
        raise ValueError("manifest common_files must be a list")
    return sorted((str(item.get("file", item.get("path"))), str(item["sha256"])) for item in value)


def runtime_record(manifest: dict[str, object]) -> tuple[Path, str]:
    value = manifest.get("runtime_packet", manifest.get("run_package"))
    return Path(value.get("file", value.get("path"))), str(value["sha256"])


def validate_run(run_dir: Path, expected_ids: set[str]) -> dict[str, object]:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    output_rows = rows(manifest)
    if len(output_rows) != len(expected_ids) or {str(row["id"]) for row in output_rows} != expected_ids:
        raise ValueError(f"{run_dir}: output IDs do not match runtime")
    for row in output_rows:
        path = run_dir / str(row["file"])
        if digest(path) != row["sha256"]:
            raise ValueError(f"{run_dir}: output hash drift: {path.name}")
    path, expected = runtime_record(manifest)
    if path != RUNTIME or digest(path) != expected:
        raise ValueError(f"{run_dir}: runtime path/hash mismatch")
    return manifest


def response(run_dir: Path, item_id: str) -> Path:
    matches = sorted(run_dir.glob(f"{item_id}*.md"))
    if len(matches) != 1:
        raise ValueError(f"{run_dir}: expected one response for {item_id}, got {matches}")
    return matches[0]


def order(round_number: int, item_id: str) -> tuple[str, str]:
    seed = f"li-xiaolai-gepa-lite-r{round_number}:{item_id}"
    bit = int(hashlib.sha256(seed.encode()).hexdigest(), 16) & 1
    return ("baseline", "candidate") if bit == 0 else ("candidate", "baseline")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    args = parser.parse_args()

    round_root = VALIDATION / "gepa-lite" / f"round-{args.round}"
    packet_root = round_root / "judge-packets"
    mapping_path = round_root / "evaluator-only" / "mapping.json"
    freeze = packet_root / "JUDGE_PACKET_FREEZE.sha256"
    if packet_root.exists():
        raise FileExistsError(f"refusing to overwrite {packet_root}")

    prompts = json.loads(RUNTIME.read_text(encoding="utf-8"))
    expected_ids = {str(item["id"]) for item in prompts}
    baseline_manifest = validate_run(args.baseline_dir, expected_ids)
    candidate_manifest = validate_run(args.candidate_dir, expected_ids)
    if common(baseline_manifest) != common(candidate_manifest):
        raise ValueError("A/B invalid: common file paths or hashes differ")
    if baseline_manifest.get("overlay") not in (None, {}):
        raise ValueError("baseline manifest unexpectedly declares an overlay")
    if not candidate_manifest.get("overlay"):
        raise ValueError("candidate manifest lacks overlay provenance")

    run_dirs = {"baseline": args.baseline_dir, "candidate": args.candidate_dir}
    mapping: dict[str, dict[str, dict[str, str]]] = {"judge_a": {}, "judge_b": {}}
    frozen: list[Path] = []
    for item in prompts:
        item_id = str(item["id"])
        texts = {name: response(path, item_id).read_text(encoding="utf-8") for name, path in run_dirs.items()}
        a_order = order(args.round, item_id)
        for judge, condition_order in {"judge_a": a_order, "judge_b": (a_order[1], a_order[0])}.items():
            pair = packet_root / judge / item_id
            pair.mkdir(parents=True, exist_ok=False)
            task = pair / "task.json"
            task.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            frozen.append(task)
            for label, condition in zip(("A", "B"), condition_order):
                path = pair / f"{label}.md"
                path.write_text(texts[condition], encoding="utf-8")
                frozen.append(path)
                mapping[judge].setdefault(item_id, {})[label] = condition

    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    frozen.append(mapping_path)
    freeze.parent.mkdir(parents=True, exist_ok=True)
    freeze.write_text(
        "\n".join(f"{digest(path)}  {os.path.relpath(path, packet_root)}" for path in sorted(frozen)) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "round": args.round,
        "pairs_per_judge": len(prompts),
        "freeze_entries": len(frozen),
        "packet_root": str(packet_root),
        "mapping": str(mapping_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
