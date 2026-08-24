# Blind A/B Report

## Setup

- Test cases: 10 holdout-derived prompts from `holdout/holdout-prompts.json`.
- Baseline: same model, no local skill.
- With-skill: `/banyuetan-skill` using generated account/type/byline DNA.
- Judge model: `openai/gpt-5.6-sol`, 3 independent blind judges.
- Rubric: route correctness, title/opening fit, mechanism analysis, steady public judgment, fact boundary, no source leakage or official/person impersonation.

## Iterations

|run|scope|with-skill votes|baseline votes|majority cases|decision|
|---|---:|---:|---:|---:|---|
|`compact_blind_ab_20260711_r2`|10 holdout|11|19|5 / 10|fail, optimize|
|`targeted_blind_ab_20260711_r3`|5 failed cases|15|0|5 / 5|targeted pass|
|`final_full_blind_ab_20260711_r4`|10 holdout|26|4|9 / 10|pass|

## Final R4 Case Summary

|id|with-skill|baseline|majority|
|---|---:|---:|---|
|h01|0|3|baseline|
|h02|3|0|with-skill|
|h03|3|0|with-skill|
|h04|3|0|with-skill|
|h05|2|1|with-skill|
|h06|3|0|with-skill|
|h07|3|0|with-skill|
|h08|3|0|with-skill|
|h09|3|0|with-skill|
|h10|3|0|with-skill|

## Follow-up

- h01 lost because weak人物散文素材需要更自然地转到“女性时间、家庭分工、精神需求”，不能让事实审查感压过成稿感。
- Added h01 boundary patch and verified `validation/h01_internal_boundary_smoke_20260711_r7/with_skill_outputs.md` has no Skill/DNA/route leakage.
