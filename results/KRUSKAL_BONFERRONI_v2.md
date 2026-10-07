# Kruskal-Wallis + Bonferroni (and paired Friedman/Wilcoxon) — checklist_evaluation_llm_multi__v2

**Input:** `results/checklist_evaluation_llm_multi__v2.json`  
**Families:** (1) Kruskal-Wallis omnibus + Dunn post-hoc, Bonferroni (unpaired, as requested); (2) Friedman omnibus + Wilcoxon signed-rank vs baseline, Bonferroni (paired, design-matched).

## Total /25

**Kruskal-Wallis (unpaired omnibus):** H=6.65, df=3, p=0.0841  
**Friedman (paired omnibus):** χ²=7.22, df=3, p=0.0652, n=40

### Dunn post-hoc (all pairs), Bonferroni-corrected

| Pair | z | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|
| baseline vs kg | -1.49 | 0.1354 | 0.8121 |
| baseline vs rag | -2.31 | 0.0207 | 0.1241 |
| baseline vs hybrid | -2.14 | 0.0322 | 0.1933 |
| kg vs rag | -0.82 | 0.4120 | 1.0000 |
| kg vs hybrid | -0.65 | 0.5167 | 1.0000 |
| rag vs hybrid | +0.17 | 0.8635 | 1.0000 |

### Wilcoxon signed-rank vs baseline (paired), Bonferroni-corrected

| Comparison | n pairs | statistic | median Δ | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|---:|---:|
| kg vs baseline | 40 | 170.5 | 1.0 | 0.0464 | 0.1392 |
| rag vs baseline | 40 | 143.0 | 1.0 | 0.0072 | 0.0216 |
| hybrid vs baseline | 40 | 167.0 | 1.0 | 0.0139 | 0.0418 |

## KG-relevant /9

**Kruskal-Wallis (unpaired omnibus):** H=6.59, df=3, p=0.0863  
**Friedman (paired omnibus):** χ²=7.98, df=3, p=0.0464, n=40

### Dunn post-hoc (all pairs), Bonferroni-corrected

| Pair | z | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|
| baseline vs kg | -2.27 | 0.0231 | 0.1384 |
| baseline vs rag | -1.66 | 0.0973 | 0.5836 |
| baseline vs hybrid | -2.15 | 0.0315 | 0.1889 |
| kg vs rag | +0.61 | 0.5391 | 1.0000 |
| kg vs hybrid | +0.12 | 0.9032 | 1.0000 |
| rag vs hybrid | -0.49 | 0.6223 | 1.0000 |

### Wilcoxon signed-rank vs baseline (paired), Bonferroni-corrected

| Comparison | n pairs | statistic | median Δ | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|---:|---:|
| kg vs baseline | 40 | 69.5 | 0.0 | 0.0058 | 0.0175 |
| rag vs baseline | 40 | 60.0 | 0.0 | 0.0488 | 0.1463 |
| hybrid vs baseline | 40 | 30.5 | 0.0 | 0.0079 | 0.0237 |

## Interpretation key

- **Omnibus p < 0.05** → the four modes are not all equal; post-hoc tests localise the differences.
- **Bonferroni** multiplies each raw p by the number of comparisons in its family (capped at 1).
- The **paired** family (Friedman + Wilcoxon) respects that the same PRs pass through every mode and is the more appropriate test for this repeated-measures design; the **unpaired** Kruskal-Wallis/Dunn family is reported because it was requested and is more conservative.
