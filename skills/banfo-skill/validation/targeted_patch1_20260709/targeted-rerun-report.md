# Targeted Blind A/B Rerun 20260709 - banfo-skill

## Setup
- Cases rerun: 10 weak/narrow cases from full run.
- New side: patched `with_skill`; baseline side: fixed old baseline output from `full_blind_ab_20260709`.
- Judges: 3 independent OpenClaw local judge runs.
- Scope: targeted rerun, not a full fresh 22-case rerun.

## Targeted Result
| Metric | patched skill | old baseline |
|---|---:|---:|
| Majority wins | 10 / 10 | 0 / 10 |
| Judge votes | 30 / 30 | 0 / 30 |
| Average overall score | 8.56 | 7.13 |

## Adjusted Full-Set Read
| Metric | patched skill | baseline |
|---|---:|---:|
| Majority wins | 22 / 22 | 0 / 22 |
| Judge votes | 64 / 66 | 2 / 66 |
| Average overall score | 8.76 | 7.56 |

## Per-Test Rerun
| Test | Majority | Skill votes | Baseline votes | Skill avg | Baseline avg |
|---|---|---:|---:|---:|---:|
| t04 | with_skill_new | 3 | 0 | 8.33 | 7.33 |
| t09 | with_skill_new | 3 | 0 | 9.00 | 8.00 |
| t10 | with_skill_new | 3 | 0 | 9.00 | 8.00 |
| t12 | with_skill_new | 3 | 0 | 8.33 | 6.00 |
| t14 | with_skill_new | 3 | 0 | 8.33 | 7.00 |
| t16 | with_skill_new | 3 | 0 | 8.33 | 6.00 |
| t17 | with_skill_new | 3 | 0 | 8.33 | 7.67 |
| t18 | with_skill_new | 3 | 0 | 8.67 | 7.33 |
| t19 | with_skill_new | 3 | 0 | 9.00 | 6.00 |
| t22 | with_skill_new | 3 | 0 | 8.33 | 8.00 |

## Remaining Weak Cases
- None in targeted set.
