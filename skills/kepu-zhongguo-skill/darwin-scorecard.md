# Darwin Scorecard

评估方式：每作者/账号线互动加权前 70% 语料蒸馏 + 12 篇 holdout 冻结 + blind A/B packet + Darwin 候选规则优化 + OpenClaw discoverability 检查 + 2026-07-21 二次证据蒸馏审计。

## 总分

- final_score: 91.0 / 100
- eval_mode: evidence_enhanced_full_real_holdout_r1
- status: expanded_blind_ab_passed_source_gaps_remain
- blind_ab_initial: 2 / 2 judge votes for with-skill on one sample packet
- real_holdout_r1: 12 / 12 completed
- real_holdout_r1_with_skill_avg: 7.27 / 10
- real_holdout_r1_baseline_avg: 4.10 / 10
- holdout_average: 7.27 / 10
- r2_focused_rule_regression: 5 cases, 8.68 / 10
- r2_full_fact_card_readiness: 12 / 12, 9.07 / 10, leak_pass=true
- r2_full_outputs: 12 / 12, 8.28 / 10, leak_pass=true, below_8=none
- expanded_blind_ab_r2: 18/18 skill votes, judges=3, cases=6
- publish_gate: 12/12 topics covered, open_gaps=12, release_gate=not_passed_until_sources_resolved
- fact_reliability: 9.7 / 10
- non_impersonation: 10 / 10
- route_correctness: 9.0 / 10
- de_ai_preservation: 9.2 / 10
- author_dna_evidence_density: 23/23
- type_dna_evidence_density: 9/9
- author_core_max_similarity_after_second_pass: 0.6832
- original_flavor_gate: high_fidelity_candidate_not_source_certified
- high_fidelity_95: not_requested_not_certified

## 通过项

- 每个作者/账号线独立取互动前 70%，不是全账号混排。
- 早期互动口径异常已做 2020-2022 加权。
- 图片/短稿和伪作者字段已排除个人 DNA。
- 作者 DNA 已补标题形状、开头入口、结尾动作、材料来源和代表训练题目。
- 类型 DNA 已补标题形状、开头入口、结尾动作、材料来源和代表训练题目。
- 已完成 h01-h12 的真实 holdout 生成对比，with-skill 平均 7.27，baseline 平均 4.10，未发现 30 字连续片段泄漏。
- 已新增 `references/R1-Darwin修补规则.md`，并接入 Skill 必读链路。
- R2 聚焦回归覆盖 h02/h04/h07/h09/h11，规则合规均分 8.68 / 10。
- R2 完整复评输入层已准备 12 张中性事实卡，readiness 均分 9.07 / 10，30 字连续片段泄漏检查通过。
- R2 完整稿已生成并评分：12/12，平均 8.28 / 10，泄漏检查通过。
- 扩大 blind A/B 覆盖 6 个 case、3 位评审，Skill 获得 18/18 票。
- 发布级门禁已定义：`references/发布级门禁.md` 已接入 Skill 必读链路，`validation/publish-gate/source-gap-register.csv` 覆盖 12/12 个 holdout 题材。
- OpenClaw discoverability 通过：`kepu-zhongguo-skill ✓ Ready`，modelVisible/commandVisible 均为 true。

## 未认证项

- R1 只给标题方向，with-skill 平均分未达 8.0；R2 已通过候选线，两个口径必须分开阅读。
- R2 聚焦回归只是中间层证据；最终候选判断以 R2 完整出稿和 expanded blind A/B 为准。
- R2 完整出稿平均分已过 8.0，扩大 blind A/B 已通过；但发布级来源和人工终审未完成。
- 低于 8.0 的 R2 样本：none。
- 扩大 blind A/B 已通过，但评审指出发布前待核实尾注、外部来源缺口和少量短段过密问题。
- 发布级来源门禁仍未通过：open_gaps=12，未补齐前默认只能交付 B 档编辑候选稿。
- 部分作者线仍需要人工读样本，补“为什么这么写”的认知层差异。
- 科普中国大量文章由外部专家/科普作者供稿，作者线不能等同后台小编本人味。

## R1 暴露弱点

- h01 材料密度不足，缺少人群占比、营养分项等扩展层。
- h02 直播预告属性不足，写成偏评论解释稿。
- h03 清单分项不足，缺少具体发酵食品大盘点密度。
- h04/h07 食品营养解释稿缺原文营养表、食材对比和热搜/数据层。
- h09/h10 心理稿有机制但生活场景铺陈不足。
- h11 科技突破稿过泛，缺团队、论文、反应路径和产业化阶段。
- with-skill 段落节奏仍偏长，短段密度低于部分原文。

## 结论

当前版本比第一版扎实，且 12 个真实 holdout 全部优于 baseline；R2 完整稿平均分已过 8.0，扩大 blind A/B 也已通过。它可以标记为“高保真候选版”。但还不能宣称“原汁原味/本人味/发布级完成”，因为仍需外部来源补齐和人工终审。
