# Multi-Editor Public Account Workflow

Use this when one public account has multiple editors, multiple article types, or an unclear author mix.

## Principle

Do not average all articles into one voice. Build a routing writing Skill:

```text
account baseline DNA + article-type DNA + optional editor DNA
```

If editor identity is unknown, distill by article type first. Only cluster suspected editor styles when clearly marked as inference with confidence.

## Phase 0: Metadata

Create:

- `语料质量报告.md`
- `文章元数据总表.csv`
- `文稿类型分布.md`
- `小编语料分布.md`
- `结构与段落指标.md`
- `原味语料分层.md`

For each article record:

- title
- date
- author/editor or unknown
- article type
- channel
- word count
- visual assets
- available performance signal if provided
- training or holdout
- paragraph/structure metrics: paragraph count per 1000 Chinese characters, median paragraph length, <=20-character short paragraph ratio, max consecutive short-paragraph run, section count, progression chain, and visual break cadence
- source stratum: representative, high-engagement, routine, atypical, early/recent, or weak sample
- original-flavor notes: account-level quirks, type-level quirks, editor-level quirks, and false-match risks

Classify article types, then ask the user to confirm if labels are uncertain.

Candidate types:

- 民生稿
- 政务稿
- 活动稿
- 商家稿
- 人物稿
- 情感稿
- 招聘稿
- 文旅稿
- 教育稿
- 突发短消息
- 深度长文
- 服务提醒
- 评论观点

## Phase 1: Layered Holdout

Use stratified holdout:

- keep holdout articles for each major article type
- keep holdout articles for each major editor when editor samples are sufficient
- keep high-fidelity scores separate by account baseline, article type, and editor; do not average weak layers into a strong account-level score
- keep at least one routine/non-best holdout when possible; high-scoring articles alone overfit the skill toward 爆款 instead of 原汁原味

Rules:

- article type `<10` samples: prototype template only
- editor `<20` samples: do not produce stable personal DNA
- editor `20-30` samples: mark as early editor DNA
- unknown author articles feed article-type DNA, not personal DNA

Create:

- `training-corpus-list.md`
- `holdout-eval-list.md`
- `holdout-leakage-log.md`
- `样本不足清单.md`
- `分层原味指纹计划.md`

## Phase 2: Account Baseline

Use `huashu-nuwa` and `writing-dna-skill` to create:

- `账号总风格.md`
- `账号选题判断框架.md`
- `账号语言底线.md`
- `账号排版规范.md`
- `去AI味保真补丁.md`
- `账号原味指纹.md`

Capture:

- account positioning
- default reader
- topic boundaries
- title intensity
- emotional intensity
- local/industry/group feeling
- fact-checking rules
- banned expressions
- shared layout habits
- account-level paragraph rhythm and structure ranges, including when short paragraphs are real account DNA and when continuous micro-paragraphs should be merged
- account-level protected quirks: what sounds rough but belongs to the account, what is generic AI polish, and what must never be averaged away

## Phase 3: Article-Type DNA

For each major article type, create `文稿类型/<类型>DNA.md`.

Each file must include:

- type positioning
- applicable scenes
- title formulas
- opening templates
- body structures
- material rules
- transition rules
- ending rules
- fact-check points
- anti-examples
- type-specific structure metrics: common section order, paragraph rhythm, list/case/example density, and visual cadence
- type-specific original-flavor fingerprint: angle reflex, material priority, emotional temperature, protected phrases, false-match warnings

## Phase 4: Editor DNA

Only for editors with enough samples, create `小编风格/<小编名>-DNA.md`.

Each file must include:

- title habit
- opening habit
- structure habit
- language rhythm
- emotional intensity
- best article types
- material habit
- common sentence patterns
- false-match warnings
- difference from account baseline
- editor-specific paragraph rhythm and structure habits, only when samples are sufficient; otherwise inherit account/type metrics
- editor original-flavor fingerprint: what to preserve even if it is awkward, blunt, repetitive, colloquial, or visually unusual

Create `小编样本不足.md` for insufficient editors. Do not force personal DNA.

## Phase 5: Routing Skill

The final `SKILL.md` must route before writing:

1. Is the account style requested?
2. Is article type specified?
3. Is editor specified?
4. Is material sufficient?
5. Which DNA files should be loaded?

Routing rules:

- no type: infer from material or ask one concise question
- type only: account baseline + type DNA
- editor only: account baseline + editor DNA + inferred type
- type + editor: account baseline + type DNA + editor DNA
- insufficient editor samples: say so and fall back to account baseline + type DNA
- original-flavor request: load account baseline + type/editor DNA + the matching original-flavor fingerprint; never blend multiple editor fingerprints into one averaged voice

## Phase 6: Route Tests

Create `test-prompts.json` with at least:

- account baseline new draft
- major type new draft
- specified editor draft
- unspecified editor draft
- rewrite
- title optimization
- blind A/B route comparison
- strong-material positive control
- review diagnosis
- insufficient material
- sensitive fact handling
- "where does this not sound like us?"
- de-AI preservation: remove AI traces while preserving account/type/editor DNA
- structure metric regression: generated draft should match the routed account/type/editor paragraph rhythm, section shape, progression chain, and visual cadence
- original-flavor routing: same material routed to two editors or two article types should produce visibly different angle, rhythm, and wording without copying source prose
- false-match guard: reject a polished draft that uses account surface phrases but misses the routed type/editor thinking method

Each test includes:

- prompt
- input_materials
- route_expected
- expected_style_traits
- forbidden_outputs
- scoring_focus

## Phase 7: Reports

Deliver:

- `holdout-comparison-report.md`
- `原文差距矩阵.csv`
- `分类型评分.md`
- `分小编评分.md`
- `盲测评分记录.md`
- `darwin-scorecard.md`
- `darwin-optimization-log.md`
- `候选规则优化记录.md`
