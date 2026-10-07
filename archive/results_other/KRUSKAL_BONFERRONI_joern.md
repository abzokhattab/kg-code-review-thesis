# Kruskal-Wallis + Bonferroni (and paired Friedman/Wilcoxon) — checklist_evaluation_llm_multi__joern

**Input:** `results/checklist_evaluation_llm_multi__joern.json`  
**Families:** (1) Kruskal-Wallis omnibus + Dunn post-hoc, Bonferroni (unpaired, as requested); (2) Friedman omnibus + Wilcoxon signed-rank vs baseline, Bonferroni (paired, design-matched).

## Total /25

**Kruskal-Wallis (unpaired omnibus):** H=11.10, df=3, p=0.0112  
**Friedman (paired omnibus):** χ²=12.49, df=3, p=0.0059, n=35

### Dunn post-hoc (all pairs), Bonferroni-corrected

| Pair | z | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|
| baseline vs kg | -3.00 | 0.0027 | 0.0160 |
| baseline vs rag | -2.42 | 0.0157 | 0.0940 |
| baseline vs hybrid | -2.61 | 0.0091 | 0.0548 |
| kg vs rag | +0.59 | 0.5573 | 1.0000 |
| kg vs hybrid | +0.40 | 0.6919 | 1.0000 |
| rag vs hybrid | -0.19 | 0.8488 | 1.0000 |

### Wilcoxon signed-rank vs baseline (paired), Bonferroni-corrected

| Comparison | n pairs | statistic | median Δ | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|---:|---:|
| kg vs baseline | 35 | 68.0 | 1.0 | 0.0018 | 0.0054 |
| rag vs baseline | 35 | 112.5 | 1.0 | 0.0069 | 0.0206 |
| hybrid vs baseline | 35 | 115.5 | 1.0 | 0.0049 | 0.0147 |

## KG-relevant /9

**Kruskal-Wallis (unpaired omnibus):** H=7.13, df=3, p=0.0678  
**Friedman (paired omnibus):** χ²=10.60, df=3, p=0.0141, n=35

### Dunn post-hoc (all pairs), Bonferroni-corrected

| Pair | z | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|
| baseline vs kg | -2.33 | 0.0200 | 0.1198 |
| baseline vs rag | -1.57 | 0.1164 | 0.6981 |
| baseline vs hybrid | -2.30 | 0.0216 | 0.1294 |
| kg vs rag | +0.76 | 0.4492 | 1.0000 |
| kg vs hybrid | +0.03 | 0.9768 | 1.0000 |
| rag vs hybrid | -0.73 | 0.4668 | 1.0000 |

### Wilcoxon signed-rank vs baseline (paired), Bonferroni-corrected

| Comparison | n pairs | statistic | median Δ | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|---:|---:|
| kg vs baseline | 35 | 69.5 | 1.0 | 0.0028 | 0.0085 |
| rag vs baseline | 35 | 59.0 | 0.0 | 0.0789 | 0.2368 |
| hybrid vs baseline | 35 | 30.5 | 0.0 | 0.0079 | 0.0237 |

## Interpretation key

- **Omnibus p < 0.05** → the four modes are not all equal; post-hoc tests localise the differences.
- **Bonferroni** multiplies each raw p by the number of comparisons in its family (capped at 1).
- The **paired** family (Friedman + Wilcoxon) respects that the same PRs pass through every mode and is the more appropriate test for this repeated-measures design; the **unpaired** Kruskal-Wallis/Dunn family is reported because it was requested and is more conservative.
