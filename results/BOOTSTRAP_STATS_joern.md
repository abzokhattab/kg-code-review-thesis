# Bootstrap CIs + paired permutation tests — Joern CPG KG

> ## ⛔ SUPERSEDED — DO NOT CITE
>
> The KG effect reported below (+1.743/6, d_z=+1.24, p<.0001, W/T/L 28/6/1) is
> an artefact of a **prompt asymmetry**: the KG arm received a prompt the
> baseline did not, so the contrast measured builder *plus* prompt. Re-running
> the same Joern builder with the prompt held at parity
> (`results/BOOTSTRAP_STATS_joern_parity.md`, n=35) yields kg +0.63 on the
> total (p=0.077) and +0.34 KG-relevant (p=0.111) — **not significant on
> either metric**.
>
> Canonical RQ2 headline: `results/BOOTSTRAP_STATS_v2.md` (era 2).
> Causal claim for structural context: `results/INJECTION_EXP2_RESULTS.md`.
> Context: `results/ERA_GUIDE.md`.


**Input:** `results/checklist_evaluation_llm_multi__joern.json`  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026.

## Per-mode mean scores with 95% bootstrap CI

| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |
|---|---:|---:|---:|
| baseline | 35 | 8.94 [8.49, 9.43] | 5.00 [4.66, 5.34] |
| kg | 35 | 10.11 [9.57, 10.69] | 5.69 [5.34, 6.06] |
| rag | 35 | 9.91 [9.40, 10.46] | 5.43 [5.03, 5.86] |
| hybrid | 35 | 9.89 [9.40, 10.34] | 5.60 [5.31, 5.89] |

## Paired differences vs baseline (mode − baseline, same PR)

| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 35 | +1.17 [+0.54, +1.77] | 0.002 | +0.61 | +0.69 [+0.31, +1.09] | 0.003 | +0.58 |
| rag | 35 | +0.97 [+0.34, +1.60] | 0.007 | +0.51 | +0.43 [+0.00, +0.89] | 0.091 | +0.32 |
| hybrid | 35 | +0.94 [+0.23, +1.60] | 0.015 | +0.46 | +0.60 [+0.20, +1.00] | 0.008 | +0.49 |

## Interpretation key

- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.
- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.
- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).
