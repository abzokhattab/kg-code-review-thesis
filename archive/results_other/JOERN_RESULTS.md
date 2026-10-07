# Joern-KG Experiment — Results

**Source:** `experiments/2026-05-15_joern_kg_main/controlled/` (reviews + evals)
**Verified:** 2026-05-31

---

## Design

**Question:** Does precise call-graph context (Joern CPG) improve LLM-generated code reviews
compared to a diff-only baseline?

**Controlled variables** (identical to main experiment):
- Generator: Gemini 2.5 Flash, temp=0.0
- System prompt: `SYSTEM_PROMPT_KG` from `prnote/note.py` — same as main experiment KG mode
- Judge panel: gpt-4o-mini + gpt-4o + gemini-2.5-flash, majority vote
- Rubric: 25-criterion, 9-criterion KG-relevant subscale

**What changed vs main experiment KG mode:**
- Evidence source: Joern CPG (exact function signatures, call-graph edges) instead of grep heuristics

**Scope:** 35 of 40 dataset PRs. 5 Go PRs excluded (PR9, 27, 35, 36, 37 — all Grafana):
Joern's Go frontend produces FILE/NAMESPACE nodes only; no METHOD nodes or CALL edges.

---

## Headline Numbers

| Mode | Total mean (/25) | KG-rel mean (/9) |
|---|---:|---:|
| Baseline (diff only) | 8.94 | 5.00 |
| **Joern-KG (controlled)** | **11.89** | **5.94** |

### Paired Wilcoxon vs baseline (n=35)

| Metric | Δ | 95% direction | p | d_z |
|---|---:|---|---:|---:|
| Total score | **+2.94** | positive | **<0.000001** | **+1.39** |
| KG-relevant subscale | **+0.94** | positive | **0.007** | **+0.51** |

Effect size interpretation: d_z > 0.8 = large, > 0.5 = medium.

Win/Tie/Loss vs baseline: **31W / 2T / 2L** (total), **19W / 9T / 7L** (KG-rel).

---

## Per-Criterion Breakdown (KG-relevant subscale)

| Criterion | Baseline | Joern-KG | Δ | Interpretation |
|---|---:|---:|---:|---|
| F3 — Integration awareness | 0.63 | 0.89 | **+0.26** | Joern callers reveal integration risks |
| F4 — Broken contracts | 0.80 | 0.77 | −0.03 | Negligible |
| T1 — Test existence | 0.97 | 0.71 | −0.26 | Baseline already saturated; Joern reviews focus elsewhere |
| T2 — Edge case tests | 0.66 | 0.63 | −0.03 | Negligible |
| T3 — Specific test files | 0.66 | 0.83 | **+0.17** | Joern locates exact test files |
| M1 — Architecture fit | 0.17 | 0.71 | **+0.54** | Largest gain; call graph shows structural role |
| M3 — API documentation | 0.09 | 0.06 | −0.03 | Negligible |
| C2 — Pattern consistency | 0.03 | 0.34 | **+0.31** | Callers reveal how similar patterns are used elsewhere |
| Q2 — Line references | 1.00 | 1.00 | 0.00 | Both at ceiling |

**Criteria where Joern adds value:** M1, C2, F3, T3 — all require understanding cross-file relationships
that are invisible in the diff alone.

**Criteria where Joern shows no gain:** T1, F4, M3 — these do not require call-graph knowledge.
T1 regression is a ceiling effect (baseline already at 0.97).

---

## Progressive Ablation (n=35) — ⛔ SUPERSEDED, DO NOT CITE

> **Corrected 2026-09-06.** The table below compares the Joern ablation arms
> against a baseline drawn from a *different pipeline*:
> `checklist_evaluation_llm_multi__v2.json`, generated with the v2 prompt on the
> same 35 pull requests. That baseline scores 5.00.
>
> The ablation has its own control. `joern_minimal` is the identical Joern
> pipeline with **neither tests nor callers**, and it scores **6.20**. So 1.20
> of the reported "+1.63 from tests" is the pipeline — prompt and generator —
> and was present before a single test file was added.
>
> Recomputed against the ablation's own control, same 35 pull requests, same
> canonical three judges:
>
> | Contrast | Δ (KG-relevant /9) | d_z | p |
> |---|---:|---:|---:|
> | tests only vs neither | +0.43 | +0.22 | 0.24 |
> | callers only vs neither | +0.09 | +0.05 | 0.84 |
> | tests vs callers, head to head | +0.34 | +0.19 | 0.32 |
>
> None significant. **"Test-awareness is the primary driver (d_z = +1.04)" does
> not hold.** This is the same cross-pipeline error that forced the Joern
> headline retraction documented in `results/ERA_GUIDE.md`, where +1.743 became
> +0.63 and non-significant once the prompt was matched; the parity re-run fixed
> the main arm and never revisited this section.
>
> The question is answered properly, on ground-truthed binary oracles, in
> `results/EXP2_FEATURE_ABLATION.md` (dependency signal) and
> `results/TEST_ORACLE.md` (test signal). Both were pre-registered and both find
> real effects — the test signal is decisive, 0/28 without a test list against
> 24/28 with the deployed one. Tests do matter; this table is not the evidence.

Which component of the Joern evidence drives the KG-relevant gain?

All three levels below use the same Joern custom prompt
(`experiments/2026-05-15_joern_kg_main/ablation/`), so they are internally
consistent with each other. They are **not** directly comparable to the
controlled experiment above (which uses `SYSTEM_PROMPT_KG`); they answer a
separate question: given the Joern prompt, which context features matter?

| Level | Context added | KG-rel mean (/9) | Δ vs baseline | p | d_z |
|---|---|---:|---:|---:|---:|
| L0 — Baseline | diff only | 5.00 | — | — | — |
| L1 — +Tests | nearest tests + test files | 6.63 | **+1.63** | **<0.0001** | **+1.04** |
| L2 — +Callers | call graph + function signatures | 6.29 | **+1.29** | **0.0004** | **+0.75** |
| L3 — Full Joern | tests + callers | 6.66 | **+1.66** | **<0.0001** | **+1.09** |

L3 vs L1 (marginal gain of adding callers on top of tests): Δ=+0.03, p=0.69, n.s.

**Interpretation:** Test-awareness is the primary driver (d_z=+1.04 alone).
Caller information is independently significant (d_z=+0.75 alone) but the two
features are largely redundant when combined — L3 does not improve meaningfully
over L1 (p=0.69). The call graph's main contribution is naming exact callers and
function signatures, which raises M1 and C2 scores; the test-location data raises
T3 and F3.

---

## Excluded Comparisons

The following comparisons are **not reported** because they are confounded or misleading:

- **Joern vs grep-KG:** The main experiment KG mode uses grep heuristics as its
  implementation detail. That is not a thesis contribution. The relevant comparison is
  Joern vs baseline (does precise context help?).

- **Custom-prompt Joern as a headline result:** The custom prompt used "CRITICAL RULES:
  You MUST name exact test files" — a stronger instruction than `SYSTEM_PROMPT_KG`.
  Reporting its KG-rel gain (+1.66) as the main finding would conflate prompt strength
  with context quality. It is used only inside the ablation section, where all three
  levels share the same prompt and the comparison is internally valid.

---

## Limitations

1. **Go exclusion (5/40 PRs):** All Grafana Go PRs excluded. Joern finding covers
   Java, Python, TypeScript, C++, Scala only.
2. **Ablation uses a different prompt than the controlled experiment:** The ablation
   (L1/L2/L3) used a stricter Joern-specific prompt; the controlled comparison uses
   `SYSTEM_PROMPT_KG`. The two sections answer different questions and must not be
   mixed in the same table.
3. **Generator:** Gemini 2.5 Flash used for Joern reviews; main experiment used gpt-4o.
   Cross-model comparisons should be interpreted with caution.
