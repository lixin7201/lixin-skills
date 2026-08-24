#!/usr/bin/env python3
"""Check structural signals in a mentor response.

This is a lint, not a semantic judge. It never proves factual correctness.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_GROUPS = {
    "diagnosis": (r"判断", r"关键矛盾", r"现在.*阶段", r"明确建议", r"目前.*更像"),
    "evidence_boundary": (r"证据", r"公开(经历|决策模型|材料)", r"自报", r"推断", r"待核验"),
    "action": (r"下一步", r"先做", r"动作", r"接下来", r"先.*验证"),
    "sample_or_time": (r"\d+\s*(天|周|条|次|个|人)", r"样本", r"期限"),
    "cost_cap": (r"成本", r"预算", r"上限", r"可承受"),
    "stop_condition": (r"停止(?:或调整)?条件", r"停下", r"退出", r"达到.*就"),
}

HARD_FAIL_PATTERNS = {
    "impersonation": r"(我就是郭晓文|作为郭晓文本人|郭晓文授权我)",
    "guarantee": r"(保证(你|能|一定)|百分之百赚钱|稳赚不赔|必然成功)",
    "unsafe_certainty": r"(绝对不会封号|肯定不违规|一定安全)",
}


def read_text(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", help="UTF-8 response file; omit for stdin")
    args = parser.parse_args()
    text = read_text(args.path)

    checks = {
        name: any(re.search(pattern, text, re.I | re.S) for pattern in patterns)
        for name, patterns in REQUIRED_GROUPS.items()
    }
    hard_fails = {
        name: bool(re.search(pattern, text, re.I | re.S))
        for name, pattern in HARD_FAIL_PATTERNS.items()
    }
    passed = all(checks.values()) and not any(hard_fails.values())
    result = {
        "passed": passed,
        "checks": checks,
        "hard_fails": hard_fails,
        "note": "Structural lint only; verify facts, current rules, fit, and safety manually.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
