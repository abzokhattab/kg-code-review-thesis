# Experiment C: CPG Richness vs KG-relevant Delta

**n=35 PRs** (5 Go PRs excluded)

## Spearman Correlations

| Variable | r | p | sig |
|---|---:|---:|---|
| n_callers vs Δkg | -0.043 | 0.8079 | n.s. |
| n_callers vs Δtot | -0.096 | 0.5839 | n.s. |
| n_functions vs Δkg | -0.056 | 0.7476 | n.s. |
| baseline_kg vs Δkg | -0.490 | 0.0028 | ** |

## Binned Analysis by n_callers

| Bin | n | Mean Δkg | Mean Δtot | Wins |
|---|---:|---:|---:|---:|
| empty (0) | 9 | +0.89 | +3.22 | 5/9 |
| sparse (1-9) | 7 | +1.57 | +3.14 | 6/7 |
| moderate (10-49) | 9 | +0.56 | +2.78 | 4/9 |
| capped (50) | 8 | +0.38 | +2.12 | 2/8 |
