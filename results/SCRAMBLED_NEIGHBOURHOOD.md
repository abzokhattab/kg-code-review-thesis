# Scrambled-neighbourhood controls — results

Pre-registered in `dataset_v2/docs/PRE_REGISTRATION_scrambled.md` before any review existed. Four tests, Holm-corrected, B = 200,000, seed 2026.

Each arm replaces one rendered list in the KG block with the same number of randomly drawn files from the same repository, holding prompt volume, section set and extension mix fixed. Relatedness is the only factor that varies.

## Pre-registered tests

| Test | Contrast | Scale | n | Δ | 95% CI | d_z | p | p (Holm) | Outcome |
|---|---|---|---:|---:|---|---:|---:|---:|---|
| P1 (primary) | kg_real - scrambled_deps | KG-relevant /9 | 31 | +0.097 | [-0.32, +0.52] | +0.08 | 0.763 | 1.000 | Rule 2 (indistinguishable) |
| P2 (primary) | kg_real - scrambled_tests | KG-relevant /9 | 25 | -0.080 | [-0.56, +0.40] | -0.06 | 0.878 | 1.000 | Rule 2 (indistinguishable) |
| S1 (secondary) | kg_real - scrambled_deps | total /25 | 31 | +0.129 | [-0.61, +0.87] | +0.06 | 0.805 | 1.000 | Rule 2 (indistinguishable) |
| S2 (secondary) | kg_real - scrambled_tests | total /25 | 25 | -0.120 | [-0.92, +0.72] | -0.06 | 0.856 | 1.000 | Rule 2 (indistinguishable) |

Sign split per contrast (real better / tie / scrambled better):

* **P1** — 11 / 12 / 8
* **P2** — 7 / 10 / 8
* **S1** — 12 / 8 / 11
* **S2** — 7 / 7 / 11

## Is the null informative?

A null is only worth reporting if the design could have seen the effect. Reading the pre-registered interval against what a full collapse would have looked like on the same pull requests:

| Test | Δ if relatedness carried the whole effect | observed Δ | CI upper | full collapse |
|---|---:|---:|---:|---|
| P1 | +0.74 | +0.097 (13% of it) | +0.52 (70%) | **excluded** |
| P2 | +0.76 | -0.080 (-11% of it) | +0.40 (53%) | **excluded** |

So this is not a shrug. On the dependency arm the interval rules out relatedness carrying more than about 70% of the effect, and the point estimate puts it near a tenth. The graph's benefit survives replacing its dependency list with unrelated files drawn at random.


## Generation noise (pre-declared by-product)

The real arm was regenerated rather than reusing cached reviews, so that model drift could not be confounded with the controls. Fresh against cached on byte-identical inputs is a one-replicate estimate of single-draw generation noise at temperature 0.

| Scale | n | mean abs difference | 95% CI | mean signed | drift p | identical |
|---|---:|---:|---|---:|---:|---:|
| KG-relevant /9 | 32 | 0.88 | [0.56, 1.22] | -0.19 | 0.508 | 14/32 |
| total /25 | 32 | 1.53 | [1.16, 1.97] | -0.03 | 1.000 | 4/32 |

Two things follow. **No drift**: the signed difference between the April cache and the September regeneration is indistinguishable from zero on both scales, so the floating `gpt-4o` alias did not move under this workload, and the precaution of regenerating the real arm turned out to be unnecessary rather than wrong. **Substantial single-draw noise**: re-running the identical prompt at temperature zero changes the KG-relevant score by 0.88 points on average and leaves it unchanged in only 14 of 32 pull requests. The noise is unbiased, so paired means over 25–40 pull requests remain trustworthy, but any single per-pull-request score should be read as one draw rather than a fixed property of the arm.

This is an estimate from one replicate, not a variance component.

