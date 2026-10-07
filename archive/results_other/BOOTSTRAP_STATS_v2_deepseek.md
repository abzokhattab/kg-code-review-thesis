# Bootstrap CIs + paired permutation tests — v2_deepseek (40 PRs, DeepSeek-V3 generator)

**Input:** `/Users/akhattab/ai/results/checklist_evaluation_llm_multi__v2_deepseek.json`  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026.

## Per-mode mean scores with 95% bootstrap CI

| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |
|---|---:|---:|---:|
| baseline | 40 | 13.57 [13.03, 14.12] | 6.83 [6.42, 7.20] |
| kg | 40 | 14.05 [13.40, 14.68] | 7.03 [6.67, 7.35] |
| rag | 40 | 14.25 [13.60, 14.88] | 7.15 [6.70, 7.58] |
| hybrid | 40 | 13.85 [13.35, 14.38] | 7.03 [6.62, 7.38] |

## Paired differences vs baseline (mode − baseline, same PR)

| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 40 | +0.47 [-0.07, +1.02] | 0.114 | +0.27 | +0.20 [-0.20, +0.57] | 0.385 | +0.16 |
| rag | 40 | +0.68 [-0.05, +1.43] | 0.101 | +0.28 | +0.33 [-0.23, +0.85] | 0.286 | +0.18 |
| hybrid | 40 | +0.28 [-0.35, +0.90] | 0.436 | +0.14 | +0.20 [-0.25, +0.65] | 0.450 | +0.14 |

## Interpretation key

- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.
- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.
- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).
