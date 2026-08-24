# discussion-goal-routing — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试员只看到 15 个 Skill 的 name、description、SKILL.md 与 prompt，看不到 type、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同批兄弟 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | B-25 | `should_trigger` | `discussion-goal-routing` | `discussion-goal-routing` | PASS | 错误数据争议已演变为互相讽刺，需要先判断是否还有共同求真和可接受的证据规则。 |
| should-trigger-02 | B-26 | `should_trigger` | `discussion-goal-routing` | `discussion-goal-routing` | PASS | 表面谈方案、实际争身份胜负，需把对话重新路由到事实、决定或关系修复。 |
| should-trigger-03 | B-27 | `should_trigger` | `discussion-goal-routing` | `discussion-goal-routing` | PASS | 合规争议不能以“不争论”为由退出免责，应留痕并路由到正式升级渠道。 |
| should-not-trigger-01 | B-28 | `should_not_trigger` | `accurate-restatement-feedback-loop` | `accurate-restatement-feedback-loop` | PASS | 对方的“不可靠”没有具体原因，需通过不夹带反驳的复述获得确认。 |
| should-not-trigger-02 | B-29 | `should_not_trigger` | `problem-ownership-routing` | `problem-ownership-routing` | PASS | 问题已确认但本人没有合同权限，重点是确定有结果责任和决策权限的接收节点。 |
| edge-01 | B-30 | `edge_case` | `边界语义` | `discussion-goal-routing` | PASS | 正确从无效争辩切换到安全责任处理与正式升级。 |

## 回炉记录

- 本 Skill 初轮 6/6，无需回炉。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 回炉复测（如适用）：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A06-R1.json`
