# decentralized-teacher-source-ladder — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试员只看到 15 个 Skill 的 name、description、SKILL.md 与 prompt，看不到 type、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同批兄弟 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | C-19 | `should_trigger` | `decentralized-teacher-source-ladder` | `decentralized-teacher-source-ladder` | PASS | 没有系统课程时选择官方文档、开源实现或专家，属于多来源角色分工与升级问题。 |
| should-trigger-02 | C-20 | `should_trigger` | `decentralized-teacher-source-ladder` | `decentralized-teacher-source-ladder` | PASS | 官方文档、博客和大V答案冲突，需要按版本、一手证据和可重复实验裁决来源。 |
| should-trigger-03 | C-21 | `should_trigger` | `decentralized-teacher-source-ladder` | `decentralized-teacher-source-ladder` | PASS | 多轮检索仍无法复现错误，适合按来源升级梯准备最小可复现的专家求助。 |
| should-not-trigger-01 | C-22 | `should_not_trigger` | `premature-reference-dual-speed-reading` | `premature-reference-dual-speed-reading` | PASS | 同一规范的前后文循环依赖正需要在脱盲粗读和关键定义精读之间分工。 |
| should-not-trigger-02 | C-23 | `should_not_trigger` | `evergreen-content-fertility-filter` | `evergreen-content-fertility-filter` | PASS | 判断教程十年后的读写价值，是长效内容耐久性与繁殖力筛选的直接场景。 |
| edge-01 | C-24 | `edge_case` | `边界语义` | `null` | PASS | 正确把危及生命问题升级到合格专业责任节点，不由论坛自行裁决。 |

## 回炉记录

- 本 Skill 初轮 6/6，无需回炉。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 回炉复测（如适用）：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A06-R1.json`
