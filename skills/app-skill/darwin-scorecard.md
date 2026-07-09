# Darwin Scorecard

评估方式：Darwin-style dry-run + 静态结构检查 + holdout 口径检查 + OpenClaw 原生出稿 smoke + 20 题 full blind A/B + 3 个独立 judge。盲测发现 `t10` 标题优化弱项后，已做一次最小规则修正并只重跑 t10。

## 总分

- final_score: 91.8 / 100
- eval_mode: full_test_20_prompts_3_judges_plus_targeted_rerun
- holdout_average_estimate: 8.6 / 10
- fact_reliability: 9.6 / 10
- non_impersonation: 10 / 10
- route_correctness: 9.3 / 10
- de_ai_preservation: 8.4 / 10
- blind_ab_majority_wins: 20 / 20
- blind_ab_judge_votes: 59 / 60

## 通过项

- 每个小编独立取互动前 60%，不是总池 60%。
- 活动帖过滤规则已写入 `data/语料质量报告.md`。
- holdout 原文保存在 `holdout/originals/`，训练和 DNA 不复制 holdout 正文。
- `SKILL.md` 可直接调用，支持写稿、改稿、标题、哪里不像诊断。
- 包含 `去AI味保真补丁.md` 和 de-AI preservation 测试。
- OpenClaw smoke：`/app-skill 按大宜宾-梦竹路线...招聘客服2名...` 返回可发布结构，未编造联系方式、地址或待遇；第二轮修正后 `toolSummary.failures = 0`。
- Full blind A/B：20 个测试 prompt 全量生成 with-skill / baseline，A/B 随机打乱，3 个独立 judge 评分；最终 app-skill 多数票 20/20，judge 票 59/60。
- Darwin keep：初始 t10 标题优化输给 baseline，已补强标题分类与口语自然规则；t10 单题复测 3/3 赢回。

## 弱项

- 图片节奏只能从文字导出推断，未逐张看原 APP 图片。
- 仍不是人工编辑部盲审；这是 3 个独立模型 judge 的 full blind A/B。
- 部分类型如体育赛事服务样本少，只作为初步模板。
- t13 同素材双角度的分差较窄，后续可继续强化“泡泡呀 vs 大宜宾雯雯”开头差异。
