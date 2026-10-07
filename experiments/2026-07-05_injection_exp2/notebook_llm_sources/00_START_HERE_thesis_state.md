# Thesis state — read-me-first anchor (2026-07-05)

**Purpose.** One file to re-orient after being away. If you read nothing
else, read §0 and §9. Every number cites its source file so you can
trust it. No number here is from memory.

---

## 0. Thirty-second orientation

- You are writing a Master's thesis (HPI) on **whether giving an LLM code
  reviewer repository context (knowledge graph and/or retrieval) makes it
  write better PR reviews than a diff-only baseline.**
- **The main result is DONE and statistically significant.** You have a
  complete, defensible thesis *right now*.
- **The bottleneck is writing, not experiments.** The decision (2026-07-05)
  is: **freeze scope, write the draft, and only then optionally scale the
  bug-injection probe into a second experiment.**
- Immediate next action: draft the thesis spine (abstract + contribution
  paragraph + chapter outline). Experiment 2 is designed and *banked* in
  this same folder for later.

---

## 1. The thesis in one paragraph

I evaluate whether augmenting an LLM code-reviewer with a repository
**knowledge graph (KG)** and/or **retrieval-augmented generation (RAG)**
produces better PR review comments than the prevailing diff-only
baseline. I compare four modes — baseline, kg, rag, hybrid — on **40 real
merged pull requests** from **5 open-source repositories**, generated with
**gpt-4o (T=0.4, seed=42)** and scored by a **three-judge LLM panel**
(gpt-4o-mini, gpt-4o, gemini-2.5-flash) on a **25-criterion rubric**
(9 tagged KG-relevant). Source: `thesis-context/CLAUDE.md`.

### The one-sentence story (for abstract / defense)
> **Context helps LLM code review only when it is scoped and matched to
> the task — not when it is merely abundant.** KG context produces
> targeted gains on cross-file/structural criteria, RAG produces gains on
> general coverage, and the two are complementary rather than one
> dominating. The practical lever is scoping and edge-precision, not
> context volume.

This framing reconciles the "structure beats vibes" hype with the 2026
finding (SWE-PRBench) that piling on context can *hurt* — your gains are
*scoped*, not uniform.

---

## 2. Dataset (memorise this)

- **40 merged PRs**, 5 repos, 5 languages. Source of truth:
  `dataset_v2/docs/SELECTION_v2.md` §3.
- Repos: **grafana (Go/TS) · apache/kafka (Java/Scala) · scikit-learn
  (Python) · godotengine/godot (C++) · jenkinsci/jenkins (Java)**.
- **CONTRADICTION TO FIX:** `thesis-context/CLAUDE.md` says the 5th repo
  is "Django". The detailed dataset doc says **godot**, and godot is what
  the PRs/human-study/injection actually use. Django is a stale error in
  the CLAUDE.md summary paragraph — correct it there.
- Built direction-blind under 8 selection criteria (all merged, no
  reverts, substantive code change, KG-parseable, ≤50 kB diff, real body,
  no chore titles, ≥2 KG-parseable files). `dataset_v2/docs/SELECTION_v2.md` §2.
- **Two distinct PR sets — do not conflate:** `dataset_v2/` 40 PRs =
  LLM-judge/RQ2 data; `human_eval_v3/` 6 PRs = human sub-sample.
- **v1 is dead** (contaminated: truncated diffs + empty bodies). Do not
  quote v1 numbers. `dataset_v2/docs/AUDIT_v1.md`.

---

## 3. HEADLINE RESULTS — Experiment 1 (canonical, DONE)

Source: `results/BOOTSTRAP_STATS_v2.md` (percentile bootstrap B=10000,
paired permutation B=20000, seed=2026, n=40).

### Per-mode means (95% bootstrap CI)
| Mode | Total mean [CI] | KG-relevant mean [CI] |
|---|---:|---:|
| baseline | 9.20 [8.70, 9.70] | 4.97 [4.67, 5.28] |
| kg | 9.82 [9.28, 10.43] | **5.58 [5.22, 5.95]** |
| rag | **10.07 [9.57, 10.60]** | 5.40 [5.00, 5.78] |
| hybrid | 9.93 [9.47, 10.38] | 5.50 [5.22, 5.78] |

### Paired Δ vs baseline
| Mode | Total Δ [CI] | p | d_z | KG-rel Δ [CI] | p | d_z |
|---|---:|---:|---:|---:|---:|---:|
| **kg** | +0.62 [+0.05, +1.20] | 0.054 | 0.33 | **+0.60 [+0.23, +0.97]** | **0.007** | 0.47 |
| **rag** | **+0.88 [+0.30, +1.45]** | **0.007** | 0.47 | +0.42 [+0.05, +0.82] | 0.057 | 0.33 |
| **hybrid** | **+0.72 [+0.10, +1.35]** | **0.037** | 0.36 | **+0.53 [+0.17, +0.90]** | **0.008** | 0.46 |

**Reading:** KG wins on the metric it targets (KG-relevant, p=0.007),
RAG wins on the metric it targets (total coverage, p=0.007), hybrid wins
on both. **Complementarity — not KG dominance.** (This is the required
framing; do not let "KG beats everything" into the prose.)

### Inter-judge agreement (Cohen's κ)
gpt-4o-mini↔gpt-4o = 0.717 · gpt-4o-mini↔gemini = 0.590 ·
gpt-4o↔gemini = 0.713. Substantial. Source: `thesis-context/CLAUDE.md`.

---

## 4. Validation infrastructure (DONE) — why the result holds up

Source: `STATUS.md` §2, `results/THREATS_TO_VALIDITY.md`.

- **Rubric provenance:** 25 criteria mapped to published sources
  (Bacchelli & Bird ICSE'13, Bosu MSR'15, Sadowski ICSE-SEIP'18, ISO 25010).
  `results/RUBRIC_PROVENANCE.md`.
- **KG-relevant tag κ = 0.615** (substantial, 84% agreement) —
  `results/RUBRIC_KAPPA_kg_relevant.md`.
- **Positive control:** deliberately-bad reviews score low (4/5) —
  `results/RUBRIC_POSITIVE_CONTROL.md`.
- **Negative control:** empty-KG priming — `scripts/generate_kg_empty_control.py`.
- **Cross-generator robustness:** KG lift is *conditional* on the base
  model not being saturated (Claude baseline already saturates → no lift).
  Refined claim, not a bug. `results/THREATS_TO_VALIDITY.md` §8.3.2.
- **Trajectory (Goodhart-proof):** result strengthened monotonically
  18→25→40 PRs (snapshots on disk).

---

## 5. Bug-injection probe — Experiment 2 candidate (PROTOTYPE DONE)

Source: `exceptional test/prototype/FINDINGS_SCALE.md`, `THESIS_SUBSECTION.md`.

Plants **known cross-file defects** (symbol renames breaking importers in
other files) and checks which mode's review catches the hidden blast
radius. Ground truth is known by construction.

**Scaled result (8 injections, scikit-learn, 3-judge majority):**
| Mode / builder | Detected |
|---|---|
| baseline (diff only) | 0/8 |
| rag (thesis-faithful top_k=10) | 1/8 |
| KG — grep-stem | 2/8 |
| **KG — Joern CPG (your deployed builder)** | **4/8** |
| KG — idealised import-level | 8/8 |
| RAG — purpose-built (AST chunks + query-by-symbol) | 5/8 |

**Key finding:** detection tracks whether the builder handed the model a
true dependent. Deployed Joern resolves cross-file *calls* but is **blind
to inheritance edges** — every Joern miss is a base-class/mixin rename.
→ Actionable contribution: add `INHERITS_FROM`/import edges to move
deployed KG from 4/8 toward the 8/8 ceiling.

**Status:** finished as a *mechanism probe*. Can be included in the
Discussion **for free** (drop-in text exists). Scaling it into a full
co-equal Experiment 2 is **designed and pre-registered** in
`experiments/2026-07-05_injection_exp2/docs/DESIGN_AND_PREREGISTRATION.md`
— but deferred until the draft is written (see §9).

---

## 6. Human study / RQ3 (STUCK → downgraded)

- v3 study: 6 PRs, baseline_strict vs Joern-KG, 6 criteria, per-pair A/B.
  `human_eval_v3/`.
- **Problem:** rating is very hard — review pairs look near-identical and
  you can't verify concrete details without knowing the codebase. Author
  (you) struggled → recruited raters will struggle more. Threatens data
  quality.
- **Decision (2026-07-05):** downgrade RQ3 to a *supporting* judge-
  validation check, not a headline experiment. **Do not sink more time
  into the rater UX.** Experiment 2 validates the judge *objectively*
  (known ground truth), which covers the same need.
- Also blocked: Apps Script webhook (HTTP 405) — but data-loss-proof
  (localStorage + export). `STATUS.md` §5.

---

## 7. Applications / take-home (for intro + defense)

- **Direct:** a smarter PR-review bot that flags cross-file breakage
  (broken callers, missing tests, dependencies) the diff hides. Demo:
  `reports/2026-06-22/demo.html`.
- **Transferable recipe:** for *any* LLM coding tool (completion,
  bug-fixing agents, refactoring), retrieve a *small, structured,
  task-matched* context slice — graph edges for structural questions,
  semantic retrieval for general ones — and don't over-stuff the window.
- **Honest scope:** a first-pass / decision-support aid, strongest on
  cross-file/structural issues, most useful when the base model isn't
  already saturated. Not a human-reviewer replacement.

---

## 8. Where everything lives (file map)

| What | Path |
|---|---|
| Operating rules + canonical numbers | `thesis-context/CLAUDE.md` |
| Section → source-file map | `thesis-context/CODE_INDEX.md` |
| Project status index | `STATUS.md` |
| Headline stats | `results/BOOTSTRAP_STATS_v2.md` |
| Dataset selection rationale | `dataset_v2/docs/SELECTION_v2.md` |
| Threats to validity | `results/THREATS_TO_VALIDITY.md` |
| Rubric provenance | `results/RUBRIC_PROVENANCE.md` |
| Cross-generator robustness | `results/CROSS_GENERATOR_REPLICATION.md` |
| Review generator (4 modes) | `prnote/note.py` |
| KG construction | `prnote/kg.py` |
| RAG retrieval | `prnote/rag.py` |
| 3-judge panel | `scripts/evaluate_reviews.py` |
| Injection prototype + findings | `exceptional test/prototype/FINDINGS_SCALE.md` |
| Injection drop-in thesis text | `exceptional test/prototype/THESIS_SUBSECTION.md` |
| **Experiment 2 design/pre-reg** | `experiments/2026-07-05_injection_exp2/docs/DESIGN_AND_PREREGISTRATION.md` |
| Human study (stuck) | `human_eval_v3/` |
| LaTeX chapters | `thesis/chapters/` |

---

## 9. THE PLAN (decided 2026-07-05) — do these in order

1. **Freeze scope.** Experiment 1 alone = a complete, significant thesis.
   Stop starting new experiments.
2. **Write the spine** — abstract + intro contribution paragraph +
   one-page chapter outline mapping each section to a `results/*.md`.
3. **Methods (Ch. 4–5)** — pipeline, dataset, rubric, judges. Mostly
   transcription; sources exist.
4. **Results (Ch. 6)** — headline table (§3) + injection *probe*
   subsection (§5, drop-in text exists).
5. **Discussion + Threats (Ch. 7–8)** — story (§1) + `THREATS_TO_VALIDITY.md`.
6. **Get the draft to the supervisor.** Show up with a decision, not a swirl.
7. **Only then**, if time remains, scale the injection probe into full
   Experiment 2 (design already banked). Secure the pass, then reach for
   the distinction.

### Open decisions parked for later (Experiment 2, §13 of the design doc)
N/split (48?), repos (confirm Joern works on Grafana Go/TS), oracle
scope, ablation arms, and confirming the RQ3 downgrade. None block writing.

---

## 10. Rules to not violate (from `thesis-context/CLAUDE.md`)
- Dataset = **40 PRs, 5 repos**. Not 25, not 18 (those are snapshots).
- Rubric = **25 criteria, 9 KG-relevant**.
- gpt-4o is the **generator**, not the judge.
- Framing = **complementarity**, never "KG dominates".
- Every number needs a `(file.md §section)` citation.
- No fabricated citations; if a paper isn't in `bibliography.bib`, flag it.
