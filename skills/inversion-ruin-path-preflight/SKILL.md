---
name: inversion-ruin-path-preflight
description: |
  当用户准备启动重要项目、创业、迁移、签约或不可逆操作，正面方案很多但担心“一次失败就出局”时调用；信号包括“先想怎么会死”“最坏路径”“pre-mortem/ruin check”。不用于无上限灾难想象、普通小事或取代正式安全评审。
source_book: 《穷查理宝典（珍藏版）（1+2册）》 查理·芒格
source_chapter: 序言；第一讲；第二讲；第三讲
source_text_lines: 96-98, 3060-3068, 3313-3315, 3421
source_sha256: 14248f425d123d3b3e5c7a6a035851c407034b01eeefc5cd4b1ceb217e59a8d3
tags: [inversion, risk, reliability]
related_skills:
  - slug: circle-of-competence-boundary-test
    relation: composes-with
  - slug: multidisciplinary-model-lattice-check
    relation: composes-with
  - slug: rare-critical-skill-rehearsal
    relation: composes-with
---

# 逆向毁灭路径预检

## R — 原文 (Reading)

> “如果要明白人生如何得到幸福，查理首先是研究人生如何才能变得痛苦；要研究企业如何做强做大，查理首先研究企业是如何衰败的。”
>
> — 李录序言对芒格方法的概括；提取文本第 96–98 行

## I — 方法论骨架 (Interpretation)

成功路径往往很多，毁灭路径通常更少也更稳定。对高影响行动先反问：哪些事件会造成永久损失、不可逆伤害或让系统失去恢复能力？再沿因果链向前找到可干预节点，把避免事项转成冗余、限额、备份、检查和取消门。只有剩余风险在授权和承受范围内，才进入收益优化。逆向不是悲观，而是把生存和恢复力排在效率之前。

## A1 — 书中的应用 (Past Application)

### 案例：主动清理通用再保险衍生品账本

- **问题**：复杂衍生品合同账面利润可观，但义务期限长、交易对手和会计风险难以可靠计量。
- **方法论的使用**：伯克希尔没有继续优化表面收益，而是先问这些头寸怎样导致无法控制的损失。
- **结论**：不可理解、难退出和可累积的尾部风险必须先被切除。
- **结果**：公司承担清算成本，换回了更可控的风险结构；这不是对所有衍生工具的统一结论。

## A2 — 触发场景 (Future Trigger)

1. 一次错误可能导致资金、数据、信誉、合规或人身安全的永久损失。
2. 用户只列成功理由，却未写失败链、备份和取消条件。
3. 项目含杠杆、不可逆迁移、单点故障或支持能力上限。

语言信号：“这事怎么会把我们搞死”“先做最坏路径”“pre-mortem”“有没有一次出局风险”。

与相邻 Skill 的区分：本 Skill 优先阻断不可逆失败；`multidisciplinary-model-lattice-check` 做全景解释；`circle-of-competence-boundary-test` 判断理解资格；`rare-critical-skill-rehearsal` 负责把应急动作练到能执行。

## E — 可执行步骤 (Execution)

1. **定义毁灭**：列 3–7 个会造成永久损失、违法、不可恢复中断或信任破产的结果。
   - 完成标准：每项含影响对象、严重度和不可逆原因。
2. **反推失败链**：从每个毁灭结果向前写触发、放大器和最早预警。
   - 完成标准：至少找到一个可干预节点；删除纯想象且无机制的灾难。
3. **安装控制**：为高风险链设置限额、冗余、备份、双人核验、分阶段试验和取消门。
   - 判停条件：无可靠控制、无恢复方案、损失超授权或风险无法估计时停止行动。
4. **确认剩余风险**：明确谁接受、谁监控、何时复查以及触发退出的阈值。
   - 完成标准：每条高风险链有责任人、预警和停止条件。
5. **复盘**：事后比较预判链与真实近失事件，记录漏项、误报和控制失效；只更新有证据的检查项。

## B — 边界 (Boundary)

- 不把所有可能性都当成必须控制的风险；低后果、可逆选择用最小试验即可。
- 失败模式：用“安全”拖延一切，或写极长清单却没有阈值和责任人。
- 盲点：书中的投资、工程类比不能直接替代行业安全标准和专业评审。
- 若核心问题只是理解范围不足，应先停止并调用能力圈测试，而不是用更多反例掩盖无知。

## 相关 Skills

- composes-with: `circle-of-competence-boundary-test` — 不理解的风险不能靠逆向清单假装可控。
- composes-with: `multidisciplinary-model-lattice-check` — 用多个机制补全失败链。
- composes-with: `rare-critical-skill-rehearsal` — 对已识别的高后果应急动作做周期模拟。

## 审计信息

- 验证通过：V1 ✓ / V2 ✓ / V3 ✓
- 测试通过率：100%（6/6；独立 sub-agent 盲测）
- 蒸馏时间：2026-07-21
