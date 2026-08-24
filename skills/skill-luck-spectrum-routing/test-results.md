# skill-luck-spectrum-routing — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试者只看到 21 个 Skill 的 name、description、SKILL.md 与 prompt，看不到类型、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同书兄弟或同作者相邻 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | B-01 | `should_trigger` | `skill-luck-spectrum-routing` | `skill-luck-spectrum-routing` | PASS | 问题要区分单次创业成功中的可重复能力与随机性，正是技巧—运气连续谱的判断任务。 |
| should-trigger-02 | B-02 | `should_trigger` | `skill-luck-spectrum-routing` | `skill-luck-spectrum-routing` | PASS | 竞技结果同时受训练与签位影响，需要先定位技巧和运气的权重，再分配训练与参赛资源。 |
| should-trigger-03 | B-03 | `should_trigger` | `skill-luck-spectrum-routing` | `skill-luck-spectrum-routing` | PASS | 高波动机会的单次结果运气成分高，技能要求据此缩小押注并保留失败空间。 |
| should-not-trigger-01 | B-04 | `should_not_trigger` | `decision-node-error-multiplier-audit` | `decision-node-error-multiplier-audit` | PASS | 十个连续判断点造成联合执行脆弱性，核心是枚举并删除、自动化或预承诺非必要节点。 |
| should-not-trigger-02 | B-05 | `should_not_trigger` | `correctness-nonconsensus-evidence-matrix` | `correctness-nonconsensus-evidence-matrix` | PASS | 问题直接要求评估非共识判断的正确性证据，并决定是否做小额可逆验证。 |
| edge-01 | B-06 | `edge_case` | `边界行为` | `null` | PASS | 正确拒绝把考试失败全推给运气，先复盘可训练因素并分列随机因素。 |

## 回炉记录

- 本 Skill 初轮行为判定 6/6，无需修改 Skill 或测试。
- 六个边界题一度因旧判卷器要求“必须选中源 Skill”显示为路由失败；人工逐项复核确认其选择 `null` 时准确执行了停止、降级或升级条件。判卷器改为分别检查路由与显式边界行为，未修改任何 prompt、答案或盲测输出。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 逐条机器判卷：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/BLIND_GRADE.json`
