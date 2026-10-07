# Joern-KG Experiment — Results v2 (optimized prompt)

> ## ⛔ SUPERSEDED — DO NOT CITE
>
> The KG effect reported below (+1.743/6, d_z=+1.24, p<.0001, W/T/L 28/6/1) is
> an artefact of a **prompt asymmetry**: the KG arm received a prompt the
> baseline did not, so the contrast measured builder *plus* prompt. Re-running
> the same Joern builder with the prompt held at parity
> (`results/BOOTSTRAP_STATS_joern_parity.md`, n=35) yields kg +0.63 on the
> total (p=0.077) and +0.34 KG-relevant (p=0.111) — **not significant on
> either metric**.
>
> Canonical RQ2 headline: `results/BOOTSTRAP_STATS_v2.md` (era 2).
> Causal claim for structural context: `results/INJECTION_EXP2_RESULTS.md`.
> Context: `results/ERA_GUIDE.md`.


**Source:** `experiments/2026-05-15_joern_kg_main/exp_b_full35/`
**Date:** 2026-06-01

---

## Design

**Question:** Does precise call-graph context (Joern CPG) improve LLM-generated code reviews
compared to a diff-only baseline?

**Controlled variables (identical to main experiment):**
- Generator: Gemini 2.5 Flash, temp=0.0
- Judge panel: gemini-2.5-flash + gemini-2.0-flash, majority vote
- Rubric: 25-criterion, 9-criterion KG-relevant subscale
- Evidence source: Joern CPG (exact function signatures, call-graph edges)

**Scope:** 35 of 40 dataset PRs. 5 Go PRs excluded (PR9, 27, 35, 36, 37 — Joern Go
frontend produces FILE/NAMESPACE nodes only; no METHOD/CALL edges).

**Prompt:** System prompt explicitly mandates coverage of all 9 KG-relevant criteria
(test file names, caller references, architecture fit, integration risks). This is
the optimized version following ablation showing that the original prompt caused
focus displacement on 7 PRs.

---

## Headline Numbers

| Mode | Total mean (/25) | KG-rel mean (/9) |
|---|---:|---:|
| Baseline (diff only) | 9.20 | 5.00 |
| **Joern-KG** | **13.57** | **7.20** |

### Paired statistics vs baseline (n=35)

| Metric | Δ mean | 95% CI | p (perm) | Cohen's d_z |
|---|---:|---:|---:|---:|
| KG-relevant subscale | **+2.200** | **[+1.686, +2.771]** | **<0.0001** | **+1.340** |

**W/T/L vs baseline: 31W / 4T / 0L**

Effect size: d_z = 1.34 is a **large effect** (conventional threshold: 0.8).

---

## Per-Criterion Breakdown (KG-relevant subscale, mean scores)

| Criterion | Baseline | Joern-KG | Δ |
|---|---:|---:|---:|
| F3 — Integration awareness | 0.63 | 0.89 | **+0.26** |
| F4 — Broken contracts | 0.80 | 0.86 | +0.06 |
| T1 — Test existence | 0.97 | 0.94 | −0.03 |
| T2 — Edge case tests | 0.66 | 0.83 | **+0.17** |
| T3 — Specific test files | 0.66 | 0.89 | **+0.23** |
| M1 — Architecture fit | 0.17 | 0.83 | **+0.66** |
| M3 — API documentation | 0.09 | 0.60 | **+0.51** |
| C2 — Pattern consistency | 0.03 | 0.71 | **+0.68** |
| Q2 — Line references | 1.00 | 0.94 | −0.06 |

**Largest gains: C2 (+0.68), M1 (+0.66), M3 (+0.51)** — all require cross-file
knowledge that is invisible in the diff alone but present in the Joern call graph.

---

## CPG Richness Analysis (Experiment C)

Spearman correlation between n_callers and KG-relevant delta: **r=−0.043, n.s.**
Raw caller count does not predict delta. The floor effect dominates:
baseline score vs delta: **r=−0.490, p=0.003** — same pattern as RAG.

| Caller bin | n | Mean Δkg | Wins |
|---|---:|---:|---:|
| empty (0) | 9 | +2.00 | 7/9 |
| sparse (1–9) | 7 | +2.57 | 6/7 |
| moderate (10–49) | 9 | +2.22 | 8/9 |
| capped (50) | 8 | +2.00 | 8/8 |

Even PRs with zero callers (empty CPG) benefit from the structured prompt — the
gains are consistent across all CPG richness levels.

---

## Language Breakdown

| Language | PRs | Wins | Ties | Losses | Avg Δkg |
|---|---|---|---|---|---|
| TypeScript | 8 | 7 | 1 | 0 | +2.25 |
| Java | 13 | 10 | 3 | 0 | +2.15 |
| Python | 8 | 7 | 1 | 0 | +1.75 |
| C++ | 4 | 4 | 0 | 0 | +2.50 |
| Scala | 2 | 1 | 1 | 0 | +1.50 |

---

## Comparison: v1 (original prompt) vs v2 (optimized prompt)

| Version | Mean Δkg | 95% CI | p | d_z | W/T/L |
|---|---:|---:|---:|---:|---:|
| v1 (original prompt) | +0.94 | [+0.51, +1.40] | 0.007 | +0.51 | 19/9/7 |
| **v2 (optimized prompt)** | **+2.20** | **[+1.69, +2.77]** | **<0.0001** | **+1.34** | **31/4/0** |

The 7 losses in v1 were prompt artifacts (focus displacement). With a prompt that
mandates coverage of all 9 criteria, losses drop to zero.
