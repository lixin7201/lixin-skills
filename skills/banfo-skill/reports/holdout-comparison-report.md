# Holdout Comparison Report

## 结论

本轮是 dry-run 验证：已冻结 10 篇 holdout，未将原文正文写入训练产物；根据标题、类型、测试 prompt 和 Skill 流程做结构化预估，平均分约 8.1/10。

## 通过项

- 标题、开头、结构、素材纪律、非冒充边界均有明确规则。
- Skill 能在素材不足时拒绝硬写。
- Skill 能诊断“哪里不像”，并给具体修法。
- holdout prompts 不包含原文正文。

## 薄弱项

- 未由独立 agent 读取 holdout 原文做盲测；语言节奏分数仍需 full_test。
- 图片内容没有 OCR，视觉风格只完成节奏级分析。
- 风险黑产科普在训练集前 50% 中数量较少，相关输出应更依赖事实门。

## 下一轮 full_test 建议

1. 用独立 agent 读取 holdout 原文，仅用于评分，不回写 DNA。
2. 对每个 holdout 生成同题新稿和 no-skill baseline。
3. 用 `reports/原文差距矩阵.csv` 的 8 个维度重新打分。
