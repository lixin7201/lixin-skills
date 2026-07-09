# OpenClaw Smoke

日期：2026-07-09

## Discoverability

命令：`openclaw skills info datudou-skill --agent main`

结果：

- `datudou-skill ✓ Ready`
- `Visible to model: yes`
- `Available as command: yes`

## Command Smoke

命令：本地运行 `/datudou-skill`，只给一句弱素材选题：“北京中年人越来越不敢消费了”。

结果摘要：

- 正确判断素材不够。
- 没有硬写完整稿。
- 输出需要补充的具体材料：人群、消费场景、金额变化、收入/房贷/孩子/养老现金流。
- OpenClaw run 成功，tool failures = 0。
