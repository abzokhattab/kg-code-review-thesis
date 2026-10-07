# Experiment 2 rejudge v2 — pre-flight

- Arms: baseline, kg, rag, hybrid, kg_idealised, kg_joern_inherit, kg_deps_only, kg_edges_only
- Judges: deepseek:deepseek-v4-pro
- Review cells: 320
- Paid judge calls: 227
- Deterministic no-match judge cells: 93
- Review cells with a matched basename collision: 1
- Missing reviews: 0
- Workers: 4

| Model | Calls | Estimated input tokens | Estimated output tokens | Estimated cost |
|---|---:|---:|---:|---:|
| `deepseek:deepseek-v4-pro` | 227 | 331,305 | 27,240 | $0.55 |

**Estimated total cost: $0.55**

Manifest correction ledger: `grafana_L2_02` is adjudicated as an actual syntax error (`=!=`), with the original label preserved in the source manifest.

No review generation is performed. Original judgments are read-only.
