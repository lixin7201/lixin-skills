# world-first-focus-shift — Stage 4 压力测试结果

- **测试日期**：2026-07-21
- **方法**：两个 `fork_turns=none` 的干净上下文独立评审；只给 5 个相邻 Skill 的 `SKILL.md` 与 8 条无答案 prompt，明确禁止读取 `test-prompts.json` 和 `test-results.md`。
- **用例**：8 条（4 应调用、3 个跨 Skill 诱饵、1 个不可逆风险边界）。
- **最终结果**：两名评审均为 8/8，合计 16/16 判断一致；主用例通过率 **100%**，诱饵 3/3，误路由 0。

| case | 预期主语义 | 评审 A | 评审 B | 结果 | 复核 |
|---|---|---|---|---|---|
| should-trigger-01 | 旧咨询业务外挂陷阱 | `world-first-focus-shift` | `world-first-focus-shift` | PASS | 明确识别旧身份与旧交付被默认不可变。 |
| should-trigger-02 | 暂时移除培训师身份 | `world-first-focus-shift` | `world-first-focus-shift` | PASS | 先冻结旧身份，再从平台结构重写问题。 |
| should-trigger-03 | 保护旧软件遮蔽交付变化 | `world-first-focus-shift` | `world-first-focus-shift` | PASS | 先检查能力、成本、角色、关系和约束的变化。 |
| should-trigger-04 | 英文焦点重构 | `world-first-focus-shift` | `world-first-focus-shift` | PASS | 在选择试验前触发，顺序正确。 |
| should-not-trigger-01 | 热点与算法失真 | `novelty-information-distortion-audit` | `novelty-information-distortion-audit` | PASS | 只需核验趋势真假，未越级重写方向。 |
| should-not-trigger-02 | 已定方向的探索/利用切换 | `explore-exploit-mode-switch` | `explore-exploit-mode-switch` | PASS | 问题空间已成立，本 Skill 正确忍住。 |
| should-not-trigger-03 | 已定方向的生产距离 | `production-distance-usefulness-audit` | `production-distance-usefulness-audit` | PASS | 先审计受益者、交付与反馈距离。 |
| edge-01 | 不可逆重仓必须拒绝 | `reality-constraint-premise-audit` | `reality-constraint-premise-audit` | PASS | 两名评审都选择更窄、更安全的现实前提审计，拒绝把焦点转换当全押许可。 |

## 边界判定说明

`edge-01` 的答案键允许本 Skill 诊断旧身份锁定，但核心验收是“不得直接运行不可逆重仓，必须先做证据与现实约束审计”。两名评审一致选择 `reality-constraint-premise-audit` 作为主路由，严格满足安全边界，且说明可将计划缩成有预算、有退出门的代理实验。因此不为追求本 Skill 触发率而改宽 description，也不修改测试题。

## 回炉记录

- 本轮 8/8，无需回炉。
- 没有依据测试结果扩大触发范围；高风险边界继续优先路由现实约束审计。

## 隔离与证据

- 测试定义：`test-prompts.json`
- 评审 A：`/root/g04_blind_judge_a`
- 评审 B：`/root/g04_blind_judge_b`
- 两名评审均声明未读取答案文件、未修改文件。
