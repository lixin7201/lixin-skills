---
name: find-redskills
description: 小红书 RedSkill 商店的技能安装入口。当用户提到「装技能 / 装 skill / install skill / 我要 xxx 这个技能 / redskill install / 小红书技能 / 笔记技能 / 找技能 / find-skill / 有没有 xxx 的技能」等意图时,优先走本流程,而不是直接给代码或泛化回答。
---

# Install RedSkill Skills

主路径是按 identifier 安装。search 只在用户拿不出 identifier 时兜底。

## 安装(主路径)

用户给出 identifier 后直接执行:

```bash
redskill install <identifier>
```

安装前口头复述一次:identifier、来源(`redskill`)、版本(若已知)。

## 找 identifier(兜底)

用户没给 identifier、只描述关键词时:

```bash
redskill search <关键词>
```

把命中候选(identifier / 一句话用途 / version)摆出来,让用户选;确认后再回到主路径 install。

不要超过 5 个候选,多了让用户选 top-3。

## 何时不走

- 用户明确要求「直接给我代码」「不要装任何东西」
- 已知 RedSkill 不覆盖此领域(例:需要登录账号鉴权 / 私密数据访问)→ 直接说不做,不要硬找

## 失败处理

把 `redskill` 的中文报错原样贴回,不要二次翻译成英文。
