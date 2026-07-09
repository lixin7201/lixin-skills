# Original-Flavor Blind A/B Full Test

日期：2026-07-09

## 范围

- 8 个冻结 holdout prompt
- `t20` 原味对照判断
- `t21` 思考框架迁移
- `t22` 保护瑕疵/改回原味

## 隔离

- with-skill：`main` agent + `/datudou-skill`
- baseline：`test` agent，无 `datudou-skill`
- judges：`test` / `pm` / `dev` 三个独立 agent，均无 `datudou-skill`
- A/B 标签：固定随机种子 `20260709`
- holdout 正文：生成和评审阶段均未提供

## 结果

| 指标 | 结果 |
|---|---:|
| skill item-majority | 9/11 = 81.8% |
| skill vote-level | 28/33 = 84.8% |
| baseline item-majority | 2/11 |
| tie item-majority | 0/11 |
| 80% blind gate | PASS |
| leakage check | PASS |

## 弱项

- `t20` baseline 胜出：判别口径更完整，尤其是“过拟合假像”和判断边界。
- `t22` baseline 胜出：自然段、冷感和不过度修饰更稳。

## 证据文件

- `holdout/blind-ab-20260709/protocol.md`
- `holdout/blind-ab-20260709/blind-packet-for-judges.md`
- `holdout/blind-ab-20260709/scores.csv`
- `holdout/blind-ab-20260709/summary.md`
- `holdout/blind-ab-20260709/leakage-check.md`
