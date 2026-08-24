# lixin-skills

李鑫的 OpenClaw 公共 Skill 与自动化镜像。

## 本次同步

- 30 个当前 OpenClaw 定时任务模板，其中 20 个启用、10 个停用。
- 地震巡逻与大宜宾自动评论/发布的可运行源码和测试。
- 153 个近期蒸馏的书籍/课程方法 Skill，来自 48 个来源包。
- 34 个近期写稿、审稿与导师风格 Skill。

## 目录

- `automations/openclaw-cron/jobs.template.json`：脱敏后的定时任务模板，不会自动启用。
- `automations/earthquake-patrol`：地震巡逻源码。
- `automations/dayibin-auto-publisher`：自动评论、自动发布与相关守护任务源码。
- `skills/BOOK_SKILLS.json`：蒸馏书 Skill 清单。
- `skills/WRITING_SKILLS.json`：写稿 Skill 清单。

## 公共安全边界

本次同步不新增账号 ID、API 密钥、个人事实库、原始语料、评测 holdout、运行日志、数据库、浏览器会话或生产配置。定时任务和自动化中的本机路径、投递目标与发布身份均已改为占位符或环境变量；使用前请在自己的环境中配置。
