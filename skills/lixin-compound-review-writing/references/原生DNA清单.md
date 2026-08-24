# 原生 DNA 清单

## 封装结论

- 封装日期：2026-08-20
- 原生 DNA 文件：24 个
- 复制一致性：`cmp` 24/24 通过
- 原生 DNA 树聚合 SHA-256：`4eef20a298865528e6e96231dcce4ac7400634008953a629749f2093a36bc10a`
- 内容边界：只封装已蒸馏 DNA，不复制训练原文、holdout 或原作者完整文章

这些文件是源 Skill 的原始蒸馏结果，不是本 Skill 对它们的二次摘要。

## 刘润

源目录：`/Users/REPLACE_ME/.openclaw/workspace/skills/liurun-skill/`

封装：

- `native-dna/liurun/Writing-DNA.md`
- `native-dna/liurun/语言DNA.md`
- `native-dna/liurun/文章结构模板.md`
- `native-dna/liurun/写作视角与认知框架.md`
- `native-dna/liurun/原味指纹.md`
- `native-dna/liurun/去AI味保真补丁.md`

主要负责：问题定义、商业机制、交易/成本/激励/责任链、概念压缩和结构化解释。

## 半佛

源目录：`/Users/REPLACE_ME/.openclaw/workspace/skills/banfo-skill/`

封装：

- `native-dna/banfo/Writing-DNA.md`
- `native-dna/banfo/语言DNA.md`
- `native-dna/banfo/标题DNA.md`
- `native-dna/banfo/开头模板.md`
- `native-dna/banfo/正文结构模板.md`
- `native-dna/banfo/转折与推进规则.md`
- `native-dna/banfo/结尾模板.md`
- `native-dna/banfo/原味指纹.md`
- `native-dna/banfo/去AI味保真补丁.md`

主要负责：主物件承重、机制反转、普通人关系、冷幽默、反手拆解和不鸡汤的收束。

## 36氪

源目录：`/Users/REPLACE_ME/.openclaw/workspace/skills/36kr-skill/`

封装：

- `native-dna/36kr/Writing-DNA.md`
- `native-dna/36kr/账号总风格.md`
- `native-dna/36kr/账号语言底线.md`
- `native-dna/36kr/文章结构模板.md`
- `native-dna/36kr/综合商业观察DNA.md`
- `native-dna/36kr/原味指纹.md`
- `native-dna/36kr/去AI味保真补丁.md`

主要负责：事实锚点、对象定义、变量和约束、信息密度、商业系统位置及谨慎结论。

## 刘思毅

源目录：`/Users/REPLACE_ME/.openclaw/workspace/skills/liu-siyi-writing-style/`

封装：

- `native-dna/liu-siyi/STYLE-DNA.md`
- `native-dna/liu-siyi/去AI味保真补丁.md`

主要负责：在场感、动作链、连续追问、直给判断、公开改判、不均匀节奏和真实张力。

## 默认加载

每次完整成稿至少读取：

1. 刘润 `Writing-DNA.md`、`语言DNA.md`、`原味指纹.md`
2. 半佛 `Writing-DNA.md`、`语言DNA.md`、`原味指纹.md`
3. 36氪 `Writing-DNA.md`、`综合商业观察DNA.md`、`原味指纹.md`
4. 刘思毅 `STYLE-DNA.md`
5. `李鑫口语DNA.md`
6. `dna-weights.json`

按任务再加载标题、开头、结构、推进、结尾和各源去 AI 补丁。读取失败时不得用高层标签代替原生 DNA；停止并报告缺失文件。
