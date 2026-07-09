# Single Author / Single Voice Workflow

Use this when the corpus is one author, one editor, one expert, or one coherent account voice.

## Inputs

- target_name
- target_type
- corpus_path
- output_skill_name
- output_dir

## Phase 0: Corpus Audit

Create:

- `语料质量报告.md`
- `training-corpus-list.md`
- `holdout-eval-list.md`
- `结构与段落指标.md`
- `原味语料分层.md`

Audit:

- total articles, complete articles, long/short ratio
- time span and content type coverage
- title/body/subtitle/visual preservation
- image, screenshot, chart, table, layout evidence
- whether the corpus can support stable distillation
- corpus strata: best-known pieces, ordinary pieces, weak/atypical pieces, early/recent pieces, high-engagement pieces if metrics exist
- repeated quirks versus one-off accidents: wording, punctuation, roughness, local slang, paragraph breaks, opening moves, and emotional temperature

Traverse every complete article, not only selected examples, and record structure metrics:

- paragraph count per 1000 Chinese characters
- median/mean paragraph length
- <=20-character and <=30-character paragraph ratios
- max consecutive <=20-character paragraph run
- section count and common section order
- opening shape, body progression chain, ending shape
- list/case/example/question density
- visual break cadence: images, screenshots, charts, dividers, captions, bold, quote blocks
- when short paragraphs are real author DNA, and when same-level facts/examples/methods are normally merged

Do not train only on "best" pieces unless the user explicitly asks for 爆款风格. 原汁原味 needs a representative author fingerprint, including ordinary cadence and real rough edges.

Hold out 5-10 complete articles before distillation. Do not use holdout prose during training.

## Phase 1: Why They Write This Way

Use `huashu-nuwa` to produce:

- `写稿判断框架.md`
- `选题判断清单.md`
- `读者画像与默认立场.md`
- `内容价值观.md`
- `反模式与诚实边界.md`
- `写稿流程操作手册.md`
- `证据索引.md`

Extract:

- what makes a topic worth writing
- default reader and reader pain
- preferred angle: person, event, benefit, conflict, trend, service, emotion, local relationship
- material priority and rejected material
- fact/risk handling
- when the voice becomes restrained or strong
- how the target moves from material to angle, outline, draft, revision, and final title
- how the target keeps a stable worldview while varying article shape, sentence rhythm, and judgment path across unrelated topics
- the target's angle reflex: which part of a messy topic they notice first, what they ignore, what they delay, and what they refuse to conclude
- the target's edit reflex: what they usually cut, soften, intensify, reorder, repeat, or leave deliberately rough
- what never sounds like the target

## Phase 2: How They Write

Use `writing-dna-skill` to produce:

- `标题DNA.md`
- `开头模板.md`
- `正文结构模板.md`
- `语言DNA.md`
- `素材使用规则.md`
- `转折与推进规则.md`
- `结尾模板.md`
- `视觉风格指南.md`
- `像不像判别器.md`
- `Writing-DNA.md`
- `原味指纹.md`
- `像不像对照样本.md`

Each rule needs evidence, reusable instruction, anti-example, and an output implication.

Minimum required content:

- 10-20 title formulas with scenarios
- 5-10 opening templates
- 3-7 body structures
- common phrase library and banned phrase library
- ordinary AI style replacement table
- `去AI味保真补丁.md`: target-specific AI traces, protected author DNA, and de-AI rollback rules
- material priority table
- structure metric table: paragraph rhythm, section shape, progression chain, and visual cadence, with source-corpus ranges and generated-draft warning thresholds
- draft revision checklist: what to cut, intensify, soften, reorder, or fact-check
- anti-template variation rules: allowed reusable patterns, banned repeated sentence molds, and how to vary structure by topic
- transition templates
- ending templates
- visual rhythm and layout rules
- protected quirks table: keep / soften / remove, with evidence count and example-free description
- false-match table: surface habits that look similar but are not the target's real method
- contrastive examples: target-like vs generic AI-like vs over-polished vs overfit/memorized, using synthetic wording only

Keep `Writing-DNA.md` under 5000 words and operational.

## Phase 3: Build the Skill

Create `<output_dir>/SKILL.md`.

The final Skill must support:

- new draft writing
- rewriting an existing draft
- original-flavor drafting: maximize target fidelity without copying source prose
- title optimization
- opening/ending optimization
- review and diagnosis
- style unification
- expansion/compression
- "where does this not sound like the target?"

`SKILL.md` must include:

- clear frontmatter name and trigger-rich description
- trigger phrases in Chinese
- material sufficiency check
- route by task type
- links to DNA files
- output self-check
- `原味指纹.md` self-check before final answer when the user asks for 原汁原味 or high fidelity
- concrete prohibitions

Detailed DNA belongs in adjacent `.md` files, not all inside `SKILL.md`.

## Phase 4: Final Files

Deliver at least:

- `SKILL.md`
- `去AI味保真补丁.md`
- `原味指纹.md`
- `像不像对照样本.md`
- all Phase 1 and Phase 2 files
- `test-prompts.json`
- `holdout-comparison-report.md`
- `holdout-leakage-log.md`
- `原文差距矩阵.csv`
- `盲测评分记录.md`
- `darwin-scorecard.md`
- `darwin-optimization-log.md`
- `候选规则优化记录.md`
