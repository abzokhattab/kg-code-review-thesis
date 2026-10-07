# Kruskal-Wallis + Bonferroni (and paired Friedman/Wilcoxon) — checklist_evaluation_llm_multi__v2_gpt4o_only

**Input:** `results/checklist_evaluation_llm_multi__v2_gpt4o_only.json`  
**Families:** (1) Kruskal-Wallis omnibus + Dunn post-hoc, Bonferroni (unpaired, as requested); (2) Friedman omnibus + Wilcoxon signed-rank vs baseline, Bonferroni (paired, design-matched).

## Total /25

**Kruskal-Wallis (unpaired omnibus):** H=5.53, df=3, p=0.1367  
**Friedman (paired omnibus):** χ²=9.27, df=3, p=0.0259, n=40

### Dunn post-hoc (all pairs), Bonferroni-corrected

| Pair | z | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|
| baseline vs kg | -1.48 | 0.1403 | 0.8415 |
| baseline vs rag | -1.47 | 0.1422 | 0.8535 |
| baseline vs hybrid | -2.31 | 0.0209 | 0.1256 |
| kg vs rag | +0.01 | 0.9941 | 1.0000 |
| kg vs hybrid | -0.83 | 0.4041 | 1.0000 |
| rag vs hybrid | -0.84 | 0.3999 | 1.0000 |

### Wilcoxon signed-rank vs baseline (paired), Bonferroni-corrected

| Comparison | n pairs | statistic | median Δ | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|---:|---:|
| kg vs baseline | 40 | 161.5 | 0.0 | 0.0527 | 0.1581 |
| rag vs baseline | 40 | 130.0 | 0.0 | 0.0909 | 0.2726 |
| hybrid vs baseline | 40 | 99.5 | 1.0 | 0.0031 | 0.0094 |

## KG-relevant /9

**Kruskal-Wallis (unpaired omnibus):** H=9.77, df=3, p=0.0206  
**Friedman (paired omnibus):** χ²=10.93, df=3, p=0.0121, n=40

### Dunn post-hoc (all pairs), Bonferroni-corrected

| Pair | z | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|
| baseline vs kg | -2.67 | 0.0076 | 0.0457 |
| baseline vs rag | -1.31 | 0.1890 | 1.0000 |
| baseline vs hybrid | -2.66 | 0.0079 | 0.0474 |
| kg vs rag | +1.35 | 0.1754 | 1.0000 |
| kg vs hybrid | +0.01 | 0.9900 | 1.0000 |
| rag vs hybrid | -1.34 | 0.1794 | 1.0000 |

### Wilcoxon signed-rank vs baseline (paired), Bonferroni-corrected

| Comparison | n pairs | statistic | median Δ | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|---:|---:|
| kg vs baseline | 40 | 107.0 | 1.0 | 0.0046 | 0.0138 |
| rag vs baseline | 40 | 115.5 | 0.0 | 0.1947 | 0.5840 |
| hybrid vs baseline | 40 | 56.5 | 1.0 | 0.0017 | 0.0052 |

## Interpretation key

- **Omnibus p < 0.05** → the four modes are not all equal; post-hoc tests localise the differences.
- **Bonferroni** multiplies each raw p by the number of comparisons in its family (capped at 1).
- The **paired** family (Friedman + Wilcoxon) respects that the same PRs pass through every mode and is the more appropriate test for this repeated-measures design; the **unpaired** Kruskal-Wallis/Dunn family is reported because it was requested and is more conservative.
