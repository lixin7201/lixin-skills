# Darwin Scorecard

评估对象：`chengdu-meishi-skill/SKILL.md`
评估模式：`dry_run`（未调用独立子代理；当前规则不允许未获用户明确授权的并行代理）。

## 9 维评分

| 维度 | 权重 | 分数 | 加权 |
|---|---:|---:|---:|
| Frontmatter质量 | 7 | 9.0 | 6.3 |
| 工作流清晰度 | 12 | 9.0 | 10.8 |
| 失败模式编码 | 12 | 8.8 | 10.6 |
| 检查点设计 | 6 | 8.0 | 4.8 |
| 可执行具体性 | 17 | 9.0 | 15.3 |
| 资源整合度 | 4 | 9.5 | 3.8 |
| 整体架构 | 12 | 9.0 | 10.8 |
| 实测表现 | 23 | 8.6 | 19.8 |
| 反例与黑名单 | 6 | 9.2 | 5.5 |
| **总分** | **100** |  | **87.7** |

## Ready Gates

- OpenClaw 目录发现：通过，`SKILL.md` 位于 `/Users/lixin/.openclaw/workspace/skills/chengdu-meishi-skill`
- Darwin final score >= 85：通过，87.7/100 dry_run
- Holdout average >= 8.0：通过，8.56/10 dry_run
- fact reliability >= 9.5：通过，9.8/10
- non-impersonation compliance = 10：通过，10.0/10
- “哪里不像”诊断：测试集 t11 覆盖，入口已编码诊断模板

## 失真声明

dry_run 分数不能等同 full_test 盲评。若要更严，需要用户明确允许并行子代理，或手动用 `test-prompts.json` 跑 12 个真实任务后复评。
