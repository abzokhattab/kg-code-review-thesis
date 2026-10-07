# Progress Report — Since Last Meeting

**Date:** March 2026  
**Author:** Abdu Khattab  
**Thesis:** Enhancing AI-Assisted Code Reviews with Knowledge Graph Context

---

## 1. What Was Done

| # | Task | Status |
|---|------|--------|
| 1 | Refined rubric from 25 → 14 criteria (merged overlaps) | Done |
| 2 | Re-evaluated all 25 PRs × 4 modes with 14-criterion rubric (GPT-4.1-mini) | Done |
| 3 | Re-ran ablation study with 14 criteria | Done |
| 4 | Multi-model validation — DeepSeek V3 (successful), Gemini 2.5 Flash (failed*) | Done |
| 5 | Three-way criteria selection → final 5 for human study | Done |
| 6 | Built & deployed human evaluation website | Done |
| 7 | Piloted the study myself | Done |

\* Gemini 2.5 Flash had persistent API issues (truncated/malformed JSON responses) resulting in near-zero scores across the board — data is unreliable and excluded from analysis.

---

## 2. Rubric Refinement: 25 → 14 Criteria

The original 25-criterion rubric had overlapping criteria. We merged related ones and dropped consistently uninformative criteria (e.g., M3 — API docs — always scored 0%).

### The 14 criteria

| ID | Category | Description |
|:--:|----------|-------------|
| **F1** | Functionality | Verifies that the change addresses the stated problem/requirement |
| **F2\*** | Functionality | Identifies edge cases, boundary conditions, error-path testing needs *(merged F2 + T2)* |
| **F3\*** | Functionality | Checks integration with existing components, APIs, architecture fit *(merged F3 + M1)* |
| **F4** | Functionality | Warns about potential breaking changes or impact on dependents |
| **T1** | Tests | Asks about or discusses the need for unit/integration tests |
| **T3** | Tests | References specific test files or suggests which tests to add/update |
| **R1** | Readability | Comments on code clarity, naming conventions, function organization |
| **R2** | Readability | Identifies unnecessary complexity or suggests simplification |
| **P1** | Performance | Identifies potential performance issues or inefficiencies |
| **S1** | Security | Checks for proper input validation or sanitization |
| **S3** | Security | Assesses error handling and failure recovery |
| **Q3** | Quality | Distinguishes between blocking issues and minor suggestions |
| **Q5** | Quality | Explains reasoning behind suggestions (the "why") |
| **C2** | Consistency | Checks if similar problems are solved consistently with existing patterns |

---

## 3. Run 2 Results — 14 Criteria, GPT-4.1-mini Judge

### Mode Averages

| Mode | Avg Score | vs Baseline |
|------|:---------:|:-----------:|
| **KG** | **45.7%** | **+4.0 pp** |
| RAG | 45.4% | +3.7 pp |
| Hybrid | 45.2% | +3.5 pp |
| Baseline | 41.7% | — |

**KG ranks #1.** Same ordering as Run 1 (25-criteria), confirming the result is robust to rubric changes.

### Per-Criterion Pass Rates (GPT-4.1-mini)

| Criterion | Category | Baseline | RAG | KG | Hybrid | Spread | KG−BL |
|:---------:|----------|:--------:|:---:|:--:|:------:|:------:|:-----:|
| **F3\*** | Functionality | 20% | 24% | **56%** | 24% | **36%** | **+36%** |
| **R1** | Readability | **44%** | 40% | 12% | 16% | 32% | −32% |
| **C2** | Consistency | 12% | **40%** | 8% | 12% | 32% | −4% |
| **T3** | Tests | 36% | 40% | **60%** | 52% | 24% | +24% |
| **Q3** | Quality | 0% | 12% | 4% | **24%** | 24% | +4% |
| **T1** | Tests | 76% | 84% | **96%** | 84% | 20% | +20% |
| **F2\*** | Functionality | 44% | 48% | **52%** | 48% | 8% | +8% |
| **F4** | Functionality | 84% | 88% | **96%** | 100% | 16% | +12% |
| **S3** | Security | 28% | 28% | 24% | **32%** | 8% | −4% |
| **R2** | Readability | **20%** | 12% | 12% | 4% | 16% | −8% |
| **S1** | Security | 12% | 12% | 12% | **24%** | 12% | 0% |
| **P1** | Performance | 8% | 8% | 8% | **12%** | 4% | 0% |
| **Q5** | Quality | 100% | 100% | 100% | 100% | 0% | 0% |
| **F1** | Functionality | 100% | 100% | 100% | 100% | 0% | 0% |

**Key observations:**
- **F3\* (integration awareness)** is the strongest discriminator — KG scores 56% vs Baseline 20% (+36 pp)
- **T3 (specific test references)** and **T1 (test discussion)** — KG leads by +24 pp and +20 pp respectively
- **R1 (readability)** — KG *loses* here (12% vs 44%), confirming the trade-off: structured context shifts attention away from style
- **Q5, F1** are non-discriminating (100% for all modes)

---

## 4. Multi-Model Validation — DeepSeek V3

We re-ran the identical 14-criterion evaluation with DeepSeek V3 as an independent judge to test whether the results depend on GPT's specific biases.

### Mode Averages: DeepSeek V3

| Mode | Avg Score | vs Baseline |
|------|:---------:|:-----------:|
| **KG** | **49.2%** | **+5.5 pp** |
| RAG | 49.1% | +5.4 pp |
| Hybrid | 47.2% | +3.5 pp |
| Baseline | 43.7% | — |

**KG ranks #1 in DeepSeek as well.** Same ordering: KG > RAG > Hybrid > Baseline.

### Per-Criterion Pass Rates (DeepSeek V3)

| Criterion | Category | Baseline | RAG | KG | Hybrid | Spread | KG−BL |
|:---------:|----------|:--------:|:---:|:--:|:------:|:------:|:-----:|
| **C2** | Consistency | 36% | **68%** | 44% | 32% | **36%** | +8% |
| **F3\*** | Functionality | 56% | 76% | **80%** | 68% | 24% | **+24%** |
| **R1** | Readability | 20% | **36%** | 16% | 16% | 20% | −4% |
| **T3** | Tests | 28% | 40% | **48%** | 40% | 20% | **+20%** |
| **T1** | Tests | 72% | 80% | **88%** | 80% | 16% | +16% |
| **R2** | Readability | **32%** | 20% | 24% | 16% | 16% | −8% |
| **S1** | Security | 20% | 20% | 16% | **32%** | 16% | −4% |
| **Q3** | Quality | 16% | 8% | **24%** | 20% | 16% | +8% |
| **F2\*** | Functionality | 40% | 40% | **48%** | 44% | 8% | +8% |
| **F4** | Functionality | 72% | 72% | **80%** | 80% | 8% | +8% |
| **S3** | Security | 24% | 28% | 24% | 28% | 4% | 0% |
| **P1** | Performance | 8% | 12% | 8% | 12% | 4% | 0% |
| **F1** | Functionality | 88% | 88% | 88% | **92%** | 4% | 0% |
| **Q5** | Quality | 100% | 100% | 100% | 100% | 0% | 0% |

### Cross-Model Comparison

| Mode | GPT-4.1-mini | DeepSeek V3 | Rank |
|------|:------------:|:-----------:|:----:|
| **KG** | **45.7%** | **49.2%** | **#1 in both** |
| RAG | 45.4% | 49.1% | #2 |
| Hybrid | 45.2% | 47.2% | #3 |
| Baseline | 41.7% | 43.7% | #4 |

**Result: The mode ranking KG > RAG > Hybrid > Baseline is identical across both independent judge models.** This is strong evidence that the finding is not an artifact of a single model's bias.

### Gemini 2.5 Flash — Technical Issues

We also attempted evaluation with Gemini 2.5 Flash. The model consistently returned truncated or malformed JSON responses despite:
- Increasing `max_tokens` to 4096
- Shortening evidence requirements to ≤15 words

The resulting data shows near-zero scores across all modes and criteria (avg ≈ 2%), making it unusable. Gemini data is **excluded** from analysis. Two independent models (GPT-4.1-mini, DeepSeek V3) still provide robust cross-validation.

---

## 5. Top-5 Criteria by Spread — Cross-Model Consistency

| Rank | GPT-4.1-mini | DeepSeek V3 |
|:----:|:------------:|:-----------:|
| 1 | F3\* (36%) | C2 (36%) |
| 2 | R1 (32%) | F3\* (24%) |
| 3 | C2 (32%) | R1 (20%) |
| 4 | T3 (24%) | T3 (20%) |
| 5 | Q3 (24%) | T1 (16%) |

**Cross-model consensus (appears in both models' top-5):**

| Criterion | GPT-4.1-mini | DeepSeek V3 | In Both? |
|:---------:|:------------:|:-----------:|:--------:|
| **F3\*** | #1 | #2 | Yes |
| **C2** | #3 | #1 | Yes |
| **R1** | #2 | #3 | Yes |
| **T3** | #4 | #4 | Yes |
| Q3 | #5 | — | GPT only |
| T1 | — | #5 | DeepSeek only |

4 out of 5 top criteria are shared between both models. The one discrepancy: GPT highlights Q3 (blocking vs minor), DeepSeek highlights T1 (test discussion).

---

## 6. Three-Way Criteria Selection

We applied three independent methods to identify the most important criteria:

| Method | Question | Top 5 |
|--------|----------|-------|
| **Spread** | Which criteria differentiate the 4 strategies? | F3\*, R1, C2, T3, Q3 |
| **KG delta** | Where does KG outperform Baseline most? | F3\*, T3, T1, F4, F2\* |
| **Ablation** | Which criteria drop when KG features are removed? | F2\*, F3\*, R1, S1, T3 |

### Cross-reference

| Criterion | Spread | KG-δ | Ablation | Appears in |
|:---------:|:------:|:----:|:--------:|:----------:|
| **F3\*** | Yes | Yes | Yes | **3/3** |
| **T3** | Yes | Yes | Yes | **3/3** |
| **R1** | Yes | — | Yes | **2/3** |
| **F2\*** | — | Yes | Yes | **2/3** |
| T1 | — | Yes | — | 1/3 |
| C2 | Yes | — | — | 1/3 |
| Q3 | Yes | — | — | 1/3 |
| F4 | — | Yes | — | 1/3 |
| S1 | — | — | Yes | 1/3 |

---

## 7. Ablation Study — 14 Criteria

We removed KG features one at a time to measure their contribution:

| Config | What's removed | Full KG → Ablated | Drop |
|--------|---------------|:-----------------:|:----:|
| `kg_no_tests` | Test info from KG | 47.3% → 43.3% | **−4.0 pp** |
| `kg_minimal` | Both tests + deps | 47.3% → 45.5% | **−1.7 pp** |
| `kg_no_deps` | Dependency info from KG | 46.6% → 45.7% | **−0.9 pp** |

### Most sensitive criteria per ablation

| Ablation | Most Affected Criteria (positive delta = score drops) |
|----------|------|
| `kg_no_tests` | F2\* (+50%), S3 (+13%), S1 (+13%), T1 (+6%), T3 (+6%) |
| `kg_no_deps` | F2\* (+26%), F3\* (+21%), S1 (+11%), T1 (+5%) |
| `kg_minimal` | F2\* (+25%), T3 (+13%), S1 (+6%) |

**Key finding:** Test information is the most valuable KG feature (−4.0 pp when removed). F2\* (edge cases) is the most sensitive criterion — it degrades consistently across all ablation configs.

---

## 8. Final 5 Criteria for Human Study

Selected based on appearing in **2+ independent methods**, plus T1 for category coverage:

| # | ID | Category | Description | Justification |
|---|:--:|----------|-------------|---------------|
| 1 | **F3\*** | Functionality | Integration with components, APIs, architecture fit | All 3 methods (spread #1, KG-δ #1, ablation top-5) |
| 2 | **T3** | Tests | References specific test files or suggests tests | All 3 methods |
| 3 | **F2\*** | Functionality | Edge cases, boundary conditions, error-path testing | KG-δ + Ablation (#1 ablation sensitivity) |
| 4 | **R1** | Readability | Code clarity, naming, function organization | Spread + Ablation (KG *loses* here — avoids bias) |
| 5 | **T1** | Tests | Discusses need for unit/integration tests | KG-δ top-5 (+20%), confirmed by DeepSeek top-5 |

These 5 criteria:
- Are confirmed by **multiple independent methods**
- Cover **3 categories** (Functionality, Tests, Readability)
- Include criteria where KG wins (F3\*, T3, T1, F2\*) and where KG loses (R1) — avoiding pro-KG bias
- Are validated across **2 independent judge models**

---

## 9. Human Evaluation Study

### Setup

| Aspect | Detail |
|--------|--------|
| **Website** | https://pr-review-human-eval.netlify.app |
| **PRs** | 6 (stratified sample: 2 high-spread, 2 mid, 2 low) |
| **Criteria** | 5 (F3\*, F2\*, T1, T3, R1) |
| **Reviews per PR** | 4 (one per mode: baseline, RAG, KG, hybrid) — blinded, randomized |
| **Time estimate** | ~15 minutes per rater |
| **Data collection** | Automatic to Google Sheet (per-PR submission, no data loss on early exit) |
| **Practice round** | Included before actual evaluation |
| **Progress saving** | localStorage — raters can resume |
| **Layout** | 2×2 grid showing all 4 reviews side by side |

### PR Selection (ordered easy → hard by diff size)

| Order | PR # | Repository | Description |
|:-----:|:----:|------------|-------------|
| 1 | #5 | grafana/grafana | Small Go change — toggle feature flag |
| 2 | #1 | scikit-learn | Python fix — ColumnTransformer error handling |
| 3 | #11 | jenkinsci/jenkins | Java — add plugin compatibility check |
| 4 | #21 | apache/kafka | Java/Scala — JDK 11 API cleanup |
| 5 | #15 | grafana/grafana | Go/TS — dashboard permissions refactor |
| 6 | #10 | grafana/grafana | Go — query caching layer implementation |

### Pilot Results (Abdu, rater_id: "tes")

Completed all 6 PRs in ~73 seconds total. Checkmarks indicate which criteria were met (1 = yes, empty = no):

| PR | Mode | F3\* | F2\* | T1 | T3 | R1 |
|:--:|------|:----:|:----:|:--:|:--:|:--:|
| #5 | baseline | | | 1 | | |
| #5 | rag | | | 1 | | |
| #5 | hybrid | | | | | |
| #5 | kg | | | 1 | | |
| #1 | baseline | | | 1 | | |
| #1 | rag | | 1 | 1 | | |
| #1 | hybrid | | | | | |
| #1 | kg | 1 | | 1 | | 1 |
| #11 | hybrid | 1 | | 1 | | 1 |
| #11 | kg | 1 | | 1 | | |
| #11 | rag | | | | | 1 |
| #11 | baseline | | | | | 1 |
| #21 | kg | | 1 | 1 | 1 | |
| #21 | baseline | 1 | | 1 | | |
| #21 | rag | 1 | 1 | 1 | | |
| #21 | hybrid | 1 | | | | |
| #15 | baseline | | | 1 | 1 | 1 |
| #15 | hybrid | | | 1 | 1 | |
| #15 | kg | | | 1 | 1 | |
| #15 | rag | | | 1 | 1 | |
| #10 | hybrid | | 1 | 1 | 1 | |
| #10 | rag | 1 | 1 | 1 | 1 | |
| #10 | kg | 1 | | 1 | | |
| #10 | baseline | | 1 | 1 | 1 | |

*Note: This is a single rater's pilot — not statistically meaningful yet. Needs 5-8 raters for Cohen's κ analysis.*

---

## 10. Comparison: Run 1 (25 criteria) vs Run 2 (14 criteria)

| Aspect | Run 1 | Run 2 |
|--------|-------|-------|
| Criteria | 25 | 14 (merged overlaps) |
| Judge | GPT-4o-mini | GPT-4.1-mini |
| Mode ranking | KG > RAG ≈ Hybrid > BL | KG > RAG > Hybrid > BL |
| KG avg | 35.4% | 45.7% |
| BL avg | 31.4% | 41.7% |
| KG−BL gap | +4.0 pp | +4.0 pp |
| Top KG criterion | F3 (+40%) | F3\* (+36%) |
| KG wins PRs | 5/25 | N/A (aggregate) |

**Key finding:** The KG advantage (+4.0 pp) is remarkably stable across rubric versions, judge models, and prompt formats.

---

## 11. Summary of Key Findings

1. **KG ranks #1 across all valid conditions** — two judge models, two rubric versions, consistent ranking.
2. **The KG advantage is structural:** F3\* (integration), T3 (test references), T1 (test discussion) — all criteria requiring repository-level context.
3. **There is a real trade-off:** KG loses on R1 (readability) — structured context shifts LLM attention away from style.
4. **Test info is the most valuable KG feature** (ablation: −4.0 pp when removed).
5. **Multi-model validation confirms robustness** — GPT-4.1-mini and DeepSeek V3 agree on mode ranking and top criteria.
6. **Human study is ready** — website deployed, data pipeline working, pilot completed.

---

## 12. Next Steps

| # | Task | Status |
|---|------|--------|
| 1 | Chris pilots the study | **Ready** |
| 2 | Recruit 5-8 developer raters | Pending |
| 3 | Collect human ratings | Pending |
| 4 | Compute inter-rater agreement (Cohen's κ) | Pending |
| 5 | Compare human vs. LLM agreement | Pending |
| 6 | Write up results in thesis | Pending |

---

## 13. Open Questions

1. **Are the final 5 criteria acceptable?** Confirmed by 2-3 methods and 2 judge models.
2. **Rater count:** 5-8 for moderate Cohen's κ (≥ 0.4)?
3. **Timeline:** Pilot → recruit → collect → analyze. ~1-2 weeks for data collection.
4. **Gemini re-run:** Worth retrying with a different API approach, or 2 models sufficient?
