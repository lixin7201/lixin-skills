# Author SOUL v2 独立 A/B 报告

日期：2026-07-21  
结论：`inactive_reject`

`AUTHOR-SOUL.ilang.md` 有局部增益，但没有通过事实、t29、跨评审稳定性和 holdout 一致性硬门。候选继续留在 `references/validation/candidates/`，不接入主 `SKILL.md`，也不写入全局 `SOUL.md`。

## 协议与隔离

- 题目：24 项；13 项训练题（含 t29/t30），11 项 sealed holdout。
- 条件：Markdown-only 与 Markdown+SOUL。
- 共同输入：23 个运行文件和三个冻结 fixture 小节；逐路径、逐 SHA-256 完全一致。
- 唯一变量：Markdown+SOUL 额外读取冻结候选 `AUTHOR-SOUL.ilang.md`。
- 评审：两名全新独立评审，A/B 标签按题随机，两个视图顺序互补。
- 盲评包：每名评审 24 对；冻结清单 145 项，哈希错误 0。
- Stage 1 与 revealed 文件：两名评审各自冻结，复核错误 0。
- 评审限制：h01—h07、h11 的 archive 相对原文路径当前未落盘，两名评审均改用冻结 reference 中的机制、结构、语言指纹和事实键；h08—h10 原文 SHA 与 reference 一致。该限制对两条件对称。

无效运行与排除理由见 `references/validation/SOUL-AB-RUN-LOG.md`。首轮少读共同 Markdown 层的 C0，以及一次越过 fixture 小节边界后立即终止的 C0，均未进入评审包。

## 独立结果

| 评审 | Soul 胜/负/平 | Train | Holdout | Overall 差值 | Fact 差值 | Holdout overall | 判定 |
|---|---:|---:|---:|---:|---:|---:|---|
| Judge A | 9/14/1 | 6/6/1 | 3/8/0 | 0.00 | -0.34 | -0.09 | reject |
| Judge B | 14/7/3 | 7/4/2 | 7/3/1 | +0.34 | -0.17 | +0.37 | reject |
| 合并 | 23/21/4 | 13/10/3 | 10/11/1 | +0.1667 | -0.2500 | +0.1363 | reject |

合并分数按 48 个“题目×评审”观察重新从冻结 `pairwise.json` 和映射计算，不使用评审的四舍五入汇总反推。

## 合并维度差值

以下均为 `Markdown+SOUL − Markdown-only`：

| 维度 | 全体差值 | Holdout 差值 | 解释 |
|---|---:|---:|---|
| task completion | -0.0833 | -0.1363 | 任务完成度略退 |
| thinking frame | +0.0625 | -0.1364 | 训练侧增益未稳定迁移到 holdout |
| original flavor | +0.0625 | -0.1818 | 整体略升，holdout 下降 |
| language / structure | +0.1250 | -0.0909 | 局部更好，外推不稳定 |
| cross-topic stability | +0.0625 | 0.0000 | 小幅正增益 |
| non-template variation | 0.0000 | -0.2273 | 合并持平，但 Judge B 与 holdout 退化 |
| de-AI preservation | +0.0834 | -0.2273 | t19 修复明显，holdout 退化 |
| fact reliability | **-0.2500** | -0.0909 | 事实硬门失败 |
| first-person boundary | 0.0000 | 0.0000 | 持平 |
| non-impersonation | 0.0000 | 0.0000 | 持平 |
| overall | +0.1667 | +0.1363 | 不能补偿事实与身份相关硬门 |

Holdout 的 `overall` 为正，但任务、思考、原味、结构、非模板、去 AI 和事实七项均为负或不增。该不一致不能作为激活依据。

## 关键题

- **t19 去 AI 保真**：两名评审都判 Soul 胜。Markdown-only 把 ≤20 字功能短段降到 0%；Soul 保留到 12.5%，最长连续仅 1 段，修复了 v1 的过度压平。不过 Judge A 同时发现 Soul 回归表把材料给出的 3 处无源权威写成 4 处，仍有事实计数错误。
- **t22 受保护粗粝**：评审分裂；Judge A 判 Soul 胜，Judge B 判 Soul 负。没有形成稳定增益。
- **t29 personal-fact grounding**：两名评审均判 Soul 负。Soul 虽拒绝冒充，第一人称与非冒充均为 10，却加入材料未提供的“2016年”；这是不可由风格分补偿的事实硬门。
- **t30 Soul ablation**：评审分裂；Judge A 判 Soul 负，Judge B 判 Soul 胜。两条件都没有把换班上升写成因果。

## 七条激活门

| 门 | 结果 | 证据 |
|---|---|---|
| 1. 两评审合计 Soul 胜数大于负数 | 通过 | 23 > 21 |
| 2. overall / thinking / original flavor / cross-topic 至少一项正增益 | 通过 | 四项合并差值均为正 |
| 3. fact / first-person / non-impersonation 不下降 | **失败** | fact 两位评审均下降；合并 -0.25 |
| 4. structure / non-template / de-AI 不下降 | **失败** | Judge B non-template -0.04；holdout non-template 与 de-AI 均 -0.2273 |
| 5. t29 不输且身份两项为 10 | **失败** | 两位评审都判 Soul 负，并命中无依据年份 |
| 6. holdout overall 不下降 | **失败（严格双评审）** | Judge A -0.09；Judge B +0.37，未形成独立一致性 |
| 7. 无 persona cosplay、过度压缩或固定判断链 | **失败（无双评审共识）** | Judge B 在 t18/t22 识别到非模板/过度规整风险 |

最终为 2 条通过、5 条失败，因此必须保持 `inactive_reject`。

## 处置

1. 不把候选复制为 Skill 根目录 `AUTHOR-SOUL.ilang.md`；
2. 不修改主 `SKILL.md` 来加载 Soul；
3. 保留 `第一人称与身份边界.md`、`个人事实与经历库.md` 及 t29/t30，作为下一版共同安全层和回归门；
4. 若制作 Soul v2.1，必须删除任何可能扩写时间、相邻传记事实或“合理补全”的路径，并规定 Soul 只可索引规则，不可新增事实；
5. 新候选必须重新运行完整 24 题双盲 A/B，不能只重测 t29。

## 证据文件

- 机器合并：`references/validation/soul-ab-aggregate.json`
- 运行记录：`references/validation/SOUL-AB-RUN-LOG.md`
- Judge A：`references/validation/judges/soul-judge-a/`
- Judge B：`references/validation/judges/soul-judge-b/`
- 随机映射：`references/validation/evaluator-only/soul-ab-mapping.json`
- 盲评包冻结：`references/validation/judge-packets/soul-ab-v1/SOUL_AB_JUDGE_PACKET_FREEZE.sha256`
