# 大土豆 Skill

路径：`/Users/lixin/.openclaw/workspace/skills/datudou-skill/`

调用名：`datudou-skill`

用途：按北京大土豆 / BJ的大土豆的写稿方式，写北京房产、教育育儿、中年生活、家庭账本、年轻人和反常识社会观察类公众号稿。

## 语料与验证

- 全量语料：48 篇 Markdown
- 训练集：40 篇
- holdout：8 篇，保存在 `holdout/originals/`
- 状态：ready dry-run；不是 95% 高保真认证

## 常用调用

```text
/datudou-skill
请按大土豆式写稿方式，围绕【主题】写一篇公众号稿。
我提供的材料如下：
1. ...
2. ...
要求：不要冒充作者本人；事实不确定的地方标待核实。
```

## 目录

```text
SKILL.md
去AI味保真补丁.md
references/
data/
holdout/
validation/
test-prompts.json
darwin-scorecard.md
darwin-optimization-log.md
调用指令.md
```
