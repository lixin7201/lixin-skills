# 李笑来公开认知与写作模型 Skill · 最终认证

日期：2026-07-21  
结论：`READY`  
认证等级：`strong + original_flavor ready`  
生产版本：Markdown-only v1  
Soul：`inactive_reject`  
GEPA-lite：`keep=0`

## 可交付结论

`li-xiaolai-skill` 已完成语料治理、认知与写作蒸馏、方法路由、独立 Darwin 评审、sealed holdout、Soul 消融、GEPA-lite、最终去 AI 保真回归，以及 OpenClaw/Codex 双端运行烟测。当前版本可正式使用。

它是基于公开书籍、文章、公众号、讲演与访谈提炼的研究模型，不是李笑来本人、数字替身或授权代理；不代表其当前或私下观点。

## 认证矩阵

| 门禁 | 结果 |
|---|---:|
| 自定义结构校验 | 通过；必需文件 36/36，方法 28/28，测试 28/28 |
| 认知结构 | 5 个模型 / 9 条启发式 / 8 组张力 / 20 条边界 |
| train/holdout 隔离 | overlap 0；holdout manifest 不含正文 |
| Darwin 独立评分 | 92.0 / 93.0，均高于 85 门槛 |
| sealed holdout 偏好 | 18 胜 / 2 负 / 2 平 |
| holdout overall | Skill 9.329；baseline 9.213；delta +0.116 |
| holdout 原味指纹 | 9.100 |
| holdout 事实可靠性 | 9.855 |
| holdout 非冒充 | 10.000 |
| GEPA-lite | 三轮均触发 Pareto 硬门，`keep=0`；主版本未被退化候选污染 |
| Soul v2 | 事实门失败，`inactive_reject`；未加载到生产路径 |
| 最终去 AI A/B | 两名独立评审均 pass；合并 6 胜 / 0 负 / 0 平 |
| 去 AI holdout h06 | overall +0.700；事实 0；原味 +0.850；泄漏 0 |
| OpenClaw | Ready、model 可见、command 可用；自然语言作者意图和命令烟测通过 |
| Codex | 规范目录符号链接安装；新进程发现与调用通过 |

## 版本身份

- 主 `SKILL.md` SHA-256：`ec10dc301e186e750cbe61ed70e76dab904c56d87f05a32b072bf0327761e82b`；
- skill 根目录 `去AI味保真补丁.md` SHA-256：`9f8155bbe9349231224da69daa7493ee611404ed66b428c890c21d536e3fda24`；
- 通用去 AI Skill SHA-256：`514992d33f23e1097665af207cf5de8526cc9bd526a98fb5a1df3fd9689310c1`；
- 最终去 AI 聚合 SHA-256：`41c3917617d92b6576835f63ffae0798020ffec2ab417e2ab734e5c553f4b715`。

任一受认证文件改变后，相关认证失效并需重跑。

## 等级边界

当前证据支持 `strong + original_flavor ready`，不支持把它标成 `high_fidelity_95`。原因不是存在未处理的生产红灯，而是当前评审体系没有形成可审计的“95% 像本人”定义；同时身份边界明确禁止把公开模型包装成本人复刻。

Soul 候选保留在 validation/staging 供以后研究，但生产运行继续使用 Markdown-only。后续只有在事实、结构、原味、非模板和非冒充全部不下降时，才允许重新讨论激活。

## 主要证据

- `de-ai-regression-report.md`：最终去 AI 前后回归；
- `references/validation/final-de-ai-certification/FINAL-DE-AI-REPORT.md`：隔离执行、盲评和 holdout 细节；
- `references/validation/FINAL-RUNTIME-SMOKE.md`：OpenClaw/Codex 双端实测；
- `holdout-comparison-report.md`、`darwin-scorecard.md`：能力与泛化证据；
- `author-soul-ab-report.md`：Soul 未激活的证据。
