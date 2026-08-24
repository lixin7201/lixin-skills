# decision-node-error-multiplier-audit — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试者只看到 21 个 Skill 的 name、description、SKILL.md 与 prompt，看不到类型、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同书兄弟或同作者相邻 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | A-19 | `should_trigger` | `decision-node-error-multiplier-audit` | `decision-node-error-multiplier-audit` | PASS | 交易策略要求连续判断多个节点，单步合理但整链执行失败，正是决策节点乘法脆弱性。 |
| should-trigger-02 | A-20 | `should_trigger` | `decision-node-error-multiplier-audit` | `decision-node-error-multiplier-audit` | PASS | 十几个可选分支增加大量临场判断，整体错误说明需审计并删减非必要节点。 |
| should-trigger-03 | A-21 | `should_trigger` | `decision-node-error-multiplier-audit` | `decision-node-error-multiplier-audit` | PASS | 自动化发布单步成功率高而全链频繁失败，符合连续节点正确率相乘导致整体脆弱的情形。 |
| should-not-trigger-01 | A-22 | `should_not_trigger` | `whole-action-chain-validity-audit` | `whole-action-chain-validity-audit` | PASS | 方案缺少退款、交付和售后等必要环节，需要补齐完整动作链及其衔接。 |
| should-not-trigger-02 | A-23 | `should_not_trigger` | `investment-decision-firewall` | `investment-decision-firewall` | PASS | 市场大涨触发立刻重仓冲动，明确需要投资前的情绪拦截、书面论证和延迟机制。 |
| edge-01 | A-24 | `edge_case` | `边界行为` | `null` | PASS | 正确保留必要安全门；虽选择 null，但边界动作与预期完全一致。 |

## 回炉记录

- 本 Skill 初轮行为判定 6/6，无需修改 Skill 或测试。
- 六个边界题一度因旧判卷器要求“必须选中源 Skill”显示为路由失败；人工逐项复核确认其选择 `null` 时准确执行了停止、降级或升级条件。判卷器改为分别检查路由与显式边界行为，未修改任何 prompt、答案或盲测输出。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 逐条机器判卷：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/BLIND_GRADE.json`
