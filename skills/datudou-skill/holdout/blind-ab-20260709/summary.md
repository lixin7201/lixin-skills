# 完整 Blind A/B 汇总

运行时间：2026-07-09
比较项：11（8 holdout + t20-t22）
评审：3 个独立 agent（test / pm / dev），均无 datudou-skill。

## 结果

- skill item-majority：9/11 = 81.8%
- skill vote-level：28/33 = 84.8%
- baseline item-majority：2/11
- tie item-majority：0/11
- original-flavor blind gate：PASS（按 item-majority >= 80%）
- vote-level 80% 参考：PASS

## 明细

| id | 类型 | 标题 | A来源 | B来源 | skill票 | baseline票 | tie票 | 多数 |
|---|---|---|---|---|---:|---:|---:|---|
| h01 | holdout | 夫妻之道 | baseline | skill | 3 | 0 | 0 | skill |
| h02 | holdout | 教育格局在发生巨变 | baseline | skill | 3 | 0 | 0 | skill |
| h03 | holdout | 为什么年轻人不愿意留在北京了？ | baseline | skill | 3 | 0 | 0 | skill |
| h04 | holdout | 终于有车牌了 | skill | baseline | 3 | 0 | 0 | skill |
| h05 | holdout | 提前退休 | baseline | skill | 3 | 0 | 0 | skill |
| h06 | holdout | 最近三个月，三件反常识的事 | baseline | skill | 3 | 0 | 0 | skill |
| h07 | holdout | 写一篇育儿经，关于英语 | skill | baseline | 3 | 0 | 0 | skill |
| h08 | holdout | 车市跟楼市现在有的一拼了 | skill | baseline | 3 | 0 | 0 | skill |
| t20 | original_flavor | t20 | skill | baseline | 0 | 3 | 0 | baseline |
| t21 | original_flavor | t21 | skill | baseline | 3 | 0 | 0 | skill |
| t22 | original_flavor | t22 | baseline | skill | 1 | 2 | 0 | baseline |

## 弱项摘录

- h01：多数=skill；弱项：J1: 北京坐标仍偏泛；J2: A北京坐标弱；理由：J1: B账本和中年家庭更足；J2: B账本更细且有北京家庭坐标；J3: 北京家庭账本更实
- h02：多数=skill；弱项：J2: A偏泛教育评论；理由：J1: B有北京房教现金流坐标；J2: B有北京房区通勤和教育账；J3: 北京教育房产更具体
- h03：多数=skill；弱项：J1: 入口都偏议论；J2: A坐标略泛；理由：J1: B长期账和家庭托举更实；J2: B把北京生存账算到家庭托举；J3: 长期账和绑定更清楚
- h04：多数=skill；弱项：J1: 标题包装略少；J2: B略温柔顺滑；理由：J1: A北京车牌家庭账更完整；J2: A车牌放进北京家庭账本更硬；J3: 车牌家庭成本更全
- h05：多数=skill；弱项：J2: A北京坐标缺失；理由：J1: B北京中年支出更具体；J2: B北京中年支出和现金流更具体；J3: 北京中年支出更硬
- h06：多数=skill；弱项：J1: 具体入口不足；J2: A北京坐标弱；理由：J1: B三件事都落家庭风险；J2: B三件事都落普通家庭风险账；J3: 三件事都落到账本
- h07：多数=skill；弱项：J1: 北京坐标还可更具体；J2: B更像通用育儿文；理由：J1: A普通家庭边界更保守；J2: A有北京家长和长期低损耗判断；J3: 北京英语投入边界更像
- h08：多数=skill；弱项：J2: B结尾偏公号；理由：J1: A车房类比账本更冷；J2: A车房差异和月供陷阱更像账本；J3: 车房类比账本更深
- t20：多数=baseline；弱项：无；理由：J1: B判别标准更有边界；J2: B判别口径更完整且边界更准；J3: 判别标准更有边界
- t21：多数=skill；弱项：J2: B结构略工整；理由：J1: A主判断更冷更像账本；J2: A主判断更冷且北京学区退路明确；J3: 判断链和退路更像
- t22：多数=baseline；弱项：无；理由：J1: A自然段和冷感更稳；J2: B口语更自然冷感更足；J3: 自然段账本更稳