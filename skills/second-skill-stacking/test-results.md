# 压力测试结果：second-skill-stacking

- 测试日期：2026-07-19
- 测试方式：独立 sub-agent 盲测；盲测员只看到全部 Skill 的 name/description 与无标签 prompt，未看到类型、预期答案或判分键。
- 通过率：**100%（6/6）**
- 判定：接受

| 盲测 ID / Skill 内 ID | 类型 | Prompt | 预期主 Skill | 实际主 Skill | 结果 |
|---|---|---|---|---|---|
| BT079 / should-trigger-01 | should_trigger | 怎样形成差异化能力 | `second-skill-stacking` | `second-skill-stacking` | ✓ |
| BT080 / should-trigger-02 | should_trigger | 我该叠加什么第二技能 | `second-skill-stacking` | `second-skill-stacking` | ✓ |
| BT081 / should-trigger-03 | should_trigger | 单项能力普通，怎么错维竞争 | `second-skill-stacking` | `second-skill-stacking` | ✓ |
| BT082 / should-not-trigger-01 | should_not_trigger | 请告诉我《价值心法》的作者、出版社和出版时间。 | 无 | 无 | ✓ |
| BT083 / should-not-trigger-02 | should_not_trigger | 没人教我怎么学会这个 | `active-learning-operating-system` | `active-learning-operating-system` | ✓ |
| BT084 / edge-01 | edge_case | 我什么都还不会，想同时学编程、设计、营销和投资 | 无 | 无 | ✓ |

## 输出质量核对

所有应触发 case 均给出了与对应 Skill 首步一致的可执行动作；所有不应触发/边界 case 均给出了不调用理由及合适的替代动作。原始理由和首个动作保存在 `_pressure-test/blind-results-*.json`。

## 失败分析

无。6 条全部符合预期，无需回炉。
