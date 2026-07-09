# Darwin Optimization Log

## Baseline

初版问题：

- 容易把“半佛风格”误解成只堆情绪词。
- 缺少素材不足时的拒写路径。
- 缺少非冒充和原文泄漏边界。

## Round 1

改动：

- 在 `SKILL.md` 增加素材门和使用边界。
- 在 `references/像不像判别器.md` 增加 10 维诊断。
- 在 `references/反模式与诚实边界.md` 增加非冒充、非复制、非编造黑名单。

结果：

- dry-run 评分从预估 82.0 提升到 87.2。
- 保留改动。

## Round 2

改动：

- 在 `SKILL.md` 增加 `🔴 CHECKPOINT：先停再写`。
- 增加 6 类失败分支：冒充、弱素材、事实敏感、伪造亲历、情绪空转、原文泄漏。
- 增加完整参考稿、短评、标题、诊断的篇幅/输出目标。
- 新增 `scripts/verify_banfo_skill.py`，写入 `reports/local-smoke-test-2026-07-05.md`。

验证：

- `python3 scripts/verify_banfo_skill.py` 通过。
- test-prompts：18 个。
- holdout prompts：10 个。
- runtime 红灯扫描：0 命中。
- holdout 60 字以上原文泄漏：0 命中。

结果：

- 评分从 87.2 提升到 89.4。
- 保留改动。

## Round 3

触发：

- 用户指出真实出稿 AI 感强、有语病。

诊断：

- 结构可用不等于出稿过关。
- 失败点不是事实，而是抽象名词承重、模板反转句过多、缺少具体物件和现场动作。

改动：

- 重写真实稿件：`/Users/lixin/AI code/openclaw/drafts/wechat/2026-07-05-ai-learning-penalty-banfo-style.md`。
- `references/语言DNA.md` 增加 `AI 腔硬禁区`。
- `references/写稿流程操作手册.md` 增加 `去 AI 腔`。
- `references/像不像判别器.md` 增加 `AI 感专项诊断`。
- `SKILL.md` 增加 `AI 感强/有语病` 任务路由。
- `scripts/verify_banfo_skill.py` 增加反 AI 腔规则存在性检查。
- 新增 `reports/ai-feel-regression-2026-07-05.md`。

验证：

- 新稿 2638 非空白字符，6 节。
- “不是 A，而是 B”：0 命中。
- “真正的问题是”：0 命中。
- `python3 scripts/verify_banfo_skill.py` 通过。
- `openclaw skills info banfo-skill` 显示 ready、visible、available。

## 停止条件

已达到 ready-local-smoke 门槛；继续优化的主要收益需要独立 judge full-test，而不是继续堆文档。
