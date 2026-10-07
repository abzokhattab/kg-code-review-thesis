# Bootstrap CIs + paired permutation tests — v2 (18 PRs, cleaned dataset)

**Input:** `results/checklist_evaluation_llm_multi__v2.json`  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026.

## Per-mode mean scores with 95% bootstrap CI

| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |
|---|---:|---:|---:|
| baseline | 18 | 8.94 [8.22, 9.67] | 5.00 [4.50, 5.50] |
| kg | 18 | 9.33 [8.61, 10.11] | 5.33 [4.83, 5.83] |
| rag | 18 | 9.44 [8.83, 10.11] | 5.39 [4.89, 5.94] |
| hybrid | 18 | 9.83 [9.17, 10.56] | 5.61 [5.28, 5.94] |

## Paired differences vs baseline (mode − baseline, same PR)

| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 18 | +0.39 [-0.56, +1.33] | 0.500 | +0.19 | +0.33 [-0.28, +0.94] | 0.391 | +0.25 |
| rag | 18 | +0.50 [-0.22, +1.22] | 0.263 | +0.31 | +0.39 [-0.11, +0.89] | 0.223 | +0.36 |
| hybrid | 18 | +0.89 [+0.17, +1.61] | 0.054 | +0.53 | +0.61 [+0.11, +1.11] | 0.049 | +0.56 |

## Interpretation key

- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.
- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.
- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).
