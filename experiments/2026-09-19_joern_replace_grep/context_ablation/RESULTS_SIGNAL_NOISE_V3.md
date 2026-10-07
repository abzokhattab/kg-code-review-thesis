# Signal vs. Noise Ablation Results (v3 corrected adjudication)

**Date:** 2026-09-20
**Adjudication:** corrected v3 (deterministic filename match + LLM causal assessment)
**Generator:** gpt-4o (T=0.0)
**Judges:** gpt-4o-mini + gpt-4o + gemini-2.5-flash (3-judge majority)
**n:** 28 structural injections

## Results

| Arm | What the LLM sees | Detected | Rate |
|---|---|---|---|
| baseline | diff only | 0/28 | 0.0% |
| noise_matched | diff + same-count WRONG edges | 1/28 | 3.6% |
| kg_deployed | diff + Joern edges + grep deps (as built) | 18/28 | 64.3% |
| relevant_only | diff + only edges hitting true dependents | 25/28 | 89.3% |
| kg_idealised | diff + ground-truth resolver | 26/28 | 92.9% |

## Comparison with original adjudication

| Arm | Original | Corrected v3 |
|---|---|---|
| baseline | 0/28 | 0/28 |
| noise_matched | 1/28 | 1/28 |
| kg_deployed | 15/28 | 18/28 |
| relevant_only | 22/28 | 25/28 |
| kg_idealised | 26/28 | 26/28 |
