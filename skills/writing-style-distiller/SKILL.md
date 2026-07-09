---
name: writing-style-distiller
description: Use when the user wants to 蒸馏/复刻/提炼 an author, public account, editor, 小编, company account, or person's writing style into a reusable writing Skill; triggers include 写作基因蒸馏, 作者风格复刻, 公众号多小编风格, 做成某某skill, 按某某写法写稿, 哪里不像某某, and generating a writing Skill with holdout/Darwin validation.
---

# Writing Style Distiller

## Goal

Create a reusable writing Skill that can write, rewrite, title, review, and diagnose drafts in the target's writing method. Analysis files are intermediate evidence; the acceptance test is whether the generated Skill can produce new drafts that match the target's writing DNA.

## Required Sub-Skills

Use these skills by name when available:

- **REQUIRED SUB-SKILL:** `huashu-nuwa` for thinking, selection logic, values, and anti-patterns.
- **REQUIRED SUB-SKILL:** `writing-dna-skill` for title, opening, structure, language, materials, transitions, ending, and visual rhythm.
- **REQUIRED SUB-SKILL:** `darwin-skill` for scoring, holdout comparison, and improvement loops.

Always integrate the local de-AI preservation layer after style DNA is built:

- read `references/de-ai-preserve-voice.md`
- generated writing Skills must include `去AI味保真补丁.md`
- generated `SKILL.md` must include a short `终稿去 AI 味保真补丁` section
- validation/验证 must include a de-AI preservation regression

If a sub-skill is not discoverable, read its local file before continuing:

- `huashu-nuwa`: `/Users/lixin/.openclaw/workspace/skills/nuwa-skill/SKILL.md`
- `writing-dna-skill`: `/Users/lixin/AI code/openclaw/skills/writing-dna-skill/SKILL.md`
- `darwin-skill`: `/Users/lixin/.openclaw/workspace/skills/darwin-skill/SKILL.md`

## Start

If target name, corpus path, or output skill name is missing, ask for only those missing fields. Otherwise execute.

Default output path:

```text
/Users/lixin/.openclaw/workspace/skills/<target-slug>-skill/
```

## Fidelity Target

Do not promise perfect replication. Treat "95%" as a high-fidelity certification target, not a default result.

If the user asks for 原汁原味, 本人味, 很像本人, 高保真, or "use the author's real writing method", run original-flavor mode:

- Preserve repeatable author quirks that have corpus evidence: angle reflexes, rough edges, punctuation habits, local phrases, paragraph rhythm, emotional temperature, source habits, and edit moves.
- Do not "improve" the voice into generic polished Chinese. Cleaner is worse if it lowers target fidelity.
- Build an `原味指纹.md` that separates thinking fingerprint, writing fingerprint, layout fingerprint, protected quirks, and false-match warnings.
- Build contrastive "像/不像" examples without copying source prose: target-like, generic AI-like, over-polished, and overfit/memorized.
- Run the GEPA-lite candidate loop in `references/validation.md` before claiming strong or high-fidelity results.

If the user asks for 95% fidelity, run high-fidelity mode:

- Require enough corpus support before certification: preferably 80+ complete articles, or mark the result as uncertified/prototype quality.
- Freeze holdout before distillation and keep original prose out of all generated DNA files.
- Validate writing process, not only surface style: topic choice, angle, material selection, structure, rhythm, editing moves, and risk handling.
- Validate non-template generalization: the Skill must keep the target's thinking and writing DNA across new topics without repeating fixed sentence molds, fixed judgments, or one-size-fits-all article structures.
- Claim 95% only when the high-fidelity gates in `references/validation.md` pass. Otherwise report the exact score and the weak dimensions.

## Route

1. If the corpus is one author/person/account voice, read `references/single-author.md`.
2. If one public account contains multiple editors or multiple article types, read `references/multi-editor-account.md`.
3. Always read `references/validation.md` before claiming the Skill is ready.

Do not average multiple editors into one voice. Use layered DNA: account baseline + article-type DNA + editor DNA when editor samples are sufficient.

## Core Workflow

1. Audit corpus and split holdout.
   - Build metadata: title, date, author/editor, article type, channel, word count, visual assets, train/holdout.
   - Traverse all complete articles to produce structure metrics: paragraph count per 1000 Chinese characters, median paragraph length, <=20-character short paragraph ratio, max consecutive <=20-character paragraph run, section count, title/opening/body/ending shapes, list/example/case density, visual break cadence, and common progression chains.
   - Store these as reusable writing constraints, not as decorative analysis; generated Skills must know when short paragraphs are real DNA and when they are mechanical AI fragmentation.
   - Keep 5-10 complete holdout articles out of training.
   - Mark `<30` complete articles as prototype quality.
2. Distill why the target writes this way.
   - With `huashu-nuwa`, extract selection logic, reader stance, content values, risk handling, anti-patterns, and evidence.
3. Distill how the target writes.
   - With `writing-dna-skill`, extract executable title, opening, structure, language, material, transition, ending, and visual rules.
   - Include the corpus-level structure metrics in `正文结构模板.md`, `语言DNA.md`, `视觉风格指南.md`, `像不像判别器.md`, and the final `SKILL.md` self-check.
   - Separate thinking DNA from writing DNA and layout DNA: why they choose an angle, how they organize judgment, how they paragraph and pace the article.
4. Convert the findings into a writing process.
   - Produce operational rules for choosing topics, shaping angles, selecting material, outlining, drafting, revising, and rejecting non-target output.
   - Produce `原味指纹.md`: what must survive generation, what must survive de-AI, what is only occasional, and what is banned as false imitation.
5. Generate the writing Skill.
   - `SKILL.md` must be short, triggerable, and operational.
   - Put detailed DNA files beside it, not all inline.
   - Include `去AI味保真补丁.md`.
   - Add a final-pass de-AI hook that preserves the target's thinking framework, writing DNA, facts, and article quality.
6. Validate with holdout and `darwin-skill`.
   - Generate drafts from holdout topics/materials without exposing original prose.
   - Compare against originals, no-skill baseline, and previous skill versions.
   - Optimize only rules that improve holdout scores without lowering fact reliability or non-impersonation compliance.
   - Use GEPA-lite candidate updates for stubborn "not like target" gaps: generate 3 small rule patches, test them against holdout, keep only Pareto-improving rules.
   - Run at least one de-AI preservation regression: remove obvious AI traces without lowering style fidelity.

## Quality Gates

Ready means all gates pass:

- OpenClaw can discover `SKILL.md`.
- `darwin-skill` score is at least 85, or the final answer states why not.
- Holdout average is at least 8.0/10, or the final answer states weak dimensions.
- Structure metrics are present and used: paragraph rhythm, section shape, progression chain, and visual cadence are compared against the source corpus, not guessed from a few examples.
- `原味指纹.md` exists and is used by the generated Skill's self-check when original-flavor mode is requested.
- Facts reliability is at least 9.5/10.
- Non-impersonation compliance is 10/10.
- The Skill can diagnose "哪里不像" with concrete fixes and produce an edited version.
- The Skill includes `去AI味保真补丁.md`, and its de-AI pass does not reduce holdout style fidelity, fact reliability, or non-template variation.
- If high-fidelity mode was requested, the final answer must say whether the 95% gates passed, failed, or could not be certified from the corpus.

## Prohibitions

- Do not present style analysis as the final product.
- Do not copy original paragraphs into the Skill.
- Do not invent facts to sound like the target.
- Do not impersonate the target as the real author.
- Do not use vague advice like "更有温度/更有逻辑" unless followed by concrete line-level rewriting rules.
- Do not raise scores by forcing formulaic titles, repeated paragraph shapes, fixed judgments, or a single reusable writing template across unrelated topics.
- Do not raise "human feel" by flattening the target's real DNA into generic natural Chinese.
- Do not delete author-specific awkwardness, bluntness, repetition, slang, punctuation, or layout habits when the corpus proves they are real DNA and they do not harm facts or safety.
