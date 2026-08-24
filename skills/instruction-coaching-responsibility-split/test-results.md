# instruction-coaching-responsibility-split — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试者只看到 21 个 Skill 的 name、description、SKILL.md 与 prompt，看不到类型、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同书兄弟或同作者相邻 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | C-19 | `should_trigger` | `instruction-coaching-responsibility-split` | `instruction-coaching-responsibility-split` | PASS | 学员理解但没有执行，说明讲解层完成而行为教练层的任务、反馈和障碍处理可能缺失。 |
| should-trigger-02 | C-20 | `should_trigger` | `instruction-coaching-responsibility-split` | `instruction-coaching-responsibility-split` | PASS | 微课与社群分别承诺什么，正需要拆开讲解层和教练层的责任、验收、容量与停止边界。 |
| should-trigger-03 | C-21 | `should_trigger` | `instruction-coaching-responsibility-split` | `instruction-coaching-responsibility-split` | PASS | 内容供给充足但课后反馈无人负责，是讲解与教练责任未分层、实践链无责任人的典型问题。 |
| should-not-trigger-01 | C-22 | `should_not_trigger` | `active-learning-operating-system` | `active-learning-operating-system` | PASS | 学习者希望围绕真实项目边学边做并形成反馈闭环，直接符合主动学习操作系统的触发条件。 |
| should-not-trigger-02 | C-23 | `should_not_trigger` | `platform-commerce-closure-audit` | `platform-commerce-closure-audit` | PASS | 观看量已有，但咨询、支付和交付之间流失，需沿商业交易全链定位断点，而非继续增加课程内容。 |
| edge-01 | C-24 | `edge_case` | `边界行为` | `instruction-coaching-responsibility-split` | PASS | 正确拒绝在事故中用责任切分推卸职责，先止损、协同、留痕再追责。 |

## 回炉记录

- 本 Skill 初轮行为判定 6/6，无需修改 Skill 或测试。
- 六个边界题一度因旧判卷器要求“必须选中源 Skill”显示为路由失败；人工逐项复核确认其选择 `null` 时准确执行了停止、降级或升级条件。判卷器改为分别检查路由与显式边界行为，未修改任何 prompt、答案或盲测输出。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 逐条机器判卷：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/BLIND_GRADE.json`
