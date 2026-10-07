# Parity-corrected clean-Joern results

**Parity run scope:** n=35 PRs (all clean-Joern PRs that have parity scores).

## Headline numbers

| Metric | Buggy (no body) | Parity (body included) | Shift |
|---|---:|---:|---:|
| n | 35 | 35 | — |
| Mean Δ KG-rel | +0.686 | +0.343 | -0.343 |
| SD Δ KG-rel | 1.183 | 1.136 | — |
| **d_z KG-rel** | **+0.580** | **+0.302** | **-0.278** |
| Mean Δ total | +1.171 | +0.629 | -0.543 |
| **d_z total** | **+0.606** | **+0.324** | **-0.282** |

**Wilcoxon paired test p-value (KG-rel, parity vs baseline):** p = 0.0573
**Wilcoxon paired test p-value (total, parity vs baseline):** p = 0.0652

## Per-PR shifts (parity − bug)

| PR | Buggy Δ KG-rel | Parity Δ KG-rel | Shift | Buggy Δ total | Parity Δ total | Shift |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | -1 | -1 | +0 | +1 | +1 | +0 |
| 2 | +1 | +0 | -1 | +1 | +0 | -1 |
| 3 | +0 | -1 | -1 | +1 | -4 | -5 |
| 6 | -1 | +0 | +1 | -1 | -1 | +0 |
| 8 | +2 | +2 | +0 | +5 | +4 | -1 |
| 10 | +0 | +0 | +0 | -1 | -1 | +0 |
| 12 | +1 | +2 | +1 | +1 | +4 | +3 |
| 13 | +0 | +1 | +1 | +3 | +1 | -2 |
| 14 | +1 | +2 | +1 | +1 | +3 | +2 |
| 15 | +3 | +0 | -3 | +3 | +0 | -3 |
| 18 | -1 | +0 | +1 | +1 | +2 | +1 |
| 19 | +0 | +0 | +0 | +0 | +1 | +1 |
| 20 | -2 | -2 | +0 | -3 | -1 | +2 |
| 21 | +1 | -1 | -2 | +2 | -1 | -3 |
| 22 | +1 | +1 | +0 | +3 | +2 | -1 |
| 23 | +0 | -1 | -1 | -3 | -2 | +1 |
| 24 | +1 | +0 | -1 | +4 | +1 | -3 |
| 28 | +1 | +2 | +1 | +0 | +2 | +2 |
| 29 | +0 | +0 | +0 | +0 | +0 | +0 |
| 30 | -1 | -1 | +0 | +1 | +0 | -1 |
| 31 | +3 | +1 | -2 | +4 | +1 | -3 |
| 32 | +1 | +0 | -1 | +0 | -2 | -2 |
| 33 | +2 | +2 | +0 | +2 | +2 | +0 |
| 34 | +1 | -1 | -2 | +0 | +1 | +1 |
| 38 | +1 | +2 | +1 | +0 | +2 | +2 |
| 39 | +2 | +2 | +0 | +3 | +1 | -2 |
| 40 | +2 | +1 | -1 | +4 | +3 | -1 |
| 41 | +2 | +2 | +0 | +3 | +2 | -1 |
| 42 | +1 | +0 | -1 | +3 | +1 | -2 |
| 43 | +2 | +0 | -2 | +1 | -2 | -3 |
| 44 | +1 | +0 | -1 | -1 | -3 | -2 |
| 45 | +0 | -1 | -1 | -1 | -1 | +0 |
| 46 | +0 | +0 | +0 | +3 | +4 | +1 |
| 47 | -1 | +0 | +1 | +0 | +1 | +1 |
| 48 | +1 | +1 | +0 | +1 | +1 | +0 |

## Reading

The parity correction **lowers** the headline KG-rel d_z from +0.580 to +0.302. This is unexpected: it suggests the
PR body was actually *helping* the baseline arm more than the joern
arm in the original comparison. Investigate.
