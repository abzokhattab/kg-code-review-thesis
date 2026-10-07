# Bootstrap CIs + paired permutation tests — Claude Sonnet 4.5 · 5 PRs · AST-KG · 3-judge majority vote

**Input:** `results/checklist_evaluation_llm_multi__claude_sample_ast.json`  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026.

## Per-mode mean scores with 95% bootstrap CI

| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |
|---|---:|---:|---:|
| baseline | 5 | 14.60 [13.20, 16.00] | 7.80 [6.80, 8.60] |
| kg | 5 | 14.00 [12.20, 15.80] | 7.20 [6.40, 8.00] |
| rag | 5 | 14.00 [13.40, 14.60] | 7.60 [6.80, 8.40] |
| hybrid | 5 | 14.00 [12.80, 15.20] | 7.00 [6.20, 7.80] |

## Paired differences vs baseline (mode − baseline, same PR)

| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 5 | -0.60 [-1.40, +0.40] | 0.500 | -0.53 | -0.60 [-1.40, +0.00] | 0.500 | -0.67 |
| rag | 5 | -0.60 [-2.60, +1.20] | 0.750 | -0.25 | -0.20 [-1.60, +1.20] | 1.000 | -0.11 |
| hybrid | 5 | -0.60 [-3.00, +1.20] | 0.875 | -0.22 | -0.80 [-2.20, +0.40] | 0.500 | -0.49 |

## Interpretation key

- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.
- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.
- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).
