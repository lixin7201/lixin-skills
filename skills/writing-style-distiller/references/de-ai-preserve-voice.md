# De-AI Preserve Voice Integration

Use this reference when generating or updating a writing Skill.

## Required Asset

Every generated writing Skill must include a file named:

```text
去AI味保真补丁.md
```

This file is not a generic polishing guide. It is a final-pass guardrail that protects the target writing DNA while removing obvious AI traces.

## What To Extract From The Corpus

Record:

- which phrases, structures, transitions, section shapes, punctuation habits, and title formulas are real target DNA;
- which patterns look like AI traces and should be cleaned;
- which awkward, blunt, repetitive, colloquial, uneven, or visually unusual patterns are protected original flavor rather than defects;
- which paragraph rhythms are real DNA, including normal paragraph length, short-paragraph use cases, and when adjacent short lines should stay separate;
- which source-attribution phrases are real journalistic/source language, and which are generation-process leaks such as “资料中提到、原文中提到、根据你提供的素材、文中写到”;
- which generic de-AI rules would harm the target style and must be exempted;
- which facts, numbers, quotes, local anchors, source labels, and author/editor boundaries must be protected;
- how to rollback a de-AI edit when it makes the draft less like the target.

## Required Section In Generated SKILL.md

Add a short section named:

```markdown
## 终稿去 AI 味保真补丁
```

It must say:

1. Execute `/Users/lixin/.openclaw/workspace/skills/de-ai-preserve-voice/SKILL.md` only after the draft is already written in the target skill's DNA.
2. The target skill's writing DNA, thinking framework, article type, editor route, and user-provided facts outrank generic de-AI rules.
3. Patch only the most obvious AI traces, such as roadmap sentences, empty summary, unsourced authority, mechanical contrast, fake first-person, generic uplift, source-material leakage, and same-shaped paragraphs.
4. Preserve the target's real paragraph rhythm. Short paragraphs may be DNA, but continuous micro-paragraphs should be merged when they carry the same fact, explanation, case, method, parallel-list, or same-level example function. If more than half of normal prose paragraphs are under 20 Chinese characters, treat it as a warning and re-check whether the explanation chain was mechanically fragmented.
5. Remove source-material leakage. Do not write “资料中提到、原文中提到、根据你提供的素材、文中写到、上面说到” in the final draft; convert provided materials into the target author's own narration. Keep source language only when it names a real source, such as public records, regulator notices, platform announcements, merchant pages, or reporting.
6. Do not remove author-specific patterns unless they are mechanically overused and no longer advance the draft.
7. Do not normalize protected original flavor into smooth platform prose. Keep corpus-proven awkwardness, bluntness, repetition, colloquial phrasing, punctuation, and layout habits when they improve target fidelity.
8. If the de-AI pass lowers style fidelity, fact reliability, original-flavor fingerprint match, or article quality, rollback that edit.

## Validation

Add at least one test prompt that asks the Skill to remove AI traces while preserving the target voice.

The test passes only if:

- facts and source boundaries are unchanged;
- the main argument and target article shape are preserved;
- the target's distinctive sentence habits are not flattened;
- paragraph rhythm is closer to the source corpus, not mechanically broken into one sentence per paragraph;
- validation checks median paragraph length, under-20-character paragraph ratio, and max consecutive under-20-character paragraph run against the source corpus;
- protected original-flavor quirks remain when they are evidence-backed and safe;
- source-material leakage is removed: the draft reads as direct author narration, while real news/source attribution remains accurate;
- AI traces are reduced;
- the output is not a generic "natural Chinese" rewrite.
