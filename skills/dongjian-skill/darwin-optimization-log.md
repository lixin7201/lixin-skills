# darwin-optimization-log

## Round 0：基线

- 生成 SKILL.md 与 15 个参考文件。
- 建立 12 个 test-prompts。
- 建立 10 篇 holdout dry-run 对比。
- 初始问题：SKILL.md 如果只写“洞见风格”，容易被误解为只模仿短句和温度。

## Round 1：结构强化

修改：在 SKILL.md 中加入明确任务类型、事实门、STOP 敏感边界、模板选择和审稿诊断模块。

保留原因：提升失败模式编码、可执行具体性、非冒充合规性。

## Round 2：反模式强化

修改：在 `反模式与诚实边界.md`、`语言DNA.md`、`SKILL.md` 中加入禁用句式、AI 腔替换、素材不足降级规则。

保留原因：减少普通 AI 文和泛泛分析风险。

## Round 3：评估闭环

修改：补齐 holdout 对比矩阵、test-prompts、Darwin scorecard。

保留原因：让最终交付可验证，而不是只给风格报告。

## 停止条件

连续优化后主要短板转为“真实素材密度/配图承重”，这需要更多带图片语义和原文上下文的人工标注，不适合继续靠规则堆叠。

## Native Darwin 调用记录

- 第一次原生 `/darwin-skill` 评估沿用 `agent:main:dongjian-skill-native`，因会话过长触发 CLI compaction，本地 OpenAI key 配置错误导致压缩失败。
- 第二次使用新 session-key `agent:main:dongjian-darwin-eval`，OpenClaw 已将 `dongjian-skill` 注入 skills 列表并执行了 10 次读取工具调用，但 343 秒内没有生成最终 assistant 回复；为避免后台悬挂，手动中断。
- 因此最终分数采用 darwin-skill 文档允许的 dry-run rubric：结构评分 + test-prompts + holdout 矩阵推演。

## Native dongjian-skill 烟测

- 命令形态：OpenClaw `agent --local`，消息以 `/dongjian-skill` 触发。
- 测试任务：把“如何减少职场内耗”改成 5 个洞见风格标题，并写 120 字以内开头。
- 结果：成功返回 5 个强判断标题和一个短句推进开头。
- 结论：`dongjian-skill` 不只是文件存在，已被 OpenClaw 原生 skills 列表注入并可直接触发使用。

## 2026-07-05 反模板化复评

- 新问题：旧 Skill 稳定性较好，但容易把标题公式、正文模板和“故事 -> 判断 -> 行动”链条当填空题。
- 修改：把 `SKILL.md` 中“选择模板”改为“选择文章骨架”，并在 `Writing-DNA.md`、`标题DNA.md`、`正文结构模板.md`、`反模式与诚实边界.md` 中加入反模板化规则。
- 测试集：`test-prompts.json` 从 12 项扩展到 18 项，补入强材料正向样本、baseline、泄漏、盲测、跨题材和反模板化测试。
- 原生烟测：同一请求生成“失业整理房间”和“孩子沉默”两个题材的标题/开头。改后能分开处理生活秩序和亲子信任，不再为每个标题机械配同构开头。
- T18 烟测：能主动判断“普通人变强的开始：X”和“人到中年，最怕的不是A，而是B”三连用属于过度模板化，并给出不同标题骨架和开头路径。
- 复评分：旧口径 87.7；新版高保真口径复评前约 84；本轮改后约 89。未认证 95%，需要完整 holdout 生成 + blind A/B。

## 2026-07-05 Full Holdout Rerun

- Rerun directory: `reruns/20260705-164315/`
- Generation: 10 skill drafts + 10 no-skill baseline drafts.
- Blind A/B: randomized labels, hidden key stored separately.
- Result: skill wins 6/10, baseline wins 4/10, ties 0/10.
- Averages: skill overall 7.6, baseline overall 7.7, skill non-template 7.4, baseline non-template 6.8.
- Gate result: high_fidelity_95 failed; ready is borderline because non-template variation is below 7.5.
- Failure cluster: H02-H05. Fix family-specific material handling and structure variation for family relationship, sensitive news, checklist, and workplace pieces. Do not add new formulaic title patterns.

## 2026-07-05 Targeted Fix Rerun

- Rerun directory: `reruns/20260705-165554-targeted-fixes/`
- Modification strategy: repair failed thinking paths, not title formulas.
- H02 fix: encode family backlash chain from over-responsibility to default obligation, resentment, control, relationship backlash, and redistributed boundaries.
- H03 fix: tighten sensitive-news handling; no unverified prior-history reconstruction and no rhetorical “first/second/third time” sequence that implies hidden facts.
- H04 fix: title count is a reader promise; if the title says 50 items, output exactly 50 items.
- H05 fix: workplace pieces must include concrete self-protection actions: confirmation, feedback, written trace, responsibility boundary, evidence, priority negotiation.
- Hard checks: H04 output contains 1-50; H03 risky prior-history terms absent; H05 action terms present.
- V3 regression check: removing visible meta labels improved publishability but weakened H02's relationship-backlash chain; H02 briefly lost to baseline.
- H02 v4 fix: added double-sided misreading, where the giver sees sacrifice while family feels control/debt, and the family sees normal help while the giver feels unseen.
- Final blind A/B against previous baseline: skill wins 4/4 on H02-H05.
- Final targeted averages: overall 8.38, non-template 8.0, style 8.38.
- Projected full under same baseline: skill wins 10/10, overall 8.15, non-template 7.9.
- Gate result: ready restored; high_fidelity_95 still not certified because this is targeted single-judge validation and projected non-template average remains below 9.0.
