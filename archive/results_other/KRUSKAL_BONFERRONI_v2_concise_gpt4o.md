# Kruskal-Wallis + Bonferroni (and paired Friedman/Wilcoxon) — checklist_evaluation_llm_multi__v2_concise_gpt4o

**Input:** `results/checklist_evaluation_llm_multi__v2_concise_gpt4o.json`  
**Families:** (1) Kruskal-Wallis omnibus + Dunn post-hoc, Bonferroni (unpaired, as requested); (2) Friedman omnibus + Wilcoxon signed-rank vs baseline, Bonferroni (paired, design-matched).

## Total /25

**Kruskal-Wallis (unpaired omnibus):** H=1.01, df=3, p=0.7984  
**Friedman (paired omnibus):** χ²=0.68, df=3, p=0.8784, n=40

### Dunn post-hoc (all pairs), Bonferroni-corrected

| Pair | z | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|
| baseline vs kg | -0.64 | 0.5254 | 1.0000 |
| baseline vs rag | -0.11 | 0.9119 | 1.0000 |
| baseline vs hybrid | -0.85 | 0.3926 | 1.0000 |
| kg vs rag | +0.52 | 0.6000 | 1.0000 |
| kg vs hybrid | -0.22 | 0.8259 | 1.0000 |
| rag vs hybrid | -0.74 | 0.4567 | 1.0000 |

### Wilcoxon signed-rank vs baseline (paired), Bonferroni-corrected

| Comparison | n pairs | statistic | median Δ | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|---:|---:|
| kg vs baseline | 40 | 153.5 | 0.0 | 0.3849 | 1.0000 |
| rag vs baseline | 40 | 284.5 | 1.0 | 0.6072 | 1.0000 |
| hybrid vs baseline | 40 | 204.5 | 0.0 | 0.3834 | 1.0000 |

## KG-relevant /9

**Kruskal-Wallis (unpaired omnibus):** H=7.98, df=3, p=0.0464  
**Friedman (paired omnibus):** χ²=8.37, df=3, p=0.0389, n=40

### Dunn post-hoc (all pairs), Bonferroni-corrected

| Pair | z | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|
| baseline vs kg | -2.71 | 0.0068 | 0.0409 |
| baseline vs rag | -0.74 | 0.4620 | 1.0000 |
| baseline vs hybrid | -1.47 | 0.1423 | 0.8538 |
| kg vs rag | +1.97 | 0.0488 | 0.2930 |
| kg vs hybrid | +1.24 | 0.2156 | 1.0000 |
| rag vs hybrid | -0.73 | 0.4643 | 1.0000 |

### Wilcoxon signed-rank vs baseline (paired), Bonferroni-corrected

| Comparison | n pairs | statistic | median Δ | p (raw) | p (Bonferroni) |
|---|---:|---:|---:|---:|---:|
| kg vs baseline | 40 | 55.5 | 1.0 | 0.0028 | 0.0083 |
| rag vs baseline | 40 | 179.5 | 0.0 | 0.4020 | 1.0000 |
| hybrid vs baseline | 40 | 105.0 | 0.0 | 0.0649 | 0.1946 |

## Interpretation key

- **Omnibus p < 0.05** → the four modes are not all equal; post-hoc tests localise the differences.
- **Bonferroni** multiplies each raw p by the number of comparisons in its family (capped at 1).
- The **paired** family (Friedman + Wilcoxon) respects that the same PRs pass through every mode and is the more appropriate test for this repeated-measures design; the **unpaired** Kruskal-Wallis/Dunn family is reported because it was requested and is more conservative.
