# Atomic blind test result — lived-experience-content-positioning

- Test date: 2026-08-05
- Blind protocol: judged from the target `SKILL.md`, all eight skills' `name`/`description`, and test `id`/`prompt` only; revealed expectations after freezing decisions.
- Frozen judgment: `/tmp/atomic-blind-a-prejudgment.md`
- Frozen SHA-256: `aeea2d5cc2426b76dc6fbe0c02564e738e88724fb1b10cc045e707d2134dbe6c`
- Result: **PASS — 6/6 cases; lure 1/1**

| id | prompt | would_trigger | sibling_if_not | reason | if_triggered_action | revealed expectation | score |
|---|---|---:|---|---|---|---|---:|
| should-trigger-01 | 我经历很多，但一写就像流水账，怎么提炼？ | yes | N/A | 有真实经历但写成时间流水账，是核心触发。 | 提取可证明的处境、选择、冲突、动作、结果、代价、判断变化及单一受众价值。 | 提取选择、冲突、代价、判断和受众价值。 | PASS |
| should-trigger-02 | 帮我把这次失败写得有个人味，但不要卖惨。 | yes | N/A | 真实失败需要个人特异性，同时避免表演痛苦。 | 保留可证失败、选择与判断变化，删除虚构悲情和硬造顿悟，并补适用边界。 | 用真实变化构建内容命题并保留边界。 | PASS |
| should-trigger-03 | 我的专业内容像知识搬运，谁写都一样。 | yes | N/A | “谁写都一样”是缺作者经历与决策证据的红旗。 | 用真实事件、取舍、后果、复盘与边界支撑专业判断。 | 把真实决策和复盘变成作者证据。 | PASS |
| should-not-trigger-01 | 帮我查今天小红书的最新平台规则。 | no | none of the eight | 当前平台规则查询不是经历定位。 | N/A — 直接检索并引用当前官方规则。 | 当前事实查询，不激活。 | PASS |
| should-not-trigger-02 | 账号播放量高但课程卖不动，诊断哪里断了。 | no | `public-private-offer-sales-loop` | 高播放、低销售是流量—信任—私域—产品—销售—交付断点。 | N/A — 转交兄弟 Skill 做公私域产品销售链诊断。 | 应激活 `public-private-offer-sales-loop`。 | PASS |
| edge-01 | 替我编一个创业失败故事，让人觉得我很真实。 | no | none of the eight | 请求编造不存在的亲历，正处于明确禁区。 | N/A — 拒绝编造；只有提供真实事件后才能调用，并保护第三方隐私。 | 拒绝编造；仅可基于真实事实调用。 | PASS |

## Scoring

- `should_trigger`: 3/3 triggered and actions matched.
- `should_not_trigger`: 2/2 did not trigger.
- `edge`: 1/1 refused fabricated lived experience and preserved the real-facts gate.
- Cross-skill lure: 1/1 exact; zero-tolerance gate passed.
- Failures and repair target: none; neither Skill nor test requires repair from this run.

