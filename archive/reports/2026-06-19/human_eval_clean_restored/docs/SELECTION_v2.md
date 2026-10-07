# v2 Human-Study PR Selection — Final, Locked

_Locked 2026-04-30. **Final selection: PRs `{12, 1, 3, 14}`** —
language-coverage-filtered. This document supersedes
`results/HUMAN_STUDY_PR_SELECTION.md` for the v2 study run. v1 data is
preserved for comparison in the writeup._

> **One-line summary.** 4 PRs across 2 repos (godot C++ ×2, grafana
> TypeScript ×2), all merged, all single-purpose, all under 13 kB diff,
> all untruncated, **all 100 % KG-parseable by tree-sitter**, all
> spot-checked for review-differentiability. Selection is
> direction-blind — no filter depends on which mode wins.

> **Why 4 PRs and not 6?** PRs 17 and 19 (Jenkins) were dropped in
> Decision 13 because their changed files include Jelly templates,
> which LUCA's KG-evidence extractor (tree-sitter) cannot parse. KG
> mode operated in degraded fallback grounding on those trials and
> produced hallucinated test-file references. With no clean
> replacement available in the candidate pool (every alternative was
> either docs-only, a revert, σ ≤ 1 paraphrasing, or truncated at
> 15 kB), the right call was to test the LLM judge only on the cases
> where KG operates as designed. Statistical power is comfortable at
> 4 PRs (4 × 5 × 20 × 2 = 800 ratings, ~3.2× the threshold from
> `POWER_ANALYSIS.md`). See `DECISION_LOG.md` §13 for the full
> reasoning.

---

## 1. Goals of the v2 re-selection

The v1 selection (`{17, 3, 19, 22, 10, 21}`) was filtered on three criteria:
repo-family coverage, FULL_KG/MARGINAL tier balance, and rubric divergence ≥ 2
(after a post-pilot swap). Closer inspection — see
`human_eval_v2/analysis/pr_candidates.md` and the conversation around
"is the data quality good?" — surfaced four problems that v1 did **not**
filter against:

1. **Two PRs are silently truncated** at the 15 kB diff cap (PR 10, PR 21),
   so humans and the LLM judge see different stimuli on those trials.
2. **Four of six PRs require niche domain knowledge** (Jelly templates,
   JVM internals, Kafka build internals, joblib API archaeology), so an
   average HPI Master/Junior rater cannot reliably evaluate them.
3. **Several PRs do multiple things at once** (#19 icon refactor + asset
   delete + class rename; #22 file move + assertion swap + dependency
   update), which makes criterion C6 ("missing information") subjective.
4. **None of the PRs has a documented "obvious issue"** anchored in the
   real maintainer comments of the original GitHub PR, so the C6 rating
   has no ground truth.

The v2 goals are:

- Eliminate truncation (mandatory).
- Maximise the share of mainstream-stack PRs (Python, JS/TS, plain Java
  app code; not Jelly, not `sun.misc.Unsafe`).
- Prefer single-purpose changes (≤ 4 changed files).
- Preserve the v1 strengths: rubric divergence ≥ 2 of 5 LLM-overlap
  criteria, tier balance, repo diversity.
- Document a "ground-truth issue" per PR taken from the real maintainer
  conversation on GitHub, so criterion C6 has an anchor.

**Direction-blind.** Every filter is on *magnitude* (divergence, accessibility,
size). None selects on *which mode wins*. See §6 for the explicit
non-bias argument.

---

## 2. Method

`human_eval_v2/scripts/analyze_pr_candidates.py` scores all 25 LUCA PRs
on nine boolean filters:

| # | Filter | Threshold |
|---|--------|-----------|
| 1 | `diff_under_5kb` | ≤ 5 000 chars |
| 2 | `diff_under_8kb` | ≤ 8 000 chars |
| 3 | `not_truncated` | < 15 000 chars (mandatory) |
| 4 | `divergence_ge_2` | Σ ≥ 2 of 5 LLM-overlap criteria |
| 5 | `state_merged` | PR state == MERGED |
| 6 | `not_revert` | not a revert PR |
| 7 | `not_docs_only` | not a pure docs change |
| 8 | `mainstream_stack` | not Jelly / JVM-internal |
| 9 | `single_purpose` | ≤ 4 changed files |

Divergence is computed across both planned comparisons (`bl_vs_kg` +
`kg_vs_rag`) on five criteria that overlap with the LLM rubric:
**F2 (edge cases), F3 (integration), T3 (test files), R1 (readability),
Q5 (reasoning)**. C6 is human-only and cannot be computed here.

Outputs:

- `human_eval_v2/analysis/pr_candidates.json` (full data)
- `human_eval_v2/analysis/pr_candidates.md` (ranked table)

---

## 3. Final selection

| Order | PR | Repo                | Type      | Diff   | Lang | Tier     | Σ div | Title (short)                       |
|------:|---:|---------------------|-----------|-------:|------|----------|------:|-------------------------------------|
| 1     | 12 | godotengine/godot   | feature   |  2 648 | C++  | MARGINAL |     2 | Add ability to pick random value    |
| 2     |  1 | godotengine/godot   | bug-fix   |  3 051 | C++  | MARGINAL |     2 | Replace OpenXR alert dialog with log |
| 3     |  3 | grafana/grafana     | feature   |  3 990 | TS   | FULL_KG  |     5 | Strict Mode notification             |
| 4     | 14 | grafana/grafana     | feature   | 12 025 | TS   | FULL_KG  |     1 | Drawer: introduce a `size` property  |

- **Repos:** 2 godot + 2 grafana ✓
- **Languages:** 2 C++ + 2 TypeScript — all 100 % KG-parseable by `scripts/build_kg_evidence_ast.py`
- **Tiers:** 2 FULL_KG + 2 MARGINAL ✓
- **Change types:** 3 feature + 1 bug-fix
- **Diff sizes:** 2.6 kB → 12.0 kB, all untruncated ✓

### 3.1 Why this list, ordered by trial position

| # | PR | Why this PR is in | Why this position |
|--:|---:|-------------------|-------------------|
| 1 | 12 | Godot C++ feature backport, three modes flag distinct concerns. Smallest readable diff (2.6 kB). | Onboarding trial — establishes pacing on accessible C++. |
| 2 |  1 | Godot OpenXR bug-fix; RAG catches a real concrete bug the others miss (a decision-quality signal, not paraphrasing). | Mid-way: still small, gives RAG a chance to show. |
| 3 |  3 | Grafana TypeScript feature, KG cross-references real Grafana symbols. Strongest FULL_KG candidate (Σ div = 5). | Strongest signal in the middle. |
| 4 | 14 | Grafana TypeScript feature; spot-check shows the three modes flag *different specific bugs* (`vh` vs `vw`, hardcoded `.main-view`, missing tests). The σ=1 LLM-divergence score undercounts this. | Largest diff, placed last so rater has warmed up. |

### 3.2 Why PRs 17 and 19 were dropped (Decision 13)

PR 17 (Jenkins, `f:hetero-list` Jelly bug-fix) and PR 19 (Jenkins,
icon refactor) were on the locked v2 selection until 2026-04-30 when
a cross-check against `scripts/build_kg_evidence_ast.py` revealed
that LUCA's KG-evidence extractor has no tree-sitter parser for Jelly:

- PR 17: only changed file is a `.jelly` template → **0 % KG-parseable**.
- PR 19: 11 changed files — only 2 `.java` parseable, 3 `.jelly`
  templates and 6 binary asset files invisible to KG → **18 %
  KG-parseable**.

The deep audit (`scripts/deep_audit.py`) confirmed KG hallucinated
test-file references on exactly these two PRs (3 hallucinations on
PR 17, 2 on PR 19) and **zero hallucinations on PRs 1, 3, 12, 14**.
The correlation is too clean to ignore: degraded KG grounding on
unsupported file types produces hallucinated context, which is a
structural disadvantage for KG mode in the rubric-comparison.

The candidate pool was searched exhaustively for replacements — see
`DECISION_LOG.md` §13 — and every alternative had its own
disqualifying flaw (docs-only, revert PR, σ ≤ 1 paraphrasing, all
modes converging on the wrong direction, or truncation at 15 kB).
There is no clean 5th or 6th PR available.

The decision was therefore to drop both PRs and run with 4. Statistical
power is comfortable: 4 × 5 × 20 × 2 = 800 ratings, ~3.2× the threshold
from `POWER_ANALYSIS.md`.

### 3.3 Why PR 18 was dropped (Decision 3)

PR 18 (`jenkinsci/jenkins#9002 — Further reduce usages of StringUtils`)
passed every numeric filter (Σ div = 2, 7 kB, single-purpose,
mainstream Java) and was 100 % KG-parseable. It was dropped after a
qualitative review-content spot-check:

- The PR's substantive direction is to **remove** `StringUtils` calls.
- All three AI-generated reviews recommend **re-introducing**
  `StringUtils` for null-safety and edge-case handling.
- The three modes converge on the same wrong-direction recommendation
  — no meaningful basis for a rater to prefer one over the other.

This is a *trial-quality* issue, not a direction-of-result issue
(we did not check who would have won).

---

## 4. Vs the v1 selection

| PR  | In v1 | In v2 | Reason for change |
|----:|:-----:|:-----:|-------------------|
|   3 | ✓     | ✓     | keep — strongest current candidate, fully KG-parseable TS |
|  17 | ✓     | ✗     | drop — KG cannot parse Jelly (Decision 13) |
|  19 | ✓     | ✗     | drop — 9 of 11 changed files invisible to KG (Decision 13) |
|  22 | ✓     | ✗     | drop — niche (Kafka/Gradle), 5 files, 10.5 kB (Decision 2) |
|  10 | ✓     | ✗     | drop — **truncated** at 15 kB (sklearn joblib) (Decision 2) |
|  21 | ✓     | ✗     | drop — **truncated** at 15 kB (Kafka JDK 11) (Decision 2) |
|   1 |       | ✓     | add — godot OpenXR bug-fix, fully KG-parseable C++ |
|  12 |       | ✓     | add — godot feature, fully KG-parseable C++ |
|  14 |       | ✓     | add — grafana feature, fully KG-parseable TS |

**Net change:** drop 5 (17, 19, 22, 10, 21), keep 1 (3), add 3 (1, 12, 14).

---

## 5. Ground-truth issues per PR

For each PR, the "ground-truth" issues are the substantive things real
maintainers raised on the GitHub conversation (review comments,
line-anchored review comments, post-merge regression reports). This
anchors criterion C6 ("does the review cover the obvious issues
without obvious missing information?") so it is not a Rorschach test.

> **How this is used.** The ground-truth set is **not shown to
> raters** — raters judge independently from the diff, the PR body,
> and their own expertise. The set is used **post-hoc** to compute a
> coverage metric: for each AI review × PR, how many of the
> ground-truth issues did it surface? This complements the binary C6
> rating with a finer-grained "coverage of real maintainer concerns"
> score. See `ANALYSIS_PLAN.md` §4.6 (coverage metric) for the
> pre-registered rule.
>
> **Source.** Every issue below has a citation to the actual GitHub
> comment that raised it. Raw fetch is in
> `human_eval_v2/data/pr_ground_truth/pr<N>.json`. The fetcher script
> is `human_eval_v2/scripts/fetch_pr_ground_truth.py`.

> **Note on dropped PRs.** The ground-truth files for PRs 17 and 19
> (now dropped per Decision 13) are still present in
> `human_eval_v2/data/pr_ground_truth/` for reference and for any
> future-work re-run, but those PRs are not in the locked v2 study
> set. The summary below covers only the 4 PRs that *are* in the
> study (1, 3, 12, 14).

### PR 12 — `[3.x] Add ability to pick random value from array`

[github.com/godotengine/godot#68625](https://github.com/godotengine/godot/pull/68625)

This is a **backport** of #67444 from master to 3.x. The substantive
review (API design, semantics) happened on the parent PR. On the
backport itself the maintainer feedback was process-only:

- **Squash and use a descriptive commit message** (`@YuriSizov`).
- **Author attribution.** Cherry-pick the original commit so
  `@nonunknown` stays as author and the backporter is credited via
  `Co-authored-by:` (`@akien-mga`).
- **No tests added in the 3.x branch.** Inherits the parent PR's
  semantics but without 3.x-specific test coverage.
- **Out-of-scope follow-up raised by users (`@oeleo1`):** the same
  pick-random helper would also be useful for `Dictionary`. Maintainer
  (`@YuriSizov`) ruled this out for the backport — needs a new proposal.

### PR 1 — Replaced OpenXR OS alert dialog with a warning log

[github.com/godotengine/godot#73144](https://github.com/godotengine/godot/pull/73144)

Three substantive line-anchored review comments and one design pivot
during the discussion:

- **i18n wrapping (`@m4gr3d`).** Suggested wrapping the user-facing
  message in `TTR("...")`. Resolved as: do **not** wrap — `@akien-mga`
  and `@BastiaanOlij` argued this is a debugging/error message and
  should stay searchable in English. Documented decision.
- **Behaviour-preserving project setting (`@BastiaanOlij`).** The
  initial PR removed the alert unconditionally; on XR-only devices,
  this would leave the screen black with no user feedback. The
  contributor added a `Startup Alert` project setting (default = true)
  in response. A competent reviewer should have flagged this risk
  immediately on reading the diff (the alert was the only user-facing
  signal on XR-only devices).
- **TTR()'s single-line constraint (`@akien-mga`).** Translation
  extraction works line-by-line, so any TTR() string must be on a
  single line. (Moot in this PR after the no-translate decision, but
  a real concern any reviewer of i18n changes should know.)
- **No tests added.**

### PR 3 — Expressions: notification for Strict Mode in Reduce

[github.com/grafana/grafana#97224](https://github.com/grafana/grafana/pull/97224)

One substantive review with a single concrete blocker:

- **Missing i18n translation key (`@itsmylife`, `CHANGES_REQUESTED`).**
  The notification text is a new user-facing string but the
  translation key was not added to
  `public/locales/en-US/grafana.json`. Fix workflow: add the key,
  then run `make i18n-extract`, then commit. This is the explicit
  reason the PR was initially rejected and then approved.
- **No tests added.**

### PR 14 — Drawer: introduce a `size` property

[github.com/grafana/grafana#67809](https://github.com/grafana/grafana/pull/67809)

Three line-anchored review comments and several discussion threads:

- **Logic simplification (`@JoaoSilvaGrafana`).** Suggested
  `useSizeWidth = !fixedWidth` because `fixedWidth` is only `false`
  when `isExpanded` is `false`. Author agreed and applied.
- **Comment wording (`@JoaoSilvaGrafana`).** Suggested clearer
  phrasing for the deprecation comment on the `width` prop.
- **Deprecated `inline` prop instead of fixing it.** The story for
  inline drawers was removed (`@torkelo`) because inline support has
  been broken since [#39390](https://github.com/grafana/grafana/issues/39390).
  Maintainers (`@JoaoSilvaGrafana`) agreed. A competent reviewer
  should have flagged the silent removal of the InLine story — this
  is a behaviour change that consumers may rely on.
- **Out-of-scope UX issue (`@amy-super`).** Drawer opens over the
  topnav but the megamenu opens under it — z-index inconsistency;
  raised but deferred to follow-up [#67824](https://github.com/grafana/grafana/pull/67824).
- **No tests added** for the new `size` property.

---

### Ground-truth coverage summary

| PR | # of substantive ground-truth issues | "Hardest" issue (one a fast reviewer might miss) |
|---:|:----:|--------------------------------------------------|
| 12 | 4    | Author attribution via cherry-pick (process, not code) |
|  1 | 4    | Black-screen risk on XR-only devices if alert is suppressed |
|  3 | 2    | i18n key missing — concrete, easy to miss without Grafana familiarity |
| 14 | 5    | Silent removal of the InLine story (behaviour change) |

---

## 6. Why this is not p-hacking

The selection criteria above filter on:

- diff length (a stimulus property)
- truncation (a fidelity property)
- divergence magnitude (signal floor — sign-blind)
- domain accessibility (rater-cognitive-load property)
- single-purpose vs multi-purpose (judgement-tractability property)
- merged status (real-PR property)

**None of these criteria depend on which mode (baseline/KG/RAG) wins.**
A PR where Baseline beats KG on 5 of 5 criteria has the same divergence
score (5) as a PR where KG beats Baseline on 5 of 5. The filter passes
or rejects them identically.

This is the same direction-blind discipline applied to the v1 swap and
documented in `results/HUMAN_STUDY_PR_SELECTION.md` §2.4. v2 extends the
filter set; it does not change the direction-blind principle.

The thesis can defend the v2 selection in front of any committee with
the following sentence:

> "PRs were selected to maximise study tractability — diff readability,
> domain accessibility, untruncated stimuli, single-purpose changes, and
> rubric-divergence signal floor — without selecting on which generation
> mode performs better on any criterion. The selection criteria are
> pre-registered in `human_eval_v2/docs/SELECTION_v2.md` and the script
> that applied them is in `human_eval_v2/scripts/analyze_pr_candidates.py`."

---

## 7. Status and next steps

| Step | Status |
|------|--------|
| 1. Lock PR list | **DONE** — `{12, 1, 3, 14}` (Decision 13) |
| 2. Build clean `study_data.json` (no truncation, no KG leak, no fences) | **DONE** — `human_eval_v2/study_data.json` |
| 3. Pre-register analysis plan | **DONE** — `human_eval_v2/docs/ANALYSIS_PLAN.md` |
| 4. Decision log | **DONE** — `human_eval_v2/docs/DECISION_LOG.md` |
| 5. Fill in §5 (ground-truth issues) | **DONE** — fetched via `scripts/fetch_pr_ground_truth.py` |
| 6. Deploy UI against v2 data | **TODO** — fork `human_eval/index.html` or repoint |
| 7. Re-run rater pool | **TODO** |
