# interest-after-competence-diagnostic — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试者只看到 21 个 Skill 的 name、description、SKILL.md 与 prompt，看不到类型、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同书兄弟或同作者相邻 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | A-13 | `should_trigger` | `interest-after-competence-diagnostic` | `interest-after-competence-diagnostic` | PASS | 只学两次便以没兴趣准备退出，可能是初学笨拙和反馈缺失被误判为不适合。 |
| should-trigger-02 | A-14 | `should_trigger` | `interest-after-competence-diagnostic` | `interest-after-competence-diagnostic` | PASS | 从未完成一篇文章，尚无最低真实体验支撑“不喜欢写作”的判断。 |
| should-trigger-03 | A-15 | `should_trigger` | `interest-after-competence-diagnostic` | `interest-after-competence-diagnostic` | PASS | 尚不会核心工作时感到无聊，需要区分未入门、反馈缺失、环境不合与真实不适配。 |
| should-not-trigger-01 | A-16 | `should_not_trigger` | `long-change-intensity-budget` | `long-change-intensity-budget` | PASS | 健身一年方向已经确定，当前问题是为长期改变设置可恢复、不过载的过程强度。 |
| should-not-trigger-02 | A-17 | `should_not_trigger` | `familiarity-weighted-estimation` | `familiarity-weighted-estimation` | PASS | 第一次做新技术项目并询问学习、试错、返工时间，完全命中陌生度加权估时。 |
| edge-01 | A-18 | `edge_case` | `边界行为` | `null` | PASS | 正确拒绝在持续羞辱和健康损害中强迫坚持，优先安全退出与支持。 |

## 回炉记录

- 本 Skill 初轮行为判定 6/6，无需修改 Skill 或测试。
- 六个边界题一度因旧判卷器要求“必须选中源 Skill”显示为路由失败；人工逐项复核确认其选择 `null` 时准确执行了停止、降级或升级条件。判卷器改为分别检查路由与显式边界行为，未修改任何 prompt、答案或盲测输出。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 逐条机器判卷：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/BLIND_GRADE.json`
