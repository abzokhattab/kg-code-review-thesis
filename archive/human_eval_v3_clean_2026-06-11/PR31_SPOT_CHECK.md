# PR31 spot check — buggy vs parity vs baseline

PR31 is the most diagnostic single PR in the dataset:

- It was a **Δ=+3 KG-rel** under buggy (driving up the headline)
- It contained the **fabricated "Danilo Silva" code owner**
- It is a `sklearn` `BayesianRidge` predict-fix — small, well-scoped, has a clear bug-class

This document compares the three reviews side-by-side, evaluates each
against the actual PR body, and explains why the headline is fragile.

---

## Score deltas (judge panel)

| Arm                | KG-rel | total | Δ vs baseline (KG-rel / total) |
|---|---:|---:|---:|
| baseline           | 5 / 9  | 9 / 25  | — |
| **buggy joern**    | 8 / 9  | 13 / 25 | **+3 / +4** ← drove the headline |
| **parity joern**   | 6 / 9  | 10 / 25 | **+1 / +1** ← shrunk by 2/3 |

Under parity the joern arm gives back 2 of the 3 KG-rel points it had under buggy. PR31 is one of the seven W → T transitions in the direction-stability table.

## What the PR body actually says

```
When BayesianRidge and ARDRegression are fit with fit_intercept=True
(default), features are centered by subtracting the mean. However,
predict(return_std=True) was using the raw (uncentered) test features
for variance computation, causing the model to report lowest
uncertainty at the origin instead of near the training data.

The fix simply subtracts self.X_offset_ from X before the variance
calculation, matching what happens during training.

Originally the bug report was just for BayesianRidge, but when writing
the non-regression test I noticed that it also applied to ARDRegression.
```

Body length: 743 chars. **No person names. No @handles. No "linear_model team".** The body is rich enough to flag the `fit_intercept` invariant — the most reviewer-relevant issue.

## The three reviews, judged on substance

### Baseline (no KG)

> "Add a condition to check if `fit_intercept` is `True` before centering
> the test features in the `predict` method."

Identifies the strongest concrete concern: `fit_intercept=False` would still hit the centering branch and silently subtract zero. This is a real code-review observation that traces to the body. **Traceability: "Not specified"** — honest abstention.

### Buggy joern

> "Code Owner: **Danilo Silva (danilo-silva-ufsc)**
> Relevant Teams: sklearn.linear_model maintainers"

**Pure fabrication.** Body contains no person names, no maintainers
section. Yet the LLM is rewarded with KG-rel +3 by the panel — likely
because the structured "Code Owner / Relevant Teams" sections look
like the rubric items C2/M1 ("identifies dependents / structural
context"). This is the mechanism the thesis discussion needs to name:
*shape-of-structural-claims rewarded over correctness*.

The buggy review also focuses on speculative `X_offset_` initialization
risks rather than the concrete `fit_intercept=False` case the body
explicitly raises.

### Parity joern

> "Code owners: sklearn/linear_model team
> Related teams: sklearn/ensemble, sklearn/tests"

The fabrication **persists in mutated form**. The model retreated from
inventing a person to inventing a team — but the "linear_model team"
attribution is still not in the body and there is no `CODEOWNERS` or
`MAINTAINERS` data in the prompt. It's a softer fabrication but a
fabrication nonetheless.

The parity review **also misses** the `fit_intercept=False` case the
body literally states. KG-rel +1 reflects judges still rewarding the
structural framing despite zero new substance vs baseline.

## What this means for the headline

PR31 is one of the largest individual contributors to the parity d_z=+0.30:

- Without PR31, parity delta drops from 12/35 wins to 11/35.
- PR31's parity Δ=+1 reflects judges rewarding the model for *attempting*
  attribution, regardless of correctness.

A more discerning judge panel (or human raters) should rate the baseline
review as **better**: it's the only one that names the `fit_intercept`
edge case. The pilot self-rating (`PILOT_SELF_RATING.md`) reached the
same conclusion 5/6 directional agreement vs LLM judges.

## Implications for the thesis

1. **PR31 is the named example for the discussion chapter.** Frame as:
   "The parity correction reduced but did not eliminate fabricated
   attribution. Under both buggy and parity prompts, the LLM invents
   ownership metadata that the panel rewards as evidence of
   structural awareness."

2. **The Δ=+1 under parity is not a substantive improvement** —
   it's the panel rewarding fabrication shape. This is a *failure
   mode of LLM-as-judge that human studies are designed to catch*.

3. **The fit_intercept gap** (a real bug the baseline catches and
   neither KG arm catches) is a concrete example of the body
   carrying review-relevant signal that the KG does not duplicate.
   This is the *opposite* of what you'd hope from a structural-context
   tool: the KG should help the LLM notice the cross-cutting concern
   that fit_intercept governs centering throughout the predict path.
   In practice it doesn't.

## What changed under parity

| Aspect | Buggy → Parity |
|---|---|
| KG-rel score | 8 → 6 (−2) |
| Total score  | 13 → 10 (−3) |
| Code owner   | "Danilo Silva" (person) → "sklearn/linear_model team" (still fabricated) |
| Concrete code concern | speculative X_offset_ init | speculative edge cases |
| `fit_intercept` insight | missed | missed |

**Parity made the review slightly less specific (less wrong) but did
not unlock the actual bug-class the body advertised.**
