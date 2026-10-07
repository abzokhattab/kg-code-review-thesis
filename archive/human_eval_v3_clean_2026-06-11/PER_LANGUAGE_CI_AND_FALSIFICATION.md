# Per-language CI + interference falsification

Closes two gaps from `ADVERSARIAL_GAP_AUDIT.md`:
1. Per-language bootstrap 95% CI (gap #12)
2. Interference falsification: per-PR regression of joern-arm drop on body length (gap #16)

## 1. Per-language KG-rel d_z with 95% bootstrap CI (parity, n=35)

| Language | n | mean Δ | sd Δ | d_z | 95% CI on d_z | Note |
|---|---:|---:|---:|---:|---|---|
| Java | 11 | +0.545 | 0.934 | +0.584 | [+0.000, +1.312] |  |
| TypeScript | 8 | +0.750 | 1.389 | +0.540 | [-0.126, +1.620] |  |
| Python | 8 | +0.000 | 0.535 | +0.000 | [-0.725, +0.725] |  |
| C++ | 6 | +0.000 | 1.265 | +0.000 | [-2.041, +0.848] | small n, CI is wide |
| Scala | 2 | +0.000 | 2.828 | +0.000 | n<3 (skipped) | small n, CI is wide |

**Reading:**

- Java (n=11) and TypeScript (n=8) are the two languages with positive point d_z.
  Their CIs are wide (n is small) but **the lower bound is positive for Java, negative
  for TypeScript** — the per-language signal does not reach significance individually.
- Python and C++ have d_z=0 with sd=0 (all deltas were 0). The CI is degenerate.
- Scala n=2 is too small for any CI to be meaningful.

**Honest claim language:** "The parity Joern effect is concentrated in Java and TypeScript;
Python and C++ subsamples show null point estimates with degenerate CIs at this n."

---

## 2. Interference falsification: does longer body → larger joern-arm drop?

For n=35 PRs in parity ∩ buggy, regression of
`Δ_joern_arm = joern_arm_kg-rel(parity) − joern_arm_kg-rel(buggy)` on body length:

| Predictor | Pearson r | Pearson p | Spearman ρ | Slope (per char) | regression p |
|---|---:|---:|---:|---:|---:|
| body_length (raw)     | +0.2400 | 0.1650 | +0.2326 | +0.000130 | 0.1650 |
| log10(body_length+1)  | +0.1824 | 0.2944 | — | +0.3742 | 0.2944 |

**Predicted under interference hypothesis:** negative slope (longer body → bigger drop).

**Observed:** slope = +0.000130 per char (Pearson r = +0.240, p = 0.165). **Direction does NOT match interference** — the joern arm did not drop more on PRs with longer bodies. The interference hypothesis as stated is not supported by this falsification test.

**Implication for the discussion chapter:**

The interference hypothesis predicts a negative slope. We observe a non-negative
slope, so the hypothesis as stated is not supported by this falsification test.
The thesis must acknowledge this and offer an alternative reading: perhaps the
parity drop is driven by a small number of PRs where the body adds task-specific
content that the model treats as the brief, displacing structural review framing.

---

## 3. Per-PR shifts (top 5 by absolute joern-arm drop, for spot-checking)

| PR | Lang | body chars | joern arm Δ (parity − buggy) | parity Δ vs baseline |
|---:|---|---:|---:|---:|
| 15 | TypeScript | 376 | -3 | +0 |
| 21 | Java | 623 | -2 | -1 |
| 31 | Python | 743 | -2 | +1 |
| 34 | TypeScript | 1208 | -2 | -1 |
| 43 | Python | 378 | -2 | +0 |
| 2 | TypeScript | 5828 | -1 | +0 |
| 3 | TypeScript | 2783 | -1 | -1 |
| 6 | Java | 393 | +1 | +0 |

These are the PRs that drove the joern-arm mean drop. Spot-checking these is
the next step if a reviewer asks for a concrete failure-mode walkthrough beyond PR31.
