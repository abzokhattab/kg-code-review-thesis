# Pre-registration — test-oracle band

**Written:** 2026-09-06, after the manifest was built (no model calls, seed
2026, deterministic) and **before any review or verdict exists.** Amendments
go in a dated addendum only.

## 1. Question

Does naming a change's related tests help the reviewer state that a **specific
test breaks**?

Experiment 2 established the dependency signal causally: 0/28 cross-file
defects found without the graph, 15/28 with it, 26/28 with ground-truth
dependents. Its feature ablation then showed both kinds of dependency evidence
contribute independently (`results/EXP2_FEATURE_ABLATION.md`: lexical file list
alone 9/28, Joern call edges alone 12/28, both significant against baseline).

The **test** section has no comparable evidence, and not for want of trying:

| Attempt | Result |
|---|---|
| 2026-03-05 ablation, single judge | "tests most valuable, −10.6%" — internally incoherent, removing both hurt less than removing tests |
| same reviews, canonical three judges | +0.25 /9, p = 0.40, incoherence persists |
| Joern progressive ablation | +1.63 /9 against a baseline from a different pipeline; +0.43, p = 0.24 against its own control |
| v2 scramble (pre-registered) | randomising the test filenames: −0.08 /9, p = 0.88 |
| v2 deletion | removing the section entirely: −0.27 /9, p = 0.33 |

All five ran on the 25-criterion coverage rubric, which moves 0.6 points
between baseline and `kg` against a measured single-draw generation noise of
0.88 points (`results/GENERATION_VARIANCE.md`). The instrument cannot resolve
the question, because the model discusses tests whether or not any are named.
This band replaces coverage with a ground-truthed binary outcome.

## 2. Construction

A symbol whose importers include at least one test file is renamed (operator
S1 from Experiment 2). The rename provably breaks every importer, so the test
files among those importers **will fail** — a static oracle requiring no test
execution.

Built: **28 injections, Grafana only**, all with at least one test dependent
and at least one non-test dependent, median 1 test dependent. Seed 2026.

## 3. Arms

| Arm | Context supplied |
|---|---|
| `baseline` | diff only |
| `kg` | changed file + dependent files **with the test files removed** |
| `kg_plus_tests` | the same, plus a labelled Related Tests section naming the true test dependents |

Removing the tests from `kg`'s dependency list is what makes this a
single-factor contrast: `kg_plus_tests` adds exactly one thing. Every target
retains at least one non-test dependent, so `kg` is never an empty-context arm
and the contrast is "tests added", not "any context added".

Generator `openai:gpt-4o` at temperature 0, one draw per cell — identical to
Experiments 1 and 2.

## 4. Endpoint

**Primary.** Detection rate: the review names at least one of the injection's
true test dependents as breaking or needing update. Majority of the three
canonical judges (`gpt-4o-mini`, `gpt-4o`, `gemini-2.5-flash`), ties to 0 —
the Experiment 2 rule.

**Secondary, and pre-declared as the fairness check.** Rate at which the review
merely says tests are affected *without naming one*. If `kg_plus_tests` wins
only on naming while generic test talk is flat, the effect is recall of a
supplied string rather than reasoning, and will be reported as such.

No injection is added or dropped. All three arms run on all 28.

## 5. Predictions, fixed now

**P1 — the test section works.** `kg_plus_tests` > `kg` on naming the breaking
test, with `kg` near `baseline`. Would give the test signal its first causal
support and put it alongside dependency in RQ2.1.

**P2 — no effect.** `kg_plus_tests` ≈ `kg`. Since the arm is *handed* the
answer, a null here is decisive: the test list does not help even when the
oracle is about tests and the correct filename sits in the prompt. Combined
with the five rubric nulls, the test section would be established as inert and
reportable as a negative result.

**P3 — `kg` already suffices.** Both arms well above `baseline`. The reviewer
infers test breakage from the non-test dependency list alone, making the test
section redundant rather than inert.

## 6. Statistics

Paired over injections. Exact McNemar for `kg_plus_tests` against `kg` and each
against `baseline`; Wilson 95% intervals; bootstrap B = 10 000 and permutation
B = 20 000 on rate differences, seed 2026. Three contrasts, Holm-corrected,
α = 0.05. One analysis after all 84 reviews and 252 verdicts are complete.

**Power.** With 28 paired binary observations, exact McNemar detects a shift of
roughly 0.3 in rate at about 80%. A small effect will not be resolved and the
report will say so rather than treating a null as absence.

## 7. Limitation, to be carried into every claim

**Single repository, single language.** Grafana/TypeScript only, because the
Experiment 2 scopes for sklearn and Kafka contain no test directories — 0
candidates against Grafana's 174. Any finding here is one repository's, and
cannot be reported with the three-repo generality of Experiment 2.

## 8. Outputs

```
experiments/2026-09-06_test_oracle/out/manifest.json         (built, 28)
experiments/2026-09-06_test_oracle/out/reviews/<id>/<arm>.md (84)
experiments/2026-09-06_test_oracle/out/judgments/<id>/       (252)
results/TEST_ORACLE.{md,json}
```

Estimated cost ~$9. Idempotent at both stages. Nothing outside this
experiment's folder and `results/TEST_ORACLE.*` is written; Experiment 2's
artefacts are read-only here.
