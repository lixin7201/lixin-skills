# De-AI Preservation Regression

## Test

Input: a generic AI-style draft containing “本文将从”“综上所述”“值得我们深思”等 phrases.

Expected:

- remove roadmap and empty summary;
- preserve half-monthly-talk warning words and governance vocabulary;
- preserve facts and source boundaries;
- keep the selected article type route;
- do not flatten the draft into generic natural Chinese.

## Dry-run Result

- facts unchanged: pass
- source leakage removed: pass
- target DNA preserved: pass
- paragraph rhythm warning included: pass
