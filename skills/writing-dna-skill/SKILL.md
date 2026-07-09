---
name: writing-dna-skill
description: Distill reusable writing style rules from a corpus of complete articles. Use when the user wants to analyze 30+ complete articles and extract language DNA, article structures, topic logic, material strategy, cognitive frame, visual style, and a Writing-DNA.md document for style-consistent writing.
---

# 写作蒸馏器

Use this skill to distill a reusable Writing DNA from a corpus of complete articles. Do not summarize the articles; extract the rules that make the writing style repeatable.

## Corpus Requirements

Require enough source material before claiming a reliable style:

- Use at least 30 complete articles.
- Prefer 80-100 complete articles for stronger results.
- Prefer articles longer than 1000 Chinese characters or words each.
- Use `.md` or `.txt` files in `raw/` or `raw-corpus/`.
- Do not place unauthorized source articles in a public repository.

If the corpus is small, explain that the output is only a format or workflow demo, not a reliable style distillation.

## Workflow

1. Inspect the corpus and create `_meta/` records for each article: title, date, author/account, article type, topic tags, hook type, structure pattern, source types, word count, and notable traits.
2. Extract L1 surface language: frequent nouns, verbs, adverbs, sentence length, short/long sentence ratio, paragraph rhythm, punctuation, title style, and mixed-language habits. Write `语言DNA.md`.
3. Extract L2 article structure: opening hook, first turn, body architecture, section rhythm, transition style, and ending pattern. Write `文章结构模板.md`.
4. Extract L3-L5 thinking rules: topic selection logic, timing, angles, material strategy, preferred authority or evidence, recurring assumptions, values, and core propositions. Write `写作视角与认知框架.md`.
5. Extract L6 visual style when the source contains images or formatting: image type, placement rhythm, screenshot/evidence role, typography hierarchy, emphasis, color, layout density, and text-image collaboration. Write `视觉风格指南.md`.
6. Extract an anti-AI preservation pass. Write `去AI味保真补丁.md`: list which AI traces should be cleaned, which target-style patterns must be preserved, which paragraph rhythms are real DNA, when continuous short paragraphs should be merged, and which de-AI edits would damage the author's DNA.
7. Integrate the outputs into `Writing-DNA.md`, keeping it concise enough for an agent to reread before writing.

For image-heavy articles, open and inspect images. Screenshots, comments, charts, and conversation images may carry evidence that is not present in the text.

## Output Files

Produce these files in the corpus directory:

```text
_meta/
语言DNA.md
文章结构模板.md
写作视角与认知框架.md
视觉风格指南.md
去AI味保真补丁.md
Writing-DNA.md
```

Use `templates/author-corpus/` as the recommended directory template. Read `写作蒸馏器.skill.md` for the full public-facing workflow when detailed instructions are needed.

## Writing With A Distilled Style

Before writing in a distilled style, reread all style documents, especially `Writing-DNA.md`, `语言DNA.md`, `文章结构模板.md`, `写作视角与认知框架.md`, `视觉风格指南.md`, and `去AI味保真补丁.md`. Then follow the target style while avoiding misleading impersonation.

## 终稿去 AI 味保真补丁

When generating a writing Skill from this DNA, include a final-pass hook to `/Users/lixin/.openclaw/workspace/skills/de-ai-preserve-voice/SKILL.md`.

The hook must say:

- the target author's style DNA outranks generic de-AI rules;
- only obvious AI traces are patched;
- facts, source material, argument order, and distinctive sentence habits are protected;
- paragraph rhythm is protected: short paragraphs are preserved where they function as pause, punchline, turn, or section promise, but continuous same-function micro-paragraphs are merged back toward the source corpus rhythm; if normal prose becomes mostly under-20-character paragraphs, re-check against the source corpus instead of treating fragmentation as style;
- list, example, method, and parallel phrases at the same level should not become one micro-paragraph per item unless the source corpus really does that; merge them into a natural paragraph or an explicit list;
- author-specific patterns are not banned just because generic de-AI guides dislike them;
- if the de-AI pass makes the draft less like the target, rollback that edit.
