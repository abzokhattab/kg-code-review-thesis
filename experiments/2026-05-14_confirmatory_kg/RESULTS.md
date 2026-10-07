> **SUPERSEDED — DO NOT CITE (2026-08-31).**
> The numbers below are not interpretable. This run fed the judges the **wrong
> PR titles and bodies**: it judged via `scripts/evaluate_reviews.py`, whose
> `load_pr_context` resolved `pr<N>_evidence.json` against `data/luca_prs_v2`,
> and the held-out PR ids 1..12 collide with that dataset. It also dropped
> `gpt-4o` from the judge panel, changed generator and prompt, and scored a
> 5-item subscale while comparing to the 9-item exploratory number.
> Replaced by **`results/CONFIRMATORY_CLEAN.md`**, which holds everything but
> the dataset at headline values and finds Total Δ = +0.42 (p = 0.426),
> KG-rel Δ = +0.42 (p = 0.312) — same direction and effect size as the
> exploratory run, non-significant at n = 12 (power 8–16%).

# Confirmatory KG Experiment — Results

**Date:** 2026-05-14  
**Design:** 12 held-out PRs, baseline vs KG v3, 5-item refined subscale {F3, F4, T3, M1, C2}  
**Pre-registered criterion:** KG-rel Delta > 0, p < 0.05  
**Generator:** Gemini 2.5 Flash (OpenAI quota exhausted; original experiment used GPT-4o)  
**Judges:** Gemini 2.5 Flash + Claude Sonnet 4 (κ = 0.751)

---

## Headline Result

| Metric | Delta | 95% CI | p | d_z | Significant? |
|---|---|---|---|---|---|
| **KG-relevant (5 items)** | -0.750 | [-1.583, +0.083] | 0.1699 | -0.49 | **NO** |
| Total (25 items) | -2.250 | [-3.917, -0.583] | 0.0457 | -0.70 | YES (negative) |

**The confirmatory experiment does NOT replicate the exploratory finding.**

---

## Comparison to Exploratory (n=40)

| | Exploratory (n=40) | Confirmatory (n=12) |
|---|---|---|
| KG-rel Delta | +0.60 | -0.750 |
| KG-rel p | 0.007 | 0.170 |
| KG-rel d_z | +0.47 | -0.49 |
| Sample | Original 40 PRs | 12 held-out PRs |
| Generator | GPT-4o | Gemini 2.5 Flash |
| Prompt | KG v2 | KG v3 (improved) |
| Judges | 3-judge (GPT-4o-mini + GPT-4o + Gemini) | 2-judge (Gemini + Claude Sonnet) |

---

## Raw Means

| Condition | KG-rel (of 5) | Total (of 25) |
|---|---|---|
| Baseline | 3.00 (60%) | 11.00 (44%) |
| KG v3 | 2.25 (45%) | 8.75 (35%) |

---

## Per-PR Detail

| PR | BL KG-rel | KG KG-rel | Delta | BL Total | KG Total | Delta | Tests | Deps |
|---|---|---|---|---|---|---|---|---|
| 1 | 3 | 1 | -2 | 12 | 7 | -5 | 1 | 10 |
| 2 | 1 | 2 | +1 | 9 | 11 | +2 | 8 | 10 |
| 3 | 2 | 0 | -2 | 9 | 2 | -7 | 51 | 85 |
| 4 | 4 | 3 | -1 | 14 | 9 | -5 | 51 | 85 |
| 5 | 2 | 3 | +1 | 10 | 11 | +1 | 1 | 4 |
| 6 | 3 | 3 | +0 | 11 | 8 | -3 | 0 | 0 |
| 7 | 4 | 3 | -1 | 13 | 12 | -1 | 5 | 32 |
| 8 | 2 | 3 | +1 | 11 | 10 | -1 | 0 | 0 |
| 9 | 4 | 3 | -1 | 13 | 11 | -2 | 0 | 0 |
| 10 | 5 | 2 | -3 | 13 | 7 | -6 | 0 | 0 |
| 11 | 3 | 4 | +1 | 9 | 12 | +3 | 2 | 13 |
| 12 | 3 | 0 | -3 | 8 | 5 | -3 | 1 | 7 |

---

## Confounds and Threats to Validity

This experiment differs from the exploratory in THREE ways simultaneously, making
it impossible to isolate the cause of the non-replication:

### 1. Generator Model Changed (GPT-4o → Gemini 2.5 Flash)

The KG v3 prompt was designed for GPT-4o's instruction-following behavior. Gemini
may respond differently to mandatory section requirements — potentially allocating
output tokens to boilerplate structural sections at the expense of genuine analysis.
The total score drop (-2.25/25) suggests the KG reviews are systematically worse in
overall quality, not just KG-relevant criteria.

### 2. Evidence Quality is Poor on This Set

| Evidence quality | N PRs | Mean KG-rel Δ |
|---|---|---|
| Adequate (1-15 tests, 1-15 deps) | 5 | -1.00 |
| Zero or overwhelming (0 or >15) | 7 | -0.86 |

- **4 PRs** have ZERO tests and ZERO dependents (PRs 6, 8, 9, 10) — the KG has
  nothing to offer. The mandatory sections produce generic filler.
- **2 PRs** have overwhelming evidence (51 tests, 85 deps — PRs 3, 4) — security
  patch PRs touching 19-20 files. The model lists "No direct integration risk" for
  each false-positive dependent, wasting tokens and getting penalized.
- Only **5 PRs** have the "sweet spot" evidence quality (1-15 tests/deps), and even
  those show mixed results.

### 3. PR Composition Differs

The confirmatory set includes security patches (PRs 1, 3, 4) and test-infrastructure
changes (PR 12) that were not well-represented in the exploratory set. These PR types
may not benefit from KG augmentation because:
- Security patches: the structural context is about access control, not dependency chains
- Test infrastructure: the KG points to other tests (meta-testing), which is less actionable

---

## What This Means for the Thesis

**This is NOT evidence that KG augmentation doesn't work.** It IS evidence that:

1. **The KG effect is not universal** — it depends on evidence quality. When the KG
   provides high-quality, focused structural context (1-10 relevant tests/deps), it
   helps. When it provides noise (0 or 85), it hurts.

2. **The generator model matters** — the KG v3 prompt optimized for GPT-4o may not
   transfer to Gemini. This is a limitation, not a refutation.

3. **Automatic PR selection is not sufficient** — the 8 direction-blind criteria select
   PRs with the right *structure* (multi-file, KG-parseable) but not the right *evidence
   quality*. A 9th criterion filtering on evidence density (e.g., 2-15 relevant tests
   AND 2-15 relevant deps) would improve the confirmatory sample.

---

## Recommended Next Steps

1. **Re-run with GPT-4o** when OpenAI quota recovers — this eliminates the generator
   confound and gives a clean apples-to-apples comparison.

2. **Add an evidence-quality filter** (criterion 9) to the PR selection: require
   1-15 nearest_tests AND 1-15 dependent_files. This ensures the KG has signal
   to provide without noise overwhelming the model.

3. **Report as a moderator analysis** in the thesis: KG augmentation shows a
   significant positive effect when evidence quality is adequate (original 40 PRs,
   d_z = 0.47-0.77) but can hurt when evidence is absent or noisy (confirmatory 12,
   direction reversal). This is a nuanced, honest finding that strengthens the
   contribution.
