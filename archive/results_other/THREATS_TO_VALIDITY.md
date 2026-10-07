# Threats to Validity (ready-to-paste draft — v2/Joern era)

_Rewritten 2026-07-06 against the current experimental state (40-PR v2
dataset; Joern-era re-run; injection probe; human study v4). The previous
version of this file cited the deprecated v1 era (25 PRs, 4 repos) and is
preserved in git history. Numbers cite `results/BOOTSTRAP_STATS_v2.md`
(era 2) and `results/FINAL_RESULTS_REPORT.md` (era 3); see
`results/ERA_GUIDE.md` for which numbers may be combined. Where a threat's
framing depends on the pending era-2-vs-era-3 headline decision, it is
marked **[era-dependent]**._

---

## 8.1 Construct validity

_Are we measuring what we claim to measure?_

### 8.1.1 LLM-as-a-judge bias

**Threat.** LLM judges share training data and stylistic priors with the
generators under test. A judge could reward its own family's output
(family bias), verbose output (verbosity bias), or textbook review style,
none of which correspond to "the review is good".

**Mitigation.** All headline runs use a three-judge cross-provider panel
with majority vote (ties → 0): gpt-4o-mini + gpt-4o + gemini-2.5-flash in
era 2; gpt-4o + gemini-2.5-flash + gemini-2.0-flash in era 3. Per-judge
verdicts are published (`checklist_evaluation_llm_multi__v2.json`) so any
aggregation rule can be re-applied. Temperature is 0.0 for generation and
judging. A dedicated verbosity analysis (`JUDGE_LENGTH_BIAS.md`) checks
whether score correlates with review length independently of content.

**Residual risk.** All judges are transformer models trained on
overlapping web corpora; a shared style prior cannot be excluded. The
human study (RQ3) is the partial external check on the judge construct.

### 8.1.2 Checkbox rubric saturates on small, self-contained PRs

**Threat.** The 25-criterion rubric asks binary "does the review address
X?" questions. On small PRs whose diffs already contain their own tests
and callers, a diff-only review can tick every KG-relevant box, leaving no
headroom for augmentation to show — the rubric then *under-measures*
grounding depth rather than measuring quality.

**Evidence.** On the six deliberately legible human-study v4 stimuli, the
baseline scores 9/9 on the KG-relevant criteria on *all six PRs* (judge
panel, 2026-07-06) — a complete ceiling — while a reference-verification
audit shows only the KG reviews ground claims in real off-diff files. The
40-PR sample does not have this ceiling (era-2 baseline KG-relevant mean
4.97/9), which is precisely why the main experiment uses larger PRs.

**Mitigation.** RQ2 claims are made on the 40-PR sample. The human study
complements the rubric with a comparative judgment ("which review does X
*better*") plus mechanical reference verification, capturing the dimension
the binary rubric saturates on. A graded 0–3 pilot
(`GRADED_SCALE_RESULTS.md`) probes the same ceiling on the main sample.

**Residual risk.** No single instrument measures "review quality"
directly; the thesis triangulates rubric, injection probe, and human
perception, and says so explicitly.

### 8.1.3 "KG-relevant" label is author-assigned **[era-dependent]**

**Threat.** The designation of 9 of 25 criteria as "KG-relevant" (era 2)
was made by the author; post-hoc selection would inflate the effect.

**Mitigation.** The labels are pre-registered in code
(`EVALUATION_CRITERIA[i].kg_relevant`, `scripts/evaluate_reviews.py`) and
were independently re-annotated by a blind model given only a
content-derived rule: raw agreement 21/25 (84%), **κ = 0.615**
(`RUBRIC_KAPPA_kg_relevant.md`). All 25 per-criterion deltas are published
so a reader can re-aggregate under their own labels. Era 3 additionally
re-bases to the 15 non-degenerate criteria (6 KG-active), removing
always-0/always-1 criteria from the denominator.

**Residual risk.** The era-3 re-basing changes denominators (/6 vs /9);
any table must state which basis it uses (see `ERA_GUIDE.md`).

### 8.1.4 Binary Yes/No over-simplifies

**Threat.** A review can partially address a criterion; 0/1 collapses
degree, and saturated criteria contribute nothing to discrimination.

**Mitigation.** Judges are instructed to score 1 only for clear,
non-vague coverage (system prompt in `scripts/evaluate_reviews.py`),
mirroring DeepCRCEval's binary scheme for comparability. A graded 0–3
anchored pilot on 27 KG-rich PRs (`GRADED_SCALE_RESULTS.md`) checks the
ceiling directly. Era 3 drops the 10 degenerate criteria.

**Residual risk.** Grading nuance ultimately shifts to the human study,
whose per-criterion comparative format ("A / B / both / neither") is
ordinal by construction.

---

## 8.2 Internal validity

_Do the causes we claim actually produce the effects we observe?_

### 8.2.1 Prompt confound: instructions vs. injected facts

**Threat.** The KG prompt differs from the baseline prompt not only in
the injected repository facts but also in the instruction to use them. A
lift could be mere instruction priming ("look for integration risks"),
not use of the graph.

**Mitigation.** Two controls. (1) *Placebo control:* the empty-KG priming
run (`CHECKLIST_EVALUATION_REPORT__kgempty_priming.md`,
`scripts/generate_kg_empty_control.py`) sends the identical KG system
prompt with an empty facts block, isolating the priming component of the
lift. (2) *Prompt-symmetric baseline:* the human-study arms share one
strict system prompt with identical mandatory coverage; only the evidence
block differs (`experiments/human_study_reviews/generate_baseline_strict.py`).

**Residual risk (quantified 2026-08-18 — larger than this section previously
implied).** The placebo comparison had never been computed; the report file's
summary table is empty because `kgempty` is not one of the four standard modes.
`scripts/compare_kg_empty_priming.py` computes it
(`results/KG_EMPTY_PRIMING_CONTROL.md`). On the era-matched v1 panel the priming
and content components are **equal**: empty-facts prompt +0.20 over baseline on
/25, full KG a further +0.20 (KG-relevant: +0.40 and +0.20). On the three PRs
that also exist in v2, the empty-facts prompt scores *above* full KG. The control
covers 5 PRs and predates the v2 rebuild, so it cannot settle the question — but
it does not support the claim that the lift is content rather than instruction,
and this section must not be cited as though it did. The 40-PR re-run of the
placebo was **cancelled by supervisor decision (2026-09-05)**, so the priming
defence rests permanently on the injection probe (8.2.3), which is immune by
construction: a prompt with an empty facts block cannot name a dependent file it
was never given.

**Do not turn this subsection into thesis prose.** Same decision: instruction
priming is not to be raised as a named threat in Chapter 8, because the attention
it would draw is out of proportion to its weight. The limitation is already
recorded, accurately and briefly, in Chapter 6
(§`sec:results-exp1-priming`), and that is where it stays. What survives the
decision is the claim ceiling, which is not negotiable: no sentence may assert
that the Experiment 1 lift is content-driven rather than instruction-driven.

### 8.2.2 Correlation only: merged PRs have no ground-truth defect

**Threat.** On real merged PRs there is no ground truth for "the review
caught the real problem"; rubric scores measure coverage, not detection.

**Mitigation.** The controlled bug-injection probe complements the
observational study: 8 single-symbol renames of top-level sklearn symbols
whose blast radius is entirely cross-file. Detection of the true broken
dependents: **baseline 0/8, RAG 1/8, idealised import-level AST KG 8/8,
deployed Joern-CPG KG 4/8** (hybrid: 8/8 idealised, 3/8 Joern)
(`exceptional test/prototype/FINDINGS_SCALE.md`). This is causal evidence
that structural context — and only structural context — surfaces
cross-file breakage, and it quantifies the deployed builder's edge-recall
gap (missing inheritance edges account for the 4 misses).

**Residual risk.** The probe covers one defect class (renames) in one
repository; the pre-registered scaled Experiment 2
(`experiments/2026-07-05_injection_exp2/docs/DESIGN_AND_PREREGISTRATION.md`)
is designed but not yet run.

### 8.2.3 Survivorship: merged PRs only

**Threat.** All 40 PRs were merged; code that survived review may be
cleaner than typical review-time code, deflating the room for any mode to
find issues (survivorship bias).

**Mitigation.** The design compares four modes *on the same PRs with the
same generator*; selection acts equally on all arms and cancels in the
paired deltas. Selection was direction-blind
(`dataset_v2/docs/SELECTION_v2.md`), and using merged PRs follows standard
practice in the code-review-generation literature (Tufano et al.;
CodeReviewer), keeping results comparable.

**Residual risk.** Absolute score levels generalise only to
merged-quality code; relative mode effects are the claim.

### 8.2.4 Human-study stimulus selection (v4)

**Threat.** The v3 human study used 6 PRs from the 40-PR sample
(sklearn/kafka/jenkins/grafana); piloting showed raters could not evaluate
them — unfamiliar languages, huge repos, and reference claims they could
not verify. Replacing the stimuli introduces a selection step.

**Mitigation.** The v4 stimuli (6 merged PRs from requests/flask/click)
were selected by pre-stated legibility criteria (2–5 files, 10–400 LoC,
descriptive body) *and* KG-richness (7–17 importing files), from ~300
candidates, before any reviews were generated
(`experiments/2026-07-06_user_study_prs/README.md`). Reviews use the v3
prompt verbatim; every file reference in every review was mechanically
verified against the repository at the PR's head commit (zero fabricated
references; the answer key ships in the UI). The analysis plan and power
analysis were frozen before data collection (`ANALYSIS_PLAN.md`,
`POWER_ANALYSIS.md`).

**Residual risk.** Legibility creates the rubric ceiling documented in
8.1.2, and the v4 stimuli are outside the 40-PR sample: the human study
is a *perception probe* of the grounding difference, not an effectiveness
estimate on RQ2's population. The KG for these stimuli is an AST import
resolver, not Joern (recorded in evidence metadata) — same relation class,
exact for Python at this repo size.

### 8.2.5 Hybrid mode is not prompt-optimised **[era-dependent]**

**Threat.** Hybrid concatenates the KG and RAG blocks without
deduplication or length control; its result may reflect the naive
template, not the ceiling of combined augmentation.

**Mitigation.** In era 2, hybrid is statistically indistinguishable from
kg alone on KG-relevant criteria (+0.53 vs +0.60; both p<.01) — reported
as "no synergy from naive stacking", not as harm. Attribution analyses
(`HYBRID_WIN_ATTRIBUTION.md`) decompose which block drives hybrid wins.

**Residual risk.** An engineered hybrid (routing, dedup, budget-aware
merging) is untested; listed as future work.

---

## 8.3 External validity

_Do the results generalise beyond the evaluated setting?_

### 8.3.1 Sample size and repository coverage

**Threat.** 40 PRs from five repositories (grafana, kafka, scikit-learn,
godot, jenkins) support directional mode-level claims, not per-repository
or per-language claims.

**Mitigation.** The five repositories span four language ecosystems:
TypeScript/Go (Grafana), Java (Kafka, Jenkins), Python/Cython
(scikit-learn), and C++ (Godot). Era-2 claims are made at the
aggregate level with bootstrap CIs and paired permutation tests over
40 paired observations; per-criterion numbers are descriptive. A
KG-richness moderator analysis (era 3: KG-rich subgroup n=31, Δ=+0.774,
p=.001, d_z=.64) reports when the effect exists at all.

**Residual risk.** Language-level effects are visible but underpowered;
not claimed.

### 8.3.2 Generator dependence of the KG lift

**Threat.** Headline runs use gpt-4o as generator; the lift could be
model-specific.

**Mitigation & finding.** Two checks. (1) Era 3 re-ran the full Joern
condition with gemini-2.5-flash as generator: d_z = +1.34 vs +1.24 for
gpt-4o — generator-robust at that capability tier. (2) A 5-PR Claude
Sonnet 4.5 replication (`CROSS_GENERATOR_REPLICATION.md`) shows the lift
*vanishes and mildly reverses* (−0.40 on KG-relevant) when the baseline
already saturates the KG-relevant criteria (Claude baseline 8.0/9 = 89%
vs gpt-4o 4.4/9). The thesis therefore states RQ2 conditionally: **KG
injection lifts rubric-measured quality for generators whose baseline has
not saturated the KG-relevant criteria**; the effect size is a function
of the baseline-to-ceiling gap.

**Residual risk.** The Claude check is n=5 and directional; a full-scale
strong-generator ablation is future work. The saturation-conditional
claim predicts the sign in both checks, which is the strongest evidence
available short of that run.

### 8.3.3 KG-builder dependence

**Threat.** "The knowledge graph" is not one artifact: grep-based,
scoped-AST, and Joern-CPG builders produce different edge sets, and
results could be builder-specific.

**Mitigation.** This is measured, not assumed. (1) Pre-registered
sensitivity on the 40 PRs (`SENSITIVITY_v2_grep_vs_ast.md`): the
scoped-AST variant yields a *smaller* lift than grep-based (kg mean 9.65
vs 9.82) — outcome rule 3, "effect depends on KG-construction choice".
(2) The injection probe quantifies builder faithfulness on ground truth:
idealised AST 8/8 vs deployed Joern 4/8 vs grep-fallback 2/8, with the
Joern misses traced to missing inheritance edges. The thesis reports
**edge precision/recall of the builder as the operative lever**, not
"KG yes/no".

**Residual risk.** No builder tested is complete; results characterise
the tested builders, and the inheritance-edge fix is proposed future
work.

### 8.3.4 Training-data contamination

**Threat.** The PRs are public and predate the models' training cutoffs;
generators may "remember" rather than "review".

**Mitigation.** All claims are relative comparisons of four modes on the
same PRs with the same generator; contamination inflates all arms'
absolute scores equally and cancels in paired deltas. The injection probe
is contamination-proof by construction — the injected defects never
existed in any repository state the models could have trained on.

**Residual risk.** Absolute score levels may be optimistic; deltas are
the claim. A replication on post-cutoff PRs remains the cleanest fix.

### 8.3.5 English-only

Not applicable — no multilingual claim is made.

---

## 8.4 Conclusion validity

_Can we draw the statistical conclusions we claim?_

### 8.4.1 Multiple comparisons

**Threat.** 25 criteria × 3 mode contrasts invite cherry-picking.

**Mitigation.** The confirmatory claim is the pre-registered
KG-relevant-bucket aggregate with bootstrap CI and paired sign-flip
permutation test (`BOOTSTRAP_STATS_v2.md`); per-criterion results are
descriptive. Where per-criterion inference is reported, it is
Kruskal-Wallis with Bonferroni correction
(`KRUSKAL_BONFERRONI_v2.md`). The human study pre-registers one primary
endpoint (F3*) with Holm correction on the exploratory criteria
(`experiments/2026-07-06_user_study_prs/ANALYSIS_PLAN.md`).

**Residual risk.** Standard; the pre-registration files are timestamped
in git.

### 8.4.2 Aggregation-rule dependence

**Threat.** Majority vote with ties→0 is the strict choice; other rules
give different magnitudes.

**Mitigation.** The rule is documented and the full per-judge detail is
published (`checklist_evaluation_llm_multi__v2.json`), so any rule can be
re-applied without re-querying models.

**Residual risk.** Negligible given published raw verdicts.

### 8.4.3 Human-study power **[pre-registered]**

**Threat.** With an 18–20-complete-rater target, underpowered endpoints could be reported
as null and over-interpreted.

**Mitigation.** A simulation-based power analysis
(`experiments/2026-07-06_user_study_prs/POWER_ANALYSIS.md`) sizes the
design in advance: at n=15, the primary endpoint (F3*) has simulated
power 0.79 under the diluted scenario and 0.99 under the pilot-like
scenario; at n=18 these rise to 0.87 and 1.00. Overall usefulness is
explicitly declared estimation-only because it is underpowered at
plausible effects. Decision rules for both positive and null outcomes are
stated before data collection.

**Residual risk.** Below 18 complete raters, the intended power depends more
strongly on the realised effect scenario; incomplete sessions are descriptive
only (rule in `ANALYSIS_PLAN.md`).

---

## 8.5 Reliability and reproducibility

### 8.5.1 API non-determinism

**Threat.** LLM APIs are not strictly deterministic even at temperature
0.0, and models get deprecated.

**Mitigation.** Temperature 0.0 throughout; model slugs recorded in every
output file; raw per-judge verdicts and generated reviews archived so all
analyses re-run from artifacts without API access.

**Residual risk.** Exact regeneration after model retirement is
impossible; analysis-level reproduction is guaranteed by the archived
artifacts.

### 8.5.2 Malformed judge output

**Threat.** A brittle parser could silently drop malformed judge JSON.

**Mitigation.** Tolerant fallback parser plus a retry pass
(`scripts/evaluate_reviews.py`, `scripts/retry_failed_judges.py`); the v2
dataset has three valid judges for every (PR × mode) cell.

**Residual risk.** None at the current 0% parse-failure rate.

### 8.5.3 Environment drift

**Mitigation.** Dependencies pinned (`requirements.txt`,
`requirements-eval.txt`); scripts are idempotent and cache-aware; the
data manifest (`results/DATA_MANIFEST.md`) maps each output file to the
script that produced it.

### 8.5.4 Era confusion inside the artifact **[meta]**

**Threat.** The repository contains three experimental eras whose
numbers are not interchangeable (different dataset size, KG builder,
judge panel, criteria denominators). Mixing them — by an author, reader,
or AI assistant — produces plausible-looking but wrong claims; an
AI-generated podcast summary of this thesis was found to do exactly that.

**Mitigation.** `results/ERA_GUIDE.md` (one page) defines the eras, their
files, their headline numbers, and the pending canonical-era decision.
Thesis tables must cite one era each and label it.

**Residual risk.** Discipline-dependent; the guide reduces but cannot
eliminate the risk.

---

## 8.6 Summary table

| Dimension | Threat | Mitigation | Residual |
|-----------|--------|------------|----------|
| Construct | Judge family/style bias | Cross-provider 3-judge panel; raw verdicts published; length-bias analysis | Shared-corpus prior possible |
| Construct | Rubric saturates on small PRs | 40-PR sample for RQ2; comparative human judgment + reference verification for RQ3; graded pilot | No single instrument suffices |
| Construct | Author-assigned KG-relevant labels | Pre-registered in code; independent re-annotation κ=0.615; all 25 deltas published | Era-3 re-basing changes denominators |
| Construct | Binary scoring | Strict thresholds; graded 0–3 pilot; era-3 drops degenerate criteria | Nuance shifts to human study |
| Internal | Instruction priming vs KG content | Empty-KG placebo; prompt-symmetric baseline; injection probe is priming-free | Priming share reported per PR |
| Internal | No defect ground truth on merged PRs | Injection probe: baseline 0/8, RAG 1/8, ideal KG 8/8, Joern 4/8 | One defect class; scaled Exp-2 pending |
| Internal | Survivorship (merged PRs) | Paired same-PR design cancels selection; standard practice | Absolute levels only for merged-quality code |
| Internal | v4 stimulus re-selection | Pre-stated criteria; verbatim prompts; mechanical reference verification; frozen analysis plan | Perception probe, not effectiveness estimate |
| Internal | Hybrid not optimised | Reported as "no synergy from naive stacking" (era 2) | Engineered hybrid untested |
| External | 40 PRs, 5 repos | Aggregate claims with CIs; moderator analysis | No per-language claims |
| External | Generator dependence | Gemini-generator replication (d_z 1.34); Claude saturation check | Saturation-conditional claim; n=5 check |
| External | KG-builder dependence | Pre-registered grep-vs-AST sensitivity; builder-faithfulness probe | No complete builder tested |
| External | Training-data contamination | Relative deltas cancel; injection probe contamination-proof | Absolute levels optimistic |
| Conclusion | Multiple comparisons | Pre-registered aggregate + Bonferroni/Holm elsewhere | Standard |
| Conclusion | Aggregation rule | Raw per-judge detail published | Negligible |
| Conclusion | Human-study power | Simulated power; single primary endpoint; null decision rule | <10 raters → descriptive only |
| Reliability | API non-determinism | Temp 0; artifacts archived; slugs recorded | Exact regen impossible post-deprecation |
| Reliability | Era confusion | `ERA_GUIDE.md`; one era per table | Discipline-dependent |
