# 来源治理

## 冻结信息

- 对象：明白
- 源清单：`/private/tmp/r9-persona-batch-20260811-v3/mingbai/source-manifest.jsonl`
- 审计：`/private/tmp/r9-persona-batch-20260811-v3/mingbai/audit.json`
- 清单 SHA-256：`73e1cd9ccd954d9d4e740e5661ea7bccbba29f376df17a02e1beba8e170439d3`
- 独立事件：65
- split：train 44、calibration 8、confirmation 6、final-lockbox 7
- 训练区：mentor train 目录可见 44 个文件；audit 的 curated 计数为 43，存在 1 个口径差异，交付按用户已确认的 train 44 标注，并保留此审计差异。
- 写作 train：16
- 直接回答：全量 2；train 1；final-lockbox 1
- 年份：2017–2025

## 能力结论

- 判断/建议：**prototype**。文章类建议证据较多，但直接回答 train 仅 1。
- 写作：**prototype**。16 篇写作训练材料不足以认证高保真或 95%。
- 经历/事实：只可调用明确公开条目，不能补传记空白。
- 非冒充：强制通过。

## 使用范围

运行时只依赖本 Skill 的蒸馏规则，不读取 calibration、confirmation 或 final-lockbox。examples 中不得放入这些区的原答、独有措辞或金标命题。

## 归属限制

当前材料以公开帖子/文章为主。若存在编辑、转载、渲染变体或他人内容嵌入，只能把可明确归于作者正文的部分用于人物规则；引用案例不等于作者亲历。

## 禁止认证

不得写：本人型导师、高保真、原汁原味、95% 相似、代表明白当前立场。升级需要更多直接问答事件族、更多写作完整文章、隔离评审与未见 lockbox 验证。
