# correctness-nonconsensus-evidence-matrix — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试员只看到 15 个 Skill 的 name、description、SKILL.md 与 prompt，看不到 type、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同批兄弟 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | C-07 | `should_trigger` | `correctness-nonconsensus-evidence-matrix` | `correctness-nonconsensus-evidence-matrix` | PASS | 团队共识与一组用户数据支持的少数判断冲突，适合拆分正确性和认同度并做可逆验证。 |
| should-trigger-02 | C-08 | `should_trigger` | `correctness-nonconsensus-evidence-matrix` | `correctness-nonconsensus-evidence-matrix` | PASS | 行业共识缺少一手证据，需要避免用认同度反推正确性并保留反证条件。 |
| should-trigger-03 | C-09 | `should_trigger` | `correctness-nonconsensus-evidence-matrix` | `correctness-nonconsensus-evidence-matrix` | PASS | 把别人没看懂当成自己正确并准备重仓，正需要用证据、反方和损失上限阻断非共识冲动。 |
| should-not-trigger-01 | C-10 | `should_not_trigger` | `novelty-information-distortion-audit` | `novelty-information-distortion-audit` | PASS | 刚上热搜的行业消息可能受算法和营销筛选，需先分离新鲜度与重要性。 |
| should-not-trigger-02 | C-11 | `should_not_trigger` | `explore-exploit-mode-switch` | `explore-exploit-mode-switch` | PASS | 假设已决定验证，当前问题正是选择广泛探索还是沿现有路线利用。 |
| edge-01 | C-12 | `edge_case` | `边界语义` | `null` | PASS | 正确拒绝用非共识优势绕过高风险医疗标准。 |

## 回炉记录

- 本 Skill 初轮 6/6，无需回炉。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 回炉复测（如适用）：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_pressure-test/blind-results-A06-R1.json`
