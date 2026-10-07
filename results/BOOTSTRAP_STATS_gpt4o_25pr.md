# Bootstrap CIs + paired permutation tests — gpt-4o · 25 PRs · 3-judge majority vote

**Input:** `results/checklist_evaluation_llm_multi.json`  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026.

## Per-mode mean scores with 95% bootstrap CI

| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |
|---|---:|---:|---:|
| baseline | 25 | 8.08 [7.24, 8.92] | 4.16 [3.44, 4.88] |
| kg | 25 | 8.24 [7.52, 8.96] | 4.80 [4.40, 5.20] |
| rag | 25 | 8.60 [7.80, 9.36] | 4.64 [4.04, 5.24] |
| hybrid | 25 | 8.04 [7.24, 8.84] | 4.16 [3.60, 4.72] |

## Paired differences vs baseline (mode − baseline, same PR)

| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 25 | +0.16 [-0.60, +0.92] | 0.759 | +0.08 | +0.64 [+0.00, +1.28] | 0.087 | +0.39 |
| rag | 25 | +0.52 [-0.12, +1.20] | 0.189 | +0.30 | +0.48 [-0.04, +1.00] | 0.123 | +0.35 |
| hybrid | 25 | -0.04 [-0.84, +0.72] | 1.000 | -0.02 | +0.00 [-0.56, +0.56] | 1.000 | +0.00 |

## Interpretation key

- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.
- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.
- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).
