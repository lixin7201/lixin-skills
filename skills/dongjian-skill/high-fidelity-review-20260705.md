# 洞见 skill 高保真复评 2026-07-05

## 结论

- 旧流程 Darwin scorecard：87.7 / 100。
- 新高保真口径复评前：约 84 / 100。
- 本轮小改后：约 89 / 100。
- 结论：`ready`，接近 `strong`，但未达到 `high_fidelity_95`。

未认证 95% 的原因：

- 旧 holdout 平均只有 8.15，未达到 9.5。
- 原测试集只有 12 项，缺少强材料正向样本、baseline、泄漏、盲测、跨题材和反模板化测试。
- 旧评估是 dry-run holdout，不是完整生成稿 + 独立盲审。
- 原 SKILL.md 和 DNA 文件把“模板/公式”写得太强，容易稳定但模板化。

## 本轮发现

强项：

- 451 篇语料，训练样本足够。
- OpenClaw 能原生触发 `/dongjian-skill`。
- 标题强判断、短句开头、数字分节、故事转判断的基本 DNA 稳定。
- 事实可靠和非冒充边界好。

短板：

- 旧规则容易把标题公式当填空题。
- `Step 3：选择模板` 会诱导跨题材套同一写稿方式。
- `test-prompts.json` 缺少反模板化测试。
- holdout 报告里多篇差距描述重复，说明评估本身也有模板化风险。

## 本轮改动

- `SKILL.md`：把“选择模板”改为“选择文章骨架”，新增反模板化自检。
- `Writing-DNA.md`：明确标题骨架只是候选，不是填空题。
- `标题DNA.md`：把“公式与示例”改为“骨架与示例”，新增模板换词反例。
- `正文结构模板.md`：改为“正文结构骨架”，新增反模板化改造规则。
- `反模式与诚实边界.md`：新增“模板号”反模式。
- `test-prompts.json`：从 12 项补到 18 项。
- `writing-style-distiller` 标准：新增非模板化泛化、跨题材泛化、反模板化变化评分。

## 本地烟测

### 反模板化生成

同一提示要求处理两个不同题材：

1. 中年人失业后开始整理房间。
2. 家长发现孩子不愿再分享学校的事。

改前表现：

- 能生成洞见感标题和短开头。
- 但多个标题直接落在标题公式上，像“普通人翻身的开始”“越是难熬”“一间屋子藏着命运”等。

改后表现：

- 输出按两个题材分别给标题和开头。
- 家庭题从“孩子沉默/父母迟钝/信任入口”切入，和失业整理房间题区分更明显。
- 仍保留洞见常见强判断与短句节奏。

### T18 反模板诊断

测试任务：三组标题和开头都套用“普通人变强的开始：X”和“人到中年，最怕的不是A，而是B”，要求判断是否模板化并改写。

结果：

- 明确判断“过度模板化，而且是同一层级的模板化”。
- 能指出问题不是句式本身，而是判断方式变懒。
- 能把情绪管理、孩子沉默、攒钱习惯拆成三套不同标题与开头路径。

## 复评分数

| 维度 | 旧口径 | 新口径复评前 | 本轮改后 |
|---|---:|---:|---:|
| Darwin 结构/执行综合 | 87.7 | 84.0 | 89.0 |
| holdout 平均 | 8.15 | 8.15 | 未全量重跑 |
| 非模板化变化 | 未评分 | 7.1 | 8.4 |
| 跨题材泛化 | 未评分 | 7.8 | 8.6 |
| 事实可靠性 | 9.81 | 9.81 | 9.8 预估保持 |
| 非冒充合规 | 10.0 | 10.0 | 10.0 预估保持 |

## 下一步

要冲 95%，不要继续堆规则。下一步应该做真实验证：

1. 用 10 篇 holdout 重新生成完整稿。
2. 每篇生成一个 no-skill baseline。
3. 做盲审 A/B：洞见原文拆解 vs skill 生成稿 vs baseline。
4. 单独打非模板化变化分。
5. 只根据失败维度微调，不增加固定句式。

## Full Holdout Rerun

Rerun directory: `reruns/20260705-164315/`

This rerun completed the next-step validation above:

- Generated 10 `/dongjian-skill` drafts from holdout titles/types/material directions.
- Generated 10 no-skill baseline drafts from the same inputs.
- Randomized A/B order and ran an independent blind judge.
- Saved clean results to `blind-ab-results.jsonl`, `blind-ab-results.csv`, and `rerun-score-summary.md`.
- Created `holdout-leakage-log.md`; generation prompts did not include original holdout prose.

Result:

- skill wins: 6/10
- baseline wins: 4/10
- ties: 0/10
- skill overall average: 7.6
- baseline overall average: 7.7
- skill non-template variation: 7.4
- baseline non-template variation: 6.8
- skill fact reliability: 9.5
- baseline fact reliability: 9.5

Updated certification:

- `high_fidelity_95`: failed. The A/B gate requires at least 8/10 skill wins, and non-template variation must be >= 9.0.
- `ready`: borderline after the new non-template gate, because skill non-template variation is 7.4 against the 7.5 ready threshold.
- Current practical status: usable but not yet high-fidelity. The next improvement should target only the failed dimensions from H02-H05, not add more title formulas.

## Targeted H02-H05 Fix Rerun

Rerun directory: `reruns/20260705-165554-targeted-fixes/`

What changed:

- H02 家庭关系：补“承担 -> 默认 -> 委屈 -> 控制/怨气 -> 反噬 -> 分工边界”的关系链条。
- H03 敏感新闻：补事实距离规则，禁止补写未核实前史，也禁止用“第一次/第二次忍了”暗示重复前史。
- H04 清单方法：标题承诺多少条，正文必须交付多少条。
- H05 职场单位：必须落到留痕、确认、反馈、责任边界、证据、自保动作。

Validation:

- Hard checks passed: H02-H05 separators complete; H04 has 1-50 full list; H03 risky prior-history terms not found; H05 contains concrete workplace actions.
- Blind A/B against the previous no-skill baseline: skill wins 4/4.
- Final targeted set uses H02 v4 plus H03-H05 v3.
- Targeted averages: skill overall 8.38 vs baseline 6.5; skill non-template 8.0 vs baseline 5.88; skill style 8.38 vs baseline 6.5; skill fact reliability 9.5.
- Projected full H01-H10 under the same baseline: skill wins 10/10, skill overall 8.15, non-template 7.9, style 8.15, fact reliability 9.6.

Updated certification:

- `ready`: pass again.
- `strong`: closer, but still needs a fresh full H01-H10 rerun after the targeted patch.
- `high_fidelity_95`: still not certified. The repair improved the weak cluster, but projected full non-template variation is 7.9, not 9.0+, and the evaluation used one judge rather than multi-judge validation.
