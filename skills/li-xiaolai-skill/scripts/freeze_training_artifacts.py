#!/usr/bin/env python3
"""Write a deterministic checksum manifest for train-side skill artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "references/validation/TRAINING_FREEZE.sha256"


def included(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if "__pycache__" in rel.parts or path == OUTPUT:
        return False
    if rel.parts[0] == "references" and len(rel.parts) > 1:
        return rel.parts[1] in {"cognition", "methods", "research", "writing"}
    return rel.parts[0] in {
        "SKILL.md", "agents", "scripts", "test-prompts.json",
        "原味指纹.md", "像不像对照样本.md", "去AI味保真补丁.md",
    }


def main() -> None:
    files = sorted(path for path in ROOT.rglob("*") if path.is_file() and included(path))
    lines = []
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(ROOT)}")
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(lines)} checksums to {OUTPUT}")


if __name__ == "__main__":
    main()
