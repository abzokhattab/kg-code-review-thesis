# Budgeted graph + semantic retrieval: zero-cost gate

**Status:** exploratory development result; not confirmatory and not thesis-quotable as independent resolver validation.

- Cases: 56 (28 dependency, 28 test)
- API/model cost: $0
- Semantic query: first indexed changed-file chunk embedding (proxy)
- Resolver warning: resolved arms reuse the oracle-generating resolver

## Go/no-go decision

**NO-GO** at the 4,000-token development budget.

| Check | Result | Observed |
|---|:---:|---:|
| dependency: preserve resolved-graph hit-any | pass | 28/28 vs 28/28 |
| dependency: include semantic-only evidence in >=90% cases | fail | 64.3% |
| dependency: no lower hit-any than resolved naive | pass | 28/28 vs 28/28 |
| dependency: all contexts stay within budget | pass | true |
| test: preserve resolved-graph hit-any | pass | 28/28 vs 28/28 |
| test: include semantic-only evidence in >=90% cases | pass | 100.0% |
| test: no lower hit-any than resolved naive | pass | 28/28 vs 28/28 |
| test: all contexts stay within budget | pass | true |

## Dependency cohort

| Arm | Budget | Hit-any | Mean target recall | Precision | Mixed-source cases | Semantic-only cases | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| `deployed_graph` | 2,000 | 26/28 (92.9%) | 47.1% | 59.3% | 0.0% | 0.0% | 941 |
| `deployed_graph` | 4,000 | 26/28 (92.9%) | 52.4% | 57.2% | 0.0% | 0.0% | 1491 |
| `deployed_graph` | 8,000 | 27/28 (96.4%) | 57.7% | 57.1% | 0.0% | 0.0% | 2239 |
| `resolved_graph` | 2,000 | 28/28 (100.0%) | 86.3% | 100.0% | 0.0% | 0.0% | 993 |
| `resolved_graph` | 4,000 | 28/28 (100.0%) | 93.5% | 100.0% | 0.0% | 0.0% | 1403 |
| `resolved_graph` | 8,000 | 28/28 (100.0%) | 99.5% | 100.0% | 0.0% | 0.0% | 1852 |
| `rag_proxy` | 2,000 | 27/28 (96.4%) | 32.1% | 38.0% | 0.0% | 100.0% | 1929 |
| `rag_proxy` | 4,000 | 27/28 (96.4%) | 45.3% | 33.3% | 0.0% | 100.0% | 3936 |
| `rag_proxy` | 8,000 | 28/28 (100.0%) | 62.5% | 29.0% | 0.0% | 100.0% | 7933 |
| `deployed_naive` | 2,000 | 27/28 (96.4%) | 37.6% | 53.1% | 96.4% | 42.9% | 1953 |
| `deployed_naive` | 4,000 | 26/28 (92.9%) | 49.7% | 43.4% | 96.4% | 82.1% | 3947 |
| `deployed_naive` | 8,000 | 27/28 (96.4%) | 66.3% | 38.2% | 96.4% | 71.4% | 7940 |
| `deployed_rrf` | 2,000 | 27/28 (96.4%) | 38.5% | 53.6% | 96.4% | 46.4% | 1950 |
| `deployed_rrf` | 4,000 | 26/28 (92.9%) | 50.4% | 44.2% | 96.4% | 78.6% | 3934 |
| `deployed_rrf` | 8,000 | 28/28 (100.0%) | 67.5% | 39.0% | 96.4% | 78.6% | 7930 |
| `resolved_naive` | 2,000 | 28/28 (100.0%) | 55.3% | 76.4% | 100.0% | 64.3% | 1943 |
| `resolved_naive` | 4,000 | 28/28 (100.0%) | 72.1% | 66.8% | 100.0% | 64.3% | 3944 |
| `resolved_naive` | 8,000 | 28/28 (100.0%) | 87.9% | 52.6% | 100.0% | 82.1% | 7946 |
| `resolved_rrf` | 2,000 | 28/28 (100.0%) | 55.6% | 75.3% | 100.0% | 71.4% | 1947 |
| `resolved_rrf` | 4,000 | 28/28 (100.0%) | 72.1% | 66.6% | 100.0% | 64.3% | 3951 |
| `resolved_rrf` | 8,000 | 28/28 (100.0%) | 87.9% | 53.0% | 100.0% | 78.6% | 7945 |

## Test cohort

| Arm | Budget | Hit-any | Mean target recall | Precision | Mixed-source cases | Semantic-only cases | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| `deployed_graph` | 2,000 | 25/28 (89.3%) | 60.6% | 87.5% | 0.0% | 0.0% | 42 |
| `deployed_graph` | 4,000 | 25/28 (89.3%) | 60.6% | 87.5% | 0.0% | 0.0% | 42 |
| `deployed_graph` | 8,000 | 25/28 (89.3%) | 60.6% | 87.5% | 0.0% | 0.0% | 42 |
| `resolved_graph` | 2,000 | 28/28 (100.0%) | 99.8% | 100.0% | 0.0% | 0.0% | 160 |
| `resolved_graph` | 4,000 | 28/28 (100.0%) | 100.0% | 100.0% | 0.0% | 0.0% | 163 |
| `resolved_graph` | 8,000 | 28/28 (100.0%) | 100.0% | 100.0% | 0.0% | 0.0% | 163 |
| `rag_proxy` | 2,000 | 26/28 (92.9%) | 71.4% | 13.3% | 0.0% | 100.0% | 1974 |
| `rag_proxy` | 4,000 | 27/28 (96.4%) | 79.0% | 9.2% | 0.0% | 100.0% | 3975 |
| `rag_proxy` | 8,000 | 28/28 (100.0%) | 87.4% | 6.2% | 0.0% | 100.0% | 7973 |
| `deployed_naive` | 2,000 | 27/28 (96.4%) | 73.0% | 14.3% | 92.9% | 100.0% | 1974 |
| `deployed_naive` | 4,000 | 27/28 (96.4%) | 80.8% | 9.3% | 92.9% | 100.0% | 3975 |
| `deployed_naive` | 8,000 | 28/28 (100.0%) | 87.4% | 6.2% | 92.9% | 100.0% | 7973 |
| `deployed_rrf` | 2,000 | 27/28 (96.4%) | 73.0% | 14.3% | 92.9% | 100.0% | 1974 |
| `deployed_rrf` | 4,000 | 27/28 (96.4%) | 80.8% | 9.3% | 92.9% | 100.0% | 3975 |
| `deployed_rrf` | 8,000 | 28/28 (100.0%) | 87.4% | 6.2% | 92.9% | 100.0% | 7973 |
| `resolved_naive` | 2,000 | 28/28 (100.0%) | 95.9% | 26.9% | 100.0% | 100.0% | 1972 |
| `resolved_naive` | 4,000 | 28/28 (100.0%) | 97.5% | 16.0% | 100.0% | 100.0% | 3978 |
| `resolved_naive` | 8,000 | 28/28 (100.0%) | 98.7% | 9.8% | 100.0% | 96.4% | 7976 |
| `resolved_rrf` | 2,000 | 28/28 (100.0%) | 96.3% | 27.7% | 100.0% | 96.4% | 1971 |
| `resolved_rrf` | 4,000 | 28/28 (100.0%) | 97.5% | 16.0% | 100.0% | 100.0% | 3978 |
| `resolved_rrf` | 8,000 | 28/28 (100.0%) | 98.7% | 9.7% | 100.0% | 100.0% | 7977 |

## All cohort

| Arm | Budget | Hit-any | Mean target recall | Precision | Mixed-source cases | Semantic-only cases | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| `deployed_graph` | 2,000 | 51/56 (91.1%) | 53.8% | 73.4% | 0.0% | 0.0% | 491 |
| `deployed_graph` | 4,000 | 51/56 (91.1%) | 56.5% | 72.4% | 0.0% | 0.0% | 766 |
| `deployed_graph` | 8,000 | 52/56 (92.9%) | 59.1% | 72.3% | 0.0% | 0.0% | 1140 |
| `resolved_graph` | 2,000 | 56/56 (100.0%) | 93.1% | 100.0% | 0.0% | 0.0% | 577 |
| `resolved_graph` | 4,000 | 56/56 (100.0%) | 96.8% | 100.0% | 0.0% | 0.0% | 783 |
| `resolved_graph` | 8,000 | 56/56 (100.0%) | 99.7% | 100.0% | 0.0% | 0.0% | 1008 |
| `rag_proxy` | 2,000 | 53/56 (94.6%) | 51.8% | 25.6% | 0.0% | 100.0% | 1951 |
| `rag_proxy` | 4,000 | 54/56 (96.4%) | 62.2% | 21.3% | 0.0% | 100.0% | 3956 |
| `rag_proxy` | 8,000 | 56/56 (100.0%) | 74.9% | 17.6% | 0.0% | 100.0% | 7953 |
| `deployed_naive` | 2,000 | 54/56 (96.4%) | 55.3% | 33.7% | 94.6% | 71.4% | 1964 |
| `deployed_naive` | 4,000 | 53/56 (94.6%) | 65.2% | 26.4% | 94.6% | 91.1% | 3961 |
| `deployed_naive` | 8,000 | 55/56 (98.2%) | 76.9% | 22.2% | 94.6% | 85.7% | 7957 |
| `deployed_rrf` | 2,000 | 54/56 (96.4%) | 55.7% | 34.0% | 94.6% | 73.2% | 1962 |
| `deployed_rrf` | 4,000 | 53/56 (94.6%) | 65.6% | 26.8% | 94.6% | 89.3% | 3955 |
| `deployed_rrf` | 8,000 | 56/56 (100.0%) | 77.5% | 22.6% | 94.6% | 89.3% | 7952 |
| `resolved_naive` | 2,000 | 56/56 (100.0%) | 75.6% | 51.6% | 100.0% | 82.1% | 1957 |
| `resolved_naive` | 4,000 | 56/56 (100.0%) | 84.8% | 41.4% | 100.0% | 82.1% | 3961 |
| `resolved_naive` | 8,000 | 56/56 (100.0%) | 93.3% | 31.2% | 100.0% | 89.3% | 7961 |
| `resolved_rrf` | 2,000 | 56/56 (100.0%) | 75.9% | 51.5% | 100.0% | 83.9% | 1959 |
| `resolved_rrf` | 4,000 | 56/56 (100.0%) | 84.8% | 41.3% | 100.0% | 82.1% | 3964 |
| `resolved_rrf` | 8,000 | 56/56 (100.0%) | 93.3% | 31.3% | 100.0% | 89.3% | 7961 |

## Interpretation limits

1. `resolved_graph` and `resolved_rrf` are packing/fusion upper bounds because the same resolver produced the oracle labels.
2. `rag_proxy` reuses a saved changed-file chunk vector; it is not the deployed full-prefix query embedding.
3. Hit-any measures evidence availability, not review correctness.
4. A pass permits only a pre-registered held-out generation test.
