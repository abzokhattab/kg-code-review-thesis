# Bootstrap CIs + paired permutation tests — v2 (40 PRs, cleaned + expansion)

**Input:** `results/checklist_evaluation_llm_multi__v2.json`  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026.

## Per-mode mean scores with 95% bootstrap CI

| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |
|---|---:|---:|---:|
| baseline | 40 | 9.20 [8.70, 9.70] | 4.97 [4.67, 5.28] |
| kg | 40 | 9.82 [9.28, 10.43] | 5.58 [5.22, 5.95] |
| rag | 40 | 10.07 [9.57, 10.60] | 5.40 [5.00, 5.78] |
| hybrid | 40 | 9.93 [9.47, 10.38] | 5.50 [5.22, 5.78] |

## Paired differences vs baseline (mode − baseline, same PR)

| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 40 | +0.62 [+0.05, +1.20] | 0.054 | +0.33 | +0.60 [+0.23, +0.97] | 0.007 | +0.47 |
| rag | 40 | +0.88 [+0.30, +1.45] | 0.007 | +0.47 | +0.42 [+0.05, +0.82] | 0.057 | +0.33 |
| hybrid | 40 | +0.72 [+0.10, +1.35] | 0.037 | +0.36 | +0.53 [+0.17, +0.90] | 0.008 | +0.46 |

## Interpretation key

- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.
- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.
- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).
