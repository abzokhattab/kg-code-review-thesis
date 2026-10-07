# Evidence digest — every study, every number, and what it answers

Written 2026-09-08. Assembled from the canonical result files, not from the
thesis prose, so it doubles as a check on the thesis. Every number below carries
the file it comes from.

Read this top to bottom once. Section 6 is the scorecard.

---

## 0. What exists

Four studies, run in this order. They measure different things and are not
interchangeable.

| # | Study | Design | n | Outcome measured |
|---|---|---|---|---|
| 1 | Rubric benchmark | observational, paired | 40 PRs | rubric coverage, 25 criteria |
| 2 | Defect injection | controlled, paired | 40 injections | detection of a planted defect |
| 3 | Component ablations | controlled, paired, pre-registered | 28 + 28 | detection of a planted defect |
| 4 | Human preference | pre-registered, blinded | 27 raters, 6 PRs | which of two reviews is preferred |

Shared throughout: generator `gpt-4o` at temperature 0, judge panel
`gpt-4o-mini` + `gpt-4o` + `gemini-2.5-flash` with majority vote and ties to 0.

---

## 1. Experiment 1 — the rubric benchmark

**Question.** Does supplying repository context improve the reviews an LLM
writes, and which kind of context?

**Design.** 40 pull requests from 5 repositories. Four arms generated from the
same frozen evidence pack, so the arms differ only in the context block:
diff-only baseline, knowledge graph, retrieval, and both. Every arm sees every
pull request, so comparisons are paired. Scored by the three-judge panel against
a 25-criterion rubric, of which **nine were designated in advance** as the ones
structural context should affect.

### Results

Source: `results/BOOTSTRAP_STATS_v2.md`

| Arm | Total /25 | vs baseline | p | KG-relevant /9 | vs baseline | p |
|---|---|---|---|---|---|---|
| baseline | 9.20 | — | — | 4.97 | — | — |
| **kg** | 9.82 | +0.62 | 0.054 | 5.58 | **+0.60** | **0.007** |
| **rag** | 10.07 | **+0.88** | **0.007** | 5.40 | +0.42 | 0.057 |
| hybrid | 9.93 | **+0.72** | **0.037** | 5.50 | **+0.53** | **0.008** |

**The crossing is the finding.** The graph arm wins the nine targeted criteria
and misses significance on the full rubric. Retrieval does the exact reverse.
They are complementary, not competing.

**The hybrid lands between them on both scales** — +0.72 against retrieval's
+0.88, +0.53 against the graph's +0.60. It does **not** combine their strengths.
Its context block is the two others concatenated with no joint ranking and no
shared budget, so dilution is the available explanation.

### Is the localisation real, or just where the line was drawn?

Source: `results/CRITERION_CONCENTRATION.md`

96% of the graph arm's total gain falls inside the nine predicted criteria,
against 36% expected if the gain were spread at random (p = 0.016, permutation
over criteria). The same test finds retrieval's gain **diffuse** (49%, p = 0.272)
and the hybrid intermediate (72%, p = 0.063).

This is the single most important result in Experiment 1. It separates the two
mechanisms statistically, which two aggregate scores cannot do.

### Robustness — the effect's size depends on the evaluator

| Varied | Configuration | KG-relevant Δ | p |
|---|---|---|---|
| — | headline | +0.60 | **0.007** |
| Judge | gpt-4o alone | +0.65 | **0.006** |
| | gpt-4o-mini alone | +0.23 | 0.430 |
| | gemini-2.5-flash alone | +0.38 | 0.185 |
| | external claude-sonnet-4.5 | +0.40 | **0.029** |
| Generator | claude-haiku-4.5 | +0.15 | 0.457 |
| | gemini-2.5-flash | +0.47 | 0.136 |
| | deepseek-v3 | +0.20 | 0.383 |
| Builder | code property graph (n=35) | +0.34 | 0.111 |
| | hunk-scoped AST (n=40) | +0.25 | 0.219 |
| Dataset | held-out set (n=12) | +0.42 | 0.312 |

**Read this honestly.** The direction survives everywhere; the significance does
not. Three points matter:

1. **Self-preference is ruled out.** `gpt-4o` both generated and judged, which is
   the worst case. An independent judge from a third provider reproduces the
   effect (+0.40, p = 0.029). So it is not models flattering themselves.
2. **Generator dependence is real and limits the claim.** No substitute generator
   reaches significance. All six of their estimates are positive, so direction is
   preserved, but this is the sharpest limitation in the thesis.
3. **The held-out test is uninformative, not negative.** It had 8–16% power. A
   null was the overwhelmingly likely outcome either way. Adequate power needs
   about 40 held-out PRs, not 12.

### What Experiment 1 does *not* establish

That graph context improves review quality **in general**. Its full-rubric effect
is p = 0.054. The supported claim is localised: it improves the criteria it was
predicted to improve, with this generator.

---

## 2. Experiment 2 — controlled defect injection

**Question.** Is the advantage *caused* by supplying dependency knowledge?

**Design.** Plant a defect whose consequence lies, by construction, in a
different file from the edit. Ask whether the review names the broken file.
Ground truth is deterministic — the experiment planted the defect, so it knows
the answer. **Pre-registered 2026-07-05, before any code was written.**

Two bands: **structural** (n=28, consequence elsewhere) and **local control**
(n=12, consequence visible in the diff itself).

### Results

Source: `experiments/2026-07-05_injection_exp2/out/RESULTS.md`

| Arm | Structural (n=28) | Local control (n=12) |
|---|---|---|
| baseline | **0/28 — 0%** | 11/12 — 92% |
| rag | 1/28 — 4% | 12/12 — 100% |
| **kg** | **15/28 — 54%** (p < 0.0001) | 10/12 — 83% |
| hybrid | 12/28 — 43% | 11/12 — 92% |
| kg_joern_inherit | 21/28 — 75% | 10/12 — 83% |
| kg_idealised | **26/28 — 93%** | 10/12 — 83% |

**This is the strongest result in the thesis.** Read the rows in order:

- **0/28 for the baseline.** Not "low" — *zero*. The information is absent from
  the prompt, not present and overlooked.
- **1/28 for retrieval.** Similarity-based context does not substitute. The
  mechanism is specifically dependency knowledge.
- **The local control band settles the rival explanation.** Every arm detects
  83–100% of defects that are visible in the diff, and the graph gives no
  advantage there. So this is not "more context helps" — context only helps when
  the answer is elsewhere.
- **The ceiling arm locates the shortfall.** With ground-truth dependents the
  reviewer reaches 26/28. So the model uses dependency information correctly when
  it has it, and the deployed arm's 15/28 is the *graph's* limit, not the model's.
- **The gap is nameable and mostly fixable.** Adding resolved inheritance edges
  reaches 21/28. The deployed builder's blind spot is that a call graph models
  calls, not inheritance — and base-class changes break dependents by inheritance.

### The hybrid is worse than the graph alone here

15/28 for the graph, 12/28 for graph+retrieval. The retrieved chunks crowd out
the one caller that mattered. This is the same dilution seen in Experiment 1,
visible more sharply because the outcome is binary.

---

## 3. Component ablations

**Question.** Which parts of the graph block carry the effect?

**Why they are not on the rubric.** Five attempts on the rubric returned nothing:
deleting either section, scrambling either section's contents, and a three-judge
re-analysis of an older ablation. That is a property of the instrument, not the
components — the whole graph effect is 0.60 rubric points and **regenerating an
identical prompt moves the score by 0.88** (`results/GENERATION_VARIANCE.md`).
A component worth a fraction of the effect sits below the noise floor.

Both ablations therefore run on the detection oracle. Both pre-registered.

### 3a. Which kind of dependency evidence

Source: `results/EXP2_FEATURE_ABLATION.md`

The deployed graph supplies two kinds at once. Each arm supplies one.

| Arm | Evidence | Detected | p (Holm) vs baseline |
|---|---|---|---|
| baseline | none | 0/28 | — |
| `kg_deps_only` | lexical file list (10% precise) | **9/28** | **0.012** |
| `kg_edges_only` | resolved call edges | **12/28** | **0.002** |
| kg | both | 15/28 | — |

**Both contribute independently and significantly.** Neither alone is
significantly below having both, so they substitute rather than being jointly
required.

**The crude list is not decoration.** A file-level list that is wrong about nine
edges in ten still recovers 9 of the 15 detections. Naming a plausibly-related
file is enough to make the reviewer look at it.

**This also bridges the two experiments.** `kg_deps_only` is Experiment 1's
builder with the Joern edges removed — so Experiment 1's own builder produces a
significant causal effect on Experiment 2's oracle.

### 3b. Whether the test section contributes

Source: `results/TEST_ORACLE.md`. Rename a symbol that test files import, so
those tests provably break. Score whether the review names one. Grafana only —
the other two repositories have no tests in scope.

| Arm | Names a broken test | Generic test talk |
|---|---|---|
| baseline | **0/28 — 0%** | 22/28 — 79% |
| kg (deps, tests removed) | **0/28 — 0%** | 28/28 — 100% |
| + tests, deployed finder | **24/28 — 86%** | 23/28 — 82% |
| + tests, ground truth | **27/28 — 96%** | 25/28 — 89% |

Both test arms beat the graph arm at **p < 0.0001**, and they do not differ from
each other (p = 0.38) — so the deployed filename-convention finder is as good as
being handed the answer.

**Two things follow.**

The dependency list does **not** substitute for the test list. The graph arm had
the full dependency list and named a breaking test in **none** of 28 cases.

And this explains the five rubric nulls. Reviews remark that tests are affected
in four cases out of five **with no context at all**. The rubric criterion that
would register the test section is satisfied by that boilerplate, so it sits at
its ceiling in every arm. The signal was real; the ruler had no headroom.

---

## 4. Human study

**Question.** Do human practitioners see the same thing the judge panel sees?

**Design.** 27 raters, blinded to arm, comparing two reviews of the same pull
request on six criteria. Six pull requests from three Python libraries
(`requests`, `flask`, `click`). Graph block built by an AST import resolver — a
third construction, different from either experiment. Pre-registered target of
18–20 raters, frozen 2026-07-06 before any response arrived.

### Results

Source: `experiments/2026-07-06_user_study_prs/RESULTS_HUMAN_V4.md`

| Endpoint | Preference for kg | Interval | p |
|---|---|---|---|
| **F3\* — names affected code** (primary) | **0.710** | [0.623, 0.787] | **0.0005** |
| overall usefulness (secondary) | 0.512 | [0.423, 0.605] | estimation only |
| F2\*, T3, Q5, C6 (exploratory) | 0.45–0.49 | — | not significant after Holm |
| R1 — code clarity (exploratory) | 0.414 | [0.370, 0.460] | 0.028 (Holm), favours baseline |

Over 120 comparisons: kg preferred 75, baseline 25, both 17, neither 3.
Rank-biserial r = 0.87.

**The pre-registered primary endpoint is met**, and the secondary is flat. Both
halves were predicted in advance. Together they say something more precise than
either alone: **the graph changes what a review grounds itself in, and does not
change how useful it feels overall.**

That is the same dissociation the judge panel produced on 40 different pull
requests with a different builder — the effect concentrates on naming affected
code while the aggregate barely moves.

**Stopping was not data-dependent.** Collection ended at 20, the *upper* bound of
a target frozen before any data. Interim looks at n = 11 and n = 16 happened and
are disclosed; they did not move the target. If more raters arrive they are a
labelled sensitivity analysis, not the primary.

**Honest caveats.** All five exploratory criteria lean *baseline*, none
significantly. And on one pull request (flask, trusted hosts) raters rejected the
graph arm's extra file references as unfounded — the edges were correct imports,
but a module-level import does not mean a change to one function reaches the
importer. Correct is not the same as relevant.

---

## 5. Supporting measurements

| Measurement | Result | Source |
|---|---|---|
| Lexical builder edge precision | **10.2%** | `BUILDER_VOLUME_PRECISION.md` |
| AST builder edge precision | **86.6%** | same |
| Generation noise, identical prompt | **0.88 /9**, identical in 14/32 | `GENERATION_VARIANCE.md` |
| Model drift, April vs September | none (−0.19, p = 0.51) | same |
| Judge agreement (κ) | 0.590–0.717 | `CHECKLIST_EVALUATION_REPORT__v2.md` |
| Rubric discriminates? | a hallucinated review scores 9.2 vs a real 9.0 | `sec:rubric` positive control |

The last row is important and uncomfortable: **the rubric measures coverage, not
correctness.** It cannot tell grounded specificity from fabricated specificity.
Every rubric number is a coverage measurement. The correctness claims come from
Experiment 2, where detection is checked against a planted defect.

---

## 6. Scorecard — what is answered

| RQ | Question | Verdict | Evidence |
|---|---|---|---|
| **1.1** | Does context improve review quality? | **Yes, on the metric each strategy targets. Not in general.** | rag +0.88 total (p=0.007); kg +0.60 subscale (p=0.007); kg total p=0.054 |
| **1.2** | Which strategy is best? | **No winner — they are complementary.** Hybrid lands between, does not combine. | the crossing, plus concentration 96% vs 49% |
| **1.3** | Is the mechanism surfacing consequences outside the diff? | **Yes — strongest result.** | 0/28 → 15/28 → 26/28, with the local control flat |
| **2.1** | Which components carry it? | **Both dependency kinds do, independently. The test section is irreplaceable.** | 9/28 and 12/28 both significant; 0/28 → 24/28 for tests |
| **3.1** | Do humans agree with the judge? | **Yes on the targeted criterion, and they agree it does not generalise.** | 0.710 (p=0.0005) with usefulness flat at 0.512 |

### What cannot be claimed, and must not be

1. **That the graph improves review quality overall.** Total-scale p = 0.054.
2. **That the hybrid beats both.** It lands between them on both scales.
3. **That the effect is generator-independent.** It reaches significance under
   none of three substitutes.
4. **That the rubric measures review correctness.** It measures coverage; the
   positive control proves it cannot tell fabricated specificity from grounded.
5. **That the held-out test replicated.** It had 8–16% power and settles nothing.

---

## 7. The argument in five sentences

Supplying an LLM reviewer with repository structure produces a **large, causal,
narrow** capability gain: without it, cross-file defects are found **zero** times
out of 28; with it, 15, and with a perfect graph, 26.

That capability shows up in ordinary review quality as a **small and localised**
improvement — +0.60 on the nine criteria it targets, with **96%** of the gain
landing inside them, and nothing significant on the rubric as a whole.

**Twenty-seven blinded practitioners see the same shape**: they prefer the graph-grounded
review on naming affected code (0.710) and are indifferent on overall usefulness.

The components behave differently from expectation: **both kinds of dependency
evidence work independently, a 10%-precise file list recovers most of what a
resolved call graph does, and the test list is irreplaceable** — none of which
the coverage rubric could detect, because its noise floor exceeds the effect.

The honest headline is therefore not "knowledge graphs improve code review" but
**"structural context causes a specific, measurable capability that current
review-quality instruments are too coarse to see."**
