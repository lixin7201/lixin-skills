# reality-constraint-premise-audit — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试者只看到 21 个 Skill 的 name、description、SKILL.md 与 prompt，看不到类型、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同书兄弟或同作者相邻 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | A-01 | `should_trigger` | `reality-constraint-premise-audit` | `reality-constraint-premise-audit` | PASS | 计划以三个月从零达到资深水平为重大承诺，核心疑点正是速成和状态瞬变前提。 |
| should-trigger-02 | A-02 | `should_trigger` | `reality-constraint-premise-audit` | `reality-constraint-premise-audit` | PASS | 一次上线即完美且不增加预算，同时包含完美与零交换两类典型不现实前提。 |
| should-trigger-03 | A-03 | `should_trigger` | `reality-constraint-premise-audit` | `reality-constraint-premise-audit` | PASS | 计划把关键信息缺口假设为未来自然消失，正需审计未知约束。 |
| should-not-trigger-01 | A-04 | `should_not_trigger` | `compound-direction-canvas` | `compound-direction-canvas` | PASS | 问题是在判断一个新长期方向是否有真实需求并能形成复利，符合长期方向画布的核心维度。 |
| should-not-trigger-02 | A-05 | `should_not_trigger` | `familiarity-weighted-estimation` | `familiarity-weighted-estimation` | PASS | 陌生技术项目却要给出周数承诺，需先按熟悉度计入学习、试错和返工。 |
| edge-01 | A-06 | `edge_case` | `边界行为` | `null` | PASS | 正确将可撤销半日原型降为轻量前提检查，没有把现实审计变成拖延。 |

## 回炉记录

- 本 Skill 初轮行为判定 6/6，无需修改 Skill 或测试。
- 六个边界题一度因旧判卷器要求“必须选中源 Skill”显示为路由失败；人工逐项复核确认其选择 `null` 时准确执行了停止、降级或升级条件。判卷器改为分别检查路由与显式边界行为，未修改任何 prompt、答案或盲测输出。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 逐条机器判卷：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/BLIND_GRADE.json`
