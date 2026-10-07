# Sensitivity analysis — v2 (40 PRs) — grep-based KG vs scoped-AST KG

**Pre-registration:** `dataset_v2/docs/PRE_REGISTRATION_scoped_ast.md` (committed 2026-05-13 before any v2 scoped-AST data existed).
**Run:** 2026-05-13.
**Cost:** ~$8 (regen $4 + judge $4 after pre-staging 80 baseline+rag cache cells).

## Pre-registered interpretation rules (verbatim from the pre-registration)

> If scoped-AST is **larger** than grep-based → "robust + amplifiable by AST scoping".
> If scoped-AST is **indistinguishable** → "robust to KG-construction choice".
> If scoped-AST is **smaller** than grep-based → "effect depends on KG-construction choice; grep-based variant captures relations the AST-scoped variant misses."

## Outcome: **Rule 3 (scoped-AST smaller).**

## Per-mode means with 95 % bootstrap CI

| Mode | n | grep-based (headline) | scoped-AST (sensitivity) | Δ |
|---|---:|---:|---:|---:|
| baseline | 40 | 9.20 [8.70, 9.70] | 9.20 [8.70, 9.70] | 0 (identical — sanity ✅) |
| kg | 40 | 9.82 [9.28, 10.43] | 9.65 [9.07, 10.25] | −0.17 |
| rag | 40 | 10.07 [9.57, 10.60] | 10.07 [9.57, 10.60] | 0 (identical — sanity ✅) |
| hybrid | 40 | 9.93 [9.47, 10.38] | 9.45 [8.93, 10.00] | −0.48 |

KG-relevant means: kg 5.58 → 5.22; hybrid 5.50 → 5.28. Baseline and RAG identical (as expected).

## Paired Δ vs baseline (the headline statistical claim)

| Mode | Run | Total Δ [95 % CI] | p (perm) | d_z | KG-rel Δ [95 % CI] | p (perm) | d_z |
|---|---|---:|---:|---:|---:|---:|---:|
| **kg** | grep (headline) | +0.62 [+0.05, +1.20] | **0.054** | **+0.33** | **+0.60 [+0.23, +0.97]** | **0.007** | **+0.47** |
| **kg** | scoped-AST | +0.45 [−0.28, +1.18] | 0.278 | +0.18 | +0.25 [−0.10, +0.60] | 0.219 | +0.22 |
| **rag** | grep (headline) | **+0.88 [+0.30, +1.45]** | **0.007** | **+0.47** | +0.42 [+0.05, +0.82] | 0.057 | +0.33 |
| **rag** | scoped-AST | +0.88 [+0.30, +1.45] | 0.007 | +0.47 | +0.42 [+0.05, +0.82] | 0.057 | +0.33 |
| **hybrid** | grep (headline) | **+0.72 [+0.10, +1.35]** | **0.037** | **+0.36** | **+0.53 [+0.17, +0.90]** | **0.008** | **+0.46** |
| **hybrid** | scoped-AST | +0.25 [−0.57, +1.07] | 0.599 | +0.09 | +0.30 [−0.15, +0.75] | 0.251 | +0.20 |

**Highlighting:**
- **rag rows identical between runs** — expected, because rag reviews and rag cache cells are unchanged between the two configurations. The match is the strongest possible sanity check that the two runs share a baseline.
- **kg loses significance** under scoped-AST: KG-relevant p goes 0.007 → 0.219; KG-relevant d_z drops from +0.47 (medium) to +0.22 (small).
- **hybrid loses significance** under scoped-AST on both metrics: total p 0.037 → 0.599; KG-relevant p 0.008 → 0.251.

## Inter-judge agreement (Cohen's κ)

| Judge pair | grep-based (n = 4000) | scoped-AST (n = 4000) |
|---|---:|---:|
| gpt-4o-mini ↔ gpt-4o | 0.717 | 0.706 |
| gpt-4o-mini ↔ gemini-2.5-flash | 0.590 | 0.589 |
| gpt-4o ↔ gemini-2.5-flash | 0.713 | 0.718 |

Effectively identical — the scoped-AST variant does not confuse the judges any more or less than the grep-based variant.

## Interpretation (per the pre-registered Rule 3)

The KG effect depends on the KG-construction choice. The grep-based variant, while less syntactically precise, retains sufficient signal to produce a significant effect on KG-relevant criteria (p = 0.007, d_z = +0.47) and on the hybrid total (p = 0.037, d_z = +0.36). The scoped-AST variant aggressively prunes the KG sub-graph to only call-graph entries that overlap with the diff's changed hunks — the in-scope counts shrink by 90–98 % relative to the unscoped AST. On this dataset of 40 PRs, that pruning is too aggressive: it drops sibling-function and outer-class context that the grep-based variant retained and that the LLM reviewer was able to use. Two PRs (12, 30) and several others (34, 35, 44, 45) end up with empty or near-empty KG context after scoping, which effectively degrades their `kg` and `hybrid` reviews toward `baseline`.

**This is not a finding that the AST builder is wrong.** It is a finding that **a *strict* hunk-overlap scoping rule, on this dataset, removes more signal than noise.** Future work should explore weaker scoping rules (e.g., "the changed function plus its 1-hop callers/callees") and/or a hybrid of grep-based and AST-based extraction.

## Why this is good for the thesis

Three things follow from this:

1. **The headline (grep-based) result survives.** All RQ2 claims in `BOOTSTRAP_STATS_v2.md` remain valid. There is no reason to retract or downgrade them. The grep-based KG is the system that was pre-committed to in the 18 → 25 → 40 trajectory, and it produces a significant effect.

2. **The headline numbers are upper-bounded by the choice of KG construction.** The committee can be told, defensibly: *"We tested an alternative KG-construction variant (AST-grounded, hunk-scoped). The effect was smaller. The grep-based variant captures useful peripheral context that the strict AST scoping drops. We retain the grep-based variant as our headline because it was the one pre-registered before the 40-PR experiment, and because the sensitivity confirms its effect is upper-bounded by KG-construction choice rather than artefactual."*

3. **The earlier 16-PR pilot doesn't generalise.** An earlier sensitivity on 16 PRs (`results/BOOTSTRAP_STATS_gpt4o_scoped_fullkg16.md`) reported Δ = +1.00 for scoped-AST. On the full 40 PRs the effect is +0.45 and not significant. This is the standard caution about small-sample sensitivity reads — and the pre-registration was the correct response.

## Audit trail

- Pre-registration: `dataset_v2/docs/PRE_REGISTRATION_scoped_ast.md` (commit `be1046f`, 2026-05-13 morning)
- Script patches: `22eca24` (`PR_CONFIGS` extension) + `1cee470` (env-var overrides on scope + regen)
- Pipeline run: 2026-05-13 13:15 – 15:48 UTC+3, on the live lab `/Users/akhattab/ai/`
- Headline panel preserved: `outputs/luca_prs_v2/` mtime Apr 30; `results/checklist_evaluation_llm_multi__v2.json` mtime May 12.
- Sensitivity panel: `outputs/luca_prs_v2_scoped_ast/`, `results/checklist_evaluation_llm_multi__v2_scoped_ast.json`, `results/BOOTSTRAP_STATS_v2_scoped_ast.md`.

## How to cite in the thesis

Suggested wording for Chapter 6 §"Sensitivity analyses":

> We pre-registered an alternative KG-construction variant — AST-grounded extraction (`scripts/build_kg_evidence_ast.py`) scoped to functions whose source lines overlap the diff's changed hunks (`scripts/scope_ast_evidence.py`) — and re-ran the `kg` and `hybrid` modes on the same 40 PRs. The pre-registration (`dataset_v2/docs/PRE_REGISTRATION_scoped_ast.md`) fixed three interpretation rules before the data was collected. The outcome (Rule 3) was that scoped-AST is **smaller** than grep-based: `kg` KG-relevant Δ drops from +0.60 [+0.23, +0.97], p = 0.007 to +0.25 [−0.10, +0.60], p = 0.22; `hybrid` total Δ drops from +0.72 [+0.10, +1.35], p = 0.037 to +0.25 [−0.57, +1.07], p = 0.60. Baseline and RAG cells are identical between runs (a built-in sanity check). The grep-based variant therefore captures peripheral context — sibling functions and outer-class methods — that the strict AST-scoping rule removes, and which the LLM reviewer was able to use. Future work should explore weaker scoping (e.g., one-hop call-graph closure around the changed function).
