# Knowledge-Graph-Augmented LLM Code Review — code and assets

Code, data and results for the Master's thesis
*An Empirical Study of Knowledge-Graph-Driven Context Retrieval for LLM-Based
Pull-Request Review Comments* (Abdelrahman Khattab, Hasso Plattner Institute,
October 2026). The thesis asks how repository context changes LLM-generated
pull-request reviews, comparing four modes — diff-only **baseline**, **KG**
(diff + structural edges from a Joern code property graph), **RAG** (diff +
embedding-similar code) and **hybrid** (both) — in three studies:

| Study | Question | Data | Headline |
|---|---|---|---|
| Experiment 1 | Which context helps rubric coverage? | 35 merged PRs, 5 repos, 25-criterion rubric, 5-judge LLM panel | KG +0.69 on the 9 structural criteria (p = 0.003); RAG +1.03 on the full rubric (p = 0.002); hybrid retains neither after correction |
| Experiment 2 | Can the reviewer name cross-file consequences? | 28 injected cross-file defects + 12 local controls, deterministic oracle | baseline 0/28, RAG 5/28, KG 18/28, KG + inheritance 26/28 |
| Human study | Do people see the difference? | 27 raters × 6 Python PRs, blinded pairwise | KG preferred for naming affected code (0.710 vs 0.5, p = 0.0005); no preference on overall usefulness; baseline preferred on clarity |

The LaTeX source of the thesis is in [`thesis/`](thesis/).

## Layout

```
prnote/                   core toolkit: four review modes, KG and RAG context builders, prompts
scripts/                  the ~36 scripts that judge, aggregate, test and plot the thesis results;
                          retired-experiment scripts are in archive/scripts_other/
dataset_v2/               construction of the 40-PR dataset (scripts + audit docs)
data/evidence_packs_v2/   the 40 frozen evidence packs (diff, metadata, graph facts, RAG chunks)
outputs/reviews_v2/       the 160 generated reviews (40 PRs x 4 modes) + per-judge verdict cache
results/                  only the result files the thesis cites or its scripts read (~45 files);
                          everything from earlier eras is in archive/results_other/
experiments/              dated experiment folders that produce the thesis numbers (below)
archive/                  superseded runs and scripts, kept for navigation only (archive/README.md)
thesis/                   LaTeX source of the thesis
DRIVE_UPLOAD_LIST.md      large artefacts that are on Drive instead of here
```

### Experiments that produce the thesis numbers

| Folder | Thesis use |
|---|---|
| `experiments/2026-05-15_joern_kg_main/` | **Joern CPG construction** for Experiment 1: builds the CPG per PR, runs the caller/callee queries and writes the 36 Joern evidence packs (`evidence/`). Its own review results are superseded; only the graph stage is used downstream |
| `experiments/2026-09-19_joern_replace_grep/` | Experiment 1 KG arm: converts the Joern callers into the KG block (`run.py`), the 35 KG reviews, judge scores, and the context-relevance (noise / relevant-only) control (`context_ablation/`) |
| `experiments/2026-10-04_joern_unified_five_judge/` | **Experiment 1 headline table**: five-judge aggregation of baseline / KG / RAG / hybrid on the 35 PRs (`RESULTS.md`, `RESULTS.json`) |
| `experiments/2026-09-23_five_judge_panel/` | Five-judge aggregation for both experiments, individual-judge sensitivity, Experiment 2 detection table (`RESULTS.json` feeds `scripts/generate_thesis_figures.py`) |
| `experiments/2026-07-05_injection_exp2/` | Experiment 2: pre-registration (`docs/`), injection harness (`harness/`), manifest, reviews, judgments (`out/`) |
| `experiments/2026-09-19_exp2_rejudge_v2/` | Experiment 2 two-stage adjudication (post-hoc correction; design and audit trail in `DESIGN.md`) |
| `experiments/2026-09-19_independent_judges/` | Non-OpenAI judge panel sensitivity (Claude, DeepSeek, Grok) |
| `experiments/2026-09-06_test_oracle/` | Test-band component probe (related-test section) |
| `experiments/2026-06-11_joern_normal_prompt_parity/` | Earlier generation of the same Joern configuration (regeneration-variance row of the robustness figure) |
| `experiments/2026-05-14_confirmatory_kg/reviews_clean/` | 12 held-out PRs (`results/CONFIRMATORY_CLEAN.md`) |
| `experiments/2026-07-06_user_study_prs/` | **Human study**: PR selection, evidence packs, the 12 review stimuli, answer key, the deployed UI (`pilot/index.html`, `pilot/study_data.json`), analysis plan, power analysis, analyser and results (`RESULTS_HUMAN_V4.{md,json}`) |

### Where each number comes from

| Thesis | File |
|---|---|
| Exp 1 paired deltas, localisation, kappa | `experiments/2026-10-04_joern_unified_five_judge/RESULTS.md`, `results/JOERN_UNIFIED_FIVE_JUDGE.json` |
| Exp 1 robustness rows (judges, generators, held-out) | `experiments/2026-09-23_five_judge_panel/RESULTS.json`, `results/CROSS_GENERATOR_v2.json`, `results/BOOTSTRAP_STATS_joern_parity.json`, `results/BOOTSTRAP_STATS_confirmatory_clean.json` |
| Exp 2 detection, per-band table, contrasts | `experiments/2026-09-23_five_judge_panel/RESULTS.json`, `experiments/2026-07-05_injection_exp2/out/manifest.json` |
| Exp 2 component and noise controls | `results/EXP2_FEATURE_ABLATION.md`, `experiments/2026-09-19_joern_replace_grep/context_ablation/RESULTS_SIGNAL_NOISE_V3.md`, `results/TEST_ORACLE.md` |
| Human study | `experiments/2026-07-06_user_study_prs/RESULTS_HUMAN_V4.md` |
| Figures | regenerated by `python3 scripts/generate_thesis_figures.py` into `thesis/figures/` |

## Re-running the analyses (no API keys)

All per-judge verdicts, reviews and oracle outputs are stored, so every
statistic in the thesis can be recomputed offline:

```bash
pip install -r requirements-eval.txt
```

| Experiment | Analysis from stored outputs |
|---|---|
| Exp 1 — headline (n = 35, five judges) | `python3 scripts/assemble_joern_five_judge.py` → `results/JOERN_UNIFIED_FIVE_JUDGE.*` |
| Exp 1 — paired effects, bootstrap, permutation | `python3 scripts/bootstrap_stats.py` (see `--help` for the panel file) |
| Exp 1 — criterion localisation | `python3 scripts/analyze_criterion_concentration.py` |
| Exp 1 — judge sensitivity, independent panel | `python3 scripts/recompute_panel_leave_one_out.py`, `python3 scripts/analyze_independent_judge_panels.py` |
| Exp 1 — substitute generators, parity run | `python3 scripts/compare_generators_v2.py`, `python3 scripts/analyze_joern_parity_run.py` |
| Exp 2 — detection rates, per-band table, McNemar | `python3 scripts/assemble_five_judge_panels.py` → `experiments/2026-09-23_five_judge_panel/RESULTS.*`; `experiments/2026-07-05_injection_exp2/harness/stats.py` |
| Exp 2 — component and test-oracle probes | `python3 scripts/analyze_exp2_feature_ablation.py`, `python3 scripts/analyze_test_oracle.py` |
| Human study | `python3 experiments/2026-07-06_user_study_prs/analyze_responses.py responses.csv` (`--selftest` runs on synthetic data) |

## Re-running the experiments (API keys required)

| Experiment | Entry points | Cost / time (documented in each folder) |
|---|---|---|
| Exp 1 — generate the four arms and judge them | `dataset_v2/scripts/regenerate_reviews_v2.py`, `experiments/2026-09-19_joern_replace_grep/run.py` (KG arm), `scripts/evaluate_reviews.py`, `scripts/rejudge_with_external_judge.py`, `scripts/rejudge_exp1_independent_panel.py` | see `reproduce.sh` |
| Exp 2 — inject, build contexts, generate six arms, adjudicate | `experiments/2026-07-05_injection_exp2/harness/{inject,build_contexts,run_modes,judge}.py`, then `scripts/rejudge_exp2_detection.py` | `experiments/2026-07-05_injection_exp2/docs/` |
| Human study — build stimuli | `experiments/2026-07-06_user_study_prs/{build_evidence,generate_reviews,judge_reviews,build_answer_key,normalize_review_surfaces,assemble_study_draft}.py` | folder README |

Rebuilding the Joern graphs needs Joern and the repositories at the PR head
commits (`scripts/clone_source_repos.sh`; CPG binaries on Drive). Thesis
figures are a by-product: `python3 scripts/generate_thesis_figures.py`
redraws them from the result JSONs.

These runs call paid APIs and need a `.env` file, which is not in the
repository:

```bash
cp .env.example .env     # then fill in the keys below
source load_env.sh
```

| Variable | Used for | Needed when |
|---|---|---|
| `OPENAI_API_KEY` | generator `gpt-4o`, judge `gpt-4o`, embeddings `text-embedding-3-small` | any review generation, RAG index build, or judging |
| `GOOGLE_API_KEY` | judge `gemini-2.5-flash` | re-running the judge panel |
| `ANTHROPIC_API_KEY` | judge `claude-sonnet-4-5` | re-running the judge panel |
| `DEEPSEEK_API_KEY` | judge `deepseek-v4-pro` | re-running the judge panel |
| `XAI_API_KEY` | judge `grok-4.6` | re-running the judge panel |

Scripts fail loudly with `… environment variable required` if a key they
need is missing. See `reproduce.sh` and the README/DESIGN file inside each
experiment folder for cost and runtime. Rebuilding graphs from source
additionally requires Joern and the repositories at the PR head SHAs, which
are on Drive (see `DRIVE_UPLOAD_LIST.md`).

## Human study

Everything that ran is in `experiments/2026-07-06_user_study_prs/`:

| | |
|---|---|
| Stimuli | `evidence/`, `reviews/` (12 frozen reviews), `answer_key.json` |
| Deployed UI (instrument r14) | `pilot/index.html`, `pilot/study_data.json` |
| Submission webhook | `deploy/apps_script_webhook.gs` (Apps Script v5; hosting and data path in `deploy/README.md`) |
| Pre-registration | `ANALYSIS_PLAN.md`, `POWER_ANALYSIS.md` |
| Analysis | `analyze_responses.py` (`--selftest` runs without data) → `RESULTS_HUMAN_V4.{md,json}` |

Raw responses and the rater pseudonym map are personal data and are not in
this repository; the committed results are aggregated and pseudonymised
(`P01…P27`).
