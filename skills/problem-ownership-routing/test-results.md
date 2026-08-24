# problem-ownership-routing — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试员只看到 15 个 Skill 的 name、description、SKILL.md 与 prompt，看不到 type、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同批兄弟 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | B-13 | `should_trigger` | `problem-ownership-routing` | `problem-ownership-routing` | PASS | 供应商问题涉及同事抱怨和合同权限缺口，需要决定接手、协助还是升级到有权限节点。 |
| should-trigger-02 | B-14 | `should_trigger` | `problem-ownership-routing` | `problem-ownership-routing` | PASS | 问题影响项目但本人没有退款权限，需要把责任和动作路由给有决策权的人。 |
| should-trigger-03 | B-15 | `should_trigger` | `problem-ownership-routing` | `problem-ownership-routing` | PASS | 公共问题无法由个人根除，仍需判断个人的有限改善、报告或倡议责任及停止阈值。 |
| should-not-trigger-01 | B-16 | `should_not_trigger` | `discussion-goal-routing` | `discussion-goal-routing` | PASS | 双方只想赢，已经缺少共同求真目标，需要决定停止普通讨论还是重构互动。 |
| should-not-trigger-02 | B-17 | `should_not_trigger` | `explore-exploit-mode-switch` | `explore-exploit-mode-switch` | PASS | 调试三小时没有新信息，正需要根据新信息率决定继续深挖还是切换探索路径。 |
| edge-01 | B-18 | `edge_case` | `边界语义` | `problem-ownership-routing` | PASS | 正确触发非负责人仍须先保护、留痕和升级的例外。 |

## 回炉记录

- 本 Skill 初轮 6/6，无需回炉。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 回炉复测（如适用）：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A06-R1.json`
