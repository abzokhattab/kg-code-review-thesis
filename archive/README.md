# Archive

Material that is **not** cited by the thesis in its final form, kept so the
project history can be navigated. Nothing here should be used to reproduce a
thesis number; the current pipeline is under `../experiments/`, `../scripts/`
and `../results/`.

| Folder | What it is | Why it is archived |
|---|---|---|
| `scripts_superseded/` | Earlier analysers and one-off scripts | Replaced by the scripts in `../scripts/`. `analyze_human_study_criteria.py` and `analyze_human_study_v4.py` target earlier study designs; `*_14criteria.py` belong to an abandoned 14-criterion rubric; `expand_dataset.py` is the v1 fetcher with the 15 kB diff-cap bug that motivated the v2 dataset. |
| `experiments/2026-06-11_joern_normal_prompt/` | First Joern run with an unmatched prompt | Superseded by the parity run (`../experiments/2026-06-11_joern_normal_prompt_parity/`) and then by `2026-09-19_joern_replace_grep`. |
| `experiments/2026-09-19_budgeted_fusion_retrieval/` | Zero-cost gate for a graph + semantic fusion follow-up | Result was NO-GO; not part of the thesis. Large JSON traces are on Drive. |
| `experiments/2026-09-20_graph_constrained_fusion/` | Second fusion gate | NO-GO; not part of the thesis. |
| `experiments/human_study_reviews/` | Review stimuli for the earlier (v3) human study on sklearn/kafka/jenkins/grafana PRs | Replaced by the Python stimuli in `../experiments/2026-07-06_user_study_prs/`. |
| `human_eval_v3/`, `human_eval_v3_clean_2026-06-11/` | UI and build scripts of the earlier human-study iteration | Replaced by the v4 study. |
| `run2_14criteria/` | Results from the abandoned 14-criterion rubric | Not cited. |
| `SYNTHETIC_*` | Dry-run outputs produced with `--sample` | Synthetic data, not human responses. |
| `paper/` | Conference-paper draft (Aug 2026) with its own integrity audit | Separate artefact; numbers predate the five-judge panel. |
| `reports/` | Dated progress reports and the interactive demo builder | Working notes. |
