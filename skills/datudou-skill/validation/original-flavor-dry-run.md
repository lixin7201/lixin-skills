# Original-Flavor Dry Run

日期：2026-07-09  
模式：dry_run；独立多人 blind A/B 已在后续 full_test 中完成。

## 新增测试

| ID | 测试 | dry-run 结论 |
|---|---|---|
| t20 | 原味对照：区分 target-like / 泛 AI / 过度润色 / 过拟合 | PASS，已由 `references/像不像对照样本.md` 提供合成对照 |
| t21 | 思考框架迁移：同一素材是否先落到大土豆式判断链 | PASS，`references/原味指纹.md` 已要求入口、账本、北京坐标、自保边界 |
| t22 | 保护瑕疵：恢复有证据的口语、冷感和不圆满结尾 | PASS，已接入 `去AI味保真补丁.md` 和 `原味指纹.md` |

## 原味门槛

| Gate | 结果 | 说明 |
|---|---|---|
| `原味指纹.md` | PASS | 已区分思考、写作、排版、保护项、假像警报、去 AI 豁免 |
| tests 20-22 | PASS dry_run | 已加入 `test-prompts.json`，未跑独立 judge |
| GEPA-lite 记录 | PASS dry_run | 见 `候选规则优化记录.md` |
| t22 live smoke | PASS | 实际调用能把过度润色稿改回现实账本和保守边界，没有硬塞口头词 |
| blind A/B >= 80% | PASS full_test | 9/11 item-majority、28/33 vote-level，见 `holdout/blind-ab-20260709/summary.md` |
| 95% 高保真 | FAIL/不可认证 | 语料 48 篇，低于 80+ 建议线 |

## 结论

状态：`original_flavor blind A/B PASS`。  
可以用于“更原汁原味”的日常写稿；不能对外宣称 95% 复刻。t20/t22 是下一轮最小补丁目标。
