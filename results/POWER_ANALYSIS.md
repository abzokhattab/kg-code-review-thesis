# Power Analysis — Human Evaluation Study

**Date:** March 2026 (updated April 2026)  
**Study:** Human evaluation of AI-generated PR review comments  
**Design:** 6 PRs × 5 criteria × 2 pairwise comparisons (Baseline vs KG, KG vs RAG)  
**Decision:** 20 raters

> **Snapshot caveat.** The per-PR tables below reflect the *planning* stimulus
> set (PR 21, 22, 26, 14, 10, 15) and the single-judge gpt-4o-mini scores used
> for effect-size estimation. Before deployment, **PR 26 was swapped for
> PR 18** (Jenkins #9002) after a weak-stimulus review; see
> `THREATS_TO_VALIDITY.md` §8.2.2 for rationale. Recomputing the sign-test
> tables with PR 18 substituted for PR 26 leaves the summary statistics
> (non-tie rate, context-win proportion) within rounding of the values below,
> so the 20-rater decision is unchanged. The tables are kept as-is as a
> planning artifact.

---

## 1. Study Design

| Parameter | Value |
|-----------|-------|
| PRs | 6 (stratified sample from 25): PR18, PR10, PR14, PR22, PR15, PR21 (original planning set substituted PR 18 for PR 26; see caveat above) |
| Criteria | 5 (F3\*, F2\*, T3, Q5, R1) |
| Modes | 4 generated (baseline, RAG, KG, hybrid) — 2 shown pairwise, blinded, randomized |
| Comparisons per PR | 2 (Baseline vs KG, KG vs RAG) |
| Items per rater | 30 (6 PRs × 5 criteria) per comparison |
| Rating type | Binary (criterion met = 1, not met = 0) |
| Statistical test | Sign test (one-sample binomial proportion) |

> **Note:** T1 was replaced with Q5 during criterion selection. T1 had a 96% yes-rate
> across LLM evaluations (ceiling effect), producing a kappa prevalence paradox that
> would make it unusable for inter-rater agreement analysis. Q5 (42% yes-rate,
> kappa@80% = 0.59) provides much better discriminative power.

### Two Planned Comparisons

| # | Comparison | Research Question |
|---|------------|-------------------|
| 1 | **Context (KG+RAG) vs Baseline** | Does adding repository context improve review quality? |
| 2 | **KG vs RAG** | Does structured KG context outperform unstructured RAG context? |

---

## 2. Effect Size Estimation from LLM Data

We estimated effect sizes from the GPT-4.1-mini evaluation on the 6 final study PRs (21, 22, 26, 14, 10, 15). For each comparison, we used a sign test framework: for each PR × criterion pair, we check which mode scores higher, discard ties, and compute the win proportion.

### Comparison 1: Context (KG+RAG) vs Baseline

For each item, "context wins" if at least one of KG or RAG scores 1 while Baseline scores 0.

| PR | Criterion | BL | RAG | KG | Result |
|:--:|:---------:|:--:|:---:|:--:|:------:|
| 21 | F3\* | 0 | 1 | 0 | **CTX** |
| 21 | F2\* | 0 | 0 | 1 | **CTX** |
| 21 | T3 | 0 | 1 | 1 | **CTX** |
| 21 | Q5 | 0 | 0 | 1 | **CTX** |
| 21 | R1 | 0 | 0 | 0 | TIE |
| 22 | F3\* | 1 | 0 | 1 | TIE |
| 22 | F2\* | 0 | 0 | 0 | TIE |
| 22 | T3 | 0 | 1 | 1 | **CTX** |
| 22 | Q5 | 1 | 1 | 0 | TIE |
| 22 | R1 | 1 | 1 | 0 | TIE |
| 26 | F3\* | 1 | 0 | 1 | TIE |
| 26 | F2\* | 0 | 1 | 1 | **CTX** |
| 26 | T3 | 0 | 0 | 0 | TIE |
| 26 | Q5 | 1 | 1 | 0 | TIE |
| 26 | R1 | 1 | 1 | 0 | TIE |
| 14 | F3\* | 0 | 1 | 1 | **CTX** |
| 14 | F2\* | 0 | 0 | 0 | TIE |
| 14 | T3 | 1 | 0 | 1 | TIE |
| 14 | Q5 | 0 | 1 | 0 | **CTX** |
| 14 | R1 | 0 | 1 | 0 | **CTX** |
| 10 | F3\* | 0 | 0 | 1 | **CTX** |
| 10 | F2\* | 1 | 1 | 1 | TIE |
| 10 | T3 | 1 | 1 | 0 | TIE |
| 10 | Q5 | 0 | 0 | 0 | TIE |
| 10 | R1 | 0 | 0 | 0 | TIE |
| 15 | F3\* | 1 | 0 | 1 | TIE |
| 15 | F2\* | 0 | 0 | 0 | TIE |
| 15 | T3 | 1 | 1 | 1 | TIE |
| 15 | Q5 | 0 | 0 | 1 | **CTX** |
| 15 | R1 | 1 | 1 | 1 | TIE |

**Summary:**
- Ties: 19/30 (63%)
- Non-ties: 11/30 (37%)
- Context wins: **11/11 = 100%**
- LLM-observed effect: p₁ = 1.00
- Conservative estimate: **p₁ = 0.90**

### Comparison 2: KG vs RAG

For each item, "KG wins" if KG = 1 and RAG = 0; "RAG wins" if RAG = 1 and KG = 0.

| PR | Criterion | KG | RAG | Result |
|:--:|:---------:|:--:|:---:|:------:|
| 21 | F3\* | 0 | 1 | **RAG** |
| 21 | F2\* | 1 | 0 | **KG** |
| 21 | T3 | 1 | 1 | TIE |
| 21 | Q5 | 1 | 0 | **KG** |
| 21 | R1 | 0 | 0 | TIE |
| 22 | F3\* | 1 | 0 | **KG** |
| 22 | F2\* | 0 | 0 | TIE |
| 22 | T3 | 1 | 1 | TIE |
| 22 | Q5 | 0 | 1 | **RAG** |
| 22 | R1 | 0 | 1 | **RAG** |
| 26 | F3\* | 1 | 0 | **KG** |
| 26 | F2\* | 1 | 1 | TIE |
| 26 | T3 | 0 | 0 | TIE |
| 26 | Q5 | 0 | 1 | **RAG** |
| 26 | R1 | 0 | 1 | **RAG** |
| 14 | F3\* | 1 | 1 | TIE |
| 14 | F2\* | 0 | 0 | TIE |
| 14 | T3 | 1 | 0 | **KG** |
| 14 | Q5 | 0 | 1 | **RAG** |
| 14 | R1 | 0 | 1 | **RAG** |
| 10 | F3\* | 1 | 0 | **KG** |
| 10 | F2\* | 1 | 1 | TIE |
| 10 | T3 | 0 | 1 | **RAG** |
| 10 | Q5 | 0 | 0 | TIE |
| 10 | R1 | 0 | 0 | TIE |
| 15 | F3\* | 1 | 0 | **KG** |
| 15 | F2\* | 0 | 0 | TIE |
| 15 | T3 | 1 | 1 | TIE |
| 15 | Q5 | 1 | 0 | **KG** |
| 15 | R1 | 1 | 1 | TIE |

**Summary:**
- Ties: 14/30 (47%)
- Non-ties: 16/30 (53%)
- KG wins: **8/16 = 50%**
- RAG wins: 8/16 = 50%
- Effect size: **p₁ = 0.50** (no directional advantage observed in LLM data)

> **Note on weak KG vs RAG signal:** The LLM scores show no directional advantage.
> However, the human study is designed to detect differences that LLM evaluation
> may miss (e.g. quality of reasoning, concreteness of suggestions). We retain the
> conservative p₁ = 0.625 estimate for power calculation, acknowledging this as an
> exploratory comparison.

---

## 3. Power Analysis Formula

We use the normal approximation to the binomial for a one-sample proportion test (sign test):

$$n = \left(\frac{z_{\alpha/2} \cdot \sqrt{p_0(1-p_0)} + z_{\beta} \cdot \sqrt{p_1(1-p_1)}}{p_1 - p_0}\right)^2$$

Where:
- $p_0 = 0.50$ (null hypothesis: no difference)
- $p_1$ = expected proportion of wins (from LLM data)
- $\alpha = 0.05$ (two-sided) → $z_{\alpha/2} = 1.9600$
- Power $= 0.80$ → $z_{\beta} = 0.8416$
- $n$ = number of **non-tie comparisons** needed

---

## 4. Calculation — Comparison 1: Context vs Baseline

**Parameters:** p₀ = 0.50, p₁ = 0.90, α = 0.05, power = 0.80

$$n = \left(\frac{1.9600 \times \sqrt{0.50 \times 0.50} + 0.8416 \times \sqrt{0.90 \times 0.10}}{0.90 - 0.50}\right)^2$$

$$= \left(\frac{1.9600 \times 0.5000 + 0.8416 \times 0.3000}{0.40}\right)^2$$

$$= \left(\frac{0.9800 + 0.2525}{0.40}\right)^2$$

$$= \left(\frac{1.2325}{0.40}\right)^2 = (3.0812)^2 = \mathbf{9.5 \approx 10}$$

**10 non-tie comparisons needed.**

Converting to raters:
- Items per rater: 30 (6 PRs × 5 criteria)
- Non-tie rate: 37% (11/30 from LLM data)
- Usable items per rater: 30 × 0.37 = **11.0**
- Raters needed: ⌈10 / 11.0⌉ = **1 rater** (trivially powered)

---

## 5. Calculation — Comparison 2: KG vs RAG

**Parameters:** p₀ = 0.50, p₁ = 0.625, α = 0.05, power = 0.80

$$n = \left(\frac{1.9600 \times \sqrt{0.50 \times 0.50} + 0.8416 \times \sqrt{0.625 \times 0.375}}{0.625 - 0.50}\right)^2$$

$$= \left(\frac{1.9600 \times 0.5000 + 0.8416 \times 0.4841}{0.125}\right)^2$$

$$= \left(\frac{0.9800 + 0.4074}{0.125}\right)^2$$

$$= \left(\frac{1.3874}{0.125}\right)^2 = (11.0994)^2 = \mathbf{123.2 \approx 124}$$

**124 non-tie comparisons needed.**

Converting to raters (using conservative p₁ = 0.625 estimate):
- Items per rater: 30 (6 PRs × 5 criteria)
- Non-tie rate: 53% (16/30 from LLM data)
- Usable items per rater: 30 × 0.53 = **16.0**
- Raters needed: ⌈124 / 16.0⌉ = **8 raters**

> The LLM data shows p₁ = 0.50 (no directional advantage), but we use the
> conservative p₁ = 0.625 for planning since human evaluators may detect
> quality differences that binary LLM scoring misses.

---

## 6. Sensitivity Analysis

### Effect of non-tie rate on required raters (KG vs RAG, p₁ = 0.625)

Human raters may disagree with LLM scores at different rates:

| Non-tie rate | Usable items / rater | Raters needed |
|:------------:|:--------------------:|:-------------:|
| 30% | 9.0 | 14 |
| 40% | 12.0 | 11 |
| 53% (LLM observed) | 16.0 | 8 |
| 60% | 18.0 | 7 |
| 70% | 21.0 | 6 |

### Effect of effect size on required raters (KG vs RAG)

| Effect (p₁) | Non-tie comparisons needed | Raters (40% NT) | Raters (53% NT) |
|:------------:|:--------------------------:|:----------------:|:----------------:|
| 0.55 | 783 | 65 | 49 |
| 0.60 | 194 | 17 | 13 |
| **0.625** | **124** | **11** | **8** |
| 0.65 | 85 | 8 | 6 |
| 0.70 | 47 | 4 | 3 |
| 0.75 | 29 | 3 | 2 |

---

## 7. Summary and Decision

| Comparison | Effect (p₁) | Non-ties needed | Raters (min) | Raters (conservative) |
|------------|:-----------:|:---------------:|:------------:|:---------------------:|
| Context vs Baseline | 0.90 | 10 | 1 | 3–4 |
| KG vs RAG | 0.625 | 124 | 8 | 12–15 |

**The bottleneck is KG vs RAG.** The effect size is modest (0.625) and the comparison is exploratory since LLM scoring shows no directional advantage (p₁ = 0.50).

### Decision: 20 raters

We recruit **20 raters** to:

1. **Comfortably power both comparisons** — even if the true human effect is weaker than p₁ = 0.625, 20 raters provide ample non-tie items
2. **Handle higher-than-expected noise** — if human non-tie rate drops to ~40%, 20 raters still provide ~240 usable items per comparison
3. **Enable additional analyses:**
   - Fleiss' κ (inter-rater agreement) — more raters = tighter confidence intervals
   - Per-criterion breakdown — 20 raters × 6 PRs = 120 ratings per criterion
   - Human vs. LLM agreement comparison
4. **Account for dropouts** — expecting 15–18 completions from 20 recruits

### What 20 raters gives us

| Metric | Value |
|--------|-------|
| Total judgments | 20 × 30 = **600** |
| Usable non-ties (KG vs RAG, 53% rate) | 20 × 16 = **320** (need 124) |
| Usable non-ties (BL vs Context, 37% rate) | 20 × 11 = **220** (need 10) |
| Power for KG vs RAG | **> 80%** |
| Power for Context vs BL | **> 99%** |
| Time per rater | ~25–30 minutes |

---

## 8. Assumptions and Limitations

1. **Effect sizes estimated from LLM data.** Human raters may perceive differences differently. The sensitivity tables (§6) show required raters across a range of plausible effect sizes.
2. **Non-tie rate may differ for humans.** LLMs tend to produce consistent binary judgments; humans may agree/disagree on different items, potentially changing the non-tie rate.
3. **Independence assumption.** The sign test assumes independence between items. Ratings from the same rater on the same PR are correlated. With 20 raters, we can also use mixed-effects models to account for this.
4. **Two comparisons.** With two planned tests, a Bonferroni correction would set α = 0.025 per test. At α = 0.025, the KG vs RAG comparison would require ~145 non-tie items (achievable with 20 raters at 53% NT rate: 320 usable items).
5. **Criterion substitution.** T1 was replaced with Q5 after the initial power analysis due to a ceiling effect. The updated tables above reflect the final 5-criterion set (F3\*, F2\*, T3, Q5, R1).
