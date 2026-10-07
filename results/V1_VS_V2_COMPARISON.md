# v1 vs v2 LLM-judge comparison

_v1 (25 PRs, contaminated) vs v2 (now **40 PRs** after two expansions: 18 audit-survivor PRs + 7 fresh ones added by `dataset_v2/scripts/find_seven_more_prs.py` (2026-05-05) + 15 more added by `dataset_v2/scripts/find_fifteen_more_prs.py` (2026-05-12, with an added KG-richness criterion: ≥ 2 KG-parseable code files). The first three rows below are an apples-to-apples comparison on the 18 PRs that exist in both datasets — those 18 are where v1 saw truncated diffs and empty PR bodies for 10 of them, and where v2 sees the recovered, untruncated context. The fourth row is the full 40-PR v2 headline, which is what the thesis's RQ2 sentence quotes._

- **v1 panel:** `results/checklist_evaluation_llm_multi.json` (100 reviews, 25 PRs)
- **v1 → 18-PR overlap:** 72 reviews, 18 PRs
- **v2 panel:** `results/checklist_evaluation_llm_multi__v2.json` (160 reviews, 40 PRs)
- **v2 → 18-PR overlap:** 72 reviews (the same 18 PRs as v1's overlap)
- **Judges:** openai:gpt-4o-mini, openai:gpt-4o, gemini:gemini-2.5-flash

## 1. By-mode mean coverage (% of 25-criterion checklist marked yes by majority vote)

| Dataset | Baseline | KG | RAG | Hybrid |
|---|---:|---:|---:|---:|
| v1 (25 PRs, contaminated) | 32.3% | 33.0% | 34.4% | 32.2% |
| v1 (18-PR overlap) | 35.3% | 34.4% | 36.7% | 34.2% |
| v2 (18-PR overlap, cleaned) | 35.8% | 37.3% | 37.8% | 39.3% |
| **v2 (40 PRs, cleaned + expansions) — headline** | 36.8% | 39.3% | 40.3% | 39.7% |

## 2. KG-relevant coverage (% of 9 KG-relevant criteria marked yes)

| Dataset | Baseline | KG | RAG | Hybrid |
|---|---:|---:|---:|---:|
| v1 (25 PRs, contaminated) | 46.2% | 53.3% | 51.6% | 46.2% |
| v1 (18-PR overlap) | 55.0% | 56.2% | 58.0% | 52.5% |
| v2 (18-PR overlap, cleaned) | 55.6% | 59.3% | 59.9% | 62.4% |
| **v2 (40 PRs, cleaned + expansions) — headline** | 55.3% | 62.0% | 60.0% | 61.1% |

## 3. Δ vs baseline (paired per-PR, percentage points)

### Total coverage Δ

| Dataset | KG − base | RAG − base | Hybrid − base |
|---|---:|---:|---:|
| v1 (25 PRs, contaminated) | +0.64 | +2.08 | -0.16 |
| v1 (18-PR overlap) | -0.89 | +1.33 | -1.11 |
| v2 (18-PR overlap, cleaned) | +1.56 | +2.00 | +3.56 |
| **v2 (40 PRs, cleaned + expansions) — headline** | +2.50 | +3.50 | +2.90 |

### KG-relevant Δ

| Dataset | KG − base | RAG − base | Hybrid − base |
|---|---:|---:|---:|
| v1 (25 PRs, contaminated) | +7.12 | +5.33 | -0.02 |
| v1 (18-PR overlap) | +1.24 | +3.09 | -2.49 |
| v2 (18-PR overlap, cleaned) | +3.71 | +4.32 | +6.81 |
| **v2 (40 PRs, cleaned + expansions) — headline** | +6.67 | +4.72 | +5.84 |

## 4. Per-judge yes-rate by mode (raw cells, before majority vote)


### v1 (18-PR overlap)

| Judge | Baseline | KG | RAG | Hybrid |
|---|---:|---:|---:|---:|
| openai:gpt-4o-mini | 34.0% | 36.9% | 37.3% | 37.6% |
| openai:gpt-4o | 33.3% | 34.7% | 34.7% | 31.6% |
| gemini:gemini-2.5-flash | 42.4% | 40.1% | 41.1% | 41.3% |

### v2 (40 PRs, cleaned)

| Judge | Baseline | KG | RAG | Hybrid |
|---|---:|---:|---:|---:|
| openai:gpt-4o-mini | 38.6% | 38.8% | 41.6% | 40.5% |
| openai:gpt-4o | 35.7% | 38.5% | 37.6% | 39.0% |
| gemini:gemini-2.5-flash | 39.6% | 40.3% | 42.4% | 39.9% |

## 5. Inter-judge agreement (Cohen's κ)

| Judge pair | v1 (18-PR overlap) | v2 (40 PRs, cleaned + expansions) | Δκ |
|---|---:|---:|---:|
| openai:gpt-4o-mini vs openai:gpt-4o | 0.680 | 0.717 | +0.037 |
| openai:gpt-4o-mini vs gemini:gemini-2.5-flash | 0.547 | 0.590 | +0.043 |
| openai:gpt-4o vs gemini:gemini-2.5-flash | 0.707 | 0.713 | +0.006 |

## How to read this report

- **Section 1–2:** Headline coverage by mode. The v1-subset row controls for PR composition; the v2 row adds the data-quality fix on top. The diff between those two rows is the contribution of cleaning the data.
- **Section 3:** The directional question (does extra context help?). If a positive Δ in v1 disappears in v2, the v1 effect was a data artefact. If it survives or grows, the effect is real.
- **Section 4:** Each judge's individual yes-rate. Diverging columns across judges hint at hard-to-judge items; they don't directly affect the majority-vote totals in §1–3.
- **Section 5:** Whether judges agree more on cleaner data. Δκ > 0 means the v2 inputs are easier to judge consistently.

_Run bootstrap CIs and paired permutation tests on the v2 effects with:_  
`python3 scripts/bootstrap_stats.py --in results/checklist_evaluation_llm_multi__v2.json --out-json results/BOOTSTRAP_STATS_v2.json --out-md results/BOOTSTRAP_STATS_v2.md --label 'v2 (18 PRs, cleaned)'`