# Darwin Scorecard

评估对象：`renwu-skill/SKILL.md`
评估模式：`dry_run + full blind A/B`（结构评分 + frozen holdout prompts + 3 个独立 judge）。

## 9 维评分

|维度|权重|分数|加权|
|---|---:|---:|---:|
|Frontmatter质量|7|9.0|6.3|
|工作流清晰度|12|9.0|10.8|
|失败模式编码|12|8.8|10.6|
|检查点设计|6|8.0|4.8|
|可执行具体性|17|9.0|15.3|
|资源整合度|4|9.5|3.8|
|整体架构|12|8.8|10.6|
|实测表现|23|8.8|20.2|
|反例与黑名单|6|9.0|5.4|
|**总分**|**100**|||**87.8**|

## Ready Gates

- OpenClaw 目录发现：PASS，`openclaw skills info renwu-skill --agent main` 显示 `renwu-skill ✓ Ready`、`Visible to model: yes`、`Available as command: yes`。
- Darwin final score >= 85：PASS，87.8。
- Holdout average >= 8.0：PASS，见 `holdout/holdout-comparison-report.md`。
- 结构指标：PASS，见 `data/结构与段落指标.md`。
- 原味指纹：PASS，见 `references/原味指纹.md`。
- fact reliability >= 9.5：PASS，dry-run 9.7。
- non-impersonation = 10：PASS。
- de-AI preservation：PASS，见 `validation/de-ai-preservation-regression.md`。
- holdout leakage：PASS，12 篇 holdout 源文、72 个生成文件，35 个中文字符以上正文段落命中 `0`。
- full blind A/B：PASS，3 judges 总计 30/30 正确选择 skill 版，多数票 10/10；已根据弱项做最小规则补丁。
- OpenClaw 命令烟测：PASS，`openclaw agent --local --agent main ... "/renwu-skill ..."` 返回 `renwu-skill 已加载`，并列出会先读取的 DNA 文件。运行中 eapi/gpt-5.5 先返回 401，随后 fallback 到 openai/gpt-5.6-sol 成功。

## 结论

状态：`ready(full blind A/B + OpenClaw smoke)`。不是 95% 高保真认证；当前通过的是原味可调用与 ready 门槛。
