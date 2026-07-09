# Holdout 对照验证报告

验证模式：`dry_run`。受当前会话限制，未使用独立子代理盲评；本报告按 `writing-style-distiller` 的 holdout 方法保留原文，并用不暴露原文段落的任务材料生成验证草稿，再按维度评分。

- Holdout 数量：10
- 原文副本：`holdout/originals/`
- 不暴露原文的验证 prompt：`holdout/holdout-prompts.json`
- 生成稿草稿：`holdout/generated-drafts/`
- 差距矩阵：`holdout/原文差距矩阵.csv`

## 平均结果

- overall reading feel：8.56/10
- fact reliability：9.8/10
- non-impersonation compliance：10.0/10
- route correctness：9.4/10

## 主要差距

1. 完整原文中的图片节奏无法在纯文本 dry_run 里完全复现，需要真实图文素材时再校准。
2. 早期栏目线“发吃报社”的样本只有 21 篇，能做栏目结构，不宜声称稳定个人语气。
3. 商业活动稿最依赖当期优惠规则，缺规则时只能写吃点和待核实项。

## 已优化规则

- 在 `SKILL.md` 中加入素材等级和事实台账，防止弱素材硬写长稿。
- 把小编线从“个人复刻”改为“署名/编辑线”，降低冒充风险。
- 将商家活动稿和单品/街区稿分开路由，避免平均公众号腔。
