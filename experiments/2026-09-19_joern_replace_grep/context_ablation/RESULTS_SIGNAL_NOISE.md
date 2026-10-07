# Signal vs. Noise Ablation Results

**Date:** 2026-09-20
**Design:** Hold context quantity constant, vary relevance (inspired by GSM-DC, Yang et al. EMNLP 2025)
**Generator:** gpt-4o (T=0.0)
**Judges:** gpt-4o-mini + gpt-4o + gemini-2.5-flash (3-judge majority)
**n:** 28 structural injections

## Headline

| Arm | What the LLM sees | Detected | Rate |
|---|---|---|---|
| baseline | diff only | 0/28 | 0.0% |
| noise_matched | diff + same-count WRONG edges | 1/28 | 3.6% |
| kg_deployed | diff + Joern edges + grep deps (as built) | 15/28 | 53.6% |
| relevant_only | diff + only edges hitting true dependents | 22/28 | 78.6% |
| kg_idealised | diff + ground-truth resolver | 26/28 | 92.9% |

## Interpretation

1. **Noise ≈ baseline (1/28 vs 0/28).** Giving the LLM the same number of
   dependency edges drawn from wrong symbols produces no detection. The KG
   effect is not "having dependency info in the prompt" — it is having the
   RIGHT dependency info.

2. **relevant_only >> kg_deployed (22/28 vs 15/28).** Filtering Joern
   edges to only those pointing at true dependents raises detection from
   54% to 79%. The 7 additional detections come from removing irrelevant
   edges that dilute the signal — direct evidence of context noise.

3. **relevant_only vs kg_deployed is one-sided.** Every injection detected
   by kg_deployed is also detected by relevant_only (15/15). The 7 extras
   are injections where the signal existed in the deployed context but was
   drowned by noise.

4. **The staircase is monotonic in relevance:**
   noise (3.6%) < deployed (53.6%) < relevant (78.6%) < idealised (92.9%).
   Each step improves by filtering context, not adding it.

## Pairwise diagnostics

- noise_matched vs baseline: 27 both missed, 1 noise-only (likely a lucky
  edge that happened to name the right file)
- relevant_only vs kg_deployed: 15 both detected, 6 both missed, 7 relevant-only
- noise_matched vs kg_deployed: 13 both missed, 14 kg-only, 1 both detected

## Connection to literature

This replicates the core finding of:
- Hong et al. (2025) "Context Rot": irrelevant tokens degrade LLM output
- Yang et al. (2025) GSM-DC: matched-quantity distractors hurt reasoning
- Gupta et al. (2025) EMNLP: context length alone hurts even with perfect retrieval

Applied to code review: the KG's value is precision, not volume.
