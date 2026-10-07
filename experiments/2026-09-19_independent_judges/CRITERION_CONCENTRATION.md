# Where the context effect lands — per-criterion decomposition

**Input:** `experiments/2026-09-19_independent_judges/RESULTS_EXP1.json`  
**Script:** `scripts/analyze_criterion_concentration.py`  
**Method:** majority-vote yes-rate per criterion per arm; concentration tested by sampling random criterion subsets of the same size (B=200,000, seed=2026).

The concentration test permutes *criteria*, not PRs. It asks whether the advantage is localised where the mechanism predicts, which is a separate question from whether the aggregate difference is non-zero (`scripts/bootstrap_stats.py`).

## Summary

| Mode | n | gain in the 9 KG-relevant | gain in the other 16 | total | share in KG-relevant | expected if diffuse | p |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 40 | +0.500 | -0.250 | +0.250 | 200% | +0.090 | 0.0095 |
| rag | 40 | +0.450 | +0.450 | +0.900 | 50% | +0.324 | 0.2411 |
| hybrid | 40 | +0.400 | +0.025 | +0.425 | 94% | +0.153 | 0.0238 |

Gains are in rubric points on the /25 scale, so the KG-relevant column is directly comparable to the /9 subscale difference reported in the bootstrap tables.


## kg vs baseline — per criterion

| ID | KG-relevant | Category | baseline | kg | Δ |
|---|---|---|---:|---:|---:|
| F3 | yes | Functionality | 57.5% | 75.0% | +17.5pp |
| F4 | yes | Functionality | 57.5% | 72.5% | +15.0pp |
| P1 | — | Performance | 12.5% | 22.5% | +10.0pp |
| T3 | yes | Tests | 62.5% | 72.5% | +10.0pp |
| M3 | yes | Maintainability | 5.0% | 12.5% | +7.5pp |
| C2 | yes | Consistency | 0.0% | 5.0% | +5.0pp |
| P2 | — | Performance | 2.5% | 7.5% | +5.0pp |
| M1 | yes | Maintainability | 7.5% | 10.0% | +2.5pp |
| R2 | — | Readability | 2.5% | 5.0% | +2.5pp |
| F1 | — | Functionality | 7.5% | 7.5% | +0.0pp |
| M2 | — | Maintainability | 0.0% | 0.0% | +0.0pp |
| S2 | — | Security | 0.0% | 0.0% | +0.0pp |
| Q1 | — | Quality | 100.0% | 100.0% | +0.0pp |
| Q2 | yes | Quality | 100.0% | 100.0% | +0.0pp |
| Q3 | — | Quality | 0.0% | 0.0% | +0.0pp |
| Q4 | — | Quality | 0.0% | 0.0% | +0.0pp |
| Q5 | — | Quality | 100.0% | 100.0% | +0.0pp |
| C1 | — | Consistency | 2.5% | 0.0% | -2.5pp |
| R1 | — | Readability | 10.0% | 7.5% | -2.5pp |
| T1 | yes | Tests | 97.5% | 95.0% | -2.5pp |
| R3 | — | Readability | 5.0% | 0.0% | -5.0pp |
| T2 | yes | Tests | 62.5% | 57.5% | -5.0pp |
| F2 | — | Functionality | 62.5% | 52.5% | -10.0pp |
| S1 | — | Security | 20.0% | 10.0% | -10.0pp |
| S3 | — | Security | 25.0% | 12.5% | -12.5pp |

**Floor/ceiling criteria** (identical in both arms at 0% or 100%, cannot register any difference): 7 of 25 — M2, Q1, Q2, Q3, Q4, Q5, S2. These enter the /25 denominator while contributing no variance, so the total score understates any real effect by construction.

**Review length** (characters):

| Arm | mean | median |
|---|---:|---:|
| baseline | 1774 | 1759 |
| kg | 1991 | 1986 |

`kg` is longer than `baseline` on 31 of 40 PRs.

## rag vs baseline — per criterion

| ID | KG-relevant | Category | baseline | rag | Δ |
|---|---|---|---:|---:|---:|
| C2 | yes | Consistency | 0.0% | 25.0% | +25.0pp |
| M1 | yes | Maintainability | 7.5% | 20.0% | +12.5pp |
| P1 | — | Performance | 12.5% | 22.5% | +10.0pp |
| F1 | — | Functionality | 7.5% | 17.5% | +10.0pp |
| F3 | yes | Functionality | 57.5% | 65.0% | +7.5pp |
| S3 | — | Security | 25.0% | 32.5% | +7.5pp |
| M3 | yes | Maintainability | 5.0% | 12.5% | +7.5pp |
| R3 | — | Readability | 5.0% | 10.0% | +5.0pp |
| R2 | — | Readability | 2.5% | 7.5% | +5.0pp |
| R1 | — | Readability | 10.0% | 15.0% | +5.0pp |
| C1 | — | Consistency | 2.5% | 5.0% | +2.5pp |
| S1 | — | Security | 20.0% | 22.5% | +2.5pp |
| T3 | yes | Tests | 62.5% | 62.5% | +0.0pp |
| M2 | — | Maintainability | 0.0% | 0.0% | +0.0pp |
| P2 | — | Performance | 2.5% | 2.5% | +0.0pp |
| S2 | — | Security | 0.0% | 0.0% | +0.0pp |
| Q1 | — | Quality | 100.0% | 100.0% | +0.0pp |
| Q2 | yes | Quality | 100.0% | 100.0% | +0.0pp |
| Q3 | — | Quality | 0.0% | 0.0% | +0.0pp |
| Q4 | — | Quality | 0.0% | 0.0% | +0.0pp |
| Q5 | — | Quality | 100.0% | 100.0% | +0.0pp |
| F4 | yes | Functionality | 57.5% | 55.0% | -2.5pp |
| F2 | — | Functionality | 62.5% | 60.0% | -2.5pp |
| T1 | yes | Tests | 97.5% | 95.0% | -2.5pp |
| T2 | yes | Tests | 62.5% | 60.0% | -2.5pp |

**Floor/ceiling criteria** (identical in both arms at 0% or 100%, cannot register any difference): 7 of 25 — M2, Q1, Q2, Q3, Q4, Q5, S2. These enter the /25 denominator while contributing no variance, so the total score understates any real effect by construction.

**Review length** (characters):

| Arm | mean | median |
|---|---:|---:|
| baseline | 1774 | 1759 |
| rag | 1782 | 1760 |

`rag` is longer than `baseline` on 18 of 40 PRs.

## hybrid vs baseline — per criterion

| ID | KG-relevant | Category | baseline | hybrid | Δ |
|---|---|---|---:|---:|---:|
| M1 | yes | Maintainability | 7.5% | 20.0% | +12.5pp |
| F3 | yes | Functionality | 57.5% | 67.5% | +10.0pp |
| C2 | yes | Consistency | 0.0% | 10.0% | +10.0pp |
| R2 | — | Readability | 2.5% | 10.0% | +7.5pp |
| P1 | — | Performance | 12.5% | 20.0% | +7.5pp |
| T2 | yes | Tests | 62.5% | 70.0% | +7.5pp |
| P2 | — | Performance | 2.5% | 7.5% | +5.0pp |
| F4 | yes | Functionality | 57.5% | 60.0% | +2.5pp |
| T3 | yes | Tests | 62.5% | 62.5% | +0.0pp |
| R1 | — | Readability | 10.0% | 10.0% | +0.0pp |
| M2 | — | Maintainability | 0.0% | 0.0% | +0.0pp |
| M3 | yes | Maintainability | 5.0% | 5.0% | +0.0pp |
| C1 | — | Consistency | 2.5% | 2.5% | +0.0pp |
| S2 | — | Security | 0.0% | 0.0% | +0.0pp |
| S3 | — | Security | 25.0% | 25.0% | +0.0pp |
| Q1 | — | Quality | 100.0% | 100.0% | +0.0pp |
| Q2 | yes | Quality | 100.0% | 100.0% | +0.0pp |
| Q3 | — | Quality | 0.0% | 0.0% | +0.0pp |
| Q4 | — | Quality | 0.0% | 0.0% | +0.0pp |
| Q5 | — | Quality | 100.0% | 100.0% | +0.0pp |
| R3 | — | Readability | 5.0% | 2.5% | -2.5pp |
| T1 | yes | Tests | 97.5% | 95.0% | -2.5pp |
| F1 | — | Functionality | 7.5% | 2.5% | -5.0pp |
| S1 | — | Security | 20.0% | 15.0% | -5.0pp |
| F2 | — | Functionality | 62.5% | 57.5% | -5.0pp |

**Floor/ceiling criteria** (identical in both arms at 0% or 100%, cannot register any difference): 7 of 25 — M2, Q1, Q2, Q3, Q4, Q5, S2. These enter the /25 denominator while contributing no variance, so the total score understates any real effect by construction.

**Review length** (characters):

| Arm | mean | median |
|---|---:|---:|
| baseline | 1774 | 1759 |
| hybrid | 1857 | 1858 |

`hybrid` is longer than `baseline` on 23 of 40 PRs.
