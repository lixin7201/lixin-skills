# Darwin Scorecard

评估方式：Darwin-style static review + OpenClaw native smoke + 8-case holdout generation + blind A/B with 3 independent OpenClaw judge sessions + targeted reruns + de-AI preservation smoke.

## 总分

- final_score: 90.6 / 100
- eval_mode: full_test_8_holdout_3_judges_targeted_rerun
- holdout_average: 8.73 / 10
- fact_reliability: 9.7 / 10
- non_impersonation: 10 / 10
- route_correctness: 9.2 / 10
- original_flavor: 8.8 / 10
- de_ai_preservation: 8.8 / 10
- blind_ab_majority_wins: 8 / 8
- blind_ab_judge_votes: 23 / 24

## 通过项

- OpenClaw `--agent main` 能发现并原生调用 `dangjian-skill`。
- Holdout 原文只保存在 `holdout/originals/`，DNA/test prompts 未泄露 holdout 标题或正文。
- 每个一级文件夹单独生成活动类型 DNA，新增类型有接入规范。
- `去AI味保真补丁.md` 已纳入 `SKILL.md` 终稿流程，并完成 smoke。
- 盲测发现的两个弱项已用最小规则修正并复测。

## 未认证项

- 不声明 95% 高保真：`发言稿` 与 `获奖宣传` 样本不足 10 篇，且图片本体未逐图分析。
- 这不是人工编辑部盲审，是 3 个独立 OpenClaw 模型 judge 的 blind A/B。
