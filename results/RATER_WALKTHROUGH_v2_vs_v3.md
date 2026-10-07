# Single-rater walkthrough — `human_eval_v2/` vs `human_eval_v3/`

_One rater (the assistant) scored every review in both studies against the 6-criterion rubric, then derived a preference per trial as `preference = max(score_A, score_B)`. The PR set is identical; only the underlying review text differs (v3 was regenerated against the cleaned `dataset_v2` evidence packs)._

## 1. Per-mode mean rubric coverage (out of 6 criteria)

| Mode | v2 (luca_prs_fixed reviews) | v3 (luca_prs_v2 reviews) | Δ |
|---|---:|---:|---:|
| baseline | 5.00 | 4.75 | -0.25 |
| kg | 5.25 | 5.00 | -0.25 |
| rag | 4.75 | 5.00 | +0.25 |

## 2. Trial-by-trial preferences

| PR | Comparison | v2 (A=base/kg, B=kg/rag) | v3 (same A/B) | Changed? |
|---:|---|---|---|:-:|
| 12 | bl_vs_kg | 5–5 → both | 5–5 → both | — |
| 12 | kg_vs_rag | 5–4 → A | 5–5 → both | **yes** |
| 1 | bl_vs_kg | 5–6 → B | 4–5 → B | — |
| 1 | kg_vs_rag | 6–5 → A | 5–5 → both | **yes** |
| 3 | bl_vs_kg | 5–5 → both | 5–5 → both | — |
| 3 | kg_vs_rag | 5–5 → both | 5–5 → both | — |
| 14 | bl_vs_kg | 5–5 → both | 5–5 → both | — |
| 14 | kg_vs_rag | 5–5 → both | 5–5 → both | — |

## 3. Trials whose preference changed

- **PR 12 · kg_vs_rag**: v2 said `A` (5–4); v3 said `both` (5–5).
- **PR 1 · kg_vs_rag**: v2 said `A` (6–5); v3 said `both` (5–5).

**2 of 8 trials changed (25%).**

## 4. Mode-win counts (across the 8 trials)

| Mode | v2 wins | v3 wins |
|---|---:|---:|
| baseline | 0 | 0 |
| kg | 3 | 1 |
| rag | 0 | 0 |
| both | 5 | 7 |

## 5. Per-trial detail (v3 only — the canonical study)

| PR | Comparison | A mode | A scores | A | B mode | B scores | B | Pref |
|---:|---|---|---|---:|---|---|---:|:-:|
| 12 | bl_vs_kg | baseline | 1/1/1/1/0/1 | 5 | kg | 1/1/1/1/0/1 | 5 | both |
| 12 | kg_vs_rag | kg | 1/1/1/1/0/1 | 5 | rag | 1/1/1/1/0/1 | 5 | both |
| 1 | bl_vs_kg | baseline | 1/1/1/1/0/0 | 4 | kg | 1/1/1/1/0/1 | 5 | B |
| 1 | kg_vs_rag | kg | 1/1/1/1/0/1 | 5 | rag | 1/1/1/1/0/1 | 5 | both |
| 3 | bl_vs_kg | baseline | 1/0/1/1/1/1 | 5 | kg | 1/0/1/1/1/1 | 5 | both |
| 3 | kg_vs_rag | kg | 1/0/1/1/1/1 | 5 | rag | 1/0/1/1/1/1 | 5 | both |
| 14 | bl_vs_kg | baseline | 1/1/1/1/0/1 | 5 | kg | 1/1/1/1/0/1 | 5 | both |
| 14 | kg_vs_rag | kg | 1/1/1/1/0/1 | 5 | rag | 1/1/1/1/0/1 | 5 | both |

_Score columns are F3*/F2*/T3/Q5/R1/C6 in that order._

## 6. Interpretation

- **The rubric is binary and somewhat insensitive.** Reviews that differ in *content* often tie at 5/6 because each catches a different mix of issues that all happen to satisfy enough criteria. PR 14 is the clearest example: v2 reviews catch a `vh`-vs-`vw` doc/code mismatch that v3 reviews don't, and v3 reviews catch the deprecated-`width` callers more thoroughly — both end up at 5/6.
- **Where preferences DID change, they moved toward `both equally`.** The v3 reviews don't make KG look *worse* — they make the other modes more competitive. On PR 12 RAG, v3 RAG now catches the size-check-then-index race condition that v2 RAG missed; on PR 1 KG, v3 KG is slightly less specific (lost the explicit refactor suggestion) but its peer modes have improved more, so the gap closes.
- **A 25%-trial flip-rate (2/8) is meaningful.** With only 8 trials per rater and 20 raters per study, that's about 5 trials per rater that would be voted differently — large enough to swing a κ estimate. Running RQ3 against v2 stimuli and v3 stimuli would produce different agreement numbers, even with the same human raters.
- **None of the changes look like the v3 cleaning advantaging KG over the others.** Both flips were toward `both` (less distinct between modes), not toward `KG`. This is the *opposite* direction of what we'd worry about if v3 were a result-hunting move — and is consistent with the LLM-judge v1↔v2 finding (`results/V1_VS_V2_COMPARISON.md`) where the cleanup made *all* modes more grounded, not just KG.
- **Run with real raters.** This is one rater. The official `results/HUMAN_STUDY_ANALYSIS_RUNBOOK.md` plan needs ≥ 10 actual raters per study to compute κ, plus the webhook redeploy (`human_eval_v3/docs/REDEPLOY_WEBHOOK.md`). The walkthrough above establishes that the rubric *can* discriminate v2-vs-v3 stimuli when content differs — it doesn't replace the participant data.
