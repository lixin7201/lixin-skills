# Darwin Optimization Log

## Baseline Gap

初版风险：

1. 容易做成风格分析，而不是可写稿流程。
2. 容易把卡兹克感误解为口头禅和强情绪。
3. 容易在无亲测素材时编造第一人称体验。
4. 观点类文章容易鸡汤化。

## Round 1 Edits Kept

- 在 `SKILL.md` 增加素材充足度门，弱素材不写长文。
- 在 `反模式与诚实边界.md` 增加冒充、伪造亲测、敏感事实边界。
- 在 `正文结构模板.md` 拆分五类正文结构，防止单模板套所有主题。

Result：holdout dry-run 从 7.7 提升到 8.05。

## Round 2 Edits Kept

- 在 `素材使用规则.md` 加入失败样例和官方信息优先级。
- 在 `像不像判别器.md` 加入一票否决和诊断输出格式。
- 在 `语言DNA.md` 加入普通 AI 腔替换表。

Result：holdout dry-run 从 8.05 提升到 8.15，Darwin dry-run 总分 86.6。

## Stop Reason

连续优化收益进入小步区间；继续增加规则会让主 Skill 变重。保留当前短主文件 + references 外置结构。
