# Validation And Optimization

Use this before claiming the generated writing Skill is ready.

## Fidelity Modes

Use explicit labels instead of vague claims:

- `prototype`: corpus is small or uneven; useful for workflow demos, not reliable style replication.
- `ready`: passes the standard gates below.
- `strong`: holdout average >= 9.0 and no core style dimension < 8.5.
- `original_flavor`: requested 原汁原味/本人味; requires an original-flavor fingerprint, contrastive like/unlike tests, and GEPA-lite candidate optimization.
- `high_fidelity_95`: a stretch target. Claim it only if every high-fidelity gate passes.

If the user asks for "95%", run `high_fidelity_95`. If any gate fails, say "not certified at 95%" and report the weakest dimensions.
If the user asks for 原汁原味, run `original_flavor` even when they do not say 95%.

## Test Set

Create `test-prompts.json` with at least 22 tests:

1. new draft writing
2. rewrite
3. title optimization
4. opening optimization
5. ending optimization
6. review diagnosis
7. expansion
8. compression
9. insufficient material
10. sensitive facts
11. same material, two angles
12. "where does this not sound like the target?"
13. strong-material positive control
14. no-skill baseline comparison
15. style leakage / memorization check
16. blind A/B judge comparison
17. cross-topic generalization
18. anti-template variation check
19. de-AI preservation check: remove obvious AI traces without lowering target-style fidelity, fact reliability, or non-template variation
20. original-flavor contrast: distinguish target-like output from generic AI, over-polished, and overfit/memorized variants
21. thinking-frame transfer: same material, judge whether the angle/material hierarchy matches the target's usual judgment method
22. protected-quirk preservation: rewrite an intentionally polished draft while restoring only corpus-proven quirks

Each test object:

```json
{
  "id": "t01",
  "prompt": "",
  "input_materials": "",
  "expected_style_traits": [],
  "forbidden_outputs": [],
  "scoring_focus": []
}
```

For multi-editor accounts, also include `route_expected`.

## Holdout Method

For each holdout article:

1. Freeze holdout before distillation and record it in `holdout-eval-list.md`.
2. Extract topic, title, opening, body structure, core view, materials, rhythm, transitions, ending, and layout.
   Also record structure metrics from the original: paragraph count per 1000 Chinese characters, median paragraph length, <=20-character short paragraph ratio, max consecutive <=20-character paragraph run, section count, progression chain, and visual break cadence.
   Also record an example-free original-flavor fingerprint: angle reflex, judgment chain, evidence priority, protected quirks, emotional temperature, and false-match warnings.
3. Do not give the original prose to the generated Skill, generated DNA files, or test prompts.
4. Give only the same topic/task/basic materials.
5. Generate a new draft.
6. Generate a no-skill baseline from the same prompt.
7. Compare output with the original after generation.
8. Record any accidental exposure in `holdout-leakage-log.md`. Any leaked holdout article is removed from certification.

## Score Dimensions

Use 0-10 scores:

- title similarity
- opening similarity
- body structure similarity
- structure metric similarity
- language rhythm similarity
- material-use similarity
- viewpoint organization similarity
- writing-process similarity
- original-flavor fingerprint match: angle reflex, judgment chain, protected quirks, and emotional temperature match without copying prose
- non-template variation
- de-AI preservation: AI traces reduced without flattening the target's writing DNA
- paragraph/structure regression: paragraph rhythm, section shape, progression chain, and visual cadence stay inside the source-corpus range unless the user explicitly asks for a different format
- transition similarity
- ending similarity
- overall reading feel
- fact reliability
- non-impersonation compliance

For multi-editor accounts also score:

- account baseline similarity
- article-type similarity
- editor similarity when applicable
- route correctness

## Darwin / GEPA-Lite Loop

Use `darwin-skill` after baseline holdout scoring.

Each round:

1. Read `holdout-comparison-report.md`.
2. Find the 1-3 biggest causes of "not like target".
3. Create 3 small candidate rule patches, not a full rewrite:
   - thinking patch: angle selection, material priority, judgment chain, risk handling
   - structure patch: opening, section order, paragraph rhythm, visual cadence
   - voice patch: diction, sentence rhythm, protected quirks, de-AI exemptions
4. Test each candidate separately on affected holdout items plus tests 12, 17, 18, 19, 20, 21, and 22.
5. Keep a candidate only if it improves at least one weak dimension without lowering fact reliability, non-impersonation compliance, leakage safety, or non-template variation.
6. Merge only Pareto-winning rules: if one patch improves voice but hurts structure, keep it only for the routed context where it wins.
7. Write the decision to `候选规则优化记录.md`: candidate, changed rule, improved dimension, harmed dimension, keep/reject.
8. Stop after 3 rounds or two consecutive rounds with less than 2 points improvement.

Do not use GEPA-lite to create more templates. It exists to learn sharper rules from failure traces, not to force a single winning article skeleton.

## Original-Flavor Gates

Use these gates when the user asks for 原汁原味, 本人味, 很像本人, or high-fidelity writing.

- `原味指纹.md` exists and separates thinking fingerprint, writing fingerprint, layout fingerprint, protected quirks, false-match warnings, and de-AI exemptions
- holdout original-flavor fingerprint match >= 8.5
- tests 20, 21, and 22 pass
- blind A/B judges prefer the skill output over no-skill baseline in at least 80% of original-flavor comparisons
- protected quirks are evidence-backed and not copied from holdout prose
- over-polished output is rejected when it lowers fingerprint match
- overfit/memorized output is rejected even if it sounds close

## High-Fidelity 95 Gates

Use these gates only when the user requested 95% replication:

- corpus supports certification: preferably 80+ complete training articles and 10 clean holdout articles; otherwise mark as `not certified at 95%`
- holdout average >= 9.5
- title/opening/structure/language/material/process averages >= 9.0
- paragraph/structure metric similarity >= 9.0 and no repeated paragraph skeletons across unrelated topics
- original-flavor fingerprint match >= 9.2
- non-template variation >= 9.0: repeated formulas, repeated paragraph skeletons, or fixed judgment chains across unrelated topics fail this gate
- no individual clean holdout article < 8.8 overall
- generated output beats the no-skill baseline in at least 80% of blind A/B comparisons
- "where does this not sound like the target?" identifies the same top gap as the holdout report in at least 80% of tested cases
- de-AI preservation check passes on at least 3 prompts without reducing title/opening/structure/language/material/process averages
- fact reliability >= 9.8
- non-impersonation compliance = 10
- leakage check passes: no original holdout prose copied into prompts, DNA files, or generated drafts
- GEPA-lite or equivalent candidate-rule optimization was run and `候选规则优化记录.md` shows only keep-if-better changes

## Ready Gates

The Skill is ready only if:

- OpenClaw discovers `SKILL.md`
- `darwin-skill` final score >= 85
- holdout average >= 8.0
- title/opening/structure/language/material averages >= 7.5
- paragraph/structure metric similarity >= 7.5
- original-flavor gates pass when original flavor was requested
- non-template variation >= 7.5
- fact reliability >= 9.5
- non-impersonation compliance = 10
- "哪里不像" diagnosis gives concrete fixes and a revised draft
- de-AI preservation check passes: facts unchanged, target DNA preserved, and generic AI traces reduced

If a gate fails, report the exact weak dimension and what corpus is needed next.
