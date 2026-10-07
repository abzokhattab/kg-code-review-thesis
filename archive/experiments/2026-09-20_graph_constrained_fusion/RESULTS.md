# Graph-constrained semantic fusion — offline gate

**Status:** exploratory development result; no API/model calls.

**Decision: NO-GO**

| Check | Result | Observed |
|---|:---:|---:|
| dependency: lose zero graph hits | pass | none |
| dependency: macro recall non-decreasing | fail | 48.9% vs 52.6% |
| dependency: oracle-path fraction non-decreasing | pass | 62.3% vs 53.8% |
| dependency: >=75% oracle paths have code snippets | pass | 100.0% |
| dependency: all contexts within budget | pass | true |
| test: lose zero graph hits | pass | none |
| test: macro recall non-decreasing | pass | 60.6% vs 60.6% |
| test: oracle-path fraction non-decreasing | pass | 87.5% vs 87.5% |
| test: >=75% oracle paths have code snippets | pass | 100.0% |
| test: all contexts within budget | pass | true |

## Dependency cohort

| Arm | Budget | Hit-any | Macro recall | Oracle-path fraction | MRR | Oracle paths with semantic code | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| `deployed_graph` | 2,000 | 24/28 (85.7%) | 45.3% | 51.9% | 0.700 | 0.0% | 888 |
| `deployed_graph` | 4,000 | 25/28 (89.3%) | 52.6% | 53.8% | 0.700 | 0.0% | 1422 |
| `deployed_graph` | 8,000 | 27/28 (96.4%) | 57.4% | 57.1% | 0.700 | 0.0% | 2223 |
| `deployed_graph_semantic` | 2,000 | 27/28 (96.4%) | 43.4% | 65.3% | 0.836 | 100.0% | 1437 |
| `deployed_graph_semantic` | 4,000 | 27/28 (96.4%) | 48.9% | 62.3% | 0.836 | 100.0% | 2154 |
| `deployed_graph_semantic` | 8,000 | 27/28 (96.4%) | 55.1% | 59.2% | 0.836 | 100.0% | 3322 |
| `manifest_resolver_graph` | 2,000 | 28/28 (100.0%) | 80.1% | 94.5% | 0.922 | 0.0% | 1131 |
| `manifest_resolver_graph` | 4,000 | 28/28 (100.0%) | 89.3% | 94.7% | 0.922 | 0.0% | 1700 |
| `manifest_resolver_graph` | 8,000 | 28/28 (100.0%) | 98.7% | 94.8% | 0.922 | 0.0% | 2472 |
| `manifest_resolver_graph_semantic` | 2,000 | 28/28 (100.0%) | 63.9% | 96.4% | 0.982 | 100.0% | 1443 |
| `manifest_resolver_graph_semantic` | 4,000 | 28/28 (100.0%) | 78.9% | 96.2% | 0.982 | 100.0% | 2421 |
| `manifest_resolver_graph_semantic` | 8,000 | 28/28 (100.0%) | 89.7% | 95.3% | 0.982 | 100.0% | 3652 |

## Test cohort

| Arm | Budget | Hit-any | Macro recall | Oracle-path fraction | MRR | Oracle paths with semantic code | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| `deployed_graph` | 2,000 | 25/28 (89.3%) | 60.6% | 87.5% | 0.893 | 0.0% | 42 |
| `deployed_graph` | 4,000 | 25/28 (89.3%) | 60.6% | 87.5% | 0.893 | 0.0% | 42 |
| `deployed_graph` | 8,000 | 25/28 (89.3%) | 60.6% | 87.5% | 0.893 | 0.0% | 42 |
| `deployed_graph_semantic` | 2,000 | 25/28 (89.3%) | 60.6% | 87.5% | 0.893 | 100.0% | 144 |
| `deployed_graph_semantic` | 4,000 | 25/28 (89.3%) | 60.6% | 87.5% | 0.893 | 100.0% | 144 |
| `deployed_graph_semantic` | 8,000 | 25/28 (89.3%) | 60.6% | 87.5% | 0.893 | 100.0% | 144 |
| `manifest_resolver_graph` | 2,000 | 28/28 (100.0%) | 100.0% | 100.0% | 1.000 | 0.0% | 154 |
| `manifest_resolver_graph` | 4,000 | 28/28 (100.0%) | 100.0% | 100.0% | 1.000 | 0.0% | 154 |
| `manifest_resolver_graph` | 8,000 | 28/28 (100.0%) | 100.0% | 100.0% | 1.000 | 0.0% | 154 |
| `manifest_resolver_graph_semantic` | 2,000 | 28/28 (100.0%) | 97.4% | 100.0% | 1.000 | 100.0% | 376 |
| `manifest_resolver_graph_semantic` | 4,000 | 28/28 (100.0%) | 98.4% | 100.0% | 1.000 | 100.0% | 447 |
| `manifest_resolver_graph_semantic` | 8,000 | 28/28 (100.0%) | 100.0% | 100.0% | 1.000 | 100.0% | 557 |

## Interpretation limits

- The changed-file embedding is a saved first-chunk proxy.
- The manifest-resolver arms are circular packing ceilings.
- These reused stimuli are development data.
- A retrieval pass does not imply an LLM review-quality gain.
