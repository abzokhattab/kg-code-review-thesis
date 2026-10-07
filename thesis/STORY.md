# Thesis Summary

## Research Problem

An LLM reviewing a pull request sees only the diff. If a change breaks
something in another file, the reviewer can't know — it's not in the diff.

## Research Approach

Give the LLM a knowledge graph: a map of what depends on what in the
repository. Now it can see that renaming `process_payment()` will break
`checkout.py` three directories away.

## System Overview

A pipeline that takes a PR and produces a review. Four conditions:

```
baseline  =  diff only
KG        =  diff + structural context (builder varies by study)
RAG       =  diff + similar code via embeddings
hybrid    =  diff + both
```

The generator and frozen evidence packs are held fixed within each study.
The arms differ in the rendered context and the instruction that names it.

## Knowledge-Graph Construction

Experiments~1 and~2 use a Joern code property graph that extracts call,
import, and inheritance edges from the repository at the pull request's
head commit. The practitioner study uses the same knowledge-graph block with
dependent edges resolved from import statements.
Both builders feed the same evidence-pack schema and renderer.

## Three Experiments

### Experiment 1: Pull-Request Evaluation

35 PRs, 5 repos, scored by a five-judge panel on a 25-criterion rubric.

- KG helps on the 9 structural criteria: **+0.69/9, p=0.003, d_z=+0.56**
- KG gains +0.71/25 overall (p=0.017 uncorrected; p_corr=0.066 after Bonferroni)
- RAG helps overall: +1.03/25, p=0.002
- **96%** of KG's advantage falls in the 9 predicted criteria (p=0.003)

**Summary:** KG gains concentrate on structurally relevant criteria, whereas
RAG produces a broader gain. The two mechanisms are complementary.

### Experiment 2: Controlled Defect Injection

28 defects planted so the consequence is in a DIFFERENT file.
12 control defects where the consequence is LOCAL (sanity check).

```
baseline    0/28   ←  can't see cross-file consequences
RAG         5/28   ←  similarity rarely finds callers
KG         18/28   ←  the graph shows the broken file
hybrid     21/28   ←  complementary, not fused
inheritance 26/28  ←  add inheritance edges → near ceiling
idealised   26/28  ←  ceiling (perfect static analysis)
```

All arms detect local controls at or near ceiling, so the advantage appears
specifically when cross-file structural information is required.

**Inheritance-edge contribution (18→26 detections):**
eight misses are recovered by adding omitted relations; two persist under the
idealised resolver.

### Experiment 3: Practitioner Evaluation

27 practitioners, blinded, compare KG vs baseline reviews on 6 PRs.

- F3 (naming affected components): **0.710, p=0.0005** → humans see it
- Overall usefulness: 0.512 → no preference
- R1 (code clarity): **0.414, Holm p=0.028** → baseline preferred after correction

Same pattern as Exp1: the graph changes what the review grounds itself
in, and that's all it changes.

## Principal Findings

Structural context gives an LLM a capability it demonstrably lacks:
seeing consequences outside the diff. That capability is real (0→18/28
under oracle), localised (96% in predicted criteria), perceived by
humans (0.710 on F3), and limited by the analyser, not the model
(18→26 with inheritance edges).

It does not make reviews broadly better. It makes them better at one
specific thing, and that thing matters when it matters.

## Key Results

| What | Number |
|------|--------|
| Pull requests in Experiment 1 | 35 across 5 repositories |
| Structural injections | 28 (+ 12 local controls) |
| Human raters | 27 |
| KG subscale effect | +0.69/9, p=0.003, d_z=+0.56 |
| KG total effect | +0.71/25, p=0.017 (uncorrected) |
| RAG total effect | +1.03/25, p=0.002 |
| Localisation | 96%, p=0.003 |
| Detection: baseline→KG | 0/28 → 18/28 |
| Detection: +inheritance | 18/28 → 26/28 (p=0.008) |
| Human F3 preference | 0.710, p=0.0005 |
| Human overall | 0.512 (indifferent) |
| Human R1 (clarity) | 0.414, Holm p=0.028 (baseline) |
| Judges | Final five-judge multi-provider panel |
