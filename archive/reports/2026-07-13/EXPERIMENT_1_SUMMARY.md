# Experiment 1 — Does repository context improve LLM code review?

**Master's thesis, Abdelrahman Khattab · Hasso Plattner Institute · status 2026-07-13**

## Question

Does augmenting an LLM code reviewer with a repository **knowledge graph**
(KG) and/or **retrieval-augmented generation** (RAG) produce better PR
review comments than the prevailing diff-only baseline?

## Design

| | |
|---|---|
| Dataset | **40 real merged pull requests** from 5 open-source repositories (Apache Kafka, Godot, Grafana, scikit-learn, Jenkins) |
| Modes compared | baseline (diff-only) · **kg** · **rag** · **hybrid** (kg+rag) |
| Generation | gpt-4o at T = 0.0 — identical prompts except the injected context |
| Scoring | 3-judge LLM panel (gpt-4o-mini, gpt-4o, gemini-2.5-flash), majority vote per criterion |
| Rubric | 25 criteria grounded in Bacchelli & Bird (ICSE'13), Bosu et al. (MSR'15), Sadowski et al. (ICSE-SEIP'18), ISO/IEC 25010; a pre-defined **9-criterion KG-relevant subset** (impact/dependency criteria the KG is designed to help with) |
| Statistics | percentile bootstrap (B = 10 000) for CIs; paired sign-flip permutation tests (B = 20 000), seed 2026 |

## Results

Per-mode means (95% bootstrap CI), n = 40:

| Mode | Total /25 | KG-relevant /9 |
|---|---|---|
| baseline | 9.20 [8.70, 9.70] | 4.97 [4.67, 5.28] |
| kg | 9.82 [9.28, 10.43] | **5.58 [5.22, 5.95]** |
| rag | **10.07 [9.57, 10.60]** | 5.40 [5.00, 5.78] |
| hybrid | 9.93 [9.47, 10.38] | 5.50 [5.22, 5.78] |

Paired differences vs baseline (same PR):

| Mode | Total Δ | p | d_z | KG-relevant Δ | p | d_z |
|---|---|---|---|---|---|---|
| kg | +0.62 [+0.05, +1.20] | 0.054 | 0.33 | **+0.60 [+0.23, +0.97]** | **0.007** | **0.47** |
| rag | **+0.88 [+0.30, +1.45]** | **0.007** | **0.47** | +0.42 [+0.05, +0.82] | 0.057 | 0.33 |
| hybrid | **+0.72 [+0.10, +1.35]** | **0.037** | **0.36** | **+0.53 [+0.17, +0.90]** | **0.008** | **0.46** |

Inter-judge agreement is substantial: Cohen's κ = 0.59–0.72 across the
three judge pairs.

## Reading

**Each context type improves the metric it targets, and the hybrid
improves both.** KG's gain concentrates on the KG-relevant criteria
(dependency/impact grounding, +0.60 of 9, p = .007, medium effect); RAG's
gain is on total coverage (+0.88 of 25, p = .007). Neither dominates the
other — the defensible claim is **complementarity**, not "graphs beat
retrieval".

## Known limitations → what Experiment 2 addresses

1. The result is **correlational**: real PRs vary in a hundred ways, so
   rubric gains do not prove the KG causes better *defect-relevant*
   reviews.
2. Scores are **LLM-judged** against a rubric, not against ground truth.

Experiment 2 (separate document) closes both gaps with a controlled
defect-injection design: known planted defects, objective ground truth,
and judge validation against a deterministic oracle. A small human study
(link in the accompanying message) then closes the remaining
machines-grading-machines loop.

---

**Correction (2026-08-12).** The generation row above originally read
"T = 0.4, seed = 42". Both were wrong: the v2 pipeline
(`dataset_v2/scripts/regenerate_reviews_v2.py`) generates at its
`--temperature` default of **0.0**, and no generation seed is sent to the
model on any code path. All reported results are unaffected — every mode in
a run shares the same setting — and every number in this document was
re-verified against the raw judge votes on 2026-08-12
(`paper/2026-08-12/INTEGRITY_AUDIT.md`).
