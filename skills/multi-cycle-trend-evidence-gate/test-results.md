# multi-cycle-trend-evidence-gate — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试者只看到 21 个 Skill 的 name、description、SKILL.md 与 prompt，看不到类型、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同书兄弟或同作者相邻 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | B-13 | `should_trigger` | `multi-cycle-trend-evidence-gate` | `multi-cycle-trend-evidence-gate` | PASS | 连续三年可能只是一段景气期，不能在未定义并比较完整周期前认定长期增长。 |
| should-trigger-02 | B-14 | `should_trigger` | `multi-cycle-trend-evidence-gate` | `multi-cycle-trend-evidence-gate` | PASS | 一次牛熊恢复只提供一个周期证据，尚不足以单独支持长期趋势或持有结论。 |
| should-trigger-03 | B-15 | `should_trigger` | `multi-cycle-trend-evidence-gate` | `multi-cycle-trend-evidence-gate` | PASS | 新技术已改变参与者结构，必须先做结构稳定性检查，不能机械外推旧模式的多次成功。 |
| should-not-trigger-01 | B-16 | `should_not_trigger` | `active-choice-passive-hold-protocol` | `active-choice-passive-hold-protocol` | PASS | 趋势证据已通过后，问题转为如何避免短期噪声驱动持有期反复改策略。 |
| should-not-trigger-02 | B-17 | `should_not_trigger` | `owner-view-value-safety-margin` | `owner-view-value-safety-margin` | PASS | 问题直接要求估算公司价值区间并判断当前价格是否具有安全边际。 |
| edge-01 | B-18 | `edge_case` | `边界行为` | `null` | PASS | 正确把单周期趋势结论降为假设，只允许损失有上限的可逆试验。 |

## 回炉记录

- 本 Skill 初轮行为判定 6/6，无需修改 Skill 或测试。
- 六个边界题一度因旧判卷器要求“必须选中源 Skill”显示为路由失败；人工逐项复核确认其选择 `null` 时准确执行了停止、降级或升级条件。判卷器改为分别检查路由与显式边界行为，未修改任何 prompt、答案或盲测输出。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 逐条机器判卷：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/BLIND_GRADE.json`
