# Bootstrap CIs + paired permutation tests — Joern CPG KG, body-parity prompt (35 PRs)

**Input:** `/Users/akhattab/ai/results/checklist_evaluation_llm_multi__joern_parity.json`  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026.

## Per-mode mean scores with 95% bootstrap CI

| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |
|---|---:|---:|---:|
| baseline | 35 | 8.94 [8.49, 9.43] | 5.00 [4.66, 5.31] |
| kg | 35 | 9.57 [9.03, 10.09] | 5.34 [5.00, 5.66] |
| rag | 35 | 9.91 [9.40, 10.46] | 5.43 [5.03, 5.86] |
| hybrid | 35 | 9.89 [9.43, 10.34] | 5.60 [5.31, 5.89] |

## Paired differences vs baseline (mode − baseline, same PR)

| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 35 | +0.63 [+0.00, +1.26] | 0.077 | +0.32 | +0.34 [-0.03, +0.71] | 0.111 | +0.30 |
| rag | 35 | +0.97 [+0.34, +1.60] | 0.006 | +0.51 | +0.43 [+0.00, +0.89] | 0.086 | +0.32 |
| hybrid | 35 | +0.94 [+0.26, +1.60] | 0.015 | +0.46 | +0.60 [+0.23, +1.03] | 0.008 | +0.49 |

## Interpretation key

- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.
- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.
- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).
