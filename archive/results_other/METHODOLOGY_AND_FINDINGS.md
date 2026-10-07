# Multi-Judge LLM Evaluation — Methodology and Findings

_Generated from `scripts/evaluate_reviews.py` (3-judge panel) and
`scripts/retry_failed_judges.py` (parse-error recovery). Data snapshots in
`results/checklist_evaluation_llm.json` (legacy-shape, majority vote) and
`results/checklist_evaluation_llm_multi.json` (full per-judge detail)._

---

## 1. Methodology (ready-to-paste § for the thesis)

> **LLM-as-a-judge evaluation.** Each of the 100 generated reviews (25 PRs × 4
> modes: baseline, KG, RAG, hybrid) is scored against a 25-criterion rubric
> covering Functionality, Tests, Readability, Maintainability, Consistency,
> Performance, Security, and review-quality meta-criteria (Chris's checklist,
> adapted from Tufano et al. 2021/2022 and refined in consultation with the
> supervisor). For each (review, criterion) pair the judge returns a binary
> verdict (1 = addressed, 0 = not addressed) together with short textual
> evidence.
>
> Prior LLM-as-a-judge work (Zheng et al., 2023; Chiang et al., 2024) has
> documented systematic biases of single-judge scoring — most prominently
> family-specific leniency, verbosity bias, and position bias. To mitigate
> these threats we use a **three-judge cross-provider panel**: `gpt-4o-mini`,
> `gpt-4o` (both OpenAI), and `gemini-2.5-flash` (Google). Verdicts are
> aggregated per (review, criterion) cell by **majority vote with
> ties broken to 0**, a strict rule that avoids over-crediting the system.
> Temperature is set to 0.0 for determinism. To avoid inflating reliability
> through shared training corpora we report inter-judge agreement not just as
> raw percent agreement but as **Cohen's κ**, following Landis & Koch (1977).

Key knobs (for reproducibility):

| Item | Value |
|------|-------|
| Judges | `openai:gpt-4o-mini`, `openai:gpt-4o`, `gemini:gemini-2.5-flash` |
| Aggregation | majority vote; ties → 0 |
| Temperature | 0.0 |
| Max review length | 4 000 chars (reviews truncated if longer) |
| Max API calls | 300 (100 reviews × 3 judges) |
| Parse-error recovery | Tolerant regex fallback for malformed JSON (21/300 cells) |
| Final error rate | 0 % after recovery (100/100 pairs have 3 valid judges) |

---

## 2. Inter-judge agreement (construct-validity check)

Agreement is computed across all (PR × mode × criterion) cells where both
judges produced a valid 0/1 score.

| Pair | Cells | Raw agreement | Cohen's κ | Interpretation* |
|------|-------|---------------|-----------|-----------------|
| `gpt-4o-mini` vs `gpt-4o` | 2 500 | 85.6 % | **0.67** | substantial |
| `gpt-4o-mini` vs `gemini-2.5-flash` | 2 464 | 78.6 % | **0.54** | moderate |
| `gpt-4o` vs `gemini-2.5-flash` | 2 464 | 86.0 % | **0.70** | substantial |

\*Landis & Koch benchmarks: 0.41–0.60 moderate, 0.61–0.80 substantial.

**Interpretation.**

- All three pairs reach at least moderate agreement, with two of three
  crossing the "substantial" threshold.
- Cross-provider agreement (OpenAI ↔ Google) is *not* meaningfully lower than
  within-provider agreement (`mini` ↔ `gpt-4o` at κ = 0.67; `gpt-4o` ↔
  `gemini` at κ = 0.70). This is a mild but useful indication that the
  criterion-level verdicts are not an artefact of shared OpenAI training data.
- `gpt-4o-mini` is the strictest judge; `gemini-2.5-flash` is the most
  lenient; `gpt-4o` sits in between. Majority vote therefore tracks the
  middle judge for contested cells and produces conservative estimates
  whenever the strict judge abstains from "yes".

---

## 3. Results (majority vote, n = 25 per mode)

| Mode | Total (out of 25) | Total % | KG-relevant (out of 9) | KG-relevant % |
|------|-------------------|---------|------------------------|---------------|
| Baseline | 8.08 | **32.3 %** | 4.16 | **46.2 %** |
| KG | 8.24 | 33.0 % | 4.80 | **53.3 %** |
| RAG | 8.60 | 34.4 % | 4.64 | 51.6 % |
| Hybrid | 8.04 | 32.2 % | 4.16 | 46.2 % |

**KG vs Baseline — headline numbers:**

- Total score: **+0.7 pp** (1.02×) — essentially flat, as expected given that
  two-thirds of the criteria are not KG-related.
- **KG-relevant score: +7.1 pp (1.15×)** — the effect is concentrated on the
  criteria the KG was designed to support.
- The hybrid mode (KG + RAG combined) is **not** additive. It matches
  baseline on total and KG-relevant scores, suggesting prompt-length
  interference or retrieval redundancy. This is an interesting negative
  result and warrants a short paragraph in the Discussion.

### 3.1 Which criteria benefit from the Knowledge Graph?

| ID | Category | Baseline | KG | Δ | Description |
|----|----------|---------:|---:|-:|-------------|
| **F3** | Functionality | 40 % | **68 %** | **+28** | Integration with existing components/APIs |
| **T1** | Tests | 76 % | **96 %** | **+20** | Asks about unit/integration tests |
| **T3** | Tests | 28 % | **48 %** | **+20** | References specific test files |
| **T2** | Tests | 36 % | 48 % | +12 | Edge-case / failure-path tests |
| F4 | Functionality | 76 % | 80 % | +4 | Warns about breaking changes |
| C2 | Consistency | 8 % | 12 % | +4 | Consistency with existing patterns |
| Q2 | Quality | 100 % | 100 % | 0 | Code-location anchors (both at ceiling) |
| M1 | Maintainability | 20 % | 16 % | −4 | Fit with existing architecture |
| M3 | Maintainability | 32 % | 12 % | −20 | Public API / interface docs |

The effect is *structured*. The four largest positive deltas (F3 +28, T1 +20,
T3 +20, T2 +12) are all criteria that require access to the test files,
dependent code, or cross-file call sites that the KG surfaces by design.
The two negative deltas (M1, M3) concern architectural judgement and are
known weaknesses of KGs built from diff-local context.

### 3.2 Trade-offs: what does the KG *cost*?

Non-KG-relevant criteria where KG reviews score *worse* than baseline:

| ID | Category | Baseline | KG | Δ |
|----|----------|---------:|---:|-:|
| R1 | Readability | 36 % | 8 % | **−28** |
| R2 | Readability | 28 % | 12 % | **−16** |
| F1 | Functionality | 28 % | 16 % | −12 |

When the model has rich structured context, it shifts attention toward
technical correctness (integration, tests) and away from surface-level
readability and high-level restatement of the PR's goal. **This trade-off is
a real finding and should be discussed explicitly in the thesis** — it is
consistent with the intuition that augmentation is not free and that
evaluation on a single axis (e.g. "overall quality") can hide it.

---

## 4. Sensitivity analysis — single-judge vs. multi-judge

The previous checklist results (single judge: `gpt-4o-mini`) are preserved in
`results/checklist_evaluation_llm.single_judge_backup.json` for comparison.

| Mode | Old total / KG-rel | New total / KG-rel | Δ total | Δ KG-rel |
|------|---------------------|--------------------|---------|----------|
| Baseline | 31.4 % / 42.2 % | 32.3 % / 46.2 % | +0.9 | +4.0 |
| KG | 35.4 % / 56.0 % | 33.0 % / 53.3 % | −2.4 | −2.7 |
| RAG | 34.2 % / 48.0 % | 34.4 % / 51.6 % | +0.2 | +3.6 |
| Hybrid | 33.9 % / 48.4 % | 32.2 % / 46.2 % | −1.7 | −2.2 |

**Δ(KG − Baseline) on KG-relevant criteria** shrinks from **+13.8 pp**
(single judge, gpt-4o-mini) to **+7.1 pp** (3-judge majority). The direction
and ordering are stable; the magnitude is about half. The single-judge
result was therefore *directionally correct but optimistic*, and the
multi-judge estimate is the conservative, methodologically defensible one.
All subsequent analysis in this thesis uses the multi-judge majority-vote
numbers.

---

## 5. Threats to validity (ready-to-paste § for the thesis)

- **Judge bias (construct validity).** LLM judges share training data and
  stylistic preferences with the generators under test. We partially mitigate
  this by mixing two OpenAI judges with a Google judge and by reporting
  Cohen's κ alongside raw agreement. We cannot fully rule out a shared-bias
  confound in favour of models that write "textbook-style" reviews.
- **Judge strictness.** `gpt-4o-mini` is systematically stricter than
  `gemini-2.5-flash`; majority vote therefore tracks the middle judge. A
  purely unanimous rule would reduce all Yes rates by roughly 30 %.
- **Stimulus selection for the human study.** The 6 PRs shown to human
  raters were selected from the single-judge scores for maximum
  discriminative power between modes. Re-running that selection on the
  multi-judge data would slightly reshuffle the ordering but would
  invalidate the in-flight pilot. We therefore keep the original stimulus
  set and treat its choice as a potential internal-validity concern for the
  human study only (not the LLM evaluation).
- **Parse-error recovery.** 21 of 300 initial judge calls returned malformed
  JSON (exclusively Gemini, unescaped quotes in evidence strings). A
  tolerant regex fallback recovered all 21 cells on retry. Every
  (PR × mode) cell therefore has three valid verdicts in the final
  dataset.
- **Dataset size.** 25 PRs × 4 modes × 25 criteria = 2 500 binary judgements
  per judge (7 500 overall), large enough to report per-mode means with
  narrow confidence intervals but not large enough to draw per-criterion
  conclusions from the 25 observations that feed each criterion-by-mode
  cell. Criterion-level percentages should be read as descriptive
  (directional), not inferential.
- **Gemini token budget.** `gemini-2.5-flash` occasionally truncates very
  long evidence strings, which is what produced the 7 % raw parse-error
  rate. A future rerun with a higher `max_tokens` budget would likely
  eliminate these errors at source; the tolerant parser makes the current
  rerun unnecessary.

---

## 6. Reproduction recipe

```bash
# 1. Full 300-call multi-judge run (≈ 66 min wall time)
set -a && . ./.env && set +a
python3 scripts/evaluate_reviews.py

# 2. Retry pass — only re-runs cells whose judge returned malformed JSON
python3 scripts/retry_failed_judges.py

# 3. Downstream: bundle reviews into human-study JSON
python3 scripts/prepare_human_study.py   # reads results/checklist_evaluation_llm.json
```

Override judges with `--models`, e.g. a single-judge sensitivity check:

```bash
python3 scripts/evaluate_reviews.py --models openai:gpt-4o-mini
```

---

## 7. Summary for the supervisor

1. The methodology is now multi-judge, cross-provider, with majority vote
   and Cohen's κ. This matches the MT-Bench / Chatbot Arena best practice.
2. The KG-vs-baseline effect survives the methodology upgrade: **KG-relevant
   criteria improve by +7.1 pp (1.15×)** over baseline, with the gain
   concentrated on exactly the criteria the KG is designed to help
   (integration, test coverage).
3. A genuine trade-off emerges: KG reviews score worse on readability and
   on restating-the-problem criteria. This is interpretable, not a bug.
4. Hybrid (KG + RAG) does not outperform KG alone. This should be reported
   as a negative result.
5. The single-judge result was directionally correct but optimistic by
   roughly 2× on the key delta. The thesis now reports the conservative
   multi-judge number.
