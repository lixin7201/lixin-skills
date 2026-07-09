# Full Blind A/B Report 20260709 - dongjian-skill

## Setup
- Test cases: 22/22 from `test-prompts.json`.
- Generations: `with_skill` uses `/dongjian-skill` in 2 batches; baseline explicitly forbidden from reading local skill/DNA.
- Judges: 3 independent OpenClaw local judge runs.
- Blind method: A/B labels randomized with seed `2026070903`; key stored separately in `blind_key.json`.
- Scope: prompt-set blind A/B, not human editorial review or external fact check.

## Result
| Metric | with_skill | baseline |
|---|---:|---:|
| Majority wins | 20 / 22 | 2 / 22 |
| Judge votes | 55 / 66 | 11 / 66 |
| Average overall score | 8.48 | 7.68 |

## Per-Test Votes
| Test | Majority | Skill votes | Baseline votes | Skill avg | Baseline avg |
|---|---|---:|---:|---:|---:|
| T01 | with_skill | 3 | 0 | 8.00 | 7.00 |
| T02 | with_skill | 3 | 0 | 8.33 | 7.33 |
| T03 | with_skill | 3 | 0 | 8.33 | 6.67 |
| T04 | with_skill | 2 | 1 | 8.00 | 7.67 |
| T05 | with_skill | 2 | 1 | 8.00 | 7.67 |
| T06 | with_skill | 3 | 0 | 8.33 | 7.33 |
| T07 | with_skill | 3 | 0 | 8.33 | 7.33 |
| T08 | with_skill | 3 | 0 | 8.33 | 5.67 |
| T09 | with_skill | 3 | 0 | 9.00 | 8.00 |
| T10 | with_skill | 2 | 1 | 8.67 | 8.67 |
| T11 | baseline | 0 | 3 | 7.33 | 8.33 |
| T12 | with_skill | 3 | 0 | 9.00 | 8.00 |
| T13 | with_skill | 3 | 0 | 9.00 | 8.00 |
| T14 | with_skill | 3 | 0 | 9.00 | 8.00 |
| T15 | with_skill | 2 | 1 | 7.67 | 7.67 |
| T16 | with_skill | 3 | 0 | 9.00 | 7.33 |
| T17 | with_skill | 2 | 1 | 8.33 | 8.00 |
| T18 | with_skill | 3 | 0 | 9.00 | 8.00 |
| t19 | baseline | 0 | 3 | 7.33 | 9.00 |
| t20 | with_skill | 3 | 0 | 9.33 | 8.00 |
| t21 | with_skill | 3 | 0 | 9.33 | 8.00 |
| t22 | with_skill | 3 | 0 | 9.00 | 7.33 |

## Weak / Narrow Cases
- `T10`: majority=with_skill, votes 2-1, avg 8.67 vs 8.67; judge_1_style_editor:B B克制且不补事实; judge_2_fact_process:B B更克制，安全提醒更完整; judge_3_skeptical_reader:A A未成年人安全边界更全
- `T11`: majority=baseline, votes 0-3, avg 7.33 vs 8.33; judge_1_style_editor:B B双角度区分更清; judge_2_fact_process:B B两个角度区分更清楚; judge_3_skeptical_reader:B B两个角度区分更清
- `T15`: majority=with_skill, votes 2-1, avg 7.67 vs 7.67; judge_1_style_editor:A A结构和行动链更完整; judge_2_fact_process:B B避开原句且不冒充过拟合; judge_3_skeptical_reader:A A处境判断行动链更足
- `t19`: majority=baseline, votes 0-3, avg 7.33 vs 9.0; judge_1_style_editor:A A保留故事顺序和行动; judge_2_fact_process:A A去味后故事链保留更好; judge_3_skeptical_reader:A A去味后故事链保留更好

## Gate Read
- Blind A/B >=80% majority gate: PASS (20/22).
- Fact/non-impersonation issues: no external fact check in this automated blind run; judges penalized visible fabrication/impersonation.
