# Deep audit — clean Joern (normal prompt) run

**Pairs analyzed:** n=35 (clean-Joern KG vs headline baseline)

## 1. Per-criterion contribution to the KG-rel delta

Sorted by mean delta (kg_score − baseline_score). KG-rel criteria (the 9 the rubric calls KG-relevant) flagged.

| Criterion | KG-rel? | n | Baseline yes | KG yes | Δ yes | Mean Δ | SD Δ |
|---|:---:|---:|---:|---:|---:|---:|---:|
| Q5 |  | 35 | 28 | 35 | +7 | +0.200 | 0.406 |
| F3 | ✓ | 35 | 22 | 28 | +6 | +0.171 | 0.568 |
| Q3 |  | 35 | 12 | 17 | +5 | +0.143 | 0.692 |
| S3 |  | 35 | 5 | 8 | +3 | +0.086 | 0.445 |
| P1 |  | 35 | 5 | 8 | +3 | +0.086 | 0.445 |
| T3 | ✓ | 35 | 23 | 26 | +3 | +0.086 | 0.507 |
| R2 |  | 35 | 2 | 4 | +2 | +0.057 | 0.338 |
| F4 | ✓ | 35 | 28 | 30 | +2 | +0.057 | 0.482 |
| F2 |  | 35 | 24 | 25 | +1 | +0.029 | 0.382 |
| M1 | ✓ | 35 | 6 | 7 | +1 | +0.029 | 0.568 |
| T2 | ✓ | 35 | 23 | 24 | +1 | +0.029 | 0.169 |
| P2 |  | 35 | 0 | 0 | +0 | +0.000 | 0.000 |
| C1 |  | 35 | 0 | 0 | +0 | +0.000 | 0.000 |
| M2 |  | 35 | 0 | 0 | +0 | +0.000 | 0.000 |
| T1 | ✓ | 35 | 34 | 34 | +0 | +0.000 | 0.243 |
| Q1 |  | 35 | 35 | 35 | +0 | +0.000 | 0.000 |
| Q2 | ✓ | 35 | 35 | 35 | +0 | +0.000 | 0.000 |
| S2 |  | 35 | 0 | 0 | +0 | +0.000 | 0.000 |
| C2 | ✓ | 35 | 1 | 1 | +0 | +0.000 | 0.243 |
| Q4 |  | 35 | 0 | 0 | +0 | +0.000 | 0.000 |
| M3 | ✓ | 35 | 3 | 2 | -1 | -0.029 | 0.296 |
| F1 |  | 35 | 15 | 13 | -2 | -0.057 | 0.338 |
| R3 |  | 35 | 3 | 0 | -3 | -0.086 | 0.284 |
| S1 |  | 35 | 4 | 1 | -3 | -0.086 | 0.284 |
| R1 |  | 35 | 5 | 2 | -3 | -0.086 | 0.373 |

**KG-rel criteria contributing positively (n=5):** F3 (+0.17), T3 (+0.09), F4 (+0.06), M1 (+0.03), T2 (+0.03)

**KG-rel criteria contributing negatively (n=1):** M3 (-0.03)

## 2. Per-language stratification

| Language | n | Mean Δ KG-rel | d_z KG-rel | Mean Δ total | d_z total | PRs |
|---|---:|---:|---:|---:|---:|:---|
| Java | 11 | +0.545 | +0.584 | +1.091 | +0.839 | 6,18,19,21,22,29,33,40… |
| Python | 8 | +0.000 | +0.000 | -0.875 | -0.533 | 10,23,24,31,32,42,43,44 |
| TypeScript | 8 | +0.750 | +0.540 | +1.000 | +0.408 | 2,3,8,14,15,28,34,38 |
| C++ | 6 | +0.000 | +0.000 | +1.500 | +0.723 | 1,12,13,30,45,46 |
| Scala | 2 | +0.000 | +0.000 | +0.000 | +0.000 | 20,39 |

**Reading:** stratify only on languages with n≥5. Strata with n<5 are noise.

- **Java** (n=11): KG-rel d_z=+0.58 → **positive**.
- **Python** (n=8): KG-rel d_z=+0.00 → **near-null**.
- **TypeScript** (n=8): KG-rel d_z=+0.54 → **positive**.
- **C++** (n=6): KG-rel d_z=+0.00 → **near-null**.

## 3. Judge unanimity

**Overall:** 675/875 cells unanimous = **77.1%**

Per-PR unanimity rate (sorted by PR):

| PR | Unanimous / 25 | Frac |
|---:|---:|---:|
| 1 | 20 | 80% |
| 2 | 21 | 84% |
| 3 | 22 | 88% |
| 6 | 16 | 64% |
| 8 | 19 | 76% |
| 10 | 18 | 72% |
| 12 | 15 | 60% |
| 13 | 21 | 84% |
| 14 | 18 | 72% |
| 15 | 16 | 64% |
| 18 | 22 | 88% |
| 19 | 18 | 72% |
| 20 | 18 | 72% |
| 21 | 17 | 68% |
| 22 | 21 | 84% |
| 23 | 19 | 76% |
| 24 | 20 | 80% |
| 28 | 18 | 72% |
| 29 | 20 | 80% |
| 30 | 19 | 76% |
| 31 | 20 | 80% |
| 32 | 20 | 80% |
| 33 | 21 | 84% |
| 34 | 17 | 68% |
| 38 | 22 | 88% |
| 39 | 22 | 88% |
| 40 | 21 | 84% |
| 41 | 19 | 76% |
| 42 | 21 | 84% |
| 43 | 19 | 76% |
| 44 | 19 | 76% |
| 45 | 15 | 60% |
| 46 | 20 | 80% |
| 47 | 19 | 76% |
| 48 | 22 | 88% |

Reading: lower unanimity = judges split = closer-to-tie scores.
If overall unanimity is well below 70%, the headline d_z is being driven
by judges leaning the same direction without consensus — a softer signal.
If above 70%, the effect is judge-robust.
