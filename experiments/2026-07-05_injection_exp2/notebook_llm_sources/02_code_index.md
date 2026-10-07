# Code index

Every Python and shell script in this bundle, organised by the thesis
section it supports. **When writing the methodology chapter, cite the
file paths listed here; when writing the results chapter, cite the
output artefact in `results/`.**

The code is verbatim from `/Users/akhattab/ai/` as of 2026-05-12.
Abandoned interim branches (the 14-criterion rubric, one-off fix
scripts) are *not* included so Claude isn't tempted to cite them.

---

## 1. Core toolkit — `prnote/`

The hand-written Python package that implements the four review-generation
modes. **Thesis location:** Chapter 4 (Approach), §"KG design", §"RAG
design", §"Generation modes".

| File | Lines | Role |
|---|---:|---|
| `prnote/__init__.py` | 3 | Package init |
| `prnote/cli.py` | ~370 | Command-line interface — `prnote review --mode {baseline,kg,rag,hybrid}` |
| `prnote/note.py` | ~640 | **Review generator.** Builds the LLM prompt for each mode, calls the model, parses the response. The four-mode logic lives here. |
| `prnote/kg.py` | ~440 | **Knowledge graph construction.** AST-based extraction of functions, files, tests, calls/imports. Supports Python, Java, TS/JS, Go, C++, Scala via tree-sitter. |
| `prnote/rag.py` | ~390 | **RAG retrieval.** Builds a chunk index over the repo with `text-embedding-3-small`; retrieves top-k chunks at review time. |
| `prnote/evidence.py` | ~300 | **Evidence pack assembly.** Glues a PR's diff, title, body, KG sub-graph, and RAG chunks into a single JSON evidence pack consumed by `note.py`. |
| `prnote/hybrid.py` | ~220 | KG+RAG context fusion (the hybrid mode's context builder). |
| `prnote/llm.py` | ~150 | LLM client wrapper (OpenAI + Gemini), with retries and rate-limit handling. |
| `prnote/utils.py` | ~130 | File-walk and path helpers. |
| `prnote/eval.py` | ~140 | (Older, single-judge eval — used for early ablations. The current production eval is `scripts/evaluate_reviews.py`.) |
| `prnote/report.py` | ~390 | Markdown report rendering for review outputs. |
| `prnote/ablation.py` | ~120 | Ablation helpers for the KG component (turn nodes/edges off and regenerate). |

**Entry point for understanding the system:** read `prnote/note.py` first
(it shows what each mode actually sends to the LLM), then `prnote/kg.py`
and `prnote/rag.py` for the two context-injection mechanisms.

---

## 2. Dataset construction

### 2.1 v1 dataset (the original 25 PRs — kept for the trajectory story only)

| File | Role | Cited in |
|---|---|---|
| `scripts/expand_dataset.py` | Original 25-PR fetcher. Cited as the contaminated path; **its 15 kB diff cap is the bug that motivated v2** (see `dataset_v2/docs/AUDIT_v1.md`). | Ch. 4 §Dataset, Ch. 7 §Threats |

### 2.2 v2 dataset (the canonical 40 PRs — RQ2 headline data)

**Thesis location:** Chapter 4 (Approach), §"Dataset construction (v2)";
Chapter 7 (Discussion), §"Replacement of v1".

Pipeline order:

```
audit_v1_dataset.py  →  fetch_evidence_v2.py  →  merge_rag_context_from_v1.py
                                              →  rebuild_rag_for_v2_contaminated.py
                                              →  find_seven_more_prs.py     →  build_rag_for_new_seven.py
                                              →  find_fifteen_more_prs.py   →  build_rag_for_new_fifteen.py
                                              →  regenerate_reviews_v2.py
                                              →  compare_v1_v2.py
```

| File | Role |
|---|---|
| `dataset_v2/scripts/audit_v1_dataset.py` | Reproduces the v1 audit (8 categories of bugs). Output: `dataset_v2/docs/audit_v1.json`. |
| `dataset_v2/scripts/fetch_evidence_v2.py` | Re-fetches 40 PRs from GitHub with the 50 kB diff cap. Output: `data/luca_prs_v2/pr*_evidence.json`. |
| `dataset_v2/scripts/merge_rag_context_from_v1.py` | Copies clean RAG chunks from v1 packs where the underlying repo state is unchanged. |
| `dataset_v2/scripts/rebuild_rag_for_v2_contaminated.py` | Re-runs RAG retrieval for the 4 PRs (1, 2, 12, 13) whose v1 RAG was contaminated. |
| `dataset_v2/scripts/find_seven_more_prs.py` | First expansion (18 → 25). Direction-blind selection script. Output: `dataset_v2/docs/seven_more_candidates.json`. |
| `dataset_v2/scripts/find_fifteen_more_prs.py` | Second expansion (25 → 40). Adds c8 KG-richness criterion. Output: `dataset_v2/docs/fifteen_more_candidates.json`. |
| `dataset_v2/scripts/build_rag_for_new_seven.py` | RAG build for PRs 27–33. |
| `dataset_v2/scripts/build_rag_for_new_fifteen.py` | RAG build for PRs 34–48. |
| `dataset_v2/scripts/regenerate_reviews_v2.py` | Regenerates all 160 reviews with gpt-4o, T = 0.4, seed = 42. Idempotent (skips on-disk reviews) and resumes through 429s with exponential backoff. |
| `dataset_v2/scripts/compare_v1_v2.py` | Builds the v1↔v2 comparison report. Output: `results/V1_VS_V2_COMPARISON.{md,json}`. |
| `dataset_v2/scripts/run_phase34_when_ready.sh` | Convenience wrapper to run regenerate + evaluate in one shot. |

---

## 3. Evidence-pack & KG/RAG builders

**Thesis location:** Chapter 4 (Approach), §"Evidence pack format".

| File | Role |
|---|---|
| `scripts/build_kg_evidence.py` | Original grep-based KG evidence builder (used in v1). Kept for the AST-vs-grep sensitivity check. |
| `scripts/build_kg_evidence_ast.py` | **AST-grounded KG evidence builder (production).** Uses tree-sitter to extract functions and call/import relations. Output: `data/luca_prs_v2/pr*_evidence.json`. |
| `scripts/build_rag_and_enrich.py` | Builds RAG indices per repo with `text-embedding-3-small`, enriches evidence packs with top-k chunks and dependent-files. |
| `scripts/rebuild_evidence_with_diffs.py` | Refreshes evidence packs when only the diff text changed (cheaper than a full rebuild). |
| `scripts/scope_ast_evidence.py` | KG-scoping experiment — restrict KG sub-graph to the diff's neighbourhood. |

---

## 4. Review generation (alternate modes)

| File | Role |
|---|---|
| `scripts/regenerate_reviews.py` | Generic regen helper (used by `dataset_v2/.../regenerate_reviews_v2.py`). |
| `scripts/regenerate_reviews_alt_model.py` | Cross-generator replication harness (e.g., a 5-PR Claude-as-generator run for sensitivity). |
| `scripts/generate_ast_kg_reviews.py` | Generates reviews with the AST-scoped KG variant. |
| `scripts/generate_kg_empty_control.py` | **Negative control.** Generates "kg" reviews with an *empty* KG; the resulting yes-rate is the floor that the real KG mode must beat. |

---

## 5. Evaluation pipeline (RQ2)

**Thesis location:** Chapter 5 (Evaluation protocol); Chapter 6 (Results,
RQ2). **Headline output:** `results/checklist_evaluation_llm_multi__v2.json`.

| File | Role |
|---|---|
| `scripts/evaluate_reviews.py` | **The 3-judge LLM panel.** For each (PR, mode, criterion) cell, asks gpt-4o-mini, gpt-4o, gemini-2.5-flash whether the review satisfies the criterion. Majority vote = cell. Per-review checkpointing; resumes through API failures. Output: `results/checklist_evaluation_llm_multi__v2.json`. |
| `scripts/evaluate_reviews_graded.py` | **Graded 0-3 scale pilot.** Replaces binary 0/1 with anchored descriptors for the 5-criterion clean subscale (F3, F4, P1, R2, T3). Used to test whether graded scoring reveals signal suppressed by the ceiling effect. Output: `results/GRADED_PILOT_RESULTS.json`, `results/GRADED_SCALE_RESULTS.md`. |
| `scripts/retry_failed_judges.py` | Retries any cells where a judge returned a non-parseable response. |
| `scripts/evaluate_completeness.py` | (Older, single-judge completeness check — kept for the v1 comparison baseline.) |
| `scripts/bootstrap_stats.py` | **Bootstrap CIs + paired permutation tests.** B = 10 000 / 20 000, seed = 2026. Output: `results/BOOTSTRAP_STATS_v2.{md,json}`. |

---

## 6. Rubric validation

**Thesis location:** Chapter 5 (Evaluation protocol), §"Rubric provenance
and validation". **Cited reports:** `results/RUBRIC_PROVENANCE.md`,
`results/RUBRIC_KAPPA_kg_relevant.md`, `results/RUBRIC_POSITIVE_CONTROL.md`.

| File | Role |
|---|---|
| `scripts/validate_kg_relevant_kappa.py` | Computes Cohen's κ between an LLM tagger and a human tagger on the "is this criterion KG-relevant?" binary label. Defends the 9-of-25 KG-relevant subset. |
| `scripts/positive_control_rubric.py` | **Positive control.** Generates deliberately-bad reviews; checks that the rubric flags 4-of-5 as below average. Shows the rubric *can* discriminate. |

---

## 7. Sensitivity & ablation studies

**Thesis location:** Chapter 6 (Results), §"Sensitivity analyses";
Chapter 7 (Discussion), §"Why the headline holds up".

| File | Role |
|---|---|
| `scripts/evaluate_ast_vs_grep.py` | Compares the AST-based KG against the older grep-based KG on the same PRs. Cited in `results/THREATS_TO_VALIDITY.md`. |
| `scripts/run_ablation_study.py` | Ablation harness: turns specific KG node/edge types off and re-runs. Cited in `results/ablation_report.md`. |
| `scripts/attribute_kg_wins.py` | Splits every paired KG-vs-baseline criterion win/loss into the 9 KG-relevant vs 16 non-KG-relevant bands (placebo-band test) and dumps the judge's reason for each KG-relevant win. Output: `results/KG_WIN_ATTRIBUTION.md`. Shows wins concentrate on KG-relevant criteria (+24 net vs +1). |
| `scripts/measure_offdiff_grounding.py` | Counts, per mode, how many KG-pack file stems absent from the diff each review cites (verifies KG context is genuinely used, not memorised). Output: `results/OFFDIFF_GROUNDING.md`. |

---

## 8. Human study (RQ3)

**Thesis location:** Chapter 5 (Evaluation protocol), §"Human study
design"; Chapter 6 (Results), §"RQ3 — human ↔ LLM agreement".

### Build the study artefacts

| File | Role |
|---|---|
| `human_eval_v3/scripts/build_study_data_v2.py` | **Study-data builder.** Takes the 6 chosen PRs, formats reviews for the UI, strips empty sections, generates `study_data.json` consumed by the front-end. |
| `human_eval_v3/scripts/generate_review_summaries.py` | **AI summary layer.** Adds a neutral, blinding-safe 2–3 bullet TL;DR per review into `study_data.json` (`review_summaries[mode]`), rendered as an orientation box atop each review card. Pre-computed offline (gpt-4o-mini), idempotent. Added after the concise ablation showed shortening reviews doesn't help (`results/SNR_RESULTS_DEDUP.md`); the summary cuts rater fatigue without touching the stimulus. |
| `human_eval_v3/scripts/generate_review_counts.py` | **Concrete-item count layer** (supervisor request, 2026-06-21). Pre-computes, per review, neutral counts of concrete items in 5 categories mapped to the study criteria — components/APIs (F3*), files, test targets (T3), edge cases (F2*), reasoned claims (Q5) — into `study_data.json` (`review_counts[mode]`, stores the extracted item lists for audit). Rendered as a hoverable chip strip on each review card so raters judge whether the *difference* in concrete substance is relevant, rather than counting themselves. Blinding-safe (text-only, neutral prompt), gpt-4o-mini, idempotent. |
| `human_eval_v3/scripts/generate_review_unique.py` | **Semantic difference-highlighting markers** (Chris spec, 2026-06-21). Pairwise LLM semantic diff of the two reviews per PR; writes `study_data.json` (`review_unique[mode]`) = verbatim phrases genuinely unique to each review (shared points, even if paraphrased, get no marker). The UI shades only blocks containing a marker, replacing the old lexical word-overlap heuristic that over-highlighted ~70%. Blinding-safe, verbatim-validated, idempotent. (The current 6-PR study ships hand-curated markers; this script reproduces them for future PR sets.) |
| `reports/2026-06-22/build_demo.py` | **Product demo builder.** Generates `reports/2026-06-22/demo.html`, a single self-contained page (no server/API) that shows, on real PRs (44/24/47), the knowledge graph the tool retrieves (changed → imported-by → tested-by, from the v2 evidence packs) and a side-by-side of the diff-only vs KG-augmented review with the concrete code locations the KG review grounds in (that the baseline omits) highlighted. For the thesis "Practical Implications" / defense. |
| `human_eval_v3/scripts/smoke_test.py` | Sanity-checks `study_data.json` (PR count, fields present, no truncations). |
| `human_eval_v3/scripts/deep_audit.py` | Deeper content-quality audit (review length, traceability sections, etc.). |
| `human_eval_v3/scripts/analyze_pr_candidates.py` | Scores PR candidates for human-study suitability (KG language coverage, diff size, body length). Drives the 6-PR selection in `human_eval_v3/docs/HUMAN_STUDY_PR_SELECTION.md`. |
| `human_eval_v3/scripts/fetch_pr_bodies.py` | Refetches PR bodies from GitHub when the cached evidence pack has an empty body. |
| `human_eval_v3/scripts/fetch_pr_ground_truth.py` | Fetches human review comments from GitHub (for the post-hoc ground-truth analysis). |

### Run / collect / analyse the study

| File | Role |
|---|---|
| `scripts/prepare_human_study.py` | Pre-flight check (PR count, comparison count, UI strings) before deploy. |
| `scripts/simulate_rater_v3.py` | Simulates a full single-rater session for v3 — used to pilot the UI without burning a real rater. |
| `scripts/rater_walkthrough_v2_vs_v3.py` | Prints a side-by-side comparison of what a rater sees in v2 vs v3 (used to justify the UX redesign). |
| `scripts/smoke_test_webhook.sh` | Smoke-tests the Apps Script webhook deployment. Currently broken upstream — see `human_eval_v3/docs/REDEPLOY_WEBHOOK.md` in the source repo. |
| `scripts/ingest_exported_payloads.py` | Ingests manually-exported JSON payloads from the UI's localStorage backup queue into CSV. Used when the webhook is down. |
| `scripts/analyze_human_llm_agreement.py` | Legacy v3 RQ3 analyser (per-criterion Cohen's κ). Kept for reference; superseded by v4. |
| `scripts/analyze_human_study_v4.py` | The v4 RQ3 analyser (5-point preference design). Computes Kendall's τ between human 5-point preference scores and LLM judge delta scores per PR, plus Krippendorff's α and per-rater quality flags. Superseded by the per-criterion design below. Output: `results/SYNTHETIC_human_study_v4_agreement.json`. **The committed output is fabricated dry-run data, not human responses; never cite it.** |
| `scripts/analyze_human_study_criteria.py` | **The current RQ3 analyser** (per-criterion A/B/both/neither + overall preference, baseline_strict vs Joern-KG). Per-criterion and overall preference normalised to the Joern arm, correct Krippendorff's α (nominal per criterion, ordinal overall), rater-quality flags, difficulty/engagement. Opt-in human↔LLM per-criterion agreement (needs `--llm-judge` + `--kg-mode`/`--baseline-mode`; the C6 criterion has no rubric equivalent and is excluded). `--sample` for a synthetic dry-run. Reads the `responses_criteria` Sheet tab. Output: `results/human_study_criteria.json`. |

---

## 9. Project metadata

| File | Role |
|---|---|
| `requirements.txt` | Runtime dependencies (OpenAI, Google Generative AI, tree-sitter, etc.). |
| `requirements-eval.txt` | Eval-only dependencies (scipy, numpy for bootstrap stats). |
| `setup.py` | Makes `prnote/` pip-installable. |
| `reproduce.sh` | Top-level "rebuild RQ2 from scratch" script. ~2 hr wall-clock, ~$15 OpenAI. |
| `load_env.sh` | Sources `.env` into the current shell (the eval scripts need `OPENAI_API_KEY` and `GOOGLE_API_KEY`). |
| `.env.example` | Template for the `.env` file. |

---

## 10. What's *not* included (and why)

| Omitted | Reason |
|---|---|
| `scripts/ablation_14criteria.py`, `scripts/evaluate_14criteria.py` | Abandoned 14-criterion branch. The thesis cites the 25-criterion path. |
| `scripts/fix_evaluation.py`, `scripts/update_c6_for_pr.py` | One-off patch scripts for specific PRs; not part of the methodology. |
| `data/luca_prs_v2/*.json` (evidence packs) | Too large for a context bundle (~40 × 50 kB). The pipeline that produces them is here; the artefacts are on the source machine. |
| `outputs/luca_prs_v2/*.md` (160 generated reviews) | Same reason as above. |
| `results/checklist_evaluation_llm_multi__v2.json` (12 000-cell panel) | Same reason. The summarised numbers are in `results/BOOTSTRAP_STATS_v2.md`. |
| `repos/` and `luca_repos/` (source repos at PR head SHAs) | Multiple GBs, fetched on demand by `prepare_human_study.py`. |

If Claude needs one of these artefacts to write a specific paragraph,
ask me — I'll either paste the relevant slice or push the file to a
separate `thesis-context-data` repo.

---

## Quick lookup — "where is X?"

| You want… | Open this |
|---|---|
| The KG construction algorithm | `prnote/kg.py` |
| The RAG chunking + retrieval logic | `prnote/rag.py` |
| The exact prompts sent in each mode | `prnote/note.py` |
| The 3-judge panel orchestration | `scripts/evaluate_reviews.py` |
| The 8 v2 selection criteria implementation | `dataset_v2/scripts/find_fifteen_more_prs.py` |
| The bootstrap CIs / perm tests | `scripts/bootstrap_stats.py` |
| Which KG construction wins (grep vs AST vs Joern) | `scripts/compare_kg_methods.py` → `results/KG_METHOD_COMPARISON.md` |
| Verbosity/length-bias check on the judge | `scripts/check_judge_length_bias.py` → `results/JUDGE_LENGTH_BIAS.md` |
| Concise-prompt ablation (negative control) | `scripts/run_concise_prompt_experiment.py`, `scripts/judge_parallel.py` |
| Project a multi-judge panel to one judge (no API) | `scripts/extract_single_judge_scores.py` |
| Kruskal-Wallis/Friedman + Bonferroni post-hoc | `scripts/kruskal_bonferroni.py` |
| The v1↔v2 comparison logic | `dataset_v2/scripts/compare_v1_v2.py` |
| The positive control for the rubric | `scripts/positive_control_rubric.py` |
| The human-study UI builder | `human_eval_v3/scripts/build_study_data_v2.py` |
| The human ↔ LLM agreement analyser (current) | `scripts/analyze_human_study_criteria.py` |
| The Google Sheets webhook (study submissions) | `human_eval/apps_script_webhook.gs` |
