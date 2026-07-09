# Darwin Scorecard

评估日期：2026-07-05  
模式：dry_run（当前环境没有独立 judge 子 agent；未声称 full_test）

## 9 维评分

| 维度 | 权重 | 分数 | 加权 | 说明 |
|---|---:|---:|---:|---|
| Frontmatter 质量 | 7 | 9.0 | 6.3 | name 稳定，description 有触发词和边界 |
| 工作流清晰度 | 12 | 9.0 | 10.8 | 任务路由、素材门、写稿流程完整 |
| 失败模式编码 | 12 | 9.0 | 10.8 | 有失败信号和处理表 |
| 检查点设计 | 6 | 8.0 | 4.8 | 素材不足和高风险事实会降级/停写 |
| 可执行具体性 | 17 | 8.8 | 15.0 | 引用具体 DNA 文件和输出格式 |
| 资源整合度 | 4 | 9.0 | 3.6 | references/data/holdout/test prompts 齐全 |
| 整体架构 | 12 | 8.8 | 10.6 | 主文件短，详细 DNA 外置 |
| 实测表现 | 23 | 8.6 | 19.8 | holdout dry-run 平均 8.15；强素材正控样稿 8.6 |
| 反例与黑名单 | 6 | 9.0 | 5.4 | 有反模式、一票否决、高风险边界 |
| **总分** | **100** |  | **87.1** | 达到 ready 门槛 |

## Ready Gates

| Gate | Result |
|---|---|
| OpenClaw 发现 SKILL.md | PASS，`openclaw skills info kazike-skill` 显示 Ready、Visible to model、Available as command |
| Darwin final score >= 85 | PASS，87.1 dry_run |
| Holdout average >= 8.0 | PASS，8.15 dry_run |
| title/opening/structure/language/material >= 7.5 | PASS，最低 7.8 |
| non-template variation >= 7.5 | PASS，8.0 |
| fact reliability >= 9.5 | PASS，9.6 |
| non-impersonation = 10 | PASS |
| 哪里不像诊断可执行 | PASS，见 `references/像不像判别器.md` |

## 结论

状态：ready。不是 95% 高保真认证；用户未要求 95%，且本轮未跑独立 judge full_test。正控样稿见 `validation/generated-draft-positive-control.md`。
