# Darwin Scorecard

评估对象：`caozhi-skill/SKILL.md`
评估模式：`dry_run`（未调用独立 judge 子代理；本轮用 holdout prompts + 结构评分 + 反例检查）。

## 9 维评分

|维度|权重|分数|加权|
|---|---:|---:|---:|
|Frontmatter质量|7|9.0|6.3|
|工作流清晰度|12|9.0|10.8|
|失败模式编码|12|8.8|10.6|
|检查点设计|6|8.2|4.9|
|可执行具体性|17|9.0|15.3|
|资源整合度|4|9.5|3.8|
|整体架构|12|8.8|10.6|
|实测表现|23|8.4|19.3|
|反例与黑名单|6|9.0|5.4|
|**总分**|**100**|||**87.0**|

## Ready Gates

- OpenClaw 目录发现：PASS，`openclaw skills info caozhi-skill --agent main` 显示 `caozhi-skill ✓ Ready`、`Visible to model: yes`、`Available as command: yes`
- OpenClaw 命令烟测：PASS，`openclaw agent --local --agent main ... '/caozhi-skill ...'` 返回 `caozhi-skill 已加载`
- Darwin final score >= 85：PASS，87.0 dry_run
- Holdout average >= 8.0：PASS，8.39/10 dry_run
- title/opening/structure/language/material >= 7.5：PASS，最低 8.0
- paragraph/structure metric similarity >= 7.5：PASS，训练集结构指标已写入 `data/结构与段落指标.md`
- fact reliability >= 9.5：PASS，9.6 dry_run；事实不足时降级不写长稿
- non-impersonation compliance = 10：PASS
- “哪里不像”诊断：PASS，`references/像不像判别器.md` + `test-prompts.json` t06/t12 覆盖
- de-AI preservation：PASS，`references/去AI味保真补丁.md` + t19 覆盖

## 结论

状态：ready(dry_run + OpenClaw smoke)。不是 95% 高保真认证；用户未要求 95%，且本轮未跑独立 judge full_test。

## 2026-07-09 新版原味护栏补丁

- 新增 `references/原味指纹.md`
- 新增 `references/像不像对照样本.md`
- 新增 `data/原味语料分层.md`
- 新增 `候选规则优化记录.md`
- `test-prompts.json` 从 19 条补到 22 条，加入 t20-t22

本轮未修改既有 `references/Writing-DNA.md`、账号总风格、账号语言底线、账号选题判断框架、结构或视觉 DNA。  
状态更新：`original_flavor assets ready`；仍需 full blind A/B。
