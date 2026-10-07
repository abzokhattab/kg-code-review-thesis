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
| dependency: include semantic-only evidence in >=90% cases | fail | 60.7% |
| dependency: no lower hit-any than deployed naive | pass | 27/28 vs 25/28 |
| dependency: all contexts stay within budget | pass | true |
| dependency: Pareto-dominate deployed naive | pass | hit 96.4%/89.3%; recall 50.2%/47.7%; semantic-only 60.7%/60.7% |
| test: lose zero deployed-graph case hits | pass | none |
| test: include semantic-only evidence in >=90% cases | pass | 100.0% |
| test: no lower hit-any than deployed naive | pass | 27/28 vs 27/28 |
| test: all contexts stay within budget | pass | true |
| test: Pareto-dominate deployed naive | fail | hit 96.4%/96.4%; recall 80.8%/80.8%; semantic-only 100.0%/100.0% |

## Dependency cohort

| Arm | Budget | Hit-any | Mean target recall | Oracle-path fraction | Mixed-source cases | Semantic-only cases | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| `deployed_graph` | 2,000 | 24/28 (85.7%) | 45.3% | 51.9% | 0.0% | 0.0% | 892 |
| `deployed_graph` | 4,000 | 25/28 (89.3%) | 52.6% | 53.8% | 0.0% | 0.0% | 1427 |
| `deployed_graph` | 8,000 | 27/28 (96.4%) | 57.3% | 57.0% | 0.0% | 0.0% | 2222 |
| `resolved_graph` | 2,000 | 28/28 (100.0%) | 80.1% | 94.5% | 0.0% | 0.0% | 1135 |
| `resolved_graph` | 4,000 | 28/28 (100.0%) | 89.1% | 94.7% | 0.0% | 0.0% | 1700 |
| `resolved_graph` | 8,000 | 28/28 (100.0%) | 98.7% | 94.8% | 0.0% | 0.0% | 2478 |
| `rag_proxy` | 2,000 | 27/28 (96.4%) | 32.1% | 40.1% | 0.0% | 100.0% | 1868 |
| `rag_proxy` | 4,000 | 27/28 (96.4%) | 45.3% | 33.6% | 0.0% | 100.0% | 3909 |
| `rag_proxy` | 8,000 | 28/28 (100.0%) | 62.5% | 29.3% | 0.0% | 100.0% | 7872 |
| `deployed_naive` | 2,000 | 23/28 (82.1%) | 36.1% | 44.7% | 96.4% | 17.9% | 1823 |
| `deployed_naive` | 4,000 | 25/28 (89.3%) | 47.7% | 38.6% | 96.4% | 60.7% | 3799 |
| `deployed_naive` | 8,000 | 27/28 (96.4%) | 65.6% | 36.2% | 96.4% | 67.9% | 7798 |
| `deployed_rrf` | 2,000 | 27/28 (96.4%) | 38.2% | 56.6% | 96.4% | 17.9% | 1818 |
| `deployed_rrf` | 4,000 | 27/28 (96.4%) | 50.2% | 46.8% | 96.4% | 60.7% | 3818 |
| `deployed_rrf` | 8,000 | 27/28 (96.4%) | 66.8% | 38.9% | 96.4% | 67.9% | 7818 |
| `deployed_compact` | 2,000 | 25/28 (89.3%) | 52.6% | 39.4% | 64.3% | 67.9% | 1883 |
| `deployed_compact` | 4,000 | 26/28 (92.9%) | 64.9% | 34.8% | 71.4% | 75.0% | 3860 |
| `deployed_compact` | 8,000 | 28/28 (100.0%) | 76.4% | 31.7% | 78.6% | 82.1% | 7795 |
| `resolved_naive` | 2,000 | 27/28 (96.4%) | 50.6% | 75.3% | 100.0% | 28.6% | 1870 |
| `resolved_naive` | 4,000 | 27/28 (96.4%) | 68.0% | 64.7% | 100.0% | 42.9% | 3840 |
| `resolved_naive` | 8,000 | 28/28 (100.0%) | 82.4% | 49.9% | 100.0% | 64.3% | 7854 |
| `resolved_rrf` | 2,000 | 28/28 (100.0%) | 51.9% | 79.5% | 100.0% | 28.6% | 1821 |
| `resolved_rrf` | 4,000 | 28/28 (100.0%) | 69.1% | 67.4% | 100.0% | 42.9% | 3851 |
| `resolved_rrf` | 8,000 | 28/28 (100.0%) | 82.9% | 50.6% | 100.0% | 64.3% | 7858 |
| `resolved_compact` | 2,000 | 28/28 (100.0%) | 80.1% | 65.6% | 64.3% | 64.3% | 1911 |
| `resolved_compact` | 4,000 | 28/28 (100.0%) | 89.1% | 51.7% | 75.0% | 75.0% | 3899 |
| `resolved_compact` | 8,000 | 28/28 (100.0%) | 98.7% | 38.6% | 89.3% | 89.3% | 7759 |

## Test cohort

| Arm | Budget | Hit-any | Mean target recall | Oracle-path fraction | Mixed-source cases | Semantic-only cases | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| `deployed_graph` | 2,000 | 25/28 (89.3%) | 60.6% | 87.5% | 0.0% | 0.0% | 42 |
| `deployed_graph` | 4,000 | 25/28 (89.3%) | 60.6% | 87.5% | 0.0% | 0.0% | 42 |
| `deployed_graph` | 8,000 | 25/28 (89.3%) | 60.6% | 87.5% | 0.0% | 0.0% | 42 |
| `resolved_graph` | 2,000 | 28/28 (100.0%) | 100.0% | 100.0% | 0.0% | 0.0% | 156 |
| `resolved_graph` | 4,000 | 28/28 (100.0%) | 100.0% | 100.0% | 0.0% | 0.0% | 156 |
| `resolved_graph` | 8,000 | 28/28 (100.0%) | 100.0% | 100.0% | 0.0% | 0.0% | 156 |
| `rag_proxy` | 2,000 | 25/28 (89.3%) | 69.7% | 13.7% | 0.0% | 100.0% | 1906 |
| `rag_proxy` | 4,000 | 27/28 (96.4%) | 79.0% | 9.7% | 0.0% | 100.0% | 3869 |
| `rag_proxy` | 8,000 | 28/28 (100.0%) | 87.4% | 6.3% | 0.0% | 100.0% | 7903 |
| `deployed_naive` | 2,000 | 27/28 (96.4%) | 73.0% | 15.1% | 92.9% | 100.0% | 1918 |
| `deployed_naive` | 4,000 | 27/28 (96.4%) | 80.8% | 9.9% | 92.9% | 100.0% | 3872 |
| `deployed_naive` | 8,000 | 28/28 (100.0%) | 87.4% | 6.3% | 92.9% | 100.0% | 7893 |
| `deployed_rrf` | 2,000 | 27/28 (96.4%) | 73.0% | 15.1% | 92.9% | 100.0% | 1918 |
| `deployed_rrf` | 4,000 | 27/28 (96.4%) | 80.8% | 9.9% | 92.9% | 100.0% | 3872 |
| `deployed_rrf` | 8,000 | 28/28 (100.0%) | 87.4% | 6.3% | 92.9% | 100.0% | 7893 |
| `deployed_compact` | 2,000 | 27/28 (96.4%) | 73.9% | 14.2% | 92.9% | 100.0% | 1911 |
| `deployed_compact` | 4,000 | 27/28 (96.4%) | 80.9% | 9.6% | 92.9% | 100.0% | 3880 |
| `deployed_compact` | 8,000 | 28/28 (100.0%) | 87.4% | 6.1% | 92.9% | 100.0% | 7880 |
| `resolved_naive` | 2,000 | 28/28 (100.0%) | 95.9% | 30.5% | 100.0% | 92.9% | 1884 |
| `resolved_naive` | 4,000 | 28/28 (100.0%) | 97.5% | 16.7% | 100.0% | 96.4% | 3882 |
| `resolved_naive` | 8,000 | 28/28 (100.0%) | 98.7% | 10.0% | 100.0% | 96.4% | 7884 |
| `resolved_rrf` | 2,000 | 28/28 (100.0%) | 96.3% | 30.5% | 100.0% | 92.9% | 1891 |
| `resolved_rrf` | 4,000 | 28/28 (100.0%) | 97.5% | 16.7% | 100.0% | 96.4% | 3882 |
| `resolved_rrf` | 8,000 | 28/28 (100.0%) | 98.7% | 10.0% | 100.0% | 96.4% | 7882 |
| `resolved_compact` | 2,000 | 28/28 (100.0%) | 100.0% | 22.9% | 96.4% | 96.4% | 1910 |
| `resolved_compact` | 4,000 | 28/28 (100.0%) | 100.0% | 13.9% | 100.0% | 100.0% | 3866 |
| `resolved_compact` | 8,000 | 28/28 (100.0%) | 100.0% | 8.1% | 100.0% | 100.0% | 7890 |

## All cohort (descriptive only)

| Arm | Budget | Hit-any | Mean target recall | Oracle-path fraction | Mixed-source cases | Semantic-only cases | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| `deployed_graph` | 2,000 | 49/56 (87.5%) | 53.0% | 69.7% | 0.0% | 0.0% | 467 |
| `deployed_graph` | 4,000 | 50/56 (89.3%) | 56.6% | 70.7% | 0.0% | 0.0% | 735 |
| `deployed_graph` | 8,000 | 52/56 (92.9%) | 58.9% | 72.3% | 0.0% | 0.0% | 1132 |
| `resolved_graph` | 2,000 | 56/56 (100.0%) | 90.0% | 97.3% | 0.0% | 0.0% | 646 |
| `resolved_graph` | 4,000 | 56/56 (100.0%) | 94.6% | 97.3% | 0.0% | 0.0% | 928 |
| `resolved_graph` | 8,000 | 56/56 (100.0%) | 99.3% | 97.4% | 0.0% | 0.0% | 1317 |
| `rag_proxy` | 2,000 | 52/56 (92.9%) | 50.9% | 26.9% | 0.0% | 100.0% | 1887 |
| `rag_proxy` | 4,000 | 54/56 (96.4%) | 62.2% | 21.6% | 0.0% | 100.0% | 3889 |
| `rag_proxy` | 8,000 | 56/56 (100.0%) | 74.9% | 17.8% | 0.0% | 100.0% | 7888 |
| `deployed_naive` | 2,000 | 50/56 (89.3%) | 54.6% | 29.9% | 94.6% | 58.9% | 1871 |
| `deployed_naive` | 4,000 | 52/56 (92.9%) | 64.2% | 24.3% | 94.6% | 80.4% | 3836 |
| `deployed_naive` | 8,000 | 55/56 (98.2%) | 76.5% | 21.3% | 94.6% | 83.9% | 7846 |
| `deployed_rrf` | 2,000 | 54/56 (96.4%) | 55.6% | 35.9% | 94.6% | 58.9% | 1868 |
| `deployed_rrf` | 4,000 | 54/56 (96.4%) | 65.5% | 28.3% | 94.6% | 80.4% | 3845 |
| `deployed_rrf` | 8,000 | 55/56 (98.2%) | 77.1% | 22.6% | 94.6% | 83.9% | 7856 |
| `deployed_compact` | 2,000 | 52/56 (92.9%) | 63.2% | 26.8% | 78.6% | 83.9% | 1897 |
| `deployed_compact` | 4,000 | 53/56 (94.6%) | 72.9% | 22.2% | 82.1% | 87.5% | 3870 |
| `deployed_compact` | 8,000 | 56/56 (100.0%) | 81.9% | 18.9% | 85.7% | 91.1% | 7838 |
| `resolved_naive` | 2,000 | 55/56 (98.2%) | 73.3% | 52.9% | 100.0% | 60.7% | 1877 |
| `resolved_naive` | 4,000 | 55/56 (98.2%) | 82.8% | 40.7% | 100.0% | 69.6% | 3861 |
| `resolved_naive` | 8,000 | 56/56 (100.0%) | 90.5% | 29.9% | 100.0% | 80.4% | 7869 |
| `resolved_rrf` | 2,000 | 56/56 (100.0%) | 74.1% | 55.0% | 100.0% | 60.7% | 1856 |
| `resolved_rrf` | 4,000 | 56/56 (100.0%) | 83.3% | 42.1% | 100.0% | 69.6% | 3867 |
| `resolved_rrf` | 8,000 | 56/56 (100.0%) | 90.8% | 30.3% | 100.0% | 80.4% | 7870 |
| `resolved_compact` | 2,000 | 56/56 (100.0%) | 90.0% | 44.3% | 80.4% | 80.4% | 1911 |
| `resolved_compact` | 4,000 | 56/56 (100.0%) | 94.6% | 32.8% | 87.5% | 87.5% | 3882 |
| `resolved_compact` | 8,000 | 56/56 (100.0%) | 99.3% | 23.4% | 94.6% | 94.6% | 7825 |

## Structural cohort at 4k by repository and band

| Group | Arm | Hit-any | Macro recall | Semantic-only cases |
|---|---|---:|---:|---:|
| repo=grafana | `deployed_graph` | 9/10 | 42.0% | 0.0% |
| repo=grafana | `deployed_naive` | 10/10 | 51.5% | 80.0% |
| repo=grafana | `deployed_rrf` | 10/10 | 51.5% | 80.0% |
| repo=kafka | `deployed_graph` | 6/8 | 34.1% | 0.0% |
| repo=kafka | `deployed_naive` | 5/8 | 8.1% | 0.0% |
| repo=kafka | `deployed_rrf` | 7/8 | 16.7% | 0.0% |
| repo=sklearn | `deployed_graph` | 10/10 | 78.1% | 0.0% |
| repo=sklearn | `deployed_naive` | 10/10 | 75.6% | 90.0% |
| repo=sklearn | `deployed_rrf` | 10/10 | 75.6% | 90.0% |
| band=S1 | `deployed_graph` | 9/9 | 46.0% | 0.0% |
| band=S1 | `deployed_naive` | 9/9 | 41.9% | 55.6% |
| band=S1 | `deployed_rrf` | 9/9 | 42.2% | 55.6% |
| band=S2 | `deployed_graph` | 8/9 | 62.4% | 0.0% |
| band=S2 | `deployed_naive` | 7/9 | 47.8% | 55.6% |
| band=S2 | `deployed_rrf` | 9/9 | 54.2% | 55.6% |
| band=S3 | `deployed_graph` | 1/1 | 100.0% | 0.0% |
| band=S3 | `deployed_naive` | 1/1 | 33.3% | 0.0% |
| band=S3 | `deployed_rrf` | 1/1 | 33.3% | 0.0% |
| band=S4 | `deployed_graph` | 4/6 | 34.1% | 0.0% |
| band=S4 | `deployed_naive` | 5/6 | 50.3% | 66.7% |
| band=S4 | `deployed_rrf` | 5/6 | 51.8% | 66.7% |
| band=S5 | `deployed_graph` | 3/3 | 64.3% | 0.0% |
| band=S5 | `deployed_naive` | 3/3 | 64.3% | 100.0% |
| band=S5 | `deployed_rrf` | 3/3 | 64.3% | 100.0% |

## Interpretation limits

1. All `resolved_*` arms are packing/fusion upper bounds because the same resolver produced the oracle labels.
2. `rag_proxy` reuses a saved changed-file chunk vector; it is not the deployed full-prefix query embedding.
3. Hit-any measures evidence availability, not review correctness.
4. A pass permits only a pre-registered held-out generation test.
