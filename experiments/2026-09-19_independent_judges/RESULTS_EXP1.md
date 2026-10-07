# Experiment 1 — independent three-provider judge panel

**Status:** post-hoc sensitivity; frozen reviews, no regeneration.

Panel: `anthropic:claude-sonnet-4-5`, `deepseek:deepseek-v4-pro`, `xai:grok-4.6`

| Mode | Mean total /25 | Mean KG-relevant /9 |
|---|---:|---:|
| `baseline` | 8.00 | 4.50 |
| `kg` | 8.25 | 5.00 |
| `rag` | 8.90 | 4.95 |
| `hybrid` | 8.43 | 4.90 |

| Contrast vs baseline | Metric | Delta [95% CI] | p | d_z |
|---|---|---:|---:|---:|
| `kg` | total | +0.25 [-0.25, +0.78] | 0.3961 | +0.15 |
| `kg` | kg_relevant | +0.50 [+0.10, +0.90] | 0.0267 | +0.38 |
| `rag` | total | +0.90 [+0.42, +1.38] | 0.0009 | +0.58 |
| `rag` | kg_relevant | +0.45 [+0.07, +0.85] | 0.0405 | +0.35 |
| `hybrid` | total | +0.42 [-0.07, +0.95] | 0.1460 | +0.25 |
| `hybrid` | kg_relevant | +0.40 [+0.03, +0.80] | 0.0704 | +0.31 |

This panel contains no OpenAI judge. It is reported beside the original panel and does not alter the historical generator configuration.
