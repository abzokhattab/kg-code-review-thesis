# Cross-generator comparison — Experiment 1 arms under four generators

**Held fixed:** evidence packs, lexical graph block, prompts, 25-criterion rubric, three-judge panel (gpt-4o-mini, gpt-4o, gemini-2.5-flash), majority vote with ties to 0, 40 PRs, T = 0.0.  
**Varied:** the generator only.  
**Method:** percentile bootstrap (B=10000), paired sign-flip permutation (B=20000), seed=2026, via `scripts/bootstrap_stats.py`.

## 1. Within-generator paired effect (the valid comparison)

| Generator | kg Δ /25 | p | kg Δ /9 | p | rag Δ /9 | p | hybrid Δ /9 | p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gpt-4o (headline) | +0.62 | 0.057 | +0.60 | 0.007 | +0.42 | 0.061 | +0.53 | 0.008 |
| claude-haiku-4.5 | +0.30 | 0.407 | +0.15 | 0.457 | +0.00 | 1.000 | +0.10 | 0.690 |
| gemini-2.5-flash | +0.33 | 0.465 | +0.47 | 0.136 | -0.50 | 0.199 | +0.25 | 0.486 |
| deepseek-v3 | +0.47 | 0.117 | +0.20 | 0.383 | +0.33 | 0.289 | +0.20 | 0.446 |

## 2. Score levels beside review length (confounded — do not read as capability)

| Generator | baseline /25 | baseline /9 | baseline words | kg words |
|---|---:|---:|---:|---:|
| gpt-4o (headline) | 9.20 | 4.97 | 243 | 266 |
| claude-haiku-4.5 | 14.12 | 7.22 | 532 | 632 |
| gemini-2.5-flash | 11.50 | 5.50 | 594 | 628 |
| deepseek-v3 | 13.57 | 6.83 | 459 | 486 |

## 3. Within-generator length/score coupling for the kg arm

Spearman correlation between the per-PR change in review length and the per-PR change in score, kg vs baseline. A high value would mean the kg arm's score advantage is a verbosity effect.

| Generator | mean Δwords | ρ(Δwords, Δ/25) | ρ(Δwords, Δ/9) |
|---|---:|---:|---:|
| gpt-4o (headline) | +23 | +0.15 | +0.10 |
| claude-haiku-4.5 | +100 | +0.01 | -0.12 |
| gemini-2.5-flash | +34 | +0.02 | +0.09 |
| deepseek-v3 | +27 | +0.22 | +0.19 |

## Reading

Section 1 is the reportable result. Section 2 exists to prevent a level comparison: the alternative generators write roughly twice as many words per review, and on a mention-check rubric length buys criteria, so the higher baselines are not evidence of higher capability. Section 3 bounds the verbosity account of the within-generator kg effect.

