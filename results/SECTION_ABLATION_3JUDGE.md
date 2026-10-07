# Section-deletion ablation — three-judge re-analysis

The 51 ablated reviews generated on 2026-03-05 were re-judged on 2026-05-31 with the canonical three-judge panel (`gpt-4o-mini`, `gpt-4o`, `gemini-2.5-flash`) into `results/ablation_3judge/`. Those verdicts had never been analysed. This file supersedes `results/ablation_report.md`, which used a single `gpt-4o-mini` judge and reported no significance test.

**Scope.** These reviews sit on the v1 25-PR dataset and the v1 prompt, not the v2 40-PR headline configuration. Generator, prompt, dataset and judge panel are shared across `full_kg` and the ablated arms, so the contrast is internally valid, but the magnitudes are not directly comparable to the v2 headline.

Paired sign-flip permutation and paired bootstrap, B = 200,000, seed 2026, Holm-corrected within each scale.

## Contrasts (positive drop = the deleted section was helping)

| Section deleted | Scale | n | full_kg | ablated | drop | 95% CI | d_z | p | p (Holm) |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| tests section deleted | KG-rel /9 | 16 | 5.06 | 4.81 | +0.250 | [-0.12, +0.62] | +0.29 | 0.399 | 1.000 |
| tests section deleted | total /25 | 16 | 8.50 | 8.19 | +0.312 | [-0.56, +1.25] | +0.16 | 0.615 | 0.731 |
| dependency section deleted | KG-rel /9 | 19 | 5.11 | 5.00 | +0.105 | [-0.58, +0.79] | +0.07 | 0.886 | 1.000 |
| dependency section deleted | total /25 | 19 | 8.53 | 9.21 | -0.684 | [-2.00, +0.63] | -0.23 | 0.366 | 0.731 |
| both sections deleted | KG-rel /9 | 16 | 5.06 | 4.88 | +0.188 | [-0.19, +0.50] | +0.25 | 0.531 | 1.000 |
| both sections deleted | total /25 | 16 | 8.50 | 9.19 | -0.688 | [-1.62, +0.19] | -0.35 | 0.227 | 0.682 |

## Coherence check

The March write-up was discredited by a non-monotonicity: removing both sections scored a smaller drop than removing tests alone, which is impossible if the effects are real. On the pull requests where all three arms exist:

* **KG-relevant /9** (n = 16): `kg_no_tests` +0.25, `kg_no_deps` -0.38, `kg_minimal` +0.19 — **still non-monotonic**
* **total /25** (n = 16): `kg_no_tests` +0.31, `kg_no_deps` -1.19, `kg_minimal` -0.69 — **still non-monotonic**

## Power

At n = 16-19 these contrasts detect only large effects. A drop of the full KG effect would be visible; a drop of half of it would not reliably be. Read non-significant rows as uninformative about small effects rather than as evidence of no effect.

