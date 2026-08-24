# Darwin Optimization Log

## v1 基线

- 冻结 Skill SHA-256：`ec10dc301e186e750cbe61ed70e76dab904c56d87f05a32b072bf0327761e82b`；
- 训练测试：28 题，两个执行条件、两名独立评审，全部 full test；
- holdout：10+1，两个执行条件、两名独立评审，全部 full test；
- Darwin：92.0 / 93.0；
- holdout：9.457 / 9.200；
- 当前决定：`baseline_frozen`，未修改 Skill。

## 诊断簇

1. **去 AI 保真**：t19 相对基线回归，过度合并短段；
2. **非模板与角度分化**：t11、t18 在训练题落后；
3. **诊断与事实纪律**：t12、t16 至少一位评审明显判负；
4. **静态一致性**：一处 27→28 方法计数漂移；
5. **Soul 新规则**：需增加 first-person grounding 与真实消融，不能直接加载。

## 尚未执行

- 未进入 Darwin Phase 2 修改循环；
- 未运行 3 候选 GEPA-lite；
- 未激活 `AUTHOR-SOUL.ilang.md`；
- 未更改 v1 训练冻结 49/49 文件；
- 等待用户确认 t29/t30 与 Soul A/B 后再进行下一候选轮。

本日志不把 staging 当成已保留优化。所有修改必须在独立评审后按 Pareto 门决定 keep/reject。
