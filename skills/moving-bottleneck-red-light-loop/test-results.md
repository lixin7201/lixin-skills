# moving-bottleneck-red-light-loop 压力测试结果

> 评测模式：主流程 fallback；使用不含 type/expected 的 blind-inputs.json。当前环境无独立 sub-agent，可信度低于独立盲测。

- 通过：6/6
- 通过率：100%
- 诱饵容错：0（全部 should_not_trigger 必须通过）

| Case | 类型 | 期望选择 | 实际选择 | 结果 | 判断理由 |
|---|---|---|---|---|---|
| should-trigger-01 | should_trigger | moving-bottleneck-red-light-loop | moving-bottleneck-red-light-loop | PASS | 多团队忙碌但订单积压，是典型端到端吞吐问题。 |
| should-trigger-02 | should_trigger | moving-bottleneck-red-light-loop | moving-bottleneck-red-light-loop | PASS | 局部优化没有改变发布周期，需要验证是否命中瓶颈。 |
| should-trigger-03 | should_trigger | moving-bottleneck-red-light-loop | moving-bottleneck-red-light-loop | PASS | 英文请求直接要求定位内容流水线瓶颈。 |
| should-not-trigger-01 | should_not_trigger | design-production-responsibility-loop | design-production-responsibility-loop | PASS | 问题是设计团队长期承担运维后果。 |
| should-not-trigger-02 | should_not_trigger | none | none | PASS | 稳定版查询是事实检索。 |
| edge-01 | edge_case | none | none | PASS | 小说创作不是稳定可观测的吞吐流程。 |

## 结论

触发、拒绝和兄弟 Skill 混淆测试全部通过。
