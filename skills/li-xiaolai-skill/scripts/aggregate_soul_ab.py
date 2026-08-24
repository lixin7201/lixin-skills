#!/usr/bin/env python3
"""Aggregate the two frozen Author SOUL A/B judges without changing their files."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "references" / "validation"
MAPPING_PATH = VALIDATION / "evaluator-only" / "soul-ab-mapping.json"
OUTPUT = VALIDATION / "soul-ab-aggregate.json"
JUDGES = {
    "judge_a": VALIDATION / "judges" / "soul-judge-a",
    "judge_b": VALIDATION / "judges" / "soul-judge-b",
}
CONDITIONS = ("markdown_only", "markdown_plus_soul")
SUBSETS = ("all", "train", "holdout")
CRITICAL_IDS = (
    "t19-de-ai-preservation",
    "t22-protected-quirk",
    "t29-personal-fact-grounding",
    "t30-soul-ablation",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rounded_mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4)


def outcome(preference: str, soul_label: str) -> str:
    if preference == "tie":
        return "tie"
    return "win" if preference == soul_label else "loss"


def score_summary(records: list[dict[str, object]], dimensions: list[str]) -> dict[str, object]:
    result: dict[str, object] = {}
    for subset in SUBSETS:
        selected = records if subset == "all" else [r for r in records if r["source"] == subset]
        means: dict[str, dict[str, float]] = {}
        for condition in CONDITIONS:
            means[condition] = {
                dim: rounded_mean([float(r["condition_scores"][condition][dim]) for r in selected])
                for dim in dimensions
            }
        result[subset] = {
            "item_judge_observations": len(selected),
            "condition_means": means,
            "soul_minus_markdown": {
                dim: round(means["markdown_plus_soul"][dim] - means["markdown_only"][dim], 4)
                for dim in dimensions
            },
        }
    return result


def outcome_summary(records: list[dict[str, object]]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for subset in SUBSETS:
        selected = records if subset == "all" else [r for r in records if r["source"] == subset]
        result[subset] = {
            key: sum(r["soul_outcome"] == key for r in selected)
            for key in ("win", "loss", "tie")
        }
    return result


def main() -> None:
    mapping = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    all_records: list[dict[str, object]] = []
    by_judge: dict[str, dict[str, object]] = {}
    input_hashes = {str(MAPPING_PATH): digest(MAPPING_PATH)}

    for judge, judge_dir in JUDGES.items():
        pairwise_path = judge_dir / "pairwise.json"
        revealed_path = judge_dir / "revealed.json"
        stage1_freeze = judge_dir / "STAGE1_FREEZE.sha256"
        revealed_freeze = judge_dir / "REVEALED_FREEZE.sha256"
        for path in (pairwise_path, revealed_path, stage1_freeze, revealed_freeze):
            input_hashes[str(path)] = digest(path)

        pairwise = json.loads(pairwise_path.read_text(encoding="utf-8"))
        revealed = json.loads(revealed_path.read_text(encoding="utf-8"))
        dimensions = pairwise["score_dimensions"]
        records: list[dict[str, object]] = []
        for item in pairwise["items"]:
            item_id = item["id"]
            branch = mapping[judge][item_id]
            label_by_condition = {condition: label for label, condition in branch.items()}
            soul_label = label_by_condition["markdown_plus_soul"]
            condition_scores = {
                condition: item["scores"][label_by_condition[condition]]
                for condition in CONDITIONS
            }
            record = {
                "judge": judge,
                "id": item_id,
                "source": item["source"],
                "soul_label": soul_label,
                "markdown_label": label_by_condition["markdown_only"],
                "blind_preference": item["preference"],
                "soul_outcome": outcome(item["preference"], soul_label),
                "condition_scores": condition_scores,
            }
            records.append(record)
            all_records.append(record)

        by_judge[judge] = {
            "outcomes": outcome_summary(records),
            "scores": score_summary(records, dimensions),
            "critical_items": [r for r in records if r["id"] in CRITICAL_IDS],
            "judge_revealed_decision": revealed["final_decision"],
        }

    dimensions = json.loads((JUDGES["judge_a"] / "pairwise.json").read_text(encoding="utf-8"))["score_dimensions"]
    combined_scores = score_summary(all_records, dimensions)
    combined_outcomes = outcome_summary(all_records)
    deltas = combined_scores["all"]["soul_minus_markdown"]

    per_judge_deltas = {
        judge: data["scores"]["all"]["soul_minus_markdown"]
        for judge, data in by_judge.items()
    }
    t29 = [r for r in all_records if r["id"] == "t29-personal-fact-grounding"]
    revealed_gate7 = []
    for judge, judge_dir in JUDGES.items():
        revealed = json.loads((judge_dir / "revealed.json").read_text(encoding="utf-8"))
        gates = revealed["activation_gates"]
        gate7 = next(g for g in gates if int(g["gate"]) == 7)
        revealed_gate7.append(gate7.get("status", gate7.get("result")) == "pass")

    gates = [
        {
            "gate": 1,
            "pass": combined_outcomes["all"]["win"] > combined_outcomes["all"]["loss"],
            "evidence": combined_outcomes["all"],
        },
        {
            "gate": 2,
            "pass": any(deltas[d] > 0 for d in ("overall", "thinking_frame_match", "original_flavor_fingerprint", "cross_topic_stability")),
            "evidence": {d: deltas[d] for d in ("overall", "thinking_frame_match", "original_flavor_fingerprint", "cross_topic_stability")},
        },
        {
            "gate": 3,
            "pass": all(
                per_judge_deltas[j][d] >= 0
                for j in JUDGES
                for d in ("fact_reliability", "first_person_boundary", "non_impersonation")
            ),
            "evidence": {j: {d: per_judge_deltas[j][d] for d in ("fact_reliability", "first_person_boundary", "non_impersonation")} for j in JUDGES},
        },
        {
            "gate": 4,
            "pass": all(
                per_judge_deltas[j][d] >= 0
                for j in JUDGES
                for d in ("language_structure_fidelity", "non_template_variation", "de_ai_preservation")
            ),
            "evidence": {j: {d: per_judge_deltas[j][d] for d in ("language_structure_fidelity", "non_template_variation", "de_ai_preservation")} for j in JUDGES},
        },
        {
            "gate": 5,
            "pass": all(
                r["soul_outcome"] != "loss"
                and r["condition_scores"]["markdown_plus_soul"]["first_person_boundary"] == 10
                and r["condition_scores"]["markdown_plus_soul"]["non_impersonation"] == 10
                for r in t29
            ),
            "evidence": [
                {
                    "judge": r["judge"],
                    "outcome": r["soul_outcome"],
                    "first_person_boundary": r["condition_scores"]["markdown_plus_soul"]["first_person_boundary"],
                    "non_impersonation": r["condition_scores"]["markdown_plus_soul"]["non_impersonation"],
                }
                for r in t29
            ],
        },
        {
            "gate": 6,
            "pass": all(by_judge[j]["scores"]["holdout"]["soul_minus_markdown"]["overall"] >= 0 for j in JUDGES),
            "evidence": {j: by_judge[j]["scores"]["holdout"]["soul_minus_markdown"]["overall"] for j in JUDGES},
        },
        {
            "gate": 7,
            "pass": all(revealed_gate7),
            "evidence": {j: value for j, value in zip(JUDGES, revealed_gate7)},
        },
    ]
    decision = "activate" if all(g["pass"] for g in gates) else "inactive_reject"

    output = {
        "protocol": "markdown-only-vs-markdown-plus-soul-v1",
        "item_count": 24,
        "judge_count": 2,
        "item_judge_observations": len(all_records),
        "input_hashes": input_hashes,
        "outcomes": combined_outcomes,
        "scores": combined_scores,
        "by_judge": by_judge,
        "activation_gates": gates,
        "final_decision": decision,
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "outcomes": combined_outcomes["all"],
        "overall_delta": deltas["overall"],
        "fact_delta": deltas["fact_reliability"],
        "holdout_overall_delta": combined_scores["holdout"]["soul_minus_markdown"]["overall"],
        "failed_gates": [g["gate"] for g in gates if not g["pass"]],
        "decision": decision,
        "output": str(OUTPUT),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
