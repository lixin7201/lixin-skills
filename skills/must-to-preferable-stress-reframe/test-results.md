# 阶段 4 压力测试结果：must-to-preferable-stress-reframe

- 日期: 2026-07-20
- 测试方式: 独立 sub-agent 盲测；只提供同书 Skill 清单、`SKILL.md` 路径和中性编号 prompt，未提供 `type`、`expected_behavior`、`notes`。
- 盲测子代理: `019f7ed5-9cc9-7873-83d6-021bcd169d5a`
- 测试文件: `test-prompts.json`

## 结果

| 类型 | 通过 | 说明 |
|---|---:|---|
| should_trigger | 3/3 | 绝不能搞砸、销售目标必须达成、must thinking 均正确触发 |
| should_not_trigger | 2/2 | 批评后转行动转 `negative-emotion-action-routing`；自伤念头判为 none 并求助 |
| edge_case | 1/1 | 长期过劳/羞辱式管理判为组织边界，不归因个人思维 |
| 同书兄弟诱饵 | 1/1 | 与 `negative-emotion-action-routing` 区分清楚 |

总通过率: **6/6，100%**。

## 失败与回炉

无失败项，未回炉。

## 结论

通过阶段 4，可进入阶段 5 安装。
