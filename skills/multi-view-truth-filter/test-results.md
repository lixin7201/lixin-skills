# 压力测试结果：multi-view-truth-filter

- 测试日期：2026-07-19
- 测试方式：独立 sub-agent 盲测；盲测员只看到全部 Skill 的 name/description 与无标签 prompt，未看到类型、预期答案或判分键。
- 通过率：**100%（6/6）**
- 判定：接受

| 盲测 ID / Skill 内 ID | 类型 | Prompt | 预期主 Skill | 实际主 Skill | 结果 |
|---|---|---|---|---|---|
| BT037 / should-trigger-01 | should_trigger | 大家都这么说但我不放心 | `multi-view-truth-filter` | `multi-view-truth-filter` | ✓ |
| BT038 / should-trigger-02 | should_trigger | 帮我找反方证据 | `multi-view-truth-filter` | `multi-view-truth-filter` | ✓ |
| BT039 / should-trigger-03 | should_trigger | 怎样避免被单一观点带偏 | `multi-view-truth-filter` | `multi-view-truth-filter` | ✓ |
| BT040 / should-not-trigger-01 | should_not_trigger | 请告诉我《价值心法》的作者、出版社和出版时间。 | 无 | 无 | ✓ |
| BT041 / should-not-trigger-02 | should_not_trigger | 有什么成功做法可以先模仿 | `proven-pattern-transfer` | `proven-pattern-transfer` | ✓ |
| BT042 / edge-01 | edge_case | 三家权威机构都给出同一温度读数，我还要找第四个反对者吗？ | 无 | 无 | ✓ |

## 输出质量核对

所有应触发 case 均给出了与对应 Skill 首步一致的可执行动作；所有不应触发/边界 case 均给出了不调用理由及合适的替代动作。原始理由和首个动作保存在 `_pressure-test/blind-results-*.json`。

## 失败分析

无。6 条全部符合预期，无需回炉。
