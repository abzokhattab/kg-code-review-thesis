# v2 Pre-Registered Analysis Plan

_Locked 2026-04-29 (revised 2026-04-30 to reflect Decision 13's
4-PR selection), **before any v2 rater data was collected**. Any
change to the rules below after rater data exists must be flagged in
the writeup as a deviation from pre-registration._

This plan is the contract the thesis defense will be held to. It
specifies, in advance, what counts as a positive result, what counts as
a negative result, and what counts as ambiguous. The author commits to
reporting all three honestly.

---

## 1. What the human study actually tests

Per the thesis (Ch. 1, RQ3) and the methodology chapter, the human
study has **one** primary purpose:

> **RQ3 — Validity of LLM-as-judge.** Do the LLM-judge scores
> (gpt-4.1-mini panel) agree with expert human raters on the same
> rubric, to a degree that licenses using the LLM judge as the primary
> evaluation instrument for the 25-PR experiment?

The human study is **not** the primary test of RQ1 ("does context help?")
or RQ2 ("does structured KG context outperform unstructured RAG?"). The
LLM-judge results on the full 25-PR set (in
`results/checklist_evaluation_llm_multi.json`) are the primary test of
those questions; the human study is the validation instrument that
tells us whether the LLM judge is trustworthy on this rubric.

This framing is important because it changes what counts as success.

---

## 2. Primary outcome — RQ3 validation

### 2.1 Statistic

For each of the five LLM-overlap criteria (F3\*, F2\*, T3, Q5, R1) and
each of the two comparisons (`bl_vs_kg`, `kg_vs_rag`), compute Cohen's
κ between:

- **Aggregated human judgment.** Per trial, the binary human score is
  the majority vote of completed raters (ties broken to the
  baseline/KG side, *whichever appears first alphabetically* — fixed
  in advance to avoid post-hoc tie-breaking choices).
- **LLM-judge score.** From the gpt-4.1-mini panel, taking the same
  binary "Mode A wins on criterion X" outcome.

This yields 10 κ values (5 criteria × 2 comparisons).

### 2.2 Decision rule (pre-registered)

| Mean κ across the 10 cells | Verdict |
|---------------------------|---------|
| κ̄ ≥ 0.60 | **Validated** — LLM judge can be reported as primary instrument |
| 0.40 ≤ κ̄ < 0.60 | **Partially validated** — LLM judge reportable with caveats; per-criterion breakdown drives discussion |
| κ̄ < 0.40 | **Not validated** — LLM-judge results are descriptive only; the human-study results become primary, with the writeup foregrounding the disagreement |

Per-criterion κ values are also reported individually with bootstrap
95 % CIs (1 000 resamples over PRs).

### 2.3 What we will not do (anti-goalpost-moving)

- We will **not** drop a criterion from the κ̄ average after seeing the
  result.
- We will **not** drop a PR from the κ computation after seeing
  per-PR breakdowns.
- We will **not** weight criteria differently from a 1/5 average after
  seeing the result.

If a criterion turns out to have a prevalence-paradox issue (i.e. one
class < 10 % of the data), we will **report κ as is and flag the
caveat**, not exclude it.

---

## 3. Secondary outcome — directional consistency

### 3.1 Statistic

For each comparison (`bl_vs_kg`, `kg_vs_rag`), compute the **non-tie
win proportion** under both judges, on the v2 PR set only.

| Comparison | Human win-prop for A | LLM win-prop for A |
|------------|---------------------|--------------------|
| baseline vs KG | _to be filled_ | _to be filled_ |
| KG vs RAG | _to be filled_ | _to be filled_ |

Win proportions are reported with binomial 95 % CIs.

### 3.2 Decision rule (pre-registered)

| Pattern | Verdict |
|---------|---------|
| Human and LLM agree on direction (sign of `win_prop − 0.5`), and both 95 % CIs exclude 0.5 | **Convergent — strong** |
| Human and LLM agree on direction, but at least one CI includes 0.5 | **Convergent — weak (underpowered)** |
| Human and LLM disagree on direction, but at least one CI includes 0.5 | **Inconclusive — humans/LLM noisy** |
| Human and LLM disagree on direction, both CIs exclude 0.5 | **Divergent — primary instrument unreliable** |

The "Divergent" cell would, if it occurs, demote the LLM-judge results
on the 25-PR set from primary to descriptive. We commit to reporting
this honestly if it occurs.

---

## 4. Pre-registered threats to validity and the analyses that handle them

Discovered during the deep data audit (`scripts/deep_audit.py`,
2026-04-29) and **disclosed here before any v2 rater data exists**.
Each threat has a fixed mitigation strategy and a pre-registered
sensitivity analysis.

### 4.1 Systematic length disparity between modes

KG-mode reviews are longer than baseline and RAG reviews on 4 of 4
and 4 of 4 PRs respectively (means on the locked 4-PR set: baseline
1 536, kg 1 797, rag 1 551 chars). KG is the longer review in 100 %
of pairwise trials in v2 (~17 % longer on average).

**Why this is a real threat.** A rater doing 12 trials may notice
"the longer review tends to be one specific blind label" and develop
a heuristic that maps length → mode. If the heuristic correlates with
quality, the rater de-blinds.

**Why it is not fixable by editing the data.** The KG mode produces
more text because it retrieves and includes more concrete entities —
that is the substance of the contribution being evaluated. Truncating
KG would remove what the study is supposed to measure; padding
baseline/RAG with synthetic content is fabrication. See
`DECISION_LOG.md` §10.

**Mitigation in the rater UI.** Both review cards are rendered in a
CSS-grid row with `align-items: stretch` (default) and internal
overflow scrolling. The visible height of each card is identical
regardless of content length; the longer review scrolls inside its
own card.

**Sensitivity analysis (pre-registered).** Compute the headline κ̄
result twice:

- on the full set of trials, and
- on the subset of trials where the mode-pair length ratio is
  < 1.2x (closely-matched lengths).

Report both numbers. The headline conclusion holds only if both
report the same direction of result. If they disagree, the writeup
foregrounds the length-controlled estimate.

### 4.2 KG hallucinated path reference (PR 14 only)

On the locked 4-PR set, KG-mode hallucinates a single non-existent
test path: `SaveDashboardDrawer.test.tsx` on PR 14. This is a single
suggested test-file path adjacent to a real changed file
(`SaveDashboardDrawer.tsx`).

**Why this is not a data-quality bug.** This is a real KG output. The
rubric criterion T3 ("concrete test files") is designed to detect
exactly this: a competent human rater should *score down* a review
that name-drops a test file that doesn't exist. The whole point is
to test whether humans (and the LLM judge) can make that distinction.

Editing or removing the hallucination would be hand-curating KG to
look better than it is. It stays in the stimulus.

**No mitigation needed.** The behaviour is the measured phenomenon.
The threat is mentioned only so the writeup discusses it explicitly
in the methodology chapter.

> **Note on PRs 17 and 19.** The earlier draft of this plan
> documented 5 KG hallucinations across 3 PRs (17, 14, 19). PRs 17
> and 19 were dropped per Decision 13 because their hallucinations
> were the predictable consequence of KG's tree-sitter parser
> lacking Jelly support. This single remaining hallucination on PR
> 14 (TypeScript, fully KG-parseable) is therefore a *substantive*
> KG behaviour rather than a structural-fallback artefact.

### 4.3 Bullet-style differences on PR 14

On PR 14, baseline and RAG use numbered lists while KG uses dashes.
A sufficiently observant rater could de-blind on this one PR by
matching list style to mode.

**Severity.** Low. Bullet style is one rater-observable feature
across one of four PRs; it is not a stable heuristic across the
session.

**Decision.** Not normalised. Normalising would risk hiding real
differences in review style and is a bigger intervention than the
risk warrants. The sensitivity analysis in §4.1 (length-controlled
trials) will incidentally provide a partial check.

### 4.4 Ground-truth coverage metric (pre-registered post-hoc analysis)

`SELECTION_v2.md` §5 documents the substantive issues that real
maintainers raised on each of the 4 PRs (line-anchored review
comments, post-merge regression reports, design discussions). This
ground-truth set is **not shown to raters** — raters judge
independently from the diff and the PR body. After ratings come back,
the ground-truth set is used to compute a coverage metric:

> For each (PR, mode) AI review, count how many of the ground-truth
> issues for that PR are *substantively addressed* by the review.
> Substantive coverage means the review names the same code area
> (file/function/concept) and identifies the same or a stronger
> failure mode. Pure surface-level mention without identifying the
> failure mode does not count.

Coverage is judged by a single coder (the thesis author) with a
cross-check from the LLM panel (gpt-4.1-mini called per (issue, review)
pair, asked "does this review substantively cover this issue?"). The
two judgements are reported together; if they disagree on > 20 % of
items, the human judgement is taken as primary and the disagreement
is reported as a methodological finding.

This metric is reported alongside criterion C6 (binary "did the
review miss obvious issues?") as a finer-grained complement, not a
replacement.

**Direction-blindness check.** The coverage metric is computed
identically across the three modes. The ground-truth set was compiled
before any v2 rater data was collected and was not modified after
inspection of the AI reviews.

### 4.5 KG language-coverage scope (study set is fully parseable)

The KG evidence extractor (`scripts/build_kg_evidence_ast.py`) uses
tree-sitter with parsers for Python, Java, TypeScript/JS, Go, C++,
and Scala. It does **not** have a parser for Jelly (Jenkins's
XML-based templating language) or for binary assets.

This was a real concern for an earlier draft of the v2 PR set, which
included PRs 17 and 19 (both Jenkins, both Jelly-heavy). On those PRs
the KG mode operated with degraded grounding and produced 5
hallucinated test-file references in the deep audit.

**Resolution (Decision 13).** The locked 4-PR set is restricted to
KG-fully-parseable file types:

| PR | KG-parseable files | KG-invisible files | Gap |
|---:|-------------------|--------------------|-----|
| 12 | 3 of 4 (`.cpp`, `.h`) | 1 (`.xml` doc) | None substantive. |
|  1 | 2 of 3 (`.cpp`) | 1 (`.xml` doc) | None substantive. |
|  3 | 1 of 3 (`.tsx`) | 2 (`.json` locale) | None substantive. |
| 14 | 6 of 7 (`.tsx`) | 1 (`.mdx` story) | None substantive. |

All four PRs have ≥ 50% of changed files KG-parseable, with the
unparseable files being i18n locale JSON or markdown docs (not the
implementation under review). KG operates within its designed
operating envelope on every trial in the study.

**Reporting commitment.** The thesis writeup will explicitly
acknowledge in §threats-to-validity that the human-study validation
of the LLM judge does not extend to KG-unsupported file types
(Jelly, raw binary assets), and will report the LLM-judge results on
the full 25-PR set — which includes Jenkins PRs — as the source of
information about KG's behaviour on unsupported file types. Future
work that extends KG with template-language parsers should re-run a
human-validation study on those file types.

### 4.6 PR 12 has a 60-character GitHub body

PR 12's GitHub body is just `Backport of https://github.com/...`.
This is a real GitHub property of the PR — it is a backport whose
substantive description is in the parent PR. The rater can follow
the link.

**Decision.** Not edited. The rater UI's "Read PR description" button
shows the real 60-char body. The criterion C6 grade for this PR
should be interpreted accordingly; this is documented in the
briefing.

---

## 5. Inter-rater agreement (descriptive)

Fleiss' κ (multi-rater) over each comparison × criterion, reported per
criterion. No decision rule is attached to inter-rater κ; it is
reported descriptively as a measure of how well-defined the rubric is.

Threshold for discussion in the writeup:

- Fleiss' κ ≥ 0.60: rubric well-defined for that criterion
- 0.40–0.59: acceptable but discuss disagreement patterns
- < 0.40: rubric ambiguous on that criterion — discuss in
  threats-to-validity

---

## 6. Sample size and power

`results/POWER_ANALYSIS.md` (locked 2026-03 / 2026-04) specifies
**20 raters** for the v2 run. The 4-PR locked selection (Decision
13) is comfortably over-powered for κ estimation:

- 4 PRs × 2 comparisons × 5 criteria × 20 raters = **800 ratings**
- Expected non-tie rate ≈ 50 % from v1 pilot → **~400 usable items
  per comparison**
- The non-tie threshold from `POWER_ANALYSIS.md` for κ̄ ≥ 0.60 vs
  κ̄ ≤ 0.40 detection is **124 non-ties per comparison**
- Headroom: ~3.2× the threshold

If fewer than 12 raters complete the v2 run, the κ values are reported
with widened CIs and the writeup discusses underpowering explicitly
in §threats-to-validity.

---

## 7. Reporting commitments

Regardless of result, the thesis writeup will include:

1. The full 4-PR × 5-criterion κ table (all 20 cells, not a summary).
2. The non-tie win proportions for both comparisons with CIs.
3. The Fleiss' κ inter-rater agreement per criterion.
4. **A side-by-side comparison of v1 (truncated, leaking, 6 PRs) and
   v2 (clean, 4 PRs) study results.** Both are reported. v2 is
   foregrounded because it has cleaner stimuli; v1 is reported as
   robustness evidence and to use the full pilot sample.
5. The list of all PRs that were excluded from v2 and the rule under
   which they were excluded (`SELECTION_v2.md` §4 + `DECISION_LOG.md`
   Decisions 2, 3, 13).
6. A threats-to-validity section that explicitly addresses:
   - Diff truncation in v1 (resolved in v2)
   - KG mode-leak via Code Owners line (resolved in v2)
   - Empty Traceability section in all 18 reviews (resolved in v2 by
     dropping the section)
   - Empty PR bodies in v1 PRs 1 and 3 (resolved in v2 by recovering
     bodies from GitHub)
   - **Systematic length disparity between modes (KG ~17 % longer than
     baseline)** — disclosed under §4.1; sensitivity analysis on
     length-ratio < 1.2x subset is pre-registered.
   - **One KG hallucinated test path on PR 14** — kept as stimulus
     per §4.2; this is the measured phenomenon.
   - Bullet-style differences on PR 14 (low severity) — §4.3.
   - PR 12 backport with 60-char body — §4.6.
   - **KG language-coverage gap on Jelly / binary assets** — locked
     selection avoids these file types per Decision 13; the
     human-study validation is therefore restricted to KG's
     supported operating envelope (§4.5). This is acknowledged as a
     scope limitation; the LLM-judge results on the full 25-PR set
     (which includes Jenkins) cover the unsupported case.
   - Single-judge vs panel LLM comparison.
   - The 4-PR sample size and ~3.2× over-power.
   - Repo coverage in human study (godot + grafana only; no Java
     stack; this is a real limitation and must be acknowledged).

---

## 8. What "success" looks like

A solid, defensible thesis result is **any of the following**, provided
all are honestly reported:

- κ̄ ≥ 0.60 + convergent direction → "LLM judge validated, KG context
  helps over baseline" (the strong story).
- κ̄ ∈ [0.40, 0.60) + convergent direction → "LLM judge partially
  validated; KG context helps over baseline with caveats" (the medium
  story — still a substantial contribution).
- κ̄ < 0.40 → "Human-LLM rubric agreement is poor on this rubric;
  reported the human-study findings as primary; this is a contribution
  to the literature on LLM-as-a-judge for code review" (the
  methodological-contribution story).
- Convergent direction but null effect (KG ≈ baseline) → "Adding KG
  context to existing LLM code-review pipelines does not yield
  measurable gains on the criteria humans care about under this
  evaluation protocol" (the negative-result story — also a real
  contribution).

What "failure" would look like (and what we do):

- Divergent direction (human says KG > baseline, LLM says baseline >
  KG, both with CIs excluding 0.5) → report honestly; discuss why the
  rubric is doing different things in the two judges; the LLM-judge
  results are demoted to descriptive in the 25-PR analysis. This is
  uncomfortable but defensible. It would also be a publishable
  methodological result.

The thesis is solid if and only if the protocol is honest. The
protocol above is honest because the decision rules are fixed before
the rater data arrives.
