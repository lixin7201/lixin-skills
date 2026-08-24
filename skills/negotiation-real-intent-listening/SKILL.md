---
name: negotiation-real-intent-listening
description: |
  用户在谈判中遇到对方坚持价格、预付款、期限、资源或某个立场，想追问表面要求背后的真实目的、兴趣点、价值观和约束时调用。Trigger: "对方为什么坚持/怎么问真实需求/谈判倾听/real intent", negotiation listening。不用于普通复述确认、心理咨询或对方已明显恶意/违法的场景。
source_book: 《麦肯锡精英的谈判策略》 高杉尚孝
source_chapter: 第一章；提取文本行 4444-4470, 4532-4548
tags: [negotiation, listening, intent]
related_skills:
  - slug: constructive-negotiation-preflight
    relation: composes-with
  - slug: accurate-restatement-feedback-loop
    relation: contrasts-with
---

# 真实意图倾听确认

## R — 原文 (Reading)

> "对方的真正意图深藏于其表面立场和具体要求背后。"
>
> — 高杉尚孝，第一章

## I — 方法论骨架 (Interpretation)

谈判里的条件往往只是表层立场。  
认真倾听不是被动听完，而是从对方的要求中找目的、兴趣点、价值观和约束。  
先复述表面要求，确认你没有听错；再问背后的原因、风险、内部限制和真正想避免的结果。  
当真实意图浮出水面，替代方案才有空间。  
这个方法专用于谈判利益挖掘，不替代一般沟通复述。

## A1 — 书中的应用 (Past Application)

### 案例 1: 山田打断提案
- **问题**: 山田急于否定软件引进，没有充分了解对方提案的好处。
- **方法论的使用**: Good Example 改为听完、确认内容，再追问真实意图。
- **结论**: 打断发言会让谈判者只看到表面要求，错失利益点。
- **结果**: 完整倾听后，双方更可能讨论削减成本和业务改善。

## A2 — 触发场景 (Future Trigger)

### 用户会在什么情境下需要这个 skill?

1. 对方坚持某个条件，但用户不知道原因。
2. 谈判卡在价格、期限、付款、范围或资源上。
3. 用户准备反驳，但担心没有听懂真实需求。
4. 想把对方立场转成可交换利益。

### 语言信号

- "对方为什么非要预付款?"
- "怎么问出真实需求?"
- "我只听到对方要降价"
- "real intent / interest behind position"

### 与相邻 skill 的区分

- `accurate-restatement-feedback-loop` 只确保理解准确；本 skill 进一步追问利益、约束和替代方案。
- `constructive-negotiation-preflight` 是谈判前准备；本 skill 常在谈判中或准备访谈时使用。
- `malicious-negotiation-tactic-defuser` 处理恶意战术；本 skill 默认对方仍可合作。

## E — 可执行步骤 (Execution)

1. **复述表面要求**
   - 用中性语言复述对方条件，确认是否听对。
   - 完成标准: 对方确认或修正表面要求。

2. **追问四类真实意图**
   - 目的、担心、内部约束、不可承受风险。
   - 判停条件: 若对方拒绝解释且持续施压/威胁，转战术反制或退出。
   - 完成标准: 至少得到 2 个表面要求背后的利益或约束假设。

3. **把意图转成替代方案**
   - 针对真实关切设计价格、期限、范围、担保、分期、试点或责任分担方案。
   - 完成标准: 每个替代方案都能对应一个真实关切。

## B — 边界 (Boundary)

### 不要在以下情况使用此 skill

- 对方已经使用欺诈、威胁、骚扰、违法或拒绝留痕行为。
- 用户需要的是一般情绪安抚、心理咨询或亲密关系沟通。
- 对方没有谈判权限或真实决策者不在场时，先确认决策链。

### 作者在书中警告的失败模式

- 对方说价格、期限或资源，你只在表面条件上讨价还价。

### 作者的盲点 / 时代局限

- 真实谈判常有法律、财务、组织政治和长期报复风险，不是问清意图就能解决。
- 文化、语言和制度差异可能让"真实意图"不容易直接表达。

### 容易混淆的邻近方法论

- 复述确认是准确听见；真实意图倾听是听见后继续追到利益。
- 倾听不是顺从，听懂后仍可坚持底线。

## 相关 skills

- composes-with: `constructive-negotiation-preflight` 用倾听补全对方关切。
- contrasts-with: `accurate-restatement-feedback-loop` 一般复述确认不自动进入谈判利益设计。

## 审计信息

- **验证通过**: V1 ✓ / V2 ✓ / V3 ✓
- **测试通过率**: 100% (6/6，独立盲测；详见 test-prompts.json 和 test-results.md)
- **蒸馏时间**: 2026-07-20
