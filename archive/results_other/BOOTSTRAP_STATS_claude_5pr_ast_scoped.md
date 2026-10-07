# Bootstrap CIs + paired permutation tests — Claude 5-PR AST (change-scoped)

**Input:** `results/checklist_evaluation_llm_multi__claude_5pr_ast_scoped.json`  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026.

## Per-mode mean scores with 95% bootstrap CI

| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |
|---|---:|---:|---:|
| baseline | 5 | 14.20 [12.00, 16.00] | 7.80 [6.80, 8.80] |
| kg | 5 | 13.80 [12.60, 15.00] | 7.80 [7.40, 8.00] |
| rag | 5 | 14.20 [13.60, 14.80] | 7.20 [6.00, 8.20] |
| hybrid | 5 | 14.40 [13.40, 15.40] | 8.00 [7.20, 8.80] |

## Paired differences vs baseline (mode − baseline, same PR)

| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 5 | -0.40 [-1.40, +0.80] | 0.750 | -0.26 | +0.00 [-0.80, +0.80] | 1.000 | +0.00 |
| rag | 5 | +0.00 [-2.00, +2.20] | 1.000 | +0.00 | -0.60 [-1.80, +0.80] | 0.625 | -0.36 |
| hybrid | 5 | +0.20 [-1.40, +2.00] | 1.000 | +0.09 | +0.20 [-0.40, +0.80] | 1.000 | +0.24 |

## Interpretation key

- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.
- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.
- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).
