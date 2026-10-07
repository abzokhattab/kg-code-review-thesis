# Bootstrap CIs + paired permutation tests — v2 (25 PRs, cleaned + expansion)

**Input:** `results/checklist_evaluation_llm_multi__v2.json`  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026.

## Per-mode mean scores with 95% bootstrap CI

| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |
|---|---:|---:|---:|
| baseline | 25 | 8.96 [8.44, 9.52] | 5.00 [4.60, 5.40] |
| kg | 25 | 9.28 [8.64, 9.96] | 5.36 [4.92, 5.80] |
| rag | 25 | 9.52 [9.00, 10.08] | 5.36 [4.88, 5.84] |
| hybrid | 25 | 9.88 [9.28, 10.48] | 5.72 [5.40, 6.00] |

## Paired differences vs baseline (mode − baseline, same PR)

| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 25 | +0.32 [-0.44, +1.12] | 0.492 | +0.16 | +0.36 [-0.16, +0.88] | 0.255 | +0.27 |
| rag | 25 | +0.56 [-0.04, +1.20] | 0.128 | +0.34 | +0.36 [-0.16, +0.92] | 0.263 | +0.26 |
| hybrid | 25 | +0.92 [+0.24, +1.60] | 0.020 | +0.53 | +0.72 [+0.28, +1.20] | 0.009 | +0.60 |

## Interpretation key

- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.
- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.
- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).
