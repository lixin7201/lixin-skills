# de-ai-preserve-voice integration smoke · 2026-07-05

## Scope

This smoke covers the de-AI preservation layer added to existing writing Skills and to the future distillation workflow.

Updated targets:

- `de-ai-preserve-voice`
- `banfo-skill`
- `kazike-skill`
- `liurun-skill`
- `dongjian-skill`
- `chengde-skill`
- `dayibin-wechat-writing-gene`
- `chengdu-meishi-skill`
- `fang-wenshan-lyrics-skill` canonical Nuwa boss file
- `writing-dna-skill`
- Codex `writing-dna-skill`
- Codex `writing-style-distiller`

## Static And Integration Checks

| Check | Result |
|---|---|
| `python3 .../verify_de_ai_integration.py` | PASS: 11 targets integrated |
| Shared `test-prompts.json` parses with `jq` | PASS |
| Existing target test prompt JSON files parse with `jq` | PASS: 8 files |
| `python3 banfo-skill/scripts/verify_banfo_skill.py` | PASS: `banfo-smoke-ok` |
| `openclaw skills info` for updated OpenClaw skills | PASS: Ready, visible to model, available as command |
| `openclaw skills check --agent main` | PASS for updated targets; unrelated `session-logs` still has missing `rg` requirement |

OpenClaw emitted existing plugin/config warnings about Feishu allowlist and plugin metadata. They are unrelated to these Skill files.

## Live Agent Regression Samples

Each sample ran through `openclaw agent --local --agent main` with a short prompt and no delivery channel.

| Skill | Session key | Evidence | Result |
|---|---|---|---|
| `banfo-skill` | `deai-test-banfo-20260705` | AI accounting app sample kept main object, mechanism reversal, and fact boundary | PASS |
| `kazike-skill` | `deai-test-kazike-20260705` | Browser plugin sample kept tool scene, steps, constraints, and pitfall; no fake hands-on result | PASS |
| `liurun-skill` | `deai-test-liurun-20260705` | Coffee price sample kept problem-essence-mechanism-method and did not delete useful `不是 A，而是 B` reasoning | PASS |
| `dongjian-skill` | `deai-test-dongjian-20260705` | Workplace record sample kept `01/02/03`, judgment, and action chain; no fabricated details | PASS |
| `chengde-skill` | `deai-test-chengde-20260705` | Park night-light sample kept local reader relation and unknown fee/parking boundaries | PASS |
| `dayibin-wechat-writing-gene` | `deai-test-dayibin-gene-20260705` | Yibin night-market sample kept time, local relation, and did not invent parking/traffic/fee info | PASS |
| `chengdu-meishi-skill` | `deai-test-chengdu-meishi-20260705` | Douhua-rice sample kept taste/action advice and did not invent price/address/queue hours | PASS |
| `fang-wenshan-lyrics-skill` | `deai-test-fangwenshan-20260705` | Old tea cup lyric sample kept nostalgia branch, main object, singability, and avoided generic AI ancient-style words | PASS |

## Guardrails Confirmed

- The de-AI pass is final-only; it does not replace each Skill's writing engine.
- Target DNA outranks generic de-AI rules.
- Facts, prices, locations, routes, comments, interviews, screenshots, security claims, and music-platform facts are not invented for naturalness.
- Author-specific patterns are protected when they are real DNA: Liu Run concept contrast, Dongjian numbering, Banfo mechanism reversal, Fang Wenshan object/chorus structure.
- Local account Skills keep article type and editor-route boundaries instead of averaging voices.

## Known Limits

This is a smoke/regression pass, not a full Darwin blind holdout. It proves the wiring works and the short live samples did not show style damage. A stricter future pass should run each existing holdout/test prompt set before and after with independent scoring.
