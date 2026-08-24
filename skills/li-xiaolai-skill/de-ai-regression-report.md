# 去 AI 前后回归报告（最终认证）

日期：2026-07-21  
状态：`FINAL_CERTIFIED_PASS`  
生产条件：Markdown-only v1  
Soul：`inactive`

## 结论

当前 v1 的终稿去 AI 保真流程通过最终三题认证。固定测试为 t19、t22 和匿名 holdout h06；两名独立评审均在 Stage 1 冻结后才揭示映射，合并结果为 after `6 胜 / 0 负 / 0 平`。

主 `SKILL.md`、目标 `去AI味保真补丁.md` 和通用 `de-ai-preserve-voice/SKILL.md` 均未修改；认证的是当前冻结规则的正确执行，不是新的 GEPA 优化。Soul 候选没有加载。

## 核心结果

| 检查 | 结果 |
|---|---:|
| 两位独立评审决定 | `pass / pass` |
| after 合并偏好 | 6 胜 / 0 负 / 0 平 |
| all AI 痕迹减少 delta | +4.8166 |
| all 原味指纹 delta | +4.1167 |
| all 非模板变化 delta | +5.7500 |
| all 段落/结构回归 delta | +5.6000 |
| all overall delta | +3.8833 |
| h06 holdout overall delta | +0.7000 |
| h06 holdout 事实 delta | 0.0000 |
| h06 holdout 原味 delta | +0.8500 |
| h06 holdout 段落/结构 delta | +0.7000 |
| 第一人称与非冒充下降 | 0 |
| 来源/holdout 泄漏 | 0 |

## 三题客观回归

### t19 · 去 AI 保真

- 空泛时代开头、两处路线图、四类无来源权威和通用升华全部删除；
- 六人、三十天、十二个工具、四次演示、零成品、每周八小时和七天试验全部保留；
- 有作用的长句和“我刚才也差点……”自我改口保留；
- 连续七个同功能短段完成合并，但仍保留一个转向直断短块；
- 正文 16→6 段，中位数 82.5→64.5，≤20 字短段 7/16→1/6，最长连续短段 7→1；短段比例没有归零；
- 回归表与最终成稿复算一致。

### t22 · 受保护粗粝

- 所有试验数字、临时照护/就医观察和“初稿尚未行业专家核验”边界保留；
- 只从给定材料恢复观察位置、问答、自我修正和不均匀节奏；
- 新增经历、人物、对话、动机、权威或结果均为 0。

### h06 · 匿名 holdout

- after 只把“第一块/第二块”配对路标改成自然推进，其余核心结构不重写；
- 观察正文 885 个中文字符，恰好两处结构风险；
- 观察者位置、降低关系背书和提问者/受访者/公开场景三方机制全部保留；
- 真实姓名、公司、产品、节目和来源路径均为 0。

## 冻结与隔离

- 输入冻结：11/11；judge packet：19/19；根复核 mismatch：0。
- before/after 分别由隔离执行器生成；after 只能读取冻结 before 和两份 treatment。
- 两名评审各自只读取自己的互补随机 A/B packet；Stage 1、Stage 2 哈希均通过。
- 聚合：`references/validation/final-de-ai-certification/aggregate.json`，SHA-256 `41c3917617d92b6576835f63ffae0798020ffec2ab417e2ab734e5c553f4b715`。

## 认证边界

本报告认证当前三份规则组合：

- 主 `SKILL.md` SHA-256：`ec10dc301e186e750cbe61ed70e76dab904c56d87f05a32b072bf0327761e82b`；
- 目标补丁 SHA-256：`9f8155bbe9349231224da69daa7493ee611404ed66b428c890c21d536e3fda24`；
- 通用去 AI Skill SHA-256：`514992d33f23e1097665af207cf5de8526cc9bd526a98fb5a1df3fd9689310c1`。

任一文件改变后都需要重新认证。本结果不激活 Soul，不改变 GEPA-lite `keep=0` 的结论，也不等同于 `high_fidelity_95` 认证。
