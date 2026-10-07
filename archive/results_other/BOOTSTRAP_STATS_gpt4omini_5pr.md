# Bootstrap CIs + paired permutation tests — gpt-4o-mini · 5 PRs · 3-judge majority vote

**Input:** `results/checklist_evaluation_llm_multi__gpt4omini_sample.json`  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026.

## Per-mode mean scores with 95% bootstrap CI

| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |
|---|---:|---:|---:|
| baseline | 5 | 10.80 [9.20, 12.20] | 6.00 [5.40, 6.60] |
| kg | 5 | 9.80 [8.20, 11.60] | 5.00 [4.20, 5.80] |
| rag | 5 | 9.80 [8.20, 11.60] | 5.80 [4.60, 7.20] |
| hybrid | 5 | 10.00 [8.00, 11.80] | 5.20 [5.00, 5.60] |

## Paired differences vs baseline (mode − baseline, same PR)

| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 5 | -1.00 [-3.20, +0.80] | 0.625 | -0.39 | -1.00 [-2.00, -0.20] | 0.250 | -0.82 |
| rag | 5 | -1.00 [-3.60, +1.20] | 0.750 | -0.32 | -0.20 [-1.80, +1.80] | 1.000 | -0.09 |
| hybrid | 5 | -0.80 [-3.00, +0.80] | 0.875 | -0.32 | -0.80 [-1.40, -0.20] | 0.250 | -0.96 |

## Interpretation key

- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.
- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.
- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).
