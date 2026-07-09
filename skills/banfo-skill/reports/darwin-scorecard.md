# Darwin Scorecard

| 维度 | 权重 | 分数 | 说明 |
|---|---:|---:|---|
| Frontmatter质量 | 7 | 9.0 | name 和触发词清晰 |
| 工作流清晰度 | 12 | 9.1 | 素材门、任务路由、写稿步骤、篇幅目标完整 |
| 失败模式编码 | 12 | 9.2 | 素材不足、事实敏感、冒充、泄漏、情绪空转均有分支 |
| 检查点设计 | 6 | 9.2 | 已加入 `🔴 CHECKPOINT`，命中风险先停再写 |
| 可执行具体性 | 17 | 9.1 | 标题、结构、诊断、素材规则、输出长度可直接执行 |
| 资源整合度 | 4 | 9.0 | references/data/reports/test-prompts 均可达 |
| 整体架构 | 12 | 8.8 | SKILL 短，DNA 外置 |
| 实测表现 | 23 | 8.5 | dry-run + local smoke 通过，未做独立 full_test |
| 反例与黑名单 | 6 | 9.2 | 非冒充、非泄漏、非编造边界清楚 |

## 加权总分

89.4 / 100

## 质量标签

`ready-local-smoke`：可直接调用，已通过本地结构、红灯、测试集、holdout 泄漏 smoke；但不是 95% 高保真认证。弱项是独立盲测和图片 OCR。

## 2026-07-09 新版原味护栏补丁

- 新增 `references/原味指纹.md`
- 新增 `references/像不像对照样本.md`
- 新增 `references/去AI味保真补丁.md`
- 新增 `data/原味语料分层.md`
- `test-prompts.json` 从 18 条补到 22 条，加入 t19-t22

本轮未修改既有 `references/Writing-DNA.md`、标题、语言、结构、素材等 DNA 文件。  
状态更新：`original_flavor assets ready`；原 blind A/B 记录仍是 dry_run，未声明 full_test。
