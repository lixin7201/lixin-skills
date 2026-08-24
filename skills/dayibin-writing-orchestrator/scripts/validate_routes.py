#!/usr/bin/env python3
"""Validate Dayibin orchestration route references against installed skills."""

from __future__ import annotations

import re
import json
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
OPENCLAW_ROOT = Path("/Users/REPLACE_ME/.openclaw/workspace/skills")
CODEX_ROOT = Path("/Users/REPLACE_ME/.codex/skills")
AUDITOR = "human-writing-soft-audit"

PERSONAS = {
    "paul-graham-perspective",
    "zhang-yiming-perspective",
    "andrej-karpathy-perspective",
    "ilya-sutskever-perspective",
    "mrbeast-perspective",
    "trump-perspective",
    "steve-jobs-perspective",
    "elon-musk-perspective",
    "munger-perspective",
    "feynman-perspective",
    "naval-perspective",
    "taleb-perspective",
    "zhangxuefeng-perspective",
    "sun-yuchen-perspective",
}

WRITERS = {
    "wechat-writing-skill",
    "liurun-skill",
    "36kr-skill",
    "banyuetan-skill",
    "renwu-skill",
    "banfo-skill",
    "caozhi-skill",
    "dongjian-skill",
    "datudou-skill",
    "kazike-skill",
    "kepu-zhongguo-skill",
    "chengdu-meishi-skill",
    "chengde-skill",
    "dangjian-skill",
    "li-xiaolai-skill",
    "bishuxifeng-skill",
}

REQUIRED_TYPES = {
    "城市发展 / 城建交通",
    "产业经济 / 企业商业",
    "民生通知 / 公共服务",
    "民生求助 / 维权 / 冲突",
    "打卡攻略 / 周边玩法 / 本地美食",
    "情怀回忆 / 城市记忆",
    "人物故事 / 创业成长",
    "本地荣誉 / 家乡被看见",
    "活动商业 / 城市资讯",
    "招聘 / 红娘 / 便民服务",
    "观点观察 / 公共议题",
}


def installed(name: str) -> bool:
    return any((root / name / "SKILL.md").is_file() for root in (OPENCLAW_ROOT, CODEX_ROOT))


def installed_dir(name: str):
    for root in (OPENCLAW_ROOT, CODEX_ROOT):
        candidate = root / name
        if (candidate / "SKILL.md").is_file():
            return candidate
    return None


def main() -> int:
    errors: list[str] = []
    skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    route_text = (SKILL_DIR / "references" / "routing-matrix.md").read_text(encoding="utf-8")
    persona_text = (SKILL_DIR / "references" / "persona-topic-map.md").read_text(encoding="utf-8")
    writer_text = (SKILL_DIR / "references" / "writer-map.md").read_text(encoding="utf-8")
    all_text = "\n".join((skill_text, route_text, persona_text, writer_text))

    if "TODO" in all_text:
        errors.append("TODO remains in runtime files")
    if len(skill_text.splitlines()) >= 500:
        errors.append("SKILL.md must remain under 500 lines")

    for name in sorted(PERSONAS | WRITERS | {"dayibin-content-review", AUDITOR}):
        if f"`{name}`" not in all_text:
            errors.append(f"missing documented skill id: {name}")
        if not installed(name):
            errors.append(f"installed SKILL.md not found: {name}")

    try:
        writer_position = skill_text.index("### 5. 执行唯一写稿")
        audit_position = skill_text.index("### 6. Human Writing 软审校")
        review_position = skill_text.index("### 7. 审稿与回炉")
        if not writer_position < audit_position < review_position:
            errors.append("audit step must follow writer and precede final review")
    except ValueError:
        errors.append("audit step must follow writer and precede final review")

    auditor_dir = installed_dir(AUDITOR)
    if auditor_dir:
        inventory_path = auditor_dir / "references" / "writing-skill-inventory.json"
        if not inventory_path.is_file():
            errors.append("human-writing-soft-audit missing writing-skill-inventory.json")
        else:
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            covered = {item.get("name") for item in inventory.get("skills", [])}
            expected = WRITERS | {"app-skill"}
            if covered != expected:
                errors.append(f"audit policy coverage mismatch: expected={len(expected)} actual={len(covered)}")

    if "`renwu-skill`：公众号《人物》的写稿 Skill" not in persona_text:
        errors.append("renwu-skill collision guard is missing")
    if re.search(r"人物.*`renwu-skill`.*选题", route_text):
        errors.append("renwu-skill appears to be used as a persona adviser")

    for article_type in sorted(REQUIRED_TYPES):
        if article_type not in route_text:
            errors.append(f"missing article type: {article_type}")

    if errors:
        print("ROUTE_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("ROUTE_VALIDATION_OK")
    print(f"personas={len(PERSONAS)} writers={len(WRITERS)} article_types={len(REQUIRED_TYPES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
