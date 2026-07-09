# Targeted Blind A/B Rerun 20260709 - caozhi-skill

## Setup
- Cases rerun: 7 weak/narrow cases from full run.
- New side: patched `with_skill`; baseline side: fixed old baseline output from `full_blind_ab_20260709`.
- Judges: 3 independent OpenClaw local judge runs.
- Scope: targeted rerun, not a full fresh 22-case rerun.

## Targeted Result
| Metric | patched skill | old baseline |
|---|---:|---:|
| Majority wins | 5 / 7 | 2 / 7 |
| Judge votes | 15 / 21 | 6 / 21 |
| Average overall score | 7.43 | 6.76 |

## Adjusted Full-Set Read
| Metric | patched skill | baseline |
|---|---:|---:|
| Majority wins | 20 / 22 | 2 / 22 |
| Judge votes | 60 / 66 | 6 / 66 |
| Average overall score | 8.30 | 7.45 |

## Per-Test Rerun
| Test | Majority | Skill votes | Baseline votes | Skill avg | Baseline avg |
|---|---|---:|---:|---:|---:|
| t02 | with_skill_new | 3 | 0 | 7.33 | 5.00 |
| t06 | with_skill_new | 3 | 0 | 8.00 | 6.00 |
| t11 | with_skill_new | 3 | 0 | 8.00 | 6.33 |
| t14 | baseline_old | 0 | 3 | 6.00 | 8.00 |
| t15 | with_skill_new | 3 | 0 | 8.33 | 7.33 |
| t16 | with_skill_new | 3 | 0 | 7.33 | 6.33 |
| t19 | baseline_old | 0 | 3 | 7.00 | 8.33 |

## Remaining Weak Cases
- `t14`: 0-3, avg 6.0 vs 8.0; judge_1_style_editor:A A有具体通勤鞋现场，非模板感强; judge_2_fact_process:A A成稿更具体，B对象偏虚; judge_3_skeptical_reader:A A具体到通勤鞋，B仍偏抽象品牌
- `t19`: 0-3, avg 7.0 vs 8.33; judge_1_style_editor:B B先成稿再边界，去味且不磨平; judge_2_fact_process:B B先给改后稿，事实边界稳; judge_3_skeptical_reader:B B先给改后稿，具体对象更强
