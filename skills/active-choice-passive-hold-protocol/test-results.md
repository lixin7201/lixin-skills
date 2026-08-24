# active-choice-passive-hold-protocol — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试者只看到 21 个 Skill 的 name、description、SKILL.md 与 prompt，看不到类型、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同书兄弟或同作者相邻 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | B-07 | `should_trigger` | `active-choice-passive-hold-protocol` | `active-choice-passive-hold-protocol` | PASS | 已研究并作出长期配置，却被每日行情诱发换策略，正是选择后减少噪声干预的场景。 |
| should-trigger-02 | B-08 | `should_trigger` | `active-choice-passive-hold-protocol` | `active-choice-passive-hold-protocol` | PASS | 公司战略因热点反复横跳，需要先主动确定方向与复核条件，再在条件未变时保持耐心。 |
| should-trigger-03 | B-09 | `should_trigger` | `active-choice-passive-hold-protocol` | `active-choice-passive-hold-protocol` | PASS | 用户要防止长期持有滑向死扛，技能正要求预先设定论文破裂、风险预算和退出条件。 |
| should-not-trigger-01 | B-10 | `should_not_trigger` | `multi-cycle-trend-evidence-gate` | `multi-cycle-trend-evidence-gate` | PASS | 用单轮上涨认定长期趋势，正是该技能要拦截的单周期外推。 |
| should-not-trigger-02 | B-11 | `should_not_trigger` | `investment-decision-firewall` | `investment-decision-firewall` | PASS | 尚未做资金资格检查就因暴涨想立即重仓，是典型的高情绪入场、叙事诱惑和风险边界缺失。 |
| edge-01 | B-12 | `edge_case` | `边界行为` | `null` | PASS | 正确把监管禁令识别为立即重开条件，没有等待固定复核日。 |

## 回炉记录

- 本 Skill 初轮行为判定 6/6，无需修改 Skill 或测试。
- 六个边界题一度因旧判卷器要求“必须选中源 Skill”显示为路由失败；人工逐项复核确认其选择 `null` 时准确执行了停止、降级或升级条件。判卷器改为分别检查路由与显式边界行为，未修改任何 prompt、答案或盲测输出。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 逐条机器判卷：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/BLIND_GRADE.json`
