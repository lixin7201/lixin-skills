# Darwin Scorecard

评估方式：每署名线互动前 70% 语料蒸馏 + holdout 冻结 + OpenClaw 可调用检查 + full blind A/B + Darwin 迭代回归。

## 总分

- final_score: 91.8 / 100
- eval_mode: real_full_blind_ab_plus_targeted_darwin_regression
- full_blind_ab: 26 / 30 judge votes for with-skill
- majority_holdout: 9 / 10 cases for with-skill
- fact_reliability: 9.7 / 10
- non_impersonation: 10 / 10
- route_correctness: 9.4 / 10
- de_ai_preservation: 9.0 / 10
- original_flavor_gate: pass
- high_fidelity_95: not_certified

## 通过项

- 每个署名线独立取互动前 70%，不是全账号混排。
- `半月谈`、`半月谈记者` 已标注为聚合路线，不冒充具体真人。
- holdout 原文保存在 `holdout/originals/`，训练和 DNA 不复制 holdout 正文。
- `SKILL.md` 可直接调用，`openclaw skills info banyuetan-skill --agent main` 返回 `banyuetan-skill ✓ Ready`。
- 13 个文稿类型 DNA、5 条署名/聚合路线 DNA、原味指纹、像不像判别器、去 AI 保真补丁均已生成。
- full blind A/B 真实模型评审通过：`validation/final_full_blind_ab_20260711_r4/ab_summary.tsv`。

## 弱项

- h01 品读散文在 full blind A/B 中输给 baseline，主要原因是人物材料不足时 baseline 的公共议题转接更自然。
- 已追加 h01 边界补丁：弱素材不冒充当事人第一人称，正文不泄露 Skill/DNA/路由信息，事实缺口集中放在事实边界。
- 图片节奏只能从 Markdown 图片数量推断，没有逐张视觉审稿。
- 个人小编 DNA 只有少数署名线样本足够；多数作者只能放账号/类型层。
