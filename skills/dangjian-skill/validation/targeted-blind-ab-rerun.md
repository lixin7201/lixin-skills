# Targeted Blind A/B Rerun 2026-07-09

## Setup

- Weak cases rerun after minimal rule patch: `a051`, `a074`.
- Baseline outputs held constant from initial blind run.
- A/B labels rerandomized with seed `20260710`.
- Judges: 3 independent OpenClaw local judge sessions.

## Results

- Majority wins on rerun: optimized_skill 1/2, baseline 1/2, ties 0/2
- Judge votes on rerun: optimized_skill 3/6, baseline 3/6, ties 0/6

| id | majority | optimized votes | baseline votes | optimized avg | baseline avg | delta |
|---|---|---:|---:|---:|---:|---:|
| a051 | baseline | 0 | 3 | 6.33 | 8.0 | -1.67 |
| a074 | with_skill_rerun | 3 | 0 | 8.0 | 6.33 | 1.67 |

## Judge Notes

### a051
- T1: A更短稳，去掉了简报抬头和额外升华段，读书分享内容完整但没有明显拉长；B格式感更重且后段有模板化延展。
- T2: A更短稳，去掉了简报套壳和额外总结段，读书会内容不被模板化拉长。
- T3: A更像短稳的读书分享会稿，去掉简报壳后结构干净，B虽然有现场感但额外拔长了平台化总结。

### a074
- T1: B更紧凑，把荣誉和案例控制在概括层面，反馈也写得克制；A分段展开较多，荣誉和服务案例堆叠感更明显。
- T2: B更紧凑，荣誉和业务点到即止，反馈表述也更克制，没有把领导宣传写得过满。
- T3: B更紧凑，荣誉和业务点到即止，反馈表述也更克制；A把案例铺得偏满，领导宣传感稍重。

