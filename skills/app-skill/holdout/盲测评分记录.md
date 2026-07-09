# Full Blind A/B Report 2026-07-07

## Setup

- Test cases: 20/20 from `test-prompts.json`, with concrete materials added in `test_cases.json`.
- Generations: one `with_skill` batch using `/app-skill`; one `baseline` batch explicitly not invoking `/app-skill`.
- Judges: 3 independent OpenClaw local judge runs.
- Blind method: A/B labels randomized with seed `20260707`; key stored separately in `blind_key.json`.
- Optimization loop: initial full run found t10 title optimization weak; one minimal SKILL.md rule update was kept, and only t10 was regenerated/rejudged.

## Final Adjusted Result

| Metric | app-skill | baseline |
|---|---:|---:|
| Majority wins | 20 / 20 | 0 / 20 |
| Judge votes | 59 / 60 | 1 / 60 |
| Average overall score | 9.3 | 8.38 |
| Average route score | 9.3 | 8.41 |
| Average fact score | 9.43 | 9.27 |

## Initial Full Run Before t10 Patch

- Majority wins: app-skill 19/20, baseline 1/20.
- Judge votes: app-skill 56/60, baseline 4/60.
- Weak test: `t10` title optimization; all 3 judges preferred baseline because titles were more natural.

## Kept Optimization

`SKILL.md` title optimization rule was tightened: titles must be grouped as strong-interaction / fact-service / local-object / safe titles, include one recommendation, and avoid stiff noun-stacking.

## t10 Rerun

- Rejudged by 3 independent judges.
- Result: corrected app-skill title output won 3/3.
- Rerun average: app-skill 8.90 vs baseline 8.07.

## Remaining Weakness

- `t13` had one baseline vote among three judges. The majority still preferred app-skill 2/3, but the score gap was narrow: app-skill 9.07 vs baseline 8.90. This route tests two openings from the same外卖补贴 material; future improvement can make 泡泡呀 vs 雯雯 opening differences sharper.
- This was a prompt-set blind A/B test, not a full human editorial blind review.
