# One-page era guide — which numbers belong together

_Read this before citing any number from `results/`. The project went through
three experimental eras whose numbers are **not interchangeable**: they differ
in dataset, KG builder, judge panel, and active-criteria count. Mixing them is
the single most common error an AI assistant (or tired author) makes with this
repository._

## Era 1 — "v1" (Jan–Apr 2026) — DO NOT CITE IN THE THESIS

- 25 PRs, 4 repos; grep-based KG; early evidence packs.
- Files: everything **without** a `__v2`/`joern` suffix, e.g.
  `checklist_evaluation_llm.json`, `BOOTSTRAP_STATS_gpt4o_25pr.md`.
- Superseded by v2 after data cleaning (empty PR bodies, evidence defects).
- Per `thesis-context/CLAUDE.md`: **"25 PRs" and any v1 number are banned**
  from thesis text.

## Era 2 — "v2" (May 2026) — 4-mode experiment

- **40 merged PRs, 5 repos** (grafana 13, kafka 8, scikit-learn 8, godot 6,
  jenkins 5). Evidence: `data/luca_prs_v2/`.
- Modes: baseline / kg / rag / hybrid. KG builder: grep-based (sensitivity:
  scoped-AST variant is *smaller*, `SENSITIVITY_v2_grep_vs_ast.md`).
- Judges: **gpt-4o-mini + gpt-4o + gemini-2.5-flash**, majority vote, ties→0.
- Rubric: 25 criteria, **9 KG-relevant** (F3 F4 T1 T2 T3 M1 M3 C2 Q2).
- Headline (`BOOTSTRAP_STATS_v2.md`): KG-relevant Δ vs baseline
  **kg +0.60 [+0.23,+0.97], p=.007, d_z=.47**; hybrid +0.53 (p=.008);
  rag +0.42 (p=.057). Total-score Δ: rag +0.88 (p=.007), hybrid +0.72
  (p=.037), kg +0.62 (p=.054).
- Files: `*__v2*`, `BOOTSTRAP_STATS_v2.*`, `KRUSKAL_BONFERRONI_v2.*`.

## Era 3 — "Joern" (June 2026) — CPG-KG experiment — ⛔ HEADLINE RETRACTED

- Same 40-PR dataset, **n=35** (5 Go PRs excluded — Joern has no Go frontend).
- KG builder: **Joern code property graph** (callers + tests).
- Judges changed: **gpt-4o + gemini-2.5-flash + gemini-2.0-flash**.
- Rubric re-based: 10 dead criteria removed → **15 active, 6 "KG-active"**
  (C2 F3 F4 M1 T2 T3). Denominators are /6, not /9 — never compare to era-2 /9.
- Files: `*joern*`, `FINAL_RESULTS_REPORT.md`, `JOERN_RESULTS_v2.md`.

**⛔ Do not cite +1.743/6, d_z=+1.24, p<.0001, W/T/L 28/6/1, or the
Gemini-generator d_z=+1.34. Those numbers are artefacts of a prompt
asymmetry, not measurements of the CPG builder.** The era-3 KG arm received a
prompt the baseline did not, so the contrast measured builder *plus* prompt.
Re-running the same builder with the prompt held at parity
(`results/BOOTSTRAP_STATS_joern_parity.md`, n=35) gives:

| Mode vs baseline | Total Δ [95% CI] | p | d_z | KG-rel Δ [95% CI] | p | d_z |
|---|---:|---:|---:|---:|---:|---:|
| kg (Joern, parity) | +0.63 [+0.00, +1.26] | 0.077 | +0.32 | +0.34 [-0.03, +0.71] | 0.111 | +0.30 |
| rag | +0.97 [+0.34, +1.60] | 0.006 | +0.51 | +0.43 [+0.00, +0.89] | 0.086 | +0.32 |
| hybrid | +0.94 [+0.26, +1.60] | 0.015 | +0.46 | +0.60 [+0.23, +1.03] | 0.008 | +0.49 |

At parity the Joern KG arm is **not significant on either metric**. A "large,
p<.0001" effect became a null one when a single confound was removed, which is
why the retracted numbers are listed here explicitly rather than quietly
deleted: anyone who finds them in an older file needs to land on this note.

## ✅ Resolved: which era is the canonical RQ2 headline

**Era 2.** This was previously logged as a pending supervisor decision between
era 2 (+0.60/9) and era 3 (+1.743/6). The parity re-run above settles it: era
3's advantage was a prompt artefact, so there was never a real choice between
a "modest" and a "large" estimate. Era 2 is the RQ2 headline, and era 3 now
serves only as the graph-builder comparison, reported at parity.

The causal claim for structural context rests on **Experiment 2**
(`results/INJECTION_EXP2_RESULTS.md`: baseline 0/28, deployed Joern KG 15/28,
oracle-scored, pre-registered), not on any era-1/2/3 judge score.

## Era-independent mechanism probes (safe to cite alongside either era)

| Probe | File | Result |
|---|---|---|
| Bug-injection (8 cross-file renames, sklearn) | `exceptional test/prototype/FINDINGS_SCALE.md` | baseline 0/8 · RAG 1/8 · idealised AST-KG 8/8 · **deployed Joern-KG 4/8** (inheritance edges missing) |
| Empty-KG priming control | `CHECKLIST_EVALUATION_REPORT__kgempty_priming.md` | ⚠ **does not** isolate priming from KG content: 5 PRs, era-crossed. Not citable as a positive claim, and the thesis deliberately says nothing about priming. |
| Cross-generator (4 generators, 40 PRs) | `CROSS_GENERATOR_v2.md` | **supersedes** the 5-PR Claude probe. kg /9: gpt-4o +0.60 (p=.007) but claude-haiku-4.5 +0.15 (p=.457), gemini-2.5-flash +0.47 (p=.136), deepseek-v3 +0.20 (p=.383). The effect is gpt-4o-specific; other baselines score higher and are more verbose. |
| KG-relevant label audit | `RUBRIC_KAPPA_kg_relevant.md` | independent re-annotation κ=0.615 |
| Graded 0–3 scale pilot | `GRADED_SCALE_RESULTS.md` | binary-ceiling check, 27 KG-rich PRs |
| Off-diff grounding count | `OFFDIFF_GROUNDING.md` | mode-level citation of off-diff facts |

## Human-study eras

- **v3** (June 2026, `human_eval_v3/`): 6 PRs from sklearn/kafka/jenkins/
  grafana. Deployed but found too hard for raters (unverifiable references).
- **v4** (July 2026, `experiments/2026-07-06_user_study_prs/`): 6 Python PRs
  (requests/flask/click ×2 each) + per-reference verification badges +
  pre-registered F3* primary endpoint, 27 raters. **Current, and complete.**
  Note: its 6 stimuli are *not* part of the 40-PR RQ2 sample, and its KG
  builder is an AST import resolver (recorded in evidence metadata), not Joern.
  Analysed **only** by `experiments/2026-07-06_user_study_prs/analyze_responses.py`.
- ⛔ `scripts/analyze_human_study_v4.py` is a superseded analyser whose only
  committed output (`results/SYNTHETIC_*`) is **fabricated dry-run data**. It
  has never been run on real responses. Never cite it.
