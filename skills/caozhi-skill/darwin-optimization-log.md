# Darwin Optimization Log

## Round 0 Baseline

- 问题：初版若只按“槽值小妹”建模，会误把账号人格当个人小编。
- 处理：移除个人小编复刻，改成账号基线 + 文稿类型路由。
- 结果：non-impersonation 风险下降。

## Round 1

- 问题：只按全局互动排名会让早期亮眼稿被后期整体高互动压低。
- 处理：最终分数加入年度分位和年度爆点加成。
- 结果：满足用户“早期突然亮眼给更多加权”的要求。

## Round 2

- 问题：槽值短段容易被模型误学成机械碎段。
- 处理：在 `data/结构与段落指标.md`、`references/账号排版规范.md`、`SKILL.md` 自检中加入段落节奏约束。
- 结果：提高结构相似度，同时降低 AI 式碎段。

## Stop Rule

当前 dry_run 总分 87.0，达到 ready 门槛。继续优化的主要收益来自真实 full_test 盲评，而不是继续加规则。

## OpenClaw Smoke

- `openclaw skills info caozhi-skill --agent main`：Ready，model visible，command visible。
- `openclaw agent --local --agent main --session-key agent:main:caozhi-skill-smoke ...`：返回 `caozhi-skill 已加载`。
- 结论：Skill 不只是文件存在，OpenClaw 主 agent 已可作为命令调用。
