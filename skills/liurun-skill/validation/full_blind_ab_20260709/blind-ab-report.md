# Full Blind A/B Report 20260709 - liurun-skill

## Setup
- Test cases: 22/22 from `test-prompts.json`.
- Generations: `with_skill` uses `/liurun-skill` in 2 batches; baseline explicitly forbidden from reading local skill/DNA.
- Judges: 3 independent OpenClaw local judge runs.
- Blind method: A/B labels randomized with seed `2026070901`; key stored separately in `blind_key.json`.
- Scope: prompt-set blind A/B, not human editorial review or external fact check.

## Result
| Metric | with_skill | baseline |
|---|---:|---:|
| Majority wins | 14 / 22 | 8 / 22 |
| Judge votes | 41 / 66 | 25 / 66 |
| Average overall score | 8.54 | 8.40 |

## Per-Test Votes
| Test | Majority | Skill votes | Baseline votes | Skill avg | Baseline avg |
|---|---|---:|---:|---:|---:|
| draft-001 | baseline | 0 | 3 | 8.00 | 8.67 |
| rewrite-001 | baseline | 1 | 2 | 8.47 | 8.47 |
| business-001 | with_skill | 2 | 1 | 8.63 | 8.33 |
| boundary-001 | with_skill | 3 | 0 | 8.87 | 8.30 |
| org-001 | with_skill | 3 | 0 | 8.77 | 8.17 |
| t06 | with_skill | 3 | 0 | 8.70 | 8.07 |
| t07 | with_skill | 3 | 0 | 8.63 | 8.07 |
| t08 | baseline | 0 | 3 | 8.10 | 8.70 |
| t09 | with_skill | 3 | 0 | 8.80 | 8.27 |
| t10 | with_skill | 3 | 0 | 8.87 | 8.33 |
| t11 | with_skill | 3 | 0 | 8.83 | 8.27 |
| t12 | baseline | 0 | 3 | 8.17 | 8.80 |
| t13 | with_skill | 3 | 0 | 8.87 | 8.30 |
| t14 | with_skill | 2 | 1 | 8.47 | 8.53 |
| t15 | with_skill | 3 | 0 | 8.83 | 8.23 |
| t16 | baseline | 1 | 2 | 7.77 | 8.13 |
| t17 | with_skill | 3 | 0 | 8.83 | 8.20 |
| t18 | with_skill | 2 | 1 | 8.67 | 8.37 |
| t19 | baseline | 0 | 3 | 8.20 | 8.73 |
| t20 | baseline | 0 | 3 | 8.23 | 8.77 |
| t21 | baseline | 0 | 3 | 8.30 | 8.90 |
| t22 | with_skill | 3 | 0 | 8.83 | 8.23 |

## Weak / Narrow Cases
- `draft-001`: majority=baseline, votes 0-3, avg 8.0 vs 8.67; judge_1_style_editor:B 链条定义更准，少冒充; judge_2_fact_process:B B链条和指标更完整; judge_3_skeptical_reader:B B责任链和指标更完整
- `rewrite-001`: majority=baseline, votes 1-2, avg 8.47 vs 8.47; judge_1_style_editor:A 概念更稳，成本追问更密; judge_2_fact_process:A A成本后台辨析更锋利; judge_3_skeptical_reader:B B交易账和案例更稳
- `t08`: majority=baseline, votes 0-3, avg 8.1 vs 8.7; judge_1_style_editor:B 分工边界更细更稳; judge_2_fact_process:B B判断标准更可复用; judge_3_skeptical_reader:B B压缩后框架更完整
- `t12`: majority=baseline, votes 0-3, avg 8.17 vs 8.8; judge_1_style_editor:B 账、风险、动作更全; judge_2_fact_process:B B按账和动作诊断更全; judge_3_skeptical_reader:B B按账和动作更实
- `t14`: majority=with_skill, votes 2-1, avg 8.47 vs 8.53; judge_1_style_editor:A 差距拆解更有命名; judge_2_fact_process:A A差距拆得更有层次; judge_3_skeptical_reader:B B拆账拆责任更准
- `t16`: majority=baseline, votes 1-2, avg 7.77 vs 8.13; judge_1_style_editor:B 判别更直接，维度更实; judge_2_fact_process:A A不预设胜方更合题; judge_3_skeptical_reader:A A作为评委更合规
- `t19`: majority=baseline, votes 0-3, avg 8.2 vs 8.73; judge_1_style_editor:A 既去味又保留机制; judge_2_fact_process:A A给出成稿且保机制; judge_3_skeptical_reader:A A去味后仍有成稿
- `t20`: majority=baseline, votes 0-3, avg 8.23 vs 8.77; judge_1_style_editor:B 分类更稳，警报更准; judge_2_fact_process:B B分类边界更稳; judge_3_skeptical_reader:B B分类标准更稳
- `t21`: majority=baseline, votes 0-3, avg 8.3 vs 8.9; judge_1_style_editor:A 主角度命名更有力; judge_2_fact_process:A A成本转移概念更强; judge_3_skeptical_reader:A A主角度命名更强

## Gate Read
- Blind A/B >=80% majority gate: FAIL (14/22).
- Fact/non-impersonation issues: no external fact check in this automated blind run; judges penalized visible fabrication/impersonation.
