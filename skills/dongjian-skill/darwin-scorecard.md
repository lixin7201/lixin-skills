# darwin-scorecard

评分方式：按 darwin-skill 9 维 rubric 做结构评分，并结合 12 个 test-prompts 与 10 篇 holdout dry-run 对比。后续已用 OpenClaw 原生 `darwin-skill` 做外部评分校准。

## 9 维评分

| 维度 | 权重 | 分数 | 加权 |
|---|---:|---:|---:|
| Frontmatter质量 | 7 | 9.0 | 6.3 |
| 工作流清晰度 | 12 | 9.0 | 10.8 |
| 失败模式编码 | 12 | 8.8 | 10.6 |
| 检查点设计 | 6 | 8.5 | 5.1 |
| 可执行具体性 | 17 | 9.0 | 15.3 |
| 资源整合度 | 4 | 9.0 | 3.6 |
| 整体架构 | 12 | 8.8 | 10.6 |
| 实测表现 | 23 | 8.7 | 20.0 |
| 反例与黑名单 | 6 | 9.0 | 5.4 |

## 总分

最终 Darwin 评分：87.7 / 100

## 2026-07-05 高保真复评

按新版 `writing-style-distiller` 口径补入“非模板化变化”和“跨题材泛化”后，旧分数需要降权理解：

- 旧口径：87.7 / 100
- 新口径复评前：约 84 / 100
- 本轮小改后烟测估计：约 89 / 100
- 10 篇 holdout 盲审重跑后：未达到 strong/high-fidelity，见 `reruns/20260705-164315/rerun-score-summary.md`
- 95% 高保真状态：未认证

原因：旧测试集只有 12 项，缺少强材料正向样本、baseline、泄漏、盲测、跨题材和反模板化测试；旧 holdout 平均 8.15，低于 9.5 高保真门槛。

## 2026-07-05 Full Holdout Rerun

本轮真实重跑：

- `/dongjian-skill` 版：10 篇
- no-skill baseline：10 篇
- blind A/B：10 组
- skill wins：6/10
- baseline wins：4/10
- skill overall：7.6
- baseline overall：7.7
- skill non-template variation：7.4
- fact reliability：9.5

结论：未通过 high_fidelity_95；新增 non-template ready gate 也没有稳过线。

## 2026-07-05 Targeted Fix Rerun

针对 Full Holdout Rerun 输掉的 H02-H05 做最小规则修复：家庭关系反噬链条、敏感新闻事实距离、清单数量承诺、职场留痕/确认/反馈/证据。没有新增标题公式或固定句式。

Rerun directory: `reruns/20260705-165554-targeted-fixes/`

- Targeted H02-H05 blind A/B：skill wins 4/4
- Targeted skill overall：8.38
- Targeted skill non-template variation：8.0
- Targeted skill style：8.38
- Targeted skill fact reliability：9.5
- Projected H01-H10 under same baseline：skill wins 10/10
- Projected full skill overall：8.15
- Projected full skill non-template variation：7.9
- Projected full skill style：8.15
- Projected full skill fact reliability：9.6

结论：主要失败簇已修复，`ready` 状态恢复；但这仍不是 `high_fidelity_95` 认证。原因是该结果是“同基线投影 + 单评审盲测”，全量投影非模板化均分仍只有 7.9，距离 9.0/9.5 高保真门槛还有明显差距。

## 内容指标

- holdout 原文对比平均分：8.15
- 标题相似度平均分：8.33
- 开头相似度平均分：8.15
- 正文结构相似度平均分：8.49
- 语言节奏相似度平均分：8.02
- 素材使用相似度平均分：8.13
- 事实可靠性：9.81
- 非冒充合规性：10.0

## 最像维度

标题强判断、数字分节结构、故事转人生判断。

## 最不像维度

真实素材密度和配图承重。Skill 可以给配图占位和素材需求，但不能复刻原文真实图片与新闻细节。

## 2026-07-09 新版原味护栏补丁

- 新增 `references/原味指纹.md`
- 新增 `references/像不像对照样本.md`
- 新增 `references/去AI味保真补丁.md`
- 新增 `data/原味语料分层.md`
- `test-prompts.json` 从 18 条补到 22 条，加入 t19-t22

本轮未修改既有 `Writing-DNA.md`、标题、开头、结构、语言、素材、结尾等 DNA 文件。  
状态更新：`original_flavor assets ready`；既有 full rerun 结论不改，仍不是 95% 高保真认证。
