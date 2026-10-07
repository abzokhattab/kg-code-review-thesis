# Earlier result files (not used by the final thesis)

Every result artefact produced during the project that the final thesis does
**not** cite and no thesis script reads. Kept so the trajectory can be
audited; do not quote numbers from here as current.

Rough map of what is in this folder:

| Pattern | Era | Why superseded |
|---|---|---|
| `*_18pr*`, `*_25pr*`, `25_PRS_*`, `LUCA_*`, `EVALUATION_REPORT_2026-01-29*`, `evaluation_results_2026-01-29.csv` | v1 (Jan–Mar 2026), 18–25 PRs | Contaminated v1 dataset; replaced by v2 (see `../../dataset_v2/docs/AUDIT_v1.md`) |
| `BOOTSTRAP_STATS_v2_*`, `KRUSKAL_BONFERRONI_v2*`, `checklist_evaluation_llm*__v2_*`, `CHECKLIST_EVALUATION_REPORT*` | v2 lexical builder, n = 40, three-judge panel | Replaced by the Joern CPG builder (n = 35) and the five-judge panel |
| `BOOTSTRAP_STATS_joern.*`, `JOERN_RESULTS*.md`, `KG_METHOD_COMPARISON*`, `KG_V3_*`, `EXPERIMENT_PLAN_kg_v3.md`, `EXP_C_*` | Joern pilots (May–June 2026) | Replaced by `experiments/2026-09-19_joern_replace_grep` and the unified five-judge aggregation |
| `BOOTSTRAP_STATS_gpt4o*`, `*_claude_5pr*`, `*_gpt4omini*`, `*fullkg16*`, `*scoped_ast*`, `SENSITIVITY_v2_grep_vs_ast.md`, `ast_vs_grep_comparison.json` | Small-sample sensitivity runs | Directional only; not reported |
| `GRADED_*`, `graded_cache/`, `REFINED_SUBSCALE_RESULTS.md` | Graded 0–3 scale pilot | Not part of the thesis |
| `SNR_*`, `snr_cache/`, `*concise*`, `JUDGE_LENGTH_BIAS.md`, `PRIMING_PLACEBO_v2.md`, `KG_EMPTY_PRIMING_CONTROL.md`, `*kgempty*`, `*deleted_deps*`, `*deleted_tests*`, `SECTION_ABLATION_3JUDGE*`, `ablation_*` | Early controls and ablations | Replaced by the Experiment 2 component and relevance controls |
| `INJECTION_EXP2_RESULTS.md`, `RAG_FAILURE_ANALYSIS_EXP2.md` | Experiment 2 under the original three-judge prompt | Replaced by the two-stage adjudication and five-judge rates in `experiments/2026-09-23_five_judge_panel` |
| `human_llm_agreement*`, `HUMAN_STUDY_*`, `POWER_human_study_criteria.md`, `RATER_WALKTHROUGH_*`, `POWER_ANALYSIS.md` | Earlier (v3) human-study design | Replaced by `experiments/2026-07-06_user_study_prs` |
| `*_WIN_ATTRIBUTION.md`, `OFFDIFF_GROUNDING.md`, `KG_EDGE_PRESENCE*`, `BUILDER_VOLUME_PRECISION*`, `AST_RESOLVER_PRECISION*`, `KG_BUILDER_COMPARABILITY.md`, `V1_VS_V2_*`, `MODERATION_*`, `SUBGROUP_*`, `DIVERGENCE*`, `divergence_filter.json` | Supporting analyses | Informative during the project; not cited in the final text |
| `ERA_GUIDE.md`, `EVIDENCE_DIGEST.md`, `THREATS_TO_VALIDITY.md`, `DISCUSSION.md`, `METHODOLOGY_AND_FINDINGS.md`, `FINAL_RESULTS_REPORT.md`, `PROGRESS_REPORT.md`, `THESIS_COMPARISON_REPORT.md`, `DATA_MANIFEST.md`, `RESULTS_LATEX.tex`, `thesis_table.tex`, `*.html` | Working notes and drafts | Superseded by the thesis text |
| `run2_*/`, `ablation_3judge/` | Per-run caches | Not needed |
