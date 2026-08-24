# Holdout Leakage Log

## 隔离链

- 日期：2026-07-21（Asia/Shanghai）。
- 读取者角色：sealed holdout 最终独立验证制题员；不是目标 Skill 作者，不是题目执行者。
- 用户已明确授权最终解封验证。
- 先读取冻结策略和两份 holdout manifest，仅以 manifest 元数据冻结分层与排序规则；规则冻结后才打开 10+1 深度项原文。
- 其余 31 篇只由确定性脚本读取字节/文本以完成 SHA-256、字符数、结构统计和近重复计算；未把正文交给执行者。
- 未读取目标 `SKILL.md`、其写作或认知规则、`test-prompts.json`、任何 train-v1 baseline/skill 输出或评分文件。
- 未修改目标 Skill 规则。

## 读取范围

- `HOLDOUT_POLICY.md`。
- `writing-holdout.jsonl`、`conversation-holdout.jsonl` 及其深度项原文；shadow 项仅做机器统计。
- `writing-train.jsonl`、`conversation-train.jsonl`、`books-local.json` 及其指向内容，仅用于哈希和近重复核查。
- `curation-summary.json` 仅用于确认冻结计数和边界。

## 剔除与替补

- 写作深度集初选 10 项。
- `2015-medium` 首项因与本地书籍文本达到 0.760082 的 13-gram 包含率、最长归一化连续匹配 2,236、holdout 覆盖 0.761062，被判定为实质近重复并剔除。
- 按同 cell 固定盐排序使用下一项替补；替补项未命中复核线。
- `2016-long` 首项训练包含率 0.606372 触发人工复核；最长连续匹配 404、仅覆盖本篇 0.111973。打开对应训练项确认重合来自重复推广尾注，正文核心机制不重复，因此保留。
- 最终深度写作 10 项、口语 1 项；shadow 写作 31 项。

## 提示去标识检查

- 执行题包每项只允许 `id`、`modality`、`task`、`sanitized_input_materials`、`constraints` 五个字段。
- 匿名 ID 仅为 `h01` 至 `h11`。
- 执行题包禁止出现真实标题、URL、`source_id`、`source_path`、正文哈希和作者标识。
- 输入材料均为事实键、主题、机制或论证任务的重新表述，不要求复写原文。
- 真实映射、来源和评审参考只放在 `references/validation/evaluator-only/`。

## 原文未进入运行包的验证

- `holdout-prompts.json` 不含 holdout 正文、短片段、标题或来源标识。
- `evaluator-only/holdout-reference.json` 只含来源元数据、统计和人工提取的机制/结构/语言指纹/事实键，不复制长原文。
- `evaluator-only/shadow-holdout.json` 只含元数据、哈希验证、结构统计和近重复指标，不含正文字段。
- 最终 SHA-256 冻结清单覆盖执行题包、两份评审参考、shadow、匿名评测清单和本日志。

## 自动验证记录

- JSON 语法：通过。
- 执行题包计数：11；写作 10，口语 1；匿名 ID 严格为 `h01` 至 `h11`。
- 每题字段白名单：通过；五个允许字段之外为 0。
- 标题、URL、`source_id`、`source_path`、正文哈希、作者标识精确泄漏：0。
- 执行题包与全部 42 篇 holdout 原文的最长归一化连续匹配：5 个字符，低于 24 字符警戒线。
- 六个冻结产物中的整篇原文泄漏：0。
- 参考包条目：11；shadow 条目：31；shadow 正文字段：0。
- 匿名评测清单 ID 与题包顺序一致：通过。
- 冻结清单生成后另行执行 `openssl dgst -sha256` 复算；结果必须 6/6 匹配方可交付。
