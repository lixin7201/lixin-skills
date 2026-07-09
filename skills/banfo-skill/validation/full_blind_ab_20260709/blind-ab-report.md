# Full Blind A/B Report 20260709 - banfo-skill

## Setup
- Test cases: 22/22 from `test-prompts.json`.
- Generations: `with_skill` uses `/banfo-skill` in 2 batches; baseline explicitly forbidden from reading local skill/DNA.
- Judges: 3 independent OpenClaw local judge runs.
- Blind method: A/B labels randomized with seed `2026070902`; key stored separately in `blind_key.json`.
- Scope: prompt-set blind A/B, not human editorial review or external fact check.

## Result
| Metric | with_skill | baseline |
|---|---:|---:|
| Majority wins | 13 / 22 | 9 / 22 |
| Judge votes | 40 / 66 | 26 / 66 |
| Average overall score | 8.59 | 8.33 |

## Per-Test Votes
| Test | Majority | Skill votes | Baseline votes | Skill avg | Baseline avg |
|---|---|---:|---:|---:|---:|
| t01 | with_skill | 3 | 0 | 9.00 | 8.00 |
| t02 | with_skill | 3 | 0 | 9.00 | 8.00 |
| t03 | with_skill | 3 | 0 | 9.00 | 8.00 |
| t04 | baseline | 0 | 3 | 8.00 | 9.00 |
| t05 | with_skill | 3 | 0 | 9.00 | 8.00 |
| t06 | with_skill | 3 | 0 | 9.00 | 8.00 |
| t07 | with_skill | 3 | 0 | 9.00 | 7.00 |
| t08 | with_skill | 2 | 1 | 8.33 | 7.67 |
| t09 | baseline | 1 | 2 | 8.33 | 8.67 |
| t10 | with_skill | 2 | 1 | 8.67 | 8.67 |
| t11 | with_skill | 3 | 0 | 9.00 | 8.00 |
| t12 | baseline | 1 | 2 | 8.33 | 8.67 |
| t13 | with_skill | 2 | 1 | 8.67 | 8.33 |
| t14 | baseline | 1 | 2 | 8.33 | 8.67 |
| t15 | with_skill | 3 | 0 | 9.00 | 8.00 |
| t16 | baseline | 0 | 3 | 8.00 | 9.00 |
| t17 | baseline | 0 | 3 | 8.00 | 9.00 |
| t18 | baseline | 0 | 3 | 8.00 | 9.00 |
| t19 | baseline | 0 | 3 | 8.00 | 9.00 |
| t20 | with_skill | 3 | 0 | 9.00 | 8.00 |
| t21 | with_skill | 3 | 0 | 9.00 | 8.00 |
| t22 | baseline | 1 | 2 | 8.33 | 8.67 |

## Weak / Narrow Cases
- `t04`: majority=baseline, votes 0-3, avg 8.0 vs 9.0; judge_1_style_editor:A 入题快，老车主关系更准; judge_2_fact_process:A A入题快且边界稳; judge_3_skeptical_reader:A 前三段入题更狠更稳
- `t09`: majority=baseline, votes 1-2, avg 8.33 vs 8.67; judge_1_style_editor:B 拒写干净，风险提示更自然; judge_2_fact_process:B B补问更完整更稳; judge_3_skeptical_reader:A 补充问题更完整稳健
- `t10`: majority=with_skill, votes 2-1, avg 8.67 vs 8.67; judge_1_style_editor:A 医疗事实门更分层具体; judge_2_fact_process:B B来源层级更清楚; judge_3_skeptical_reader:B 来源层级和医疗边界更硬
- `t12`: majority=baseline, votes 1-2, avg 8.33 vs 8.67; judge_1_style_editor:B 改稿更短促，机制反转更好; judge_2_fact_process:A A诊断改稿边界更全; judge_3_skeptical_reader:B 改稿更自然，少生产痕迹
- `t14`: majority=baseline, votes 1-2, avg 8.33 vs 8.67; judge_1_style_editor:A 对比锋利，公告翻译有味; judge_2_fact_process:B B差异说明更可复用; judge_3_skeptical_reader:A 对比清楚，参考版更有劲
- `t16`: majority=baseline, votes 0-3, avg 8.0 vs 9.0; judge_1_style_editor:A 标题判断有物件和机制; judge_2_fact_process:A A用例具体判断更准; judge_3_skeptical_reader:A 有实例对照，标题DNA更准
- `t17`: majority=baseline, votes 0-3, avg 8.0 vs 9.0; judge_1_style_editor:B 跨题迁移更像现场拆解; judge_2_fact_process:B B跨题材迁移更自然; judge_3_skeptical_reader:B 跨题材迁移更自然鲜活
- `t18`: majority=baseline, votes 0-3, avg 8.0 vs 9.0; judge_1_style_editor:B 三种开头结构差异更稳; judge_2_fact_process:B B结构变化更明显; judge_3_skeptical_reader:B 结构变化更明显，不模板
- `t19`: majority=baseline, votes 0-3, avg 8.0 vs 9.0; judge_1_style_editor:B 去AI味更自然，保机制; judge_2_fact_process:B B去味后更像成稿; judge_3_skeptical_reader:B 去AI味更彻底，保留反转
- `t22`: majority=baseline, votes 1-2, avg 8.33 vs 8.67; judge_1_style_editor:B 恢复原味但不补事实; judge_2_fact_process:A A恢复原味且边界稳; judge_3_skeptical_reader:A 恢复原味更足，边界也稳

## Gate Read
- Blind A/B >=80% majority gate: FAIL (13/22).
- Fact/non-impersonation issues: no external fact check in this automated blind run; judges penalized visible fabrication/impersonation.
