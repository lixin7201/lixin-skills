---
name: kgi-kpi-causal-tree-validity-check
description: |
  当用户已有明确 KGI/最终结果，却不知道该拆哪些 KPI、指标之间是否有因果、为什么目标没达成时使用。触发词包括: KGI, KPI, 指标树, 指标拆解, causal metric tree, metric decomposition。不适用于: 目标措辞 SMART 改写、OKR 是否适用、0-1 探索、战略模型选择或现场 6S 治理。
source_book: 《分章节P1-06 组织团队管理》 PPT
source_chapter: Slide 13; 《6S管理方法与技巧培训PPT》Slide 38
tags: [metrics, kpi, management]
related_skills:
  - slug: okr-smart-kr-quality-guard
    relation: contrasts-with
  - slug: okr-fit-preflight
    relation: depends-on
  - slug: strategy-model-evidence-gate-router
    relation: contrasts-with
  - slug: six-s-site-order-governance-loop
    relation: composes-with
---

# KGI-KPI 因果树有效性检查

## R — 原文 (Reading)

> 将关键目标指标（KGI）放在顶端进行树状分解，分析为了达成KGI需要完成哪些指标，然后将过程进行数值化验证，这些指标成为KPI。
>
> — 《分章节P1-06 组织团队管理》Slide 13

> 一开始设定的数值可以不必太准确，只要是个概数就可以，同时需要注意“确认KPI指标是否有效”。
>
> — 《分章节P1-06 组织团队管理》Slide 13

> 在最终未能达成KGI的情况下，可以对哪个部分的KPI出现了问题进行验证，找出需要解决的问题。
>
> — 《分章节P1-06 组织团队管理》Slide 13

## I — 方法论骨架 (Interpretation)

KPI 树不是把目标拆成很多数字，而是把一个最终结果拆成可验证的因果结构。顶端是 KGI，也就是最终要达成的结果；下一层 KPI 必须能解释 KGI 为什么上升或下降。

拆树时先判断业务是否稳定、结果是否可度量，再用加法或乘法表示关键关系。人数类、来源类常用加法；转化、频次、客单价这类过程关系常用乘法。

有效 KPI 要同时满足四件事：和 KGI 有因果关系、责任人可影响、有可得数据、不会诱发反向激励。树拆完以后，不是平均用力，而是看哪一段最能解释缺口，给 KPI 排优先级。

这个 skill 的输出是一张“指标因果树 + 无效指标清单 + 下一轮验证顺序”，不是一组漂亮但没人负责的数字。

## A1 — 资料中的应用 (Past Application)

### 示例 1: 店铺销售额 KPI 树

- **问题**: 目标是提高店铺销售额，但不知道该先看客流、购买率还是客单价。
- **方法论的使用**: PPT 将销售额拆成来店顾客人数、购买率、客单价，并进一步区分回头客人数和新顾客人数。
- **结论**: 如果销售额没有达成，可以沿树验证是购买率、客单价、来店人数或回头客结构出了问题。
- **结果**: 管理动作从“努力提高销售额”变成“定位哪一个 KPI 节点解释了 KGI 缺口”。

### 示例 2: 会员人数和客单价目标

- **问题**: 资料示例中同时出现会员人数增加、销售额达到 1 亿日元、客单价提高 30% 等目标。
- **方法论的使用**: 将不同 KGI 放在树顶，分别拆出对应过程指标，而不是把所有数字混成一张目标表。
- **结论**: 每个 KGI 都需要自己的 KPI 因果链，且每个指标都要对达成 KGI 有效果。
- **结果**: 目标检查能从“达成/没达成”推进到“哪条过程链需要修正”。

## A2 — 触发场景 (Future Trigger)

### 用户会在什么情境下需要这个 skill?

1. 已经有一个业务结果目标，例如销售额、转化率、会员数、交付时长、缺陷率，但不知道该拆哪些 KPI。
2. 团队列了一堆指标，却说不清哪些指标真的影响最终结果。
3. 目标没达成，用户想定位到底是客流、转化、客单价、复购、效率、质量还是供给出了问题。
4. 用户担心某些指标只是虚荣指标、不可控指标或会诱发坏行为。

### 语言信号

- “帮我拆一下 KPI 树 / KGI-KPI”
- “这个指标和最终目标有因果吗？”
- “为什么目标没达成，应该看哪个指标？”
- “metric tree / causal KPI / metric decomposition”

### 与相邻 skill 的区分

- 与 `okr-fit-preflight` 的区别: 先用它判断当前工作适不适合 KPI 化；本 skill 只在已有明确 KGI 且业务相对稳定时拆指标树。
- 与 `okr-smart-kr-quality-guard` 的区别: 目标/KR 写得像口号或待办时转它；本 skill 关注指标之间的因果公式和解释力。
- 与 `strategy-model-evidence-gate-router` 的区别: 战略问题还没确定战场或模型时转战略路由；本 skill 只处理已选定业务结果的指标拆解。
- 与 `six-s-site-order-governance-loop` 的区别: 现场 6S 可用本 skill 设目标和过程监控，但现场治理流程由 6S skill 承接。

## E — 可执行步骤 (Execution)

1. **确认 KGI 和业务类型**
   - 完成标准: 写出一个最终结果、时间周期、口径和责任边界。
   - 判停条件: 如果目标属于 0-1 探索、没有稳定过程、没有数据口径，停止 KPI 树，转 OKR/实验或取证计划。

2. **拆出一阶因果公式**
   - 完成标准: 用加法或乘法写出 2-5 个能解释 KGI 的一阶 KPI。
   - 判停条件: 如果只是罗列部门指标，不能解释 KGI 变化，退回重拆。

3. **继续拆到可行动层**
   - 完成标准: 每个关键 KPI 至少能对应一个可观察过程、责任人、数据来源和可调整动作。

4. **检查 KPI 有效性**
   - 完成标准: 对每个 KPI 标注因果强度、可控性、数据可得性、滞后性、反向激励风险。
   - 判停条件: 指标不可控、无数据、只代表忙碌或会诱发坏行为时，列入无效/危险指标清单。

5. **排序并设验证节奏**
   - 完成标准: 选出最可能解释 KGI 缺口的 1-3 个 KPI，写出本周验证动作、复盘时间和判断阈值。

## B — 边界 (Boundary)

### 不要在以下情况使用此 skill

- 用户只是想把目标写得更具体、更可衡量，应转 `okr-smart-kr-quality-guard`。
- 用户不确定应该用 OKR、KPI、PDCA 还是任务管理，应先转 `okr-fit-preflight`。
- 用户在做新产品、新内容方向、创业早期定位等 0-1 探索，不能过早 KPI 化。
- 用户想分析行业、市场、竞争或战略方向，应转 `strategy-model-evidence-gate-router`。

### 资料中的失败模式提示

- PPT 明确提示要“确认 KPI 指标是否有效”；无效指标会让团队优化数字而不是优化结果。
- PPT 的正确/错误目标示例提醒：模糊目标不能进入指标树，否则后续拆解只是伪精确。

### 作者的盲点 / 资料局限

- PPT 是模型培训材料，案例较短，没有提供真实组织中 KPI 失真的长案例。
- 对数据治理、统计显著性、归因偏差和隐私合规没有展开；实际使用时必须另行核验数据来源和权限。

### 容易混淆的邻近方法论

- KPI 树不是 OKR；KPI 树适合稳定业务的结果解释和过程控制，OKR 更适合探索性方向和跨团队对齐。
- KPI 树不是战略模型；它不能回答该进入哪个市场、选择哪种竞争战略。

## 相关 skills

- depends-on: `okr-fit-preflight`。先判断工作是否适合 KPI 化，再拆指标树。
- contrasts-with: `okr-smart-kr-quality-guard`。目标措辞质量归 OKR/SMART 护栏，指标因果结构归本 skill。
- contrasts-with: `strategy-model-evidence-gate-router`。战略模型选择在前，指标树在目标已清楚后使用。
- composes-with: `six-s-site-order-governance-loop`。6S 推进中的目标管理可用 KPI 树设过程监控。

## 审计信息

- **验证通过**: V1 ✓ / V2 ✓ / V3 ✓
- **测试状态**: 6/6 独立盲测通过
- **蒸馏时间**: 2026-07-20
