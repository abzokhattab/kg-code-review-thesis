# Joern-REPLACE-grep Experiment Results

**Date:** 2026-09-19  
**Design:** Replace grep-based `dependent_files` with Joern-resolved cross-file callers  
**Generator:** gpt-4o (T=0.0)  
**Judges:** gpt-4o-mini + gpt-4o + gemini-2.5-flash (3-judge majority vote)  
**n:** 35 (5 Go PRs excluded — Joern Go frontend failure)  
**Seed:** 2026  
**Bootstrap:** B_boot=10,000, B_perm=20,000

## Headline

Replacing grep dependents with Joern callers recovers the headline effect:

| Run | n | Total Δ | Total p | KG-rel Δ | KG-rel p | KG-rel d_z |
|---|---|---|---|---|---|---|
| Headline lexical | 40 | +0.62 | 0.054 | **+0.60** | **0.007** | +0.47 |
| Parity (grep+Joern) | 35 | +0.63 | 0.077 | +0.34 | 0.111 | +0.30 |
| **Joern-replace** | **35** | **+0.77** | **0.030** | **+0.57** | **0.008** | **+0.51** |

## Interpretation

The parity run (2026-06-11) scored poorly because it inherited grep-based
`dependent_files` and added Joern callers on top. This diluted the signal:
grep contributes ~10% precision noise alongside Joern's precise call edges.

When Joern callers *replace* grep dependents entirely:
- KG-relevant delta recovers from +0.34 to +0.57 (vs headline +0.60)
- Significance returns: p=0.008 (vs parity p=0.111)
- Effect size improves: d_z=+0.51 (vs parity d_z=+0.30)

## Head-to-head: Joern-replace vs Parity

- KG-rel: +0.23 [-0.09, +0.57], p=0.252
- Total: +0.14 [-0.43, +0.71], p=0.699

The improvement over parity is directional but not individually significant
at n=35. The important result is that Joern-replace matches the headline
rather than falling short.

## Evidence modification

- Original (grep) total dependent_files across 35 PRs: 351
- Modified (Joern callers) total dependent_files across 35 PRs: 1425
- Joern callers provide function-level resolved cross-file dependencies
  vs grep's filename-stem text search (~10% precision)

## Raw means

|  | Baseline | Joern-replace | Δ [95% CI] | p | d_z |
|---|---|---|---|---|---|
| Total /25 | 8.94 | 9.71 | +0.77 [+0.14, +1.37] | 0.030 | +0.40 |
| KG-rel /9 | 5.00 | 5.57 | +0.57 [+0.20, +0.94] | 0.008 | +0.51 |
