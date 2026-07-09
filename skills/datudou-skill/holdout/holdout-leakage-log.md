# Holdout Leakage Log

初始检查：DNA 文件生成前冻结 holdout；本批次不把 holdout 正文复制进 `SKILL.md`、`references/`、`test-prompts.json`。

| Check | Result | Note |
|---|---|---|
| holdout originals copied | PASS | 8 files in `holdout/originals/` |
| holdout body in DNA | PASS | `holdout_body_leaks 0` across SKILL/references/test/validation/data reports |
| generated draft body leak | PASS | positive-control and validation drafts do not copy holdout body snippets |
| blind A/B generated body leak | PASS | `holdout/blind-ab-20260709/leakage-check.md` longest common fragment threshold check passed |
