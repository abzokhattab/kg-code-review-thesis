# Final five-judge aggregation — both experiments

Panel: `openai:gpt-4o`, `gemini:gemini-2.5-flash`, `anthropic:claude-sonnet-4-5`, `deepseek:deepseek-v4-pro`, `xai:grok-4.6`

Aggregation: strict majority of valid votes (normally 3/5; 3/4 when one judge abstains). At least four valid votes are required; ties are false. `gpt-4o-mini` is excluded.

## Experiment 1

| Mode | Mean total /25 [95% CI] | Delta [95% CI], p | Mean KG /9 [95% CI] | Delta [95% CI], p |
|---|---:|---:|---:|---:|
| `baseline` | 8.20 [7.70, 8.70] | — | 4.62 [4.28, 4.97] | — |
| `kg` | 8.85 [8.30, 9.38] | +0.65 [+0.07, +1.25], p=0.0428 | 5.25 [4.85, 5.65] | +0.62 [+0.17, +1.07], p=0.0144 |
| `rag` | 9.18 [8.70, 9.62] | +0.97 [+0.42, +1.50], p=0.0013 | 5.08 [4.70, 5.45] | +0.45 [+0.03, +0.90], p=0.0732 |
| `hybrid` | 8.68 [8.30, 9.07] | +0.47 [+0.03, +0.97], p=0.0695 | 5.00 [4.67, 5.33] | +0.38 [+0.00, +0.78], p=0.0898 |

Criterion localisation:

- `kg`: target gain +0.625, other-criteria gain +0.025, share 96.2%, criterion-subset permutation p=0.0162.
- `rag`: target gain +0.450, other-criteria gain +0.525, share 46.2%, criterion-subset permutation p=0.3156.
- `hybrid`: target gain +0.375, other-criteria gain +0.100, share 78.9%, criterion-subset permutation p=0.0596.

Single-judge sensitivity for the KG-relevant contrast:

| Judge | Delta /9 | 95% CI | p |
|---|---:|---:|---:|
| `openai:gpt-4o` | +0.650 | [+0.225, +1.050] | 0.0064 |
| `gemini:gemini-2.5-flash` | +0.375 | [-0.225, +0.975] | 0.2644 |
| `anthropic:claude-sonnet-4-5` | +0.400 | [+0.075, +0.725] | 0.0292 |
| `deepseek:deepseek-v4-pro` | +0.600 | [+0.200, +1.000] | 0.0077 |
| `xai:grok-4.6` | +0.450 | [+0.100, +0.800] | 0.0252 |

Pairwise inter-judge agreement across all Experiment 1 rubric cells:

| Judge pair | Valid cells | Raw agreement | Cohen's kappa |
|---|---:|---:|---:|
| `openai:gpt-4o` / `gemini:gemini-2.5-flash` | 3836 | 86.3% | 0.713 |
| `openai:gpt-4o` / `anthropic:claude-sonnet-4-5` | 4000 | 89.6% | 0.785 |
| `openai:gpt-4o` / `deepseek:deepseek-v4-pro` | 4000 | 89.8% | 0.777 |
| `openai:gpt-4o` / `xai:grok-4.6` | 4000 | 91.6% | 0.817 |
| `gemini:gemini-2.5-flash` / `anthropic:claude-sonnet-4-5` | 3836 | 86.4% | 0.721 |
| `gemini:gemini-2.5-flash` / `deepseek:deepseek-v4-pro` | 3836 | 89.4% | 0.773 |
| `gemini:gemini-2.5-flash` / `xai:grok-4.6` | 3836 | 88.5% | 0.752 |
| `anthropic:claude-sonnet-4-5` / `deepseek:deepseek-v4-pro` | 4000 | 86.6% | 0.719 |
| `anthropic:claude-sonnet-4-5` / `xai:grok-4.6` | 4000 | 87.0% | 0.726 |
| `deepseek:deepseek-v4-pro` / `xai:grok-4.6` | 4000 | 95.6% | 0.899 |

Gemini abstained on 164 of 4,000 Experiment 1 criterion cells; every cell retained at least four valid judges.

## Experiment 2

| Arm | Structural detection [Wilson 95% CI] | Local control |
|---|---:|---:|
| `baseline` | 0/28 [0.00, 0.12] | 12/12 |
| `rag` | 5/28 [0.08, 0.36] | 12/12 |
| `kg` | 18/28 [0.46, 0.79] | 12/12 |
| `hybrid` | 21/28 [0.57, 0.87] | 11/12 |
| `kg_joern_inherit` | 26/28 [0.77, 0.98] | 12/12 |
| `kg_idealised` | 26/28 [0.77, 0.98] | 12/12 |
| `kg_deps_only` | 16/28 [0.39, 0.73] | 12/12 |
| `kg_edges_only` | 17/28 [0.42, 0.76] | 12/12 |

Paired structural contrasts:

- `kg_vs_baseline`: delta=+0.643, wins/losses=18/0, exact McNemar p=7.629e-06
- `rag_vs_baseline`: delta=+0.179, wins/losses=5/0, exact McNemar p=0.0625
- `hybrid_vs_baseline`: delta=+0.750, wins/losses=21/0, exact McNemar p=9.537e-07
- `hybrid_vs_kg`: delta=+0.107, wins/losses=4/1, exact McNemar p=0.375
- `kg_joern_inherit_vs_kg`: delta=+0.286, wins/losses=8/0, exact McNemar p=0.007812

## Interpretation

This file provides one aggregation rule and one result table per experiment. The six-model vote archive remains available, but the final panel excludes gpt-4o-mini to avoid an even-panel tie and reduce same-provider duplication.
