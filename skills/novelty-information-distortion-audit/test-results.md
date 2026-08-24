# novelty-information-distortion-audit — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试员只看到 15 个 Skill 的 name、description、SKILL.md 与 prompt，看不到 type、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同批兄弟 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | A-13 | `should_trigger` | `novelty-information-distortion-audit` | `novelty-information-distortion-audit` | PASS | 群体转发和突然爆火正在推动立即改变产品方向，需要先区分新鲜度、重要性和证据强度。 |
| should-trigger-02 | A-14 | `should_trigger` | `novelty-information-distortion-audit` | `novelty-information-distortion-audit` | PASS | 信息流中的一致观点不等于总体真实，需要检查算法筛选、社交展示和缺失样本。 |
| should-trigger-03 | A-15 | `should_trigger` | `novelty-information-distortion-audit` | `novelty-information-distortion-audit` | PASS | 竞品新概念触发 FOMO，需先拆开新鲜感与对当前目标、前提和风险的实际重要性。 |
| should-not-trigger-01 | A-16 | `should_not_trigger` | `attention-allocation-ledger` | `attention-allocation-ledger` | PASS | 消息真实性已经确认，剩下的是如何按价值和收益重新配置被占用的注意力。 |
| should-not-trigger-02 | A-17 | `should_not_trigger` | `correctness-nonconsensus-evidence-matrix` | `correctness-nonconsensus-evidence-matrix` | PASS | 团队共识与个人产品判断冲突，需要把是否正确和是否被认同拆开，并用证据验证非共识假设。 |
| edge-01 | A-18 | `edge_case` | `边界语义` | `null` | PASS | 官方一手公告与当前暴露已由 prompt 给定，正确停止反新鲜拖延并转入安全响应。 |

## 回炉记录

- 本 Skill 初轮 6/6，无需回炉。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 回炉复测（如适用）：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A06-R1.json`
