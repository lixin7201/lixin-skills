# 大土豆 Skill 完整 Blind A/B 测试协议

运行时间：2026-07-09
范围：8 个冻结 holdout + t20-t22 原味专项，共 11 个比较项。

## 隔离规则

- with_skill：使用 main agent + `/datudou-skill`。
- baseline：使用 test agent；该 agent 无 `datudou-skill`，同题生成无 skill 基线。
- judge：使用 test / pm / dev 三个 agent；这些 agent 均未安装 `datudou-skill`。
- 生成和评审都不读取 `holdout/originals/` 正文，只使用冻结 prompt、标题、类型和原味评分卡。
- A/B 标签用固定随机种子 `20260709` 打乱，judge 看不到来源。

## 判定规则

- 每个 judge 对每项选择 A/B/tie。
- 汇总 item-majority：每项三票多数胜出。
- 原味 gate：skill item-majority 胜率 >= 80%，同时记录 vote-level 胜率。
- 如果失败，只针对弱项补最小规则，不重新打开全 skill。
