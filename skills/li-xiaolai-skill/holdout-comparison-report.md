# Holdout 对照报告（v1 Markdown-only）

> 状态：双评审 holdout 基线已完成；Soul 与 GEPA-lite 尚未运行。  
> 运行：10 篇书面 + 1 篇口语，两个隔离条件，22 份真实输出；两名评审逐项 full test，`dry_run=0`。

## 结论

v1 Markdown-only Skill 在 sealed holdout 上通过全部 ready 硬门，并相对无 Skill 基线取得小而一致的净增益：两位评审合计 18 胜、2 负、2 平；Skill overall 9.329，基线 9.213，差值 +0.116。

这不是最终认证。训练合成题中 Skill 未稳定击败强基线，t19 去 AI 单题还出现相对回归；新增 Soul 层和 GEPA-lite 都尚未经过确认与消融。

## 17 维汇总

| 维度 | Skill | 基线 | 差值 |
|---|---:|---:|---:|
| title | 9.273 | 9.245 | +0.027 |
| opening | 9.273 | 9.141 | +0.132 |
| body structure | 9.468 | 9.314 | +0.155 |
| structure metric | 8.714 | 8.641 | +0.073 |
| language rhythm | 9.018 | 8.836 | +0.182 |
| material use | 9.491 | 9.373 | +0.118 |
| viewpoint organization | 9.586 | 9.464 | +0.123 |
| writing process | 9.486 | 9.373 | +0.114 |
| original-flavor fingerprint | 9.100 | 8.891 | +0.209 |
| non-template variation | 9.259 | 9.186 | +0.073 |
| de-AI preservation | 9.145 | 8.986 | +0.159 |
| paragraph/structure regression | 8.759 | 8.668 | +0.091 |
| transition | 9.355 | 9.227 | +0.127 |
| ending | 9.418 | 9.295 | +0.123 |
| overall reading feel | 9.355 | 9.177 | +0.177 |
| fact reliability | 9.855 | 9.827 | +0.027 |
| non-impersonation compliance | 10.000 | 10.000 | 0.000 |

## 评审一致性

| 评审 | Skill 胜 / 负 / 平 | Skill overall | 基线 overall | 差值 |
|---|---:|---:|---:|---:|
| Judge A | 8 / 2 / 1 | 9.457 | 9.387 | +0.070 |
| Judge B | 10 / 0 / 1 | 9.200 | 9.040 | +0.150 |

Judge A 的两项负例是 h01 与 h09；Judge B 对 h01、h09 均判 Skill 小胜。跨评审合并后，h01 差值 -0.008、h09 +0.018，属于接近噪声的争议项。最大一致增益来自 h02、h07、h08；逐项 17 维明细见 `原文差距矩阵.csv`。

## 硬门

- holdout overall ≥8.0：9.329，过；
- title/opening/structure/language/material ≥7.5：全部过；
- structure metric 与 paragraph regression ≥7.5：8.714 / 8.759，过但为最弱结构簇；
- original-flavor fingerprint ≥8.5：9.100，过；
- non-template variation ≥7.5：9.259，过；
- fact reliability ≥9.5：9.855，过；
- non-impersonation =10：10.000，过；
- holdout 原文泄漏：0；一项书籍近重复已在制题时剔除并替补。

## 当前最弱点

1. 结构统计匹配与段落回归仍是最低维度；不能再靠统一合并短段来“去 AI”。
2. 训练 t19 中带 Skill 版本保留事实，却把 16 段压成 5 个近同长长段；两位评审均认为不如基线自然。
3. 训练 t11、t12、t16、t18 在至少一位评审处明显落后，分别指向双角度分化、诊断完整性、因果纪律与反模板变化。

## 认证状态

`holdout strong`：达到 strong 数值线（overall ≥9.0，核心维度无低于 8.5）。  
`final not certified`：Soul A/B、t29/t30、GEPA-lite 和最终安装/触发烟测尚未完成；不能据此宣布总 Skill 已 ready 或 original_flavor 完成。
