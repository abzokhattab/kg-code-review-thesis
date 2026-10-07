> # ⛔ SUPERSEDED — DO NOT CITE
>
> **Superseded 2026-09-06 by `results/EXP2_FEATURE_ABLATION.md` and
> `results/TEST_ORACLE.md`.** Its headline claim — "test coverage context is
> the most valuable KG feature, a 10.6% relative drop when removed" — is not
> supported and should not appear anywhere.
>
> Three reasons:
>
> 1. **It refutes itself.** Removing tests *and* dependencies together scored a
>    smaller drop (6.6%) than removing tests alone (10.6%). Removing more
>    information cannot improve a review, so the ordering is impossible if the
>    effects are real.
> 2. **A single weak judge and no statistics.** Scored by `gpt-4o-mini` alone
>    with no p-values, confidence intervals or significance test of any kind.
>    The same 51 reviews were re-judged with the canonical three-judge panel on
>    2026-05-31 (`results/ablation_3judge/`); on that panel removing tests costs
>    +0.25 /9 at p = 0.40, removing dependencies +0.11 /9 at p = 0.89, and the
>    impossible ordering persists. So it was never a judge artefact — it is
>    noise at n = 16–19.
> 3. **Wrong instrument.** The 25-criterion coverage rubric moves 0.6 points
>    between baseline and the graph arm, against a measured single-draw
>    generation noise of 0.88 points (`results/GENERATION_VARIANCE.md`). It
>    cannot resolve sub-features. In particular its T3 criterion is satisfied by
>    generic test talk, which runs at 79–100% in every arm including diff-only
>    (`results/TEST_ORACLE.md`), so the test section has no headroom to move.
>
> **What replaced it.** Both questions were re-run on ground-truthed binary
> oracles, pre-registered, where the dynamic range is 0/28 to 27/28:
>
> * dependency signal — `results/EXP2_FEATURE_ABLATION.md`
> * test signal — `results/TEST_ORACLE.md`
>
> Superseded material is kept for provenance only.

# Ablation Study Results — RQ2.1: KG Feature Importance

*Generated 2026-03-05 | 25-criterion LLM-as-judge (GPT-4o-mini) | 51 ablated reviews across 25 PRs*

---

## Executive Summary

> **Test coverage context is the most valuable KG feature**, causing a **10.6% relative drop** in review quality when removed.
> Dependency/caller context contributes a **5.2% relative drop**.
> Both features primarily improve edge-case identification (F2), test-related feedback (T2), and pattern consistency (C2).

---

## 1. What is an Ablation Study?

An ablation study answers the question: **"Which parts of our system actually matter?"**

In our main evaluation (RQ1), the KG mode feeds the LLM three types of context alongside the diff: **test coverage data**, **dependency/caller information**, and the **diff itself**. The KG mode scored highest overall — but we don't know *which* of those context features are actually driving the improvement. Maybe tests alone do all the work, or maybe dependencies are what matter.

To find out, we **systematically remove one feature at a time**, regenerate the review from scratch, and re-evaluate it. If the score drops significantly, that feature was important. If it barely changes, the feature wasn't contributing much.

### Process (step by step)

1. **Start with the full KG evidence packs** — the same 25 evidence JSONs used in the main evaluation, each containing the diff, nearest tests, and dependent files.

2. **Create ablated copies** — for each PR, we make modified evidence packs with specific features zeroed out (e.g., `nearest_tests: []`). We produced 51 ablated packs across 3 configurations.

3. **Regenerate KG reviews** — each ablated evidence pack is fed to GPT-4o with the same KG system prompt. The LLM generates a fresh review without access to the removed feature. This produced 51 new review documents.

4. **Re-evaluate with the LLM judge** — each ablated review is scored by GPT-4o-mini against the same 25-criterion rubric. This gives us a comparable score for every ablated review.

5. **Compare against the baseline** — we load the existing full_kg scores from the main evaluation and compute the score drop for each ablation, both overall and per-criterion.

6. **Analyse** — which features cause the biggest drops? Which specific criteria are affected? Do the features overlap or complement each other?

---

## 2. Experiment Design

Starting from the full KG evidence (tests, dependencies, diff), we create three ablated variants and regenerate KG-mode reviews from scratch. Each review is re-evaluated with the same 25-criterion rubric used in the main study.

| Config | What was removed | PRs evaluated | Rationale |
|--------|-----------------|:---:|-----------|
| **full_kg** *(baseline)* | Nothing | 25 | Existing KG reviews from main evaluation |
| **kg_no_tests** | `nearest_tests` | 16 | Only PRs that had test data to remove |
| **kg_no_deps** | `dependent_files` | 19 | Only PRs that had dependency data to remove |
| **kg_minimal** | Both tests + deps | 16 | Combined removal; isolates the diff-only KG signal |

> PRs without the relevant feature (e.g., no tests in the evidence) are excluded from that ablation since removal would have no effect.

---

## 3. Feature Importance Ranking

| Rank | Feature removed | Baseline | Ablated | Drop | Relative drop |
|:----:|-----------------|:--------:|:-------:|:----:|:-------------:|
| 1 | Test coverage (`kg_no_tests`) | 37.8% | 33.8% | **-4.0 pp** | **10.6%** |
| 2 | Dependencies (`kg_no_deps`) | 36.4% | 34.5% | **-1.9 pp** | **5.2%** |
| 3 | Both (`kg_minimal`) | 37.8% | 35.3% | **-2.5 pp** | **6.6%** |

**Reading the table**: "Baseline" is the average full_kg score for the same PR subset. "Drop" is in percentage points. "Relative drop" normalises by the baseline.

> The combined removal (`kg_minimal`) shows a **6.6%** drop — less than `kg_no_tests` alone (10.6%). This reflects LLM generation variance: when both features are removed, the model sometimes compensates by producing different but equally-scored content. With 16 PRs per condition, individual noise of +/-4 pp is expected.

---

## 4. Per-Criterion Impact

Average score delta per criterion (**full_kg minus ablated**). Positive values mean the feature *helped* that criterion.

### Criteria with meaningful impact (|delta| >= 0.1)

| Criterion | Description | no_tests | no_deps | minimal |
|:---------:|-------------|:--------:|:-------:|:-------:|
| **F2** | Edge cases / boundary conditions | **+0.50** | +0.26 | +0.31 |
| **T2** | Testing edge cases & error paths | **+0.44** | +0.11 | +0.19 |
| **S3** | Error handling & failure recovery | +0.19 | — | +0.19 |
| **Q5** | Explains reasoning behind suggestions | +0.19 | — | +0.13 |
| **F3** | Integration with existing components | -0.13 | **+0.16** | — |
| **M1** | Fits existing architecture/design | — | **+0.16** | — |
| **C2** | Consistent with existing patterns | +0.13 | +0.11 | +0.13 |
| **P1** | Performance issues | -0.13 | — | -0.13 |
| **Q3** | Distinguishes blocking vs. minor | -0.19 | -0.26 | -0.19 |

*"—" = |delta| < 0.05 (no meaningful change). Full table in appendix below.*

### Interpretation

- **Test context (no_tests)** most impacts **F2** and **T2** — test data surfaces edge cases and directly informs test-related feedback.
- **Dependency context (no_deps)** most impacts **F3** and **M1** — caller/importer data helps assess integration risks and architectural fit.
- **Q3 improves when features are removed** — with less context, reviews are more concise and naturally distinguish priorities better.
- **P1 improves when features are removed** — without structural context, the LLM falls back to scanning the diff for performance issues more carefully.

---

## 5. Top 5 Affected Criteria per Ablation

### Removing test context (`kg_no_tests`)

| Criterion | Category | Delta | What this means |
|:---------:|----------|:-----:|-----------------|
| F2 | Functionality | +0.50 | Half of reviews lose edge-case coverage |
| T2 | Tests | +0.44 | Test scenario suggestions drop sharply |
| S3 | Security | +0.19 | Error-handling insights reduced |
| Q5 | Quality | +0.19 | Less "why" reasoning in suggestions |
| C2 | Consistency | +0.13 | Pattern-matching comments decrease |

### Removing dependency context (`kg_no_deps`)

| Criterion | Category | Delta | What this means |
|:---------:|----------|:-----:|-----------------|
| F2 | Functionality | +0.26 | Fewer edge cases caught without caller info |
| F3 | Functionality | +0.16 | Integration checking weakens |
| M1 | Maintainability | +0.16 | Architecture assessment weakens |
| T2 | Tests | +0.11 | Slight reduction in test suggestions |
| C2 | Consistency | +0.11 | Slight reduction in pattern checks |

---

## 6. Key Findings

1. **Test coverage is the most valuable KG feature.** Removing it causes a 10.6% relative drop, concentrated on edge-case identification (F2: +0.50) and test feedback (T2: +0.44). Test context doesn't just help with T-criteria — it surfaces edge cases that improve functionality coverage.

2. **Dependency/caller information provides complementary value.** Its 5.2% drop is smaller but targets different criteria — integration (F3: +0.16) and architectural fit (M1: +0.16) — that test context alone does not cover.

3. **Features are partially complementary.** The combined removal (6.6%) is less than the sum of individual drops (10.6% + 5.2% = 15.8%), indicating some overlap in what they enable. However, each feature has unique impact on different criterion categories.

4. **LLM evaluation noise is a factor.** With binary scoring on 25 criteria and 16 PRs per condition, individual PRs can vary by +/-4 pp between runs. Aggregate trends are reliable; per-PR deltas should be interpreted cautiously.

---

## Appendix: Full Per-Criterion Delta Table

Delta = full_kg score minus ablated score. Positive = feature helped.

| ID | Category | KG-relevant | no_tests | no_deps | minimal |
|:--:|----------|:-----------:|:--------:|:-------:|:-------:|
| F1 | Functionality | | 0.000 | 0.000 | 0.000 |
| F2 | Functionality | | +0.500 | +0.263 | +0.312 |
| F3 | Functionality | * | -0.125 | +0.158 | 0.000 |
| F4 | Functionality | * | -0.125 | 0.000 | 0.000 |
| T1 | Tests | * | +0.062 | 0.000 | +0.062 |
| T2 | Tests | * | +0.438 | +0.105 | +0.188 |
| T3 | Tests | * | +0.062 | 0.000 | 0.000 |
| R1 | Readability | | 0.000 | 0.000 | -0.062 |
| R2 | Readability | | +0.062 | -0.053 | -0.062 |
| R3 | Readability | | 0.000 | 0.000 | 0.000 |
| M1 | Maintainability | * | -0.062 | +0.158 | 0.000 |
| M2 | Maintainability | | 0.000 | 0.000 | 0.000 |
| M3 | Maintainability | * | 0.000 | 0.000 | 0.000 |
| C1 | Consistency | | 0.000 | 0.000 | 0.000 |
| C2 | Consistency | * | +0.125 | +0.105 | +0.125 |
| P1 | Performance | | -0.125 | -0.053 | -0.125 |
| P2 | Performance | | 0.000 | 0.000 | 0.000 |
| S1 | Security | | +0.062 | 0.000 | +0.062 |
| S2 | Security | | -0.062 | 0.000 | 0.000 |
| S3 | Security | | +0.188 | +0.053 | +0.188 |
| Q1 | Quality | | 0.000 | 0.000 | 0.000 |
| Q2 | Quality | * | 0.000 | +0.053 | 0.000 |
| Q3 | Quality | | -0.188 | -0.263 | -0.188 |
| Q4 | Quality | | 0.000 | 0.000 | 0.000 |
| Q5 | Quality | | +0.188 | -0.053 | +0.125 |

---

*Generated by `scripts/run_ablation_study.py`*
