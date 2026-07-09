# New Standard Upgrade Report

日期：2026-07-09  
对象：`kazike-skill`  
模式：最小保真升级 + targeted validation，不声明 95% 高保真认证。

## 本轮改动

| 项目 | 结果 |
|---|---|
| `references/原味指纹.md` | 已新增 |
| `references/去AI味保真补丁.md` | 已新增 |
| `候选规则优化记录.md` | 已新增 |
| `test-prompts.json` | 18 -> 22，补齐 t19-t22 |
| `SKILL.md` | 已接入原味指纹和去 AI 保真补丁 |
| 核心 DNA 文件 | 未改动 |

## t19 去 AI 保真烟测

命令：`openclaw agent --local --agent main ... '/kazike-skill t19 去AI保真烟测...'`

输入事实：

- 某 AI 浏览器可以总结网页、提取表格、辅助填表。
- 只测试 3 个公开网页。
- 2 个成功，1 个表格错列。
- 未测试账号提交和支付。
- 隐私风险未确认。
- 原稿含“根据你提供的素材、本文将、综上所述、具有广泛应用前景”等 AI 味表达。

输出检查：

| Gate | Result |
|---|---|
| 删除生产链路泄漏 | PASS |
| 删除“本文将/综上所述”类路标句 | PASS |
| 保留 3 个公开网页、2 成功、1 错列 | PASS |
| 保留未测账号提交/支付/隐私风险 | PASS |
| 未新增亲测、截图、价格、产品能力 | PASS |
| 保留卡兹克式短段、口语判断、降温收束 | PASS |

代表输出：

```text
这个 AI 浏览器最有意思的地方，不是“会总结网页”这么简单。

它还能从网页里提表格，甚至辅助填表。

结果是：2 个成功，1 个表格错列。

酷归酷，先别上头。
```

## Targeted Blind A/B

任务：同一 AI 浏览器素材，A 为泛化顺滑版本，B 为 skill/t19 版本；3 个 agent 盲评哪版更像数字生命卡兹克式 AI 公众号写法。

| Judge | Winner | Reason |
|---|---|---|
| dev | B | 短促推进、有判断、有口语化刹车 |
| pm | B | 有节奏、有转折、有口语化判断 |
| test | B | 一句句拆解、降温、有口语判断和收束 |

结果：B 3/3。

## 当前结论

`kazike-skill` 已从旧版 ready 升级到新标准的基础 ready：

- 资产齐全：原味指纹、去 AI 保真、GEPA-lite 候选记录、22 测试。
- OpenClaw 可调用性未破坏。
- t19 去 AI 保真烟测通过。
- targeted A/B 小样本 3/3 胜出。

未声明：

- 未声明 full blind A/B。
- 未声明 high_fidelity_95。
- 未重蒸馏核心 DNA。

后续若要认证 strong/original_flavor，需要跑完整 blind A/B 或至少覆盖 t20-t22 的多 prompt targeted A/B。

