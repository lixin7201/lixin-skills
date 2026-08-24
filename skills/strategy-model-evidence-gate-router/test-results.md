# strategy-model-evidence-gate-router — 阶段 4 压力测试结果

- **日期**: 2026-07-20
- **批次**: 第10批原始安装；第13/14批修订回归
- **测试方式**: 独立 sub-agent 盲测
- **测试代理**: Hubble `019f8014-f811-79e2-93a7-7503c8d8c800`
- **测试文件**: `/Users/REPLACE_ME/.codex/skills/strategy-model-evidence-gate-router/test-prompts.json`
- **结果**: 9/9 通过
- **回炉要求**: 无

## 覆盖范围

- should_trigger: 5 条，覆盖战略模型选择、SWOT 证据排序、五力结构原因追问、BCG 标准线校准、GE 变量/权重/风险。
- should_not_trigger: 2 条，覆盖 `strategy-house-alignment-check` 和 `problem-analysis-tool-router` 混淆诱饵。
- edge_case: 2 条，覆盖高时效市场结论和 PEST 凭记忆填表边界。

## 盲测摘要

盲测代理只读取目标 `SKILL.md` 正文和相邻 Skill 的 frontmatter/标题，不读取 `expected_behavior`、`type` 或 `notes`。

所有应触发场景均命中 `strategy-model-evidence-gate-router`。战略屋对齐和泛问题工具选择均被正确分流。两个边界场景均拒绝凭经验或凭记忆输出市场进入结论，并停在当前来源核验/取证计划。

## 结论

触发、诱饵和高时效证据边界均符合预期；接受为阶段 5 修订交付，无需回炉。
