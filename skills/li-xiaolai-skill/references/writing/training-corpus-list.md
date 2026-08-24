# Training Corpus List

## 唯一权威清单

为避免把 206 行元数据复制成第二份易漂移清单，训练集唯一权威文件是：

`/Users/REPLACE_ME/.codex/skills/distillation-orchestrator/builds/li-xiaolai-skill/manifests/curated/writing-train.jsonl`

- 条目：206 个唯一 `source_id`
- SHA-256：`bf000cea229779c3a6ef121e4af44aab5040305cfdfafe8e71d400e4c003de1e`
- 每条包含：来源集合、路径、URL、标题、日期、作者、正文字符数、正文哈希、时代、体裁、风险标签和归因状态
- 内容正文不复制进本 Skill；运行时只读取被清单指向、且哈希匹配的训练文件

## 进入条件

1. 归因为李笑来原创；
2. 正文长度和完整性过门；
3. 不是转载、翻译、短通知或仅审计材料；
4. 不属于冻结 holdout；
5. 来源正文 SHA-256 与账本一致。

## 使用限制

- 写作核只用净化正文视图；
- 研究引用仍须回到来源账本和公开 URL；
- 训练清单不能用于推断 holdout 的内容；
- 后期人机混合条目只作演化证据，不覆盖经典原味锚。
