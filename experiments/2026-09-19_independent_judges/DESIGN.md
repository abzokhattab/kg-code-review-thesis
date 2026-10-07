# Independent judge panels for Experiments 1 and 2

Date: 2026-09-19  
Status: post-hoc provider-independence sensitivity

## Motivation

The original three-judge panel contains two OpenAI-family models, including
the gpt-4o model that generated every review. Retained Experiment 2 rationales
also show correlated path-recognition false negatives from the two OpenAI
judges.

This sensitivity uses an odd, fully non-OpenAI panel:

1. `anthropic:claude-sonnet-4-5`
2. `deepseek:deepseek-v4-pro`
3. `xai:grok-4.6`

No review is regenerated. The generator remains truthfully reported as
`openai:gpt-4o`; only the evaluation panel changes.

## Experiment 1

- Inputs: the 160 frozen reviews under `outputs/luca_prs_v2/`
- Criteria: the existing 25-criterion rubric
- Aggregation: majority of three per criterion
- Claude: reuse all 160 completed external-judge cache entries
- New paid work: DeepSeek V4 Pro and Grok 4.6 only (160 reviews each)
- Output: `RESULTS_EXP1.{md,json}`

The same paired bootstrap/permutation analysis is applied to total /25 and
KG-relevant /9 scores.

## Experiment 2

- Inputs: the 320 frozen review/arm cells
- Arms: six headline arms plus two feature-ablation arms
- Adjudication: corrected passage-ID v3 protocol in
  `experiments/2026-09-19_exp2_rejudge_v2/DESIGN.md`
- Deterministic no-match cells require no model call
- Aggregation: majority of Claude, DeepSeek, and Grok
- Output:
  `experiments/2026-09-19_exp2_rejudge_v2/RESULTS_INDEPENDENT.{md,json}`

## Reporting rule

This panel is post-hoc and does not erase the historical panel. The thesis
must report:

- the original panel as originally executed;
- the corrected original-provider panel;
- this independent three-provider panel.

If conclusions differ, the model dependence is the finding. If they agree,
provider independence strengthens the mechanism claim.

## Verified smoke tests

- All three credentials authenticate.
- Claude passes the real Experiment 2 adjudication using Anthropic native
  JSON-schema output.
- DeepSeek V4 Pro and Grok 4.6 pass the same real adjudication.
- DeepSeek V4 Pro and Grok 4.6 each return all 25 valid Experiment 1 rubric
  scores on a frozen review.

## Pre-flight

Expected new paid work:

- Experiment 1: 320 calls (Claude's 160 are cached)
- Experiment 2: 681 calls
- Expected total cost: approximately $5.42
- Expected wall-clock: 15--30 minutes with 16 workers per stage

Every call is cached independently. Original reviews and judgments are
read-only.
