# evergreen-content-fertility-filter — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试员只看到 15 个 Skill 的 name、description、SKILL.md 与 prompt，看不到 type、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同批兄弟 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | C-25 | `should_trigger` | `evergreen-content-fertility-filter` | `evergreen-content-fertility-filter` | PASS | 爆火工具的长教程可能很快过时，需要评估读者价值并拆分耐久原理层与易变版本层。 |
| should-trigger-02 | C-26 | `should_trigger` | `evergreen-content-fertility-filter` | `evergreen-content-fertility-filter` | PASS | 大量阅读没有产生作品或技能，正需要按输入繁殖力降低无产出的内容预算。 |
| should-trigger-03 | C-27 | `should_trigger` | `evergreen-content-fertility-filter` | `evergreen-content-fertility-filter` | PASS | 书稿范围膨胀且要筛必备和长期有用内容，符合必备性与耐久层审计。 |
| should-not-trigger-01 | C-28 | `should_not_trigger` | `decentralized-teacher-source-ladder` | `decentralized-teacher-source-ladder` | PASS | 官方文档和社区答案冲突时，核心任务是比较来源等级、版本适用性和可重复证据。 |
| should-not-trigger-02 | C-29 | `should_not_trigger` | `premature-reference-dual-speed-reading` | `premature-reference-dual-speed-reading` | PASS | 大量过早引用并要求设计粗读与精读顺序，是双速阅读协议的直接适用场景。 |
| edge-01 | C-30 | `edge_case` | `边界语义` | `null` | PASS | 正确允许时效性应急通知，不因不耐久否定即时职责价值。 |

## 回炉记录

- 本 Skill 初轮 6/6，无需回炉。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 回炉复测（如适用）：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A06-R1.json`
