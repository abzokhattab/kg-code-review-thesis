# Bootstrap CIs + paired permutation tests — v2_gemini (40 PRs, Gemini 2.5 Flash generator)

**Input:** `/Users/akhattab/ai/results/checklist_evaluation_llm_multi__v2_gemini.json`  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026.

## Per-mode mean scores with 95% bootstrap CI

| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |
|---|---:|---:|---:|
| baseline | 40 | 11.50 [10.78, 12.22] | 5.50 [4.97, 6.00] |
| kg | 40 | 11.82 [11.30, 12.35] | 5.97 [5.60, 6.35] |
| rag | 40 | 11.25 [10.35, 12.18] | 5.00 [4.42, 5.60] |
| hybrid | 40 | 12.30 [11.60, 13.00] | 5.75 [5.22, 6.28] |

## Paired differences vs baseline (mode − baseline, same PR)

| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 40 | +0.33 [-0.47, +1.12] | 0.464 | +0.13 | +0.47 [-0.10, +1.05] | 0.136 | +0.25 |
| rag | 40 | -0.25 [-1.27, +0.78] | 0.688 | -0.07 | -0.50 [-1.20, +0.17] | 0.190 | -0.22 |
| hybrid | 40 | +0.80 [-0.20, +1.75] | 0.127 | +0.26 | +0.25 [-0.38, +0.85] | 0.485 | +0.12 |

## Interpretation key

- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.
- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.
- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).
