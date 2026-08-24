# Holdout 泄漏核验记录

- 冻结阶段：训练与 holdout 精确 hash 重合 0；下游 240 字窗口命中 0。
- 生成 prompt：10 个条目；去除题名后，20 字连续重合命中 0；结果 PASS。
- 生成结果：20 个 Skill/baseline 比较；去除题名后，24 字连续重合命中 0；结果 PASS。
- 盲评员只读匿名 A/B packet，不读映射、候选身份或语料目录。生成代理只读 prompt-only packet，不读 holdout 原文。

结论：泄漏门通过。文章题名不计入重合；候选没有借用 holdout 原句来提高相似分。
