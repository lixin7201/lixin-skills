# OpenClaw Smoke Test 2026-07-07

## Command

```bash
openclaw agent --local --agent main --session-key app-skill-smoke-20260707-r2 --timeout 180 --json --message '/app-skill 按大宜宾-梦竹路线，把这条素材整理成一条大宜宾 APP 招聘帖：宜宾某物业公司招聘客服2名，薪资4000-5000元/月，工作地点临港，报名截止2026年7月15日，报名电话待核实。要求：不要编造待遇、地址和联系方式，缺失信息列待核实。'
```

## Result

- status: success
- model: gpt-5.5
- durationMs: 48942
- toolSummary.failures: 0
- route: 大宜宾-梦竹 / 招聘求职信息
- fact check: 未编造报名电话、具体地址、社保福利、岗位要求；缺失项列为待核实。

## Output Shape

```text
【宜宾临港一物业公司招客服2名，薪资4000-5000元/月】
...
【待核实/提醒】
...
【评论口】
...
```

## Optimization Kept

第一次 smoke 曾出现文稿类型文件路径猜测失败；已添加 `references/文稿类型/<类型>.md` 兼容别名并复测通过。
