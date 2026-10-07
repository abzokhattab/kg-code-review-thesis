# 2026-07-06 — New human-study PRs (Python, rater-friendly)

Replacement stimuli for the RQ3 human study. The v3 stimuli (sklearn/kafka/
jenkins/grafana) were too hard for raters: unfamiliar languages, huge repos,
reference claims they could not verify. These 6 PRs are from small, familiar
Python libraries, selected in `pr_hunt/` from ~300 merged PRs by legibility
(2–5 files, 10–400 LoC, real code change, descriptive body) and KG-richness
(changed modules have 7–17 importing files).

## The 6 PRs

| pr_id | repo | PR | what it changes |
|---|---|---|---|
| 101 | psf/requests | [#7433](https://github.com/psf/requests/pull/7433) | `prepare_body` stream detection for `__getattr__` proxies |
| 102 | pallets/flask | [#5637](https://github.com/pallets/flask/pull/5637) | new `TRUSTED_HOSTS` config + host validation |
| 103 | pallets/click | [#3493](https://github.com/pallets/click/pull/3493) | `echo` empty-bytes handling + type narrowing |
| 104 | psf/requests | [#7328](https://github.com/psf/requests/pull/7328) | `resolve_redirects` self-reference in `resp.history` |
| 105 | pallets/flask | [#5799](https://github.com/pallets/flask/pull/5799) | `stream_with_context` refactor for async views |
| 106 | pallets/click | [#3578](https://github.com/pallets/click/pull/3578) | `make_metavar` double-bracketing fix in usage synopsis |

## Pipeline (all idempotent, run in this order)

1. `build_evidence.py` — evidence packs (schema of `data/luca_prs_v2`), KG
   edges via AST import resolution at PR head SHA ($0).
2. `generate_reviews.py` — baseline_strict + kg reviews, gpt-4o temp 0,
   prompts verbatim from the v3 generators (~$0.40).
3. `judge_reviews.py` — 2-judge panel (gemini-2.5-flash + 2.5-pro), same as
   `judge_human_study_pairs.py` (~$0.50).
4. `normalize_review_surfaces.py` — blinding-safe surface normalization
   (added 2026-07-13 after a pre-submission blinding audit). Uniformly strips
   the prompt-scaffolding tail (`## Traceability` + "Code Owners" +
   "MANDATORY COVERAGE" checklist, present inconsistently across arms) and
   flattens Evidence subsection labels (`**Structural Context:**` etc.
   appeared only in KG reviews). Rules are defined on the artifact surface,
   never the mode label; no reference content added/removed. Idempotent, $0.
   Pre-normalization originals: `reviews_prenorm_backup_2026-07-13/`.
4b. `reports/2026-08-01/simplify_reviews_draft.py` — template
   de-boilerplate (added 2026-08-01, v2, after pilot-rater fatigue
   feedback). Uniform, direction-blind rules R1–R4: drop the template
   title and the "Scope:" line, strip bold category labels in
   Problem/Impact bullets, plain-language section headers. No sentence
   reworded/added/removed; reference sets and all 38 markers verified
   intact; reduction symmetric (−12.7% / −12.8%). Originals:
   `reviews_presimplify_backup_2026-08-01/`. See ANALYSIS_PLAN.md
   amendment 2026-08-01 (also covers the v2 UI burden cuts: collapsed
   diff, compact criterion labels, optional "why", anti-counting wording).
5. `build_answer_key.py` — verifies every file reference in every review
   against the repo: in_diff / verified / exists / not_found ($0).
6. `assemble_study_draft.py` — `study_data_draft.json` in the v3 UI schema
   (+ hand-authored summaries + hand-curated unique markers + answer key
   + plain-language `pr_context` per PR + plain-language criteria wording,
   both added 2026-07-13 for raters who know neither the repos nor Python;
   preserves the frozen `review_counts` layer across re-assembly),
   then `human_eval_v3/scripts/generate_review_counts.py --study ...`
   (~$0.03). Note: the unique markers are CURATED in the assemble script
   (audited 2026-07-06 — the generate_review_unique.py output contained
   section headers present in both reviews); do not re-run that script here.

## Key outputs

- `study_data_draft.json` — study data (6 PRs × 2 modes). Summaries,
  unique markers, and the answer key support the assisted interface; counts
  remain embedded for offline audit but are not rendered. Deployed copy:
  `pilot/study_data.json`.
- `answer_key.json` — neutral repository-reference evidence. **Zero
  hallucinated file references in all 12 reviews**. Existence is reported
  separately from source-audited relationship strength (direct, indirect,
  related data flow, module-only, type-only, or unestablished).
- `reviews/*_eval.json` — LLM-judge scores per review. NOTE: judged on the
  pre-normalization texts (incl. the scaffolding tail); directional only.
- `pilot/` — deployable assisted study UI (plain-language context, summaries
  framed as review claims, inline file-reference tooltips, optional
  highlighting off by default, optional diff, and no criterion-mapped count
  strip), with `study_id=human_eval_v4_python_20260808` and
  `instrument_version=python-prs-study-v4-diff-default-r14`.
  `pilot/PILOT_RESULTS.md` documents the earlier instrument-validation run.
  The standalone file-check badge strip was withdrawn at r5 as an un-blinding
  cue, the occupation categories were rebuilt at r6, and the KG summary bullets
  were brought to risk parity with the baseline ones at r7; see
  `ANALYSIS_PLAN.md` for all three rationales.
  **Deployment status (2026-08-24, 17:35 local): r14 is LIVE at
  https://khattab-thesis.github.io/pr-review-study/** — verified by
  `curl -sL https://khattab-thesis.github.io/pr-review-study/study_data.json`
  reporting `python-prs-study-v4-diff-default-r14`, by the served `index.html`
  carrying `BUILD_ID = "2026-08-24-data-epoch"`, and by the live file
  being byte-identical to `pilot/index.html`. r14 shows the diff by default
  instead of collapsed, so F3\* is not answerable without seeing the code; the
  briefing and diff header now warn that the diff holds only the changed files,
  which keeps the default from reading as "affected = in the diff". Four
  copy-only builds ride on `build_id` alone, two before r14 and four after:
  `2026-08-24-occupation-label` (hint line dropped, "PhD / Researcher" label),
  `2026-08-24-time-estimate` (advertised duration corrected to 25–35 minutes),
  `2026-08-24-gh-button` (the GitHub link became a button in the PR header) and
  `2026-08-24-copy-sweep` (filler and pleading removed from every screen) and
  `2026-08-24-gate-message` (the narrow-screen gate now tells a desktop rater to
  widen the window or zoom out, instead of telling them to find a laptop) and
  `2026-08-24-data-epoch` (a `DATA_EPOCH` constant in `pilot/index.html`; edit
  it and every device discards its saved progress and starts the study over on
  the next load, while unsent submissions in the outbox survive — use it when a
  change makes earlier answers incomparable, not for copy fixes, and note that a
  bump mid-recruitment makes anyone half-finished redo the PRs they have done).
  r12 turns away viewports narrower than
  900px, where the review pair collapses to one column; r13 replaces the
  timestamp-based "active in another tab" check with a Web Lock and restores the
  last rater id so returning raters resume instead of retyping. See the
  changelog entries "Narrow screens are turned away" and "Returning to the study
  warned falsely" in `ANALYSIS_PLAN.md`. The study moved from
  `abzokhattab/pr-review-study` to `khattab-thesis/pr-review-study` so the
  recruitment URL does not carry a personal handle; the old repo's Pages site
  is stale (serves r4) and should be taken down before recruiting so raters
  cannot land on it. Historical note: r5–r9 deploys were blocked for a day by a
  GitHub-wide Actions/Pages incident, which is why the older repo never got past
  r4.
  Webhook: Apps Script **v5-2026-08-19** (`human_eval/apps_script_webhook.gs`)
  bound to the "Human Eval" spreadsheet; every POST is mirrored to a
  `raw_log` tab before parsing. The two fixes that got there, in order: **v4 was
  deployed and the UI pointed at it**
  (endpoint rotated 2026-08-19; verified by a POST returning
  `{"ok":true,"version":"v4-2026-08-19","wrote":{...}}`). v3 wrote rows with
  `appendRow()`, which parses every value as if typed, and a full pilot run
  showed the demographics answer `3-5` stored as the date 2026-03-05 (serial
  46086); `1-3` and `5-10` corrupt the same way, and free text beginning with
  `=`, `+` or `-` was read as a formula. v4 preformats string cells as plain
  text. **Creating a new deployment mints a new `/exec` URL**, which is why
  `SHEET_URL` in `pilot/index.html` had to change; to avoid that step, redeploy
  by editing the existing deployment (Manage deployments → pencil → New
  version). The superseded v3 deployment is still reachable and still corrupts
  data, so nothing may be left pointing at it.
  **v5-2026-08-19 is deployed and verified** (same URL; redeployed as a new
  version of the existing deployment). v4's plain-text format fixed value
  coercion but not formula parsing — `setValues()` treats a leading `=` as a
  formula whatever the cell format, and a probe `why` of `=1+1 ...` was stored
  as `#ERROR!`. v5 writes any cell starting with `= + - @ '` as rich text,
  which never parses, and stops `?selftest=1` returning `spreadsheet_id` /
  `spreadsheet_name`. Four probes confirmed `exp_years` (`5-10`, `1-3`, `3-5`,
  `<1`), `role_other`, and `why` openings of `-`, `=` and plain text all store
  verbatim while numeric columns stay numeric. Known residual: a leading
  straight apostrophe in free text is still consumed by Sheets' text-marker
  convention (`'quoted'` → `quoted'`); `raw_log` retains the verbatim payload,
  see `ANALYSIS_PLAN.md`. Since r11 the UI reads
  that reply instead of firing blind: the POST is a CORS-simple request
  (`Content-Type: text/plain`, no custom headers, no preflight), the Apps
  Script reply is readable cross-origin, and the completion screen states
  whether the responses were actually received. Two probe rows written during
  that verification sit in `raw_log` under rater ids `smoke_cors_probe` and
  `smoke_receipt` with `instrument_version` values `cors-probe` and
  `receipt-probe`; both the version filter and the `smoke*` rule exclude them.
- `POWER_ANALYSIS.md` / `power_analysis.py` — simulated power for the
  18–20-complete-rater target. Primary endpoint = F3* criterion preference
  (at n=15,
  simulated power is 0.79 for the diluted scenario and 0.99 for the
  pilot-like scenario); overall usefulness is secondary/descriptive.
- `ANALYSIS_PLAN.md` — initial plan plus transparent pilot-informed,
  pre-confirmatory amendments.
- `analyze_responses.py` — implements the plan; takes the Sheet CSV export or
  the UI's JSON backups, handles exclusion/dedup/un-blinding, writes
  `RESULTS_HUMAN_V4.md`. Validated via `--selftest` on synthetic data.
- `check_payload_schema.py` — runs a payload captured from the deployed client
  (`fixtures/client_payloads.json`) through both of the analyser's ingestion
  routes and asserts it is accepted and un-blinded. `--selftest` cannot catch
  client drift, because its fixtures are written beside the code that reads
  them; this one fails if `pilot/index.html` stops sending a field the analyser
  needs, or if `INSTRUMENT_VERSION` and `STUDY.version` diverge. Re-run after
  editing the payload in `submitCurrent()` or bumping either version.

## Findings from the judge panel (n=6, directional only)

KG did not beat baseline on the 25-criterion rubric here (totals baseline
12/14/13/13/13/13 vs kg 12/13/11/13/13/10). Expected: these PRs already ship
their own tests in the diff, so the baseline_strict prompt scores the test
criteria without needing the KG. The human-study contrast is about
perceived grounding: KG reviews add off-diff references with varying
relationship strength, while baseline reviews add none. The interface reports
those strengths without certifying the review's consequence claims.

This is a six-PR assisted-interface mechanism probe: it tests whether people
perceive better naming/grounding of affected code. It is consistent with,
but does not directly validate, the canonical 40-PR LLM-judge ranking because
the PR sample, KG implementation, and endpoint wording differ.

## Caveat to state in the thesis

KG edges here come from AST import resolution (`ast_import_resolver` in pack
metadata), not the Joern CPG pipeline used for the 40-PR experiment. Same
relation class (files importing changed modules); for Python at this repo
size the AST resolver is exact. Mode is therefore labeled `kg`, not `joern`.
