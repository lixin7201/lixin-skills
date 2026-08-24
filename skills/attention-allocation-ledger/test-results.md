# attention-allocation-ledger — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试员只看到 15 个 Skill 的 name、description、SKILL.md 与 prompt，看不到 type、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同批兄弟 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | A-07 | `should_trigger` | `attention-allocation-ledger` | `attention-allocation-ledger` | PASS | 整天忙于消息和会议却未完成重要事项，是典型的注意力收支与价值排序问题。 |
| should-trigger-02 | A-08 | `should_trigger` | `attention-allocation-ledger` | `attention-allocation-ledger` | PASS | 免费社区持续占用时间，而交换所得不清楚，需要还原这笔注意力交易的净收益。 |
| should-trigger-03 | A-09 | `should_trigger` | `attention-allocation-ledger` | `attention-allocation-ledger` | PASS | 消息热度已知，决策重点是是否值得投入一天回应及这笔注意力交换能得到什么。 |
| should-not-trigger-01 | A-10 | `should_not_trigger` | `novelty-information-distortion-audit` | `novelty-information-distortion-audit` | PASS | 爆火行业消息可能经过算法和营销筛选，正需审计信息生成链、代表性与独立证据。 |
| should-not-trigger-02 | A-11 | `should_not_trigger` | `production-distance-usefulness-audit` | `production-distance-usefulness-audit` | PASS | 大量功能无人使用，核心是审计功能产出到真实用户采用和结果反馈之间的距离。 |
| edge-01 | A-12 | `edge_case` | `边界语义` | `null` | PASS | 正确识别紧急照护强制例外，未用注意力账本拒绝响应。 |

## 回炉记录

- 本 Skill 初轮 6/6，无需回炉。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 回炉复测（如适用）：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A06-R1.json`
