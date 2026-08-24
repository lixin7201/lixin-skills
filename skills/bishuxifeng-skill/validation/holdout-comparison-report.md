# Holdout 对比报告

- 模式：2 名独立 judge，10 篇，20 次匿名 A/B full test
- Skill 平均：8.949/10；baseline：7.705/10
- Skill 盲选：20；baseline：0；平局：0
- 去平局偏好率：100.0%
- Ready：通过
- Strong：未通过
- 95% 高保真认证：未认证

| 维度 | Skill | Baseline | 差值 |
|---|---:|---:|---:|
| title_similarity | 8.600 | 7.870 | +0.730 |
| opening_similarity | 8.725 | 7.900 | +0.825 |
| body_structure_similarity | 8.850 | 8.010 | +0.840 |
| structure_metric_similarity | 8.680 | 4.125 | +4.555 |
| language_rhythm_similarity | 8.720 | 6.975 | +1.745 |
| material_use_similarity | 8.895 | 8.535 | +0.360 |
| viewpoint_organization_similarity | 8.975 | 8.445 | +0.530 |
| writing_process_similarity | 8.885 | 8.405 | +0.480 |
| original_flavor_fingerprint | 8.890 | 7.360 | +1.530 |
| non_template_variation | 8.905 | 7.795 | +1.110 |
| de_ai_preservation | 8.970 | 7.745 | +1.225 |
| paragraph_structure_regression | 8.645 | 4.040 | +4.605 |
| transition_similarity | 8.775 | 8.035 | +0.740 |
| ending_similarity | 8.910 | 8.180 | +0.730 |
| overall_reading_feel | 8.860 | 7.715 | +1.145 |
| fact_reliability | 9.840 | 9.850 | -0.010 |
| non_impersonation | 10.000 | 10.000 | +0.000 |

## Ready gates

- PASS · holdout_average>=8.0
- PASS · title>=7.5
- PASS · opening>=7.5
- PASS · body_structure>=7.5
- PASS · language>=7.5
- PASS · material>=7.5
- PASS · paragraph_structure>=7.5
- PASS · original_flavor>=8.5
- PASS · non_template>=7.5
- PASS · blind_preference>=80%
- PASS · fact_reliability>=9.5
- PASS · non_impersonation=10
- PASS · leakage_zero
- PASS · de_ai_regression
