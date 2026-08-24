#!/usr/bin/env python3
"""Aggregate frozen independent final de-AI before/after judgments."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "references" / "validation" / "final-de-ai-certification"
MAPPING = FINAL / "evaluator-only" / "mapping.json"
CONDITIONS = ("before", "after")
SUBSETS = ("all", "train", "holdout")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4)


def select(records: list[dict[str, object]], subset: str) -> list[dict[str, object]]:
    return records if subset == "all" else [row for row in records if row["source"] == subset]


def summarize(records: list[dict[str, object]], dimensions: list[str]) -> dict[str, object]:
    result = {}
    for subset in SUBSETS:
        selected = select(records, subset)
        means = {
            condition: {
                dimension: mean([float(row["scores"][condition][dimension]) for row in selected])
                for dimension in dimensions
            }
            for condition in CONDITIONS
        }
        result[subset] = {
            "observations": len(selected),
            "outcomes": {
                outcome: sum(row["after_outcome"] == outcome for row in selected)
                for outcome in ("win", "loss", "tie")
            },
            "means": means,
            "after_minus_before": {
                dimension: round(means["after"][dimension] - means["before"][dimension], 4)
                for dimension in dimensions
            },
        }
    return result


def main() -> None:
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    all_records: list[dict[str, object]] = []
    by_judge = {}
    input_hashes = {str(MAPPING): digest(MAPPING)}
    dimensions: list[str] | None = None

    for judge_key, judge_dirname in (("judge_a", "judge-a"), ("judge_b", "judge-b")):
        judge_dir = FINAL / "judges" / judge_dirname
        pairwise_path = judge_dir / "pairwise.json"
        revealed_path = judge_dir / "revealed.json"
        for filename in (
            "pairwise.json",
            "summary-blind.json",
            "STAGE1_FREEZE.sha256",
            "revealed.json",
            "REVEALED_FREEZE.sha256",
        ):
            path = judge_dir / filename
            input_hashes[str(path)] = digest(path)

        pairwise = json.loads(pairwise_path.read_text(encoding="utf-8"))
        revealed = json.loads(revealed_path.read_text(encoding="utf-8"))
        items = pairwise.get("items", pairwise.get("pairs"))
        if not isinstance(items, list) or len(items) != 3:
            raise ValueError(f"{pairwise_path}: expected three items")
        judge_dimensions = pairwise.get("dimensions", list(items[0]["scores"]["A"].keys()))
        if dimensions is None:
            dimensions = judge_dimensions
        elif dimensions != judge_dimensions:
            raise ValueError("judge dimensions differ")

        records = []
        for item in items:
            item_id = str(item["id"])
            branch = mapping[judge_key][item_id]
            label_by_condition = {condition: label for label, condition in branch.items()}
            after_label = label_by_condition["after"]
            preference = item["preference"]
            outcome = "tie" if preference == "tie" else ("win" if preference == after_label else "loss")
            record = {
                "judge": judge_key,
                "id": item_id,
                "source": item["source"],
                "after_label": after_label,
                "before_label": label_by_condition["before"],
                "blind_preference": preference,
                "after_outcome": outcome,
                "scores": {
                    condition: item["scores"][label_by_condition[condition]]
                    for condition in CONDITIONS
                },
                "hard_gate_hits": item.get("hard_gate_hits", {}),
            }
            records.append(record)
            all_records.append(record)

        judge_summary = summarize(records, judge_dimensions)
        judge_summary["per_item"] = records
        judge_summary["independent_decision"] = revealed.get(
            "independent_decision",
            revealed.get("decision", revealed.get("final_decision")),
        )
        by_judge[judge_key] = judge_summary

    assert dimensions is not None
    aggregate = summarize(all_records, dimensions)
    output = {
        "schema_version": 1,
        "item_count": 3,
        "judge_count": 2,
        "observations": len(all_records),
        "dimensions": dimensions,
        "input_hashes": input_hashes,
        "aggregate": aggregate,
        "by_judge": by_judge,
    }
    output_path = FINAL / "aggregate.json"
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "outcomes": aggregate["all"]["outcomes"],
        "deltas": aggregate["all"]["after_minus_before"],
        "holdout_deltas": aggregate["holdout"]["after_minus_before"],
        "judge_decisions": {
            key: value["independent_decision"] for key, value in by_judge.items()
        },
        "output": str(output_path),
        "sha256": digest(output_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
