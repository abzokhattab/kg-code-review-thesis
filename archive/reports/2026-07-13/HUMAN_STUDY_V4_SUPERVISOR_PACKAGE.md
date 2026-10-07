# Human study v4 — submission package (2026-07-13)

One-page summary of the RQ3 human study, ready for your review before we
recruit raters. Everything referenced lives in
`experiments/2026-07-06_user_study_prs/`.

## Why this study exists — the gap it closes

Every headline result in the thesis so far is scored by LLM judges: the
RQ2 rubric result (KG +0.60/9 on KG-relevant criteria, p = .007;
`results/BOOTSTRAP_STATS_v2.md`) and the injection experiment's detection
rates (deployed KG 54% vs baseline 0% / RAG 4% on cross-file defects,
rising to 75% with inheritance edges and 93% at the static-resolver
ceiling; `results/INJECTION_EXP2_RESULTS.md`). LLM-as-judge is a legitimate
protocol (Zheng et al. 2023) but has documented biases, and the expected
committee question is "why no human gold standard?". This study supplies
the one piece of evidence no LLM can: that the difference the machines
measure is *visible to and valued by people*.

## What the study asks, and what result we expect

Do blinded human reviewers *perceive* the difference the KG makes —
specifically, better grounding of the concrete components/files affected
by a change (criterion F3*)?

F3* is the pre-registered primary endpoint because the whole evidence
chain already points there: RQ2 localises the KG effect on exactly this
criterion family (+0.60/9, p = .007, vs a marginal total effect); the
injection experiment shows the mechanism (the KG's contribution is knowing
the dependents); the stimuli differ mechanically there (every KG review
carries 2–5 verified off-diff references, every baseline zero); and the
code-review literature (Bosu et al. 2015; Bacchelli & Bird 2013) finds
reviewers rate comments useful precisely when they identify specific
issues at specific locations.

Expected pattern: per-rater KG-preference > 0.5 on F3* (Wilcoxon
signed-rank, α = .05) with the secondary "overall usefulness" CI
overlapping 0.5 — i.e. *KG changes what a review grounds, not necessarily
holistic perceived usefulness*. A null primary is pre-registered as a
reportable boundary result (the KG difference is objectively real per the
injection experiment but not salient to humans); no re-running to chase
significance.

This is deliberately a **perception probe**, not an effectiveness
estimate. Effectiveness is RQ2's and the injection experiment's job; 6
stimuli keep the session at 20–30 minutes, a fatigue/data-quality
decision, not a statistical compromise — the fully crossed within-subject
design (every rater rates all 6 PRs) is what makes n = 15–20 sufficient.

## Design (frozen in ANALYSIS_PLAN.md, 2026-07-06; amended 2026-07-13, see below)

- **Stimuli:** 6 merged PRs from small, familiar Python libraries
  (requests ×2, flask ×2, click ×2), chosen from ~300 candidates for
  legibility (2–5 files, 10–400 LoC) and KG-richness. Replaces the v3
  stimuli (sklearn/kafka/jenkins/grafana) that raters found impossible to
  verify.
- **Comparison:** per PR, one blind side-by-side pair — `baseline_strict`
  vs `kg` review (gpt-4o, temp 0, identical prompts except KG context;
  A/B sides randomized per rater).
- **Judgments per PR:** 6 criteria (A/B/both/neither), one overall
  preference, a required "why", difficulty 1–5.
- **Raters:** target n = 15–20 (recruit ~20 to survive the pre-registered
  ≥4-of-6-tasks inclusion rule), fully crossed — every rater rates all 6
  PRs, so the rater is the unit of analysis (90–120 paired judgments).
- **Primary endpoint (confirmatory):** F3* — "which review better names the
  specific functions, classes, or files affected". Wilcoxon signed-rank vs
  0.5. Sample size from a simulated power analysis (seed 2026, 4 000
  sims/cell, `POWER_ANALYSIS.md`): power 0.99 at n=15 for pilot-like
  effects, 0.79/0.87/0.91 at n=15/18/20 in the conservative diluted
  scenario; type-I error verified ≈.05 under the null.
- **Secondary (estimation only):** overall usefulness — reported with a
  bootstrap CI, no significance claim; pre-registered as underpowered.

## Rater aids (the v3 lesson)

v3 raters could not verify reference claims in unfamiliar codebases. v4
pre-computes three neutral, arm-symmetric aids into the UI:

1. **Answer-key badges** — every file reference in every review checked
   against the repo at the PR's commit (in-diff / verified / exists /
   not-found). Result across all 12 reviews: **zero hallucinated
   references**; every KG off-diff reference is a real file that imports
   the changed module (2–5 per review).
2. **Concrete-item counts** — auto-extracted counts (components, files,
   test targets, edge cases, reasoned claims) shown as chips, so raters
   judge the *difference* rather than counting.
3. **Unique-content highlighting** — hand-curated verbatim markers shade
   only genuinely unique points; shared points stay unshaded.
4. **Plain-language PR context** (added 2026-07-13) — raters know neither
   these repos nor necessarily Python, so each PR opens with one
   hand-written paragraph explaining what the library is and what the
   change does. Written from the PR title/body/diff only (never from a
   review), so it is arm-neutral. The 6 criteria descriptions and the
   orientation summaries were reworded into plain language at the same
   time (criterion ids and meaning unchanged; review texts untouched).

## Blinding fix (2026-07-13, before any real data)

A pre-submission audit found two surface tells that could reveal the arm:
a prompt-scaffolding tail (`## Traceability` / "MANDATORY COVERAGE"
checklist, present inconsistently across arms) and Evidence subsection
labels (`**Structural Context:**`) present only in KG reviews.

`normalize_review_surfaces.py` removed both with uniform rules defined on
the artifact surface (never the mode label); no reference content was added
or removed. All downstream layers (answer key, counts, markers, one summary
bullet) were rebuilt on the normalized texts, and the audit was re-run:

- tell-token scan: 0 asymmetric tokens across the 12 shipped reviews;
- section structure now identical across arms
  (Problem / Evidence / Impact / Recommendation);
- lengths comparable (baseline mean 273 words, KG mean 290);
- all highlight markers verbatim-present and arm-unique;
- all answer-key references still present in the shipped texts.

Pre-normalization originals: `reviews_prenorm_backup_2026-07-13/`.
Recorded as an amendment in `ANALYSIS_PLAN.md` (still before any rater data).

## Pilot status

Instrument validated end-to-end 2026-07-06 with an AI rater
(`pilot/PILOT_RESULTS.md`; excluded from analysis by pre-registered rule).
Every criterion was answerable without codebase knowledge; blind overall
tally kg 5, tie 1, baseline 0, with wins concentrated exactly on F3* —
convergent with the RQ2 LLM-judge localisation. The UI was smoke-tested
again today on the normalized data (all 6 tasks render with badges,
counts, and highlights; no tells).

## How the three legs fit together

The thesis claim — KG context improves LLM code review where structure
matters — rests on three legs, each covering the others' weakness:

| Leg | Shows | Strength | Weakness it leaves |
|---|---|---|---|
| RQ2 (40 PRs, 3-judge panel) | KG improves the criteria it targets (+0.60/9, p = .007) | scale, real PRs | machine-judged, correlational |
| Injection experiment (2026-07-13) | KG context is causally the difference between detecting and missing a cross-file defect (KG 54–93% across variants vs baseline 0% / RAG 4%), against objective ground truth | causal, judge validated vs a deterministic oracle | synthetic defects, no humans |
| **This study (RQ3)** | blinded humans perceive that same specific difference when the verification burden is lifted | human validity | small n, perception not effectiveness |

All three converge on one construct: *naming the true dependents of a
change*. RQ2 measures it at scale, the injection experiment proves the
mechanism, and the human study shows people see and value it.

## Honest limitations (stated up front)

- KG builder for these stimuli is AST import resolution, not the Joern CPG
  pipeline of the 40-PR experiment (same relation class; exact for Python
  at this repo size; recorded in metadata).
- The "verified" badge guarantees the file imports the changed module, not
  that the review's stated *mechanism* is precise; "why" texts will be
  coded for over-crediting (pre-registered threat).
- On the 25-criterion LLM rubric these 6 PRs show no KG advantage (they
  ship their own tests) — the study's contrast is verifiable grounding,
  which is why F3* is the primary endpoint, not rubric totals.

## Deployment status (2026-07-13)

The study is live and end-to-end verified: UI at
https://abzokhattab.github.io/pr-review-study/ (GitHub Pages), data
collection via a Google Apps Script webhook into the "Human Eval"
spreadsheet (health-checked; task, demographics, and feedback payloads
all confirmed written; every POST additionally mirrored verbatim to a
`raw_log` tab, and each rater's browser keeps a downloadable local
backup). You can try the study yourself at that link — use any rater ID
starting with `pilot` or `smoke` and it will be excluded from analysis
by the pre-registered rule.

## What we need from you

1. Green light to recruit 15–20 raters on this instrument.
2. (Separate memo) the v2-vs-Joern canonical-era decision for RQ2 —
   `ERA_DECISION_MEMO.md`.
