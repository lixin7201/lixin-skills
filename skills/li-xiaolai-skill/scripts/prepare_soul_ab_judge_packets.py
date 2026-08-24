#!/usr/bin/env python3
"""Build complementary blind views for Markdown-only vs Markdown+SOUL outputs."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "references" / "validation"
RUNTIME = VALIDATION / "soul-ab" / "soul-ab-runtime-prompts.json"
RUN_ROOT = VALIDATION / "runs" / "soul-ab-v1"
PACKET_ROOT = VALIDATION / "judge-packets" / "soul-ab-v1"
MAPPING = VALIDATION / "evaluator-only" / "soul-ab-mapping.json"
FREEZE = PACKET_ROOT / "SOUL_AB_JUDGE_PACKET_FREEZE.sha256"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def response(run_dir: Path, item_id: str) -> Path:
    matches = sorted(run_dir.glob(f"{item_id}*.md"))
    if len(matches) != 1:
        raise ValueError(f"{run_dir}: expected one response for {item_id}, got {matches}")
    return matches[0]


def manifest_rows(manifest: dict[str, object]) -> list[dict[str, str]]:
    rows = manifest.get("outputs", manifest.get("items", []))
    if not isinstance(rows, list):
        raise ValueError("manifest outputs/items must be a list")
    return rows


def common_reads(manifest: dict[str, object]) -> list[tuple[str, str]]:
    rows = manifest.get(
        "common_markdown_files",
        manifest.get("common_markdown_reads", manifest.get("common_files", [])),
    )
    if not isinstance(rows, list):
        raise ValueError("manifest common Markdown reads must be a list")
    normalized = [(str(row.get("file", row.get("path"))), str(row["sha256"])) for row in rows]
    fixture = manifest.get("fixture")
    if isinstance(fixture, dict):
        normalized.append((str(fixture["path"]), str(fixture["sha256"])))
    return sorted(normalized)


def validate_run(run_dir: Path, condition: str, prompt_ids: set[str]) -> dict[str, object]:
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest_rows(manifest)
    ids = {str(row["id"]) for row in rows}
    if ids != prompt_ids or len(rows) != len(prompt_ids):
        raise ValueError(f"{condition}: manifest IDs do not match frozen runtime packet")
    for row in rows:
        path = run_dir / str(row["file"])
        if digest(path) != row["sha256"]:
            raise ValueError(f"{condition}: output hash drift: {path.name}")
    runtime = manifest.get("runtime_packet", manifest.get("run_package"))
    runtime_path = Path(runtime.get("file", runtime.get("path")))
    if runtime["sha256"] != digest(runtime_path) or runtime_path != RUNTIME:
        raise ValueError(f"{condition}: runtime packet hash/path mismatch")
    return manifest


def order(item_id: str) -> tuple[str, str]:
    bit = int(hashlib.sha256(f"li-xiaolai-soul-ab-v1:{item_id}".encode()).hexdigest(), 16) & 1
    return ("markdown_only", "markdown_plus_soul") if bit == 0 else ("markdown_plus_soul", "markdown_only")


def main() -> None:
    if PACKET_ROOT.exists():
        raise FileExistsError(f"refusing to overwrite frozen packet: {PACKET_ROOT}")
    prompts = json.loads(RUNTIME.read_text(encoding="utf-8"))
    if len(prompts) != 24:
        raise ValueError(f"expected 24 prompts, got {len(prompts)}")
    run_dirs = {
        "markdown_only": RUN_ROOT / "markdown-only-clean",
        "markdown_plus_soul": RUN_ROOT / "markdown-soul",
    }
    prompt_ids = {str(item["id"]) for item in prompts}
    manifests = {
        condition: validate_run(run_dir, condition, prompt_ids)
        for condition, run_dir in run_dirs.items()
    }
    if common_reads(manifests["markdown_only"]) != common_reads(manifests["markdown_plus_soul"]):
        raise ValueError("A/B invalid: common Markdown read sets or hashes differ")
    if "soul_file" in manifests["markdown_only"]:
        raise ValueError("A/B invalid: Markdown-only manifest declares a Soul read")
    if "soul_file" not in manifests["markdown_plus_soul"]:
        raise ValueError("A/B invalid: Markdown+SOUL manifest lacks the Soul read")
    mapping: dict[str, dict[str, dict[str, str]]] = {"judge_a": {}, "judge_b": {}}
    frozen: list[Path] = []

    for item in prompts:
        item_id = item["id"]
        texts = {condition: response(run_dir, item_id).read_text(encoding="utf-8") for condition, run_dir in run_dirs.items()}
        a_order = order(item_id)
        for view, condition_order in {"judge_a": a_order, "judge_b": (a_order[1], a_order[0])}.items():
            pair = PACKET_ROOT / view / item_id
            pair.mkdir(parents=True, exist_ok=False)
            task = pair / "task.json"
            task.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            frozen.append(task)
            for label, condition in zip(("A", "B"), condition_order):
                path = pair / f"{label}.md"
                path.write_text(texts[condition], encoding="utf-8")
                frozen.append(path)
                mapping[view].setdefault(item_id, {})[label] = condition

    MAPPING.parent.mkdir(parents=True, exist_ok=True)
    MAPPING.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    frozen.append(MAPPING)
    FREEZE.parent.mkdir(parents=True, exist_ok=True)
    FREEZE.write_text(
        "\n".join(f"{digest(path)}  {os.path.relpath(path, PACKET_ROOT)}" for path in sorted(frozen)) + "\n",
        encoding="utf-8",
    )
    print(f"pairs_per_judge: {len(prompts)}")
    print("orders: complementary")
    print(f"packet: {PACKET_ROOT}")
    print(f"mapping: {MAPPING}")


if __name__ == "__main__":
    main()
