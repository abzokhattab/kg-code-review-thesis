# Kruskal-Wallis + Bonferroni (and paired Friedman/Wilcoxon) — checklist_evaluation_llm_multi__v2_scoped_ast

**Input:** `results/checklist_evaluation_llm_multi__v2_scoped_ast.json`  
**Families:** (1) Kruskal-Wallis omnibus + Dunn post-hoc, Bonferroni (unpaired, as requested); (2) Friedman omnibus + Wilcoxon signed-rank vs baseline, Bonferroni (paired, design-matched).

## Total /25

**Kruskal-Wallis (unpaired omnibus):** H=5.04, df=3, p=0.1686  
**Friedman (paired omnibus):** χ²=5.91, df=3, p=0.1162, n=40

### Dunn post-hoc (all pairs), Bonferroni-corrected

| Pair | z | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|
| baseline vs kg | -1.25 | 0.2124 | 1.0000 |
| baseline vs rag | -2.24 | 0.0252 | 0.1514 |
| baseline vs hybrid | -1.06 | 0.2883 | 1.0000 |
| kg vs rag | -0.99 | 0.3217 | 1.0000 |
| kg vs hybrid | +0.18 | 0.8533 | 1.0000 |
| rag vs hybrid | +1.18 | 0.2397 | 1.0000 |

### Wilcoxon signed-rank vs baseline (paired), Bonferroni-corrected

| Comparison | n pairs | statistic | median Δ | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|---:|---:|
| kg vs baseline | 40 | 203.5 | 1.0 | 0.1639 | 0.4918 |
| rag vs baseline | 40 | 143.0 | 1.0 | 0.0072 | 0.0216 |
| hybrid vs baseline | 40 | 272.0 | 0.0 | 0.6593 | 1.0000 |

## KG-relevant /9

**Kruskal-Wallis (unpaired omnibus):** H=3.23, df=3, p=0.3571  
**Friedman (paired omnibus):** χ²=2.76, df=3, p=0.4301, n=40

### Dunn post-hoc (all pairs), Bonferroni-corrected

| Pair | z | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|
| baseline vs kg | -1.10 | 0.2729 | 1.0000 |
| baseline vs rag | -1.59 | 0.1123 | 0.6739 |
| baseline vs hybrid | -1.52 | 0.1281 | 0.7684 |
| kg vs rag | -0.49 | 0.6231 | 1.0000 |
| kg vs hybrid | -0.42 | 0.6706 | 1.0000 |
| rag vs hybrid | +0.07 | 0.9473 | 1.0000 |

### Wilcoxon signed-rank vs baseline (paired), Bonferroni-corrected

| Comparison | n pairs | statistic | median Δ | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|---:|---:|
| kg vs baseline | 40 | 94.0 | 0.0 | 0.1649 | 0.4948 |
| rag vs baseline | 40 | 60.0 | 0.0 | 0.0488 | 0.1463 |
| hybrid vs baseline | 40 | 174.0 | 0.0 | 0.2137 | 0.6412 |

## Interpretation key

- **Omnibus p < 0.05** → the four modes are not all equal; post-hoc tests localise the differences.
- **Bonferroni** multiplies each raw p by the number of comparisons in its family (capped at 1).
- The **paired** family (Friedman + Wilcoxon) respects that the same PRs pass through every mode and is the more appropriate test for this repeated-measures design; the **unpaired** Kruskal-Wallis/Dunn family is reported because it was requested and is more conservative.
