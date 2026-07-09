# Targeted Blind A/B Rerun 20260709 - liurun-skill

## Setup
- Cases rerun: 9 weak/narrow cases from full run.
- New side: patched `with_skill`; baseline side: fixed old baseline output from `full_blind_ab_20260709`.
- Judges: 3 independent OpenClaw local judge runs.
- Scope: targeted rerun, not a full fresh 22-case rerun.

## Targeted Result
| Metric | patched skill | old baseline |
|---|---:|---:|
| Majority wins | 8 / 9 | 1 / 9 |
| Judge votes | 24 / 27 | 3 / 27 |
| Average overall score | 7.93 | 7.11 |

## Adjusted Full-Set Read
| Metric | patched skill | baseline |
|---|---:|---:|
| Majority wins | 21 / 22 | 1 / 22 |
| Judge votes | 61 / 66 | 5 / 66 |
| Average overall score | 8.43 | 7.78 |

## Per-Test Rerun
| Test | Majority | Skill votes | Baseline votes | Skill avg | Baseline avg |
|---|---|---:|---:|---:|---:|
| draft-001 | with_skill_new | 3 | 0 | 8.33 | 7.33 |
| rewrite-001 | with_skill_new | 3 | 0 | 8.33 | 7.33 |
| t08 | with_skill_new | 3 | 0 | 8.00 | 7.00 |
| t12 | with_skill_new | 3 | 0 | 8.17 | 7.33 |
| t14 | with_skill_new | 3 | 0 | 8.33 | 7.67 |
| t16 | baseline_old | 0 | 3 | 5.00 | 6.17 |
| t19 | with_skill_new | 3 | 0 | 8.17 | 7.17 |
| t20 | with_skill_new | 3 | 0 | 8.33 | 6.33 |
| t21 | with_skill_new | 3 | 0 | 8.67 | 7.67 |

## Remaining Weak Cases
- `t16`: 0-3, avg 5.0 vs 6.17; judge_1_style_editor:B B较像评委标准，A太流程说明; judge_2_fact_process:B B更像评判框架但仍未直判; judge_3_skeptical_reader:B B可用维度更清楚但仍偏流程说明
