## Generation noise (pre-declared by-product)

The real arm was regenerated rather than reusing cached reviews, so that model drift could not be confounded with the controls. Fresh against cached on byte-identical inputs is a one-replicate estimate of single-draw generation noise at temperature 0.

| Scale | n | mean abs difference | 95% CI | mean signed | drift p | identical |
|---|---:|---:|---|---:|---:|---:|
| KG-relevant /9 | 32 | 0.88 | [0.56, 1.22] | -0.19 | 0.508 | 14/32 |
| total /25 | 32 | 1.53 | [1.16, 1.97] | -0.03 | 1.000 | 4/32 |

Two things follow. **No drift**: the signed difference between the April cache and the September regeneration is indistinguishable from zero on both scales, so the floating `gpt-4o` alias did not move under this workload, and the precaution of regenerating the real arm turned out to be unnecessary rather than wrong. **Substantial single-draw noise**: re-running the identical prompt at temperature zero changes the KG-relevant score by 0.88 points on average and leaves it unchanged in only 14 of 32 pull requests. The noise is unbiased, so paired means over 25–40 pull requests remain trustworthy, but any single per-pull-request score should be read as one draw rather than a fixed property of the arm.

This is an estimate from one replicate, not a variance component.

