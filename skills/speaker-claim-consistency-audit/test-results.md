# speaker-claim-consistency-audit — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试员只看到 15 个 Skill 的 name、description、SKILL.md 与 prompt，看不到 type、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同批兄弟 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | A-19 | `should_trigger` | `speaker-claim-consistency-audit` | `speaker-claim-consistency-audit` | PASS | 讲者被要求公开承诺自己不认可的日期，需要区分组织立场、个人确信、证据和表达边界。 |
| should-trigger-02 | A-20 | `should_trigger` | `speaker-claim-consistency-audit` | `speaker-claim-consistency-audit` | PASS | 讲稿中的强烈主张缺少根据，仅因听起来厉害而保留，正需审计主张归属、确信和证据。 |
| should-trigger-03 | A-21 | `should_trigger` | `speaker-claim-consistency-audit` | `speaker-claim-consistency-audit` | PASS | 上台时扮演陌生人设并使用平时不会说的话，体现讲者身份、语言和真实确信不一致。 |
| should-not-trigger-01 | A-22 | `should_not_trigger` | `misunderstanding-map-preflight` | `misunderstanding-map-preflight` | PASS | 规则已经确定，且担心发布前被扩大理解为无条件退款，适合用小样本复述预演误解。 |
| should-not-trigger-02 | A-23 | `should_not_trigger` | `accurate-restatement-feedback-loop` | `accurate-restatement-feedback-loop` | PASS | 评审反馈含糊且已经发生，需要先确认“不可靠”具体指向的事实、担忧、影响和请求。 |
| edge-01 | A-24 | `edge_case` | `边界语义` | `speaker-claim-consistency-audit` | PASS | 正确区分组织立场与个人确信并保留归属。 |

## 回炉记录

- 本 Skill 初轮 6/6，无需回炉。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 回炉复测（如适用）：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A06-R1.json`
