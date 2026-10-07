# Plan — standalone conference paper on context-augmented LLM code review

**Created:** 2026-08-12. **Target:** Overleaf project `69898cd06b12a933baacf032`
(shared space; existing content to be archived, not co-authored).
**Style reference only:** `paper/2026-08-12/reference/main.tex`
(Mariotto et al., competency-based PR scoring — unrelated topic, IEEE
conference format).

---

## 1. What the paper is

A standalone IEEE-conference-format paper (8–10 pages) arguing that
**repository context shapes the quality of LLM-generated PR reviews, and
different context types contribute different things**. Exactly **two
experiments**, matching the plan confirmed on 2026-07-13
(`reports/2026-07-13/STATE_OF_THE_THESIS.md` §0).

Overarching question, matching the context-centric framing already agreed
with the supervisor (`reports/2026-07-20/SLACK_REPLY_RQ.md`):

> How does repository context shape the quality of LLM-generated pull-request
> reviews, and which kind of context contributes what?

| RQ | Question | Evidence |
|---|---|---|
| RQ1 | Does KG / RAG / hybrid context improve review quality over a diff-only baseline, and on which criteria? | Experiment 1 (observational, 40 PRs) |
| RQ2 | Is the KG advantage causally attributable to dependency knowledge rather than to context volume? | Experiment 2 (pre-registered injection; structural bands vs local-control placebo) |
| RQ3 | How far does the effect depend on the KG builder's edge coverage? | Experiment 1 builder sensitivity + Experiment 2 arm ladder |
| RQ4 | Do human reviewers perceive the difference? | **Placeholder only** — study live, data pending |

---

## 2. Resolved: which Experiment 1 numbers are canonical

`results/ERA_GUIDE.md` flags this as the open supervisor decision, but the
record already answers it: the Experiment 1 summary sent to the supervisor
(`reports/2026-07-13/EXPERIMENT_1_SUMMARY.{md,pdf}`, to which he replied
"no comments on these results") **is era 2** — 40 PRs, 5 repos, four modes,
the gpt-4o-mini/gpt-4o/gemini-2.5-flash panel, 25 criteria with a
pre-registered 9-criterion KG-relevant subset.

**Decision for the paper: era 2 is the headline.** It has full n=40, a
pre-registered rubric, no post-hoc instrument change, and it is what the
supervisor has already accepted.

**The Joern result becomes a builder-sensitivity subsection inside
Experiment 1, reported on the original 25-criterion rubric** — not on the
re-based 15/6-criterion instrument. On the same rubric and the same
denominators (`results/BOOTSTRAP_STATS_joern.md`, n=35):

| Builder | KG-relevant Δ /9 | p | d_z | Total Δ /25 | p |
|---|---:|---:|---:|---:|---:|
| grep-based (era 2, n=40) | +0.60 [+0.23, +0.97] | .007 | +0.47 | +0.62 [+0.05, +1.20] | .054 |
| Joern CPG (era 3, n=35) | +0.69 [+0.31, +1.09] | .003 | +0.58 | +1.17 [+0.54, +1.77] | .002 |

This framing has three advantages: it keeps the paper at two experiments,
it never quotes the post-hoc `+1.743/6` figure (so there is no re-based
rubric to defend), and it makes the builder change a *finding* that motivates
Experiment 2's arm ladder rather than a confound.

It also fixes a coherence problem that would otherwise bite in review:
**Experiment 1's headline KG is grep-based while Experiment 2's KG arm is
the deployed Joern CPG.** The sensitivity table above is what licenses
moving from one to the other, and RQ3 makes that transition explicit.

### Naming trap to avoid

`results/FINAL_RESULTS_REPORT.md` labels its own internal analyses
"Experiment 1 / 2 / 3", where its "Experiment 2" is a *generator-robustness
check*, not the injection study. That collision is part of what made the
project state feel contradictory. The paper uses Experiment 1 / Experiment 2
strictly in the `STATE_OF_THE_THESIS.md` §3 sense, and cites that report's
sub-analyses by name (generator robustness, KG-rich subgroup), never by
number.

---

## 3. Still open

### D1. The RAG = 5/28 claim is not backed by any artifact

You asked earlier to raise Experiment 2's RAG detection from 1/28 to 5/28,
citing an independent run. Current repository state:

- `results/INJECTION_EXP2_RESULTS.md` line 29 → `rag | 1/28 | 0.04 [0.00, 0.11]`
- `experiments/2026-07-05_injection_exp2/out/RESULTS.md` line 11 → same
- `reports/2026-07-13/EXPERIMENT_2_INJECTION_SUMMARY.md` line 49 → `RAG | 1/28`
- A repository-wide search finds **no file containing `5/28`**

No live contradiction exists in the files, and the supervisor-facing summary
says 1/28. The paper can only cite 1/28 unless that run's output is produced
and committed. Point me at it and I will reconcile the artifacts; otherwise
1/28 stands and the observation can appear as an unquantified note.

### D2. Venue, page limit, author list

The reference paper is IEEE conference format with HPI + Mercedes-Benz Tech
Innovation authors. I don't know your target venue, page budget, or whether
Adriano/Giese are co-authors here. The page limit decides how much of the
sensitivity material (§5 below) survives.

---

## 4. Section plan with source mapping

Every number carries a `(file §section)` citation in the draft, per
`thesis-context/CLAUDE.md`.

| Section | Content | Sources |
|---|---|---|
| Abstract | Structured tags ([Background]/[Aims]/[Methods]/[Results]/[Conclusions]) mirroring reference style | canonical claim in `thesis-context/CLAUDE.md` §"One-sentence claim" |
| 1. Introduction | Diff-only review as prevailing baseline; context as the lever; contributions | `reference/main.tex` for structure only |
| 2. Background & related work | Code review expectations, LLM-assisted review, RAG, KG/CPG, GraphRAG claims | `thesis/bibliography.bib` (24 entries — insufficient, see §6) |
| 3. Approach | Four modes; KG construction; RAG index; evidence-pack assembly; prompts | `prnote/note.py`, `prnote/kg.py`, `prnote/rag.py`, `prnote/evidence.py`, `prnote/hybrid.py` |
| 4. Experiment 1 — design | 40 PRs / 5 repos selection; rubric provenance; 3-judge panel; majority vote | `dataset_v2/scripts/find_fifteen_more_prs.py`, `results/RUBRIC_PROVENANCE.md`, `scripts/evaluate_reviews.py` |
| 5. Experiment 1 — results | Per-mode means + CIs; paired Δ; κ = .59–.72; win attribution | `results/BOOTSTRAP_STATS_v2.md`, `results/KG_WIN_ATTRIBUTION.md` (+24 on the 9 dependency criteria vs +1 on the other 16), `results/RAG_WIN_ATTRIBUTION.md` |
| 5b. Experiment 1 — builder sensitivity | grep vs Joern on the original rubric (§2 table) | `results/BOOTSTRAP_STATS_joern.md` |
| 6. Experiment 2 — design | Pre-registration; 40 injections (28 structural / 12 local control); 6 arms; direction-blind discovery | `experiments/2026-07-05_injection_exp2/docs/DESIGN_AND_PREREGISTRATION.md`, `harness/inject.py`, `harness/operators.py` |
| 7. Experiment 2 — results | Structural detection 0/28 → 15/28 → 21/28 → 26/28; local-control parity −0.08 inside [−.15,+.15]; S4 inheritance Δ +0.50; judge validation vs oracle | `results/INJECTION_EXP2_RESULTS.md`, `experiments/2026-07-05_injection_exp2/out/{RESULTS.md,JUDGE_VALIDATION.md}` |
| 8. Discussion | Complementarity; dilution (kg 15/28 > hybrid 12/28); builder-coverage mechanism; RAG floor effect; graph-population moderator; generator independence | `results/RAG_FAILURE_ANALYSIS_EXP2.md`, `results/FINAL_RESULTS_REPORT.md` §"Key Analytical Findings", `results/MODERATION_ANALYSIS_v2.md`, `reports/2026-07-20/SLACK_REPLY_FACTORS.md` |
| 9. Threats to validity | Construct/internal/external/judge threats | `results/THREATS_TO_VALIDITY.md` (19 kB, written against the v2/Joern state) |
| 10. Conclusion & future work | **Human study placeholder** — design stated, results marked pending | `experiments/2026-07-06_user_study_prs/ANALYSIS_PLAN.md` |

The human study gets a short stated-design paragraph plus an explicit
`[TODO: results pending]` marker, so the section can be filled the moment the
cohort completes without restructuring anything.

---

## 5. Discussion assets worth the space (page-limit dependent)

Three findings strengthen the mechanism argument beyond the two headline
results, all citable:

- **RAG floor effect** — Spearman r = −0.577, p = 0.0001 between baseline
  score and RAG delta: RAG is corrective, not additive
  (`results/FINAL_RESULTS_REPORT.md` §Finding 1).
- **Graph population is the moderator** — KG-poor PRs (n=9) give −0.11, n.s.;
  KG-rich (n=31) give +0.774, p = 0.001, d_z = +0.64 (§Finding 2). Explains
  why the full-sample effect is modest.
- **Generator independence** — GPT-4o d_z = +1.326 vs Gemini 2.5 Flash
  d_z = +1.340 on the same evidence, KG-relevant /9 (§"Experiment 2 —
  Generator robustness"; cite by name, not number).

---

## 6. Figures, tables, and the bibliography gap

`results/RESULTS_LATEX.tex` looks reusable but **is not**: its tables are
era-1 (14-criterion rubric, 25 PRs, GPT-4.1-mini and DeepSeek judges), which
`thesis-context/CLAUDE.md` §"Strict rules" bans. `thesis/figures/` is empty.
The only existing usable asset is
`exceptional test/prototype/figure_kg_builders.png`.

Planned artefacts, all generated from JSON rather than transcribed:

- **T1** Per-mode means with 95% bootstrap CI (Exp 1) — `BOOTSTRAP_STATS_v2.json`
- **T2** Paired Δ vs baseline with p and d_z (Exp 1) — same source
- **T3** Builder sensitivity, grep vs Joern on the original rubric — `BOOTSTRAP_STATS_joern.json`
- **T4** Structural-band detection by arm with CIs (Exp 2) — `out/results.json`
- **T5** Local-control parity table (Exp 2 placebo)
- **F1** Architecture diagram (four modes, evidence pack) — new, TikZ
- **F2** Win attribution: KG-relevant vs non-KG-relevant bands — `KG_WIN_ATTRIBUTION.md`
- **F3** Detection rate by arm, structural vs local — `out/results.json`
- **F4** Worked example: a cross-file defect the KG catches and the baseline misses — material in `reports/2026-06-22/demo.html`

One verb-first script under `scripts/` (repo convention) emits T1–T5 and
F2–F3, with a one-line entry added to `thesis-context/CODE_INDEX.md`.

**Bibliography:** `thesis/bibliography.bib` has 24 entries; the reference
paper's `references_paper.bib` has 58 but on competency/PR-description
topics, overlapping only on code-review classics
(`bacchelli2013expectations`, `mcintosh2014impact`). Coverage of RAG,
GraphRAG, code property graphs / Joern, and LLM-based review is largely
missing. I will not invent BibTeX; I will hand you a
`## Citations I need` list with titles and DOIs to approve.

---

## 7. Phased work sequence

### Status as of 2026-08-12

Phases 0–4 are done; a complete 7-page draft is on Overleaf (project
`69898cd06b12a933baacf032`, commits `d83baae` and `e70b9cf`). What changed
against the plan below:

- **Title:** "Graph Context, Not More Context: Isolating What Repository
  Structure Adds to LLM Code Review". The framing that survived contact with
  the data is *context shape beats context quantity*, with the aggregate-vs-
  capability gap as the methodological contribution.
- **Tables:** seven, not five — the configuration table (T7) was added because
  the two experiments' generation temperatures differ and that has to be
  visible, and the builder-sensitivity table earned its own place.
- **Figures:** F3 (the detection ladder plus placebo band) is in as Fig. 1,
  emitted as pgfplots rather than a raster. F1, F2, and F4 are not in yet:
  F2 would duplicate Table IV, and F1/F4 are worth adding only if the page
  budget allows.
- **MCP named projects (step 3):** skipped. Plain git over the Overleaf remote
  does everything needed, and editing `~/.cursor/mcp.json` would have required
  a Cursor reload to take effect — not worth breaking a working setup mid-run.
- **Human study:** not in the draft. It is live but unanalysed, so there is
  nothing citable yet; a marked TODO holds its place in Section VIII.

**Remaining before submission**

1. Venue, page budget, and the author list (the draft carries a single-author
   block and a TODO).
2. Bibliography gaps — the draft cites 20 of the 24 real entries and carries
   explicit TODO markers where a key is missing: the Joern / code-property-graph
   formulation, GraphRAG-style graph retrieval, mutation testing as the ancestor
   of the injection design, and ISO/IEC 25010. No key was invented.
3. A public or anonymised artefact link for the Data Availability section.
4. Decide the human study's fate once it has data.

### Original plan

**Phase 0 — setup (safe, reversible)**
1. Archive existing Overleaf content: tag the current commit and keep a local
   copy, so the previous paper is recoverable even though the space is shared.
2. Clone the target project into `paper/2026-08-12/draft/`.
3. Register both Overleaf projects as named projects in the MCP config so
   `read_file`/`write_section` can address them explicitly.

**Phase 1 — skeleton**
4. Replace `main.tex` with title/authors/abstract and empty sections, keeping
   `IEEEtran.cls`; remove the archived paper's `evaluation/images/` assets.
5. Push once; confirm it compiles on Overleaf.

**Phase 2 — methods**
6. Approach plus both experiment designs, written from source files.

**Phase 3 — numbers**
7. Build the table/figure generator; emit T1–T5, F2–F3.
8. Write both results sections against generated values only.

**Phase 4 — argument**
9. Discussion, threats, conclusion; introduction last, once findings are
   fixed.

**Phase 5 — references and polish**
10. Resolve the citation list; compile check; trim to page budget.

---

## 8. Boundaries I will hold

- No number enters the draft without a source path beside it.
- One era per table, always labeled (`results/ERA_GUIDE.md`); never mix the
  /9 and /6 denominators.
- No v1, 25-PR, or 14-criterion numbers; no `+1.743/6`.
- The Overleaf project is shared space: nothing is deleted there until the
  Phase 0 archive is verified.

**Archive verification (done 2026-08-12).** The previous document is recoverable
three ways before anything was overwritten: git tag
`archive/pre-rewrite-2026-08-12` and branch `archive-luca-paper` in
`paper/2026-08-12/draft/`, and a plain filesystem copy of all 25 files
(7.1 MB, including `evaluation/images/`) in
`paper/2026-08-12/archive-original-overleaf/`. Overleaf's remote accepts only
`main`, so the tag and branch are local; the filesystem copy is the durable one.
