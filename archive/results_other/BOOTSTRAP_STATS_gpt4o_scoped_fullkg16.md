# Bootstrap CIs + paired permutation tests — gpt4o_scoped_fullkg16

**Input:** `results/checklist_evaluation_llm_multi__gpt4o_scoped_fullkg16.json`  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026.

## Per-mode mean scores with 95% bootstrap CI

| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |
|---|---:|---:|---:|
| baseline | 16 | 8.25 [7.44, 9.12] | 4.25 [3.38, 5.06] |
| kg | 16 | 8.56 [7.88, 9.25] | 4.69 [4.19, 5.19] |
| rag | 16 | 8.56 [7.88, 9.19] | 4.94 [4.38, 5.50] |
| hybrid | 16 | 9.12 [8.31, 9.94] | 5.25 [4.50, 6.00] |

## Paired differences vs baseline (mode − baseline, same PR)

| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 16 | +0.31 [-0.38, +1.00] | 0.500 | +0.22 | +0.44 [-0.31, +1.19] | 0.345 | +0.28 |
| rag | 16 | +0.31 [-0.56, +1.19] | 0.585 | +0.17 | +0.69 [-0.19, +1.56] | 0.207 | +0.36 |
| hybrid | 16 | +0.88 [-0.06, +1.81] | 0.128 | +0.44 | +1.00 [+0.25, +1.69] | 0.032 | +0.65 |

## Interpretation key

- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.
- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.
- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).
