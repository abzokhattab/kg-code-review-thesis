# Priming placebo, v2 parity run — is it the instruction or the facts?
**Arms:** `baseline`, `kgempty` (KG system prompt, empty context), `kg`  **PRs:** 40  **Generator:** openai:gpt-4o @ T=0.0  **Judges:** headline 3-judge panel  **Script:** `scripts/run_priming_placebo_v2.py`  **Method:** paired sign-flip test, B=10,000, seed=2026; bootstrap percentile CIs.
The placebo arm is generated through `regenerate_reviews_v2.generate_one` with the KG system prompt and a context builder that returns `""`, so it differs from the `kg` arm in exactly one respect: the facts.
## Arm means
| Arm | total /25 | KG-relevant /9 | mean review chars |
|---|---:|---:|---:|
| baseline | 9.20 | 4.97 | 1774 |
| kgempty | 9.97 | 5.45 | 1889 |
| kg | 9.82 | 5.58 | 1991 |

## Decomposition
| Contrast | What it isolates | Metric | Δ | 95% CI | p |
|---|---|---|---:|---|---:|
| baseline → kgempty | instruction only (priming) | total | +0.78 | [+0.15, +1.38] | 0.024 |
| baseline → kgempty | instruction only (priming) | kgrel | +0.47 | [+0.12, +0.82] | 0.018 |
| kgempty → kg | facts only (content) | total | -0.15 | [-0.78, +0.45] | 0.697 |
| kgempty → kg | facts only (content) | kgrel | +0.12 | [-0.28, +0.57] | 0.651 |
| baseline → kg | headline effect (priming + content) | total | +0.62 | [+0.05, +1.20] | 0.056 |
| baseline → kg | headline effect (priming + content) | kgrel | +0.60 | [+0.20, +0.97] | 0.007 |

## Reading

On the KG-relevant subscale the instruction accounts for +0.47 of the +0.60 headline difference (79%), leaving +0.12 (p = 0.651) attributable to the graph facts themselves.

The decisive quantity is the `kgempty → kg` row: it is the only contrast in Experiment 1 that isolates the structural content from everything else in the prompt. If it is near zero the KG lift is a prompt-engineering result, not a knowledge-graph result, and the thesis must say so. Experiment 2 is unaffected either way — a prompt with no facts cannot name a dependent file it was never given.

Supersedes `results/KG_EMPTY_PRIMING_CONTROL.md` (5 PRs, T=0.3, pre-v2 evidence, hand-rolled prompt).

## The placebo against every other arm

The decomposition above concerns `kg` only. Extending the same paired test to the
other two context arms, on the 40 PRs common to all five, asks a blunter question:
does *any* form of retrieved context beat an instruction to imagine it?

| Arm | total /25 | KG-relevant /9 | mean review chars |
|---|---:|---:|---:|
| baseline | 9.20 | 4.97 | 1774 |
| **kgempty** (no retrieved content) | **9.97** | **5.45** | 1889 |
| kg | 9.82 | 5.58 | 1991 |
| rag | 10.07 | 5.40 | — |
| hybrid | 9.93 | 5.50 | — |

| Contrast | Metric | Δ | p |
|---|---|---:|---:|
| kgempty → kg | total | −0.15 | 0.700 |
| kgempty → kg | kgrel | +0.12 | 0.654 |
| kgempty → rag | total | +0.10 | 0.766 |
| kgempty → rag | kgrel | −0.05 | 0.888 |
| kgempty → hybrid | total | −0.05 | 0.933 |
| kgempty → hybrid | kgrel | +0.05 | 0.879 |

No context arm is distinguishable from the placebo on either metric. The placebo
outscores `kg` on the total. Every mode-vs-baseline effect Experiment 1 reports is
therefore reproduced by a prompt containing no repository information whatsoever.

Review length does not explain this: `kgempty` scores above `kg` on the total while
being ~100 characters shorter.

## Consequence for the criterion-localisation result

`results/CRITERION_CONCENTRATION.md` reports that `kg` concentrates 96% of its gain
in the 9 KG-relevant criteria (p = 0.016) and reads this as evidence that the graph
does the specific thing it was designed to do. That inference does not survive the
placebo, because the KG *system prompt* names those same categories explicitly.

Re-running the same test with `kgempty` as the reference instead of `baseline`:

| Reference | Contrast | Gain in the 9 | Share | p |
|---|---|---:|---:|---:|
| baseline | kg | +0.600 of +0.625 | 96% | 0.016 |
| baseline | kgempty | +0.475 of +0.775 | 61% | 0.141 |
| **kgempty** | **kg** | **+0.125 of −0.150** | **—** | **0.174** |

Against the placebo the graph's residual contribution is +0.125 rubric points on the
/9 subscale, not significant. The localisation finding measures where the
*instruction* points the model, not where the *facts* land. It should be cited only
with the placebo reference alongside it.

One nuance worth keeping: `kg` localises more sharply (96%, p = 0.016) than
`kgempty` (61%, p = 0.141), which is the pattern a real but small content effect
would produce. The direct test is underpowered rather than clearly null, so the
honest statement is "not established", not "shown to be zero".

## What this does and does not overturn

Unaffected: Experiment 2. Its detection task has ground truth, and a prompt with no
facts cannot name a dependent file it was never given — 0/28 for `baseline` against
15/28 for the graph arm cannot be priming.

Unaffected: the hallucinated-review control (`results/RUBRIC_PROVENANCE.md`), where
a review citing fabricated files and line numbers scored 9.2 against 9.0 for real
reviews. That control and this placebo are the same finding reached from two
directions: the coverage rubric scores the *shape* of a review, not whether its
claims are true or grounded.

Overturned: any reading of Experiment 1 in which the knowledge graph, rather than
the prompt that accompanies it, produces the measured advantage.
