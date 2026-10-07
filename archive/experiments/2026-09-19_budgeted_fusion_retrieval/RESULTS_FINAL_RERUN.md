# Budgeted graph + semantic retrieval: zero-cost gate

**Status:** exploratory development result; not confirmatory and not thesis-quotable as independent resolver validation.

- Cases: 56 (28 dependency, 28 test)
- API/model cost: $0
- Semantic query: first indexed changed-file chunk embedding (proxy)
- Resolver warning: resolved arms reuse the oracle-generating resolver

## Go/no-go decision

**NO-GO** for `deployed_rrf` at the 4,000-token development budget.

| Check | Result | Observed |
|---|:---:|---:|
| dependency: lose zero deployed-graph case hits | pass | none |
| dependency: include semantic-only evidence in >=90% cases | fail | 75.0% |
| dependency: no lower hit-any than deployed naive | pass | 27/28 vs 25/28 |
| dependency: all contexts stay within budget | pass | true |
| dependency: Pareto-dominate deployed naive | pass | hit 96.4%/89.3%; recall 64.8%/47.7%; semantic-only 75.0%/60.7% |
| test: lose zero deployed-graph case hits | pass | none |
| test: include semantic-only evidence in >=90% cases | pass | 100.0% |
| test: no lower hit-any than deployed naive | pass | 27/28 vs 27/28 |
| test: all contexts stay within budget | pass | true |
| test: Pareto-dominate deployed naive | pass | hit 96.4%/96.4%; recall 80.9%/80.8%; semantic-only 100.0%/100.0% |

## Dependency cohort

| Arm | Budget | Hit-any | Mean target recall | Oracle-path fraction | Mixed-source cases | Semantic-only cases | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| `deployed_graph` | 2,000 | 24/28 (85.7%) | 45.3% | 51.9% | 0.0% | 0.0% | 888 |
| `deployed_graph` | 4,000 | 25/28 (89.3%) | 52.6% | 53.8% | 0.0% | 0.0% | 1422 |
| `deployed_graph` | 8,000 | 27/28 (96.4%) | 57.4% | 57.1% | 0.0% | 0.0% | 2223 |
| `resolved_graph` | 2,000 | 28/28 (100.0%) | 80.1% | 94.5% | 0.0% | 0.0% | 1131 |
| `resolved_graph` | 4,000 | 28/28 (100.0%) | 89.3% | 94.7% | 0.0% | 0.0% | 1700 |
| `resolved_graph` | 8,000 | 28/28 (100.0%) | 98.7% | 94.8% | 0.0% | 0.0% | 2472 |
| `rag_proxy` | 2,000 | 27/28 (96.4%) | 32.1% | 40.1% | 0.0% | 100.0% | 1866 |
| `rag_proxy` | 4,000 | 27/28 (96.4%) | 45.3% | 33.6% | 0.0% | 100.0% | 3904 |
| `rag_proxy` | 8,000 | 28/28 (100.0%) | 62.5% | 29.2% | 0.0% | 100.0% | 7880 |
| `deployed_naive` | 2,000 | 23/28 (82.1%) | 36.1% | 44.7% | 96.4% | 17.9% | 1821 |
| `deployed_naive` | 4,000 | 25/28 (89.3%) | 47.7% | 38.5% | 96.4% | 60.7% | 3804 |
| `deployed_naive` | 8,000 | 27/28 (96.4%) | 66.0% | 36.3% | 96.4% | 67.9% | 7834 |
| `deployed_rrf` | 2,000 | 27/28 (96.4%) | 54.9% | 49.5% | 96.4% | 67.9% | 1806 |
| `deployed_rrf` | 4,000 | 27/28 (96.4%) | 64.8% | 39.0% | 96.4% | 75.0% | 3873 |
| `deployed_rrf` | 8,000 | 28/28 (100.0%) | 76.7% | 32.5% | 96.4% | 85.7% | 7800 |
| `deployed_compact` | 2,000 | 25/28 (89.3%) | 52.6% | 39.4% | 64.3% | 67.9% | 1878 |
| `deployed_compact` | 4,000 | 26/28 (92.9%) | 64.9% | 34.8% | 71.4% | 75.0% | 3852 |
| `deployed_compact` | 8,000 | 28/28 (100.0%) | 76.6% | 31.8% | 78.6% | 82.1% | 7789 |
| `resolved_naive` | 2,000 | 27/28 (96.4%) | 50.6% | 75.3% | 100.0% | 28.6% | 1868 |
| `resolved_naive` | 4,000 | 27/28 (96.4%) | 68.0% | 64.7% | 100.0% | 42.9% | 3849 |
| `resolved_naive` | 8,000 | 28/28 (100.0%) | 82.4% | 49.8% | 100.0% | 64.3% | 7851 |
| `resolved_rrf` | 2,000 | 28/28 (100.0%) | 79.2% | 67.1% | 100.0% | 60.7% | 1896 |
| `resolved_rrf` | 4,000 | 28/28 (100.0%) | 88.2% | 52.3% | 100.0% | 75.0% | 3901 |
| `resolved_rrf` | 8,000 | 28/28 (100.0%) | 97.7% | 38.3% | 100.0% | 89.3% | 7750 |
| `resolved_compact` | 2,000 | 28/28 (100.0%) | 80.1% | 65.6% | 64.3% | 64.3% | 1906 |
| `resolved_compact` | 4,000 | 28/28 (100.0%) | 89.3% | 51.7% | 75.0% | 75.0% | 3896 |
| `resolved_compact` | 8,000 | 28/28 (100.0%) | 98.7% | 38.6% | 89.3% | 89.3% | 7745 |

## Test cohort

| Arm | Budget | Hit-any | Mean target recall | Oracle-path fraction | Mixed-source cases | Semantic-only cases | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| `deployed_graph` | 2,000 | 25/28 (89.3%) | 60.6% | 87.5% | 0.0% | 0.0% | 42 |
| `deployed_graph` | 4,000 | 25/28 (89.3%) | 60.6% | 87.5% | 0.0% | 0.0% | 42 |
| `deployed_graph` | 8,000 | 25/28 (89.3%) | 60.6% | 87.5% | 0.0% | 0.0% | 42 |
| `resolved_graph` | 2,000 | 28/28 (100.0%) | 100.0% | 100.0% | 0.0% | 0.0% | 154 |
| `resolved_graph` | 4,000 | 28/28 (100.0%) | 100.0% | 100.0% | 0.0% | 0.0% | 154 |
| `resolved_graph` | 8,000 | 28/28 (100.0%) | 100.0% | 100.0% | 0.0% | 0.0% | 154 |
| `rag_proxy` | 2,000 | 25/28 (89.3%) | 69.7% | 13.7% | 0.0% | 100.0% | 1904 |
| `rag_proxy` | 4,000 | 27/28 (96.4%) | 79.0% | 9.7% | 0.0% | 100.0% | 3873 |
| `rag_proxy` | 8,000 | 28/28 (100.0%) | 87.4% | 6.3% | 0.0% | 100.0% | 7902 |
| `deployed_naive` | 2,000 | 27/28 (96.4%) | 73.0% | 15.1% | 92.9% | 100.0% | 1916 |
| `deployed_naive` | 4,000 | 27/28 (96.4%) | 80.8% | 9.9% | 92.9% | 100.0% | 3867 |
| `deployed_naive` | 8,000 | 28/28 (100.0%) | 87.4% | 6.3% | 92.9% | 100.0% | 7908 |
| `deployed_rrf` | 2,000 | 27/28 (96.4%) | 73.9% | 14.2% | 92.9% | 100.0% | 1911 |
| `deployed_rrf` | 4,000 | 27/28 (96.4%) | 80.9% | 9.6% | 92.9% | 100.0% | 3887 |
| `deployed_rrf` | 8,000 | 28/28 (100.0%) | 87.4% | 6.1% | 92.9% | 100.0% | 7881 |
| `deployed_compact` | 2,000 | 27/28 (96.4%) | 75.1% | 14.5% | 92.9% | 100.0% | 1917 |
| `deployed_compact` | 4,000 | 27/28 (96.4%) | 80.9% | 9.6% | 92.9% | 100.0% | 3893 |
| `deployed_compact` | 8,000 | 28/28 (100.0%) | 87.4% | 6.1% | 92.9% | 100.0% | 7878 |
| `resolved_naive` | 2,000 | 28/28 (100.0%) | 95.9% | 30.5% | 100.0% | 92.9% | 1882 |
| `resolved_naive` | 4,000 | 28/28 (100.0%) | 97.5% | 16.7% | 100.0% | 96.4% | 3877 |
| `resolved_naive` | 8,000 | 28/28 (100.0%) | 98.7% | 10.0% | 100.0% | 96.4% | 7899 |
| `resolved_rrf` | 2,000 | 28/28 (100.0%) | 99.8% | 22.9% | 100.0% | 96.4% | 1914 |
| `resolved_rrf` | 4,000 | 28/28 (100.0%) | 100.0% | 14.0% | 100.0% | 100.0% | 3867 |
| `resolved_rrf` | 8,000 | 28/28 (100.0%) | 100.0% | 8.1% | 100.0% | 100.0% | 7888 |
| `resolved_compact` | 2,000 | 28/28 (100.0%) | 100.0% | 22.9% | 96.4% | 96.4% | 1907 |
| `resolved_compact` | 4,000 | 28/28 (100.0%) | 100.0% | 13.9% | 100.0% | 100.0% | 3868 |
| `resolved_compact` | 8,000 | 28/28 (100.0%) | 100.0% | 8.1% | 100.0% | 100.0% | 7887 |

## All cohort (descriptive only)

| Arm | Budget | Hit-any | Mean target recall | Oracle-path fraction | Mixed-source cases | Semantic-only cases | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| `deployed_graph` | 2,000 | 49/56 (87.5%) | 53.0% | 69.7% | 0.0% | 0.0% | 465 |
| `deployed_graph` | 4,000 | 50/56 (89.3%) | 56.6% | 70.7% | 0.0% | 0.0% | 732 |
| `deployed_graph` | 8,000 | 52/56 (92.9%) | 59.0% | 72.3% | 0.0% | 0.0% | 1133 |
| `resolved_graph` | 2,000 | 56/56 (100.0%) | 90.0% | 97.3% | 0.0% | 0.0% | 643 |
| `resolved_graph` | 4,000 | 56/56 (100.0%) | 94.6% | 97.4% | 0.0% | 0.0% | 927 |
| `resolved_graph` | 8,000 | 56/56 (100.0%) | 99.3% | 97.4% | 0.0% | 0.0% | 1313 |
| `rag_proxy` | 2,000 | 52/56 (92.9%) | 50.9% | 26.9% | 0.0% | 100.0% | 1885 |
| `rag_proxy` | 4,000 | 54/56 (96.4%) | 62.2% | 21.6% | 0.0% | 100.0% | 3888 |
| `rag_proxy` | 8,000 | 56/56 (100.0%) | 74.9% | 17.7% | 0.0% | 100.0% | 7891 |
| `deployed_naive` | 2,000 | 50/56 (89.3%) | 54.6% | 29.9% | 94.6% | 58.9% | 1868 |
| `deployed_naive` | 4,000 | 52/56 (92.9%) | 64.2% | 24.2% | 94.6% | 80.4% | 3835 |
| `deployed_naive` | 8,000 | 55/56 (98.2%) | 76.7% | 21.3% | 94.6% | 83.9% | 7871 |
| `deployed_rrf` | 2,000 | 54/56 (96.4%) | 64.4% | 31.9% | 94.6% | 83.9% | 1859 |
| `deployed_rrf` | 4,000 | 54/56 (96.4%) | 72.8% | 24.3% | 94.6% | 87.5% | 3880 |
| `deployed_rrf` | 8,000 | 56/56 (100.0%) | 82.0% | 19.3% | 94.6% | 92.9% | 7840 |
| `deployed_compact` | 2,000 | 52/56 (92.9%) | 63.8% | 27.0% | 78.6% | 83.9% | 1898 |
| `deployed_compact` | 4,000 | 53/56 (94.6%) | 72.9% | 22.2% | 82.1% | 87.5% | 3873 |
| `deployed_compact` | 8,000 | 56/56 (100.0%) | 82.0% | 19.0% | 85.7% | 91.1% | 7834 |
| `resolved_naive` | 2,000 | 55/56 (98.2%) | 73.3% | 52.9% | 100.0% | 60.7% | 1875 |
| `resolved_naive` | 4,000 | 55/56 (98.2%) | 82.8% | 40.7% | 100.0% | 69.6% | 3863 |
| `resolved_naive` | 8,000 | 56/56 (100.0%) | 90.5% | 29.9% | 100.0% | 80.4% | 7875 |
| `resolved_rrf` | 2,000 | 56/56 (100.0%) | 89.5% | 45.0% | 100.0% | 78.6% | 1905 |
| `resolved_rrf` | 4,000 | 56/56 (100.0%) | 94.1% | 33.1% | 100.0% | 87.5% | 3884 |
| `resolved_rrf` | 8,000 | 56/56 (100.0%) | 98.9% | 23.2% | 100.0% | 94.6% | 7819 |
| `resolved_compact` | 2,000 | 56/56 (100.0%) | 90.0% | 44.3% | 80.4% | 80.4% | 1906 |
| `resolved_compact` | 4,000 | 56/56 (100.0%) | 94.6% | 32.8% | 87.5% | 87.5% | 3882 |
| `resolved_compact` | 8,000 | 56/56 (100.0%) | 99.3% | 23.3% | 94.6% | 94.6% | 7816 |

## Structural cohort at 4k by repository and band

| Group | Arm | Hit-any | Macro recall | Semantic-only cases |
|---|---|---:|---:|---:|
| repo=grafana | `deployed_graph` | 9/10 | 42.0% | 0.0% |
| repo=grafana | `deployed_naive` | 10/10 | 51.5% | 80.0% |
| repo=grafana | `deployed_rrf` | 10/10 | 64.7% | 100.0% |
| repo=kafka | `deployed_graph` | 6/8 | 34.1% | 0.0% |
| repo=kafka | `deployed_naive` | 5/8 | 8.1% | 0.0% |
| repo=kafka | `deployed_rrf` | 7/8 | 34.0% | 12.5% |
| repo=sklearn | `deployed_graph` | 10/10 | 78.1% | 0.0% |
| repo=sklearn | `deployed_naive` | 10/10 | 75.6% | 90.0% |
| repo=sklearn | `deployed_rrf` | 10/10 | 89.5% | 100.0% |
| band=S1 | `deployed_graph` | 9/9 | 46.0% | 0.0% |
| band=S1 | `deployed_naive` | 9/9 | 41.9% | 55.6% |
| band=S1 | `deployed_rrf` | 9/9 | 58.3% | 77.8% |
| band=S2 | `deployed_graph` | 8/9 | 62.4% | 0.0% |
| band=S2 | `deployed_naive` | 7/9 | 47.8% | 55.6% |
| band=S2 | `deployed_rrf` | 9/9 | 66.3% | 66.7% |
| band=S3 | `deployed_graph` | 1/1 | 100.0% | 0.0% |
| band=S3 | `deployed_naive` | 1/1 | 33.3% | 0.0% |
| band=S3 | `deployed_rrf` | 1/1 | 100.0% | 100.0% |
| band=S4 | `deployed_graph` | 4/6 | 34.1% | 0.0% |
| band=S4 | `deployed_naive` | 5/6 | 50.3% | 66.7% |
| band=S4 | `deployed_rrf` | 5/6 | 66.6% | 66.7% |
| band=S5 | `deployed_graph` | 3/3 | 64.3% | 0.0% |
| band=S5 | `deployed_naive` | 3/3 | 64.3% | 100.0% |
| band=S5 | `deployed_rrf` | 3/3 | 64.3% | 100.0% |

## Interpretation limits

1. All `resolved_*` arms are packing/fusion upper bounds because the same resolver produced the oracle labels.
2. `rag_proxy` reuses a saved changed-file chunk vector; it is not the deployed full-prefix query embedding.
3. Hit-any measures evidence availability, not review correctness.
4. A pass permits only a pre-registered held-out generation test.
