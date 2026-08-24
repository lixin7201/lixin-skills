# OpenClaw 定时任务备份

本目录来自 OpenClaw 当前 SQLite 权威库的只读导出。

- 定时定义：30 个，其中 20 个启用、10 个停用。
- `openclaw-cron/jobs.template.json`：保留名称、启停状态、计划、任务正文、命令和安全限制。
- `earthquake-patrol/`：地震巡逻实际代码。
- `dayibin-auto-publisher/`：自动评论、自动发布、起势监控、公共服务巡逻和发布后复盘共用代码。

公开模板已删除任务 ID、创建时间、运行状态、session key、收件人、账号 ID、密钥和本机数据；本机路径改为 `${HOME}`、`${OPENCLAW_WORKSPACE}` 或 `${OPENCLAW_REPO}`。恢复前必须填写占位符并人工复核，不能直接开启外发、评论或发布。

热点采集、生财扫描、飞书巡检等任务引用的其他本地项目只保留 cron 定义，本目录没有复制这些项目的运行数据或私有知识库。
