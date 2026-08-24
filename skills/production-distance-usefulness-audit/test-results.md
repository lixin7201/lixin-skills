# production-distance-usefulness-audit — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试员只看到 15 个 Skill 的 name、description、SKILL.md 与 prompt，看不到 type、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同批兄弟 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | A-01 | `should_trigger` | `production-distance-usefulness-audit` | `production-distance-usefulness-audit` | PASS | 问题要判断热门证书是否改善真实工作产出，正适合审计学习投入与可交付结果、受益者之间的距离。 |
| should-trigger-02 | A-02 | `should_trigger` | `production-distance-usefulness-audit` | `production-distance-usefulness-audit` | PASS | 团队忙碌却远离客户，核心是检查内部活动到用户反馈和关键产出的生产距离。 |
| should-trigger-03 | A-03 | `should_trigger` | `production-distance-usefulness-audit` | `production-distance-usefulness-audit` | PASS | 用户想把自我喜欢与对他人有用分开，并寻找真实需求和受益证据。 |
| should-not-trigger-01 | A-04 | `should_not_trigger` | `null` | `null` | PASS | 问题是把已验证的一对一经验产品化和规模化；目录中的生产距离审计明确把这类任务区分给其他方法。 |
| should-not-trigger-02 | A-05 | `should_not_trigger` | `attention-allocation-ledger` | `attention-allocation-ledger` | PASS | 群消息造成被动打断，用户需要核算各项注意力支出、收益和优先级。 |
| edge-01 | A-06 | `edge_case` | `边界语义` | `production-distance-usefulness-audit` | PASS | 初测误把非价格证据理解为不适用；回炉重写 A2/B 后，R1 独立盲测正确调用并先定义非价格受益证据。 |

## 回炉记录

- 初测 `A-06` 选择 `null`，初轮为 5/6；失败原因是 description 与 B 段把“不能用短期价格否定基础研究”写得像整个 Skill 不适用。
- 未修改测试预期。回到阶段 2，重写 description、A2 触发和 B 边界；E 段原有“覆盖、风险下降、能力增量”步骤保留。
- 新的独立盲测员在 `A-06-R1` 正确选择 `production-distance-usefulness-audit`，并先定义非价格受益证据；最终 6/6。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 回炉复测（如适用）：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A06-R1.json`
