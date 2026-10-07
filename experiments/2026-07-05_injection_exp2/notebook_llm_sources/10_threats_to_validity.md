# Threats to Validity (ready-to-paste draft)

_This chapter inventories the threats to the four canonical validity
dimensions — construct, internal, external, and conclusion — plus
reliability / reproducibility, which sits across the other four. Each
threat is paired with a concrete mitigation and a residual-risk
statement. Numbers cite the multi-judge LLM run
(`results/checklist_evaluation_llm.json`) and the inter-judge analysis in
`results/checklist_evaluation_llm_multi.json`._

---

## 8.1 Construct validity

_Are we measuring what we claim to measure?_

### 8.1.1 LLM-as-a-judge bias

**Threat.** LLM judges share training data and stylistic priors with the
generators under test. A judge could systematically reward its own
family's output (family-bias), verbose output (verbosity-bias), or the
first option seen (position-bias), none of which correspond to "the
review is good".

**Mitigation.** We use a three-judge cross-provider panel
(`gpt-4o-mini`, `gpt-4o`, `gemini-2.5-flash`) with majority-vote
aggregation (ties → 0). Cross-provider agreement is reported alongside
within-provider agreement: `gpt-4o ↔ gemini-2.5-flash` reaches
κ = 0.70, *higher* than `gpt-4o-mini ↔ gpt-4o` at κ = 0.67, giving
partial evidence that the headline effect is not an OpenAI-specific
artefact. Temperature is fixed at 0.0 to remove within-call randomness.

**Residual risk.** All three judges are transformer-family models
trained on broadly overlapping web corpora, so a shared "textbook
review style" bias cannot be fully ruled out. We report this as a
limitation rather than a resolved concern.

### 8.1.2 Rubric semantic drift between human and LLM evaluation

**Threat.** The human-study rubric uses stricter wording on two
criteria than the LLM checklist:
- `F3*` ("name *concrete* components …") vs. LLM `F3` ("check
  integration …")
- `F2*` ("describe *concrete* edge cases …") vs. LLM `F2` ("identify
  edge cases …")

Humans are therefore expected to say "yes" less often than the LLM
judge would on the same review, even for identically-labelled criteria.

**Mitigation.** The human ↔ LLM agreement analysis (`scripts/
analyze_human_llm_agreement.py`) flags `F3*` and `F2*` as
*stricter-on-human-side* in every output table so readers can interpret
lower raw agreement on those two criteria appropriately. The thesis
compares human→LLM κ on shared-wording criteria (`T3`, `Q5`, `R1`, `C6`)
as the primary validity signal and uses `F3*`/`F2*` only as descriptive
evidence.

**Residual risk.** A κ below 0.40 on a tightened criterion cannot
be distinguished from a rubric mismatch without a second human pass on
the looser wording. This is documented as future work.

### 8.1.3 "KG-relevant" label is author-assigned

**Threat.** The pre-registration of nine criteria as "KG-relevant"
(F3, F4, T1, T2, T3, M1, M3, C2, Q2) was made by the author before the
evaluation run. Post-hoc selection would inflate effect size; our
pre-registration removes that concern in principle but not in practice
if readers dispute the labels.

**Mitigation.** The labels are in the code (`EVALUATION_CRITERIA[i].
kg_relevant` in `scripts/evaluate_reviews.py`) and in the published
checklist file, timestamped. The thesis additionally reports the raw
per-criterion deltas for *all 25 criteria*; a reader who disagrees
with the labels can re-aggregate.

**Residual risk.** Three of the nine KG-relevant criteria (M1, M3, Q2)
show zero or negative deltas; removing them tightens the effect size
but is not reported as the headline because it would be post-hoc.

### 8.1.4 Binary Yes/No over-simplifies nuanced reviews

**Threat.** A review can partially address a criterion; collapsing to
0/1 discards that nuance and, at the extremes, can invert the ordering
between two reviews that differ only in degree.

**Mitigation.** Rubric items were authored with explicit "counts as
yes" thresholds (e.g. "references specific test files" — not just "asks
about testing in general"). Judges are instructed to "score 1 only if
the review CLEARLY addresses the criterion; score 0 if the criterion
is not addressed or only vaguely mentioned". The binary scheme mirrors
DeepCRCEval (Lu et al., 2024), which makes the results comparable
with prior work.

**Residual risk.** For the three saturated criteria
(Q1 = 100 %, Q2 = 100 %, Q4 = 0 % across all modes), the binary scale
contributes zero to mode discrimination. These criteria are excluded
from the reported means on the KG-relevant subset where the result
depends on them (Q2 is the only case).

---

## 8.2 Internal validity

_Do the causes we claim actually produce the effects we observe?_

### 8.2.1 Generation-time prompt variance

**Threat.** Different modes (baseline / KG / RAG / hybrid) use
different prompt templates of meaningfully different lengths. A
performance difference could in principle be attributable to "the
model prefers one prompt length" rather than "the model uses the
augmentation signal".

**Mitigation.** All four modes share the same system prompt, same
output template, and the same base model. The KG/RAG/hybrid prompts
are the baseline prompt *plus* an augmentation block. Temperature is
0.0 for generation *and* for evaluation. The per-criterion pattern
(KG wins on the exact criteria the augmentation surfaces) is
inconsistent with a generic length-based preference and is positive
evidence that the augmentation signal is the cause.

**Residual risk.** We cannot fully distinguish "the model uses the KG
content" from "the model writes in a different stylistic register
when given more context, and the register happens to win on F3/T3".
Both interpretations are consistent with the observed data; both
support the thesis's practical claim (KG augmentation improves
integration/testing coverage).

### 8.2.2 Stimulus selection for the human study

**Threat.** The six PRs shown to human raters (PR 18, 10, 14, 22, 15,
21) were selected for maximum discriminative power using the
**single-judge** pilot scores. Re-selecting with the multi-judge data
would produce a slightly different stimulus set.

**Pre-deployment stimulus swap.** A pre-deployment review flagged one
of the originally selected PRs (PR 26, Django \#18322) as a weak
stimulus: it is a *revert* of a readability refactor, its descriptive
title telegraphed the expected review content, and under the
multi-judge data its KG-vs-baseline delta on KG-relevant criteria
collapses to zero (B=4, KG=4, R=4 on nine KG-relevant criteria).
PR 26 was therefore **excluded before any production human data was
collected** and replaced with PR 18 (Jenkins \#9002, "Further reduce
usages of \texttt{StringUtils}"). PR 18 is a real seven-file refactor
(core + four test files) where the multi-judge KG scores beat both
baseline and RAG on KG-relevant criteria ($\Delta_\text{KG-B}=+1$,
$\Delta_\text{KG-R}=+2$) and the diff size/topic matches the cognitive
load envelope of the other five stimuli. We record this swap here
rather than burying it: it is the only change to the stimulus set
after its initial definition, and it post-dates Christian's pilot v1
(whose PR-level results were inspected and did not depend on PR 26's
inclusion).

**Mitigation.** Apart from the swap above, we froze the stimulus set
and kept it frozen through the 6-criterion revision so that human
data across pilots is comparable. The selection criterion
(per-pair "flips" between modes) is independent of the absolute yes
rates, which is the dimension most affected by the judge change. The
human-study rubric is tightened (F2*, F3*, C6) relative to the LLM
checklist anyway, so re-running the selection on multi-judge scores
would not produce a dramatically different set.

**Residual risk.** A small amount of selection bias remains: PRs where
single-judge gpt-4o-mini happened to be most strict are over-represented.
We document this in the thesis and note that extending to additional
PRs (especially from a fifth repository) is the cheapest future work.

### 8.2.3 The hybrid mode is not prompt-optimised

**Threat.** The hybrid mode simply concatenates the KG block and the
RAG block with a shared header. No deduplication, no reordering, no
length control. A negative result on hybrid could reflect an
unoptimised template rather than a fundamental limitation of
combining augmentations.

**Mitigation.** We present the hybrid result as a *negative result* for
naive augmentation stacking, not as a claim about the theoretical
upper bound of combined augmentations. The thesis Discussion
(§ 7.3) explicitly lists two alternative designs (inference-time
routing; merged retrieval surface) as future work.

**Residual risk.** A prompt-engineered hybrid could still beat KG
alone. The thesis does not claim otherwise.

---

## 8.3 External validity

_Do the results generalise beyond the evaluated setting?_

### 8.3.1 Small PR sample

**Threat.** The LLM evaluation covers 25 PRs drawn from four
repositories; the human study covers six of those 25. Neither is large
enough for repository- or language-specific claims.

**Mitigation.** Repositories are deliberately diverse (Java/Kafka,
TS/Grafana, Python/Django, Python/scikit-learn) to broaden the
construct coverage. The 25 PRs yield 100 (pr × mode) pairs and 2 500
binary judgements per judge — adequate for directional mode-level
comparisons. Per-criterion effects are reported as descriptive rather
than inferential, with ranges rather than single-number confidence
intervals on criteria with n = 25.

**Residual risk.** Language-level effects (e.g. "KG helps more for
Java than for TS") are visible in the data but not reported because the
per-repository sample is too small to support them.

### 8.3.2 Base-generator dependence of the KG lift

**Threat.** All reviews for the main ablation were generated with a
single base model (gpt-4o). A simple "KG improves reviews" claim would
not be generator-robust, because the KG-vs-baseline delta could be
gpt-4o-specific.

**Empirical test.** We ran a 5-PR cross-generator replication under
Claude Sonnet 4.5, using identical prompts, identical multi-judge panel
(`gpt-4o-mini`, `gpt-4o`, `gemini-2.5-flash`, majority vote), and a
sample stratified by KG fact-density (two high-density, three
low/mid-density). See
[`CROSS_GENERATOR_REPLICATION.md`](CROSS_GENERATOR_REPLICATION.md) for
full numbers.

**Finding.** The simple claim "KG improves reviews" **does not
generalise across generators.** Under gpt-4o, KG adds +0.60 points on
the 9 KG-relevant criteria (+6.7 pp, same sign as the full 25-PR run).
Under Claude Sonnet 4.5, KG scores **−0.40 points** on the same
criteria (−4.4 pp) because Claude's baseline already saturates the
KG-relevant subset (8.00/9 = 88.9% without any retrieved context,
versus gpt-4o baseline at 4.40/9 = 48.9%). On the two highest-KG-
density PRs (PR 3, PR 6), where KG has the *most* unique repo facts to
inject, Claude + KG scores −1.0 points on KG-relevant criteria versus
Claude baseline — the inverse of the intuitive prediction.

Inter-judge agreement is unchanged across generators (pairwise
κ = 0.61–0.75), so the flip is not judge noise.

**Refined claim adopted in this thesis.** We therefore report RQ2 with
an explicit conditional: **KG-based context injection improves
rubric-measured review quality on KG-relevant criteria for base
generators whose baseline is not already saturated on those criteria.**
Above that saturation threshold, KG provides no lift and may mildly
distract. The effect size of KG is a function of the *gap* between the
baseline generator's quality and the ceiling, not a property of the KG
in isolation. This interpretation is consistent with the saturation
pattern routinely reported in the retrieval-augmentation literature.

**Residual risk.** The 5-PR replication is directional (n too small
for a per-criterion significance test). A full 25-PR Claude ablation
is scheduled as a confirmation run and, if it reproduces the sign
flip, is promoted to a first-class RQ2 result rather than a robustness
footnote. A mid-strength generator row (e.g. gpt-4o-mini-as-generator)
would additionally pin down the crossover point.

### 8.3.3 English-only reviews

**Threat.** All reviews and review-target repositories are in English.
Non-English codebases or reviewer communities may behave differently.

**Mitigation.** Not applicable — we do not claim multilingual
generality.

### 8.3.4 LLM-as-a-judge limits the ceiling

**Threat.** The evaluation is upper-bounded by what a 2024-era LLM
can reliably judge. A criterion that requires, e.g., verifying a
security claim against the actual call graph of a large code-base
cannot be reliably scored by gpt-4o-mini. Our checklist is chosen to
stay inside this ceiling.

**Mitigation.** We validate judge verdicts against human raters for a
subset (human-study rubric, 6 PRs) and report Cohen's κ. Criteria
with κ < 0.40 are treated qualitatively.

**Residual risk.** Any criterion that genuinely requires domain
expertise the judges lack will appear saturated or noisy rather than
flat-wrong. We mitigate by excluding criteria the LLM cannot judge
from the rubric design; we cannot guarantee we caught every such
criterion.

---

## 8.4 Conclusion validity

_Can we draw the statistical conclusions we claim?_

### 8.4.1 Multiple-comparisons exposure

**Threat.** We report per-criterion deltas for 25 criteria across 4
modes. With 25 × 3 = 75 pairwise mode comparisons per criterion (and a
Δ column per criterion × mode pair), some differences will appear
significant by chance.

**Mitigation.** The headline claim is made at the *aggregate*
KG-relevant-bucket level (nine pre-registered criteria summed into
one metric), not at the individual-criterion level. Per-criterion
numbers are reported as descriptive support for the aggregate, not as
independent tests. The pattern (positive deltas concentrated on
F3/T1/T3/T2, negative on R1/R2) is *internally coherent* in a way
that chance alone would not produce.

**Residual risk.** We do not report formal p-values or confidence
intervals per criterion, and we do not apply Bonferroni-style
corrections. Readers who want frequentist reassurance for the
per-criterion numbers will have to re-analyse from
`results/checklist_evaluation_llm.json`.

### 8.4.2 Aggregation rule affects magnitudes

**Threat.** We report majority vote with ties → 0 (the strict side).
Reporting ties → 1 (lenient) or unanimous-only would produce
different numbers.

**Mitigation.** We documented the rule explicitly and kept the
single-judge backup (`results/checklist_evaluation_llm.single_
judge_backup.json`) and the per-judge detail
(`results/checklist_evaluation_llm_multi.json`) so readers can
re-aggregate under any rule.

**Residual risk.** Negligible given the full per-judge detail is
published alongside the aggregates.

### 8.4.3 Kappa with imbalanced marginals

**Threat.** Cohen's κ is known to be sensitive to marginal
imbalance (the "prevalence paradox"): high agreement on a mostly-No
criterion can produce low κ even when both raters are
well-calibrated.

**Mitigation.** We report *both* raw agreement and κ so readers can
diagnose the paradox when it appears (typically on saturated
criteria like R1 and Q4). Landis & Koch interpretation is provided
for κ, not as a substitute for domain reading.

**Residual risk.** Criteria with near-uniform marginals will show
low κ as an artefact of prevalence, not of disagreement. We flag
this in the human↔LLM agreement runbook.

---

## 8.5 Reliability and reproducibility

_Can the results be independently recreated?_

### 8.5.1 API non-determinism

**Threat.** LLM APIs are not strictly deterministic even at
temperature 0.0. Two calls with the same prompt can produce different
outputs (same sampling, different internal kv caching, different
backend versions).

**Mitigation.** Temperature is fixed at 0.0 throughout; we include
the call timestamp in every output record so a reader can tell when
scores were produced; we publish the raw per-judge output
(`results/checklist_evaluation_llm_multi.json`), not only the
aggregates, so a reader can re-aggregate without re-querying.

**Residual risk.** Re-running `scripts/evaluate_reviews.py` six
months from now will not reproduce the exact 0/1 verdicts because the
underlying models may have been updated or deprecated. We document the
exact model slugs used (`openai:gpt-4o-mini`, `openai:gpt-4o`,
`gemini:gemini-2.5-flash`) in the metadata of every output file. When
these model slugs are deprecated, exact reproduction will require
running against the archived verdicts.

### 8.5.2 Malformed judge output

**Threat.** 21 of 300 initial Gemini responses returned malformed JSON
(unescaped quotes in evidence strings). A brittle parser would have
silently dropped these or, worse, crashed and produced incomplete
aggregates.

**Mitigation.** We implemented a tolerant fallback parser
(`scripts/evaluate_reviews.py`: `_parse_judge_output`) that recovers
(id, score) pairs from malformed JSON via regex. A dedicated retry
pass (`scripts/retry_failed_judges.py`) re-ran only the affected
(pr × mode × judge) cells; all 21 were recovered. The final dataset
has three valid judges for every one of the 100 (pr × mode) pairs.

**Residual risk.** None, given the final 0 % parse-error rate.

### 8.5.3 Environment and dependency drift

**Threat.** Python and library versions affect parser behaviour and
could in principle change extraction.

**Mitigation.** Dependencies are pinned in `requirements.txt` (Python
3.10+; `openai` as the core dependency); the reproduction recipe is
written out in `README.md` and mirrored in `reproduce.sh`. The thesis
artefact includes a data manifest (`results/DATA_MANIFEST.md`) listing
every output file and the script that produced it.

**Residual risk.** Standard for any Python-based research artefact.
Pinning protects against silent drift; it does not help if upstream
APIs disappear.

### 8.5.4 Training-data contamination

**Threat.** The 25 PRs are real open-source PRs that predate the
evaluation (Kafka ticket numbers from 2023, scikit-learn from 2020,
etc.). They may be present in the training data of `gpt-4o` and
therefore "remembered" rather than "reviewed".

**Mitigation.** The finding is *relative* — we compare baseline,
KG, RAG, and hybrid modes on the *same* PRs with the *same* base
model. Training-data contamination affects all four modes equally
and therefore cancels out in the mode comparisons. Contamination
affects *absolute* ceilings (all modes may score higher than they
would on fresh unseen PRs), not the *deltas* between modes.

**Residual risk.** A portion of the absolute gains could be memorised
content. We flag this and suggest replicating on fresh PRs (e.g.
PRs merged after the gpt-4o training cut-off) as the cleanest fix.

---

## 8.6 Summary table

| Dimension | Threat | Mitigation | Residual |
|-----------|--------|------------|----------|
| Construct | LLM-judge family bias | 3-judge cross-provider panel; report κ | Shared-corpus bias possible |
| Construct | Human/LLM rubric drift (F2*, F3*) | Flag stricter criteria in all tables | Cannot isolate rubric from judgement |
| Construct | "KG-relevant" pre-registration | Labels in code, pre-timestamped | Labels may be disputed |
| Construct | Binary Yes/No simplification | Rubric with explicit thresholds | Saturated criteria contribute noise |
| Internal | Prompt-length differences across modes | Shared base prompt; structured per-criterion effect | Length vs. content not fully separable |
| Internal | Human-study stimulus selection | Frozen pre-pilot; flip-based selection | Mild selection bias |
| Internal | Hybrid not prompt-optimised | Reported as negative result for naive stacking | Optimised hybrid untested |
| External | 25 PRs, 4 repos, 1 language family | Diverse repo choice; aggregate-level claims | No per-repo or per-lang claims |
| External | Single base generator (main run) | 5-PR Claude Sonnet 4.5 replication → KG lift is generator-dependent; claim refined to saturation-conditional | n=5 replication; full 25-PR Claude ablation pending |
| External | Judge-ceiling-limited criteria | Human validation via κ; drop if κ < 0.40 | Some ceiling effects unavoidable |
| Conclusion | Multiple comparisons | Aggregate bucket is the headline | Per-criterion numbers descriptive only |
| Conclusion | Aggregation rule dependence | Full per-judge detail published | Negligible |
| Conclusion | Prevalence-paradox κ | Report raw-agreement and κ together | Saturated criteria hard to interpret |
| Reliability | API non-determinism | Temperature 0.0; raw verdicts published | Future model retirement breaks exact reproduction |
| Reliability | Malformed judge output | Tolerant parser + retry pass | None after recovery |
| Reliability | Dep / env drift | `requirements.txt` pinned; `reproduce.sh` recipe | Standard Python-research risk |
| Reliability | Training-data contamination | Relative mode comparison cancels contamination | Absolute ceilings inflated |
