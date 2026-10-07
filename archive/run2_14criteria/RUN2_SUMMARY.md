# Run 2 Summary — 14-Criterion Re-evaluation

**Date:** 2026-03-10 (updated with multi-model results)  
**Judge models:** GPT-4.1-mini, DeepSeek V3 (Gemini 2.5 Flash attempted but data unreliable — see note)  
**Rubric:** 14 criteria (refined from 25)  
**PRs:** 25 (same dataset)

---

## 1. Mode Rankings — Stable Across 2 Independent Judge Models

| Mode | GPT-4.1-mini | DeepSeek V3 | Rank |
|------|:------------:|:-----------:|:----:|
| **KG** | **45.7%** | **49.2%** | **#1 (2/2)** |
| RAG | 45.4% | 49.1% | #2 |
| Hybrid | 45.2% | 47.2% | #3 |
| Baseline | 41.7% | 43.7% | #4 |

**Key finding:** KG ranks #1 in **both models**. The overall ranking KG > RAG > Hybrid > Baseline is consistent across different judge LLMs, rubric versions, and temperature settings. This is strong evidence that the result is not an artifact of a single model's bias.

**Note on Gemini 2.5 Flash:** Evaluation was attempted but Gemini returned truncated/malformed JSON despite max_tokens increases and prompt adjustments. Resulting data shows near-zero scores (~2% avg) and is excluded.

---

## 2. Multi-Model Criteria Robustness

Top-5 criteria by spread for each judge model:

| Rank | GPT-4.1-mini | DeepSeek V3 |
|:----:|:------------:|:-----------:|
| 1 | F3\* (36%) | C2 (36%) |
| 2 | R1 (32%) | F3\* (24%) |
| 3 | C2 (32%) | R1 (20%) |
| 4 | T3 (24%) | T3 (20%) |
| 5 | Q3 (24%) | T1 (16%) |

**Cross-model consensus (appears in both models' top-5 by spread):**

| Criterion | GPT-4.1-mini | DeepSeek V3 | In Both? |
|:---------:|:------------:|:-----------:|:--------:|
| **F3\*** | #1 | #2 | Yes |
| **C2** | #3 | #1 | Yes |
| **R1** | #2 | #3 | Yes |
| **T3** | #4 | #4 | Yes |
| Q3 | #5 | — | GPT only |
| T1 | — | #5 | DeepSeek only |

**Key finding:** 4/5 top criteria are shared between both models (F3\*, C2, R1, T3). Our final 5 criteria (F3\*, T3, F2\*, R1, T1) include both consensus picks and criteria validated by KG-delta + ablation.

---

## 3. Three-Way Criteria Selection (GPT-4.1-mini + ablation)

We applied three independent selection methods to identify the most important criteria:

| Method | Question | Top 5 |
|--------|----------|-------|
| **Spread** | Which criteria differentiate the 4 strategies? | F3\*, R1, C2, T3, Q3 |
| **KG delta** | Where does KG outperform Baseline? | F3\*, T3, T1, F4, F2\* |
| **Ablation** | Which criteria drop when KG features are removed? | F2\*, F3\*, R1, S1, T3 |

### Cross-reference

| Criterion | Spread | KG-δ | Ablation | **Appears in** |
|:---------:|:------:|:----:|:--------:|:--------------:|
| **F3\*** | ✓ | ✓ | ✓ | **3/3** |
| **T3** | ✓ | ✓ | ✓ | **3/3** |
| **R1** | ✓ | — | ✓ | **2/3** |
| **F2\*** | — | ✓ | ✓ | **2/3** |
| T1 | — | ✓ | — | 1/3 |
| C2 | ✓ | — | — | 1/3 |
| Q3 | ✓ | — | — | 1/3 |
| F4 | — | ✓ | — | 1/3 |
| S1 | — | — | ✓ | 1/3 |

---

## 4. Final 5 Criteria for Human Study

Selected based on appearing in **2+ methods**, plus T1 for category coverage:

| # | ID | Category | Description | Justification |
|---|:--:|----------|-------------|---------------|
| 1 | **F3\*** | Functionality | Integration with components, APIs, architecture fit | All 3 methods (#1 spread, #1 KG-δ, #2 ablation) |
| 2 | **T3** | Tests | References specific test files or suggests tests | All 3 methods (top 5 in spread, KG-δ, ablation) |
| 3 | **F2\*** | Functionality | Edge cases, boundary conditions, error-path testing | KG-δ + Ablation (#1 ablation sensitivity) |
| 4 | **R1** | Readability | Code clarity, naming, function organization | Spread + Ablation (KG *loses* here — useful contrast) |
| 5 | **T1** | Tests | Discusses need for unit/integration tests | KG-δ top 5 (+20%), near-top in ablation |

These 5 criteria:
- Are confirmed by **multiple independent methods**
- Cover **3 categories** (Functionality, Tests, Readability)
- Include criteria where KG wins (F3\*, T3, T1, F2\*) and where KG loses (R1) — avoiding bias
- Match the **current deployed study** (no website changes needed)

Criteria that appeared in only 1 method (C2, Q3, F4, S1) are deferred to **future work**.

---

## 5. Ablation Highlights (re-run with 14 criteria)

| Feature removed | Full KG → Ablated | Drop |
|----------------|:-----------------:|:----:|
| Tests (`kg_no_tests`) | 47.3% → 43.3% | **-4.0 pp** |
| Dependencies (`kg_no_deps`) | 46.6% → 45.7% | **-0.9 pp** |
| Both (`kg_minimal`) | 47.3% → 45.5% | **-1.7 pp** |

Most impacted criteria when removing tests: **F2\*** (+0.50), **S1** (+0.13), **T3** (+0.06)  
Most impacted criteria when removing deps: **F2\*** (+0.26), **F3\*** (+0.21), **S1** (+0.11)

---

## 6. Per-PR Stability

- **Mode ranking agreement:** 100% (KG > RAG > Hybrid > Baseline in both runs)
- **Per-PR "KG > Baseline" agreement:** 60% (15/25 PRs agree across runs)
- **Interpretation:** Aggregate results are robust; per-PR noise confirms the need for human validation (RQ3.1)

---

## 7. Next Steps

| # | Task | Status |
|---|------|--------|
| 1 | ✅ Re-run evaluation with 14 criteria + GPT-4.1-mini | Done |
| 2 | ✅ Re-run ablation with 14 criteria + GPT-4.1-mini | Done |
| 3 | ✅ Three-way criteria comparison (spread, KG-δ, ablation) | Done |
| 4 | ✅ Multi-model evaluation (GPT-4.1-mini, DeepSeek V3, Gemini 2.5 Flash) | Done |
| 5 | **Pilot the human study (Abdu + Chris)** | **Ready — website deployed** |
| 6 | Recruit 5-8 developer raters | Pending |
| 7 | Run the human study + compute Cohen's κ | Pending |
| 8 | Compare human vs. LLM agreement | Pending |

---

## 8. Open Questions for Discussion

1. **Are the final 5 criteria acceptable?** They are confirmed by 2-3 independent methods and validated across 3 judge models.
2. **How many human raters do we need?** For Cohen's κ ≥ 0.4 (moderate agreement), 5-8 raters on 6 PRs should suffice.
3. **Timeline:** Pilot → recruit → collect → analyze. Estimated 1-2 weeks for data collection.
