# Independent judge panels — Experiments 1 and 2

**Status:** post-hoc provider-independence sensitivity. Frozen reviews; no review regeneration.

Panel: `anthropic:claude-sonnet-4-5`, `deepseek:deepseek-v4-pro`, `xai:grok-4.6`

## Experiment 1

| Mode | Total delta [95% CI] | p | KG-relevant delta [95% CI] | p |
|---|---:|---:|---:|---:|
| `kg` | +0.25 [-0.25, +0.78] | 0.3961 | +0.50 [+0.10, +0.90] | 0.0267 |
| `rag` | +0.90 [+0.42, +1.38] | 0.0009 | +0.45 [+0.07, +0.85] | 0.0405 |
| `hybrid` | +0.42 [-0.07, +0.95] | 0.1460 | +0.40 [+0.03, +0.80] | 0.0704 |

KG localisation: +0.500 points in the nine pre-specified criteria against -0.250 in the other sixteen (criterion-subset permutation p=0.0095).

Inter-judge agreement:

- `anthropic:claude-sonnet-4-5 ↔ deepseek:deepseek-v4-pro`: kappa=0.719, raw agreement=86.6%
- `anthropic:claude-sonnet-4-5 ↔ xai:grok-4.6`: kappa=0.726, raw agreement=87.0%
- `deepseek:deepseek-v4-pro ↔ xai:grok-4.6`: kappa=0.899, raw agreement=95.6%

## Experiment 2 — structural injections

| Arm | Detected | Rate [Wilson 95% CI] |
|---|---:|---:|
| `baseline` | 0/28 | 0.00 [0.00, 0.12] |
| `rag` | 5/28 | 0.18 [0.08, 0.36] |
| `kg` | 18/28 | 0.64 [0.46, 0.79] |
| `hybrid` | 21/28 | 0.75 [0.57, 0.87] |
| `kg_joern_inherit` | 26/28 | 0.93 [0.77, 0.98] |
| `kg_idealised` | 26/28 | 0.93 [0.77, 0.98] |
| `kg_deps_only` | 14/28 | 0.50 [0.33, 0.67] |
| `kg_edges_only` | 17/28 | 0.61 [0.42, 0.76] |

Key paired contrasts (exact McNemar):

- `kg_vs_baseline`: delta=+0.643, wins/losses=18/0, p=7.629e-06
- `rag_vs_baseline`: delta=+0.179, wins/losses=5/0, p=0.0625
- `hybrid_vs_baseline`: delta=+0.750, wins/losses=21/0, p=9.537e-07
- `hybrid_vs_kg`: delta=+0.107, wins/losses=4/1, p=0.375
- `kg_joern_inherit_vs_kg`: delta=+0.286, wins/losses=8/0, p=0.007812

## Interpretation

The independent panel reproduces the targeted Experiment 1 KG effect without any OpenAI judge and preserves the mechanism separation: KG is significant on the KG-relevant subscale, while RAG leads total coverage. Experiment 2 independently reproduces the corrected ordering (hybrid 21/28, KG 18/28) and rejects the earlier claim that hybrid is lower because of context dilution.

These analyses are post-hoc and must be reported beside the historical panels rather than described as pre-registered.
