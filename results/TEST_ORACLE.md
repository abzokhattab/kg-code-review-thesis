# Test-oracle band — does naming the tests help?

Pre-registered in `experiments/2026-09-06_test_oracle/docs/PRE_REGISTRATION_test_oracle.md` before any review existed.

n = 28 injections. A symbol whose importers include test files is renamed, so those tests provably fail. The reviewer is scored on whether it names one of them.

**Grafana/TypeScript only** — the Experiment 2 scopes for sklearn and Kafka contain no test directories, so this result is one repository's and cannot be reported with the three-repo generality of Experiment 2.

## Primary — names a genuinely breaking test file

This is the actionable outcome: a review that says *which* test breaks.

| Arm | Context | Rate | 95% Wilson |
|---|---|---:|---|
| `baseline` | diff only | 0/28 (0%) | [0.00, 0.12] |
| `kg` | dependencies, test files removed | 0/28 (0%) | [0.00, 0.12] |
| `kg_plus_tests_lexical` | + tests from the deployed filename finder | 24/28 (86%) | [0.69, 0.94] |
| `kg_plus_tests` | + tests from ground truth (ceiling) | 27/28 (96%) | [0.82, 0.99] |

| Contrast | Δ | 95% CI | discordant | McNemar | p (Holm) |
|---|---:|---|---:|---:|---:|
| kg - baseline | +0% | [+0.00, +0.00] | 0/0 | 1.0000 | 1.0000 |
| kg_plus_tests_lexical - kg | +86% | [+0.71, +0.96] | 24/0 | 0.0000 | 0.0000 ** |
| kg_plus_tests - kg | +96% | [+0.89, +1.00] | 27/0 | 0.0000 | 0.0000 ** |
| kg_plus_tests - kg_plus_tests_lexical | +11% | [-0.04, +0.25] | 4/1 | 0.3750 | 0.7500 |

## Secondary — talks about tests without naming one

Pre-declared fairness check. This is what the coverage rubric's T3 criterion actually rewards.

| Arm | Context | Rate | 95% Wilson |
|---|---|---:|---|
| `baseline` | diff only | 22/28 (79%) | [0.60, 0.90] |
| `kg` | dependencies, test files removed | 28/28 (100%) | [0.88, 1.00] |
| `kg_plus_tests_lexical` | + tests from the deployed filename finder | 23/28 (82%) | [0.64, 0.92] |
| `kg_plus_tests` | + tests from ground truth (ceiling) | 25/28 (89%) | [0.73, 0.96] |

| Contrast | Δ | 95% CI | discordant | McNemar | p (Holm) |
|---|---:|---|---:|---:|---:|
| kg - baseline | +21% | [+0.07, +0.36] | 6/0 | 0.0312 | 0.1250 |
| kg_plus_tests_lexical - kg | -18% | [-0.32, -0.04] | 0/5 | 0.0625 | 0.1875 |
| kg_plus_tests - kg | -11% | [-0.21, +0.00] | 0/3 | 0.2500 | 0.5000 |
| kg_plus_tests - kg_plus_tests_lexical | +7% | [-0.07, +0.21] | 3/1 | 0.6250 | 0.6250 |

## Why five rubric attempts found nothing

Generic test talk is near ceiling in every arm, including the diff-only baseline. The model says tests are affected whether or not any are named, and the rubric criterion that would move — T3, *references specific test files or suggests which tests* — is satisfied by exactly that boilerplate. So the coverage instrument has no headroom on the test section, which is why deletion, scrambling and the three-judge re-analysis all returned null. The signal is real; the ruler could not see it.

## Quality of the deployed finder on these targets

The filename-convention finder returned a genuinely broken test for **25/28** targets and nothing at all for 2. TypeScript's `Foo.test.ts` beside `Foo.ts` convention is unusually favourable, so this recall should not be assumed for other languages.

