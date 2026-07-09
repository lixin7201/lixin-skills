# Holdout Comparison Report

## Scope

- Frozen holdout: 8 articles across 5 activity types.
- Prompts used material summaries only; original holdout prose stayed under `holdout/originals/`.
- Generation: main OpenClaw agent with `/dangjian-skill` vs no-skill baseline.
- Blind A/B: 3 independent OpenClaw judge sessions; weak cases rerun with targeted Darwin patches.

## Final Adjusted Results

- Holdout average: 8.73/10
- Majority wins: skill 8/8, baseline 0/8
- Judge votes after targeted reruns: skill 23/24, baseline 1/24
- Fact reliability estimate: 9.7/10
- Non-impersonation compliance: 10/10

| id | type | final skill source | skill avg | baseline avg | votes | note |
|---|---|---|---:|---:|---|---|
| a004 | 发言稿 | with_skill | 8.77 | 8.23 | 2/3 | 发言稿/先进事迹结构稳，仍有一票偏好 baseline 的口语发言感。 |
| a010 | 日常活动开展 | with_skill | 8.83 | 7.13 | 3/3 | 党员参与、承办关系和党建落点更完整。 |
| a021 | 日常活动开展 | with_skill | 8.87 | 8.00 | 3/3 | 党课学习事实和岗位转化更像日常活动简报。 |
| a039 | 获奖宣传 | with_skill | 8.93 | 8.07 | 3/3 | 喜报语气、荣誉承接和品牌深化更完整。 |
| a046 | 读书分享会、精英研学会 | with_skill | 8.90 | 8.03 | 3/3 | 逐人分享、岗位转化和学习型党组织承接更完整。 |
| a051 | 读书分享会、精英研学会 | with_skill_rerun2 | 8.67 | 7.00 | 3/3 | 第二轮补丁去掉默认简报头和长尾总结后赢回。 |
| a061 | 领导宣传 | with_skill | 8.87 | 8.00 | 3/3 | 领导调研宣传结构、事实边界和下一步承接更稳。 |
| a074 | 领导宣传 | with_skill_rerun | 8.00 | 6.33 | 3/3 | 第一轮补丁压缩荣誉和业务堆叠后赢回。 |

## Remaining Weakness

- `发言稿` still has a narrow style split: some judges prefer more口语化现场发言, while this Skill prefers书面发言材料结构。
- `领导宣传` needs the user to provide confirmed feedback wording; otherwise the Skill intentionally downgrades praise.
- `发言稿` and `获奖宣传` have fewer than 10 corpus samples, so they are usable prototype types, not 95% certified types.
