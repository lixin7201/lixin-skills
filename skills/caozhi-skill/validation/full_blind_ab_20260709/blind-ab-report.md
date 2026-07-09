# Full Blind A/B Report 20260709 - caozhi-skill

## Setup
- Test cases: 22/22 from `test-prompts.json`.
- Generations: `with_skill` uses `/caozhi-skill` in 2 batches; baseline explicitly forbidden from reading local skill/DNA.
- Judges: 3 independent OpenClaw local judge runs.
- Blind method: A/B labels randomized with seed `2026070904`; key stored separately in `blind_key.json`.
- Scope: prompt-set blind A/B, not human editorial review or external fact check.

## Result
| Metric | with_skill | baseline |
|---|---:|---:|
| Majority wins | 16 / 22 | 6 / 22 |
| Judge votes | 49 / 66 | 17 / 66 |
| Average overall score | 8.35 | 7.92 |

## Per-Test Votes
| Test | Majority | Skill votes | Baseline votes | Skill avg | Baseline avg |
|---|---|---:|---:|---:|---:|
| t01 | with_skill | 3 | 0 | 8.83 | 8.00 |
| t02 | with_skill | 2 | 1 | 8.00 | 7.83 |
| t03 | with_skill | 3 | 0 | 8.50 | 7.50 |
| t04 | with_skill | 3 | 0 | 8.83 | 8.00 |
| t05 | with_skill | 3 | 0 | 8.50 | 7.50 |
| t06 | baseline | 0 | 3 | 7.50 | 8.33 |
| t07 | with_skill | 3 | 0 | 8.83 | 8.00 |
| t08 | with_skill | 3 | 0 | 8.33 | 7.50 |
| t09 | with_skill | 3 | 0 | 8.83 | 8.00 |
| t10 | with_skill | 3 | 0 | 8.50 | 7.50 |
| t11 | baseline | 1 | 2 | 8.00 | 8.17 |
| t12 | with_skill | 3 | 0 | 8.83 | 8.00 |
| t13 | with_skill | 3 | 0 | 8.83 | 8.00 |
| t14 | baseline | 0 | 3 | 6.67 | 8.33 |
| t15 | baseline | 0 | 3 | 7.50 | 8.50 |
| t16 | baseline | 1 | 2 | 7.67 | 8.17 |
| t17 | with_skill | 3 | 0 | 8.83 | 7.83 |
| t18 | with_skill | 3 | 0 | 8.83 | 7.50 |
| t19 | baseline | 0 | 3 | 7.67 | 8.50 |
| t20 | with_skill | 3 | 0 | 8.50 | 7.67 |
| t21 | with_skill | 3 | 0 | 8.83 | 8.00 |
| t22 | with_skill | 3 | 0 | 8.83 | 7.50 |

## Weak / Narrow Cases
- `t02`: majority=with_skill, votes 2-1, avg 8.0 vs 7.83; judge_1_style_editor:A A有示范句，更像可复用改法; judge_2_fact_process:B 边界更稳，不硬示范; judge_3_skeptical_reader:A 示范句更贴槽值
- `t06`: majority=baseline, votes 0-3, avg 7.5 vs 8.33; judge_1_style_editor:B B诊断更聚焦，改法更落地; judge_2_fact_process:B 诊断更聚焦可执行; judge_3_skeptical_reader:B 诊断更具体少模板
- `t11`: majority=baseline, votes 1-2, avg 8.0 vs 8.17; judge_1_style_editor:A A路线差异更清楚，少套题; judge_2_fact_process:A 路线迁移更清楚; judge_3_skeptical_reader:B 双路线更像成稿
- `t14`: majority=baseline, votes 0-3, avg 6.67 vs 8.33; judge_1_style_editor:A A贴合材料，比较更有效; judge_2_fact_process:A 贴合材料且比较有效; judge_3_skeptical_reader:A 贴任务且有对照
- `t15`: majority=baseline, votes 0-3, avg 7.5 vs 8.5; judge_1_style_editor:B B新题更少套路，情绪更准; judge_2_fact_process:B 新题不过拟合更自然; judge_3_skeptical_reader:B 新题更自然少套壳
- `t16`: majority=baseline, votes 1-2, avg 7.67 vs 8.17; judge_1_style_editor:B B示例判断更具体有现场; judge_2_fact_process:A 不补题，边界更干净; judge_3_skeptical_reader:A 不硬造AB更稳
- `t19`: majority=baseline, votes 0-3, avg 7.67 vs 8.5; judge_1_style_editor:A A去味且守住事实边界; judge_2_fact_process:A 保留事实边界更准; judge_3_skeptical_reader:A 更守去味和边界

## Gate Read
- Blind A/B >=80% majority gate: FAIL (16/22).
- Fact/non-impersonation issues: no external fact check in this automated blind run; judges penalized visible fabrication/impersonation.
