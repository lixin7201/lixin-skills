#!/usr/bin/env python3
"""Validate the topic-angle engine package and its editorial contract."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/angle-lenses.md",
    "references/scoring-rubric.md",
    "references/output-contract.md",
    "references/evaluation-cases.md",
)

SKILL_TOKENS = (
    "angle-only",
    "auto-handoff",
    "review-angle",
    "HOLD_FOR_EVIDENCE",
    "NO_GO",
    "exactly one writing skill",
    "at most three persona",
    "do not write the article body",
)

OUTPUT_FIELDS = (
    "source_facts",
    "audience_relationship",
    "why_now",
    "core_tension",
    "non_obvious_judgment",
    "explicit_exclusions",
    "evidence_and_gaps",
    "strongest_counterargument",
    "reader_payoff",
    "comment_share_trigger",
    "risk_boundary",
    "headline_options",
    "angle_exposition",
    "suggested_structure",
    "writer_handoff",
)

ANGLE_FAMILIES = (
    "change-and-consequence",
    "hidden-cost",
    "counter-consensus",
    "local-human",
    "decision-service",
    "system-mechanism",
)

PERSONAS = (
    "Paul Graham",
    "张一鸣",
    "Andrej Karpathy",
    "Ilya Sutskever",
    "MrBeast",
    "Donald Trump",
    "Steve Jobs",
    "Elon Musk",
    "Charlie Munger",
    "Richard Feynman",
    "Naval Ravikant",
    "Nassim Taleb",
    "张雪峰",
    "孙宇晨",
)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AssertionError(f"cannot read {path}: {exc}") from exc


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")

    if errors:
        return errors

    skill = read_text(root / "SKILL.md")
    contract = read_text(root / "references/output-contract.md")
    lenses = read_text(root / "references/angle-lenses.md")
    rubric = read_text(root / "references/scoring-rubric.md")
    cases = read_text(root / "references/evaluation-cases.md")
    metadata = read_text(root / "agents/openai.yaml")

    if not re.search(r"^name:\s*dayibin-topic-angle-engine\s*$", skill, re.M):
        errors.append("frontmatter name must be dayibin-topic-angle-engine")
    for token in SKILL_TOKENS:
        if token not in skill:
            errors.append(f"SKILL.md missing contract token: {token}")
    for relative in REQUIRED_FILES[2:]:
        if relative not in skill:
            errors.append(f"SKILL.md must link {relative}")
    if "TODO" in "\n".join(read_text(root / p) for p in REQUIRED_FILES):
        errors.append("package contains TODO placeholder")

    for field in OUTPUT_FIELDS:
        if field not in contract:
            errors.append(f"output contract missing field: {field}")
    if contract.count("headline_") < 3:
        errors.append("output contract must require at least three headline variants")

    for family in ANGLE_FAMILIES:
        if family not in lenses:
            errors.append(f"angle lenses missing family: {family}")
    persona_count = sum(persona in lenses for persona in PERSONAS)
    if persona_count != 14:
        errors.append(f"persona lens map must include all 14 personas; found {persona_count}")

    for gate in ("KNOCKOUT", "evidence", "counterargument", "risk", "100"):
        if gate not in rubric:
            errors.append(f"scoring rubric missing: {gate}")

    for case_id in ("CASE-01", "CASE-02", "CASE-03", "CASE-04", "CASE-05"):
        if case_id not in cases:
            errors.append(f"evaluation cases missing: {case_id}")

    if "$dayibin-topic-angle-engine" not in metadata:
        errors.append("openai.yaml default_prompt must mention the skill")
    if 'allow_implicit_invocation: true' not in metadata:
        errors.append("openai.yaml must allow implicit invocation")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    errors = validate(root)
    if errors:
        print("TOPIC_ANGLE_ENGINE_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("TOPIC_ANGLE_ENGINE_VALID")
    print("modes=3 angle_families=6 personas=14 output_fields=15")
    return 0


if __name__ == "__main__":
    sys.exit(main())
