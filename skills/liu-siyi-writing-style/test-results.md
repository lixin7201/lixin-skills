# 测试结果

- 24 题行为测试：24/24 PASS。
- 初轮冻结 holdout：10 个完整 H1/H2 样本，91.1/100，20 胜/4 平/0 负，连续 40 字泄漏 0。
- 分离式盲测：10 个非 holdout 事实包；处理组 10 胜/0 平/0 负，94.3/100；基线 87.9/100。
- 去 AI 八维回归：事实、方法、立场、张力、问题链、声纹、安全、时效全部 PASS。
- 非冒充：10/10；事实保真：10/10；未生成 `AUTHOR-SOUL.ilang.md`，避免把结构迁移升级为人物冒充。

证据：`validation/writing-style-holdout-ab.md`、`validation/style-full-blind-judge1.md`、`validation/style-full-blind-result.md`、`validation/holdout-page-corrections.md`。
