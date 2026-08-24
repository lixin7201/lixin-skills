# bounded-rapid-failure-protocol 压力测试结果

> 评测模式：主流程 fallback；使用不含 type/expected 的 blind-inputs.json。当前环境无独立 sub-agent，可信度低于独立盲测。

- 通过：6/6
- 通过率：100%
- 诱饵容错：0（全部 should_not_trigger 必须通过）

| Case | 类型 | 期望选择 | 实际选择 | 结果 | 判断理由 |
|---|---|---|---|---|---|
| should-trigger-01 | should_trigger | bounded-rapid-failure-protocol | bounded-rapid-failure-protocol | PASS | 小流量试验同时存在留存损失风险，需要试验边界和回退。 |
| should-trigger-02 | should_trigger | bounded-rapid-failure-protocol | bounded-rapid-failure-protocol | PASS | 用户明确询问失败情况下的成功标准。 |
| should-trigger-03 | should_trigger | bounded-rapid-failure-protocol | bounded-rapid-failure-protocol | PASS | 安全失败试验与迁移风险直接匹配。 |
| should-not-trigger-01 | should_not_trigger | surge-mode-governor | surge-mode-governor | PASS | 问题是组织是否进入战时状态，不是单个试验。 |
| should-not-trigger-02 | should_not_trigger | none | none | PASS | 无备份全量迁移突破 Skill 边界，不能用快速失败背书。 |
| edge-01 | edge_case | none | none | PASS | 未经批准的患者试验涉及不可逆健康、伦理和监管。 |

## 结论

触发、拒绝和兄弟 Skill 混淆测试全部通过。
