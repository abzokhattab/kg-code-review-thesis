# Experiment 2 — injection detection results

n = 40 injections (28 structural, 12 local control) · majority of 3 judges, ties→0 · bootstrap B=10000, permutation B=20000, seed=2026

## structural bands (S1, S2, S3, S4, S5) — n=28

| Arm | Detected | Rate [95% CI] |
|---|---:|---:|
| baseline | 0/28 | 0.00 [0.00, 0.00] |
| kg | 15/28 | 0.54 [0.36, 0.71] |
| rag | 1/28 | 0.04 [0.00, 0.11] |
| hybrid | 12/28 | 0.43 [0.25, 0.61] |
| kg_idealised | 26/28 | 0.93 [0.82, 1.00] |
| kg_joern_inherit | 21/28 | 0.75 [0.57, 0.89] |

| Contrast | Δ rate [95% CI] | p (perm) |
|---|---:|---:|
| kg − baseline | +0.54 [+0.36, +0.71] | 0.0000 |
| rag − baseline | +0.04 [+0.00, +0.11] | 1.0000 |
| hybrid − baseline | +0.43 [+0.25, +0.61] | 0.0005 |
| kg_idealised − baseline | +0.93 [+0.82, +1.00] | 0.0000 |
| kg_joern_inherit − kg | +0.21 [+0.04, +0.39] | 0.0714 |

## local_control bands (L1, L2) — n=12

| Arm | Detected | Rate [95% CI] |
|---|---:|---:|
| baseline | 11/12 | 0.92 [0.75, 1.00] |
| kg | 10/12 | 0.83 [0.58, 1.00] |
| rag | 12/12 | 1.00 [1.00, 1.00] |
| hybrid | 11/12 | 0.92 [0.75, 1.00] |
| kg_idealised | 10/12 | 0.83 [0.58, 1.00] |
| kg_joern_inherit | 10/12 | 0.83 [0.58, 1.00] |

| Contrast | Δ rate [95% CI] | p (perm) |
|---|---:|---:|
| kg − baseline | -0.08 [-0.25, +0.00] | 1.0000 |
| rag − baseline | +0.08 [+0.00, +0.25] | 1.0000 |
| hybrid − baseline | +0.00 [-0.25, +0.25] | 1.0000 |
| kg_idealised − baseline | -0.08 [-0.25, +0.00] | 1.0000 |
| kg_joern_inherit − kg | +0.00 [+0.00, +0.00] | 1.0000 |

## S4 (inheritance) band — augmentation check, n=6

kg_joern_inherit − kg on S4: Δ = +0.50 (5/6 vs 2/6)

## Per-injection detail

| id | band | fanout | baseline | kg | rag | hybrid | kg_idealised | kg_joern_inherit |
|---|---|---:|---|---|---|---|---|---|
| sklearn_S4_01 | S4 | 32 | miss | DET | miss | DET | DET | DET |
| sklearn_S4_02 | S4 | 8 | miss | DET | miss | DET | DET | DET |
| sklearn_S3_01 | S3 | 42 | miss | DET | miss | DET | DET | DET |
| sklearn_S2_01 | S2 | 4 | miss | DET | miss | miss | DET | DET |
| sklearn_S2_02 | S2 | 2 | miss | DET | miss | DET | DET | DET |
| sklearn_S2_03 | S2 | 2 | miss | DET | miss | DET | DET | DET |
| sklearn_S1_01 | S1 | 18 | miss | miss | miss | miss | DET | DET |
| sklearn_S1_02 | S1 | 3 | miss | miss | miss | miss | DET | DET |
| sklearn_S1_03 | S1 | 3 | miss | DET | miss | DET | DET | DET |
| sklearn_S5_01 | S5 | 1 | miss | DET | miss | DET | DET | DET |
| sklearn_L1_01 | L1 | 0 | DET | DET | DET | DET | DET | DET |
| sklearn_L1_02 | L1 | 0 | DET | DET | DET | DET | DET | DET |
| sklearn_L2_01 | L2 | 0 | DET | DET | DET | DET | DET | DET |
| sklearn_L2_02 | L2 | 0 | DET | DET | DET | DET | miss | DET |
| kafka_S4_01 | S4 | 26 | miss | miss | miss | miss | DET | DET |
| kafka_S4_02 | S4 | 22 | miss | miss | miss | miss | DET | miss |
| kafka_S2_01 | S2 | 24 | miss | miss | miss | miss | DET | miss |
| kafka_S2_02 | S2 | 21 | miss | miss | miss | miss | DET | miss |
| kafka_S2_03 | S2 | 18 | miss | miss | miss | miss | DET | miss |
| kafka_S1_01 | S1 | 89 | miss | miss | DET | miss | DET | DET |
| kafka_S1_02 | S1 | 82 | miss | miss | miss | miss | miss | miss |
| kafka_S1_03 | S1 | 75 | miss | DET | miss | DET | DET | DET |
| kafka_L1_01 | L1 | 0 | DET | DET | DET | DET | DET | DET |
| kafka_L1_02 | L1 | 0 | DET | DET | DET | DET | DET | DET |
| kafka_L2_01 | L2 | 0 | DET | DET | DET | DET | DET | DET |
| kafka_L2_02 | L2 | 0 | DET | DET | DET | DET | DET | DET |
| grafana_S4_01 | S4 | 4 | miss | miss | miss | miss | DET | DET |
| grafana_S4_02 | S4 | 3 | miss | miss | miss | miss | DET | DET |
| grafana_S2_01 | S2 | 46 | miss | DET | miss | miss | DET | miss |
| grafana_S2_02 | S2 | 23 | miss | miss | miss | DET | DET | miss |
| grafana_S2_03 | S2 | 18 | miss | DET | miss | DET | DET | DET |
| grafana_S1_01 | S1 | 14 | miss | miss | miss | miss | miss | DET |
| grafana_S1_02 | S1 | 13 | miss | DET | miss | DET | DET | DET |
| grafana_S1_03 | S1 | 11 | miss | DET | miss | miss | DET | DET |
| grafana_S5_01 | S5 | 8 | miss | DET | miss | DET | DET | DET |
| grafana_S5_02 | S5 | 7 | miss | DET | miss | miss | DET | DET |
| grafana_L1_01 | L1 | 0 | DET | DET | DET | DET | DET | DET |
| grafana_L1_02 | L1 | 0 | DET | DET | DET | DET | DET | DET |
| grafana_L2_01 | L2 | 0 | DET | miss | DET | miss | DET | miss |
| grafana_L2_02 | L2 | 0 | miss | miss | DET | DET | miss | miss |
