# Experiment: KG Prompt v3 — Forced Evidence Utilization

**Date:** 2026-05-14  
**Status:** COMPLETE — Rule 1 confirmed  
**Estimated cost:** ~$8 (regen $4 + judge $4)  
**Estimated wall-clock:** ~30 min  
**Will create:** `outputs/luca_prs_v2_kg_v3/pr{1-48}_kg.md`, `results/checklist_evaluation_llm_multi__v2_kg_v3.json`  
**Will read:** `data/luca_prs_v2/pr*_evidence.json`  
**Idempotent:** yes (skips existing outputs unless `--force`)

---

## Hypothesis

The current KG prompt achieves only 11% evidence utilization (model mentions 23/203 available test files). PRs where the model actually uses evidence show KG-rel Δ = +1.25 vs +0.10 when it ignores evidence. An improved prompt that **requires** explicit structural sections (Integration Risk, Test Coverage Assessment) will increase utilization to >50% and approximately double the KG effect.

**Predicted outcome:** KG-rel Δ ≥ +0.90 full-sample (currently +0.60), with the strong-language subgroup reaching Δ ≥ +1.30.

## What Changed in the Prompt

| Aspect | v2 (current) | v3 (improved) |
|---|---|---|
| System prompt | "Use this structural context to provide deeper insights" (vague) | Mandatory output sections: "Integration Risk" + "Test Coverage Assessment" |
| Context format | Flat list: "Related Tests: file1, file2, ..." | Sectioned with explicit instructions: "⚠️ YOU MUST discuss each of these" |
| Output format | Problem / Evidence / Impact / Recommendation | Integration Risk / Test Coverage Assessment / Problem / Evidence / Impact / Recommendation |
| Enforcement | None | "CRITICAL RULES: You MUST reference specific test file paths" |

## Why This Should Work

1. **Evidence:** Correlation between utilization and effect is r ≈ 0.6 (mentions ≥1 test → Δ=+1.25; mentions 0 → Δ=+0.10)
2. **Mechanism:** The output format forces the model to allocate output tokens to structural analysis before it can discuss anything else
3. **No new data:** Same evidence packs, same PRs, same judge panel — only the generation prompt changes
4. **Conservative test:** We compare v3 against baseline using the same multi-judge evaluation, not a custom metric

## Execution

```bash
# Step 0: Source API keys
source load_env.sh

# Step 1: Generate improved KG reviews (~$4, ~15 min)
python3 scripts/regenerate_reviews_kg_v3.py

# Step 2: Run multi-judge evaluation (~$4, ~15 min)
python3 -m scripts.evaluate_reviews \
    --outputs-dir outputs/luca_prs_v2_kg_v3 \
    --output-suffix v2_kg_v3

# Step 3: Compare results
python3 scripts/compare_kg_v3_vs_v2.py
```

## Pre-registered Interpretation Rules

Before seeing results:

1. If **KG v3 KG-rel Δ > KG v2 KG-rel Δ** and **p < 0.01**: The prompt was the bottleneck. Report v3 as the improved system; v2 becomes "unoptimized prompt" in the ablation narrative.
2. If **KG v3 ≈ KG v2** (Δ within ±0.1): The prompt doesn't matter; the model already extracts what it can regardless of instructions. The 11% utilization rate is a measurement artifact (model uses context implicitly without naming files).
3. If **KG v3 < KG v2**: The forced sections distract the model from the diff, analogous to the Hybrid "Lost in the Middle" effect. Report as negative result.

## Thesis Integration

If Rule 1: The thesis gains a new experiment showing that **prompt design is a critical moderator** of KG effectiveness. The headline becomes: "With an optimized prompt, KG augmentation produces a large effect (d_z ≈ 0.7–0.9) across all language families." This partially addresses the language-moderator finding (Python/C++ may improve simply because the model is forced to use the evidence it already receives).

If Rule 2: The thesis reports the prompt experiment as a robustness check — "the effect is not sensitive to prompt wording, confirming that the KG's value lies in information access rather than prompt engineering."

If Rule 3: Report alongside the Hybrid negative result as further evidence that "more explicit context forcing is not monotonically helpful."
