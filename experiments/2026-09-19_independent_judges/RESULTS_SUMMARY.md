# Independent judge-panel results

Date: 2026-09-19  
Status: post-hoc sensitivity analysis  
Review generation: unchanged; all reviews were frozen

## Panels

The new independent panel contains no OpenAI judge:

- `anthropic:claude-sonnet-4-5`
- `deepseek:deepseek-v4-pro`
- `xai:grok-4.6`

The original panels and judgments remain preserved. The new panel is a
provider-independence sensitivity analysis, not a pre-registered replacement.

## Experiment 1

### Mean rubric scores

| Mode | Total /25 | KG-relevant /9 |
|---|---:|---:|
| baseline | 8.00 | 4.50 |
| KG | 8.25 | 5.00 |
| RAG | 8.90 | 4.95 |
| hybrid | 8.43 | 4.90 |

### Paired effects against baseline

| Mode | Total delta [95% CI] | p | KG-relevant delta [95% CI] | p |
|---|---:|---:|---:|---:|
| KG | +0.25 [−0.25, +0.78] | 0.3961 | **+0.50 [+0.10, +0.90]** | **0.0267** |
| RAG | **+0.90 [+0.42, +1.38]** | **0.0009** | +0.45 [+0.07, +0.85] | 0.0405 |
| hybrid | +0.42 [−0.07, +0.95] | 0.1460 | +0.40 [+0.03, +0.80] | 0.0704 |

### Criterion localisation

For KG versus baseline:

- gain in the nine pre-specified KG-relevant criteria: **+0.50**;
- gain in the other sixteen criteria: **−0.25**;
- criterion-subset permutation: **p = 0.0095**.

RAG remains diffuse:

- gain in KG-relevant criteria: +0.45;
- gain in other criteria: +0.45;
- concentration test: p = 0.2411.

### Inter-judge agreement

| Judge pair | Cohen's kappa | Raw agreement |
|---|---:|---:|
| Claude ↔ DeepSeek | 0.719 | 86.6% |
| Claude ↔ Grok | 0.726 | 87.0% |
| DeepSeek ↔ Grok | 0.899 | 95.6% |

### Experiment 1 interpretation

The independent panel reproduces the targeted KG result without an OpenAI
judge. KG improves the structural subscale but not total coverage; RAG
produces the largest total-coverage gain. The mechanism-specific localisation
is stronger than the aggregate KG score.

## Experiment 2

### Why the original panel was corrected

The original prompt required each LLM judge to both find dependent filenames
and judge the causal claim. Retained rationales contained clear false
negatives—for example, a review explicitly named `_least_angle.py`, while two
judges stated that it did not.

The corrected v3 procedure:

1. deterministically resolves exact true-file path/basename mentions;
2. returns false at zero cost when no true file is named;
3. asks the LLM only whether a matched file is causally linked to the injected
   change;
4. uses validated evidence and review-passage IDs.

### Structural detection, n = 28

| Arm | Original panel | Corrected original-provider panel | Independent panel |
|---|---:|---:|---:|
| baseline | 0/28 | 0/28 | 0/28 |
| RAG | 1/28 | 7/28 | 5/28 |
| KG | 15/28 | 18/28 | **18/28** |
| hybrid | 12/28 | 21/28 | **21/28** |
| KG + inheritance | 21/28 | 26/28 | **26/28** |
| idealised KG | 26/28 | 26/28 | **26/28** |
| lexical dependencies only | 9/28 | 16/28 | 14/28 |
| Joern call edges only | 12/28 | 17/28 | 17/28 |

### Independent-panel rates and paired tests

| Arm | Rate [Wilson 95% CI] |
|---|---:|
| baseline | 0.00 [0.00, 0.12] |
| RAG | 0.18 [0.08, 0.36] |
| KG | 0.64 [0.46, 0.79] |
| hybrid | 0.75 [0.57, 0.87] |
| KG + inheritance | 0.93 [0.77, 0.98] |
| idealised KG | 0.93 [0.77, 0.98] |

| Contrast | Delta | Discordant wins/losses | Exact McNemar p |
|---|---:|---:|---:|
| KG − baseline | +0.643 | 18/0 | 0.0000076 |
| RAG − baseline | +0.179 | 5/0 | 0.0625 |
| hybrid − baseline | +0.750 | 21/0 | 0.0000010 |
| hybrid − KG | +0.107 | 4/1 | 0.375 |
| KG+inheritance − KG | +0.286 | 8/0 | 0.0078 |

### Local controls, n = 12

| Arm | Independent panel |
|---|---:|
| baseline | 11/12 |
| KG | 11/12 |
| RAG | 12/12 |
| hybrid | 10/12 |
| KG + inheritance | 12/12 |
| idealised KG | 12/12 |

The local controls remain near ceiling, while structural-context arms separate
strongly on cross-file defects.

### Experiment 2 interpretation

The corrected original-provider panel and the fully independent panel agree on
the central ordering:

```text
baseline 0 < RAG 5–7 < KG 18 < hybrid 21 < inheritance/ideal 26
```

Therefore:

- KG still provides a large cross-file detection capability.
- Hybrid is **not lower than KG** after correcting the adjudication.
- The earlier 12/28 versus 15/28 ordering was a judge-operationalisation
  artefact and does not support a context-bloating claim.
- Resolved inheritance edges close the measured gap to the idealised ceiling.
- RAG retrieves some structural evidence, but remains substantially below KG.

## Note on hybrid fusion

The evaluated hybrid is a naive concatenation: the KG block is followed by
five independently retrieved RAG snippets, without joint ranking,
de-duplication, routing, or a shared evidence budget. Modern repository
retrievers more often rank or route graph and semantic evidence before
generation.

Two zero-cost development probes tested stronger fusion policies. The
graph-constrained semantic reranker improved dependency hit-any from 25/28 to
27/28, MRR from 0.700 to 0.836, and oracle-path fraction from 53.8% to 62.3%.
However, adding code snippets reduced macro dependent recall from 52.6% to
48.9% under the same 4k budget. The result is promising but mixed and does not
license a paid generation claim.

Fusion is therefore future work: a new held-out study should freeze a jointly
ranked, de-duplicated and budgeted policy before generation. The present thesis
should not claim either that hybrid is superior to KG ($p=0.375$) or that
combined context necessarily causes dilution.

## Overall conclusion

The non-OpenAI panel strengthens the central thesis result:

1. Experiment 1 reproduces a localised KG benefit on the targeted criteria.
2. Experiment 2 reproduces a large causal cross-file detection benefit.
3. Both experiments separate graph structure from similarity retrieval.
4. The hybrid result should be interpreted as complementary—not as evidence
   that combined context necessarily causes dilution.

## Limitations

- These panels are post-hoc sensitivity analyses.
- The review generator remains `gpt-4o`; only the judges changed.
- Provider model aliases can float over time.
- Experiment 2 ground truth is static-structural, not runtime test execution.
- Original and corrected results must both remain available in the audit trail.

## Source artefacts

- `experiments/2026-09-19_independent_judges/RESULTS_EXP1.md`
- `experiments/2026-09-19_independent_judges/CRITERION_CONCENTRATION.md`
- `experiments/2026-09-19_exp2_rejudge_v2/RESULTS_V3.md`
- `experiments/2026-09-19_exp2_rejudge_v2/RESULTS_INDEPENDENT.md`
- `results/INDEPENDENT_JUDGE_PANELS.md`
