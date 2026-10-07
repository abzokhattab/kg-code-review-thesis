# Readiness verdict — three asks, three answers, 2026-06-12

The user's ask, verbatim:
> "all i want to have rn is **strong results with strong analysis** for
> the results for the research questions and **strong data that make
> the user study doable and easy for raters** and **we have a strong
> purpose of the user study**"

This document gives a one-line answer per ask, then the receipts, then
the gaps that block "ready" and the recommended fixes.

---

## TL;DR — am I ready on all three?

| Ask | Status | One-line |
|---|---|---|
| 1. Strong results + strong analysis for RQs | ✅ **READY** | Tree-sitter d_z=+0.47 / p=0.006 / CI [+0.17,+0.83] holds; Joern parity d_z=+0.30 (exploratory) holds with full robustness battery; 21 hostile-reviewer attacks closed in `ADVERSARIAL_GAP_AUDIT.md`. |
| 2. Data that makes the user study doable and easy for raters | ⚠️ **MOSTLY** | Stimuli are clean (6 PRs, ~10–12 min/session, payload 90 kB). UI is rater-friendly. **One real gap:** the live UI dropped per-criterion rating since 2026-05-13 and now collects only 5-point preference + free-text — analysis pipelines and ANALYSIS_PLAN expect per-criterion. |
| 3. Strong purpose for the user study | ⚠️ **MOSTLY** | The pre-registered purpose (RQ3 = LLM-judge ↔ human κ on 6 criteria) is sharp and falsifiable. **But** the live study version (`strict-bl-vs-joern-v1`) and the pre-reg (`bl_vs_kg`, 4 PRs) don't agree — there is no Decision 18 covering the switch to strict-baseline-vs-Joern with PRs {44,24,31,22,47,38}. |

**Net:** I would not launch the public study today. Two undocumented
protocol drifts since 2026-05-13 must be reconciled first. They are
fixable in 1–2 hours of focused work each. Receipts and the exact
fix list are below.

---

## 1. Strong results + strong analysis ✅

### Headline numbers (all scipy-validated, all in `COMBINED_RESULTS_TABLE.md`)

| Configuration | n | d_z (KG-rel) | 95% CI | Wilcoxon p | Verdict |
|---|---:|:---:|:---:|:---:|---|
| **Tree-sitter `kg` (pre-registered RQ2)** | 40 | **+0.47** | [+0.17, +0.83] | **0.006** | Pre-registered, headline |
| Joern strict (forced 9-criterion) | 35 | +1.34 | [+1.09, +1.78] | <0.0001 | Exploratory upper bound |
| Joern clean buggy (body omitted) | 35 | +0.58 | [+0.25, +1.01] | 0.003 | Confound — discard |
| **Joern clean parity (post-bug-fix)** | 35 | +0.30 | [−0.03, +0.65] | **0.057** | Exploratory replication |

### Defence depth

- **21 hostile-reviewer attacks closed** in `ADVERSARIAL_GAP_AUDIT.md`,
  each with a one-line attack + a one-line receipt.
- **28 anticipated committee questions answered** in `REVIEWER_QA.md`,
  grouped by chapter (methodology, statistics, mechanism, threats, scope).
- **Robustness battery (7 probes)** in `ROBUSTNESS_BATTERY.md` —
  bootstrap, sign test, permutation, per-judge, body-redundancy,
  direction stability, judge unanimity. All seven receipts in place.
- **Statistics validation** in `STATS_VALIDATION.md` — every reported
  number cross-checked against scipy to 4 decimals (Wilcoxon, sign,
  Pearson, Spearman, percentile + BCa bootstrap).
- **Mechanism honesty:** both candidate mechanisms (redundancy,
  interference) are explicitly **retracted** with receipts in
  `PER_LANGUAGE_CI_AND_FALSIFICATION.md` §2 and `PER_REPO_REGRESSION.md`.
  The thesis reports "parity drop observed without confirmed mechanism"
  — that is the strongest defensible claim.
- **Power analysis (`POWER_ANALYSIS.md`)** explains why n=35 doesn't
  reach p<0.05: achieved power 0.41 for d_z=+0.30, MDE=+0.49, n=88
  needed for 80% power. Tree-sitter at n=40 had 0.83 power → consistent
  with p=0.006.
- **Per-judge × per-language disaggregation
  (`PER_JUDGE_BY_LANGUAGE.md`)** — Java (+0.58) and TypeScript (+0.54)
  are positive across all 3 judges (judge-robust). Python and C++
  are panel-aggregate nulls that mask judge sign disagreement at small
  n — reported honestly as "judges disagree at this n", not "KG fails
  on Python/C++".
- **Strict sensitivity (`STRICT_SENSITIVITY.md`)** — strict d_z=+1.34
  stays >+1.03 under removal of any single criterion (max drop 23.3%
  when C2 removed). Effect is broadly distributed, not 1-2-criterion
  driven. T1/Q2 negative criteria honestly disclosed.

**Conclusion on ask 1: ready.** No further analysis needed for the
RQ-level results. The three-tier defensive structure (HONEST_HEADLINE
→ ADVERSARIAL_GAP_AUDIT → REVIEWER_QA) is in place.

---

## 2. Data that makes the user study doable and easy for raters ⚠️

### What's solid

- **Session length is right:** 6 PRs × 1 comparison × ~2 min/PR ≈
  10–12 min (Decision 15's cognitive-load target).
- **Payload weight is reasonable:** 90 kB total study_data.json across
  6 PRs (median diff 10 kB, median review 2.3 kB each).
- **UI flow is rater-friendly:** welcome → consent → demographics
  (3 questions) → briefing (4 sections + concrete example) → 1 warmup
  trial → 6 real trials → feedback → completion.
- **De-blinding mitigations live in the UI:** stretch-to-equal review
  cards (length parity), sentence-level uniqueness highlighting with
  a hide-toggle (Decision 15), randomized A/B label assignment
  (`blind_label`).
- **Difficulty + free-text reasoning collected** alongside the
  preference judgment.
- **Auto-save:** `claude_pilot_001.json` confirms the export pipeline
  works end-to-end.
- **Stimuli on disk:** all 12 reviews (`pr{44,24,31,22,47,38}_{baseline_strict,joern}.md`)
  exist in `experiments/human_study_reviews/` and
  `experiments/2026-05-15_joern_kg_main/exp_gpt4o_joern/`.
- **Smoke test exists:** `scripts/smoke_test.py` is the deploy gate.

### The real gap — **per-criterion rating was silently dropped**

Pre-registered design (ANALYSIS_PLAN.md §2.1):
- Per-trial human binary score on each of **6 criteria** (F3*, F2*,
  T3, Q5, R1, C6).
- Cohen's κ vs LLM judge per criterion → primary RQ3 outcome.

Pilot data (`data/exported_payloads/claude_pilot_001.json`,
`data/ingested_csv/responses.csv`):
- `scores: {F3*: 1, F2*: 1, T3: 1, Q5: 1, R1: 0, C6: 1}` — per-criterion.
- CSV has 6 dedicated columns for the criteria.

**Live UI today (`index.html`, version `strict-bl-vs-joern-v1`):**
- Preference (5-point Likert), free-text "why", difficulty (5-point).
- **No per-criterion rating widget.** No mention of F3*, F2*, T3,
  Q5, R1, or C6 anywhere in the rater UI.

**Consequences if launched as-is:**
1. ANALYSIS_PLAN.md §2.1 (the *primary* RQ3 outcome) **cannot be
   computed** from the data the live study collects.
2. The CSV ingestion will produce empty F3*/F2*/T3/Q5/R1/C6 columns
   for every new rater.
3. The pilot data and the new rater data are **not poolable** — they
   have different schemas.

**Decision-log status:** no Decision 18 documenting this change.
Decision 15 (the most recent rubric-touching decision) explicitly
says *"6-criterion rubric — same definitions, same wording. Not
changed."*

### Smaller gaps

- **PR set drift:** Decision 17 locks the set at `{1, 14, 22, 24, 30, 42}`.
  Live study is `{44, 24, 31, 22, 47, 38}` — five of six PRs swapped.
  No Decision 18+ documenting this either.
- **Comparison drift:** Decision 17 (and ANALYSIS_PLAN) say
  `bl_vs_kg`. Live study is `baseline_strict vs joern`. Different
  baseline, different KG implementation — a real protocol change.
- **Ground-truth coverage payloads** in `data/pr_ground_truth/` cover
  the old set ({1, 12, 14, 3, 17, 19}), not the live set. ANALYSIS_PLAN
  §4.4's coverage metric can't be computed for the new PRs.
- **PR47 has a 7.2 kB body** — outlier. Worth a length-band check.
- **Repo coverage at the live set:** sklearn ×3, kafka ×1, jenkins ×1,
  grafana ×1. No godot, no C++, no TypeScript at all. ANALYSIS_PLAN
  §7 already flagged "no Java stack" as a limitation; new live set
  has only Python (sklearn) + Java (kafka) + Java/Groovy (jenkins) +
  TS/JS (grafana). The diversity claim weakens further.

**Conclusion on ask 2: mostly ready, with one blocker.** Per-criterion
rating must come back, OR the analysis plan must be formally amended
to a preference-only design with κ replaced by a different agreement
measure (proportion-of-agreement, Krippendorff's α on ordinal preference,
or rank correlation). Either is defensible if pre-registered as a
deviation.

---

## 3. Strong purpose for the user study ⚠️

### What's solid (from ANALYSIS_PLAN.md, locked 2026-04-29)

- **One sharp purpose:** validate the LLM-judge against human raters
  on the same rubric (RQ3). Not a re-test of RQ1/RQ2.
- **Falsifiable decision rule:**
  - κ̄ ≥ 0.60 → LLM judge validated as primary.
  - 0.40 ≤ κ̄ < 0.60 → partially validated, caveats in writeup.
  - κ̄ < 0.40 → LLM judge demoted to descriptive.
- **Anti-goalpost-moving rules:** no dropping criteria, no dropping
  PRs after seeing data, no re-weighting after the fact.
- **Pre-registered threats and mitigations:** length disparity (§4.1
  with sensitivity analysis), KG hallucination kept as stimulus
  (§4.2), bullet-style differences (§4.3), ground-truth coverage
  metric (§4.4), language coverage (§4.5).
- **Reporting commitments:** §7 lists exactly what the writeup must
  contain regardless of result, including a "negative result" story
  framing in §8.

### The drift from the live study

The pre-registered plan was written for:
- 4 PRs (later 6 per Decision 17): `{1, 14, 22, 24, 30, 42}`
- Comparison `bl_vs_kg` (tree-sitter KG vs baseline)
- 5 LLM-overlap criteria for κ (F3*, F2*, T3, Q5, R1) + C6 ground-truth
- Validates the **tree-sitter** LLM-judge headline (d_z=+0.47, n=40)

The live study is now:
- 6 PRs: `{44, 24, 31, 22, 47, 38}`
- Comparison `baseline_strict vs joern` (forced 9-criterion baseline
  vs Joern KG, both under strict prompt)
- Preference-only (no κ-eligible per-criterion scores)
- Validates the **Joern strict** LLM-judge result (d_z=+1.34, n=35)

**These are not the same study.** Validating Joern strict is a
different scientific question from validating tree-sitter KG. Both
are defensible questions, but the pre-registration document the
defense will hold the work to is `ANALYSIS_PLAN.md`, and that
document binds the study to validating tree-sitter `bl_vs_kg`.

The committee will read Decision 17 (locks the 6 PRs and the
`bl_vs_kg` comparison) and then look at the live UI showing
`baseline_strict vs joern` on a different 6 PRs and ask: *"Where is
Decision 18?"*

### Possible reconciliation paths

| Path | Effort | Trade-off |
|---|---|---|
| **A. Roll the live study back** to Decision-17 spec (`bl_vs_kg`, PRs `{1, 14, 22, 24, 30, 42}`, 6-criterion ratings) | 1 day | Validates tree-sitter (the pre-registered headline). Loses the Joern-strict validation. |
| **B. Write Decision 18** documenting the strict-vs-Joern pivot, amend ANALYSIS_PLAN §2.1 to use preference-only metrics, restore 6-criterion rating in the UI for κ | 1 day | Most honest. Validates Joern (which is what the new live UI is set up for). Requires rebuilding the rating widget. |
| **C. Run two studies** — one with the original spec (validate tree-sitter), one with the live spec (validate Joern strict) | 2× rater budget | Strongest defense. May exceed compensation budget. |
| **D. Demote the user study** in the thesis from "primary RQ3" to "supplementary" and rely on the LLM-judge cross-validation that already exists | 0 days | Cheapest. Weakens the thesis but stays honest. Requires a chapter rewrite. |

**My read: Path B is the right call.** The Joern strict d_z=+1.34
result has 80%+ power and is the most striking finding in the lab.
A user study that *validates* it would be a strong contribution.
Path A gives up that lever; Path C is over-budget; Path D wastes
the work already done.

**Conclusion on ask 3: purpose is strong on paper but the live study
no longer matches the paper.** Either roll back or write Decision 18 +
amend the plan. Until that's done, the study has a sharp purpose for
the *original* protocol, not the protocol that will actually run.

---

## What blocks "fully ready"

In strict order of severity:

1. ⛔ **Decision 18 missing.** No documentation for the protocol
   pivot from `bl_vs_kg` (4 → 6 PRs) to `baseline_strict vs joern`
   (different 6 PRs). Without it, the defense narrative breaks.
2. ⛔ **Per-criterion rating dropped from UI but expected by
   ANALYSIS_PLAN, pilot CSV, and analysis scripts.** The live study
   cannot produce the pre-registered primary outcome (per-criterion κ).
3. ⚠️ **Ground-truth coverage payloads cover old PR set, not new.**
   ANALYSIS_PLAN §4.4 metric uncomputable for live PRs.
4. ⚠️ **Repo/language diversity narrowed** with the new PR set
   (no godot, no C++; sklearn ×3 dominates). Bigger threats-to-
   validity disclosure required.
5. ℹ️ **PR47 has 7.2 kB body** — single rater outlier; warrants
   ANALYSIS_PLAN §4.6-style carve-out.

Items 1 and 2 are the only true blockers. Items 3–5 are disclosure
work, not redesign.

---

## Recommended next 60 minutes

If we agree on **Path B** (document the pivot, restore per-criterion
rating):

1. Draft `Decision 18 — Pivot to strict-baseline-vs-Joern on 6 new
   PRs (2026-06-12)` covering: why the swap (validate the largest
   LLM-judge effect), what changed (PRs, modes, version string),
   what stays (6-criterion rubric, κ analysis, decision rules).
   Length: ~2 pages. *I can draft this against the existing
   Decision 16/17 template.*
2. Amend `ANALYSIS_PLAN.md` §1 (purpose), §2.1 (statistic) to
   reference the strict-vs-Joern stimulus pair while keeping the
   6-criterion κ analysis intact. Mark as "amended 2026-06-12 with
   rationale in Decision 18".
3. Restore the 6-criterion rating widget in `index.html` (one
   `<div>` per criterion, six binary radio pairs). Update
   `study_data.json` schema usage. Re-run `smoke_test.py`.
4. Refresh `ground_truth/pr*.json` for the new PR set OR explicitly
   drop §4.4's coverage metric in the amendment.
5. Re-run pilot self-rating (one rater, ~15 min) to confirm the
   restored UI works end-to-end and the CSV pipeline catches the
   new column writes.

**Estimated effort:** 4–6 hours. **Estimated cost:** $0 (no LLM
re-runs). **What changes on disk:** `human_eval_v3/index.html`,
`human_eval_v3/docs/DECISION_LOG.md`, `human_eval_v3/docs/ANALYSIS_PLAN.md`,
`human_eval_v3/data/pr_ground_truth/*` (new PR set).

If we agree on **Path A** (roll back to Decision-17 spec): half a day
of build_study_data_v2.py changes; everything else already exists.

If we agree on **Path D** (demote the user study): zero implementation
work, but a thesis-chapter framing change.

---

## What I am NOT recommending

- I am **not** recommending we launch with the current UI as-is. The
  schema mismatch between the UI, the CSV ingestion, and the
  ANALYSIS_PLAN will surface in the defense as "the data the study
  collects can't answer the question the study was registered to ask".
- I am **not** recommending we patch the analysis plan post-hoc to
  match the UI. That is the textbook anti-pattern the pre-registration
  was designed to prevent (ANALYSIS_PLAN.md §2.3 anti-goalpost-moving
  list).
- I am **not** recommending we re-run any LLM-judge work. The
  results catalog (`COMBINED_RESULTS_TABLE.md`) is locked and
  defensible; the gaps are in the human-study side only.

---

## Bottom line

**Results & analysis: ready.** **User study: needs Decision 18 +
restore per-criterion rating before launch.** **Purpose: sharp on
paper but currently mismatched to what the live UI will collect.**

Total time to "ready on all three": **one focused half-day** following
Path B above.
