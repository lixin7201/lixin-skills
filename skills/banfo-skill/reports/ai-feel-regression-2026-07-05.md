# AI Feel Regression Report

## 用户反馈

用户指出 `2026-07-05-ai-learning-penalty-banfo-style.md` AI 感强、有语病，尤其是：

- 抽象判断太多。
- “学生没有更会，但作业更像会了”一类句子像 AI 总结。
- “很不像效率，还很像进步”不顺。

## 诊断

这不是事实问题。CEPR 关键数字核对无误：26811 名学生、30 个月、作业分数 +18%、作业时间 -30%、月考 -20%、高风险考试 -18% 到 -24%。

失败点在写法：

1. 缺少主物件承重，原稿主要靠“能力/交付/效率/训练”等抽象词推进。
2. “不是 A，而是 B”过多，像模型套结构。
3. 数字像论文摘要，没有被放进作业本、红笔、月考卷、PPT 答辩这类场景里。
4. 结论句太顺，缺少半佛式具体拧巴感。

## 修复

- 重写稿件：`/Users/lixin/AI code/openclaw/drafts/wechat/2026-07-05-ai-learning-penalty-banfo-style.md`
- 主物件改为：作业本、红笔、月考卷、PPT 答辩。
- 标题改为：`AI 写作业，最邪门的是作业本开始会化妆了`
- 删除“不是 A，而是 B”连续模板。
- 将 Skill 增加三处反 AI 腔规则：
  - `references/语言DNA.md`：AI 腔硬禁区
  - `references/写稿流程操作手册.md`：去 AI 腔
  - `references/像不像判别器.md`：AI 感专项诊断

## 本地测试

| 检查 | 结果 |
|---|---|
| 新稿字数 | 2638 非空白字符 |
| 小节数 | 6 节 |
| “不是 A，而是 B” | 0 |
| “真正的问题是” | 0 |
| `verify_banfo_skill.py` | 通过 |
| OpenClaw skill info | `banfo-skill ✓ Ready` |

## 结论

不能说上一版“已经蒸馏好”。上一版只能算结构可用，实际出稿暴露了 AI 腔漏洞。本轮已把这个漏洞编码进 Skill 和验证脚本。
