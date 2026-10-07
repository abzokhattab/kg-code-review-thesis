# Bootstrap CIs + paired permutation tests — Clean confirmatory re-run — 12 held-out PRs, headline config

**Input:** `results/checklist_evaluation_llm_multi__confirmatory_clean.json`  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026.

## Per-mode mean scores with 95% bootstrap CI

| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |
|---|---:|---:|---:|
| baseline | 12 | 10.00 [9.00, 11.08] | 5.17 [4.58, 5.75] |
| kg | 12 | 10.42 [9.75, 11.08] | 5.58 [5.00, 6.08] |

## Paired differences vs baseline (mode − baseline, same PR)

| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 12 | +0.42 [-0.25, +1.17] | 0.426 | +0.30 | +0.42 [-0.17, +1.00] | 0.312 | +0.39 |

## Interpretation key

- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.
- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.
- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).
