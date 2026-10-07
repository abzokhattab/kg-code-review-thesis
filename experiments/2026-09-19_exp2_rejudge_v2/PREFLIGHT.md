# Experiment 2 rejudge v2 — pre-flight

- Arms: baseline, kg, rag, hybrid, kg_idealised, kg_joern_inherit, kg_deps_only, kg_edges_only
- Review cells: 320
- Paid judge calls: 681
- Deterministic no-match judge cells: 279
- Review cells with a matched basename collision: 1
- Missing reviews: 0
- Workers: 8

| Model | Calls | Estimated input tokens | Estimated output tokens | Estimated cost |
|---|---:|---:|---:|---:|
| `openai:gpt-4o-mini` | 227 | 264,467 | 27,240 | $0.06 |
| `openai:gpt-4o` | 227 | 264,467 | 27,240 | $0.93 |
| `gemini:gemini-2.5-flash` | 227 | 264,467 | 27,240 | $0.15 |

**Estimated total cost: $1.14**

Manifest correction ledger: `grafana_L2_02` is adjudicated as an actual syntax error (`=!=`), with the original label preserved in the source manifest.

No review generation is performed. Original judgments are read-only.
