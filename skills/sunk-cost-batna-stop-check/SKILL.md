---
name: sunk-cost-batna-stop-check
description: |
  用户谈判已经投入很多时间、面子、费用或内部沟通，当前协议却差于替代方案，纠结是否继续成交时调用。Trigger: "都谈这么久了/不想白费/B计划/低于底线/要不要停止谈判", sunk cost BATNA。不用于投资持仓、普通项目复盘或没有定义B计划的早期谈判。
source_book: 《麦肯锡精英的谈判策略》 高杉尚孝
source_chapter: 第三章；提取文本行 6650-6672
tags: [negotiation, sunk-cost, stop-condition]
related_skills:
  - slug: constructive-negotiation-preflight
    relation: depends-on
  - slug: active-choice-passive-hold-protocol
    relation: contrasts-with
---

# 沉没成本-B计划停止检查

## R — 原文 (Reading)

> "如果结果差于谈判破裂时的替代方案，那么就应该斩钉截铁地中断谈判。"
>
> — 高杉尚孝，第三章

## I — 方法论骨架 (Interpretation)

谈判投入越多，越容易把过去努力当成继续谈的理由。  
这个方法要求把已经花掉的时间、费用、面子和内部协调归零，只比较两个未来: 当前协议 vs 谈崩后的 B 计划。  
如果当前协议低于 B 计划，继续成交不是善始善终，而是在沉没成本绑架下接受坏结果。  
停止谈判可以是理性动作，不是失败。

## A1 — 书中的应用 (Past Application)

### 案例 1: 谈判投入过多后想让它善终
- **问题**: 谈得越久，越不想承认过去劳动白费。
- **方法论的使用**: 作者把沉没成本引入谈判，要求彻底忘掉过去投入。
- **结论**: 达成协议不是目的，协议必须优于 B 计划。
- **结果**: 若结果差于谈判破裂替代方案，就应停止或升级。

## A2 — 触发场景 (Future Trigger)

### 用户会在什么情境下需要这个 skill?

1. 与供应商、客户、合作方谈了很久，条件越来越差。
2. 因为已经投入大量时间、面子或内部资源，不愿停止。
3. 当前协议低于最初底线或换方案的收益。
4. 担心别人评价"谈崩了"而继续让步。

### 语言信号

- "都谈这么久了，要不要算了?"
- "不想让前面努力白费"
- "当前条件比换一家还差"
- "sunk cost / BATNA stop"

### 与相邻 skill 的区分

- `constructive-negotiation-preflight` 在谈判前定义 B 计划；本 skill 用它做停止判定。
- `active-choice-passive-hold-protocol` 处理投资/持有决策；本 skill 只处理谈判协议 vs B 计划。
- `whole-action-chain-validity-audit` 查完整策略链，本 skill 是谈判停止点。

## E — 可执行步骤 (Execution)

1. **冻结过去投入**
   - 列出已投入时间、费用、面子和内部成本，并标记为不可回收。
   - 完成标准: 这些成本不再参与继续/停止评分。

2. **比较两个未来**
   - 当前协议未来收益/风险/成本 vs B 计划未来收益/风险/成本。
   - 判停条件: 若当前协议低于 B 计划且无可谈改善，停止或升级。
   - 完成标准: 只有未来差额，不使用"都谈这么久了"作为理由。

3. **执行停止或重设条件**
   - 若停止，写明感谢、原因、保留关系和后续边界；若继续，列不可让步条件。
   - 完成标准: 发出清晰下一步，不再拖延。

## B — 边界 (Boundary)

### 不要在以下情况使用此 skill

- 早期谈判尚未定义 B 计划，先做谈判预案。
- 投资持仓、创业项目 sunk cost 或情感关系，不直接套用本谈判 Skill。
- 涉及法律纠纷、合同违约或高金额损失时，先咨询专业人士。

### 作者在书中警告的失败模式

- 因投入大量时间、面子或费用，不愿承认谈判不值得继续。

### 作者的盲点 / 时代局限

- 原书未充分展开合同违约、长期报复和组织政治后果；停止谈判前需评估外部约束。
- B 计划质量若虚高，停止判断会失真。

### 容易混淆的邻近方法论

- 停止不是情绪性退出，而是当前协议低于 B 计划。
- 沉没成本检查不否定关系维护；可以礼貌停止。

## 相关 skills

- depends-on: `constructive-negotiation-preflight` 没有 B 计划就无法判定低于替代方案。
- contrasts-with: `active-choice-passive-hold-protocol` 投资持有类决策使用另一套协议。

## 审计信息

- **验证通过**: V1 ✓ / V2 ✓ / V3 ✓
- **测试通过率**: 100% (6/6，独立盲测；详见 test-prompts.json 和 test-results.md)
- **蒸馏时间**: 2026-07-20
