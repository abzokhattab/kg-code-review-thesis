# Thesis writing plan

Last updated: 2026-08-18. Owner: Abdelrahman Khattab.
This file is the hand-off note between writing sessions. Update the status table
at the end of every session.

---

## 1. Current status

The empirical work is finished and audited; the document is not written.

**Existing assets available for reuse:**

| Asset | Location | Use |
|---|---|---|
| Final five-judge headline numbers | `experiments/2026-09-23_five_judge_panel/RESULTS.{md,json}` | Chapter 6 |
| Conference paper, ~3,700 words, compiles | `paper/2026-08-12/draft/main.tex` | Chapters 5–6 backbone |
| Seven generated result tables + one pgfplots figure | `paper/2026-08-12/draft/tables/`, `figures/` | Chapter 6 |
| Threats catalogue, 2,918 words | `results/THREATS_TO_VALIDITY.md` | Chapter 6 threats section |
| Seeded chapters 1–4, ~1,930 words | `thesis-context/thesis/chapters/` | Chapters 1–4 raw material |
| Approved exposé, ~4,970 words | `Expose-latex/.../main.tex` | Chapters 1–3 |
| Code-to-section map | `thesis-context/CODE_INDEX.md` | Chapter 4 |
| Frozen, pre-registered human-study design | `experiments/2026-07-06_user_study_prs/ANALYSIS_PLAN.md` | Chapter 5 |

**Remaining gaps, ordered by estimated effort:**

1. **Bibliography.** 33 unique entries; four cited keys have no entry at all. A
   thesis of this scope needs roughly two to three times that. This is the only
   task measured in weeks, so it runs in parallel from day one.
2. **Chapters 5–7 do not exist** in any form other than the conference paper.
3. **Chapters 1–4 exist but are stale** — seeded from the exposé, before results,
   and still say "25 PRs across four repositories".
4. **One open framing decision** (see §4) that blocks the introduction.

---

## 2. Writing order and rationale

Not chapter order. Artifact order: write what is already determined, so that
prose is never blocked on an unmade decision or an unfinished experiment.

1. **Chapter 5 — Experimental Design and Setup.** Every input is frozen: the
   dataset, the rubric, the judge panel, the statistical plan, the human-study
   design. Nothing here waits on the running study. Start here.
2. **Chapter 6 — Results and Discussion**, minus the human-study section. The
   numbers are audited and the tables are generated.
3. **Threats section.** Conversion of an existing draft, not new writing.
4. **Chapter 4 — Approach.** Requires reading the code, which is slower than it
   looks; `CODE_INDEX.md` is the map.
5. **Chapters 2 and 3 — Background and State of the Art.** Gated on the
   bibliography, which is why the bibliography starts in week one.
6. **Chapter 1 — Introduction** and the abstract. Written last, when the story
   is fixed.
7. **Chapter 7 — Conclusions.** Answers each research question in the words it
   was asked.

The human-study results section is the only part of the thesis that must wait,
and it is one section of one chapter.

---

## 3. Rules that apply to every writing session

Inherited from `thesis-context/CLAUDE.md`; repeated here because they are the
rules that get broken under time pressure.

- Every number carries its source path. No number is quoted from memory.
- The dataset is **35 PRs across five repositories** (five Go-only PRs excluded
  because Joern's Go frontend does not emit method-level nodes). Anything in
  `results/` presenting 25 or 40 PRs as a headline is superseded.
- gpt-4o is the **generator**; the final evaluation uses a five-model,
  multi-provider judge panel. Never call gpt-4o "the judge".
- Experiment 1 ran at T = 0.0, Experiment 2 at T = 0.0, and **no generation seed
  was ever sent**. Seed 2026 is the bootstrap/permutation seed.
- The final five-judge RAG detection rate in Experiment 2 is **5/28**;
  **1/28** belongs to the superseded original adjudication.
- The defensible framing is **complementarity**, not KG dominance.
- Judge-agreement values must be labelled by panel. The separate value
  $\kappa=0.615$ concerns re-annotation of the KG-relevant tag, not review
  scoring.
- Never invent a BibTeX entry. Missing citations are listed, not fabricated.

---

## 4. Open decisions

| # | Decision | Blocks | Status |
|---|---|---|---|
| D1 | Research-question numbering. | Ch. 1, Ch. 5 §RQs, Ch. 7 | **Resolved 2026-09-26: three flat RQs — see §4.1** |
| D2 | Where the injection experiment lives. | Ch. 5, Ch. 6 | **Resolved as RQ2**; scope addition should be disclosed |
| D3 | Human-study scope. The exposé promises validating the LLM judge against humans; the deployed study tests targeted practitioner preference. | Ch. 5 §human study, Ch. 6, Ch. 7 | **Resolved as RQ3**; narrower scope should be disclosed |
| D4 | How component analyses are represented in the RQ structure. | Ch. 6 | **Resolved as supporting evidence for RQ2, not a separate RQ** |
| D5 | Title, degree programme, hand-in date, second reviewer, German title. | `thesis.tex` | **Resolved in the title-page metadata** |
| D6 | How to name Experiment 1's graph block, given that it is built by basename search rather than by parsing. | Ch. 4, Ch. 5 §setup, Ch. 6 §sensitivity, paper | **Resolved 2026-08-18: keep the name `kg`, disclose the construction** — see §4.2 |

### 4.2 Experiment 1 context block uses lexical matching (2026-08-18)

Found while assembling the configuration for chapter 5 §setup.
`dataset_v2/scripts/fetch_evidence_v2.py::find_dependents` runs `grep -rl` for the
**basename stem** of each changed file, filters hits by source extension, caps at
15, and hardcodes the relation label `"imports"`. `find_tests` does the same with
the label `"tests"`. Nothing is parsed and no relation is verified. Inspection of
`data/luca_prs_v2/pr10_evidence.json` shows the failure mode concretely: three
files are listed as `imports` of `README.rst`.

Consequences, none of which invalidate a result but all of which change how it
must be worded:

1. **The headline KG effect is an effect of this construction**, not of
   graph-structured context in general. Chapter 5 now says so
   (`5_evaluation/experimental_setup.tex` §Context Construction).
2. **The paper's Approach section is currently wrong.** It states the graph is
   "built by static analysis" and that "nothing is inferred from name similarity"
   (`paper/2026-08-12/draft/main.tex` lines 205–210). That sentence describes a
   builder that produced a sensitivity analysis, not the headline. Must be fixed
   before submission.
3. **The scoped-AST sensitivity is temperature-confounded.** The headline ran at
   T = 0.0; the sensitivity regenerated its `kg` and `hybrid` arms at T = 0.4
   (`logs/step3_regen.log` line 6). So "the effect shrinks under a parsed builder"
   conflates builder and temperature. The Joern comparison *is* temperature-matched
   and is therefore the stronger of the two defences — but it only supports the
   baseline-vs-kg contrast, because its other three arms were carried over from the
   grep run (`paper/2026-08-12/INTEGRITY_AUDIT.md` lines 111–116).
4. **Experiment 2 is unaffected**: its deployed graph arm is the code property
   graph, so the causal claim rests on parsed structure. The two experiments do not
   share a builder, and the thesis should stop implying they do.

**Decided 2026-08-18: the arm keeps the name `kg`.** Renaming it would break
continuity with every existing artefact, table, figure and cached judge cell, and
would make the two experiments look like different studies when the only
difference is the builder. The honesty requirement is met by disclosure instead:
chapter 5 §Context Construction states how the block is built, what it can get
wrong, and that the headline effect is an effect of that construction. Every
chapter that mentions the arm must carry a pointer to that disclosure rather than
relying on the reader's assumption about what "KG" means. This still needs to be
said out loud to the supervisor — the decision is about naming, not about hiding
the construction.

### 4.1 Final research-question structure (2026-09-26)

**Decision: the thesis uses three flat research questions, one per study.**

| ID | Question | Evidence | Status |
|---|---|---|---|
| RQ1 | How do KG, RAG, and hybrid context affect rubric coverage compared with a diff-only baseline? | Experiment 1, final five-judge panel | complete |
| RQ2 | To what extent does structural context enable detection of cross-file consequences absent from the diff? | Experiment 2 and component analyses | complete |
| RQ3 | Do blinded practitioners prefer graph-augmented reviews for identifying affected code? | Final 25-rater study | complete |

This structure supersedes the two-level RP/RQ scheme recorded on 2026-08-18.
The injection study remains a scope addition relative to the exposé, and the
practitioner study is narrower than broad validation of an LLM judge. Those
changes should be disclosed to the supervisor; the simplified numbering does
not alter any experiment or result.

---

## 5. Chapter status

| Ch. | Title | Status | Blocked by |
|---|---|---|---|
| — | Abstract / Zusammenfassung | stub | written last; German version required by the template |
| 1 | Introduction | stub | D1 and final narrative framing |
| 2 | Background | stub (6 sections) | bibliography |
| 3 | State of the Art | stub | bibliography |
| 4 | Approach | stub | nothing — needs code reading |
| 5 | Experimental Design and Setup | stub (3 sections) | nothing — **start here** |
| 6 | Results and Discussion | stub (5 sections) | human-study section only |
| 7 | Conclusions | stub | chapters 5–6 |

---

## 6. Build and sync

- Overleaf project `6a8463b2592c1f03823e2dd8` is the build of record; it is
  synced from this directory over the Overleaf git bridge (`git push origin main`).
- `_reference/` holds the previous student's thesis for style comparison and is
  excluded from both the build and the sync.
- Local builds typeset the body cleanly but cannot run the bibliography:
  tectonic's bundle ships biblatex 3.17 while Homebrew's biber is 2.22. Either
  pin biber to 2.17 or treat Overleaf as the only full build.
