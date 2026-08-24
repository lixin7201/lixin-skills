# long-change-intensity-budget — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试员只看到 15 个 Skill 的 name、description、SKILL.md 与 prompt，看不到 type、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同批兄弟 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | C-01 | `should_trigger` | `long-change-intensity-budget` | `long-change-intensity-budget` | PASS | 从零直接每天写两小时是典型的长期改变初始强度过高，需要按承载力设置可持续剂量。 |
| should-trigger-02 | C-02 | `should_trigger` | `long-change-intensity-budget` | `long-change-intensity-budget` | PASS | 公开宣誓后短期坚持、一次中断便放弃，符合反复高强度启动又反弹的模式。 |
| should-trigger-03 | C-03 | `should_trigger` | `long-change-intensity-budget` | `long-change-intensity-budget` | PASS | 这是组织长期习惯被现有会议和奖励环境反向塑造的问题。 |
| should-not-trigger-01 | C-04 | `should_not_trigger` | `explore-exploit-mode-switch` | `explore-exploit-mode-switch` | PASS | 连续调试却没有新信息，正需要依据新信息率决定由深挖切换到广搜。 |
| should-not-trigger-02 | C-05 | `should_not_trigger` | `null` | `null` | PASS | 这是有硬截止时间的一次性事故报告执行任务，不是长期习惯、来源选择或探索利用切换问题。 |
| edge-01 | C-06 | `edge_case` | `边界语义` | `null` | PASS | 正确拒绝把严重成瘾当作普通低强度习惯改变，升级专业支持。 |

## 回炉记录

- 本 Skill 初轮 6/6，无需回炉。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 回炉复测（如适用）：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A06-R1.json`
