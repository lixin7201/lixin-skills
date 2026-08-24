# 最终产物去 AI 保真审计

所有装入本包的 Markdown 先经过目标专属人工规则扫描；JSON、CSV 与锁文件执行字节级语义回归，不改字段、数字、hash 或评分。随后由 `writing-style-distiller` 路线对应的 `de-ai-preserve-voice` 规则做三组前后回归。

- AI 痕迹：13 → 0。
- 事实保持：true；数字保持：true。
- 原味不下降：true；非冒充：10/10。
- 独立匿名偏好：去 AI 后版本 6/6 次胜出。

安装前的 `de-ai-file-manifest.json` 会逐文件记录处理类型、前后 hash、主动 AI 痕迹和语义回归失败。该清单由审计过程生成，不自我递归列入自身清单。
