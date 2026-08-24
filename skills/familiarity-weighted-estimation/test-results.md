# familiarity-weighted-estimation — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试者只看到 21 个 Skill 的 name、description、SKILL.md 与 prompt，看不到类型、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同书兄弟或同作者相邻 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | A-07 | `should_trigger` | `familiarity-weighted-estimation` | `familiarity-weighted-estimation` | PASS | 团队首次做数据库迁移且被要求给准确单点日期，是陌生任务伪精确估时的典型场景。 |
| should-trigger-02 | A-08 | `should_trigger` | `familiarity-weighted-estimation` | `familiarity-weighted-estimation` | PASS | 现有估算只含开发执行，明确遗漏新框架学习、联调和返工。 |
| should-trigger-03 | A-09 | `should_trigger` | `familiarity-weighted-estimation` | `familiarity-weighted-estimation` | PASS | 任务部分熟悉、部分陌生，正需按熟悉度差异建立区间与缓冲以减少延期。 |
| should-not-trigger-01 | A-10 | `should_not_trigger` | `reality-constraint-premise-audit` | `reality-constraint-premise-audit` | PASS | 问题直接要求核验资源交换、完美度和改变速度三类现实前提。 |
| should-not-trigger-02 | A-11 | `should_not_trigger` | `planning-and-task-breakdown` | `planning-and-task-breakdown` | PASS | 需求明确是把大项目拆成依赖清晰、可实施的任务清单。 |
| edge-01 | A-12 | `edge_case` | `边界行为` | `null` | PASS | 正确优先隔离安全事件，常规估时只用于后续恢复阶段。 |

## 回炉记录

- 本 Skill 初轮行为判定 6/6，无需修改 Skill 或测试。
- 六个边界题一度因旧判卷器要求“必须选中源 Skill”显示为路由失败；人工逐项复核确认其选择 `null` 时准确执行了停止、降级或升级条件。判卷器改为分别检查路由与显式边界行为，未修改任何 prompt、答案或盲测输出。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 逐条机器判卷：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/BLIND_GRADE.json`
