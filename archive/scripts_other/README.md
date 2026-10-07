# Scripts not used by the final thesis

Scripts from retired experiments and early controls. They run against
artefacts that are themselves archived (`../results_other/`) or on Drive, and
nothing in `../../results/` or `../../thesis/` depends on them.

| Scripts | What they were for |
|---|---|
| `run_concise_prompt_experiment.py`, `judge_parallel.py`, `analyze_snr.py`, `evaluate_review_snr.py`, `filter_divergent_review_pairs.py`, `check_judge_length_bias.py` | Concise-prompt / signal-to-noise controls (`SNR_*`, `JUDGE_LENGTH_BIAS`) |
| `run_priming_placebo_v2.py`, `compare_kg_empty_priming.py`, `generate_kg_empty_control.py` | Prompt-priming placebo controls |
| `run_ablation_study.py`, `analyze_section_ablation_3judge.py`, `decompose_kg_effect_by_edges.py`, `attribute_kg_wins.py`, `measure_offdiff_grounding.py` | Early rubric-level ablations and win attribution (three-judge era) |
| `build_kg_evidence.py`, `evaluate_ast_vs_grep.py`, `compare_kg_methods.py`, `compare_kg_builder_volume_precision.py`, `measure_ast_resolver_precision.py`, `scope_ast_evidence.py`, `generate_ast_kg_reviews.py` | Lexical vs AST builder comparisons, superseded by the Joern CPG builder |
| `evaluate_reviews_graded.py` | Graded-scale pilot (`evaluate_completeness.py` is in `../scripts_superseded/`) |
| `evaluate_budgeted_fusion_retrieval.py`, `evaluate_graph_constrained_fusion.py` | Fusion follow-ups that returned NO-GO |
| `screen_pr_crossfile_fanout.py`, `build_human_study_pr.py`, `prepare_human_study.py`, `simulate_rater_v3.py`, `rater_walkthrough_v2_vs_v3.py`, `smoke_test_webhook.sh` | Earlier (v3) human-study tooling |
| `generate_paper_figures.py`, `generate_paper_tables.py` | Conference-paper draft artefacts (`../paper/`) |
