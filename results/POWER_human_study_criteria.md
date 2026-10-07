# Human study — sample size & power (per-criterion + overall design)

_baseline_strict vs Joern-KG · 6 PRs · per-criterion (A/Both/Neither/B) + one overall preference._
_Prepared for the supervisor meeting. Numbers from `scripts/analyze_human_study_criteria.py`
and the per-PR judge scores in `experiments/human_study_reviews/pr*_eval.json`._

## TL;DR
- **6 PRs is appropriate** for this design. The study is a within-subjects
  (repeated-measures) preference study + pilot convergent-validity check —
  **not** a survey estimating a population proportion. Power comes from
  **raters**, not PR count.
- **Recruit ~15–20 raters.** That gives ≥80–90 % power to detect a *clear*
  human preference at the overall level.
- **The per-criterion human↔judge agreement is not viable** on these PRs: the
  binary rubric scores joern and baseline as **tied on ~80 % of criterion
  cells**. Report per-criterion human data as **descriptive**, and run the
  convergent-validity correlation at the **whole-review (total / KG-relevant)
  level**, where the 6 PRs genuinely span the range.

## Three sample-size principles (and which one applies)
1. **Proportion estimation** (the ~385-PR figure): margin-of-error for a single
   proportion at 95 %/±5 %. This would apply only if the claim were "X % of all
   PRs benefit from KG." That is **not** our claim, so 385 does not bind us.
2. **Effect detection (do humans prefer KG?)** — a within-subjects test
   (Wilcoxon / sign / paired permutation). Power is driven by **effect size ×
   number of raters**. This is our primary analysis.
3. **Rank agreement with the LLM judge** — a correlation across PRs, so here
   **n = number of PRs**. Underpowered at n = 6 for a correlation; treated as a
   pilot, computed at the level that has signal.

The practical ceiling on PR count is **rater fatigue** (≈3–5 min/PR; 6 PRs ≈
20–30 min), not a formula. This is why within-subjects studies use few stimuli
and gain power from participants.

## Do the 6 PRs span the outcome range? (judge on the exact study reviews)
| Level | Spread across the 6 PRs |
|---|---|
| Total score Δ (joern − baseline) | **−1 … +3** → 3 joern-favored, 1 tie, 2 baseline-favored |
| KG-relevant subscore Δ | **−2 … +2** → 2 joern, 2 tie, 2 baseline |

Balanced — good for a whole-review correlation. **But per criterion the judge is
mostly ties:**

| Criterion | PRs where judge differentiates joern vs baseline |
|---|---|
| F3* | 0 / 6 |
| F2* | 1 / 6 |
| T3  | 2 / 6 |
| Q5  | 0 / 6 |
| R1  | 0 / 6 |
| C6  | — (no rubric equivalent) |

This is a **rubric-granularity limit, not a sample-size one** — adding PRs would
not fix it. It is also a *result*: humans can still distinguish the reviews where
the binary rubric scores them tied.

## Power (rater = unit; paired/one-sample test, two-sided α = .05)
| True effect d_z | interpretation | raters @ .80 power | raters @ .90 |
|---|---|---|---|
| 0.30 | small | ~90 | ~119 |
| 0.47 | (the d_z we cite elsewhere) | ~38 | ~50 |
| 0.50 | medium | ~34 | ~45 |
| 0.65 | med-large | ~21 | ~27 |
| 0.80 | large | ~15 | ~19 |

Binomial sign test on decisive overall votes (≈ raters × 6 × 0.6 decisive):
- **15 raters → 0.90 power** to detect a clear preference (p ≈ 0.70)
- **20 raters → 0.96**; subtle preferences (p ≈ 0.65) need ~20+

## Recommendation
- Keep **6 PRs**; recruit **~15–20 raters**.
- **Primary, powered result:** the overall preference (joern vs baseline).
- **Pilot convergent validity:** Spearman/Kendall of human overall preference
  vs judge Δtotal and Δkgrel across the 6 PRs (computed automatically by the
  analyzer).
- **Per-criterion human data:** report as descriptive evidence — humans detect
  differences the binary rubric scores as ties.
- Do **not** add a rag-vs-kg human comparison; cover rag/hybrid with the
  existing 40-PR LLM-judge panel.
