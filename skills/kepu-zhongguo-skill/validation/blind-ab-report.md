# Blind A/B Report

## Packet

- 文件：`validation/blind-ab-packet.json`
- A：no-skill baseline
- B：with `kepu-zhongguo-skill`
- 映射：见 `blind-ab-answer-key.json`

## 结论

- 两位独立 blind judge 均判定 with-skill 版本胜出，票数 2/2。
- 胜出原因：标题更有提醒动作；开头有夏天家庭场景；正文不是泛泛列点，而是解释风险机制、判断条件和处理动作；事实缺口没有硬编。
- baseline 弱项：出现“本文将从”“总之”等 AI 痕迹；没有科普中国的家庭转发动作；建议过泛。
- with-skill 弱项：交付标签容易被误认为发布正文；个别风险句需要权威来源支撑后再写实。

## Judge 记录

- Judge 1：winner=B；B 分项为标题 8、开头 8、结构过程 8、语言原味 7、事实边界 8、去AI痕迹 7。
- Judge 2：winner=B；B 分项为标题 8、开头 8、结构过程 8、语言原味 7、事实边界 7、去AI痕迹 6。
- 平均：标题 8.0、开头 8.0、结构过程 8.0、语言原味 7.0、事实边界 7.5、去AI痕迹 6.5。

## Darwin 修补

- 发布版正文剥离交付标签。
- 无权威来源的具体风险句降级处理，保留待核实边界。
