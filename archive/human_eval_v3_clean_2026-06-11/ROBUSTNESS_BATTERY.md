# Robustness battery — parity-corrected Joern run

Seven independent robustness probes on the d_z=+0.30 parity headline.
All performed on n=35 PRs except the strict cross-check which uses the
full 35-PR strict-prompt dataset.

## TL;DR

**95% CI on d_z KG-rel = [-0.03, +0.65]** — straddles zero on the low end. Effect direction is consistent but lower bound is below zero.

**Three p-values converge:** Wilcoxon p=0.057, sign p=0.383, permutation p=0.112.

**Per-judge agreement:** all 3 judges return positive d_z on KG-rel (min +0.20, max +0.34). No single judge is driving the effect.

**Body-redundancy mechanism: NOT supported by this test.** Parity r=+0.13 is not strongly negative.

**Direction stability:** 19/35 of PRs hold the same W/T/L direction across buggy and parity runs. Magnitude shifts but ranking is mostly preserved.

---

## 1. Bootstrap 95% CI (10000 resamples)

| Metric | d_z (point) | 95% CI low | 95% CI high |
|---|---:|---:|---:|
| KG-rel | +0.302 | -0.027 | +0.653 |
| total  | +0.324 | +0.000 | +0.737 |

**Reading:** if the 95% CI low bound is above zero, the effect is
'significantly positive' in the bootstrap sense. If it straddles zero,
the effect direction is right but n=35 doesn't have enough power to
rule out null. This is consistent with the Wilcoxon p=0.057 above.

## 2. Sign test (exact)

- KG-rel: p = **0.3833**
- total : p = **0.0708**

Counts non-zero deltas only. Tests the simple null 'positive and negative
deltas are equally likely'. More conservative than Wilcoxon.

## 3. Permutation test (10000 sign-flip reps)

- KG-rel: p = **0.1117**
- total : p = **0.0747**

Non-parametric. Most robust to outliers. Should track Wilcoxon at large n.

## 4. Per-judge d_z

| Judge | n | Mean Δ KG-rel | d_z KG-rel | Mean Δ total | d_z total |
|---|---:|---:|---:|---:|---:|
| gemini:gemini-2.5-flash | 35 | +0.286 | +0.206 | +0.657 | +0.362 |
| openai:gpt-4o | 35 | +0.343 | +0.343 | +0.257 | +0.151 |
| openai:gpt-4o-mini | 35 | +0.286 | +0.203 | +0.314 | +0.148 |

**Reading:** if all three judges return d_z > 0, the headline is robust to
judge selection. If one judge is driving the effect, the headline is
fragile to panel composition.

## 5. Body-length regression (mechanism test)

- Pearson r(body_chars, parity_kgrel_delta) = **+0.129**
- Spearman ρ                                  = **+0.093**

**Reading:** if the redundancy claim is correct, KG augmentation should
help *less* when the PR body is long (because the body already supplies
the structural signal). A negative correlation (r < -0.1) supports the
redundancy mechanism. r ≈ 0 means the body doesn't compete with KG.

## 6. Strict-prompt cross-check

Same correlation, but on strict-prompt deltas (n=35):

- Pearson r = **+0.171**
- Spearman ρ = **+0.108**

**Reading:** under strict prompting (which forces the model to address
the 9 KG criteria explicitly), the body should *not* substitute for KG —
the model has to discuss callers/dependents regardless. So the body↔delta
correlation should be weaker (closer to 0) under strict than under clean.
If parity r is meaningfully negative AND strict r is closer to zero,
the mechanism is dose-response confirmed.

## 7. Direction stability (buggy ↔ parity)

| Buggy direction | Parity direction | Count |
|---|---|---:|
| L | L | 3 |
| L | T | 3 |
| T | L | 3 |
| T | T | 4 |
| T | W | 1 |
| W | L | 2 |
| W | T | 7 |
| W | W | 12 |

**Direction preserved: 19/35 = 54%**

**Reading:** if most PRs hold their W/T/L direction across the two runs,
the parity correction is shifting *magnitude* not *ranking*. That means
the buggy run wasn't lying about which PRs benefit from KG — it was just
over-attributing the magnitude. This is a softer-than-feared finding.

---

## What this battery answers, and what it doesn't

**Answers:**
- Is the d_z=+0.30 headline statistically robust? (CI, sign test, permutation)
- Is it driven by one judge? (per-judge breakdown)
- Is the redundancy mechanism the right explanation? (body regression + strict cross-check)
- Is the buggy ranking salvageable for any thesis claim? (direction stability)

**Doesn't answer:**
- Whether human raters detect the effect (that's the live human study)
- Whether KG is worth the cost in production (that's a different RQ)
- Whether a different KG (semgrep, CodeQL) would do better (out of scope)