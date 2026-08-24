# Blind A/B Report

评估对象：`validation/blind-ab-judge-packet.json`

## 结果

- Judge 数：3
- 每个 judge 只读取无 answer key 的 `blind-ab-judge-packet.json`
- 每个 judge 正确选择：10/10
- 总正确选择：30/30
- 按 item 多数票：10/10
- 通过门槛：skill 输出优于 no-skill baseline >= 80%

## Judge 一致指出的弱项

1. `h01/h05`：题目主体明确偏女性或女孩时，候选样稿使用“他/采访对象”不贴合事实。
2. `h07`：逝者/作品纪念题不应强行写成“采访对象坐在房间里”的现场。
3. `h10`：商业科技/AI 题必须落到鱼塘、车间、手机屏幕、一次具体操作等材料场景。

## 已保留的最小规则补丁

- `SKILL.md` 新增 `2.5 校准人物、代词和入口场景`。
- `references/账号语言底线.md` 新增代词边界和场景边界。
- `references/像不像判别器.md` 新增盲测暴露的硬伤。

## 结论

状态：`full blind A/B pass with targeted patch`。
