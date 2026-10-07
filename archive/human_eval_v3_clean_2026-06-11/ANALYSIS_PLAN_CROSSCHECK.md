# ANALYSIS_PLAN cross-check — what the parity finding does and doesn't disturb

**Plan reference:** `human_eval_v3/docs/ANALYSIS_PLAN.md` (locked 2026-04-29,
revised 2026-04-30). **The plan is honest and well-constructed.** This
document maps the post-parity findings onto the plan to identify (a)
what the plan continues to license, (b) where the plan needs a footnote,
and (c) what is genuinely new since lock-date.

---

## 1. What does the plan actually pre-register?

The plan locks the **human study (v2)**, not the LLM-judge experiment.
Specifically:

- **Primary outcome**: Cohen's κ between human and gpt-4.1-mini panel
  on 5 criteria × 2 comparisons (`bl_vs_kg`, `kg_vs_rag`) over the
  locked 4-PR set (12, 1, 3, 14).
- **Decision rule** is on κ̄ thresholds (≥0.60 / 0.40-0.60 / <0.40).
- **Secondary outcome**: directional consistency on win-proportions
  using the LLM-judge results on the full 25-PR set as context.

The "full 25-PR set" the plan references is `results/checklist_evaluation_llm_multi.json`
(now `__v2.json` with 40 PRs). The `kg` mode in that file is the
**tree-sitter KG**, not Joern.

## 2. Which results in the audit are downstream of the plan?

| Result | Is it the plan's primary instrument? |
|---|---|
| Tree-sitter KG d_z=+0.47, n=40 (headline) | **Yes** — the `kg` mode in the v2 multi-judge file is what feeds the plan's secondary outcome. |
| Joern KG strict-prompt d_z=+1.34, n=35 | No — exploratory follow-on, post-lock. |
| Joern KG normal-prompt buggy d_z=+0.58 | No — methodological work, post-lock. |
| **Joern KG normal-prompt parity d_z=+0.30 (new headline candidate)** | No — this is *replacement* work, post-lock. |

**Implication:** the plan is intact for the *tree-sitter kg* secondary
outcome. The Joern work is a *separate* methodological strand and the
plan does not constrain how it is reported.

## 3. What does the plan say about goalpost-moving?

> "We will **not** drop a criterion … We will **not** drop a PR … We
> will **not** weight criteria differently from a 1/5 average after
> seeing the result."

Anti-goalpost-moving rules apply to **human-study κ analysis**, not to
the choice of LLM-judge instrument upstream. Switching from the
tree-sitter `kg` to Joern (or from buggy-Joern to parity-Joern) is a
*different question* — which structural-context implementation should
be the headline — and is not goalpost-moving with respect to the plan.

**However**, if the thesis pivots from tree-sitter `kg` to Joern as the
*primary* RQ2 instrument, the plan's secondary outcome (directional
consistency) becomes about a different signal. That's a deviation worth
flagging in the writeup. See §6 below.

## 4. The §4.1 length-disparity threat — does parity change it?

The plan §4.1 reports KG-mode reviews are 17% longer than baseline on
the 4-PR human-study set, and pre-registers a sensitivity analysis on
`length_ratio < 1.2`. This concerns tree-sitter `kg`, generated via
the original headline pipeline (which already had the body in the
prompt). The parity correction does not affect the human-study stimuli.

**Length comparison post-parity (Joern):**

- Buggy Joern reviews: median `1366` chars (computed from disk).
- Parity Joern reviews: ~10-15% longer (PR body inflates output style).

This is *not* the length disparity the plan mitigates — different runs,
different PR set. No plan deviation.

## 5. The §4.2 hallucination threat — what the new audit adds

The plan §4.2 names *one* hallucinated test path on PR 14
(`SaveDashboardDrawer.test.tsx`). The post-parity audit shows a richer
picture:

- **File-citation hallucinations**: 10/35 buggy reviews; 10/35 parity
  reviews. Joern is at ~29% on this metric across both runs.
- **Owner-attribution fabrications**: 3/35 parity reviews fabricate
  team-shaped attributions (PR10, PR31, PR42 — all sklearn). Buggy run
  had 1 person-shaped fabrication (PR31 "Danilo Silva").

The plan's framing — "the rubric is designed to score down hallucinated
test files; this is the measured phenomenon" — extends naturally:
fabricated team attributions are **the same failure mode in a different
shape**. The thesis discussion already has the conceptual machinery to
name them. **No plan deviation; the post-parity audit just gives more
examples.**

## 6. Where the parity finding *does* require a deviation note

If the writeup pivots the **headline RQ2 result** from tree-sitter
(d_z=+0.47, n=40) to Joern parity (d_z=+0.30, n=35, p=0.057), this is:

- **Allowed**: the plan does not lock the LLM-judge instrument used for
  RQ2; it only commits to *reporting* whatever LLM-judge result drives
  the secondary directional-consistency outcome.
- **Required disclosures**:
  - The Joern parity result is *post-hoc selection* of a different
    structural-context implementation and prompt configuration.
  - The +0.30 effect *does not reach p<0.05* in any of three tests
    (Wilcoxon p=0.057, sign p=0.383, permutation p=0.112).
  - The 95% bootstrap CI **straddles zero** ([-0.03, +0.65]).
  - The 5 Go PRs are excluded (Joern frontend gap), reducing n from
    40 to 35.

These should be in §threats-to-validity alongside the existing §4.1-§4.6.

## 7. The plan's "what success looks like" cells, re-evaluated

The plan offers 4 success modes (§8). Where do we now sit?

| Cell | Plan's framing | Status post-parity |
|---|---|---|
| κ̄ ≥ 0.60 + convergent | "Strong: LLM judge validated, KG helps" | **Awaits human study.** Tree-sitter d_z=+0.47 is the directional anchor; if humans agree, this cell. |
| κ̄ ∈ [0.40, 0.60) + convergent | "Medium: validated with caveats" | Plausible landing zone. |
| κ̄ < 0.40 | "Methodological contribution" | Live possibility. |
| Convergent direction but null effect | "Negative result" | **Joern parity sits closer to here than to the strong cell.** |

The plan was already prepared for a null-effect-but-honest landing.
The parity finding nudges Joern toward that cell while tree-sitter
remains the +0.47 directional anchor for the human-study secondary
outcome.

## 8. Recommended deviations log entry (draft)

> **Deviation 2026-06-11.** Discovery of a body-omission bug in the
> Joern normal-prompt run. Re-run with body parity reduced KG-rel d_z
> from +0.58 to +0.30. The Joern result is reported as a post-hoc
> exploratory follow-on to the pre-registered tree-sitter `kg` headline
> (d_z=+0.47, n=40). Pre-registered tree-sitter analyses are unaltered.
> Joern parity result is reported with full 95% CI [-0.03, +0.65],
> three p-values (Wilcoxon, sign, permutation), per-judge breakdown,
> and direction-stability table. The thesis discussion frames the gap
> between buggy and parity as a finding about how prompt parity
> interacts with structural-context augmentation, not as a goalpost
> move.

## 9. Anti-goalpost-moving check (self-applied)

| Did I... | Status |
|---|---|
| Drop PRs after seeing results to inflate d_z? | **No.** All 35 are reported. Direction stability shows the buggy ranking is mostly preserved (54%) — i.e., I did not "find" the new headline by re-shuffling. |
| Re-weight criteria after seeing results? | **No.** Per-criterion contributions reported as-is including M3's negative drift and T1/Q2 ceiling. |
| Pick the best p-value? | **No.** All three p-values are reported (Wilcoxon 0.057, sign 0.383, permutation 0.112). |
| Hide the fact that CI straddles zero? | **No.** The robustness battery's TL;DR leads with this. |
| Quietly drop the redundancy mechanism after the body-length test failed? | **Need to update older docs (FINAL_REPORT.md, VERDICT_v2.md) which still claim the mechanism is supported.** This document and the next sweep do that. |

The last row is the only outstanding hygiene item. Addressed in the
companion `HONEST_HEADLINE.md` update next.
