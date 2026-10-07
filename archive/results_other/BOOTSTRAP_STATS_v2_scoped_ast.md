# Bootstrap CIs + paired permutation tests — v2 (40 PRs, scoped-AST KG)

**Input:** `results/checklist_evaluation_llm_multi__v2_scoped_ast.json`  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026.

## Per-mode mean scores with 95% bootstrap CI

| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |
|---|---:|---:|---:|
| baseline | 40 | 9.20 [8.70, 9.70] | 4.97 [4.67, 5.28] |
| kg | 40 | 9.65 [9.07, 10.25] | 5.22 [4.88, 5.58] |
| rag | 40 | 10.07 [9.57, 10.60] | 5.40 [5.00, 5.78] |
| hybrid | 40 | 9.45 [8.93, 10.00] | 5.28 [4.85, 5.67] |

## Paired differences vs baseline (mode − baseline, same PR)

| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 40 | +0.45 [-0.28, +1.18] | 0.278 | +0.18 | +0.25 [-0.10, +0.60] | 0.219 | +0.22 |
| rag | 40 | +0.88 [+0.30, +1.45] | 0.007 | +0.47 | +0.42 [+0.05, +0.82] | 0.057 | +0.33 |
| hybrid | 40 | +0.25 [-0.57, +1.07] | 0.599 | +0.09 | +0.30 [-0.15, +0.75] | 0.251 | +0.20 |

## Interpretation key

- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.
- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.
- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).
