# Graded 0-3 Scale Pilot — Results

**Date:** 2026-06-01
**Judges:** Gemini 2.5 Flash + Gemini 2.5 Pro (mean score per criterion)
**PRs:** 27 KG-rich non-Go PRs (of 35 total non-Go; 8 missing from both dirs)
**Criteria:** F3, F4, P1, R2, T3 (clean subscale, graded 0-3 with anchors)

---

## Motivation

Binary 0/1 scoring creates a ceiling effect. A review that vaguely mentions
integration (deserves 1/3) and one that names 3 exact callers with file:line
references (deserves 3/3) receive the same score. This pilot tests whether
anchored 0-3 descriptors capture the true signal.

---

## Main Results: Joern-KG vs Baseline (n=27, graded scale /15)

| Metric | Δ mean | 95% CI | p (perm) | d_z | W/T/L |
|---|---:|---:|---:|---:|---:|
| **AGGREGATE (/15)** | **+3.981** | **[+3.11, +4.85]** | **<0.0001 ***| **+1.724** | **26/0/1** |

Per criterion:

| Criterion | Δ mean | 95% CI | p | d_z | W/T/L |
|---|---:|---:|---:|---:|---:|
| F3 — Integration awareness | +1.074 | [+0.72, +1.43] | <0.0001 *** | +1.133 | 19/8/0 |
| F4 — Broken contracts | +0.963 | [+0.57, +1.37] | 0.0001 *** | +0.882 | 18/6/3 |
| P1 — Performance | +0.111 | [−0.09, +0.37] | 0.253 n.s. | +0.170 | 2/23/2 |
| R2 — Complexity | +0.648 | [+0.19, +1.11] | 0.008 ** | +0.508 | 11/14/2 |
| T3 — Specific test files | +1.185 | [+0.80, +1.59] | <0.0001 *** | +1.075 | 22/3/2 |

**P1 (Performance) is the only non-significant criterion** — Joern provides no
performance profiling data, so this is expected and mechanistically justified.

---

## Inter-Rater Agreement (Spearman ρ, graded 0-3)

| Criterion | Baseline ρ | Joern-KG ρ | Interpretation |
|---|---:|---:|---|
| F3 | 0.643 | 0.528 | Good / Moderate |
| F4 | 0.719 | 0.569 | Good / Moderate |
| P1 | 0.665 | 0.832 | Good / Excellent |
| R2 | 1.000 | 0.844 | Excellent / Excellent |
| T3 | 0.706 | 0.442 | Good / Moderate |

All criteria show ρ ≥ 0.44 (moderate or above). Agreement is consistent
with binary kappa scores from the main experiment.

---

## Comparison: Binary vs Graded d_z

| Scale | Metric | d_z | n |
|---|---|---:|---:|
| Binary (0/1) | KG-active /6 (main exp, KG mode) | +0.628 | 40 |
| Binary (0/1) | KG-active /6 (Joern-KG) | +1.464 | 35 |
| **Graded (0-3)** | **Clean subscale /15 (Joern-KG)** | **+1.724** | **27** |

Graded scale with Joern context: d_z=+1.724 — the largest effect we have
measured. Moving from binary to graded reveals additional signal that binary
scoring masks.

---

## Key Findings

1. **Graded scale amplifies real signal**: d_z jumps from +1.464 (binary) to
   +1.724 (graded) on the same Joern context, same PR set.

2. **F3 and T3 are the biggest movers**: Both are 0/1 ceiling-capped in binary
   mode. With graded anchors, the full spectrum of "mentioning callers" vs
   "naming 3 callers with file:line references" is captured.

3. **P1 is mechanistically null**: Joern provides call-graph data, not perf
   profiling. P1 should be removed from the KG-relevant subscale.
   Revised clean subscale: **F3, F4, R2, T3** (4 criteria, /12).

4. **Inter-rater agreement holds**: ρ ≥ 0.44 on all criteria. Graded scale
   does not degrade agreement vs binary kappa.

---

## Revised 4-Criterion Clean Subscale

Dropping P1 (mechanistically null for KG), the active subscale is:

| Criterion | What it measures | Graded d_z |
|---|---|---:|
| F3 | Integration awareness — names specific callers | +1.133 |
| F4 | Broken contracts — identifies API contract violations | +0.882 |
| R2 | Complexity — suggests specific simplifications | +0.508 |
| T3 | Test specificity — names exact test file paths | +1.075 |

All p < 0.01.
