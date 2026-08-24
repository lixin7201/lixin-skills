# 来源与归因

## 主训练集

- 审计：112 个去重事件；52 篇分享、60 个问答。
- 四区：train 71、calibration 12、confirmation 11、final-lockbox 18。
- train 直接回答 36；curated mentor-train 65；writing-train 14。
- 时间：2017–2026。
- 主清单 SHA-256：9606720b508cb5535a8b87e3a33aa9863866c7bdddba178f38bd6110c92767b6。
- 本次只读 train；未读 calibration、confirmation、final-lockbox、judge 或 prompts。

直接问答支持判断、因果、回答策略；文章支持世界观、主题和有限写作特征。

## 飞书补充集

- 365 个可归因章节；train 248，curated mentor-train 160。
- 证据等级 P1.5-user-supplied-attributed-compilation；attribution_verified=false。
- capture SHA-256：7c986221835e159d1558ab044a3780eb3635e413e9129dffd52e4c22752155c7。
- content SHA-256：39da06c91d5aaeaa7202f5367261637443d797114412d56bd52789e8cd4f48b4。

只能丰富主题、经历线索、张力和候选框架，不能写成本人直接回答或计入直接回答认证。

## 认证状态

本 Skill 走 R9 构建，但本次只做训练内合成 smoke，没有揭盲、独立评审或 final-lockbox 对照，不得标“已通过高保真认证”。写作 14 篇，低于 30 篇预检线，只能标有限原型。