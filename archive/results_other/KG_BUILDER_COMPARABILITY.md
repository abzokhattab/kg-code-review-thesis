# KG builder comparability (additional analysis)

Does not replace Tables 6.1–6.5 or any headline number. Not a clean
confirmation of the lexical headline. Produced 2026-09-07.

**Scripts.** `scripts/analyze_joern_parity_run.py` (mtime 2026-09-03) assembled
the n=35 panel; `scripts/bootstrap_stats.py` (mtime 2026-09-03) was re-run
2026-09-07 onto `results/BOOTSTRAP_STATS_joern_parity_confirmatory.{md,json}`.
`vs_baseline` and `by_mode` are byte-identical to
`results/BOOTSTRAP_STATS_joern_parity.json` (seed 2026, B_boot=10 000,
B_perm=20 000). `scripts/measure_ast_resolver_precision.py` measured the human
study's AST import resolver. Joern 4.0.530 (`gosrc2cpg`). No model calls.

---

## Task 1 — Five missing pull requests

Source of the n=35 row in Table 6.6 / `tab:exp1-robustness`: the body-parity
Joern run `experiments/2026-06-11_joern_normal_prompt_parity`, whose kg scores
cover 35 of 40 dataset PRs. The five absences are exactly the PRs whose CPG
export produced no METHOD nodes in
`experiments/2026-05-15_joern_kg_main/progress_full40.json`.

| PR ID | GitHub | Repo | Language | Failure type | Cause |
|---|---|---|---|---|---|
| 9 | grafana/grafana#98123 | grafana/grafana | Go | empty graph | `joern-parse --language golang` wrote a 7.9 KB CPG; export has FILE / NAMESPACE / META_DATA only, no METHOD nodes (`export_pr9`: "No METHOD nodes in export", 2026-05-16T00:32:57Z) |
| 27 | grafana/grafana#124099 | grafana/grafana | Go (+ one TypeScript file) | empty graph | Same: 7.9 KB CPG, FILE/NAMESPACE only (`export_pr27`) |
| 35 | grafana/grafana#124598 | grafana/grafana | Go | empty graph | Same (`export_pr35`) |
| 36 | grafana/grafana#124593 | grafana/grafana | Go | empty graph | CPG is a symlink to PR35's 7.9 KB bin; same empty export (`export_pr36`) |
| 37 | grafana/grafana#124572 | grafana/grafana | Go | empty graph | CPG is a symlink to PR35's 7.9 KB bin; same empty export (`export_pr37`) |

An earlier 10-PR pilot (`experiment_log.txt`) failed PR9 and PR37 inside
`GoCpgGenerator.goSrc2CpgGenerate` when the Go toolchain was absent. The
full-40 run that actually determined n=35 got past parse and failed at export:
the graph existed but contained no methods. FILE nodes in those exports are
placeholders (`<empty>`, language `<unknown>`).

---

## Task 2 — Bounded fix attempt

Shared root cause: Joern 4.0.530's Go frontend (`gosrc2cpg`) does not emit
METHOD nodes, so the call-graph extractor in
`experiments/2026-05-15_joern_kg_main/run_full_40.py` cannot build a usable
evidence pack.

**What was tried (2026-09-07).** Go 1.26.3 is now installed. A two-function
hello-world (`package main`; `Hello` + `main`) was parsed with the same
`joern-parse --language golang` binary. Result: 7.9 KB CPG, 4 nodes (FILE,
META_DATA, NAMESPACE, NAMESPACE_BLOCK), **no METHOD nodes**, parse+export in
9 seconds. That is the same skeleton as the five Grafana CPGs, so the failure
is not flakiness, a timeout ceiling, or a missing `go` binary.

**Decision: documented as a genuine tool limitation.** No patch was applied.
Forcing n=40 by swapping in grep edges, a different Joern version, or an
unrelated Go frontend would mix builders inside the kg arm and bias the
comparability contrast. Producing reviews for the five would also cost API
calls the confirmatory brief does not authorise.

**Time spent on Task 2:** approximately 20 minutes (artefact inspection + one
hello-world re-parse). Stopped.

Final sample: **n = 35/40**.

---

## Task 3 — Comparability tables (same pipeline as Tables 6.1 / 6.2)

Input: `results/checklist_evaluation_llm_multi__joern_parity.json`.
Re-run: `python3 scripts/bootstrap_stats.py --in … --seed 2026`.
Only the baseline-versus-kg contrast is a CPG measurement. rag and hybrid
are carried from the lexical headline panel on the same 35 PRs
(`analyze_joern_parity_run.py`).

**Not a clean confirmation.** The KG-relevant subscale went from +0.60
(p = 0.007, n = 40, lexical; `results/BOOTSTRAP_STATS_v2.md`) to +0.34
(p = 0.111, n = 35, CPG; `results/BOOTSTRAP_STATS_joern_parity_confirmatory.md`).
Direction replicates under the CPG builder, but both magnitude and significance
attenuate at n = 35 — consistent with the sensitivity already flagged in
Chapter 8 (Conclusions) regarding the prompt-asymmetry correction
(`sec:results-exp1-builder`). The effect size nearly halved; underpowered n is
not the reading.

### Per-mode means (format of Table 6.1)

| Mode | n | Total /25 [95 % CI] | KG-relevant /9 [95 % CI] |
|---|---:|---:|---:|
| baseline | 35 | 8.94 [8.49, 9.43] | 5.00 [4.66, 5.31] |
| kg (CPG) | 35 | 9.57 [9.03, 10.09] | 5.34 [5.00, 5.66] |
| rag (carried) | 35 | 9.91 [9.40, 10.46] | 5.43 [5.03, 5.86] |
| hybrid (carried) | 35 | 9.89 [9.43, 10.34] | 5.60 [5.31, 5.89] |

### Paired Δ vs baseline (format of Table 6.2)

| Mode vs baseline | n | Total Δ [95 % CI] | p | d_z | KG-rel Δ [95 % CI] | p | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| **kg (CPG)** | 35 | +0.63 [+0.00, +1.26] | 0.077 | +0.32 | +0.34 [−0.03, +0.71] | 0.111 | +0.30 |
| rag (carried) | 35 | +0.97 [+0.34, +1.60] | 0.006 | +0.51 | +0.43 [+0.00, +0.89] | 0.086 | +0.32 |
| hybrid (carried) | 35 | +0.94 [+0.26, +1.60] | 0.015 | +0.46 | +0.60 [+0.23, +1.03] | 0.008 | +0.49 |

Source: `results/BOOTSTRAP_STATS_joern_parity_confirmatory.md`. Licensed
contrast is the kg row.

---

## Task 4 — AST import resolver precision

Census of every displayed `dependent_files` edge in the six human-study packs
(`experiments/2026-07-06_user_study_prs/evidence/*_evidence.json`). n = 47.
Headline quantity: does the flagged file import a function the diff added or
modified (`ImportFrom` of a changed def). That is the check that can sit next
to lexical precision. Source: `results/AST_RESOLVER_PRECISION.md`.

| Builder | n edges | confirmed | precision |
|---|---:|---:|---:|
| lexical grep (40-PR set, stem-in-import) | 177 checked | 18 | **10.2%** |
| AST import resolver (human study, function-reach) | 47 | 9 | **19.1% (9/47)** |

The 10.2% row is quoted from `results/BUILDER_VOLUME_PRECISION.md` (18/177),
not recomputed. The 19.1% row is 9 confirmed / 47 in
`results/AST_RESOLVER_PRECISION.md` ("ImportFrom of a changed function").

The resolver's own `ast.Import` / `ast.ImportFrom` filter confirms 47/47
(100%). That is a construction-consistency check, not a relevance measure:
the resolver emits an edge only after that parse already succeeded, so the
check cannot return anything but 100% and is not comparable to the lexical
10.2%.

---

## What this does not establish

No single builder was evaluated end-to-end across all three roles (Experiment 1
headline, Experiment 2 injection, human study). The CPG numbers above are the
Experiment 1 prompt-parity re-score of Joern on 35 parsable PRs, not a
replication of Experiment 2, and they attenuate rather than confirm the
lexical headline. The 19.1% figure is the human study's resolver on its own
six Python packs, not the tree-sitter builder of the 40-PR volume study.
