# Power of a confirmatory test of the KG effect

Contrast: kg minus baseline. alpha = 0.05, 2000 sign-flip permutations per test, 1200 simulations per sample size, seed 2026.

Resampled from the 40 observed per-PR paired differences, so the effect size is inherited from the data. Optimistic by construction: it assumes the exploratory point estimate is the truth. The curve draws **with** replacement, which is the only scheme that extends past n = 40.

| Scale | observed d_z | power at n = 12 (subsample) | power at n = 12 (bootstrap) | n for 80 % | n for 90 % |
|---|---|---|---|---|---|
| Total /25 | +0.33 | 10% | 14% | 85 | 110 |
| KG-relevant /9 | +0.47 | 18% | 18% | 40 | 55 |

The subsample column is the check against Chapter 6, which reports about 8 % and 16 % for this design from the same scheme.

## Full curves

| n | total | KG-relevant |
|---|---|---|
| 10 | 0.097 | 0.141 |
| 15 | 0.178 | 0.293 |
| 20 | 0.237 | 0.433 |
| 25 | 0.325 | 0.533 |
| 30 | 0.356 | 0.664 |
| 35 | 0.428 | 0.717 |
| 40 | 0.495 | 0.802 |
| 45 | 0.547 | 0.855 |
| 50 | 0.612 | 0.882 |
| 55 | 0.655 | 0.911 |
| 60 | 0.665 | 0.942 |
| 65 | 0.736 | 0.964 |
| 70 | 0.733 | 0.978 |
| 75 | 0.790 | 0.975 |
| 80 | 0.797 | 0.989 |
| 85 | 0.832 | 0.993 |
| 90 | 0.848 | 0.993 |
| 95 | 0.862 | 0.993 |
| 100 | 0.887 | 0.995 |
| 105 | 0.897 | 0.997 |
| 110 | 0.921 | 1.000 |
| 115 | 0.927 | 1.000 |
| 120 | 0.935 | 0.997 |
| 125 | 0.953 | 0.998 |
| 130 | 0.953 | 1.000 |
| 135 | 0.965 | 1.000 |
| 140 | 0.964 | 1.000 |
| 145 | 0.975 | 1.000 |
| 150 | 0.974 | 1.000 |
| 155 | 0.976 | 1.000 |
| 160 | 0.978 | 1.000 |
| 165 | 0.985 | 1.000 |
| 170 | 0.988 | 1.000 |
| 175 | 0.983 | 1.000 |
| 180 | 0.993 | 1.000 |
| 185 | 0.991 | 1.000 |
| 190 | 0.993 | 1.000 |
| 195 | 0.993 | 1.000 |
| 200 | 0.998 | 1.000 |
