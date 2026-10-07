# Analysis plan — human study v4 (Python PRs)

Initial plan frozen 2026-07-06. The dated amendments below were informed by
excluded pilot/instrument-validation sessions and were all completed before
confirmatory-cohort recruitment.
Companion: `POWER_ANALYSIS.md` (power simulations), `analyze_responses.py`
(implements exactly this plan; tested on synthetic data).

## Design

- 6 PRs (requests ×2, flask ×2, click ×2), fully crossed: every rater rates
  all 6. One blind A/B comparison per PR: `baseline_strict` vs `kg`
  (A/B side randomized per rater, seeded by rater ID).
- Per task: 6 per-criterion choices (A / B / both / neither), one overall
  preference (A / equal / B), a free-text "why", difficulty (1–5).
- Target n = 18–20 complete raters (15 is a lower-bound recruitment
  checkpoint whose power is scenario-dependent).

## Data handling (before any statistics)

1. Keep only rows with `study_id == human_eval_v4_python_20260808` and
   `instrument_version == python-prs-study-v4-diff-default-r14`.
2. Exclude rater IDs matching `pilot*` / `smoke*` / `test*`. The researcher and
   anyone validating the instrument must use one of these prefixes. `test*` was
   added on 2026-08-19 after a full instrument check was run under the id
   `test`, which the first two patterns did not catch; the rule is widened
   rather than the row deleted so the exclusion stays reproducible from the
   sheet.
3. De-duplicate by (rater_id, pr_id, comparison), keeping the latest
   `completed_at` (the UI resends on edit).
4. Un-blind using the row's `mode_A`/`mode_B`.
5. Rater inclusion: only raters completing all 6 tasks enter confirmatory
   analyses, matching the fully crossed power simulation. Partial sessions
   are reported descriptively and excluded from inference.
6. Background responses (`role`, `exp_years`, `freq_review_pr`) are
   **descriptive only**. No subgroup, moderator, or covariate analysis is
   planned; at the target of 18-20 raters none would be interpretable, and
   permitting one after seeing the data would be a researcher degree of
   freedom. These fields appear in the participant-characteristics table and
   nowhere else, which is why `analyze_responses.py` does not read them.
7. Raters answering `freq_review_pr == never` are **retained** in the primary
   analysis; their count is reported separately in the characteristics table.
   Fixed in advance so the decision cannot depend on how they answered. The
   task asks which review is more useful to a PR author, which does not
   presuppose a reviewing habit, and at this sample size discarding raters
   costs more power than the heterogeneity they introduce.

## Scoring

For any choice, the KG-preference value is:
kg-side pick = 1, baseline-side pick = 0, both / neither / equal = 0.5.
A rater's score for an endpoint = mean over all 6 PRs. "Both" and "neither"
share the neutral directional score but are reported separately in raw-choice
descriptives because they have different substantive meanings.

## Endpoints

1. **Primary (confirmatory): F3\*** — "which review better names concrete
   components/APIs affected". Per-rater F3\* score vs 0.5, two-sided Wilcoxon
   signed-rank, alpha = .05. Effect size: matched-pairs rank-biserial r and
   the mean score with a 10,000-resample rater-level bootstrap 95% CI.
2. **Secondary (estimation only, no significance claim): overall usefulness**
   — same scoring; report mean + bootstrap CI. Pre-registered expectation
   (from power analysis): underpowered at n = 15–20; interpretation rests on
   the CI.
3. **Exploratory: remaining criteria** (F2\*, T3, Q5, R1, C6) — same test as
   primary, Holm-corrected across the 5 criteria.
4. **Descriptives:** per-PR breakdown, difficulty distribution (compare to
   v3's reported difficulty), time per task, GitHub-link clicks, optional
   highlight use, raw "both"/"neither" counts, realised A/B side balance, and
   "why" texts coded post hoc for whether repository evidence is cited.

## Decision rules (stated in advance)

- Primary p < .05 with mean > 0.5 → "raters perceive the KG reviews' better
  grounding of affected components" in this six-PR assisted-interface probe.
  This is mechanism-consistent with RQ2 but is not a direct validation of the
  canonical 40-PR LLM-judge ranking: the samples, KG implementation, and
  endpoint wording differ.
- Primary null → reported as a boundary result: the KG's mechanical
  difference (additional off-diff references) is not salient enough for human
  raters when neutral repository relationships are provided. No re-running with new stimuli
  to chase significance.
- Overall-usefulness CI overlapping 0.5 alongside a positive primary is the
  expected pattern and will be framed as: KG changes what a review grounds,
  not necessarily holistic perceived usefulness.

## Threats noted in advance

- The two systems produce recognisably different review content, so repeated
  exposure may let raters infer that the same latent strategy tends to name
  more off-diff files. A/B side randomisation prevents a fixed-side cue, but
  cannot hide content differences that constitute the treatment itself.
- Claim summaries and neutral repository-reference evidence reduce rater burden but are
  still presentation interventions. Semantic difference highlighting is
  available only on demand and starts off. The criterion-mapped count strip
  is not rendered. Conclusions are therefore about this assisted comparison
  interface, not unaided review reading.
- 6 PRs from 3 repos limits stimulus generalizability; framed as a
  perception probe, not an effectiveness estimate (that is RQ2's job).
- KG builder for these stimuli is the AST import resolver, not Joern
  (recorded in evidence metadata; same relation class).

## Amendment 2026-07-13 (before confirmatory-cohort data)

A pre-submission blinding audit found two surface tells that could let a
rater identify the arm (a prompt-scaffolding tail present inconsistently
across arms, and Evidence subsection labels present only in KG reviews).
`normalize_review_surfaces.py` removed both with uniform, surface-defined
rules; no reference content was added or removed. Downstream layers
(answer key, counts, unique markers, one summary bullet) were rebuilt on
the normalized texts. Pre-normalization originals are archived in
`reviews_prenorm_backup_2026-07-13/`. Endpoints, scoring, and decision
rules above are unchanged.

Additionally, three rater-comprehension changes (still before any real
rater data), motivated by the fact that raters know neither these repos
nor necessarily Python:

1. **Plain-language PR context box** (`pr_context` in the study data,
   rendered above the original PR description): one hand-written paragraph
   per PR explaining what the library is and what the change does. Written
   from the PR title/body/diff only — never from either review — so it is
   arm-neutral. Verified to contain no unique-content marker of either arm.
2. **Criteria descriptions reworded** into plain language (e.g. "design
   patterns"/"boundary conditions" removed). The 6 criterion ids and their
   meaning are unchanged; the analysis keys on ids only.
3. **Summary bullets reworded** for jargon (glosses added in parentheses,
   e.g. "`nl=False` (print without a line break)"). Same points, same
   identifiers, arm-symmetric edits; review texts untouched.

## Amendment 2026-08-01 (before confirmatory-cohort data) — study version v2

A pilot rater (2026-07-23) reported the session was too heavy to finish:
too much required reading, repetitive-feeling questions. Two groups of
changes, both before confirmatory-cohort data (the completed supervisor and
pilot-rater sessions are instrument-validation pilots and excluded):

1. **Review template de-boilerplate** (`reports/2026-08-01/
simplify_reviews_draft.py`, rules R1–R4): uniform, direction-blind
   removal of the template title, the "Scope:" line (restates the PR
   description shown above), and bold category labels in Problem/Impact
   bullets; plain-language section headers. No sentence reworded, added,
   or removed. Verified: file/line reference sets identical in all 12
   files; all 38 unique-content markers survive; word reduction
   symmetric (baseline −12.7%, kg −12.8%). Pre-simplification texts
   archived in `reviews_presimplify_backup_2026-08-01/`.
2. **UI burden cuts** (`pilot/index.html`): diff collapsed by default
   (optional reference); compact criterion labels ("short" field) with
   the full question as sub-line; the per-trial "why" rationale is now
   optional (empty notes still recorded; notes quality flags unchanged);
   the criteria instruction and file-reference briefing now state
   explicitly that naming more files/items is not automatically better
   (a pilot rater inferred a count-based heuristic from the old wording).

Endpoints, scoring, decision rules, and criterion ids are unchanged.
Study data `version` was bumped to `python-prs-pilot-v2`. These versions
used the same legacy study id and therefore must remain pilot-only; the final
instrument below uses a new study id and explicit instrument version.

## Amendment 2026-08-01b (before confirmatory-cohort data) — summary bullets

A rater-perspective re-audit of the deployed data found a residual surface
tell in the TL;DR summaries: every kg summary opened with "Names `src/...`
files" and every baseline summary with "Warns ...", so after one or two
trials a rater could identify a review from the first word of its summary
without reading the review. Two arm-symmetric fixes, deployed as site
v2.2:

1. **Bullet order is now rule-based**: `order_bullets()` in
   `assemble_study_draft.py` sorts each summary's bullets by the position
   in the review body where the bullet's backticked identifiers first
   appear (bullets with no identifier keep relative order at the end,
   matching where such points sit in the template). Deterministic and
   arm-blind.
2. **Opening verbs varied** (Lists / Identifies / Points to / Cautions /
   Notes / Warns / Names) so no verb is a per-arm signature. Wording-only
   edits; every bullet's content, identifiers, and claims are unchanged.

Verified after rebuild: all summary identifiers still present in the
corresponding review text, all 38 unique markers and all counted file
items intact. Review texts, endpoints, and scoring untouched.

## Note 2026-08-08 (before confirmatory-cohort data) — one-bullet repair

An agent walkthrough of the study found one ungrammatical bullet the
2026-08-01 label-stripping rule (R3) left behind in the PR 104 kg review:
"**Regression risk:** High for clients ..." became the fragment "High for
clients ...", because the stripped label carried the sentence's subject.
Repaired to "Regression risk is high for clients expecting the original
request in the history." — same meaning, no identifiers or claims added.
A scan of all 12 reviews confirmed this was the only such fragment (other
"High risk of regression ..." bullets are grammatical noun phrases).
No count item or unique marker referenced the bullet. Deployed as site
v2.3.

## Final amendment 2026-08-08 (before confirmatory-cohort data) — assisted, no counts

A final scientific audit separated aids that reduce reading burden from the
one aid that too directly exposed the primary outcome. The concrete-item
strip displayed Components/APIs and Files immediately beside F3\* ("names
the affected code"), effectively pre-counting the evidence raters were asked
to judge. It is therefore omitted.

The final instrument retains three usability aids:

1. the arm-neutral plain-language PR context and short review summaries;
2. repository-reference evidence labels, with explicit wording that they
   describe existence/relationship facts but do not validate review claims; and
3. curated semantic highlighting as an optional toggle that starts off on
   every practice and real trial.

The normalized review texts, randomized A/B sides, optional collapsed diff,
six criteria, overall preference, optional rationale, and difficulty remain
unchanged. This is explicitly an assisted-comparison instrument. The count
data remain in `study_data.json` for offline audit but are never rendered.
Whether a rater enables highlighting is recorded per trial and reported
descriptively.

To make versions unambiguous, final responses use
`study_id=human_eval_v4_python_20260808` and
`instrument_version=python-prs-study-v4-diff-default-r14`. The analyzer requires both,
so all earlier pilot instruments are excluded structurally as well as by
their `pilot*` rater ids. Its matched-pairs rank-biserial calculation was
also corrected to retain direction (the former two-sided implementation
always returned a non-negative magnitude); a positive/negative-direction
self-test was added.

Finally, a stale prose claim in the power report was reconciled with the
simulation table: at n=15, simulated F3\* power is 0.79 in the diluted
scenario and 0.99 in the pilot-like scenario (not 0.85). The target remains
18–20 complete raters; 15 is retained only as a lower-bound checkpoint.

## Final pre-launch audit 2026-08-08

A second independent content/data-contract audit found and corrected:

- one PR 104 baseline summary that had retained an "original request" claim
  found only in the paired KG review;
- one stale duplicate `sessions.py` badge, removed by rebuilding the answer
  key from current review text; `.md` references are now covered;
- two summary paraphrase drifts and one visible `metatvars` typo;
- backup ingestion (the analyzer now unwraps the UI outbox's
  `{queued_at, payload}` records);
- strict row validation for PR ids, comparison, mode pair, all criteria,
  overall choice, difficulty, and numeric telemetry;
- complete-case (6/6) confirmatory inclusion, realised side balance,
  separate raw both/neither counts, task-time/click/highlight descriptives,
  rationale export, and rejected-row audit reporting;
- version-safe resume detection and elapsed-time accumulation across revisits.

The current self-test includes wrapped UI backups, malformed-row rejection,
exclusions, unblinding, and positive/negative effect direction.

## Final evidence-semantics amendment 2026-08-08 (before confirmatory recruitment)

A source-level audit found that the former green `verified` badge conflated
file existence/module import with behavioral affectedness. This could cause
repo-unfamiliar raters to interpret researcher-provided presentation as
confirmation of a review's consequence claim. No PR or generated review was
replaced or regenerated: model inaccuracies remain outcomes to be rated.

The presentation layer now:

- labels summaries as summaries of review claims, not verified facts;
- confirms file existence separately from relationship strength;
- distinguishes changed file, direct use, indirect path, related data flow,
  module-only import, type-only reference, existing/unestablished link, and
  not found;
- exposes a compact source-audited basis on demand for every file; and
- states that relationship evidence does not prove the review's risk or
  consequence claim.

The classification rule is applied to references in both arms and is frozen
in `build_answer_key.py`. This amendment corrects the evidence aid without
conditioning PR selection or review generation on observed outcomes.

## Identity-field correction 2026-08-09 (before confirmatory recruitment)

The welcome field was restored to the original “Enter your name or rater ID”
wording at the researcher's request. Consent now states explicitly that the
provided name or rater ID is stored with responses and that email address and
IP address are not requested. The review stimuli, aids, endpoints, and
analysis are unchanged. This consent-visible revision uses instrument version
`python-prs-study-v4-neutral-reference-evidence-r2`.

## File-check simplification 2026-08-09 (before confirmatory recruitment)

Rater feedback showed that displaying direct/indirect/import/type-only
relationship categories and expandable source explanations was too technical.
The audited relationship metadata remains available offline, but the UI now
shows only three compact facts: **in this PR**, **exists**, or **not found**.
The briefing explicitly says these badges do not establish affectedness or
review correctness. This usability-only presentation uses instrument version
`python-prs-study-v4-simple-file-check-r3`.

A label-only refinement then made each badge self-explanatory
(`changed in this PR`, `exists in project`, `not found in project`) and added
an accessible `i` icon with the same neutral explanation. No stimulus,
endpoint, or recorded response field changed. Instrument version:
`python-prs-study-v4-simple-file-check-r4`.

The badge strip was **withdrawn** at r5 because it was an un-blinding cue.
The badges were rendered per arm from the same offline audit, but on the
frozen stimuli the resulting palettes separated the arms almost perfectly:
`baseline_strict` reviews cite only files the PR already touches, so their
strip was uniformly `changed in this PR`, whereas `kg` reviews cite
cross-file dependencies, so their strip was always mixed. A rater could
therefore sort the arms from the badge pattern alone, without reading a
review — and the direction of that cue is confounded with the outcome the
study measures. The `not found in project` badge additionally never fired on
any of the 12 stimuli, so the strip's only live contrast was the one that
leaked the condition.

The aid is retained but attached inline: each file path mentioned in a review
carries a dotted underline and a hover/focus tooltip. Every reference renders
with one identical neutral indicator — no status-dependent colour, badge, or
ordering. Coverage is complete: all 43 audited paths across the 12 stimuli are
annotated. No stimulus text, endpoint, or recorded response field changed.
Instrument version: `python-prs-study-v4-inline-file-tips-r5`.

**Correction.** As first written, this entry claimed the tooltip removed the
arm signature. That was wrong, and r5 was never deployed or used to collect
responses. The tooltip initially carried each file's audited `basis` sentence,
which moved the signature into hover text rather than eliminating it, and made
it worse: `basis` states whether a cited file is genuinely connected to the
change, which is a verdict on the review rather than a fact about the
repository. All 14 `baseline_strict` references are files the PR itself
changed, so every baseline tooltip was identical, while 7 of the 29 `kg`
references carry a "no ... connection was established" basis. A rater hovering
those would have been told that the kg review named code which is not
affected — precisely the judgement F3\* asks them to make unaided, and the
study's primary outcome. See the following section for the fix.

## Occupation categories 2026-08-17 (before confirmatory recruitment)

The background question "Current role" offered Student / Junior Developer /
Software Engineer / Senior Engineer / Other. Three defects made the resulting
variable close to uninterpretable. Its options mixed two dimensions, since
"Student" is an enrolment status while the rest form an industry ladder, so a
Master's student employed part-time — a large share of the HPI recruiting
pool — matched two options and had to choose arbitrarily. The ladder's middle
rung was also mislabelled: "Software Engineer" is the generic title that
contains juniors and seniors, not a level between them. And PhD students and
researchers, the other large share of the pool, matched nothing and would
have fallen into an "Other" option that recorded no detail.

The replacement asks for primary occupation on a single axis: student /
researcher / junior developer / mid-level developer / senior developer /
other, the last revealing an optional free-text field recorded as
`role_other`. The labels follow the Stack Overflow Developer Survey's job-type
question, which likewise lists `Student` and `Academic researcher` alongside
developer roles. The `researcher` option is labelled `PhD / Researcher` so that
doctoral students, who could otherwise reasonably read themselves into
`student`, are directed by the label itself.

The three developer rungs are named explicitly rather than collapsed into one
`developer` option, because a bare label leaves a respondent to guess how much
detail is wanted and the explicit ladder is what practitioners recognise. The
cost is that `role` and `exp_years` are no longer orthogonal: both carry
seniority. They are not interchangeable — `exp_years` counts years including
study and hobby programming, while the rung reflects the responsibility a
respondent currently holds — but they are correlated, so any split of the
sample uses `exp_years` alone and `role` is reported only as a frequency table.

Short labels were chosen over longer self-descriptive sentences so that
this question keeps the same compact control as the other two; a
stacked variant was tried first and made one descriptive item visually
dominate the whole screen. The "writes code at work but not primarily a
developer" case, a distinct option in the Stack Overflow instrument, is
absorbed by `other` plus its free text, which is adequate because the variable
is descriptive and the sample is small.

The motivation is reporting rather than modelling. Item 6 above still
applies, so no subgroup analysis is planned. The relevant comparable work
(Tufano et al., _Deep Learning-based Code Reviews_, arXiv:2411.11401)
deliberately excluded CS students without industrial experience, on the view
that industrial experience is essential in code-review studies. This
instrument takes the opposite position because its task is a preference
judgement between two reviews rather than the performance of a review, which
depends far less on professional expertise. That position is defensible only
if the sample composition is stated plainly, per the reporting guidance of
Baltes and Ralph (_Sampling in Software Engineering Research_, EMSE 2022),
and the previous categories could not state it. A related study drawing on a
comparable pool (arXiv:2607.24601) saw 26% of participants select "Other",
which is the failure this revision is meant to avoid.

This adds one recorded response field, `role_other`, and changes the value
vocabulary of `role`; no stimulus text or endpoint changed. No responses were
collected under r5, so no data is orphaned. Instrument version:
`python-prs-study-v4-occupation-categories-r6`.

**Hint line removed 2026-08-24.** The occupation question carried a sub-line
reading "Pick whichever takes more of your time. PhD students: choose
Researcher." It was removed as instructional clutter. Its second clause is
preserved in the option label, now `PhD / Researcher`. Its first clause is not:
a respondent who both studies and works full-time is again left to choose
between `student` and a developer rung without guidance. That is accepted
rather than overlooked — `role` is descriptive only, reported as a frequency
table and used in no split (see above), so a dual-status respondent landing in
either category costs nothing that the analysis depends on. `exp_years`, which
does carry the one pre-specified split, is unaffected because it asks a
question with no dual-status case.

**Correction 2026-08-24.** As first written, the two paragraphs above described
a four-option question (student / researcher / developer / other) and argued
that seniority was deliberately absent. That was accurate when r6 shipped, but
the three developer rungs were restored at the researcher's request shortly
afterwards and the entry was never updated, so the plan described a form no
participant would see. The paragraphs now describe the six options the
deployed instrument actually offers, and the orthogonality claim — which the
restoration falsified — has been replaced by the reason `exp_years` is the
variable used for any split. Found by reading `pilot/index.html` against this
document, not by a rater. No response has been collected under any version, so
no data is affected, and nothing in code reads `role`: `analyze_responses.py`
does not touch demographics at all and `_writeDemographics()` stores the value
as an opaque string. The instrument version is unchanged because the form
itself did not change; only this description did.

## File tooltips restricted to existence 2026-08-17

Shipped with r6, correcting the r5 defect recorded above. `_tipText()` in
`pilot/index.html` no longer reads the audit's `basis` or `relationship`
fields and emits only two strings: "This file is changed by this PR." and
"This file exists in the project." (a third, "This file was not found in the
project.", is reachable but fires on none of the current stimuli). Verified
across all 12 stimuli: 65 annotated references resolve to exactly those two
texts, with zero occurrences of audit prose. The `basis` and `relationship`
fields remain in `study_data.json` for offline analysis and are simply never
rendered.

A residual is accepted knowingly. Existence still correlates with arm, because
`baseline_strict` cites only files the PR changed (14/14) while `kg` cites
cross-file dependencies (17 of its 29 references exist but are unchanged), so
a rater who hovers many references could still infer a pattern. This was
retained over removing the aid entirely because the remaining statement is a
neutral fact about the repository that a rater could confirm by expanding the
diff, rather than a judgement about whether the review is right. The
distinction that matters is that no tooltip now evaluates a review's claim.
Analysis must therefore continue to treat the reading aids as a shared,
arm-independent affordance only in appearance, not in information content;
the un-blinding risk is reduced, not eliminated, and belongs in the threats
section of any write-up.

## Summary bullets brought to risk parity 2026-08-17

An audit of the 12 hand-authored summaries in `assemble_study_draft.py` found
them factually grounded — all 54 code identifiers appeared in the review each
described, and every summary carried exactly three bullets — but not neutral in
how they rendered risk. All 12 reviews flag breakage explicitly; the summaries
reported it as "could break" for `baseline_strict` in 5 of 6 PRs and as the
weaker "could be affected" for `kg` in 5 of 6. PR 101's `kg` summary dropped the
review's first two points (breakage and API-contract violation) altogether and
spent a bullet restating its own file list. Because the rubric asks whether a
review finds real problems and covers the important issues, a rater leaning on
the aid would have scored `baseline_strict` higher on those criteria for a
difference the summariser introduced rather than one present in the stimulus.

Five `kg` summaries were re-worded (PRs 101, 103, 104, 105, 106) to state
breakage at the strength the `kg` review itself uses, in the same plain register
as the baseline bullets — "could break" plus a concrete noun a non-expert can
picture (_other code_, _scripts_, _views_), avoiding "callers", "clients" and
"API contract". PR 102 needed no change. The `baseline_strict` summaries were
audited against the same standard and none were softened or truncated, so none
were touched. After the change "could break" appears in 5 of 6 summaries in both
arms, matching the reviews.

No file list was removed and no new file was named, so the treatment content is
unchanged: `kg` summaries still name source files no baseline summary names, and
"could be affected" still appears in 3 of 6 `kg` summaries where it describes a
dependency rather than a risk. That asymmetry is retained deliberately. The
governing distinction, as with the tooltips above, is that an asymmetry
mirroring the reviews is the effect under measurement, while one introduced by
the aid is measurement error. Only the latter was corrected. No responses were
collected under r6, so no data is orphaned. Instrument version:
`python-prs-study-v4-summary-risk-parity-r7`.

## Counterbalanced sides, stimulus and payload fixes 2026-08-17

Four defects found by an independent review of the r7 instrument, all confirmed
against the source before acting.

**Side assignment was not counterbalanced.** `buildOrder()` drew an independent
coin per PR, so over rater IDs only 31% received an even 3/3 split of which arm
appeared on the left and 22% received five or six of six on the same side.
Simulation over 20 000 rater IDs reproduced that distribution exactly. Side is
now assigned by shuffling a balanced array, which yields 3/3 for every rater;
the same simulation confirms it. Order remains seeded by rater ID, so resuming
on a fresh device still reproduces a session.

**A PR template comment was visible in one stimulus.** GitHub hides HTML
comments, but `renderPRBody()` escapes `<` and `>` before rendering, so the
contributor checklist embedded in PR 103's body printed as readable text
instructing the reader to add tests, update docs and add a changelog entry —
priming the T3 and Q5 criteria on one of six stimuli. `strip_html_comments()`
in `assemble_study_draft.py` now removes comments from every PR body, so the
rule is a property of the pipeline rather than a patch for the one case where
it was noticed. Only PR 103 was affected.

**`started_at` never reached the sheet.** It was held in localStorage and
dropped at submission, leaving no way to reconstruct session duration or detect
straight-lining from the responses tab. It is now sent per trial and written by
`human_eval/apps_script_webhook.gs`; `_appendByName()` reconciles the new column
into the existing sheet, but the webhook must be redeployed for it to appear as
a first-class column. Until then the value is recoverable from `raw_payload`.

**The tooltip comment justified a design choice by its effect on the outcome.**
The note in `pilot/index.html` argued that showing the audit's `basis` and
`relationship` fields "would hand the rater a negative judgement of the kg arm
on F3\*, which is the study's primary outcome." The decision is right but that
reasoning is not defensible: it appeals to which arm the information would harm.
The comment now gives the methodological reason — existence is a repository fact
a rater can verify independently, whereas `basis` and `relationship` are this
project's adjudication of whether a review's claim holds, which is the judgement
the rater is being asked to make. Behaviour is unchanged.

Two further points from the same review are accepted but not yet actioned, and
are recorded here so they are not lost: `time_spent_ms` is raw wall clock with
no `visibilitychange` handling, so idle time inflates it; and the consent text
does not name Google as the processor or state a retention period and withdrawal
route. A third — that existence tooltips still separate the arms in 6 of 6 PRs —
is not new; it is the residual accepted and reasoned about in the section above.

No responses were collected under r7, so no data is orphaned. Instrument
version: `python-prs-study-v4-counterbalanced-r8`.

## Consent and disclosure corrected 2026-08-17

A read of the consent card against what the instrument actually transmits found
it accurate but materially incomplete, in two ways.

**Undisclosed collection.** The card listed identifier, background, preference
judgements, per-comparison time and optional feedback. The payload also carries
`github_clicks`, `highlight_used`, `difficulty`, `started_at`/`completed_at` and
`role_other`. The first two are behavioural telemetry rather than answers the
participant knowingly gives, and `analyze_responses.py` uses both for rater
quality flags, so they are not incidental. All are now itemised, with the
interaction measures named explicitly as such.

**Undisclosed processing.** The card said only that responses are "used solely
for academic research". It did not say they are transmitted to a Google Sheet
via an Apps Script web app deployed with access set to "Anyone", that Google is
therefore a processor, or that data may rest outside the EEA. Nor did it give a
legal basis, a retention period, a route to erasure after submission, or the
right to complain to a supervisory authority — five of the Art. 13 information
duties. All are now stated. Retention is set to deletion no later than
31 December 2027; confirm this against HPI's own data-protection guidance, which
governs, before recruiting.

Collecting a name remains lawful under consent and was not the defect. Under
data minimisation the identifier need only be stable enough to support resume
and completion tracking, so the field and its placeholder now say a nickname is
acceptable. Note that pseudonymisation does not remove the data from GDPR scope;
the disclosures above are required either way.

**A related data-path bug was fixed at the same time.** `role_other`, the
free-text occupation added at r6, was never written by `_writeDemographics()` in
`human_eval/apps_script_webhook.gs`, whose column list was fixed at `role`,
`exp_years`, `freq_review_pr`. Any participant selecting "Other" had their text
dropped from the demographics tab, surviving only in `raw_log`. The column is
now written, as is the `started_at` added at r8. Both require the webhook to be
redeployed before they appear; `_appendByName()` reconciles new columns into the
existing sheet, so no manual sheet edit is needed.

No stimulus, criterion, or recorded response field changed, and no responses
were collected under r8. Instrument version:
`python-prs-study-v4-consent-disclosure-r9`.

## Pre-registered: usefulness-vs-compliance checks and a time floor 2026-08-17

Added before any confirmatory response was collected (n = 0 at the time of
writing; the live endpoint was still serving r4 and no payload had been
accepted). Both additions answer challenges raised in review rather than
anything observed in data.

### Why these are needed

The primary endpoint F3\* asks which review better names the components a change
affects, and the `kg` arm names more files by construction. Counting distinct
file paths per review against the answer key:

| PR  | baseline |  kg | delta | of the kg files, exist but are unchanged |
| --- | -------: | --: | ----: | ---------------------------------------: |
| 101 |        2 |   4 |    +2 |                                        2 |
| 102 |        3 |   5 |    +2 |                                        3 |
| 103 |        2 |   5 |    +3 |                                        3 |
| 104 |        2 |   4 |    +2 |                                        2 |
| 105 |        2 |   4 |    +2 |                                        2 |
| 106 |        3 |   7 |    +4 |                                        5 |

The delta is positive in 6 of 6 PRs. A reviewer can therefore separate the arms
on file count alone, and the briefing tells raters that naming affected
components is what F3* rewards. A positive F3* result is consequently open to
the reading that raters complied with the briefing's definition rather than
judged usefulness. The checks below are pre-registered to address that.

### C1. Does preference track the size of the file-count gap? (weak by design)

Spearman's rho between each PR's `kg`-preference rate on F3\* and that PR's
file-count delta, across the 6 PRs. **This test has very little leverage and is
reported as descriptive only**: the predictor takes three values (+2 on four
PRs, +3 on one, +4 on one), and with n = 6 significance would require rho of
roughly 0.83. It is pre-registered so the number is published whichever way it
falls, not because it can settle the question. No correction is applied and no
inference is drawn from it alone.

### C2. Does preference survive among raters who verified the claims? (primary)

This is the better-powered version of the same question and carries the
argument. `github_clicks` and `highlight_used` are recorded per trial, so raters
can be split by whether they checked anything against the repository. Two
pre-specified contrasts, each over raters rather than PRs:

- **Verifier contrast.** Compare the per-rater F3\* `kg`-preference score between
  raters with at least one GitHub click across their six trials and raters with
  none, by Mann-Whitney U with a rank-biserial effect size and a bootstrap CI.
- **Aid-use contrast.** The same comparison, splitting on whether the rater ever
  switched on highlighting.

Interpretation is fixed in advance. If the `kg` preference holds or strengthens
among raters who verified, that is evidence the extra references were found
useful on inspection. If it is carried by raters who never verified, the
compliance reading gains support and must be reported as the more likely
explanation. Both groups are expected to be small, so these are reported with
CIs and no significance claim.

### C3. Stated reasons

The free-text `why` field is coded by a single rater against three
non-exclusive labels — mentions naming files or modules; mentions a risk,
breakage or test gap; mentions neither — and the distribution is reported per
arm. Pre-registering the scheme prevents it being built after the direction of
the result is known. Coding is descriptive; no test is run on it.

### C4. Time floor

`time_spent_ms` is raw wall clock with no `visibilitychange` handling, so idle
and tab-away time inflate it. It is therefore trustworthy as a lower bound and
unreliable as an upper one, and only the lower bound is used.

Each trial presents two reviews of roughly 215-290 words each, plus summaries
and the PR context. Reading both once at a brisk 250 wpm takes about two
minutes; answering six criteria and an overall preference after reading only the
summaries could not plausibly take less than about 45 seconds.

- Trials under 45 s are flagged as implausibly fast.
- A rater whose **median** trial time is under 60 s is flagged.
- **No rater is excluded from the primary analysis on this basis.** The primary
  endpoint is computed over all complete raters, as already specified above.
- A pre-specified sensitivity analysis repeats the primary endpoint excluding
  flagged raters. Both results are reported. If they diverge, both are reported
  in full and the divergence is discussed rather than resolved in favour of
  either.

Exclusion is kept out of the primary because n is small, power at n = 18 is
0.87 under the planned scenario, and time-on-task may correlate with the outcome
— dropping fast raters after seeing their answers would be exactly the
degree of freedom this plan exists to remove.

## Consent: supervision named, storage description simplified 2026-08-18

Two changes to the consent card in `pilot/index.html`, both before any
confirmatory response was collected.

**The research team is now named.** The r9 card gave only the student's contact
address, which leaves a participant with no independent party to approach — a
weakness in any student-run study and a practical problem for the erasure and
complaint rights the same card grants. The card now names the supervision:
Dr. Christian Medeiros Adriano and Prof. Dr. Holger Giese, System Analysis and
Modeling group, Hasso Plattner Institute, with the supervisor reachable at his
published HPI address. Participants are told they may use either contact.

**The storage paragraph was shortened to what a participant can act on.** It
previously read "sent to a Google Sheet belonging to the researcher, via Google
Apps Script", and then named Google as processor with a possible transfer
outside the EEA. It now states that submissions travel over an encrypted
connection to a cloud storage service, that access is limited to the named
research team, and that a copy is held in the browser's local storage which
clearing browser data removes.

This is a deliberate trade and is recorded as such. Naming the processor and
the possibility of a third-country transfer are Art. 13(1)(e) and 13(1)(f)
information duties, and dropping them narrows the disclosure. The paragraph
retains the substance a participant needs — that the data leaves their machine,
travels encrypted, is held by a third-party service, and is reachable only by
the named team — and the erasure, withdrawal and complaint routes are stated in
full in the following paragraph. **Confirm the wording with the supervisor and
against HPI's data-protection guidance before recruiting**; if the processor
and transfer must be named, the fuller sentence is preserved in the deployment
repository at commit `7dcb996`.

No stimulus, criterion, or recorded response field changed. Instrument version:
`python-prs-study-v4-supervision-contact-r10`. The storage paragraph was
shortened a second time on the same day, a few minutes after r10 first went
live and before the URL had been shared with anyone; the version was not bumped
again because no response has ever been submitted under r10, and this entry
describes the wording as it now stands.

## Highlighting aid made discoverable, default unchanged 2026-08-18

The semantic-difference highlighter was presented as a small underlined text
link, placed **below** the review pair and styled in the muted secondary colour,
so a rater met the aid only after they had finished reading the thing it was
meant to help them read. It is now a labelled pill button sitting **above** the
pair, reading "Highlight what differs", with one line of explanation beside it;
the colour key is shown only once highlighting is on, since it describes shading
that is otherwise not on screen. The briefing names the button so raters know it
exists before the first trial.

**The default remains off, deliberately.** Turning it on by default was
considered and rejected. The highlighter shades blocks carrying keys unique to
one review, and the two arms do not light up equally — across the six PRs it
shades 13 baseline blocks against 28 `kg` blocks, with `kg` ahead on every PR
(4/1, 4/4, 5/3, 3/1, 4/2, 8/2 for `kg`/baseline on PRs 101–106). Enabling it for
everyone would put that salience difference on every trial, on a primary
endpoint (F3*) that is already exposed to the reading that raters follow the
briefing's definition rather than judge usefulness. It would also collapse
pre-registered contrast C2, which splits raters by whether they ever switched
the aid on. Keeping the default off preserves both the contrast and the
rater's choice; only its discoverability changed.

`highlight_used` is still recorded per trial and still resets to off at the
start of every trial, so the recorded variable means the same thing it did
before this change. No stimulus, criterion, or recorded response field changed.
Instrument version: `python-prs-study-v4-highlight-affordance-r11`.

**Review panes were also enlarged, under the same version.** The pane height was
capped at 600px while the rendered reviews measure 639–957px (measured for all
twelve reviews at column widths corresponding to 1280px, 1440px and 1920px
screens), so every trial opened with two independent inner scrollbars and a
rater had to scroll each column separately to read either review in full. The
cap is now 1000px, at which no review scrolls internally on any of those widths:
the page scrolls as one unit and the two columns stay vertically aligned, which
is what a side-by-side comparison needs. This is a layout change with no effect
on content, wording, or what is recorded, and it was made minutes after r11 was
deployed and before the URL was shared, so the version was not bumped again; no
response has been submitted under r11.

**The progress bar was also repaired, under the same version.** `.pfill`, the
element whose width `updProg()` sets on every trial, is a `<span>` and carried no
`display` rule, so it was laid out as an inline box and inline boxes ignore
`width` and `height`. Its rendered size was 0 × 0 throughout, and the bar showed
an empty track from the first trial to the last while the "n / 6" counter beside
it advanced normally. With `display:block` the fill steps 30, 60, 90, 120, 150,
180px across the six trials. This is presentation only and touches nothing that
is recorded.

**Submission receipts replaced the backup-download panel, under the same
version.** Every POST used `mode:"no-cors"`, which returns an opaque response,
so the page could not tell a successful write from a silent failure. The
completion screen handled this by telling the rater it "cannot independently
confirm server receipt" and asking them to download a JSON backup and hold it —
which put the burden of the instrument's own uncertainty on the participant.

The request is now CORS-simple (`Content-Type: text/plain`, no custom headers,
so no preflight) and the Apps Script reply is readable cross-origin; verified
against the live endpoint, which returned
`{"ok":true,"version":"v3-2026-08-17","wrote":{"raw_log":1}}`. The webhook
itself needed no change: it reads `e.postData.contents` regardless of declared
content type and already replied with `{ok, version, wrote}`.

Each queued payload now carries an id and an `acked` flag, set only when the
endpoint confirms the write. The completion screen resends whatever is
unconfirmed and then reports the truth: confirmed receipt, or a warning with a
retry button and the JSON download as a fallback. The download therefore still
exists as a recovery path, but appears only when it is actually needed rather
than being presented to every rater as a routine precaution. Retries are now
driven by knowledge of failure instead of firing blind, which should reduce
rather than increase duplicate rows; deduplication by
(`rater_id`, `pr_id`, `comparison`) keeping the latest `completed_at` is
unchanged and still required. Payloads queued before this change carry no
`acked` flag and are treated as unconfirmed, which is the safe reading.

All four paths were exercised in-browser against the live endpoint: a confirmed
send marks the queue acked; the completion screen shows the confirmed state;
a simulated network failure produces the warning state with one payload still
pending; and a retry after recovery clears it and returns to the confirmed
state. This changes what the rater is told about delivery, not what is
delivered — no stimulus, criterion, or recorded field changed.

## Sheet write path corrupted demographics 2026-08-19

Found by inspecting a full end-to-end pilot run (rater id `test`, six
comparisons, r11) exported from the "Human Eval" spreadsheet, not by reading
code. The run was otherwise clean, which is what made the one bad field
visible.

`_appendByName()` wrote rows with `appendRow()`, which passes every value
through the same parser Sheets applies to typed input. The UI sent
`"exp_years": "3-5"`; the sheet stored the date 2026-03-05 (serial 46086). The
`raw_log` copy of the same POST holds the correct string, so the loss happened
on write, not in transit. Three of the five experience buckets — `1-3`, `3-5`,
`5-10` — corrupt this way; `<1` and `10+` survive. Left unfixed, the experience
variable would have been unusable for most raters, and the corruption is silent:
the cell holds a plausible-looking value rather than an error.

The same parser makes free text unsafe. A `why` response beginning with `=`,
`+` or `-` would have been stored as a formula, not as the rater's words.

v4-2026-08-19 preformats each string cell as plain text (`@`) and writes with
`setValues()`; numeric fields keep `General` and stay numeric. Only pilot rows
were affected and no confirmatory data was lost.

**v4 fixed half of it, which a verification probe caught.** Deployed against a
probe carrying `exp_years: "3-5"` and a `why` of `"=1+1 formula probe, and a 3-5
range"`, the demographics value stored correctly as text, but the `why` cell
stored `#ERROR!`: `setValues()` treats a string beginning with `=` as a formula
regardless of the cell's number format, so the plain-text format never applied
to it. The verbatim text survived in `raw_log`, which is the design intent of
that tab, but `responses_criteria` is what the analyzer reads.

v5-2026-08-19 writes any cell whose value starts with `=`, `+`, `-`, `@` or `'`
as rich text, which sets characters without parsing them. `-` and `'` are
included because both are realistic openings for free text ("- Review A named
the file"). v5 also removes `spreadsheet_id` and `spreadsheet_name` from the
public `?selftest=1` response. The lesson recorded here is that a schema or
write-path change is not verified until a probe has been written and read back
out of the sheet.

**v5 was deployed and verified against four probes** covering a `why` beginning
with `-`, with `=`, with `'`, and with ordinary text, each paired with a
different `exp_years` bucket. Nine of the ten assertions pass: all four
`exp_years` values (`5-10`, `1-3`, `3-5`, `<1`) store as text, `role_other`
stores, the `-` and `=` openings survive verbatim, and the numeric columns
(`pr_id`, `difficulty`, `time_spent_ms`, `github_clicks`, `criteria_net`) stay
numeric rather than being flattened to text.

**One accepted residual: a leading straight apostrophe is still consumed.**
`'quoted' opening ...` was stored as `quoted' opening ...`, so Sheets applies
its text-marker convention even to rich-text writes. This costs one character
and only when a rater's free text opens with `'` — rare in English prose, and
typographic apostrophes (`'`) are unaffected because they are a different
codepoint. It is not fixed because the obvious remedy, doubling the apostrophe,
corrupts in the opposite direction if the convention ever changes. `raw_log`
holds the verbatim payload for every POST, so any affected `why` is recoverable
from there; the free-text coding in C3 should be done against `raw_log` if a
response is found to begin with an apostrophe.

The same export confirmed several things work: all six comparisons arrived with
every column populated including `started_at`, `github_clicks` and
`highlight_used`; the r8 counterbalancing produced exactly three trials with
`kg` on side A and three with `baseline_strict` on side A; and the free-text
feedback POST landed in its own tab.

## A stale cached build wrote to the superseded endpoint 2026-08-19

A full six-comparison run (rater id `qwfqw`) completed at 13:53Z stored
`exp_years` as the date 2026-01-03 (serial 46025), the corruption v5 had
already fixed. The run cannot have reached v5: v5 was deployed on the same URL
at 13:42Z, eleven minutes earlier, and four probes written through the same
`_writeDemographics` path minutes before stored `5-10`, `1-3`, `3-5` and `<1`
correctly. The POST therefore went to the superseded deployment, which is still
reachable and still runs the old write path — the browser was holding an
`index.html` that carried the previous `SHEET_URL`. GitHub Pages serves the
page with `cache-control: max-age=600`, and a tab left open keeps running
whatever it loaded, indefinitely.

Two properties were missing and are now added:

1. **Nothing in a payload said which build produced it.** The endpoint change
   did not alter `instrument_version`, correctly — it changed plumbing, not
   what a rater saw — so no recorded field could distinguish the two. Payloads
   now carry `build_id`. No sheet schema change is needed for this to be
   useful: `raw_log` stores every payload verbatim, so the field is queryable
   immediately, and it can be promoted to a column at the next webhook
   redeploy.
2. **A stale page could not notice it was stale.** On load the page now fetches
   its own URL with `cache: "no-store"`, compares the served `BUILD_ID` against
   the one it is running, and if they differ reloads once through a
   cache-busting query. A `sessionStorage` guard makes a reload loop
   impossible, and a failed check is ignored so an offline rater is never
   blocked.

This closes the reload path. It cannot rescue a tab that was opened before a
deploy and never reloaded, so any change to the data path during recruitment
should still be followed by checking `build_id` in `raw_log` before trusting
the rows that arrive around it. `qwfqw` is a pilot row under the `test`-style
exclusions in spirit but not in name; it is excluded by the rule in Data
handling only if the id is treated as a pilot, so the row should be deleted
from the sheet rather than relied on.

## Narrow screens are turned away 2026-08-19

The instrument was measured at phone viewports before recruitment. The
responsive CSS holds: at 390x844, 360x740 and 414x896 there is no horizontal
scrolling, nothing spills past the viewport, and the criteria rows stack
cleanly. Nothing is broken. What changes is the task.

Below 900px the review pair collapses to one column, so Review B sits roughly
three screens below Review A and a single trial costs about 6.2 screens of
scrolling at 390px and 7.2 at 360px, against roughly 2 on a laptop. The two
reviews can then never be seen together. That matters specifically here: F3*,
the primary endpoint, asks which review better names the components a change
affects, which is a judgement about the relative content of two texts. A rater
who can only hold one at a time is doing a recall task, not a comparison, and
would plausibly lean harder on the plain-language summary, spend less time, and
fall back on "about the same". With a target of 18-20 raters, that subgroup
would be both small and systematically different, and device type would be
confounded with it.

Phones are therefore excluded rather than silently given a different task. A
full-screen notice appears below `MIN_WIDTH = 900` asking the rater to use a
laptop or widen the window, and explaining why. Three properties matter:

1. **The threshold and the layout agree.** The grid breakpoint was moved from
   `max-width:900px` to `max-width:899px` so that at exactly `MIN_WIDTH` the
   pair is still two columns. Verified: the gate is shown at 390px and at 768px
   (tablet portrait) and hidden at 900px, where the columns measure 415.5px
   each.
2. **The gate is not latched.** It is re-evaluated on `resize` and
   `orientationchange`, so widening a window or turning a tablet to landscape
   lifts it, and no state is discarded while it is up — a desktop rater who
   narrows their window mid-study sees the notice and resumes on widening.
3. **Width is recorded regardless.** Every payload now carries `viewport`
   (`innerWidth x innerHeight` at submission), so a rater working in a narrow
   window just above the threshold is visible in analysis instead of being
   assumed away. As with `build_id`, `raw_log` stores payloads verbatim, so the
   field is queryable without a webhook redeploy.

Exclusion is on eligibility, not on responses: anyone who submits sees exactly
the instrument r11 raters saw. The version is bumped to
`python-prs-study-v4-min-width-gate-r12` anyway, so that the recruited
population is identifiable from the recorded version alone, consistent with
earlier bumps for changes in what a rater experiences. No stimulus, criterion,
response field, or analysis decision changed.

## Returning to the study warned falsely and asked for the name again 2026-08-19

A pilot rater closed the study and reopened it, and was met with a browser
dialog reading "This rater ID appears active in another tab. Continue anyway?"
with no other tab open. Two separate defects.

**The concurrency check could not detect concurrency.** It wrote a timestamp to
`heval4_lock_<id>` on Start, refreshed it every 60s, and warned if the stored
value was under five minutes old. Nothing cleared it on unload, and a timestamp
cannot distinguish a live tab from a closed one, so any return within five
minutes warned — the ordinary case, not the exceptional one. It is now a Web
Lock, which the browser holds only while the holding document is alive and
releases on close or crash, so a refusal means a second tab genuinely holds it.
A same-document guard (`lockHeldFor`) was added after testing showed that
pressing Start twice in one tab made the tab collide with itself. The
`confirm()` dialog is replaced by an inline notice; a second click continues
anyway. Where the API is absent the check is skipped entirely, on the grounds
that a false alarm which teaches raters to dismiss warnings costs more than the
concurrent-tab case it guards against. Stale `heval4_lock_*` values from earlier
builds are deleted on Start.

**Resuming required retyping the exact name.** Progress is keyed by rater id, so
a returning rater who typed a variant of their name silently started an empty
session instead of resuming, and the saved data became unreachable without
knowing the original string. The last id used on this device is now restored
into the field, with the note "Welcome back, <id> — N of 6 comparisons done …
or type a different name if this isn't you" so a second person on the same
machine is not captured by it. Consent and warm-up completion are now recorded
(`consented`, `warmupSeen`), so a resumed session no longer re-asks for consent
that was already given, and — the other side of the same coin — a rater who
returns before ever seeing the warm-up still gets it, which the previous
`hasExistingProgress` test got wrong.

Verified in a headless browser driving the real `start()` path: reopening with a
prior session and a stale old-style lock present produces no warning and lands
on the briefing; a second document opened while the first is alive is warned and
proceeds on a second click; once the others are closed a new document is not
warned; and pressing Start twice in one tab does not warn.

Instrument version `python-prs-study-v4-resume-r13`. Note for the recruitment
period: `load()` requires the saved `instrumentVersion` to equal the running
one, so bumping the version discards any session a rater has in progress. This
bump is free because recruitment has not started. Once it has, plumbing changes
should ride on `build_id` alone.

## Advertised duration corrected to 25-35 minutes 2026-08-24

The welcome screen and the briefing both advertised 15-25 minutes. That figure
predates the current stimulus set and does not survive arithmetic. A trial
presents two reviews of roughly 215-290 words each, plus the plain-language
description and both summaries; reading that once at a brisk 250 wpm is close to
three minutes, and seven judgements (six criteria plus overall preference) add
about a minute even when the rater does not reopen the diff. At three and a half
to four and a half minutes per trial, six trials alone consume 21-27 minutes,
before consent, demographics, the warm-up, and the closing feedback box. The
advertised range now reads 25-35 minutes, and both places also state that
progress is saved so a rater can stop and resume.

Understating the commitment is a data-quality problem, not only a courtesy one:
a rater who budgeted fifteen minutes and finds themselves at trial four is the
rater most likely to skim the second half, which is exactly the behaviour the
C4 time floor exists to detect. Advertising the real number costs some
recruitment yield and buys attention on the trials that are completed.

Copy only. No stimulus, criterion, response field, or analysis decision changed,
so the instrument version stays `python-prs-study-v4-resume-r13` and the change
rides on `build_id = "2026-08-24-time-estimate"`.

## The diff is shown by default 2026-08-24 (before recruitment)

From 2026-08-01 the diff was collapsed on every trial, on pilot feedback that
the required reading was too heavy. The cost of that default is that F3\* — the
primary endpoint, "which review better names concrete components/APIs
affected" — could be answered without ever seeing the code that changed, which
leaves the counting heuristic (prefer whichever review lists more paths) as the
path of least effort. The diff now opens by default and is re-opened at the
start of each trial, so collapsing it on one PR does not silently carry over.
It remains collapsible, and the diffs are small: 35, 96, 80, 35, 169 and 85
lines including context, median 85.

**This default is not neutral between the arms, and the briefing is worded to
offset that.** The diff contains only the files the PR changed. All 14 file
references in the baseline reviews are to changed files; of the 29 in the kg
reviews, 12 are changed and 17 point elsewhere in the project (3 `direct`, 4
`indirect`, 1 `related`, 2 `module_only`, 2 `type_only`, 5 `exists`). A rater
who reads "affected" as "appears in the diff" would therefore mark the baseline
arm correct on every reference and the kg arm correct on 12 of 29, penalising
the treatment arm precisely where its mechanism operates. Both the briefing and
the diff header now state that the diff contains only the changed files, that a
review may mention code elsewhere that the change could affect, and that the
diff can neither confirm nor refute such a mention — pointing raters at the
GitHub link if they want to check one. The wording asserts nothing about
correctness in either direction, and the existing "naming more files is not
automatically better" line is unchanged, so the pair of cautions remains
symmetric.

The residual risk runs against the hypothesis rather than for it, which is the
safer direction to be wrong in, and C2's verifier contrast is unaffected because
it splits on GitHub clicks and highlighting rather than on diff exposure. Note
that diff expansion is still not recorded, so the analysis cannot report how
long raters spent in the diff — only that it was in front of them.

The rater's experience changes, so the version is bumped to
`python-prs-study-v4-diff-default-r14`, consistent with r11 and r12. Free now
because recruitment has not started; `load()` requires the saved version to
match, so any in-progress session would otherwise be discarded. No stimulus,
criterion, response field, or analysis decision changed.

## Copy sweep of the rater-facing text 2026-08-24

A read-through of every screen removed language that asked raters for a favour
or padded the instructions. The `why` box was labelled "optional — even one
short sentence helps us a lot", which solicits an answer to a field the plan
treats as descriptive, and the briefing repeated the request a second time in
the tips list; both are gone and the label is now just "(optional)". Also
removed: "Three quick questions before we start", "Got it — start with a
practice round", "I'm ready — start the real study", "to unlock the button",
"we'd love to hear your thoughts", and "Instead of one overall 'who wins'",
which misdescribed an instrument that does ask for an overall judgement.

Two substantive corrections came out of the same pass. The tips list told
raters that "no preference" was a valid answer, a label the form does not show;
it now names the options that exist (Both, Neither, About the same), so the
instruction and the radio buttons finally agree. And the consent screen still
described the diff as "an optional reference", contradicting r14 one screen
before the rater sees it open. The practice-round and real `why` prompts, which
had drifted apart in wording, now ask the same question.

Copy only, and the changes either shorten instructions or correct them toward
what the interface does, so no version bump: `build_id =
"2026-08-24-copy-sweep"`. Nothing recorded changed.

In the same pass the GitHub link was promoted from a run of link text in the
metadata row to a bordered button at the right of the PR header
(`build_id = "2026-08-24-gh-button"`), for the reason given above: with the
diff limited to changed files, it is the only route to the rest of the project.
This one is not purely cosmetic for the analysis. C2 splits raters on whether
they ever clicked that link, so a more visible control should raise the click
rate, and the contrast is best powered near an even split. If almost every
rater clicks, the non-verifier group shrinks and C2 loses resolution — a cost
accepted deliberately, because a verification route nobody notices produces a
clean split of a variable nobody acted on. The realised split is reported
either way.

## Narrow-screen gate now names the right cause 2026-08-24

The gate at `MIN_WIDTH = 900` is unchanged and still decides who may take the
study; only the explanation was wrong. It read "Please open this on a larger
screen", which is the correct instruction for a phone and a false one for the
other group that reaches it: a laptop whose window is not maximised, or a
desktop at 125–150% browser zoom, where a 1280px screen reports an
`innerWidth` of 1024 or 853 and trips a gate the rater cannot diagnose. A rater
told to move to a laptop while sitting at one is likely to leave.

The two cases are now separated by input type — `(pointer: coarse)` and
`(hover: none)`, with a phone-sized physical screen as a fallback — rather than
by any size threshold, because no threshold distinguishes them: a 1280x800
laptop screen is smaller than an iPad Pro's. Touch-primary devices keep the
original message. Everything else gets "Your browser window is a little too
narrow", the suggestion to widen it or zoom out, and a live readout of the
current width against the 900px it needs, so the fix is self-evident and lifts
the moment there is room.

Verified on the deployed build at 1440px (no gate), 850px with a fine pointer
(narrow-window message), and an emulated 390px touch device (device message).
Copy and branching only, no version bump: `build_id = "2026-08-24-gate-message"`.
Nothing recorded changed, and the width at which the study runs is the same as
in r12.

## A switch to force saved sessions to start over 2026-08-24

Two kinds of release already behave differently on purpose. A bump of
`STUDY.version` invalidates saved progress on its own, because `load()` accepts
a stored session only when its `instrumentVersion` matches, so a rater resumes
into a fresh, correctly ordered session rather than into stimuli that no longer
exist. A copy-only build, carried on `build_id` alone, deliberately keeps
progress: the alternative is discarding a half-finished session over a typo.

What was missing is the case in between — a change that alters what an answer
means without changing the stimulus set, where the honest thing is to have
everyone start over. `DATA_EPOCH` is that switch: a hand-edited constant,
checked at startup against the value last stored on the device, that deletes
every `heval_<STUDY_ID>_*` progress record and the remembered rater id when it
differs. It is not derived from `BUILD_ID`, precisely so that shipping a copy
fix cannot trigger it by accident.

The wipe is confined to progress. Outbox entries survive it, since an entry the
server has not yet acknowledged is the only copy of that submission in
existence, and the theme and device token are not study data. Comparisons
already acknowledged are safe server-side; a rater who redoes one produces a
second row for the same rater and PR, which the dedupe in step 3 of the
analysis resolves in favour of the later timestamp, so a mid-study bump costs
rater time rather than data.

Verified on the deployed build: introducing the constant left three existing
sessions and their outboxes untouched and simply recorded the epoch, while a
simulated bump removed all three progress records and the remembered rater id,
kept all four outbox entries, and left the next load on an empty welcome screen
with no resume note. First epoch is `2026-08-24`;
`build_id = "2026-08-24-data-epoch"`, no version bump, nothing recorded changed.
