# Bootstrap CIs + paired permutation tests — v2_claude (40 PRs, Claude Haiku 4.5 generator)

**Input:** `/Users/akhattab/ai/results/checklist_evaluation_llm_multi__v2_claude.json`  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026.

## Per-mode mean scores with 95% bootstrap CI

| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |
|---|---:|---:|---:|
| baseline | 40 | 14.12 [13.50, 14.75] | 7.22 [6.85, 7.60] |
| kg | 40 | 14.43 [13.80, 15.05] | 7.38 [7.08, 7.65] |
| rag | 40 | 14.20 [13.60, 14.80] | 7.22 [6.90, 7.53] |
| hybrid | 40 | 14.12 [13.60, 14.68] | 7.33 [7.08, 7.55] |

## Paired differences vs baseline (mode − baseline, same PR)

| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 40 | +0.30 [-0.33, +0.93] | 0.404 | +0.14 | +0.15 [-0.17, +0.47] | 0.459 | +0.14 |
| rag | 40 | +0.07 [-0.57, +0.75] | 0.883 | +0.03 | +0.00 [-0.40, +0.40] | 1.000 | +0.00 |
| hybrid | 40 | +0.00 [-0.60, +0.62] | 1.000 | +0.00 | +0.10 [-0.25, +0.47] | 0.686 | +0.09 |

## Interpretation key

- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.
- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.
- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).
