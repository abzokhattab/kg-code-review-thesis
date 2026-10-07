# Synthesis — what the thesis establishes, and how the experiments fit together

**Written:** 2026-08-31. **Scope:** the whole evidence base as of today, after the
robustness work of 2026-08 (leave-one-out, cross-generator, builder parity,
criterion localisation, clean held-out replication).

Every number below is followed by its source file. Nothing here is quoted from
memory. Where a claim is *not* established, that is stated in the same sentence
as the claim.

---

## 1. The one-paragraph argument

A diff-only LLM reviewer cannot see consequences that live outside the diff — in
a controlled injection study it caught **0 of 28** cross-file structural defects
(`results/INJECTION_EXP2_RESULTS.md`). Supplying a structural code graph closes
most of that gap (**15/28**, +0.54, p < 0.0001), and the residual is graph
completeness rather than model capability, since an idealised resolver reaches
26/28. Retrieval does not substitute (**1/28**): "what breaks if I change this"
is a structural query, not a similarity query. On real merged pull requests the
same mechanism is detectable but small in aggregate (**+0.60 of 9** on the
targeted subscale, p = 0.007; `results/BOOTSTRAP_STATS_v2.md`), because the
situation the graph uniquely helps with is uncommon in an arbitrary PR — and
**96% of the total advantage lands in the 9 criteria the mechanism predicts**
(p = 0.016; `results/CRITERION_CONCENTRATION.md`), which is what distinguishes a
real mechanism from a drift. That aggregate magnitude is fragile to evaluation
choices: it leans on one judge of three, weakens under three other generators,
and halves when a prompt asymmetry in the graph-builder comparison is corrected.
A pre-registered held-out replication agrees in direction and effect size
(+0.42, d_z +0.39) but has only 8–16% power and therefore cannot confirm it
(`results/CONFIRMATORY_CLEAN.md`).

**The contribution is therefore twofold:** a demonstrated, causally-identified
capability gain from structural context, and an honest measurement of how much
that gain is worth in realistic conditions — including how much the answer moves
when you change the evaluator rather than the system.

---

## 2. Why there are two experiments, and how they reconcile

The two experiments measure different quantities and the apparent tension
between them is the thesis's central insight rather than a problem to explain
away.

| | Experiment 1 (observational) | Experiment 2 (controlled) |
|---|---|---|
| Question | On a real PR, does context raise review quality? | Can the reviewer see an off-diff consequence at all? |
| Ground truth | none — LLM-judge opinion on a rubric | known by construction (defect was injected) |
| Sampling | 40 real merged PRs, 5 repos | 40 injections chosen for structural fan-out |
| Effect | +0.60 of 9, p = 0.007 | 0.00 → 0.54, p < 0.0001 |
| Internal validity | weak (no oracle; judge-dependent) | strong (oracle, placebo band, pre-registered) |
| External validity | strong (real PRs, real review criteria) | weak (synthetic defects, 3 repos, one at a time) |

Experiment 2 establishes that the mechanism **exists and is causal**. Experiment 1
estimates **what it is worth in expectation** on an arbitrary PR. A large
capability gain and a small average gain are both true because Experiment 2
conditions on the mechanism applying, while Experiment 1 samples PRs where it
usually does not apply.

Stated plainly for the thesis: *the graph gives the reviewer a new ability; that
ability is rarely decisive on a randomly chosen pull request.*

The join between the two is empirical, not rhetorical. Experiment 1's advantage
concentrates in F3 "names the affected code" (60.0% → 82.5%, +22.5pp,
`results/CRITERION_CONCENTRATION.md`), which is the rubric's closest proxy for
exactly the capability Experiment 2 isolates.

---

## 3. Claim-by-claim status

Each claim, its evidence, and an explicit strength label. Use these labels in the
prose; do not upgrade them.

> **Notation.** Claims are numbered "Claim 1 … Claim 9". Rubric criteria use
> their own letter-prefixed ids (F1–F4, M1–M3, T1–T3, P1–P2, R1–R3, Q1–Q5,
> S1–S3, C1–C2, plus C6 in the human-study instrument). "C1" therefore always
> means the Consistency criterion, never a claim.

### Claim 1 — Diff-only LLM review has a structural blind spot. **ESTABLISHED.**
Baseline detection on 28 cross-file structural injections: **0/28**, CI
[0.00, 0.00] (`results/INJECTION_EXP2_RESULTS.md`). Not a tuning deficiency —
the information is absent from the prompt.

### Claim 2 — Structural graph context closes most of the gap; the residual is graph completeness. **ESTABLISHED.**
Deployed Joern CPG **15/28 = 0.54** [0.36, 0.71]; kg − baseline = **+0.54**
[+0.36, +0.71], **p < 0.0001**, meeting the pre-registered §10.1 threshold
(≥ +0.30, p < .05). Adding import/`INHERITS_FROM` edges: **21/28 = 0.75**.
Idealised static resolver ceiling: **26/28 = 0.93**. On the S4 inheritance band
(n = 6) the augmented builder scores 5/6 vs 2/6, Δ = +0.50, meeting §10.3;
across all structural bands the augmentation is +0.21 [+0.04, +0.39], p = 0.071
(n = 28). Source: `results/INJECTION_EXP2_RESULTS.md`.

### Claim 3 — Retrieval is not a substitute for structure. **ESTABLISHED (negative result).**
RAG detection **1/28 = 0.04** [0.00, 0.11]; rag − baseline = +0.04, **p = 1.0**.
Hybrid (0.43) does not exceed KG alone (0.54). Source:
`results/INJECTION_EXP2_RESULTS.md`; failure analysis in
`thesis-context/results/RAG_FAILURE_ANALYSIS_EXP2.md`. This is a substantive
finding against the assumption that retrieval is a general-purpose context fix.

### Claim 4 — The advantage is structural, not a context-volume or prompt-priming artefact. **ESTABLISHED IN EXPERIMENT 2 ONLY.**
On the 12 local-control injections — defects visible in the diff — kg − baseline
= **−0.08** [−0.25, +0.00], inside the pre-registered parity window
[−0.15, +0.15] (§10.2); all arms detect at 0.83–1.00. Extra context confers no
advantage when the answer is already on screen.
**Not established for Experiment 1.** The empty-KG priming control there covers
only 5 PRs and, on the era-matched panel, splits the lift equally between
priming (+0.20) and content (+0.20)
(`results/KG_EMPTY_PRIMING_CONTROL.md`) — it does **not** show the Experiment 1
lift is content-driven.

**Decision, 2026-09-05 (supervisor):** the placebo is *not* re-run on the 40-PR
set, and instruction priming is **not discussed in the thesis at all** — it would
draw reviewer attention disproportionate to its weight. Executed the same day:
§`sec:results-exp1-priming` was deleted from `results_experiment1.tex`, and the
threats chapter never raised the topic.

Deleting a disclosure is only safe because nothing depended on it, which was
verified rather than assumed. No sentence in any `.tex` file asserts that the
Experiment 1 lift comes from the graph's content rather than from the instruction
to look for integration risks, so removing the caveat left no claim
unsupported. Experiment 2 is also immune to the objection by construction — a
prompt containing no facts cannot name a dependent file it was never given — so
the mechanism argument (Claims 1–3) never rested on the Experiment 1 control.

**The claim ceiling survives the decision and is not negotiable.** Because the
control is 5 PRs and era-crossed, no sentence may be *added* asserting that the
Experiment 1 lift is content-driven. Silence on the question is permitted; a
positive claim is not. If a viva question raises priming, the answer is
Experiment 2's construction, not the 5-PR control.

### Claim 5 — On real PRs the effect is small in aggregate but sharply localised. **ESTABLISHED for localisation; BORDERLINE for the aggregate total.**
Paired vs baseline, n = 40 (`results/BOOTSTRAP_STATS_v2.md`):
kg total **+0.62** [+0.05, +1.20], p = 0.054, d_z +0.33; KG-relevant **+0.60**
[+0.23, +0.97], **p = 0.007**, d_z +0.47.
Localisation (`results/CRITERION_CONCENTRATION.md`, B = 200 000, seed 2026):

| Arm | gain in the 9 KG-relevant | total gain | share | expected if diffuse | p |
|---|---:|---:|---:|---:|---:|
| kg | +0.600 | +0.625 | **96%** | +0.225 | **0.016** |
| rag | +0.425 | +0.875 | 49% | +0.315 | 0.272 |
| hybrid | +0.525 | +0.725 | 72% | +0.261 | 0.063 |

This is the strongest single argument in the thesis, for two reasons. First, a
noise or verbosity artefact would spread in proportion to subset size (36%);
kg's advantage is 96% localised. Second, the test **discriminates the two
mechanisms**: RAG's advantage is diffuse (49%, p = 0.27), exactly as the
complementarity claim predicts. Two aggregate numbers cannot make that argument;
the localisation test can.

Supporting detail: the aggregate is diluted by construction — 6 of the 25
criteria (C1, M2, Q1, Q2, Q4, S2) sit at 0% or 100% in both arms and can never
register a difference.

### Claim 6 — The measured magnitude on real PRs is fragile to evaluation choices. **ESTABLISHED.**
- **Judge.** The KG-relevant effect is carried by gpt-4o alone (+0.65,
  p = 0.006) and is not significant under either other judge or with gpt-4o
  dropped (`results/JUDGE_LEAVE_ONE_OUT.md`). gpt-4o is also the generator, so
  self-preference cannot be excluded.
- **Generator.** Non-significant under claude-haiku-4.5, gemini-2.5-flash and
  deepseek-v3 on the same packs, prompts, rubric and panel; verbosity is ruled
  out as the explanation (`results/CROSS_GENERATOR_v2.md`).
- **Builder.** With prompt composition matched, the CPG builder gives +0.63
  total (p = 0.077) and +0.34 KG-relevant (p = 0.111), n = 35
  (`results/BOOTSTRAP_STATS_joern_parity.md`). This **supersedes** the
  +1.17/+0.69 in `results/BOOTSTRAP_STATS_joern.md`, which was inflated by an
  omitted PR description rather than being a lower bound.

Note the direction of this finding: the *capability* result (Claims 1–4) is robust
because it has an oracle; the *rubric magnitude* is fragile because it does not.
That is a coherent position, and it is the honest one.

### Claim 7 — Held-out replication agrees in direction and size, and cannot do more. **ESTABLISHED as consistency; NOT a confirmation.**
12 held-out PRs, headline configuration, only the dataset varying
(`results/CONFIRMATORY_CLEAN.md`): total **+0.42** [−0.25, +1.17], p = 0.426,
d_z +0.30; KG-relevant **+0.42** [−0.17, +1.00], p = 0.312, d_z +0.39. Effect
sizes track the exploratory run closely (d_z 0.33 → 0.30 and 0.47 → 0.39); the
mild attenuation is expected when re-estimating an effect off new data.
**The pre-registered p < 0.05 criterion is not met, and could not realistically
have been:** resampling 12 PRs from the 40 observed paired differences and
running the same exact permutation test reaches significance only **8%** (total)
and **16%** (KG-relevant) of the time when the effect is exactly real. The
p-value from this design carries almost no evidential weight; the point estimate
does.
The localisation of Claim 5 also replicates in direction on the held-out set: **100%**
of the kg gain (+0.417 of +0.417) falls in the 9 KG-relevant criteria, though at
n = 12 the concentration test is itself underpowered (p = 0.192)
(`scripts/analyze_criterion_concentration.py` run against
`results/checklist_evaluation_llm_multi__confirmatory_clean.json`).

The earlier 2026-05-14 run reporting a *significant negative* (−2.25, p = 0.046)
is **superseded and must not be cited**: it fed the judges the wrong PR titles
and bodies (held-out ids 1..12 collide with `data/luca_prs_v2`, which
`load_pr_context` preferred), dropped gpt-4o from the panel, changed generator
and prompt, and scored a 5-item subscale against a 9-item comparator.

### Claim 8 — There is a cost: localisation is traded against failure-mode reasoning. **WEAK — PANEL-SIDE ONLY. Downgraded 2026-09-01.**
In the panel decomposition the kg arm loses ground on security and readability
criteria: S1 17.5% → 7.5% (−10pp), R3 7.5% → 0.0% (−7.5pp), S3 20% → 15%
(−5pp) (`results/CRITERION_CONCENTRATION.md`). KG reviews are longer (mean 1991
vs 1774 characters; longer on 31 of 40 PRs), consistent with output budget being
spent narrating structure.

**Final human-side read (n = 20, target reached): F2\* = 0.446, raw p = 0.0405,
Holm 0.1216.** The trajectory across interim looks was 0.379 (n = 11, raw
p = 0.0104) → 0.458 (n = 16, raw p = 0.1349) → **0.446 (n = 20)**, which is why
no interim read may be quoted: the endpoint wandered either side of the value it
settled on. Directionally the human raters lean the same way as the panel, and
that is all it is — the contrast does not survive correction across the family of
five.

**This is directional support, not corroboration, and the distinction is load-bearing.**
Two facts limit it. The panel's own F2 moved by −2.5pp, which over 40 PRs is one
review, so the criterion that the human instrument actually shares with the panel
carries almost no panel-side signal. And the criteria carrying the panel's real
losses — S1, R3, S3 — have no counterpart in the six-item human instrument at all.
So the correct statement is that *neither* instrument finds the kg arm better at
describing how a change can fail, and one of them finds it slightly worse.

Claim 8 therefore stays **WEAK** and the wording "KG trades failure-mode reasoning
for localisation" is still forbidden. What changed at target is that the claim is
no longer panel-side-only: it is now two instruments declining to find a benefit,
which is weaker than agreement on a cost and stronger than a single panel.
Written up in §`sec:results-human-crossinstrument` on exactly those terms, with a
back-reference added to §`sec:results-exp1-attribution` that explicitly declines to
upgrade the paragraph.

### Claim 9 — Methodological: rubric + LLM-judge on real PRs is a low-power, fragile instrument for this question. **ESTABLISHED within this project.**
The same underlying mechanism registers as p < 0.0001 under injection with an
oracle and as p = 0.054 on a 25-criterion rubric with an LLM panel. The rubric
instrument additionally proved judge-dependent (Claim 6), diluted by 6 dead criteria
(Claim 5), and — in one documented case — capable of producing a *significant
negative* from a context-loading defect (Claim 7). This is a transferable warning for
a literature in which the generate-then-LLM-judge design is common.

---

## 4. Human study — COMPLETE at target, primary endpoint met

**Status: 20 complete raters against a pre-registered target of 18–20 — target
reached at its upper bound, 2 partial sessions excluded by the pre-registered
rule** (finalised 2026-09-05; previous interim reads were n = 11 and n = 16)
(`experiments/2026-07-06_user_study_prs/RESULTS_HUMAN_V4.md` and
`RESULTS_HUMAN_V4.json`; study `human_eval_v4_python_20260808`, instrument
`python-prs-study-v4-diff-default-r14`).

- Primary **F3\***: KG-preference **0.708** [0.629, 0.787], Wilcoxon
  **p = 0.0008**, non-tie n = 19, rank-biserial r = 0.87. Choices over the 120
  comparisons: kg 75, baseline 25, both 17, neither 3. **The pre-registered
  primary endpoint is met.** Observed 0.708 sits between the planning scenario
  (0.65, power 0.91 at n = 20) and the optimistic one (0.75).
- Secondary **overall usefulness** (estimation only, no significance claim):
  **0.483** [0.392, 0.575] — interval contains 0.5, no preference either way.
- Exploratory (Holm across five): **nothing survives**; smallest adjusted value is
  R1 at 0.089. All five means are below 0.5, i.e. every exploratory criterion
  leans baseline. F2\* 0.446 (Holm 0.1216), T3 0.425 (0.1171), Q5 0.458 (0.3086),
  R1 0.408 (0.0894), C6 0.471 (0.4989).

Interim trajectory, retained because it is the argument for running to target
rather than analysing continuously:

| Endpoint | n = 11 | n = 16 | **n = 20 (final)** |
|---|---:|---:|---:|
| F3\* | 0.689, p = 0.0118 | 0.719, p = 0.0011 | **0.708, p = 0.0008** |
| overall usefulness | 0.439 [0.318, 0.568] | 0.505 [0.401, 0.604] | **0.483 [0.392, 0.575]** |
| F2\* | 0.379, raw p = 0.0104 | 0.458, raw p = 0.1349 | **0.446, raw p = 0.0405** |

F3\* was stable across all three looks; the two non-primary endpoints wandered.
That is the expected behaviour of an underpowered exploratory endpoint and the
reason no interim read may be quoted as a result.

**Stopping was not data-dependent, and this must be stated if challenged.** The
18–20 target was frozen 2026-07-06, before any response; collection ended at 20,
the *upper* bound, so the stopping point could not have been chosen for its
p-value. Interim looks happened and are disclosed above, but they did not move
the target.

**If more raters arrive, they do not join the confirmatory analysis.** n = 20
exhausts the pre-registered range. Adding raters after seeing a significant
primary is textbook optional stopping, and re-reporting a larger n as the primary
result would forfeit exactly the error control that running to target bought.
Report any additional responses as a clearly-labelled sensitivity analysis, with
the n = 20 confirmatory read left standing as primary.

Two earlier constraints, both now discharged:

1. ~~Do not stop collecting because F3\* is already significant.~~ **Done** —
   ran to 20.
2. ~~Rater ids are real full names.~~ **Done** — `analyze_responses.py` now
   pseudonymises to P01…Pnn by default (`--real-ids` opts out), writes the map to
   a gitignored `RATER_PSEUDONYM_MAP.txt`, and the report is verified free of
   names. P-prefix rather than R- because R1 is a criterion id in this instrument.

The study's role in the argument is corroborative and now discharges it. Humans
and the LLM panel independently favour the kg arm on the *same* criterion (naming
affected code) and independently reproduce the *dissociation* between that
criterion and the global judgement, which is what Claim 5 predicts. Because the
panel effect is partly carried by the judge that also generated the reviews
(Claim 6), a human replication of the direction on the targeted criterion is the
single most useful thing the study contributes.

One finding is the study's own rather than a corroboration, and it is worth
carrying into the discussion. On PR 102 the kg arm named `logging.py`,
`sessions.py` and `tests/test_instance_config.py`; multiple raters independently
called those references speculative, and it is the only PR of six where the kg arm
*lost* F3 (0.35). The edges were not wrong — this study's builder is the AST import
resolver and all twelve returned files genuinely import the changed
`src/flask/app.py` — they were irrelevant. A module-level import edge does not
imply that a change to one function reaches the importer. So **graph precision and
impact relevance are separate problems, and parsing correctly does not fix the
second**; that is the argument for function-granularity structure (Exp 2's CPG)
over module-granularity imports. It also rules out the most obvious rival
explanation for the primary result: raters were not rewarding longer file lists,
since the one PR with unfounded extra references is the one that lost the endpoint
counting references.

---

## 5. What the thesis should and should not claim

**Claim:**
- Diff-only LLM review has a measurable structural blind spot, and structural
  graph context is a causally-identified remedy for it (Claims 1–4).
- Retrieval does not address that blind spot (Claim 3).
- The remaining gap is graph engineering, with a quantified path: +21pp from
  import/inheritance edges, ceiling at 0.93 (Claim 2).
- On real PRs the benefit is real, small, and precisely localised in the
  criteria the mechanism targets, and the localisation discriminates KG from
  RAG (Claim 5).
- The size of that benefit depends materially on evaluation choices, quantified
  three ways (Claim 6).
- Rubric-plus-LLM-judge evaluation of context augmentation is underpowered and
  fragile relative to oracle-based injection (Claim 9).

**Do not claim:**
- That KG context improves code review quality overall. The total-score effect
  is p = 0.054 exploratory, +0.42 non-significant on held-out data, and absent
  under three of four generators.
- That KG dominates RAG. It does not; they are complementary, and the
  localisation result is the evidence for complementarity, not for dominance.
- That the Experiment 1 lift is established as content-driven rather than
  prompt-driven. The 5-PR priming control does not support that (Claim 4).
- That the held-out test confirmed the finding. It agreed; it could not confirm.
- That the human study validates the Experiment 1 ranking. Its own pre-registered
  decision rule denies this: different samples, a different builder, different
  criterion wordings. It supports the narrower statement that raters perceive the
  better grounding of affected components in a six-PR assisted-interface probe (§4).
- That the human study shows KG reviews are better. Overall usefulness is flat at
  0.483 and all five exploratory criteria lean baseline (§4).
- Any human-study number from an interim look (n = 11 or n = 16), or a re-analysis
  at n > 20 presented as the confirmatory result (§4).
- Anything from `experiments/2026-05-14_confirmatory_kg/RESULTS.md`,
  `results/BOOTSTRAP_STATS_joern.md`, or the v1-era files. All superseded.

---

## 6. Known seams to disclose rather than hide

1. **Different graph builders across experiments** — four, not three:
   lexical/grep (Exp 1 headline), Joern CPG (Exp 2), scoped AST restricted to
   functions overlapping the changed hunks (sensitivity), and a plain AST
   import resolver (human study, `build_evidence.py` metadata
   `kg_builder = ast_import_resolver`). Defensible as different instruments for
   different questions, and the builder-parity run quantifies part of the
   difference (Claim 6). Disclose; do not imply one unified builder, and do not
   conflate the human study's import resolver with the scoped-AST sensitivity
   builder — they differ in granularity, which §4 shows to matter.
2. **Different temperatures** — Exp 1 at T = 0.0, Exp 2 at T = 0.3 (hardcoded in
   `prnote/note.py::generate_review_direct`). No methodological justification;
   state it as a limitation.
3. **Generator/judge family overlap** — gpt-4o generates and also judges. Claim 6
   shows the effect leans on that judge. A judge outside the generator's family
   would separate self-preference from judge capability; not yet run.
4. **Lost run log** for the canonical 160-review generation. T = 0.0 is not
   bit-deterministic in any case, so this bounds reproducibility claims rather
   than invalidating results.
5. **Floating model aliases** rather than dated snapshots in the generation
   config; the API-returned model is not recorded.
6. **n = 40, not 48, in Experiment 2** — band supply shortfalls reported per band
   under the pre-registration's anti-goalpost rule, not back-filled.

---

## 7. Source index for this document

| Claim area | File |
|---|---|
| Experiment 2 headline + placebo + judge validation | `results/INJECTION_EXP2_RESULTS.md`, `experiments/2026-07-05_injection_exp2/out/JUDGE_VALIDATION.md` |
| Experiment 2 pre-registration | `experiments/2026-07-05_injection_exp2/docs/DESIGN_AND_PREREGISTRATION.md`, `DECISIONS.md` §13 |
| Experiment 1 headline | `results/BOOTSTRAP_STATS_v2.md` |
| Criterion localisation (new, 2026-08-31) | `results/CRITERION_CONCENTRATION.md` — `scripts/analyze_criterion_concentration.py` |
| Held-out replication (new, 2026-08-31) | `results/CONFIRMATORY_CLEAN.md`, `results/BOOTSTRAP_STATS_confirmatory_clean.md` — `scripts/rerun_confirmatory_heldout.py` |
| Judge sensitivity | `results/JUDGE_LEAVE_ONE_OUT.md` |
| Generator sensitivity | `results/CROSS_GENERATOR_v2.md` |
| Builder sensitivity (parity-corrected) | `results/BOOTSTRAP_STATS_joern_parity.md` |
| Priming control (inconclusive) | `results/KG_EMPTY_PRIMING_CONTROL.md` |
| Human study (final, n = 20) | `experiments/2026-07-06_user_study_prs/RESULTS_HUMAN_V4.md`, `.json` |
| Era map — read before citing any number | `results/ERA_GUIDE.md` |
