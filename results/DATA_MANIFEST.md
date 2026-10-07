# Data & Artefact Manifest

_This manifest lists every file produced or consumed by the thesis
evaluation pipeline, the script that produced it, and its role in the
thesis narrative. Files are grouped by the pipeline stage that
produces or consumes them._

Legend:

- **[STIMULUS]** input to the pipeline (hand-curated or extracted once)
- **[CACHED]** output of a generation step, shipped in the artefact so
  the evaluation can be reproduced without re-generation
- **[PRIMARY]** thesis-critical evaluation output
- **[DERIVED]** human-readable / analysis view over primary output
- **[DOC]** thesis-ready narrative document
- **[LEGACY]** kept for sensitivity analysis or historical reference

---

## 1. Stimuli

Inputs hand-curated from four open-source repositories (Apache Kafka,
Django, Grafana, scikit-learn) checked out under `luca_repos/`.

| Path | Role | Notes |
|------|------|-------|
| `data/luca_prs_fixed/pr{1..25}_evidence.json` | **[STIMULUS]** | Per-PR evidence bundle (title, body, diff, file list, issue context). One JSON per PR. |
| `data/new_prs_files.json` | **[STIMULUS]** | Source map of PRs to upstream repos + commit SHAs. |
| `LUCA_PRS_CATALOG.md` | **[DOC]** | Human-readable catalog of the 25 PRs with repo / language / size metadata. |
| `luca_repos/{apache_kafka,django_django,grafana_grafana,scikit-learn_scikit-learn}/` | **[STIMULUS]** | Checked-out source repos at the PR head commits. Used for KG construction and evidence extraction. |

## 2. Generated reviews (cached)

Produced once by the `prnote` toolkit; shipped so the evaluation can
run without LLM generation costs.

| Path | Role | Notes |
|------|------|-------|
| `outputs/luca_prs_fixed/pr{1..25}_{baseline,kg,rag,hybrid}.md` | **[CACHED]** | 100 LLM-generated reviews (25 PRs × 4 modes). All generated with `gpt-4o` @ temperature 0.0. These are the stimuli for the evaluation scripts. |
| `outputs/luca_prs_fixed_ast/` | **[CACHED]** | AST-grounded variant used in the AST-vs-grep sensitivity check. |
| `outputs/ablation/` | **[CACHED]** | Ablation reviews for `kg_minimal` / `kg_no_deps` / `kg_no_tests` variants. |
| `outputs/luca_prs/` | **[LEGACY]** | Earlier generation run, superseded by `luca_prs_fixed`. Kept for audit. |

## 3. Thesis evaluation (primary outputs)

Produced by running the evaluation scripts on the cached reviews.
These are the files the thesis cites.

### 3.1 Multi-judge 25-criterion evaluation

| Path | Role | Produced by |
|------|------|-------------|
| `results/checklist_evaluation_llm_multi.json` | **[PRIMARY]** raw per-judge verdicts for 100 × 25 × 3 = 7 500 cells, plus panel metadata | `scripts/evaluate_reviews.py` |
| `results/checklist_evaluation_llm.json` | **[PRIMARY]** majority-vote aggregate in legacy shape (ties → 0); consumed by downstream analyses | `scripts/evaluate_reviews.py` |
| `results/checklist_evaluation_llm.csv` | **[DERIVED]** tabular aggregate | `scripts/evaluate_reviews.py` |
| `results/checklist_evaluation_summary.csv` | **[DERIVED]** mode-level roll-up | `scripts/evaluate_reviews.py` |
| `results/CHECKLIST_EVALUATION_REPORT.md` | **[DERIVED]** human-readable report with KG vs. baseline deltas and κ | `scripts/evaluate_reviews.py` |
| `results/checklist_evaluation_llm_multi_run.log` | log of the multi-judge run |  |
| `results/checklist_evaluation_llm_retry.log` | log of the Gemini-failure retry pass | `scripts/retry_failed_judges.py` |

### 3.2 Completeness (C6) evaluation — post-pilot addition

| Path | Role | Produced by |
|------|------|-------------|
| `results/c6_completeness_llm.json` | **[PRIMARY]** C6 scores for 18 (pr × mode) pairs × 3 judges; stimulus subset = 6 human-study PRs. | `scripts/evaluate_completeness.py` |
| `results/c6_completeness_llm_run.log` | run log |  |

### 3.3 Human ↔ LLM agreement (analysis)

| Path | Role | Produced by |
|------|------|-------------|
| `results/human_eval_sample.csv` | **[STIMULUS]** synthetic sample used to dry-run the analysis script before real human data arrives | `scripts/analyze_human_llm_agreement.py` (`_write_sample_csv`) |
| `results/human_llm_agreement.json` | **[DERIVED]** Cohen's κ and raw-agreement tables on the synthetic sample | `scripts/analyze_human_llm_agreement.py` |

When real pilot-v2 data lands, replace `human_eval_sample.csv` with
the Google Sheet export following
`results/HUMAN_STUDY_ANALYSIS_RUNBOOK.md`.

### 3.4 Sensitivity / backup / legacy

| Path | Role |
|------|------|
| `results/checklist_evaluation_llm.single_judge_backup.json` | **[LEGACY]** pre-multi-judge single-judge evaluation (gpt-4o-mini). Used for sensitivity analysis in `METHODOLOGY_AND_FINDINGS.md`. |
| `results/checklist_evaluation_llm.single_judge_backup.csv` | same, tabular |
| `results/CHECKLIST_EVALUATION_REPORT.single_judge_backup.md` | same, human-readable |
| `results/checklist_evaluation.json` | **[LEGACY]** rule-based (non-LLM) checklist scoring. Superseded by the LLM multi-judge evaluation. |
| `results/ablation_raw.json`, `results/ablation_report.md` | **[PRIMARY]** KG ablation (minimal / no-deps / no-tests) for Chapter 5. |
| `results/ast_vs_grep_comparison.json` | **[PRIMARY]** sensitivity to the evidence-extraction method. |
| `results/luca_pipeline_results.csv`, `results/luca_similarity_metrics.csv` | **[LEGACY]** pilot-stage comparison vs. the LUCA baseline. |

## 4. Thesis-ready documents

Paste-ready narrative text.

| Path | Role |
|------|------|
| `results/METHODOLOGY_AND_FINDINGS.md` | **[DOC]** Methodology + results chapter material |
| `results/DISCUSSION.md` | **[DOC]** Discussion chapter draft |
| `results/THREATS_TO_VALIDITY.md` | **[DOC]** Threats-to-validity chapter draft |
| `results/HUMAN_STUDY_ANALYSIS_RUNBOOK.md` | **[DOC]** runbook for analysing human pilot data |
| `results/POWER_ANALYSIS.md` | **[DOC]** statistical power calculations for the human study |
| `results/25_PRS_EVALUATION_REPORT.md` | **[DOC]** narrative summary of the 25-PR evaluation |
| `results/THESIS_COMPARISON_REPORT.md` | **[DOC]** comparison against prior work (DeepCRCEval, CRScore, Chatbot Arena) |
| `results/PROGRESS_REPORT.md` | **[DOC]** progress log |
| `results/RESULTS_LATEX.tex`, `results/thesis_table.tex` | **[DOC]** LaTeX snippets to paste into the thesis |

## 5. Human study (deployed)

| Path | Role |
|------|------|
| `human_eval/index.html` | deployed static site for the pairwise human study (6 criteria, 3 PR pairs + warmup + briefing + consent) |
| `human_eval/study_data.json` | stimulus + criteria definitions (version `6-criterion-v3-pairwise`) |

The human study's backend is a Google Apps Script that appends to a
Google Sheet; the sheet URL and Apps Script source live in
`human_eval/index.html`'s `SHEET_URL` constant. Apps Script source is
under version control in the deployment account (not in this repo —
it is Google-hosted). Exports from the sheet are consumed by
`scripts/analyze_human_llm_agreement.py`.

## 6. Reproducibility infrastructure

| Path | Role |
|------|------|
| `README.md` | top-level reproduction recipe |
| `requirements.txt` | full pipeline dependencies (generation + eval) |
| `requirements-eval.txt` | evaluation-only dependencies (minimum to reproduce `results/` from cached reviews) |
| `reproduce.sh` | one-command pipeline driver |
| `.env.example` | API-key template |
| `results/DATA_MANIFEST.md` | this file |

## 7. Regenerating a specific output

- `results/checklist_evaluation_llm_multi.json` + derived files:
  `python3 -m scripts.evaluate_reviews`
- `results/c6_completeness_llm.json`:
  `python3 -m scripts.evaluate_completeness`
- `results/human_llm_agreement.json`:
  `python3 -m scripts.analyze_human_llm_agreement --human-csv <path>`
- Recovery from malformed Gemini JSON:
  `python3 -m scripts.retry_failed_judges`

Every run writes a metadata block embedding the judge model slugs, the
timestamp, and the aggregation rule — so even if this manifest falls
out of date with the scripts, the output files are self-describing.
