# audience-distance-conclusion-ordering — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试员只看到 15 个 Skill 的 name、description、SKILL.md 与 prompt，看不到 type、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同批兄弟 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | B-07 | `should_trigger` | `audience-distance-conclusion-ordering` | `audience-distance-conclusion-ordering` | PASS | 面对强烈反对者讲高风险方案，需要按观念距离决定共同事实、证据桥与结论的顺序。 |
| should-trigger-02 | B-08 | `should_trigger` | `audience-distance-conclusion-ordering` | `audience-distance-conclusion-ordering` | PASS | 听众已熟悉背景，问题正是是否应减少铺垫并采用结论先行。 |
| should-trigger-03 | B-09 | `should_trigger` | `audience-distance-conclusion-ordering` | `audience-distance-conclusion-ordering` | PASS | 专家与新手构成观念和知识距离不同的混合受众，需要分层安排结论与证据。 |
| should-not-trigger-01 | B-10 | `should_not_trigger` | `speaker-claim-consistency-audit` | `speaker-claim-consistency-audit` | PASS | 核心承诺既不被讲者相信又缺乏证据，首先是能否诚实表达，而不是表达顺序问题。 |
| should-not-trigger-02 | B-11 | `should_not_trigger` | `misunderstanding-map-preflight` | `misunderstanding-map-preflight` | PASS | 退款规则尚在发布前，目标是收集用户的错误复述并据此修订表达。 |
| edge-01 | B-12 | `edge_case` | `边界语义` | `audience-distance-conclusion-ordering` | PASS | 正确把致命安全风险列为不可延迟披露。 |

## 回炉记录

- 本 Skill 初轮 6/6，无需回炉。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 回炉复测（如适用）：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A06-R1.json`
