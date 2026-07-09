# Darwin Scorecard

评估日期：2026-07-09  
模式：结构/holdout 分数为 dry_run；original-flavor blind A/B 已跑 full_test。

## 9 维评分

| 维度 | 权重 | 分数 | 加权 | 说明 |
|---|---:|---:|---:|---|
| Frontmatter 质量 | 7 | 9.0 | 6.3 | name 稳定，description 有触发词、场景和边界 |
| 工作流清晰度 | 12 | 9.0 | 10.8 | 任务类型、素材门、写稿流程清楚 |
| 失败模式编码 | 12 | 8.8 | 10.6 | 有素材不足、事实不清、冒充、AI 味等处理 |
| 检查点设计 | 6 | 8.2 | 4.9 | 高风险事实和弱素材会降级/停写 |
| 可执行具体性 | 17 | 8.8 | 15.0 | DNA 文件、结构指标、输出格式均可执行 |
| 资源整合度 | 4 | 9.0 | 3.6 | references/data/holdout/test prompts 齐全 |
| 整体架构 | 12 | 8.7 | 10.4 | 主入口短，详细规则外置 |
| 实测表现 | 23 | 8.5 | 19.6 | holdout dry-run 平均 8.19，正控样稿可用 |
| 反例与黑名单 | 6 | 9.0 | 5.4 | 有反模式、禁用 AI 腔、非冒充边界 |
| **总分** | **100** |  | **86.6** | 达到 ready 门槛 |

## Ready Gates

| Gate | Result |
|---|---|
| OpenClaw 发现 SKILL.md | PASS，`openclaw skills info datudou-skill --agent main` 显示 Ready、Visible to model、Available as command |
| OpenClaw 实际 smoke | PASS，`/datudou-skill` 弱素材自检正确触发素材不足门；tool failures = 0 |
| Darwin final score >= 85 | PASS，86.6 dry_run |
| Holdout average >= 8.0 | PASS，8.19 dry_run |
| title/opening/structure/language/material >= 7.5 | PASS，最低 7.6 |
| paragraph/structure metric similarity >= 7.5 | PASS，最低 8.1 |
| non-template variation >= 7.5 | PASS，最低 8.0 |
| fact reliability >= 9.5 | PASS，9.56 |
| non-impersonation = 10 | PASS |
| 哪里不像诊断可执行 | PASS，见 `validation/where-not-like-test.md` |
| de-AI preservation check | PASS，见 `validation/de-ai-preservation-test.md` |
| original-flavor dry-run | PASS dry_run，见 `validation/original-flavor-dry-run.md` |
| original-flavor blind A/B | PASS full_test，9/11 item-majority、28/33 vote-level，见 `holdout/blind-ab-20260709/summary.md` |
| blind A/B leakage check | PASS，见 `holdout/blind-ab-20260709/leakage-check.md` |

## 结论

状态：ready；original_flavor blind A/B PASS。  
不是 95% 高保真认证；如果要升级，需要更多完整语料，并针对 t20/t22 弱项做最小补丁后复测。
