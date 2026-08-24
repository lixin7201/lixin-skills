# surge-mode-governor 压力测试结果

> 评测模式：主流程 fallback；使用不含 type/expected 的 blind-inputs.json。当前环境无独立 sub-agent，可信度低于独立盲测。

- 通过：6/6
- 通过率：100%
- 诱饵容错：0（全部 should_not_trigger 必须通过）

| Case | 类型 | 期望选择 | 实际选择 | 结果 | 判断理由 |
|---|---|---|---|---|---|
| should-trigger-01 | should_trigger | surge-mode-governor | surge-mode-governor | PASS | 三周现金形成真实生存窗口，正在考虑全员战时状态。 |
| should-trigger-02 | should_trigger | surge-mode-governor | surge-mode-governor | PASS | 六小时迁移窗口需要跨团队临时运行模式。 |
| should-trigger-03 | should_trigger | surge-mode-governor | surge-mode-governor | PASS | 用户要求审计永久 crunch 是否合理，属于治理器反向触发。 |
| should-not-trigger-01 | should_not_trigger | moving-bottleneck-red-light-loop | moving-bottleneck-red-light-loop | PASS | 当前尚不知道客服积压的主瓶颈。 |
| should-not-trigger-02 | should_not_trigger | none | none | PASS | 个人日记习惯没有真实危机窗口。 |
| edge-01 | edge_case | surge-mode-governor | surge-mode-governor | PASS | 正在考虑通宵冲刺，治理器应触发并因需求未验证拒绝启用。 |

## 结论

触发、拒绝和兄弟 Skill 混淆测试全部通过。
