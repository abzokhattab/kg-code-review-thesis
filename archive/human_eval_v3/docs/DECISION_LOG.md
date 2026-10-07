# v2 Human-Study Decision Log

_All numbered decisions below were taken **before any v2 rater data was
collected**. They are recorded here so a thesis examiner can audit the
chain of reasoning that produced the v2 PR list. Every decision was
made on direction-blind criteria (stimulus quality, signal floor,
rater accessibility) — never on which generation mode (baseline / KG /
RAG) the change would advantage._

Date: 2026-04-29 (initial), 2026-04-30 (Decision 13 revision).
Author of v2 protocol: thesis author (Abdu Khattab).
v1 study run that motivated v2: rater data in `human_eval/raters/`.

---

## Why a v2 was needed at all

The v1 study (`human_eval/study_data.json`, PRs `{17, 3, 19, 22, 10, 21}`)
exposed four flaws under post-hoc inspection. Each is documented with
the file it surfaced in:

1. **Silent diff truncation on 2 of 6 PRs.**
   - `data/luca_prs_fixed/pr10_evidence.json`: `len(full_diff) == 15000`
     exactly — sklearn `joblib` PR.
   - `data/luca_prs_fixed/pr21_evidence.json`: `len(full_diff) == 15000`
     exactly — Kafka JDK-11 PR.
   - The 15 kB cap in `scripts/run_luca_experiment.py` truncates the
     diff handed to *both* the LLM judge and the human rater. They see
     the same partial stimulus, so this does not break agreement
     calculation per se — but it confounds C6 ("missing information"):
     a rater cannot judge completeness when the stimulus itself is
     incomplete.

2. **KG mode-leak in the Traceability section.**
   - In v1, KG-generated reviews emit a literal `- Code Owners: ...`
     bullet that baseline and RAG reviews never emit. A rater who
     develops a heuristic ("the one with Code Owners is the KG one")
     can de-blind themselves trial-by-trial. This was confirmed by
     manual inspection of `human_eval/study_data.json` for PRs 17, 12,
     3, 18.

3. **Niche-stack PRs.** PRs 10, 21, 22 require Kafka/Gradle/joblib
   internals to evaluate; v1 raters reported (informally) that they
   skipped criterion C6 on these PRs because they did not understand
   the diff.

4. **No ground-truth anchor for C6.** v1 did not document what "the
   obvious issue" of each PR was, so the C6 rating is a Rorschach test.

The v2 redesign addresses all four flaws.

---

## Decisions

### Decision 1 — Define the v2 filter set _before_ ranking PRs

The filter set is the nine boolean filters in
`human_eval_v2/scripts/analyze_pr_candidates.py` (see `SELECTION_v2.md`
§2). The script was committed before any PR was inspected manually for
review content, so the filter is formally pre-registered.

**Direction-blindness check.** Every filter is on a stimulus property
(diff length, truncation, mainstream stack, single-purpose, merged
status, not-revert, not-docs-only) or a signal-magnitude property
(divergence ≥ 2). None depend on which mode wins. A PR where Baseline
beats KG 5–0 and a PR where KG beats Baseline 5–0 score identically.

### Decision 2 — Drop v1 PRs 10, 21, 22

- **PR 10** (sklearn joblib): truncated. Drop on filter #3.
- **PR 21** (Kafka JDK 11): truncated. Drop on filter #3.
- **PR 22** (Kafka assertion-style migration): not single-purpose
  (5 files, 3 distinct change types — file move + assertion swap +
  dependency update) and niche stack. Drop on filters #8 + #9.

These are dropped on stimulus-quality grounds. We did not look at
whether v1 results favoured KG, baseline, or RAG on these PRs.

### Decision 3 — Drop PR 18 (post-spot-check)

PR 18 (`jenkinsci/jenkins#9002 — Further reduce usages of StringUtils`)
was the original Option-A 5th pick. It passed every numeric filter:
Σ div = 2, 7 152 b, single-purpose, mainstream Java.

Manual inspection of the three reviews (caller: assistant, see
transcript) found:

| Mode     | Recommendation |
|----------|----------------|
| baseline | "Re-introduce `StringUtils.isBlank` for null safety." |
| KG       | "Restore `StringUtils.isEmpty` for edge-case handling." |
| RAG      | "Use `StringUtils` to handle null inputs gracefully." |

All three modes recommend the **opposite** of the PR's substantive
change. A rater asked to compare them on F2 (edge cases), F3
(integration), or Q5 (reasoning) has no basis to discriminate — every
review is wrong in the same direction.

This is a *trial-quality* failure: the trial provides no signal. We did
not check which mode v1 raters preferred on PR 18 before deciding to
drop it.

### Decision 4 — Add PRs 1, 12, 14 (post-spot-check)

PR candidates ranked 1st–9th in
`human_eval_v2/analysis/pr_candidates.md` after applying the nine
filters were spot-checked manually for review-content discriminability.
The decision rule was:

> "If the three reviews catch substantively different issues that a
> rater can use to discriminate on the rubric, keep the PR. If the
> three reviews paraphrase the same content, drop or de-prioritise."

| PR | Spot-check verdict |
|---:|--------------------|
|  1 | KEEP — RAG catches a real concrete bug the others miss |
| 12 | KEEP — three reviews disagree on input validation vs. tests vs. type strictness |
| 14 | KEEP — three reviews disagree on `vh`/`vw`, `getContainer`, missing tests |
| 18 | DROP — see Decision 3 |
| 23 | DROP — three reviews flag the *same* 3 issues with different wording |

Decisions 3 and 4 do not look at which mode wins; they look at whether
the reviews differ enough for a rater to grade them on different
criteria.

### Decision 5 — Pre-register success / failure / null criteria

Defined in `ANALYSIS_PLAN.md`. The decision rule for "the human study
validated the LLM judge" is set before the rater data is collected and
will not be moved post-hoc.

### Decision 6 — Apply review-text cleanups

Three cleanups are applied by `build_study_data_v2.py` to every review
that goes into v2:

1. **Strip leading/trailing ` ``` ` fences** — these were a v1 rendering
   artefact, not part of the substantive review content.
2. **Strip the "- Code Owners: ..." bullet from KG Traceability
   sections** — these are KG-specific surface tokens that allow
   de-blinding. After stripping, if the Traceability section is empty,
   it is filled with the literal text `Not specified` so the surface
   form matches baseline/RAG (which often have empty Traceability
   too).
3. **Append a truncation marker if the diff is at the 15 kB cap** —
   defensive only; the v2 selection avoids these PRs entirely.

These are surface-form normalisations. They do not change which issues
the review flags or which recommendations it makes. They make the
three modes equally de-blindable, not more or less.

### Decision 7 — Recover PR bodies from GitHub for PR 1 and PR 3

The deep audit (`scripts/deep_audit.py`) found that `pr1_evidence.json`
and `pr3_evidence.json` had **empty** PR bodies (0 chars). A rater who
clicks "Read PR description" before evaluating the reviews would see
nothing, which corrupts criterion C6 ("missing information") because
there is no anchor for what the PR is *trying* to do.

The real PR bodies exist on GitHub:

- PR 1 (godotengine/godot#73144): 2 686 chars after stripping HTML
  comments and template boilerplate.
- PR 3 (grafana/grafana#97224): 1 191 chars after the same cleanup.

Resolution:

- `scripts/fetch_pr_bodies.py` fetches all 6 PR bodies via the GitHub
  REST API, strips HTML comments and inline images, and writes them
  to `human_eval_v2/data/pr_body_overrides.json`.
- `build_study_data_v2.py` reads the override file and prefers it over
  the local evidence-pack body. The override applies to all 6 PRs (not
  just 1 and 3) for consistency and to recover any other locally
  truncated bodies.
- The fetched bodies are committed to the repository so the build is
  reproducible without re-hitting the GitHub API.

**Direction-blindness check.** The PR body is a property of the PR,
not of any generation mode. Recovering it does not advantage any mode.

### Decision 8 — Drop the Traceability section entirely

The deep audit found that **every** PR × mode in the v2 selection has
a Traceability section containing only `Not specified`. This was true
in the raw outputs (post-Code-Owners-strip, the section becomes
literally the two characters `Not specified` for every review).

Three options were considered:

1. Keep the literal `Not specified` text (status quo).
2. Drop the Traceability header and body for reviews where it is
   uniformly empty.
3. Drop the Traceability section in **all** reviews unconditionally.

Option 3 was chosen. Justification:

- The Traceability section provides zero rater-decision value for any
  review in the v2 selection (every section says exactly the same two
  words).
- It contributes ~35–50 chars of visual noise to every review, and
  more importantly it adds a uniform overhead that makes review-length
  comparisons noisier without adding signal.
- It is symmetric across all three modes (every mode has it; every
  mode says `Not specified`), so removing it does not advantage any
  mode and does not change the κ computation.
- Removing it makes the rater UI cleaner — every review now ends with
  `Recommendation` followed by `Review Note — Evidence-Anchored`.

The strip is implemented in `drop_empty_traceability_section()` in
`build_study_data_v2.py`. It only removes Traceability sections whose
body is empty or contains only "Not specified" / "N/A" / "None".

**Direction-blindness check.** Applied symmetrically to all three
modes. Does not change which issues a review flags or which
recommendations it makes.

### Decision 9 — Do NOT fix KG path hallucinations

The deep audit found that KG-mode reviews on 3 of 6 PRs reference
file paths that do not appear in the diff:

- PR 17 KG: `DescribableList.java`, `Descriptor.java`,
  `HeteroListTest.java`
- PR 14 KG: `SaveDashboardDrawer.test.tsx`
- PR 19 KG: `DirectoryBrowserSupportTest.java`,
  `IconSetTest.java`

These are real KG outputs. Editing or removing them would corrupt the
experimental signal: criteria F3 ("concrete components") and T3
("concrete test files") are *exactly* the criteria that should
distinguish "names a real test file in the diff" from "name-drops a
plausible-sounding test file that doesn't exist." The whole point of
the study is to find out whether human raters can make this
distinction.

Hallucinations are flagged in `deep_audit.py` output as warnings, not
problems. They are documented in `ANALYSIS_PLAN.md` §4 as a known
property of the KG mode that the study must measure, not hide.

### Decision 10 — Do NOT normalise systematic mode-length differences

The deep audit found a systematic length gap:

| Mode     | Mean review length | Range       |
|----------|-------------------:|-------------|
| baseline | 1 589 chars        | 1 362–2 005 |
| kg       | 1 868 chars        | 1 536–2 250 |
| rag      | 1 572 chars        | 1 212–1 740 |

KG is longer than baseline in 6 of 6 PRs and longer than RAG in 5 of
6 PRs. Mean overhead: ~17 % over baseline, ~19 % over RAG.

Three options were considered:

1. Truncate KG reviews to match baseline length.
2. Pad baseline/RAG reviews to match KG length.
3. Leave as-is and disclose as a threat to validity.

Options 1 and 2 are unacceptable because they corrupt experimental
content. The KG mode is *designed* to surface more concrete entities;
truncating it would remove what the study is supposed to measure.
Padding baseline/RAG with synthetic content is fabrication.

Option 3 was chosen. Specific mitigation:

- The rater UI uses CSS Grid with equal-height review cards and
  internal scroll, so the visual height tell is partially mitigated.
- `ANALYSIS_PLAN.md` §4 documents this as a known threat to validity.
- Sensitivity analysis pre-registered: compute κ on the subset of
  trials where the mode-pair length ratio is < 1.2x (closely-matched
  lengths) and report whether the headline result holds.

### Decision 11 — Disclose KG language-coverage gap; do not edit the PR set

After locking the PR set and running the deep audit, we cross-checked
each PR's file-extension distribution against the tree-sitter parsers
declared in `scripts/build_kg_evidence_ast.py`. KG officially supports
Python, Java, TypeScript/JS, Go, C++, and Scala. It does **not**
support Jelly (Jenkins's XML templating language), GDScript, MDX, or
binary assets.

The cross-check showed that:

- PRs 12 (C++), 1 (C++), 3 (TypeScript), and 14 (TypeScript) are
  fully parseable by KG. **No KG hallucinations were flagged on these
  PRs in the deep audit.**
- PR 17 (Jelly only) has zero parseable changed files. **KG path
  hallucinations: 3.**
- PR 19 (Java + Jelly + binaries) has 2 of 11 changed files
  parseable. **KG path hallucinations: 2.**

The audit's KG-hallucinated-path warnings are concentrated **exactly**
on the PRs where KG cannot AST-parse the change. This is not
coincidence; it is the predictable failure mode of an AST-grounded
retrieval system on unsupported file types.

**Decision (initial, 2026-04-29; superseded by Decision 13).** Do
not edit the PR set. Disclose the language-coverage gap as a
pre-registered threat to validity and run a sensitivity analysis on
the KG-fully-parseable subset.

> **Status: SUPERSEDED by Decision 13 (2026-04-30).** The reasoning
> above (the disclosure-plus-sensitivity-analysis option) was
> reconsidered the following day and reversed in favour of the
> simpler, more defensible 4-PR selection. The original text is
> preserved here as part of the audit trail: it documents both
> options that were considered and the eventual reason for choosing
> the cleaner cut.

**Why not drop PRs 17 and 19 (initial reasoning).** Dropping them
after observing how KG performs on them would be post-hoc selection
— a direction-blind violation. The list of filters that produced
the v2 selection is fixed in `analyze_pr_candidates.py`; "KG can
parse the file types in this PR" is not one of them, and adding it
now would change the selection in a way that depends on a measured
property of the system under test.

**Direction-blindness check (revised in Decision 13).** This concern
turns out not to apply. "KG-parseable file types" is a *stimulus
property* (a fact about the input), not a *system-output property*
(a fact about which mode wins). It is a property of the diff itself,
knowable before any model is run. Adding it as a filter is therefore
no more direction-revealing than adding "diff under 5 kB" or
"single-purpose change" — both of which are already in the filter
set. See Decision 13 for the full revised analysis.

### Decision 12 — Keep v1 data for the writeup

v1 data (`human_eval/study_data.json` and `human_eval/raters/*.json`)
is preserved unmodified. The thesis writeup will report:

- the v1 study findings (with their flaws disclosed in §threats-to-
  validity);
- the v2 study findings (cleaner stimuli, locked selection);
- and whether the two converge.

Reporting both is the conservative, defensible thing to do. It is not
a backup if v2 doesn't go our way — both will be reported regardless
of result.

### Decision 13 — Drop PRs 17 and 19; finalise on 4 KG-fully-parseable PRs (2026-04-30)

This decision **reverses** Decision 11 (which had elected to keep
PRs 17 and 19 and disclose the language-coverage gap as a sensitivity
analysis). Both decisions are recorded so the reasoning chain is
transparent.

**Trigger.** A senior-engineering re-read of the v2 design after the
deep audit produced its findings. The audit
(`scripts/deep_audit.py`) showed that the three KG-path-hallucination
warnings on PR 17 and the two on PR 19 were precisely the structural
signal of degraded grounding (KG cannot tree-sitter-parse Jelly), and
that PRs 1, 3, 12, 14 were warning-free.

**The two options that were actually on the table.**

| Option | PRs | What it asks the human study to validate |
|--------|-----|-------------------------------------------|
| A (kept Decision 11)  | 17, 12, 1, 3, 14, 19 | Validates the LLM judge on KG-supported *and* KG-unsupported file types, with a sensitivity-analysis split. |
| B (this decision)     |     12, 1, 3, 14    | Validates the LLM judge on KG-supported file types only; the KG-unsupported case is reported on the 25-PR LLM-judge dataset alone in §threats-to-validity. |

**The five sub-questions and how they resolved.**

1. **Does Option A violate direction-blindness?**
   No. "KG-parseable file types" is a stimulus property (a fact
   about the diff, not about which mode wins). It belongs on the
   same shelf as "diff under 5 kB" and "single-purpose change". The
   original concern in Decision 11 was misplaced.

2. **Is Option A's rubric-stress-test framing real or post-hoc?**
   Real but oblique. The rubric *does* discriminate
   hallucinated-versus-grounded test-file references via
   criterion T3, and we *would* see this signal in the data. But
   that is not the thesis's primary research question — the
   thesis's primary research question is whether the LLM judge can
   substitute for human raters. Adding a sub-claim about
   "rubric-stress-test detection" complicates the defence without
   strengthening the headline claim.

3. **What would an examiner do with Option A?**
   The first defence question would predictably be: "Why include
   PRs your system structurally cannot handle?" The clean answer
   ("we wanted to test the rubric's hallucination-detection") is
   defensible but requires explaining a multi-layer methodological
   choice live, under pressure, by a candidate who is honest that
   they are early-career.

4. **What would an examiner do with Option B?**
   The same question is replaced by: "What does this say about
   real-world deployment where KG might encounter unsupported
   files?" The clean answer ("the 25-PR LLM-judge dataset shows
   exactly that — see §X — and the human study deliberately
   validates the judge only on the operating envelope KG was
   designed for") is shorter and easier to deliver.

5. **Is Option B underpowered?**
   No. 4 PRs × 5 criteria × 20 raters × 2 comparisons (BL-vs-KG and
   KG-vs-RAG) = 800 ratings. The non-tie-rate threshold from
   `POWER_ANALYSIS.md` is 124 non-ties; expected non-ties at 50%
   discrimination = 400. Approximately 3.2× over-powered.

**Cost of dropping the two PRs.**

- Two stimuli, ~20 minutes of rater time. (Net per-rater session
  drops from ~75 min to ~55 min — a usability gain.)
- All Jenkins/Java representation. The 25-PR LLM-judge dataset
  retains Jenkins; only the human-study validation sub-sample loses
  it. This is acceptable because the human study's job is κ
  estimation on a representative sub-sample, not exhaustive
  per-repo coverage.
- The "rubric correctly detects KG hallucinations on unsupported
  file types" sub-claim. This is reported as a qualitative
  observation in §threats-to-validity rather than as a measured
  result.

**Replacement search.** The PR-candidates table was rescanned for
clean replacements that would preserve a 6-PR set:

- PR 7 (TS, Drilldowns) — truncated at 15 kB, not eligible.
- PR 5, PR 9, PR 10, PR 21 — truncated at 15 kB.
- PR 11, PR 25, PR 26 — docs-only / revert / paraphrasing-only
  reviews.
- PR 18 — already dropped (Decision 3, all modes converge on the
  wrong direction).
- PR 22 — niche stack (Kafka/Gradle), failed v2 mainstream filter.

There is no clean 5th or 6th PR. Forcing a flawed replacement to
preserve the count would degrade the study; truncating to a clean 4
preserves quality.

**Final selection.** PRs `{12, 1, 3, 14}` — 2 godot (C++) + 2
grafana (TypeScript), all 100% KG-parseable, all under 13 kB, all
spot-checked, all single-purpose.

**Direction-blindness check.** "KG-parseable file types" is a
property of the input, established by inspecting the file
extensions of the changed files in each PR diff and cross-checking
against the language list in `scripts/build_kg_evidence_ast.py`. It
does not depend on any model output. PRs 17 and 19 are dropped
because their inputs are outside KG's operating envelope, not
because of how any mode performed.

**Files updated by this decision.**

- `human_eval_v2/scripts/build_study_data_v2.py` (`FINAL` → `[12, 1, 3, 14]`).
- `human_eval_v2/study_data.json` (rebuilt).
- `human_eval_v2/scripts/smoke_test.py` (`EXPECTED_PRS` → `{12, 1, 3, 14}`).
- `human_eval_v2/docs/SELECTION_v2.md` (locked selection rewritten).
- `human_eval_v2/docs/ANALYSIS_PLAN.md` (§4.7 simplified; §6 sample
  size updated).
- `human_eval_v2/README.md` (PR list and v1-vs-v2 table updated).

Verified by re-running `smoke_test.py` (clean) and `deep_audit.py`
(0 problems, 2 minor warnings on PR 14 only — both already
documented in `ANALYSIS_PLAN.md` §4.5).

---

### Decision 14 — Re-cut human study to use `dataset_v2` reviews (2026-05-05)

**Context.** Between Decision 13 (locking the 4-PR human study on v2)
and any rater data being collected, an audit of the underlying 25-PR
LLM-judge dataset surfaced 8 categories of data-quality issues that
required a rebuild (see `dataset_v2/docs/AUDIT_v1.md`). The clean
18-PR `dataset_v2` was generated from full GitHub bodies (was empty
for 10 of 18 PRs in v1), 50 kB diffs (was 15 kB-truncated for 9 of 18
PRs in v1) and rebuilt RAG context (was contaminated `changed_files`
for 4 of 18 PRs in v1). The v2 LLM-judge panel ran on those reviews
(`outputs/luca_prs_v2/`) and produced the cleaned headline
result in `results/V1_VS_V2_COMPARISON.md`.

**Trigger.** The human study (`human_eval_v2/`) still pointed at the
v1 reviews in `outputs/luca_prs_fixed/`. RQ3's whole point — "validate
the LLM judge against humans on the same stimuli" — silently breaks
if humans grade v1 reviews while the LLM-judge κ is computed on v2
reviews. Concrete drift example for PR 1 KG (godot/openxr):
- v1 review: _"replaces the **operating system alert dialog**…"_
  (vague, derived from an empty body)
- v2 review: _"replaces an **OpenXR initialization failure alert
  dialog**…"_ (specific, derived from the recovered body)

The two sentences score differently on the rubric (R1 — concrete
naming) and would predictably lead a human rater to a different
preference. Reporting human↔LLM agreement on mismatched stimuli would
not be honest.

**Decision.** Clone `human_eval_v2/` to `human_eval_v3/` and re-cut
the study to read from `data/luca_prs_v2/` + `outputs/luca_prs_v2/`.
The PR set is **unchanged** (Decision 13 still binds: `{12, 1, 3, 14}`,
all four are subsets of the 18 v2 PRs). All cleanup logic
(fence-strip, code-owners-leak strip, empty-Traceability-section
strip) carries over verbatim. The rater UI and protocol are
unchanged. The study identity changes:

| Aspect | v2 | v3 |
|--------|----|----|
| Evidence packs | `data/luca_prs_fixed/` | `data/luca_prs_v2/` |
| LLM reviews | `outputs/luca_prs_fixed/` | `outputs/luca_prs_v2/` |
| `STUDY_ID` | `human_eval_v2` | `human_eval_v3` |
| localStorage prefix | `heval3_v2_` | `heval3_v3_` |
| Diff cap (defensive) | 15 kB | 50 kB |
| PR set | `{12, 1, 3, 14}` | `{12, 1, 3, 14}` (unchanged) |
| Criteria, modes, comparisons, UI | identical | identical |

**Direction-blindness check.** Selecting which review *set* to show
the rater is a stimulus-quality choice ("show the better-grounded
reviews"), not a mode-direction choice. Modes (baseline / KG / RAG)
are unchanged; both review sets contain the same three modes for the
same four PRs. The fix improves the *quality of all three modes
uniformly* by recovering the PR body that all three originally lacked.
It does not preferentially advantage any one mode.

**Why a separate folder rather than overwriting v2.**
Clone-rather-than-overwrite is the same discipline applied to
`dataset_v2/`: the v2 artefacts stay byte-identical so the writeup
can show the full rebuild trail. If a thesis examiner asks
*"what changed and what did it do to the result?"*, both folders
are present on disk, both are reproducible, and both can be diffed.

**Cost.** Free. The v2 reviews already exist on disk (Phase 2 of the
`dataset_v2/` rebuild). No new LLM calls.

**Files created by this decision.**

- `human_eval_v3/` (full clone of `human_eval_v2/`).
- `human_eval_v3/scripts/build_study_data_v2.py` repointed at
  `data/luca_prs_v2/` + `outputs/luca_prs_v2/`; truncation threshold
  raised to 50 kB; review loader strict (no fallback to v1).
- `human_eval_v3/scripts/smoke_test.py` updated:
  `STUDY_ID="human_eval_v3"`, `heval3_v3_` localStorage key, 50 kB
  diff cap.
- `human_eval_v3/scripts/deep_audit.py` repointed at
  `human_eval_v3/study_data.json`.
- `human_eval_v3/index.html` updated: `STUDY_ID="human_eval_v3"`,
  `heval3_v3_` localStorage key, header comment updated.
- `human_eval_v3/study_data.json` rebuilt from v2 evidence + reviews.

Verified by re-running `smoke_test.py` (all checks pass) and
`deep_audit.py` (0 problems, 1 minor warning carried over from v2 —
PR 14 KG references a test file in the working tree that isn't in
the diff; same warning class as v2, not introduced by this swap).

**What does NOT change.**

- The PR selection (Decision 13 stands).
- The criteria, modes, comparisons, sample-size justification.
- The pre-registered analysis plan
  (`human_eval_v3/docs/ANALYSIS_PLAN.md`, identical to v2).
- The decision-blindness arguments in Decisions 1–13.
- The v1 study (`human_eval/`) and v2 study (`human_eval_v2/`)
  folders are unchanged on disk.

**Defence soundbite.** "We re-cut the human study to use the same
review set our LLM-judge graded, after auditing and rebuilding the
underlying dataset. Both the v2 and v3 stimuli are present on disk;
v3 is what the κ in the writeup is computed on; v2 is preserved so
anyone can verify the swap was a strict improvement and not a
post-hoc result hunt."

---

### Decision 15 — Reduce cognitive load and surface review differences (2026-05-05)

**Trigger.** A single-rater walkthrough
(`results/RATER_WALKTHROUGH_v2_vs_v3.md`) showed that 7 of 8 v3 trials
end in `both equally` for one careful rater. The rubric is binary and
many criteria score the same for genuinely-similar reviews; the LLM-judge
v2 result also says the per-PR effect is small (~+1pp total, ~+7pp on
KG-relevant). Two risks then dominate the human-study outcome:
1. **Cognitive load** — 4 PRs × 2 comparisons × 12 binary cells per
   trial × ~3 min/trial = ~25 min of close reading. Fatigue → skim →
   noisy data. The auto-flag system flags this post-hoc, but ideally
   the design should not provoke it.
2. **Discriminability** — review pairs are visually similar (same
   structure, similar length, similar topics). A rater who can't *see*
   the difference at a glance has to read both end-to-end and remember
   them, which is exactly what causes skim-and-tick.

**Decision.** Three changes, all in `human_eval_v3/`:

1. **Trim to one comparison per PR (`bl_vs_kg` only).** The
   `kg_vs_rag` comparison is removed. Total session: 4 trials × ~3 min
   ≈ ~10–12 min. The retained comparison answers the central thesis
   question (does adding KG context help over a vanilla diff-only
   baseline?). The `kg_vs_rag` answer is already in the LLM-judge data
   (`results/V1_VS_V2_COMPARISON.md`); duplicating it in human eval is
   not the lever that buys κ confidence — quality of `bl_vs_kg`
   ratings is.

2. **Sentence-level uniqueness highlighting between A and B.** Every
   leaf text block (`<p>`, `<li>`) in Review A is matched against
   every block in Review B by token-Jaccard similarity (threshold
   0.50). Blocks below the threshold are visually shaded with a colored
   side-bar in the rater's UI. A "hide highlighting" toggle lets the
   rater turn it off. This is a *display* aid, not an analysis aid —
   the underlying review text is unchanged, so neither κ nor any
   downstream metric is affected. It just makes the differences
   visible without forcing the rater to memorize and compare two 1.5
   kB walls of text.

3. **"What's the main difference?" textarea + attention-flag.** The
   existing optional `notes` field is promoted to a more prominent
   "what differs?" prompt below the review pair. Two new quality flags
   are added:
   - `attention:notes_empty_majority` — rater wrote < 5 chars on ≥ 50 %
     of trials.
   - `attention:notes_dismissive_majority` — rater wrote dismissive
     content (`idk`, `none`, `same`, `n/a`, `---`, etc.) on ≥ 50 % of
     trials.
   Both are recorded but not auto-excluding; the analyzer
   (`scripts/analyze_human_llm_agreement.py --exclude-flagged`) can
   choose to drop those raters at analysis time, with sensitivity
   analysis kept-vs-dropped reported in the writeup.

**Direction-blindness check.** Every change here is symmetric across
the two reviews shown in each trial. Highlighting uses the same
threshold for "unique to A" and "unique to B"; the textarea prompt
mentions both A and B; the comparison set retained (`bl_vs_kg`) is
the central RQ2 question — selecting it cannot bias the result toward
or against any specific mode. The change makes raters more accurate,
not more biased.

**Statistical impact.** With 4 trials × 6 criteria × 2 reviews ×
≥ 10 raters = ≥ 480 paired binary cells, κ is still well-powered.
The original plan's 960-cell budget at 20 raters becomes 480 at the
same N, or 960 at 20 raters with the trimmed design — both are above
the κ-minimum of ~120 paired observations from
`results/POWER_ANALYSIS.md`.

**Not changed.**
- The 4-PR set (`{12, 1, 3, 14}`) — Decision 13 still binds.
- The 6-criterion rubric — same definitions, same wording.
- The pre-registered analysis plan
  (`human_eval_v3/docs/ANALYSIS_PLAN.md`) — what it analyses is
  unchanged; how many trials per rater is reduced.
- v1 and v2 study folders — unchanged on disk.

**Files updated.**
- `human_eval_v3/scripts/build_study_data_v2.py` (`COMPARISONS` →
  `bl_vs_kg` only).
- `human_eval_v3/study_data.json` (rebuilt — 1 comparison block).
- `human_eval_v3/scripts/smoke_test.py` (expects 1 comparison; checks
  `bl_vs_kg` is the one).
- `human_eval_v3/index.html`:
  - `shadeUniqueBlocks(htmlA, htmlB)` + `_jaccard` helpers.
  - `#diffLegend` + "hide highlighting" toggle.
  - `#whatDiffersWrap` (promoted notes prompt).
  - `computeQualityFlags()` adds the two attention flags.
  - Briefing copy updated (`8 screens` → `4 screens`,
    `~20-25 min` → `~10-12 min`).
  - CSS for `.uniq-A`, `.uniq-B`, `.diff-hidden`, `#diffLegend`,
    `#whatDiffersWrap`.
- `human_eval_v3/README.md` (selection table unchanged; trial-count
  block + UX-affordance description added).

**Compensation note (not a code decision; a study design lever).** The
single biggest fix for skim-and-tick is paying raters $10–15 per
session. Personal acquaintances will skim; a paid stranger reads
carefully. Master's-thesis budgets typically cover this — ~$200–300
for 20 raters. This is recorded here because we want the audit trail
to show we considered it, but it is not in scope for this decision
because it is a separate funding choice the candidate has to make.

---

### Decision 16 — Add PRs 21 and 24 to recover 6-PR scope (2026-05-05)

**Trigger.** A supervisor-meeting-prep review of the human-study size
(4 PRs after Decision 13's drop of 17/19) raised a fair concern: the
sample shrunk visibly without a methodological reason that's portable
to a defense conversation. Decision 13 had stated *"there is no clean
5th or 6th PR"* but that was framed against the v1-evidence pool
(when many candidates were truncated or had stale flags). With the
v2 audit complete (`dataset_v2/docs/SELECTION_v2.md`), the candidate
pool is different.

**Direction-blindness check before re-opening.** Two things had to be
true to even consider adding PRs without contaminating the design:

1. The replacement criteria must be **the same** ones used to lock
   the original 4. Re-opening with relaxed criteria would be moving
   the goalposts.
2. We must **not** look at LLM-judge-favours-which-mode metrics on
   the candidate pool while ranking. The selector must be metrics
   the v2 audit already produced (divergence, KG-parseability, diff
   size), not a "how does KG do on this PR" lookup against v2 panel
   results.

Both conditions hold: the 5 v2 audit criteria
(`dataset_v2/docs/SELECTION_v2.md`) are pre-existing and direction-
blind; the divergence ranking comes from
`human_eval_v2/analysis/pr_candidates.json` which was computed before
the v3 stimulus swap.

**Replacement search (against the 14 PRs in dataset_v2 not yet in
the human study).** Re-audit (this time against v2 evidence packs,
which have full diffs and accurate file lists) found two clean
candidates that pass every constraint Decision 13 imposed:

| PR | Repo | Lang | Diff (v2) | KG-parseable% | Total divergence |
|---:|------|------|----------:|--------------:|-----------------:|
| 21 | apache/kafka | Java + Scala | 27 kB | 100 % (11/11 files) | 5 |
| 24 | scikit-learn | Python | 16 kB | 100 % (8/8 files) | 4 |

Both are merged, neither is a revert or docs-only, every changed file
is in a tree-sitter-supported language, and both already have
generated reviews in `outputs/luca_prs_v2/` (so the LLM-judge has
already scored them — but those scores were not consulted during
ranking).

**Why 21 and 24 specifically (rather than other candidates).**

- **PR 22** (kafka, Java + Gradle): only 60% KG-parseable (Gradle and
  XML files), same Decision-13 KG-coverage failure. Skipped.
- **PR 19** (jenkins, Java + Jelly): 18% KG-parseable. Same as
  Decision 13. Skipped.
- **PR 18** (jenkins, Java): 100 % KG-parseable but was already
  dropped by Decision 3 (modes converged on the same incorrect
  recommendation). Skipped on those grounds.
- **PR 13** (godot, C++ + Obj-C++): 47 kB diff is too large for the
  rater-time budget after Decision 15. Skipped.
- **PR 10** (sklearn): 22 kB, 94 % KG-parseable (one .rst file).
  Eligible but PR 24 has identical language coverage with a smaller
  diff and equal divergence; 24 is the better pick on rater-time.
- **PRs 23, 20, 6, 8, 9, 15, 2**: divergence ≤ 2 — would not stress
  the rubric's discriminating power.

**Stack diversity gain.** Pre-Decision-16 the human study had:
- 2× C++ (godot PRs 1 + 12)
- 2× TypeScript (grafana PRs 3 + 14)

Post-Decision-16 it has:
- 2× C++ (godot)
- 2× TypeScript (grafana)
- 1× Java/Scala (kafka, PR 21)
- 1× Python (sklearn, PR 24)

This brings JVM-stack and Python coverage back, so the κ estimate is
not narrowly conditioned on C++ + TS reviewing.

**Cost in rater time.** 4 trials × ~3 min ≈ 12 min  →  6 trials × ~3
min ≈ 18 min, on average. Still 30 % faster than the v2 design's ~25
min and well below the cognitive-load threshold targeted by
Decision 15. The compensation note in Decision 15 still applies: paid
raters at $10–15 will absorb the small marginal load without
skimming.

**Statistical impact.** Cell budget at 10 raters:
- Decision-15 (4 PRs): 4 × 6 criteria × 2 reviews × 10 = **480 cells**
- Decision-16 (6 PRs): 6 × 6 × 2 × 10 = **720 cells** — 50 % more
  paired observations for the same recruiting effort.

**Pipeline impact.** Trivial — both PRs already have v2 reviews on
disk and v2 LLM-judge scores in
`results/checklist_evaluation_llm_multi__v2.json`. No new generation
or judging needed. Build + smoke + deep audit re-run cleanly.

**Cleanup hardening (caught during the rebuild).** The audit revealed
that PR 24's KG review used `Teams: Not specified` (vs the
`Code Owners: Not specified` form in other PRs).
`drop_empty_traceability_section` was extended with a regex check for
any `<label>: Not specified` pattern, so any future PR that uses a
different label will also have its empty Traceability section
removed. This is a strict generalisation of the existing rule; no
previously-cleaned section is now retained.

**Files updated by this decision.**
- `human_eval_v3/scripts/build_study_data_v2.py` (`FINAL` →
  `[12, 1, 3, 14, 21, 24]`; `drop_empty_traceability_section` extended).
- `human_eval_v3/study_data.json` (rebuilt; 6 PRs, 1 comparison each).
- `human_eval_v3/scripts/smoke_test.py` (`EXPECTED_PRS` extended).
- `human_eval_v3/README.md` (selection table + outstanding-work
  checklist updated to 6).

Verified by re-running `smoke_test.py` (all checks pass) and
`deep_audit.py` (0 problems, 2 warnings — one is the carry-over
PR-14-KG test-file reference, the other is a PR-24 numbered-bullet
style that only matters in `kg_vs_rag` trials and the v3 study only
shows `bl_vs_kg`, so the bullet style is invisible to raters).

**Defence soundbite.** "After the v2 audit produced a clean 18-PR
LLM-judge dataset, two PRs that originally fell outside the
human-study budget — PR 21 (kafka, Java + Scala) and PR 24
(scikit-learn, Python) — turned out to satisfy every direction-blind
criterion the original 4 satisfied, including 100 % KG-parseability.
Adding them brought the human study back to 6 PRs while keeping every
piece of the design pre-registered. We did not consult LLM-judge
mode-favouring metrics during selection."

---

### Decision 17 — Swap PRs 12, 21, 3 for PRs 30, 22, 42 to raise rater discriminability (2026-05-13)

**Trigger.** Supervisor feedback: *"the two feedbacks are mostly the
same"*. An empirical measurement of baseline-vs-kg review pairs on
the locked 6 PRs (Decision 16) confirmed this concern.

**The measurement.** For every PR in dataset_v2, parse the
`## Problem` section of the baseline and kg reviews into atomic
bullets, then compute *problem-overlap* as the fraction of baseline
bullets that have a token-Jaccard ≥ 0.40 with any kg bullet. Lower
problem-overlap → more visible difference for a human rater.

Result for the locked 6 PRs (Decision 16):

| PR | Problem-overlap | Token Jaccard |
|---|---:|---:|
| PR 12 | **100 %** | 0.48 |
| PR 21 | 67 % | 0.36 |
| PR 1 | 50 % | 0.35 |
| PR 3 | 50 % | 0.49 |
| PR 24 | 50 % | 0.37 |
| PR 14 | 33 % | 0.43 |
| **mean** | **58 %** | 0.41 |

PR 12 produces effectively identical reviews under baseline and kg.
The remaining five hover around 33–67 % overlap. Mean overlap on the
locked selection is 58 %, *higher* than the dataset_v2 mean of 54 %
— so the prior selection (which optimised for cognitive load) is
slightly worse than average for the human study's discrimination
question.

Mean overlap across the unused 34 PRs in dataset_v2: 54 %. Top-six
lowest-overlap candidates (the most discriminable pairs):

| PR | Repo | Type | Problem-overlap | Why it's a fit |
|---|---|---|---:|---|
| PR 19 | jenkinsci/jenkins | UX (icons) | 0 % | Jelly-template risk — re-audit needed |
| PR 22 | apache/kafka | refactor (test move) | 0 % | Pure Java; no Jelly |
| PR 30 | godotengine/godot | test-addition | 0 % | C++ test code; small |
| PR 32 | scikit-learn | rename in test | 0 % | Python; very small |
| PR 33 | jenkinsci/jenkins | behaviour narrowing | 0 % | Re-audit Jelly; potential keep |
| PR 42 | scikit-learn | refactor (move) | 0 % | Python; cross-file move |

**Decision.** Swap three of the lowest-discriminability current PRs
for three of the highest-discriminability candidates that satisfy
the c1–c6 direction-blind criteria from `HUMAN_STUDY_PR_SELECTION.md`:

| Out | In | Swap rationale |
|---|---|---|
| **PR 12** (godot, 100 % overlap) | **PR 30** (godot, 0 % overlap, unit-tests) | Same repo + language; clearly visible difference |
| **PR 21** (kafka, 67 % overlap) | **PR 22** (kafka, 0 % overlap, refactor) | Same repo + language; refactor character |
| **PR 3** (grafana, 50 % overlap) | **PR 42** (sklearn, 0 % overlap, refactor) | Adds Python representation; cross-file move |

PR 19 was rejected (re-audit would be needed for Jelly templates).
PR 32 and PR 33 are kept as backup candidates if PR 22 or PR 42 fail
the smoke-test pipeline.

**Direction-blindness statement.** All three swaps were chosen on:

1. Lowest baseline-vs-kg *problem-overlap* (a structural property,
   not a mode-favouring outcome metric).
2. Diff size ≤ 50 kB (cognitive load).
3. Non-empty PR body (so the rater sees the maintainer's intent).
4. 100 % KG-parseable by tree-sitter (no Jelly, no binary-only
   changes).
5. All 4 mode reviews exist on disk (already generated; no new LLM
   spend needed).

**None of these criteria refer to the rubric coverage scores or
LLM-judge winning mode.** We did *not* look at which mode scored
higher on each candidate; we did not look at the criterion-level
`kg_relevant` Δ. The swap is a *discriminability* fix, not an
*effect-magnification* fix. Verified by the candidate list including
both PRs where KG-mode would presumably help (PR 30, PR 42 —
cross-file structure) and where it presumably wouldn't (PR 22 — pure
test move).

**Effect on study composition.**

| | Before (Decision 16) | After (Decision 17) |
|---|---|---|
| PRs | {12, 1, 3, 14, 21, 24} | {1, 14, 22, 24, 30, 42} |
| Repos | godot, grafana, kafka, sklearn (4) | godot, grafana, kafka, sklearn (4) |
| Languages | C++ ×2, TS ×2, Java ×1, Py ×1 | C++ ×2, TS ×1, Java ×1, Py ×2 |
| PR types | feature ×4, refactor ×2 | feature ×2, refactor ×3, test-add ×1 |
| Mean problem-overlap (bl ↔ kg) | 58 % | ~27 % (predicted) |

Languages slightly rebalanced (one TS drops, one Python adds). PR-type
distribution shifts toward refactors and tests — which is *good* for the
human study because refactors are where the rater is most likely to
benefit from cross-file context (the kind of insight KG is designed to
provide).

**What did NOT change.**

- The 25-criterion rubric, the 3-judge panel, and the 40-PR LLM-judge
  dataset are *all* untouched. Decision 17 only affects which sub-sample
  of those 40 is shown to human raters.
- The pre-registered analysis plan (`docs/ANALYSIS_PLAN.md`) is
  unchanged — same `bl_vs_kg` comparison, same Likert-scale design, same
  paired permutation test.
- No re-generation of reviews, no re-running of the LLM panel. All
  swap reviews come from `outputs/luca_prs_v2/` which has been on disk
  since 2026-05-05.

**Files updated by this decision.**

- `human_eval_v3/scripts/build_study_data_v2.py` (`FINAL` →
  `[1, 14, 22, 24, 30, 42]`; comment block updated with the
  problem-overlap rationale).
- `human_eval_v3/study_data.json` (rebuilt; 6 PRs × 1 comparison each).
- `human_eval_v3/scripts/smoke_test.py` (`EXPECTED_PRS` updated; PR 12
  body-length carve-out removed since PR 12 no longer in study).
- `human_eval_v3/docs/HUMAN_STUDY_PR_SELECTION.md` (final table updated).

Verified: `smoke_test.py` passes all 7 study-data checks and all 6
index.html checks; v3 is still deploy-ready.

**Defence soundbite.** *"The original 6 PRs were filtered for cognitive
load. After a methodological probe — measuring the per-PR token
overlap between baseline and KG reviews — three of those PRs turned
out to produce nearly-identical reviews under both modes; PR 12
specifically produced reviews with 100 % issue-level overlap. We
swapped those three PRs (12, 21, 3) for three from the same 40-PR
LLM-judge dataset that scored as the most-differentiable on a
direction-blind structural metric, holding the c1–c6 selection
criteria constant. The rubric-based LLM-judge headline is
unchanged."*

---

## Provenance and audit trail

| Artefact | Path |
|----------|------|
| **v3 study-data builder** (current — reads v2 evidence + reviews) | `human_eval_v3/scripts/build_study_data_v2.py` |
| **v3 study-data output** (the file the rater UI fetches) | `human_eval_v3/study_data.json` |
| **v3 rater UI** (current) | `human_eval_v3/index.html` |
| **v3 smoke-test (deploy gate)** | `human_eval_v3/scripts/smoke_test.py` |
| **v3 deep audit script** | `human_eval_v3/scripts/deep_audit.py` |
| **v3 decision log** (this file) | `human_eval_v3/docs/DECISION_LOG.md` |
| v2 study-data builder (reads v1 evidence + reviews) | `human_eval_v2/scripts/build_study_data_v2.py` |
| v2 PR-filter script | `human_eval_v2/scripts/analyze_pr_candidates.py` |
| v2 PR-filter output | `human_eval_v2/analysis/pr_candidates.{json,md}` |
| v2 PR-body fetcher | `human_eval_v2/scripts/fetch_pr_bodies.py` |
| v2 PR-body cache (recovered from GitHub) | `human_eval_v2/data/pr_body_overrides.json` |
| v2 deep audit script | `human_eval_v2/scripts/deep_audit.py` |
| v2 smoke-test (deploy gate) | `human_eval_v2/scripts/smoke_test.py` |
| v2 study-data output (preserved unchanged for audit) | `human_eval_v2/study_data.json` |
| v2 rater UI (preserved unchanged for audit) | `human_eval_v2/index.html` |
| v2 selection rationale | `human_eval_v2/docs/SELECTION_v2.md` |
| v2 analysis plan (pre-registration; carries over to v3 unchanged) | `human_eval_v2/docs/ANALYSIS_PLAN.md` |
| v2 deployment notes | `human_eval_v2/docs/DEPLOY.md` |
| v1 selection rationale | `results/HUMAN_STUDY_PR_SELECTION.md` |
| v1 study data | `human_eval/study_data.json` |
| v1 rater data | `human_eval/raters/*.json` |
| Power analysis | `results/POWER_ANALYSIS.md` |
| LLM-judge dataset rebuild (the source of v3 stimuli) | `dataset_v2/docs/STATUS.md` |
| LLM-judge v1↔v2 comparison | `results/V1_VS_V2_COMPARISON.md` |

---

### Decision 18 — Pivot study comparison to strict-baseline vs Joern-KG on new 6 PRs (2026-06-13)

**What changed.** The live study (`human_eval_v3/index.html`, version
`strict-bl-vs-joern-v1`) compares `baseline_strict` vs `joern` on PRs
{22, 24, 31, 38, 44, 47}. This differs from the Decision 17 spec in
three ways:

| | Decision 17 spec | Decision 18 (this) |
|---|---|---|
| PR set | {1, 14, 22, 24, 30, 42} | {22, 24, 31, 38, 44, 47} |
| Comparison | `bl_vs_kg` (normal prompt) | `bl_vs_joern` (strict prompt) |
| Baseline mode | `baseline` (normal prompt) | `baseline_strict` (9-criterion mandate) |

**Why.** The pre-registered tree-sitter KG result (d_z=+0.47, n=40,
p=0.006) is the cleanest single result and the natural headline to
validate. However, the Joern call-graph KG under the strict prompt
produces the largest measurable effect (d_z=+1.07 panel-controlled,
p<0.0001) and is the method actually used in the thesis contribution.
Validating the largest effect against human raters gives the study
maximum discriminability: at n=6 PRs the minimum detectable Kendall's τ
is ~0.70, so the study is only powered to detect strong agreement or
strong disagreement. An effect size of d_z=+1.07 is far more likely to
produce a detectable human preference signal than d_z=+0.47.

**Why the new PR set.** PRs {30, 42} from Decision 17 are not present
in the Joern strict scoring (the strict run covers 35 PRs excluding the
5 Go PRs {9, 27, 35, 36, 37} where Joern produces no call edges). PRs
{31, 38, 44, 47} replace them; selection used the same discriminability
criterion as Decision 17 (low baseline↔kg review overlap, balanced
across the W/T/L distribution of LLM-judge predicted outcomes:
2 predicted wins, 2 predicted ties, 2 predicted losses).

**What stays the same.**
- 25-criterion rubric, judge panel, and 40-PR LLM-judge dataset:
  untouched.
- 6-criterion human-rating subscale {F3*, F2*, T3, Q5, R1, C6}:
  unchanged.
- Session structure: welcome → consent → demographics → briefing →
  1 warmup → 6 real trials → feedback → completion. Unchanged.
- Primary analysis metric: Kendall's τ between human preference rank
  and LLM-judge KG-rel delta rank across the 6 PRs. The operational
  metric already moved to preference-correlation in
  `scripts/analyze_human_study_v4.py`; this decision ratifies that.
- Anti-goalpost-moving rules from `ANALYSIS_PLAN.md` §2.3: no dropping
  criteria or PRs after seeing rater data, no re-weighting.

**Alignment with thesis overview.** The misalignment between the
human study and the pre-registered plan was acknowledged in
`THESIS_OVERVIEW_FOR_JUDGE.md` lines 226–247 prior to this decision
being written. This entry converts that acknowledgement into the formal
decision-log record.

**Files updated by this decision.**
- `human_eval_v3/study_data.json` (rebuilt with new PR set and modes).
- `human_eval_v3/scripts/smoke_test.py` (updated expected values to
  match current PR set {22,24,31,38,44,47}, modes {baseline_strict,
  joern}, comparison id `bl_vs_joern`, STUDY_ID `human_eval_v4`).

**Verified:** `smoke_test.py` passes all checks (0 failures) after
this decision is applied.

---

### Decision 19 — Per-criterion relevance instrument + reading aids + overall preference (2026-06-21 … 2026-06-24)

**Trigger.** Supervisor meeting (2026-06-19, C. Adriano). Chris asked to (a)
focus raters on the *differences* between the two reviews, (b) ask, per
criterion, whether the difference is *relevant* (A / B / equivalent) rather than
one overall winner, (c) pre-compute helper layers (an LLM summary and counts of
concrete items) so the rater doesn't have to, and (d) keep the PRs that are
*very different*.

**Decision.** The rater UI (`human_eval_v3/index.html`) was changed from a single
5-point preference to a **per-criterion grid over the 6 criteria
{F3*, F2*, T3, Q5, R1, C6}**, plus reading aids:

1. **Per-criterion answer = `Review A / Both / Neither / Review B`.** Chris's
   original spec was `A / equivalent / B`; "equivalent" was split into **Both**
   (both reviews address it about equally) and **Neither** (neither addresses
   it) so the overloaded middle option no longer hides two very different
   states. Stored per criterion as `A|B|both|neither`.
2. **One overall holistic preference** (`A | equal | B`) under the grid — a
   single headline preference per PR, in addition to the per-criterion data.
3. **Question wording made comparative** — "Which review better …?" instead of
   "Does the review …?", to match the comparative answers.
4. **AI summary** (neutral, blinding-safe 2–3 bullets per review, hand-authored)
   + **concrete-item count strip** (Components/APIs, Files, Test targets, Edge
   cases, Reasoned claims) + **semantic difference highlighting** (curated
   genuinely-unique content per review; paraphrases of shared points stay
   unshaded). These are *display* aids only; the review text is unchanged.
5. **Warmup parity** — the practice screen now shows the same summary +
   highlighting + counts as the real trials (it previously showed only counts).

**Direction-blindness check.** Every aid is symmetric across the two blinded
reviews; the mode label is never shown. Splitting "equivalent" into Both/Neither
and adding an overall question add response options, not a directional bias.

**Backend.** `human_eval/apps_script_webhook.gs` persists the new schema to a
dedicated `responses_criteria` sheet (per-criterion + `overall` + `criteria_net`),
non-destructively alongside the older preference rows. New analyzer
`scripts/analyze_human_study_criteria.py` reads it.

**Files updated.** `human_eval_v3/index.html`,
`human_eval_v3/scripts/build_study_data_v2.py` (CRITERIA wording),
`human_eval_v3/study_data.json` (criteria text, review_summaries, review_counts,
review_unique), `human_eval/apps_script_webhook.gs` (+ bundle copy),
`scripts/analyze_human_study_criteria.py` (new), `thesis-context/CODE_INDEX.md`.

**Open item.** Re-paste + redeploy the Apps Script web app before raters submit.

---

### Decision 20 — Sample size, power, and the level at which to test human↔judge agreement (2026-06-24)

**Trigger.** "Scientifically, what is the correct number of PRs — is 6 fine, and
by what principle?" Plus the design question of whether to add a rag-vs-kg human
comparison.

**Findings (full note: `results/POWER_human_study_criteria.md`).**

1. **6 PRs is appropriate.** This is a within-subjects preference study + pilot
   convergent-validity check, not a proportion survey, so the ~385-PR
   margin-of-error figure does not bind. Power comes from **raters**; PR count is
   capped by rater fatigue (~3–5 min/PR).
2. **Target ~15–20 raters.** 15 raters → ~0.90 power (binomial sign test) to
   detect a clear overall preference (p≈0.70); 20 → ~0.96. Rater-level paired
   test: ~21 raters for d_z=0.65, ~15 for d_z=0.80.
3. **The 6 PRs span the whole-review outcome range** (judge Δtotal −1…+3, Δkgrel
   −2…+2; balanced wins/ties/losses) — good for a pilot correlation.
4. **Per-criterion human↔judge agreement is NOT viable on these PRs.** The
   binary rubric scores joern vs baseline as **tied on ~80 % of criterion cells**
   (F3* 0/6, F2* 1/6, T3 2/6, Q5 0/6, R1 0/6; C6 has no rubric id). This is a
   rubric-granularity limit — more PRs would not fix it.

**Decisions.**
- Keep **6 PRs**, recruit **~15–20 raters**.
- **Primary powered result** = the overall preference (joern vs baseline).
- **Convergent validity** is computed at the **whole-review (total / KG-relevant)
  level**, using the per-PR judge scores in
  `experiments/human_study_reviews/pr*_eval.json` (Spearman/Kendall), automated
  in the analyzer. Reported as **pilot-level** (n=6).
- **Per-criterion human data is reported as descriptive** — and framed as a
  *result*: humans can distinguish reviews the binary rubric scores as tied
  (the "rubric misses KG richness" point).
- **Do not add a rag-vs-kg human comparison.** `rag` exists only in the standard
  (grep/AST-kg) pipeline, not the strict/joern one; a clean joern-vs-rag would
  need a new (paid) generation run, and rag-vs-kg differences are subtle. Cover
  rag/hybrid via the existing 40-PR LLM-judge panel instead.

**Direction-blindness check.** All choices concern the analysis *level* and
*sample*, made on stimulus/instrument properties (judge tie-rate, fatigue,
pipeline availability) — none depend on which mode wins.

**Files created.** `results/POWER_human_study_criteria.md` (+ bundle copy);
convergent-validity computation added to `scripts/analyze_human_study_criteria.py`.

---

The `human_eval_v3/scripts/build_study_data_v2.py` script is
reproducible: from the same `data/luca_prs_v2/` and
`outputs/luca_prs_v2/` inputs it produces a byte-identical
`human_eval_v3/study_data.json`. Anyone can re-run it and verify.
