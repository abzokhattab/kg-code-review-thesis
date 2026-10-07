# Discussion (ready-to-paste draft)

_This is a thesis-chapter Discussion section written against the multi-judge
LLM evaluation data in `results/checklist_evaluation_llm.json` and the
per-criterion breakdown in `results/CHECKLIST_EVALUATION_REPORT.md`. It
deliberately avoids restating numbers that already appear in the Results
chapter and instead focuses on interpretation, prior-work positioning, and
implications. Numbers kept here are the ones the interpretation hinges on._

---

## 7.1 The Knowledge Graph improves exactly the criteria it is designed to help

The headline finding of the LLM evaluation is not that the Knowledge Graph
(KG) makes reviews "better on average" — it does not, and the overall score
improvement of **+0.7 percentage points (32.3 % → 33.0 %)** is within
measurement noise. What the data show instead is a structured effect: the
KG improves exactly the criteria whose satisfaction requires access to
information *outside* the local diff, and leaves the other criteria
essentially untouched. On the nine criteria we pre-registered as
"KG-relevant" — those that explicitly require reasoning about tests,
dependents, APIs, or architectural integration — the KG mode reaches
**53.3 %** versus baseline's **46.2 %**, a **1.15× gain (+7.1 pp)** under a
strict three-judge majority-vote aggregation.

Drilling into individual criteria sharpens the picture further. The four
largest positive deltas are all in the integration-and-testing family:
F3 (integration with existing components) improves by **+28 pp**, T1 (need
for tests) by **+20 pp**, T3 (references specific test files) by **+20 pp**,
and T2 (edge-case tests) by **+12 pp**. These are exactly the criteria
where the KG-augmented prompt exposes content — call-graphs, test-file
paths, existing invocations — that is invisible to a diff-local reviewer.
The symmetry between *what we designed the KG to surface* and *where the
evaluation gains appear* is the strongest construct-validity signal in
the thesis.

Two criteria in the KG-relevant bucket move in the *opposite* direction:
M1 (architectural fit, **−4 pp**) and M3 (API/interface documentation,
**−20 pp**). Both require reasoning about cross-cutting design rather than
about local callers or test files, and the KG we build does not attempt to
capture design rationale. M3 in particular appears to suffer because the
KG-augmented reviews shift attention toward mechanical integration checks
and rarely revisit the PR's interface surface. This points to a natural
extension in future work: enriching the KG with documentation anchors
(docstrings, changelog, ADR entries) rather than only code-structural
facts.

## 7.2 Augmentation is not free: the readability trade-off

A finding that did not appear in the single-judge pilot, and only becomes
visible once the judge panel is tightened, is a **systematic readability
trade-off** produced by KG augmentation. On three non-KG-relevant criteria
the KG mode scores meaningfully *worse* than baseline: R1 (code clarity /
naming) drops from **36 %** to **8 %** (**−28 pp**), R2 (suggesting
simplification) drops by **−16 pp**, and F1 (restating the PR's stated
problem) drops by **−12 pp**. In absolute terms these effects are larger
than many of the KG's positive gains.

The interpretation is interpretable rather than alarming. When the prompt
supplies structured context about tests, dependents, and architectural
hotspots, the model spends its finite output budget on technical-correctness
content (what the tests cover, which callers break) and writes *less*
surface-level commentary about naming and restatement. Put differently, the
KG does not "suppress" readability comments; it redirects attention. The
practical consequence is that a deployed KG-augmented reviewer would be
unwise to operate *in isolation*: the most obvious productisation is a
two-pass system that runs the KG-augmented model for correctness and a
smaller, cheaper baseline pass for style. This is, in retrospect, an
argument against monolithic "one-prompt-to-rule-them-all" design of
LLM-based code review, and the thesis's data are the first place we have
seen the trade-off quantified on real PRs.

## 7.3 Hybrid (KG + RAG) does not outperform KG alone

One of the most surprising results is negative. The Hybrid mode, which
combines KG-derived structural context with RAG-retrieved textual context
in a single prompt, matches baseline on overall score
(**32.2 %** vs. **32.3 %**) and is effectively *tied with baseline* on the
KG-relevant bucket (**46.2 %** vs. **46.2 %**). The expected additive gain
over either augmentation alone does not materialise.

Two mechanisms likely account for this. First, **prompt-length
interference**: the combined prompt pushes the structured KG signals
further from the diff, and recency/primacy effects in long contexts
(Liu et al., 2024, "Lost in the Middle") plausibly mute the KG content
that appears earliest. Second, **retrieval redundancy**: in many of our
PRs, the snippets surfaced by RAG overlap substantially with the entities
already named by the KG. Whenever both channels surface the same call
site, the model spends budget on cross-referencing rather than generating
new review content.

The negative result is useful. It rules out the "more context is always
better" heuristic and argues for either (a) selection between KG and RAG
at inference time (e.g. a classifier that routes test-heavy PRs to KG and
documentation-heavy PRs to RAG), or (b) a merged retrieval surface that
deduplicates before prompting. Both are concrete directions for future
work.

## 7.4 Positioning against prior work

Our evaluation framework is most closely related to DeepCRCEval (Lu et al.,
2024), which introduced the 25-criterion checklist idea in the code-review
context, and CRScore (Rahman et al., 2024), which operationalised
reference-free scoring. Both rely on **single-judge** LLM evaluation. Our
contribution relative to these works is twofold: first, we apply the
framework *across an ablation* (baseline / KG / RAG / Hybrid) on a curated
set of 25 real-world PRs rather than a single monolithic comparison;
second, we harden the scoring itself by moving from a single judge to a
**three-judge cross-provider panel** with majority-vote aggregation and
Cohen's κ reporting, following MT-Bench / Chatbot Arena practice
(Zheng et al., 2023; Chiang et al., 2024).

The hardening matters. Under the single-judge protocol used in the
published checklist-style evaluations, our own KG vs. baseline delta on
KG-relevant criteria was **+13.8 pp**; under the three-judge majority-vote
protocol it is **+7.1 pp**. The direction and per-criterion pattern are
stable; the magnitude halves. A single-judge study of this system would
therefore over-state the benefit of the KG by roughly 2×. We report the
conservative number throughout the thesis and treat the single-judge
result as a sensitivity comparison only. We believe this is the first
code-review-quality study to publish a multi-judge sensitivity analysis,
and we recommend it as standard practice for LLM-as-a-judge evaluations
whose conclusions depend on single-digit percentage-point differences.

With respect to generation-side prior work, Tufano et al. (2021, 2022) and
Li et al. (CodeReviewer, 2022) treat code review as a sequence-to-sequence
translation problem without structured context augmentation. Our results
suggest that the bottleneck is not model capacity but access to
out-of-diff information: the same underlying model reaches meaningfully
higher coverage on integration and testing criteria merely by being shown
a KG view of the repository. This reframes "better code-review AI" as a
retrieval-augmentation problem more than a model-training problem, which
has implications for how future research teams allocate compute.

## 7.5 Implications and limitations

The thesis supports three concrete implications for practitioners and
researchers building LLM-based code reviewers.

**(1) Measure per-criterion, not aggregate.** Aggregate scores hide the
KG's main benefit (integration and testing coverage) behind its main cost
(readability attention). A system evaluated only on a single "overall
quality" axis would appear flat; the structured effect is only visible in
the per-criterion breakdown. Future evaluations of retrieval-augmented
review systems should report per-category deltas with the same
granularity used here.

**(2) Judge-side robustness is a first-class methodological concern.** Our
data show that a single judge can over-state an effect by about 2× in
magnitude without changing its direction. This is not a failure of any
particular model; it is a property of the protocol. A minimum defensible
protocol for LLM-as-a-judge in this domain is: at least two providers,
majority-vote aggregation, and reported Cohen's κ. Kappa values of
0.54–0.70 observed here are consistent with "moderate to substantial"
agreement (Landis & Koch, 1977) and provide a baseline for future
comparisons.

**(3) Retrieval augmentation is not monotonic.** Adding more context
channels (KG + RAG) did not improve the system; in aggregate it erased
the KG's advantage. Practitioners should be cautious about stacking
augmentation techniques and should, at minimum, run A/B comparisons
before combining them.

The principal limitations are the following. The evaluation uses 25 PRs
drawn from four repositories across three languages, which is sufficient
for directional conclusions about augmentation strategies but not for
repository- or language-specific claims. The LLM-as-a-judge setup, even
with a three-model panel, cannot fully rule out a shared-family bias in
favour of "textbook-style" reviews. The human-study stimulus set (six PRs)
was chosen using the single-judge pilot scores for discriminative power;
re-deriving the stimulus set from the multi-judge data would perturb the
ordering slightly but would invalidate the in-flight pilot, so we retain
the original set and document this as a minor threat to internal validity
for the human study only. Finally, our KG construction is code-centric
(call-graph, test membership, dependency edges); a richer KG including
documentation and review-history anchors would likely lift the M1/M3
deltas and is a natural extension for future work.

---

## References (append to the thesis bibliography as needed)

- Chiang, W.-L., et al. (2024). *Chatbot Arena: An Open Platform for
  Evaluating LLMs by Human Preference.*
- Landis, J. R., & Koch, G. G. (1977). *The Measurement of Observer
  Agreement for Categorical Data.* Biometrics, 33(1), 159–174.
- Li, L., et al. (2022). *CodeReviewer: Pre-Training for Automating Code
  Review Activities.* FSE 2022.
- Liu, N. F., et al. (2024). *Lost in the Middle: How Language Models Use
  Long Contexts.* TACL 2024.
- Lu, J., et al. (2024). *DeepCRCEval: Revisiting the Evaluation of Code
  Review Comments Generated by Deep Learning.*
- Rahman, M. M., et al. (2024). *CRScore: Grounding Automated Evaluation
  of Code Review Comments in Code Claims and Smells.*
- Tufano, R., et al. (2021). *Towards Automating Code Review Activities.*
  ICSE 2021.
- Tufano, R., et al. (2022). *Using Pre-Trained Models to Boost Code
  Review Automation.* ICSE 2022.
- Zheng, L., et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and
  Chatbot Arena.* NeurIPS 2023.
