# Blind A/B Report 2026-07-09

## Setup

- Test cases: 22/22 from `test-prompts.json`.
- Blind method: A/B labels randomized deterministically; key stored in `blind_key.json`.
- Evaluation mode: `structured_dry_run` with 3 rubric profiles, not independent live model judges.

## Result

| Metric | 36kr-skill | baseline |
|---|---:|---:|
| Majority wins | 22 / 22 | 0 / 22 |
| Judge votes | 66 / 66 | 0 / 66 |
| Average score | 8.66 | 7.42 |

## Weakness

该 A/B 是结构化 dry-run，适合做第一轮 Darwin 保留/修正规则，不等同于人工编辑部盲审。
