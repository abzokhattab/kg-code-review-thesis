# Joern-unified five-judge aggregation — Experiment 1 (n=35)

Panel: `openai:gpt-4o`, `gemini:gemini-2.5-flash`, `anthropic:claude-sonnet-4-5`, `deepseek:deepseek-v4-pro`, `xai:grok-4.6`

Aggregation: strict majority of valid votes (3/5; 3/4 when one judge abstains). gpt-4o-mini excluded.

KG mode: Joern CPG reviews (35 PRs, 5 Go-only PRs excluded).
Baseline/RAG/Hybrid: subset from existing 5-judge panel.

## Paired Comparisons

| Mode | n | Mean total /25 [95% CI] | Delta [95% CI], p, d_z | Mean KG /9 [95% CI] | Delta [95% CI], p, d_z |
|---|---:|---:|---:|---:|---:|
| `baseline` | 35 | 8.03 [7.51, 8.54] | — | 4.66 [4.29, 5.03] | — |
| `kg` | 35 | 8.74 [8.11, 9.37] | +0.71 [+0.20, +1.26], p=0.0173, d_z=+0.44 | 5.34 [4.94, 5.74] | +0.69 [+0.29, +1.11], p=0.0033, d_z=+0.56 |
| `rag` | 35 | 9.06 [8.57, 9.54] | +1.03 [+0.46, +1.60], p=0.0018, d_z=+0.59 | 5.09 [4.69, 5.49] | +0.43 [-0.03, +0.94], p=0.1269, d_z=+0.29 |
| `hybrid` | 35 | 8.60 [8.20, 9.00] | +0.57 [+0.09, +1.11], p=0.0563, d_z=+0.35 | 5.11 [4.77, 5.46] | +0.46 [+0.03, +0.91], p=0.0680, d_z=+0.34 |

## Criterion-Level Win/Loss Counts

| Mode | KG-relevant (9): W / L / net | Other (16): W / L / net |
|---|---:|---:|
| `kg` | 35 / 11 / +24 | 14 / 13 / +1 |
| `rag` | 36 / 21 / +15 | 28 / 7 / +21 |
| `hybrid` | 31 / 15 / +16 | 20 / 16 / +4 |

## Criterion Localisation

- `kg`: target gain +0.686, other +0.029, share 96.0%, p=0.0027
- `rag`: target gain +0.429, other +0.600, share 41.7%, p=0.3926
- `hybrid`: target gain +0.457, other +0.114, share 80.0%, p=0.0496

## Single-Judge Sensitivity (KG-relevant contrast)

| Judge | Delta /9 | 95% CI | p | d_z |
|---|---:|---:|---:|---:|
| `openai:gpt-4o` | +0.629 | [+0.229, +1.029] | 0.0068 | +0.53 |
| `gemini:gemini-2.5-flash` | +0.743 | [+0.314, +1.171] | 0.0047 | +0.55 |
| `anthropic:claude-sonnet-4-5` | +0.257 | [-0.057, +0.600] | 0.1917 | +0.25 |
| `deepseek:deepseek-v4-pro` | +0.600 | [+0.171, +1.086] | 0.0194 | +0.43 |
| `xai:grok-4.6` | +0.600 | [+0.229, +1.029] | 0.0087 | +0.49 |

## Inter-Judge Agreement

| Judge pair | Valid cells | Raw agreement | Cohen's kappa |
|---|---:|---:|---:|
| `openai:gpt-4o` / `gemini:gemini-2.5-flash` | 3396 | 85.7% | 0.701 |
| `openai:gpt-4o` / `anthropic:claude-sonnet-4-5` | 3500 | 89.8% | 0.788 |
| `openai:gpt-4o` / `deepseek:deepseek-v4-pro` | 3500 | 90.3% | 0.786 |
| `openai:gpt-4o` / `xai:grok-4.6` | 3500 | 92.0% | 0.822 |
| `gemini:gemini-2.5-flash` / `anthropic:claude-sonnet-4-5` | 3396 | 85.8% | 0.708 |
| `gemini:gemini-2.5-flash` / `deepseek:deepseek-v4-pro` | 3396 | 88.4% | 0.753 |
| `gemini:gemini-2.5-flash` / `xai:grok-4.6` | 3396 | 87.3% | 0.729 |
| `anthropic:claude-sonnet-4-5` / `deepseek:deepseek-v4-pro` | 3500 | 87.1% | 0.727 |
| `anthropic:claude-sonnet-4-5` / `xai:grok-4.6` | 3500 | 87.5% | 0.735 |
| `deepseek:deepseek-v4-pro` / `xai:grok-4.6` | 3500 | 95.3% | 0.893 |

Gemini abstained on 104 criterion cells.
