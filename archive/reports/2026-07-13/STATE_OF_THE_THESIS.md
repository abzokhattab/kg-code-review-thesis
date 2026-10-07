# State of the thesis — consolidation anchor (2026-07-13)

> ## ⛔ SUPERSEDED — DO NOT CITE
>
> The KG effect reported below (+1.743/6, d_z=+1.24, p<.0001, W/T/L 28/6/1) is
> an artefact of a **prompt asymmetry**: the KG arm received a prompt the
> baseline did not, so the contrast measured builder *plus* prompt. Re-running
> the same Joern builder with the prompt held at parity
> (`results/BOOTSTRAP_STATS_joern_parity.md`, n=35) yields kg +0.63 on the
> total (p=0.077) and +0.34 KG-relevant (p=0.111) — **not significant on
> either metric**.
>
> Canonical RQ2 headline: `results/BOOTSTRAP_STATS_v2.md` (era 2).
> Causal claim for structural context: `results/INJECTION_EXP2_RESULTS.md`.
> Context: `results/ERA_GUIDE.md`.


**Purpose.** One file to end the confusion. Written after reconstructing
the full experiment timeline by folder creation/modification dates and
re-reading every state document. Every number cites its source file.
This file supersedes nothing — it *points at* what is canonical and
names the contradictions explicitly.

**Note on dates:** a bulk operation touched most file mtimes on
2026-07-12 16:37, so per-file mtimes are unreliable for sequencing.
The timeline below uses folder creation dates and dated folder names.

---

## 0. The confirmed plan (what you told the assistant on 2026-07-13)

> **Two experiments.**
> **Experiment 1** — the existing context-augmentation experiment
> (baseline vs KG vs RAG vs hybrid, LLM-judged rubric).
> **Experiment 2** — the controlled bug-injection experiment.

This is **exactly the plan you already decided on 2026-07-05** and wrote
down in `experiments/2026-07-05_injection_exp2/THESIS_STATE_2026-07-05.md`
§9. Nothing about that plan is stale. It only *feels* contradictory
because of three things, named in §2 below.

---

## 1. Timeline — how we got here (reconstructed 2026-07-13)

| When | What happened | Where it lives | Status today |
|---|---|---|---|
| Jan–Feb 2026 | Exposé + POC report | `Expose-latex/` | Historical context only |
| Jan–Apr 2026 | **Era 1 "v1"**: 25 PRs, 4 repos, grep-KG | files without `__v2` suffix | **DEAD — contaminated.** Never cite. (`dataset_v2/docs/AUDIT_v1.md`) |
| May 2026 | **Era 2 "v2"**: 40 PRs, 5 repos, 4 modes, 3-judge panel | `results/BOOTSTRAP_STATS_v2.md` | **DONE, significant.** Candidate canonical Exp 1 |
| 15 May – Jun 2026 | **Era 3 "Joern"**: same 40 PRs (n=35), Joern CPG-KG, different judges, re-based 15-criterion rubric | `experiments/2026-05-15_joern_kg_main/`, `results/FINAL_RESULTS_REPORT.md`, `results/BOOTSTRAP_STATS_joern.md` | **DONE.** The other candidate canonical Exp 1 |
| Jun 2026 | Human study v3 built (6 PRs, sklearn/kafka/etc.) | `human_eval_v3/` | Deployed, **too hard for raters** — stuck |
| 24–28 Jun 2026 | Bug-injection **prototype** (8 renames, sklearn) | `exceptional test/prototype/FINDINGS_SCALE.md` | **DONE as mechanism probe**: baseline 0/8 · RAG 1/8 · deployed Joern-KG 4/8 · idealised AST-KG 8/8 |
| 5 Jul 2026 | **DECISION: freeze scope, write the draft, bank Exp 2, downgrade human study** | `experiments/2026-07-05_injection_exp2/THESIS_STATE_2026-07-05.md` §9; pre-registration in `docs/DESIGN_AND_PREREGISTRATION.md` | **This is still the plan** |
| 6 Jul 2026 | Human study **v4** built anyway (6 Python PRs, requests/flask/click) | `experiments/2026-07-06_user_study_prs/` | Built, piloted; **contradicts the 7-05 freeze** |
| 12–13 Jul 2026 | "Option B" out-of-dataset human-study PR builder + cross-file fan-out screen (incl. Django) | `scripts/build_human_study_pr.py`, `scripts/screen_pr_crossfile_fanout.py`, `human_eval_v3/analysis/fanout/` | **Contradicts the 7-05 freeze**; also blocked — Joern needs a Java runtime and none is installed (see terminal) |

---

## 2. The three actual sources of confusion — named

### 2.1 Two candidate "Experiment 1"s (REAL, undecided — supervisor call)

Era 2 (v2, 4 modes) and Era 3 (Joern) are **different experiments**, not
two estimates of the same number: different KG builder, judge panel,
active-criteria count, and denominator (`results/ERA_GUIDE.md`).

| | Era 2 "v2" | Era 3 "Joern" |
|---|---|---|
| n | 40 PRs | 35 PRs (5 Go excluded) |
| Modes | baseline / kg / rag / hybrid | baseline / joern-kg / rag |
| KG builder | grep-based | Joern CPG (callers + tests) |
| Judges | gpt-4o-mini, gpt-4o, gemini-2.5-flash | gpt-4o, gemini-2.5-flash, gemini-2.0-flash |
| Rubric | 25 criteria, 9 KG-relevant | 15 active, 6 KG-active |
| KG headline | +0.60/9, p=.007, d_z=.47 (`BOOTSTRAP_STATS_v2.md`) | +1.743/6, p<.0001, d_z=1.24 (`BOOTSTRAP_STATS_joern.md`) |
| Story | modest, complementarity (KG≈RAG, each on its metric) | large, KG≫RAG |

**Until the supervisor decides which is the canonical RQ2 headline, any
draft must cite one era per table and label it** (`results/ERA_GUIDE.md`
§"Pending decision"). This is the single most important open decision.
Note the Exp 2 pre-registration assumes the **deployed Joern builder**
is "the same one behind the 40-PR headline" — i.e., it leans era-3.
Deciding the era *before* running Exp 2 keeps the two experiments
coherent.

### 2.2 The human-study flip-flop (self-inflicted — resolve by sticking to 7-05)

- 2026-07-05: decided to **downgrade RQ3** to a supporting check and
  stop investing in rater UX (`THESIS_STATE_2026-07-05.md` §6, §9).
- 2026-07-06: built human-study v4 anyway.
- 2026-07-12/13: built "Option B" out-of-dataset study PRs anyway
  (currently broken: no Java runtime for Joern).

Under the two-experiment plan confirmed today, **the 7-05 decision
stands**: Exp 2 validates the judge objectively against known ground
truth (`DESIGN_AND_PREREGISTRATION.md` §9), which covers what the human
study was for. v4 and Option B stay on disk as *optional supporting
material* — no more time goes into them until the draft and Exp 2 are
done. (Bonus: this makes the missing-Java problem irrelevant for now.)

### 2.3 Cosmetic contradictions (fixed or ignorable)

- `thesis-context/CLAUDE.md` repo list now correctly says godot (the
  "Django" error flagged in `THESIS_STATE_2026-07-05.md` §2 appears
  fixed). Django only appears in the 7-13 fan-out screen, which is
  out-of-dataset Option B material — not the 40-PR set.
- Human-study v4's own 6-PR judge panel showed KG *not* beating baseline
  on rubric totals (`experiments/2026-07-06_user_study_prs/README.md`
  §Findings). That is **not** a contradiction of the 40-PR result: n=6,
  different PRs (tests shipped in-diff), different purpose (grounding,
  not rubric totals). Do not average it into anything.
- v1 numbers, "25 PRs", the 14-criterion rubric: all banned, per
  `thesis-context/CLAUDE.md` §Strict rules. Unchanged.

---

## 3. The two experiments — precise definitions

### Experiment 1 — context-augmented review quality (DONE, era choice pending)

Does repository context (KG / RAG) improve LLM PR-review quality over a
diff-only baseline, measured by an LLM-judge rubric on real merged PRs?
Both candidate versions are complete and statistically significant
(§2.1). **Remaining work: the era decision, then writing. No new runs.**

### Experiment 2 — controlled cross-file defect injection (DESIGNED, not run)

Does structural context let the reviewer catch a *known, hidden*
cross-file defect — and does the advantage disappear on local defects
(the placebo band)? Fully pre-registered:
`experiments/2026-07-05_injection_exp2/docs/DESIGN_AND_PREREGISTRATION.md`.

- N = 48 injections (36 structural S1–S5 + 12 local control L1–L2),
  3 repos (sklearn, kafka, grafana — pending §13 sign-off).
- Same 4 modes + 2 ablation arms (`kg-idealised`, `kg-joern+inherit`).
- Same 3-judge panel and stats machinery as era 2.
- Estimated ~$15–30, ~2–4 h (pre-reg §12; must re-confirm at run time).
- **Blockers before running:** (a) §13 sign-off (N/split, repos, oracle
  scope, ablation arms, human-study downgrade confirmation); (b) a Java
  runtime for Joern (currently missing — see terminal); (c) confirm
  Joern coverage for grafana Go/TS.

### Prototype evidence Exp 2 scales (already citable in Discussion)

8 injections, sklearn (`exceptional test/prototype/FINDINGS_SCALE.md`):
baseline 0/8 · rag 1/8 · grep-KG 2/8 · deployed Joern-KG 4/8 ·
idealised import-KG 8/8. Every Joern miss = missing inheritance edge →
the `kg-joern+inherit` ablation arm is the engineering contribution.

---

## 4. Ordered next actions

1. **Decide (with supervisor) the canonical era for Experiment 1**
   (§2.1). Everything downstream — abstract, results chapter, Exp 2
   mode config — depends on it. Prepare a half-page comparison memo
   from `results/ERA_GUIDE.md` and bring it to the next meeting.
2. **Write the spine** — abstract + contribution paragraph + chapter
   outline mapping each section to a `results/*.md`
   (`THESIS_STATE_2026-07-05.md` §9 steps 2–5 are still the writing
   plan).
3. **Sign off Exp 2 §13 decisions** (can happen in the same supervisor
   meeting as the era decision).
4. **Install a Java runtime** (needed for Joern) — only when Exp 2 is
   actually about to run, not before.
5. **Run Experiment 2** per the pre-registration, in
   `experiments/2026-07-05_injection_exp2/` (harness stages listed in
   pre-reg §16). Print the cost/wall-clock pre-flight summary first.
6. **Do not touch the human study** (v3, v4, Option B) until 1–5 are
   done. It is downgraded, not deleted.

---

## 5. Standing rules that keep applying

- Dataset = 40 PRs, 5 repos (grafana, kafka, scikit-learn, godot,
  jenkins). Not 25, not 18.
- One era per table, always labeled. Never mix /9 (era 2) with /6
  (era 3) denominators.
- gpt-4o is the generator, never "the judge".
- Framing = complementarity (era 2) — and if era 3 becomes canonical,
  the framing must be re-derived from `FINAL_RESULTS_REPORT.md`, not
  asserted.
- Every number cites `(file.md §section)`.
- Warn with estimated $ before any token-spending run.
