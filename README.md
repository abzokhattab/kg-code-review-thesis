# Knowledge-Graph-Augmented LLM Code Review — thesis replication package

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
| `experiments/2026-09-19_joern_replace_grep/` | Experiment 1 KG arm: Joern CPG evidence packs, the 35 KG reviews, judge scores, and the context-relevance (noise / relevant-only) control (`context_ablation/`) |
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

## Reproducing

Everything in `results/` and `experiments/*/RESULTS*` is already computed;
re-running statistics and figures needs no API keys:

```bash
pip install -r requirements-eval.txt
python3 scripts/generate_thesis_figures.py            # all thesis figures from the result JSONs
python3 scripts/assemble_five_judge_panels.py        # five-judge aggregation from stored per-judge votes
python3 experiments/2026-07-06_user_study_prs/analyze_responses.py --selftest
```

Re-generating reviews or re-judging them calls paid APIs and needs a `.env`
file, which is not in the repository:

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

## Human-study data

Raw responses and the rater pseudonym map are personal data and are not in
this repository. The committed results are aggregated and pseudonymised
(`P01…P27`). The analyser (`analyze_responses.py`) reads a local CSV export
and reproduces `RESULTS_HUMAN_V4.*` from it.
