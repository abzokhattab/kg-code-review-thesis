# Joern CPG construction stage (Experiment 1 graph builder)

This folder is the **upstream graph stage** of the Experiment 1 KG arm. The
review results it produced in May 2026 are superseded (see the one-line
`RESULTS*.md`), but its graph construction code and output are what the
final pipeline consumes.

| File | Role |
|---|---|
| `run_experiment.py` | Per PR: `joern-parse` the repository at the head SHA into a CPG, `joern-export` it, `extract_call_graph()` runs the exact-name caller/callee queries over the changed methods, and `build_evidence()` writes the enriched evidence pack (`metadata.joern_enriched = true`, caller and function counts recorded). |
| `run_full_40.py` | Driver over the 40 PRs; the five Go-only PRs fail at the Joern frontend and are excluded, leaving 35. |
| `exp_a_fix_testonly_cpg.py`, `exp_b_*.py`, `exp_c_*.py`, `exp_gpt4o_joern.py`, `fix_failures.py` | Pilot variants and repairs from May–June 2026; not used by the thesis. |
| `evidence/` | The 36 Joern-enriched evidence packs (`pr*_evidence.json`) with `callers` and `functions_in_changed_files`. **Consumed by** `../2026-09-19_joern_replace_grep/run.py`, which turns the caller files into the KG block's dependent list and generates the 35 KG reviews scored in the thesis. |
| `pr_config.json`, `progress*.json`, `*_log.txt` | Run configuration and logs. |

Not in the repository (on Drive, see `../../LARGE_ASSETS.md`): `cpgs/`
(CPG binaries, 1.0 GB), `exports/` (Neo4j-CSV exports, 6.5 GB), `cache/`.
Rebuilding them requires Joern and the repositories at the PR head SHAs.
