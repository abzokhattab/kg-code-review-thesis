# Experiment 2 feature ablation — which kind of edge finds the defect

Pre-registered in `experiments/2026-07-05_injection_exp2/docs/PRE_REGISTRATION_feature_ablation.md` before any review existed.

The deployed `kg` arm supplies two kinds of dependency evidence at once. These arms hold everything else fixed — generator, prompt, diff, changed-file list, changed-symbol list — and supply one each:

| Arm | Evidence supplied | Granularity | Precision |
|---|---|---|---|
| `kg_deps_only` | lexical `grep` file list | file | 10.2% |
| `kg_edges_only` | Joern CPG call edges | function | program analysis |

Run on Experiment 2 rather than the coverage rubric because the rubric moves 0.6 points against a measured 0.88-point generation noise floor, while these bands run 0/28 to 26/28 on a binary outcome.

## structural bands (n = 28)

| Arm | Detected | Rate | 95% Wilson |
|---|---:|---:|---|
| `baseline` | 0/28 | 0% | [0.00, 0.12] |
| `rag` | 1/28 | 4% | [0.01, 0.18] |
| `kg_deps_only` | 9/28 | 32% | [0.18, 0.51] |
| `kg_edges_only` | 12/28 | 43% | [0.27, 0.61] |
| `kg` | 15/28 | 54% | [0.36, 0.70] |
| `kg_joern_inherit` | 21/28 | 75% | [0.57, 0.87] |
| `kg_idealised` | 26/28 | 93% | [0.77, 0.98] |
| `hybrid` | 12/28 | 43% | [0.27, 0.61] |

| Contrast | Δ rate | 95% CI | discordant | McNemar (exact) | p (Holm) |
|---|---:|---|---:|---:|---:|
| kg_deps_only - baseline | +32% | [+0.14, +0.50] | 9/0 | 0.0039 | 0.0117 ** |
| kg_edges_only - baseline | +43% | [+0.25, +0.61] | 12/0 | 0.0005 | 0.0020 ** |
| kg_deps_only - kg | -21% | [-0.43, +0.00] | 3/9 | 0.1460 | 0.2920 |
| kg_edges_only - kg | -11% | [-0.21, +0.00] | 0/3 | 0.2500 | 0.2920 |

## local control bands (n = 12)

| Arm | Detected | Rate | 95% Wilson |
|---|---:|---:|---|
| `baseline` | 11/12 | 92% | [0.65, 0.99] |
| `rag` | 12/12 | 100% | [0.76, 1.00] |
| `kg_deps_only` | 12/12 | 100% | [0.76, 1.00] |
| `kg_edges_only` | 10/12 | 83% | [0.55, 0.95] |
| `kg` | 10/12 | 83% | [0.55, 0.95] |
| `kg_joern_inherit` | 10/12 | 83% | [0.55, 0.95] |
| `kg_idealised` | 10/12 | 83% | [0.55, 0.95] |
| `hybrid` | 11/12 | 92% | [0.65, 0.99] |

| Contrast | Δ rate | 95% CI | discordant | McNemar (exact) | p (Holm) |
|---|---:|---|---:|---:|---:|
| kg_deps_only - baseline | +8% | [+0.00, +0.25] | 1/0 | 1.0000 | 1.0000 |
| kg_edges_only - baseline | -8% | [-0.25, +0.00] | 0/1 | 1.0000 | 1.0000 |
| kg_deps_only - kg | +17% | [+0.00, +0.42] | 2/0 | 0.5000 | 1.0000 |
| kg_edges_only - kg | +0% | [-0.25, +0.25] | 1/1 | 1.0000 | 1.0000 |

