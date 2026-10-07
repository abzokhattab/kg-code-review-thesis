# Where the context effect lands — per-criterion decomposition

**Input:** `results/checklist_evaluation_llm_multi__v2.json`  
**Script:** `scripts/analyze_criterion_concentration.py`  
**Method:** majority-vote yes-rate per criterion per arm; concentration tested by sampling random criterion subsets of the same size (B=200,000, seed=2026).

The concentration test permutes *criteria*, not PRs. It asks whether the advantage is localised where the mechanism predicts, which is a separate question from whether the aggregate difference is non-zero (`scripts/bootstrap_stats.py`).

## Summary

| Mode | n | gain in the 9 KG-relevant | gain in the other 16 | total | share in KG-relevant | expected if diffuse | p |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 40 | +0.600 | +0.025 | +0.625 | 96% | +0.225 | 0.0162 |
| rag | 40 | +0.425 | +0.450 | +0.875 | 49% | +0.315 | 0.2724 |
| hybrid | 40 | +0.525 | +0.200 | +0.725 | 72% | +0.261 | 0.0629 |

Gains are in rubric points on the /25 scale, so the KG-relevant column is directly comparable to the /9 subscale difference reported in the bootstrap tables.


## kg vs baseline — per criterion

| ID | KG-relevant | Category | baseline | kg | Δ |
|---|---|---|---:|---:|---:|
| F3 | yes | Functionality | 60.0% | 82.5% | +22.5pp |
| M1 | yes | Maintainability | 17.5% | 30.0% | +12.5pp |
| F4 | yes | Functionality | 80.0% | 90.0% | +10.0pp |
| T3 | yes | Tests | 62.5% | 72.5% | +10.0pp |
| P1 | — | Performance | 20.0% | 30.0% | +10.0pp |
| R2 | — | Readability | 7.5% | 15.0% | +7.5pp |
| C2 | yes | Consistency | 5.0% | 12.5% | +7.5pp |
| P2 | — | Performance | 2.5% | 7.5% | +5.0pp |
| Q3 | — | Quality | 37.5% | 42.5% | +5.0pp |
| M3 | yes | Maintainability | 7.5% | 10.0% | +2.5pp |
| Q5 | — | Quality | 80.0% | 82.5% | +2.5pp |
| F1 | — | Functionality | 45.0% | 45.0% | +0.0pp |
| T1 | yes | Tests | 97.5% | 97.5% | +0.0pp |
| M2 | — | Maintainability | 0.0% | 0.0% | +0.0pp |
| C1 | — | Consistency | 0.0% | 0.0% | +0.0pp |
| S2 | — | Security | 0.0% | 0.0% | +0.0pp |
| Q1 | — | Quality | 100.0% | 100.0% | +0.0pp |
| Q2 | yes | Quality | 100.0% | 100.0% | +0.0pp |
| Q4 | — | Quality | 0.0% | 0.0% | +0.0pp |
| F2 | — | Functionality | 70.0% | 67.5% | -2.5pp |
| R1 | — | Readability | 15.0% | 12.5% | -2.5pp |
| S3 | — | Security | 20.0% | 15.0% | -5.0pp |
| T2 | yes | Tests | 67.5% | 62.5% | -5.0pp |
| R3 | — | Readability | 7.5% | 0.0% | -7.5pp |
| S1 | — | Security | 17.5% | 7.5% | -10.0pp |

**Floor/ceiling criteria** (identical in both arms at 0% or 100%, cannot register any difference): 6 of 25 — C1, M2, Q1, Q2, Q4, S2. These enter the /25 denominator while contributing no variance, so the total score understates any real effect by construction.

**Review length** (characters):

| Arm | mean | median |
|---|---:|---:|
| baseline | 1774 | 1759 |
| kg | 1991 | 1986 |

`kg` is longer than `baseline` on 31 of 40 PRs.

## rag vs baseline — per criterion

| ID | KG-relevant | Category | baseline | rag | Δ |
|---|---|---|---:|---:|---:|
| M1 | yes | Maintainability | 17.5% | 40.0% | +22.5pp |
| C2 | yes | Consistency | 5.0% | 25.0% | +20.0pp |
| F1 | — | Functionality | 45.0% | 55.0% | +10.0pp |
| R2 | — | Readability | 7.5% | 17.5% | +10.0pp |
| Q5 | — | Quality | 80.0% | 90.0% | +10.0pp |
| S3 | — | Security | 20.0% | 27.5% | +7.5pp |
| R1 | — | Readability | 15.0% | 20.0% | +5.0pp |
| P1 | — | Performance | 20.0% | 25.0% | +5.0pp |
| F3 | yes | Functionality | 60.0% | 62.5% | +2.5pp |
| C1 | — | Consistency | 0.0% | 2.5% | +2.5pp |
| T2 | yes | Tests | 67.5% | 70.0% | +2.5pp |
| F4 | yes | Functionality | 80.0% | 80.0% | +0.0pp |
| T1 | yes | Tests | 97.5% | 97.5% | +0.0pp |
| M2 | — | Maintainability | 0.0% | 0.0% | +0.0pp |
| M3 | yes | Maintainability | 7.5% | 7.5% | +0.0pp |
| P2 | — | Performance | 2.5% | 2.5% | +0.0pp |
| S1 | — | Security | 17.5% | 17.5% | +0.0pp |
| S2 | — | Security | 0.0% | 0.0% | +0.0pp |
| Q1 | — | Quality | 100.0% | 100.0% | +0.0pp |
| Q2 | yes | Quality | 100.0% | 100.0% | +0.0pp |
| Q3 | — | Quality | 37.5% | 37.5% | +0.0pp |
| Q4 | — | Quality | 0.0% | 0.0% | +0.0pp |
| F2 | — | Functionality | 70.0% | 67.5% | -2.5pp |
| R3 | — | Readability | 7.5% | 5.0% | -2.5pp |
| T3 | yes | Tests | 62.5% | 57.5% | -5.0pp |

**Floor/ceiling criteria** (identical in both arms at 0% or 100%, cannot register any difference): 5 of 25 — M2, Q1, Q2, Q4, S2. These enter the /25 denominator while contributing no variance, so the total score understates any real effect by construction.

**Review length** (characters):

| Arm | mean | median |
|---|---:|---:|
| baseline | 1774 | 1759 |
| rag | 1782 | 1760 |

`rag` is longer than `baseline` on 18 of 40 PRs.

## hybrid vs baseline — per criterion

| ID | KG-relevant | Category | baseline | hybrid | Δ |
|---|---|---|---:|---:|---:|
| M1 | yes | Maintainability | 17.5% | 37.5% | +20.0pp |
| R2 | — | Readability | 7.5% | 22.5% | +15.0pp |
| Q5 | — | Quality | 80.0% | 95.0% | +15.0pp |
| F4 | yes | Functionality | 80.0% | 90.0% | +10.0pp |
| F3 | yes | Functionality | 60.0% | 67.5% | +7.5pp |
| C2 | yes | Consistency | 5.0% | 12.5% | +7.5pp |
| P1 | — | Performance | 20.0% | 25.0% | +5.0pp |
| T2 | yes | Tests | 67.5% | 72.5% | +5.0pp |
| T3 | yes | Tests | 62.5% | 65.0% | +2.5pp |
| P2 | — | Performance | 2.5% | 5.0% | +2.5pp |
| S2 | — | Security | 0.0% | 2.5% | +2.5pp |
| S3 | — | Security | 20.0% | 22.5% | +2.5pp |
| F1 | — | Functionality | 45.0% | 45.0% | +0.0pp |
| T1 | yes | Tests | 97.5% | 97.5% | +0.0pp |
| M2 | — | Maintainability | 0.0% | 0.0% | +0.0pp |
| M3 | yes | Maintainability | 7.5% | 7.5% | +0.0pp |
| C1 | — | Consistency | 0.0% | 0.0% | +0.0pp |
| S1 | — | Security | 17.5% | 17.5% | +0.0pp |
| Q1 | — | Quality | 100.0% | 100.0% | +0.0pp |
| Q2 | yes | Quality | 100.0% | 100.0% | +0.0pp |
| Q4 | — | Quality | 0.0% | 0.0% | +0.0pp |
| Q3 | — | Quality | 37.5% | 35.0% | -2.5pp |
| R1 | — | Readability | 15.0% | 10.0% | -5.0pp |
| F2 | — | Functionality | 70.0% | 62.5% | -7.5pp |
| R3 | — | Readability | 7.5% | 0.0% | -7.5pp |

**Floor/ceiling criteria** (identical in both arms at 0% or 100%, cannot register any difference): 5 of 25 — C1, M2, Q1, Q2, Q4. These enter the /25 denominator while contributing no variance, so the total score understates any real effect by construction.

**Review length** (characters):

| Arm | mean | median |
|---|---:|---:|
| baseline | 1774 | 1759 |
| hybrid | 1857 | 1858 |

`hybrid` is longer than `baseline` on 23 of 40 PRs.
