# audience-reverse-shaping-audit — Stage 4 压力测试结果

- **测试日期**：2026-07-20
- **方法**：干净上下文独立 sub-agent 盲测；测试者只看到 21 个 Skill 的 name、description、SKILL.md 与 prompt，看不到类型、预期和答案键。
- **用例**：6 条（3 应调用、2 不应调用、1 边界）；不应调用含同书兄弟或同作者相邻 Skill 诱饵。
- **最终结果**：6/6，**100%**；诱饵 2/2，容错 0。

| case | blind id | 类型 | 预期路由 | 盲测选择 | 结果 | 主流程复核 |
|---|---|---|---|---|---|---|
| should-trigger-01 | C-13 | `should_trigger` | `audience-reverse-shaping-audit` | `audience-reverse-shaping-audit` | PASS | 播放增长同时目标客户流失，表明平台流量奖励可能正在把内容和受众结构带离原方向。 |
| should-trigger-02 | C-14 | `should_trigger` | `audience-reverse-shaping-audit` | `audience-reverse-shaping-audit` | PASS | 争议评论的即时奖励正在把下一轮选题推向极端，形成受众反馈反向塑造创作者的闭环。 |
| should-trigger-03 | C-15 | `should_trigger` | `audience-reverse-shaping-audit` | `audience-reverse-shaping-audit` | PASS | 新粉丝数量增长但没有购买或采用，需判断实际受众是否偏离目标并正在用流量反馈塑造方向。 |
| should-not-trigger-01 | C-16 | `should_not_trigger` | `platform-commerce-closure-audit` | `platform-commerce-closure-audit` | PASS | 受众已确认正确，问题集中在咨询、支付和交付的交易链断点，应审计商业闭环而非受众塑造。 |
| should-not-trigger-02 | C-17 | `should_not_trigger` | `evergreen-content-fertility-filter` | `evergreen-content-fertility-filter` | PASS | 用户明确要用正确、有用、必备和耐久标准筛选文章，直接对应长效内容繁殖力五问。 |
| edge-01 | C-18 | `edge_case` | `边界行为` | `audience-reverse-shaping-audit` | PASS | 正确保留用户屏蔽权；反向塑造不等于强制触达或操纵。 |

## 回炉记录

- 本 Skill 初轮行为判定 6/6，无需修改 Skill 或测试。
- 六个边界题一度因旧判卷器要求“必须选中源 Skill”显示为路由失败；人工逐项复核确认其选择 `null` 时准确执行了停止、降级或升级条件。判卷器改为分别检查路由与显式边界行为，未修改任何 prompt、答案或盲测输出。

## 证据路径

- 测试定义：`test-prompts.json`
- 隔离盲测包：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-packets`
- 原始盲测结果：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/blind-results-A.json`、`blind-results-B.json`、`blind-results-C.json`
- 逐条机器判卷：`/Users/REPLACE_ME/.codex/skills/cangjie-skill/books/_authors/li-xiao-lai/_batch3-pressure-test/BLIND_GRADE.json`
