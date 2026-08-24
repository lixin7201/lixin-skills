# extreme-price-volume-hindsight-audit — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试者只看到 21 个 Skill 的 name、description、SKILL.md 与 prompt，看不到类型、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同书兄弟或同作者相邻 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | C-01 | `should_trigger` | `extreme-price-volume-hindsight-audit` | `extreme-price-volume-hindsight-audit` | PASS | 复盘把图上已完成的最高点当成当时显而易见、且可全仓成交的选择，正是极值后见偏差与容量幻觉。 |
| should-trigger-02 | C-02 | `should_trigger` | `extreme-price-volume-hindsight-audit` | `extreme-price-volume-hindsight-audit` | PASS | 大仓位精准卖顶买底的传言必须同时核验极值可识别性、成交量、深度、滑点和连续两次判断。 |
| should-trigger-03 | C-03 | `should_trigger` | `extreme-price-volume-hindsight-audit` | `extreme-price-volume-hindsight-audit` | PASS | 用事后最佳价格评价交易员忽略了当时信息集和实际可执行性，属于典型后见复盘偏差。 |
| should-not-trigger-01 | C-04 | `should_not_trigger` | `multi-cycle-trend-evidence-gate` | `multi-cycle-trend-evidence-gate` | PASS | 问题正在用跨周期表现判断长期趋势，需核验周期是否完整可比以及制度、技术和样本结构是否稳定。 |
| should-not-trigger-02 | C-05 | `should_not_trigger` | `investment-decision-firewall` | `investment-decision-firewall` | PASS | 暴涨引发的追入冲动是重要投资决定中的情绪与从众风险，需要事前暂停、书面论证和延迟机制。 |
| edge-01 | C-06 | `edge_case` | `边界行为` | `null` | PASS | 正确拒绝用后见偏差为事前仓位违规开脱，转向过程与治理处置。 |

## 回炉记录

- 本 Skill 初轮行为判定 6/6，无需修改 Skill 或测试。
- 六个边界题一度因旧判卷器要求“必须选中源 Skill”显示为路由失败；人工逐项复核确认其选择 `null` 时准确执行了停止、降级或升级条件。判卷器改为分别检查路由与显式边界行为，未修改任何 prompt、答案或盲测输出。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 逐条机器判卷：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/BLIND_GRADE.json`
