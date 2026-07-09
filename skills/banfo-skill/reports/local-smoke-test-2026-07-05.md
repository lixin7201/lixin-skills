# Local Smoke Test

- 日期：2026-07-05
- 模式：local deterministic smoke
- 结论：通过

## 检查项

| 项目 | 结果 |
|---|---|
| 必备文件 | 10 个存在 |
| test-prompts | 18 个 |
| holdout prompts | 10 个 |
| 🔴 CHECKPOINT | 存在 |
| 弱素材拒写分支 | 存在 |
| 当前事实敏感分支 | 存在 |
| 完整参考稿篇幅目标 | 存在 |
| runtime 红灯扫描 | 0 命中 |
| holdout 60 字以上原文泄漏 | 0 命中 |

## 说明

这不是独立 agent blind A/B；它验证的是 skill 包结构、失败分支、非冒充边界、holdout 泄漏和测试集完整性。继续冲高保真时，再补独立 judge full-test。
