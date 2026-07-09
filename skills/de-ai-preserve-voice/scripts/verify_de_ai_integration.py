#!/usr/bin/env python3
from pathlib import Path

ROOT = Path("/Users/lixin/.openclaw/workspace/skills")
CODEX = Path("/Users/lixin/.codex/skills")

TARGETS = {
    "banfo-skill": ROOT / "banfo-skill/SKILL.md",
    "kazike-skill": ROOT / "kazike-skill/SKILL.md",
    "liurun-skill": ROOT / "liurun-skill/SKILL.md",
    "dongjian-skill": ROOT / "dongjian-skill/SKILL.md",
    "chengde-skill": ROOT / "chengde-skill/SKILL.md",
    "dayibin-wechat-writing-gene-skill": ROOT / "dayibin-wechat-writing-gene-skill/SKILL.md",
    "chengdu-meishi-skill": ROOT / "chengdu-meishi-skill/SKILL.md",
    "fang-wenshan-lyrics-skill": ROOT / "nuwa-skill/bosses/fang-wenshan-lyrics-skill/SKILL.md",
    "openclaw-writing-dna-skill": ROOT / "writing-dna-skill/SKILL.md",
    "codex-writing-dna-skill": CODEX / "writing-dna-skill/SKILL.md",
    "codex-writing-style-distiller": CODEX / "writing-style-distiller/SKILL.md",
}

COMMON = [
    "终稿去 AI 味保真补丁",
    "de-ai-preserve-voice",
]

SPECIFIC = {
    "liurun-skill": ["不是 A，而是 B", "不一刀切"],
    "dongjian-skill": ["数字分节", "不删除洞见式"],
    "banfo-skill": ["主物件", "机制反转"],
    "kazike-skill": ["不编造亲测", "现场入口"],
    "chengde-skill": ["本地事实", "类型 DNA"],
    "dayibin-wechat-writing-gene-skill": ["本地事实", "小编线"],
    "chengdu-meishi-skill": ["价格、地址", "小编线"],
    "fang-wenshan-lyrics-skill": ["支线", "可唱性"],
    "openclaw-writing-dna-skill": ["去AI味保真补丁.md"],
    "codex-writing-dna-skill": ["去AI味保真补丁.md"],
    "codex-writing-style-distiller": ["去AI味保真补丁.md", "验证"],
}


def require(name: str, path: Path) -> list[str]:
    if not path.exists():
        return [f"{name}: missing {path}"]
    text = path.read_text(encoding="utf-8")
    missing = [token for token in COMMON if token not in text]
    missing += [token for token in SPECIFIC.get(name, []) if token not in text]
    return [f"{name}: missing token {token!r}" for token in missing]


def main() -> int:
    failures: list[str] = []
    core = ROOT / "de-ai-preserve-voice/SKILL.md"
    tests = ROOT / "de-ai-preserve-voice/test-prompts.json"
    if not core.exists():
        failures.append("shared skill missing")
    elif "段落节奏保真" not in core.read_text(encoding="utf-8"):
        failures.append("shared skill missing paragraph rhythm guard")
    if not tests.exists():
        failures.append("shared test prompts missing")
    for name, path in TARGETS.items():
        failures.extend(require(name, path))
    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"PASS: {len(TARGETS)} targets integrated with de-ai-preserve-voice")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
