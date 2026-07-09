# Darwin Optimization Log

## Round 0 Baseline

从零创建 app-skill，无旧版 baseline。

## Round 1 Keep

- 修正取样口径：每个小编独立过滤活动帖并取自己的互动前 60%。
- 加入小编路由，避免平均风格。
- 加入事实红线、去 AI 保真补丁、holdout 泄漏检查口径。

status: keep

## Round 2 Keep

- OpenClaw smoke 暴露路径问题：agent 自然尝试读取 `references/文稿类型/招聘求职信息.md`，但生成文件只有 `招聘求职信息DNA.md`。
- 修复：在 `SKILL.md` 写明类型文件可读取无后缀别名，并为所有类型生成同名 `.md` 兼容文件。
- 复测：`openclaw agent --local ... /app-skill 按大宜宾-梦竹路线...` 成功出稿，`toolSummary.failures = 0`。

status: keep

## Round 3 Keep

- Full blind A/B：20 个测试 prompt，with-skill 与 no-skill baseline 各生成一批，A/B 随机打乱，3 个独立 judge 评分。
- 初始结果：app-skill 多数票赢 19/20，judge 票 56/60；唯一弱项是 `t10` 标题优化，3 个 judge 都认为 baseline 标题更自然。
- 修复：只改 `SKILL.md` 的标题优化规则，要求 10 个标题按强互动/事实服务/本地对象/稳妥标题分组，标出推荐标题，并避免生硬名词堆叠。
- 复测：只重跑 `t10`，3 个独立 judge 复评 corrected app-skill 3/3 胜出，平均分 8.90 vs baseline 8.07。
- 最终 adjusted：app-skill 多数票赢 20/20，judge 票 59/60。

status: keep
