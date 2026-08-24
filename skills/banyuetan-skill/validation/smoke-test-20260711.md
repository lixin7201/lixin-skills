# Smoke Test 2026-07-11

## OpenClaw Skill Check

- command: `openclaw skills info banyuetan-skill --agent main`
- result: `banyuetan-skill ✓ Ready`
- visible_to_model: yes
- available_as_command: yes

## Generation Smoke

- model: `openai/gpt-5.6-sol`
- command shape: `/banyuetan-skill 按半月谈记者线，把这条素材写成一篇半月谈式短评...`
- result: success
- observed: no invented region, policy, expert, or specific data; missing facts listed as facts to verify.

## H01 Internal Boundary Smoke

- path: `validation/h01_internal_boundary_smoke_20260711_r7/with_skill_outputs.md`
- forbidden internal terms checked: `Skill`, `skill`, `DNA`, `路由`, `署名线`, `训练材料`, `参考文件`, `按账号层`
- result: forbidden_hits = 0

## Static Checks

- holdout_body_leaks: 0
- missing_type_refs: []
