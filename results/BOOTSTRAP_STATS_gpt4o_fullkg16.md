# Bootstrap CIs + paired permutation tests — GPT-4o · 25-PR run filtered to FULL_KG subset (n=16) · unscoped AST

**Input:** `results/checklist_evaluation_llm_multi__fullkg16.json`  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026.

## Per-mode mean scores with 95% bootstrap CI

| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |
|---|---:|---:|---:|
| baseline | 16 | 8.69 [7.88, 9.50] | 4.62 [3.75, 5.50] |
| kg | 16 | 8.69 [7.81, 9.56] | 5.00 [4.62, 5.38] |
| rag | 16 | 8.69 [8.06, 9.31] | 5.06 [4.38, 5.75] |
| hybrid | 16 | 8.31 [7.31, 9.44] | 4.44 [3.75, 5.12] |

## Paired differences vs baseline (mode − baseline, same PR)

| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 16 | +0.00 [-0.88, +0.94] | 1.000 | +0.00 | +0.38 [-0.31, +1.12] | 0.443 | +0.24 |
| rag | 16 | +0.00 [-0.56, +0.56] | 1.000 | +0.00 | +0.44 [-0.19, +1.06] | 0.292 | +0.32 |
| hybrid | 16 | -0.38 [-1.31, +0.56] | 0.532 | -0.19 | -0.19 [-0.88, +0.44] | 0.725 | -0.14 |

## Interpretation key

- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.
- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.
- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).
