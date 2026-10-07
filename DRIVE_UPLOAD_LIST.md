# Artefacts not in this repository (too large for GitHub)

These are available on Drive under the same relative paths as the lab
repository (e.g. `experiments/2026-05-15_joern_kg_main/exports/`).

**Drive folder:** _link to be added_ Nothing in the thesis *depends* on them being here: every
number is recomputable from the JSON/Markdown result files that are in this
repository. They are needed only to re-run generation or re-build graphs from
scratch.

| Path (source machine) | Size | What it is | Needed for |
|---|---:|---|---|
| `experiments/2026-07-05_injection_exp2/out/rag/` | 461 MB | Embedding indices (kafka, grafana, sklearn) for the RAG arm of Experiment 2 | re-running `harness/run_modes.py` for the `rag`/`hybrid` arms |
| `experiments/2026-07-05_injection_exp2/harness/workspace/` | 49 MB | Checked-out repository scopes at injection SHAs | re-running injection + Joern CPG build |
| `experiments/2026-09-19_joern_replace_grep/context_ablation/workspace/` | 49 MB | Repository scopes for the context-relevance (noise) control | re-running the noise/relevant-only arms |
| `experiments/2026-07-06_user_study_prs/pr_hunt/repos/` | 31 MB | Clones of candidate Python repos used to select the six human-study PRs | re-running PR selection only |
| `experiments/2026-05-15_joern_kg_main/{exports,cpgs,cache}/` | 7.5 GB | Joern CPG binaries, exported query results and caches for the 35 PRs. The query code and the 36 resulting evidence packs (`evidence/`) **are** in the repo; only the binaries are here | rebuilding the CPGs or re-running the CPGQL queries |
| `experiments/2026-05-15_joern_kg/` | 173 MB | Superseded Joern pilot (May 2026) | historical only |
| `archive/experiments/2026-09-19_budgeted_fusion_retrieval/RESULTS*.json` | 49 MB | Per-budget retrieval traces for the NO-GO fusion study (Markdown summaries are in the repo) | re-plotting only |
| `repos/`, `luca_repos/` | 7.5 GB | Source repositories checked out at the 40 PR head SHAs | rebuilding evidence packs / CPGs |
| `data/` (other than `luca_prs_v2`) | ~2.5 GB | v1 and intermediate datasets (v1 is contaminated; see `dataset_v2/docs/AUDIT_v1.md`) | historical only |
| `workspace/` | 927 MB | Scratch working directory | none |

Private, never uploaded anywhere: `RATER_PSEUDONYM_MAP.txt` and the raw
Google-Sheets export of human-study responses (`Human Eval (N).xlsx`). The
analyser reads the export locally; the committed `RESULTS_HUMAN_V4.{md,json}`
contain only aggregated, pseudonymised results.
