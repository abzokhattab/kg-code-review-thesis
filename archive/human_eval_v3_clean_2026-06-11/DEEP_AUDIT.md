# Deep audit — clean Joern (normal prompt) run

**Pairs analyzed:** n=35 (clean-Joern KG vs headline baseline)

## 1. Per-criterion contribution to the KG-rel delta

Sorted by mean delta (kg_score − baseline_score). KG-rel criteria (the 9 the rubric calls KG-relevant) flagged.

| Criterion | KG-rel? | n | Baseline yes | KG yes | Δ yes | Mean Δ | SD Δ |
|---|:---:|---:|---:|---:|---:|---:|---:|
| Q5 |  | 35 | 28 | 35 | +7 | +0.200 | 0.406 |
| M1 | ✓ | 35 | 6 | 13 | +7 | +0.200 | 0.632 |
| P1 |  | 35 | 5 | 10 | +5 | +0.143 | 0.430 |
| C2 | ✓ | 35 | 1 | 6 | +5 | +0.143 | 0.430 |
| F3 | ✓ | 35 | 22 | 27 | +5 | +0.143 | 0.494 |
| R2 |  | 35 | 2 | 6 | +4 | +0.114 | 0.404 |
| F4 | ✓ | 35 | 28 | 32 | +4 | +0.114 | 0.471 |
| T3 | ✓ | 35 | 23 | 26 | +3 | +0.086 | 0.445 |
| Q3 |  | 35 | 12 | 15 | +3 | +0.086 | 0.562 |
| S3 |  | 35 | 5 | 7 | +2 | +0.057 | 0.416 |
| F2 |  | 35 | 24 | 25 | +1 | +0.029 | 0.382 |
| T2 | ✓ | 35 | 23 | 24 | +1 | +0.029 | 0.453 |
| P2 |  | 35 | 0 | 1 | +1 | +0.029 | 0.169 |
| Q4 |  | 35 | 0 | 0 | +0 | +0.000 | 0.000 |
| T1 | ✓ | 35 | 34 | 34 | +0 | +0.000 | 0.243 |
| C1 |  | 35 | 0 | 0 | +0 | +0.000 | 0.000 |
| Q1 |  | 35 | 35 | 35 | +0 | +0.000 | 0.000 |
| S2 |  | 35 | 0 | 0 | +0 | +0.000 | 0.000 |
| Q2 | ✓ | 35 | 35 | 35 | +0 | +0.000 | 0.000 |
| M2 |  | 35 | 0 | 0 | +0 | +0.000 | 0.000 |
| R1 |  | 35 | 5 | 4 | -1 | -0.029 | 0.382 |
| M3 | ✓ | 35 | 3 | 2 | -1 | -0.029 | 0.296 |
| F1 |  | 35 | 15 | 14 | -1 | -0.029 | 0.568 |
| S1 |  | 35 | 4 | 3 | -1 | -0.029 | 0.296 |
| R3 |  | 35 | 3 | 0 | -3 | -0.086 | 0.284 |

**KG-rel criteria contributing positively (n=6):** M1 (+0.20), C2 (+0.14), F3 (+0.14), F4 (+0.11), T3 (+0.09), T2 (+0.03)

**KG-rel criteria contributing negatively (n=1):** M3 (-0.03)

## 2. Per-language stratification

| Language | n | Mean Δ KG-rel | d_z KG-rel | Mean Δ total | d_z total | PRs |
|---|---:|---:|---:|---:|---:|:---|
| Java | 11 | +0.545 | +0.449 | +1.364 | +0.870 | 6,18,19,21,22,29,33,40… |
| Python | 8 | +1.125 | +1.135 | +0.875 | +0.338 | 10,23,24,31,32,42,43,44 |
| TypeScript | 8 | +1.250 | +1.410 | +1.375 | +0.778 | 2,3,8,14,15,28,34,38 |
| C++ | 6 | -0.167 | -0.221 | +1.333 | +0.886 | 1,12,13,30,45,46 |
| Scala | 2 | +0.000 | +0.000 | +0.000 | +0.000 | 20,39 |

**Reading:** stratify only on languages with n≥5. Strata with n<5 are noise.

- **Java** (n=11): KG-rel d_z=+0.45 → **positive**.
- **Python** (n=8): KG-rel d_z=+1.14 → **positive**.
- **TypeScript** (n=8): KG-rel d_z=+1.41 → **positive**.
- **C++** (n=6): KG-rel d_z=-0.22 → **near-null**.

## 3. Judge unanimity

**Overall:** 660/875 cells unanimous = **75.4%**

Per-PR unanimity rate (sorted by PR):

| PR | Unanimous / 25 | Frac |
|---:|---:|---:|
| 1 | 20 | 80% |
| 2 | 20 | 80% |
| 3 | 20 | 80% |
| 6 | 19 | 76% |
| 8 | 21 | 84% |
| 10 | 19 | 76% |
| 12 | 14 | 56% |
| 13 | 22 | 88% |
| 14 | 20 | 80% |
| 15 | 18 | 72% |
| 18 | 18 | 72% |
| 19 | 19 | 76% |
| 20 | 16 | 64% |
| 21 | 20 | 80% |
| 22 | 22 | 88% |
| 23 | 16 | 64% |
| 24 | 18 | 72% |
| 28 | 20 | 80% |
| 29 | 18 | 72% |
| 30 | 19 | 76% |
| 31 | 18 | 72% |
| 32 | 19 | 76% |
| 33 | 18 | 72% |
| 34 | 21 | 84% |
| 38 | 19 | 76% |
| 39 | 21 | 84% |
| 40 | 22 | 88% |
| 41 | 20 | 80% |
| 42 | 20 | 80% |
| 43 | 18 | 72% |
| 44 | 18 | 72% |
| 45 | 16 | 64% |
| 46 | 15 | 60% |
| 47 | 17 | 68% |
| 48 | 19 | 76% |

Reading: lower unanimity = judges split = closer-to-tie scores.
If overall unanimity is well below 70%, the headline d_z is being driven
by judges leaning the same direction without consensus — a softer signal.
If above 70%, the effect is judge-robust.
