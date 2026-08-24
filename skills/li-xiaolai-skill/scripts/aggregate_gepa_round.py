#!/usr/bin/env python3
"""Aggregate one frozen GEPA-lite round from pairwise scores and mapping."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "references" / "validation" / "gepa-lite"
CONDITIONS = ("baseline", "candidate")
SUBSETS = ("all", "train", "holdout")
CRITICAL_IDS = {
    "t11-two-angles", "t12-where-unlike", "t16-blind-ab",
    "t18-anti-template", "t19-de-ai-preservation",
    "t27-impersonation", "t29-personal-fact-grounding",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4)


def summarize_scores(records: list[dict[str, object]], dimensions: list[str]) -> dict[str, object]:
    result = {}
    for subset in SUBSETS:
        selected = records if subset == "all" else [r for r in records if r["source"] == subset]
        means = {
            condition: {
                dim: mean([float(r["scores"][condition][dim]) for r in selected])
                for dim in dimensions
            }
            for condition in CONDITIONS
        }
        result[subset] = {
            "observations": len(selected),
            "means": means,
            "candidate_minus_baseline": {
                dim: round(means["candidate"][dim] - means["baseline"][dim], 4)
                for dim in dimensions
            },
        }
    return result


def summarize_outcomes(records: list[dict[str, object]]) -> dict[str, object]:
    result = {}
    for subset in SUBSETS:
        selected = records if subset == "all" else [r for r in records if r["source"] == subset]
        result[subset] = {
            outcome: sum(r["candidate_outcome"] == outcome for r in selected)
            for outcome in ("win", "loss", "tie")
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, required=True)
    args = parser.parse_args()

    round_root = VALIDATION / f"round-{args.round}"
    mapping_path = round_root / "evaluator-only" / "mapping.json"
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    all_records: list[dict[str, object]] = []
    by_judge = {}
    input_hashes = {str(mapping_path): digest(mapping_path)}
    dimensions: list[str] | None = None

    for judge_key, judge_dirname in (("judge_a", "judge-a"), ("judge_b", "judge-b")):
        judge_dir = round_root / "judges" / judge_dirname
        pairwise_path = judge_dir / "pairwise.json"
        revealed_path = judge_dir / "revealed.json"
        for name in ("pairwise.json", "summary-blind.json", "STAGE1_FREEZE.sha256", "revealed.json", "REVEALED_FREEZE.sha256"):
            path = judge_dir / name
            input_hashes[str(path)] = digest(path)
        pairwise = json.loads(pairwise_path.read_text(encoding="utf-8"))
        revealed = json.loads(revealed_path.read_text(encoding="utf-8"))
        judge_dimensions = pairwise.get("score_dimensions", pairwise.get("dimensions"))
        if judge_dimensions is None:
            judge_dimensions = list(pairwise["items"][0]["scores"]["A"].keys())
        if dimensions is None:
            dimensions = judge_dimensions
        elif dimensions != judge_dimensions:
            raise ValueError("judge dimensions differ")
        records = []
        pairwise_items = pairwise.get("items", pairwise.get("pairs"))
        if not isinstance(pairwise_items, list):
            raise ValueError(f"{pairwise_path}: expected items or pairs list")
        for item in pairwise_items:
            item_id = item.get("id", item.get("task_id"))
            branch = mapping[judge_key][item_id]
            label_by_condition = {condition: label for label, condition in branch.items()}
            candidate_label = label_by_condition["candidate"]
            preference = item["preference"]
            candidate_outcome = "tie" if preference == "tie" else ("win" if preference == candidate_label else "loss")
            record = {
                "judge": judge_key,
                "id": item_id,
                "source": item["source"],
                "candidate_label": candidate_label,
                "baseline_label": label_by_condition["baseline"],
                "blind_preference": preference,
                "candidate_outcome": candidate_outcome,
                "scores": {
                    condition: item["scores"][label_by_condition[condition]]
                    for condition in CONDITIONS
                },
                "hard_gate_hits": item.get("hard_gate_hits", {}),
            }
            records.append(record)
            all_records.append(record)
        by_judge[judge_key] = {
            "outcomes": summarize_outcomes(records),
            "scores": summarize_scores(records, dimensions),
            "critical": [r for r in records if r["id"] in CRITICAL_IDS],
            "revealed_decision": revealed.get(
                "final_decision",
                revealed.get("decision", revealed.get("independent_decision")),
            ),
        }

    assert dimensions is not None
    output = {
        "round": args.round,
        "item_count": 21,
        "judge_count": 2,
        "observations": len(all_records),
        "input_hashes": input_hashes,
        "outcomes": summarize_outcomes(all_records),
        "scores": summarize_scores(all_records, dimensions),
        "by_judge": by_judge,
    }
    output_path = round_root / "aggregate.json"
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "round": args.round,
        "outcomes": output["outcomes"]["all"],
        "deltas": output["scores"]["all"]["candidate_minus_baseline"],
        "holdout_overall_delta": output["scores"]["holdout"]["candidate_minus_baseline"]["overall"],
        "judge_decisions": {j: data["revealed_decision"] for j, data in by_judge.items()},
        "output": str(output_path),
        "sha256": digest(output_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
