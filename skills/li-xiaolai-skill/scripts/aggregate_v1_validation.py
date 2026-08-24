#!/usr/bin/env python3
"""Aggregate frozen independent-judge results without re-scoring outputs."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "references" / "validation"
JUDGES = VALIDATION / "judges"
MAPPING = json.loads((VALIDATION / "evaluator-only" / "holdout-ab-mapping.json").read_text(encoding="utf-8"))
AGGREGATE = VALIDATION / "v1-aggregate.json"
MATRIX = ROOT / "原文差距矩阵.csv"


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def train_summary(judge: str) -> dict[str, object]:
    data = json.loads((JUDGES / judge / "darwin-revealed.json").read_text(encoding="utf-8"))
    if judge == "judge-a":
        outcome = data["pairwise_outcome_for_skill"]
        condition = data["condition_field_means"]
        dim8 = data["darwin"]["dim8"]
        total = data["darwin"]["total"]
        return {
            "win": outcome["win"], "loss": outcome["loss"], "tie": outcome["tie"],
            "skill_overall": condition["overall"]["skill_assisted"],
            "baseline_overall": condition["overall"]["unassisted"],
            "dim8": dim8, "darwin_total": total,
        }
    outcome = data["pairwise_summary"]
    condition = data["condition_means"]
    return {
        "win": outcome["skill_win"], "loss": outcome["skill_loss"], "tie": outcome["tie"],
        "skill_overall": condition["skill_assisted"]["overall"],
        "baseline_overall": condition["unassisted"]["overall"],
        "dim8": data["darwin"]["dim8_score"],
        "darwin_total": data["darwin"]["total"],
    }


def holdout_scores() -> tuple[dict[str, object], list[dict[str, object]]]:
    per_item: dict[str, dict[str, dict[str, list[float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    outcomes = {}
    dimensions: set[str] = set()

    for judge, branch in (("judge-a", "judge_a"), ("judge-b", "judge_b")):
        data = json.loads((JUDGES / judge / "holdout-pairwise.json").read_text(encoding="utf-8"))
        for item in data["items"]:
            item_id = item["id"]
            for label in ("A", "B"):
                condition = MAPPING[branch][item_id][label]
                normalized = "skill" if condition == "skill_assisted" else "baseline"
                for dimension, value in item[label].items():
                    if dimension == "overall":
                        continue
                    if isinstance(value, (int, float)):
                        per_item[item_id][dimension][normalized].append(float(value))
                        dimensions.add(dimension)

    revealed = {
        judge: json.loads((JUDGES / judge / "holdout-revealed.json").read_text(encoding="utf-8"))
        for judge in ("judge-a", "judge-b")
    }
    outcomes["judge-a"] = revealed["judge-a"]["skill_win_loss_tie"]
    outcomes["judge-b"] = revealed["judge-b"]["skill_win_loss_tie"]

    rows = []
    for item_id in sorted(per_item):
        for dimension in sorted(per_item[item_id]):
            skill_values = per_item[item_id][dimension]["skill"]
            baseline_values = per_item[item_id][dimension]["baseline"]
            rows.append({
                "holdout_id": item_id,
                "dimension": dimension,
                "skill_mean": round(mean(skill_values), 3),
                "baseline_mean": round(mean(baseline_values), 3),
                "delta": round(mean(skill_values) - mean(baseline_values), 3),
                "judge_a_skill": skill_values[0],
                "judge_b_skill": skill_values[1],
                "judge_a_baseline": baseline_values[0],
                "judge_b_baseline": baseline_values[1],
            })

    global_dimensions = {}
    for dimension in sorted(dimensions):
        skill_values = [row["skill_mean"] for row in rows if row["dimension"] == dimension]
        baseline_values = [row["baseline_mean"] for row in rows if row["dimension"] == dimension]
        global_dimensions[dimension] = {
            "skill": round(mean(skill_values), 3),
            "baseline": round(mean(baseline_values), 3),
            "delta": round(mean(skill_values) - mean(baseline_values), 3),
        }

    a_overall = revealed["judge-a"]["condition_overall_means"]
    b_overall = revealed["judge-b"]["condition_means"]
    summary = {
        "outcomes": outcomes,
        "combined_preferences": {
            "win": outcomes["judge-a"]["win"] + outcomes["judge-b"]["win"],
            "loss": outcomes["judge-a"]["loss"] + outcomes["judge-b"]["loss"],
            "tie": outcomes["judge-a"]["tie"] + outcomes["judge-b"]["tie"],
        },
        "skill_overall": round(mean([a_overall["markdown_only_skill"], b_overall["markdown_only_skill"]["overall"]]), 3),
        "baseline_overall": round(mean([a_overall["unassisted"], b_overall["unassisted"]["overall"]]), 3),
        "dimensions": global_dimensions,
    }
    summary["overall_delta"] = round(summary["skill_overall"] - summary["baseline_overall"], 3)
    return summary, rows


def main() -> None:
    train = {judge: train_summary(judge) for judge in ("judge-a", "judge-b")}
    holdout, rows = holdout_scores()
    payload = {"schema_version": "v1-aggregate-1", "train": train, "holdout": holdout}
    AGGREGATE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with MATRIX.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"matrix_rows: {len(rows)}")


if __name__ == "__main__":
    main()
