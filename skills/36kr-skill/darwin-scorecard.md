# Darwin Scorecard

评估对象：`36kr-skill/SKILL.md`
评估方式：Darwin-style dry-run + 静态结构检查 + holdout 口径检查 + structured blind A/B。OpenClaw 原生发现/烟测见 `validation/smoke-test-20260709.md`。

| 维度 | 权重 | 分数 | 加权 |
|---|---:|---:|---:|
| Frontmatter质量 | 7 | 9.0 | 6.3 |
| 工作流清晰度 | 12 | 9.2 | 11.0 |
| 失败模式编码 | 12 | 8.8 | 10.6 |
| 检查点设计 | 6 | 8.2 | 4.9 |
| 可执行具体性 | 17 | 9.1 | 15.5 |
| 资源整合度 | 4 | 9.5 | 3.8 |
| 整体架构 | 12 | 9.0 | 10.8 |
| 实测表现 | 23 | 8.4 | 19.3 |
| 反例与黑名单 | 6 | 9.4 | 5.6 |
| **总分** | **100** |  | **88.9** |

## Ready Gates

- OpenClaw 目录发现：PASS，`36kr-skill ✓ Ready`，`Visible to model: yes`，`Available as command: yes`。
- OpenClaw fleet check：PASS，`eligible=true`，`modelVisible=true`，`commandVisible=true`。
- OpenClaw 命令烟测：PASS，`/36kr-skill` 被 main agent 加载并产出最前线短稿，未编造公司名、价格、客户或集成方。
- Darwin final score >= 85：PASS，88.9 dry_run。
- Holdout average >= 8.0：PASS，8.67/10 dry_run。
- paragraph/structure metric similarity >= 7.5：PASS，见 `data/结构与段落指标.md`。
- original-flavor gates：PASS(dry_run)，见 `references/原味指纹.md` 和 tests t20-t22。
- fact reliability >= 9.5：PASS，9.7 dry_run。
- non-impersonation compliance = 10：PASS。
- “哪里不像”诊断：PASS，见 `references/像不像判别器.md`。
- de-AI preservation：PASS，见 `references/去AI味保真补丁.md`。

状态：`ready(dry_run + OpenClaw smoke)`。它是可直接调用的 36氪写稿 Skill；不是 95% 认证，也不是人工编辑部盲审。
