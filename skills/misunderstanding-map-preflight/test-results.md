# misunderstanding-map-preflight — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试员只看到 15 个 Skill 的 name、description、SKILL.md 与 prompt，看不到 type、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同批兄弟 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | A-25 | `should_trigger` | `misunderstanding-map-preflight` | `misunderstanding-map-preflight` | PASS | 已确定的新规则即将上线，用户明确要在发布前测试范围扩大这一误解。 |
| should-trigger-02 | A-26 | `should_trigger` | `misunderstanding-map-preflight` | `misunderstanding-map-preflight` | PASS | 陌生概念发布前最容易被旧概念自动补全，适合用无提示复述发现概念替换和混淆。 |
| should-trigger-03 | A-27 | `should_trigger` | `misunderstanding-map-preflight` | `misunderstanding-map-preflight` | PASS | 读者反复把建议扩大到未声明范围，已有历史误解模式可用于系统修订材料的正反定义和边界。 |
| should-not-trigger-01 | A-28 | `should_not_trigger` | `accurate-restatement-feedback-loop` | `accurate-restatement-feedback-loop` | PASS | 一次真实评审刚给出含糊负面反馈，当前首要任务是复述并确认对方真正担忧的问题。 |
| should-not-trigger-02 | A-29 | `should_not_trigger` | `speaker-claim-consistency-audit` | `speaker-claim-consistency-audit` | PASS | 讲稿包含讲者自己不相信的承诺，需要按确信、证据和归属决定删除、改写、声明或拒绝。 |
| edge-01 | A-30 | `edge_case` | `边界语义` | `null` | PASS | 低风险同质小群采用轻量确认而非机械扩大样本。 |

## 回炉记录

- 本 Skill 初轮 6/6，无需回炉。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 回炉复测（如适用）：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A06-R1.json`
