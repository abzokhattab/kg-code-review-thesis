# Power analysis — parity Joern n=35, tree-sitter n=40

Closes the reviewer attack: "n=35, p=0.057, CI straddles zero — isn't
this just an underpowered null?"

The honest answer: yes, n=35 has limited power for d_z=+0.30. We do **not**
claim p<0.05; we report the CI [−0.03, +0.65] and the point estimate, and
flag the parity result as exploratory replication of the pre-registered
tree-sitter headline.

This document quantifies the power so the committee can see exactly what
we could and could not have detected.

## Headline numbers

- **Observed d_z (parity, n=35): +0.302**
- **Achieved power for d_z=+0.30 at n=35:** 0.412 (41%)
- **MDE at n=35 for 80% power, α=0.05:** d_z ≈ +0.487
- **MDE at n=40 (tree-sitter) for 80% power, α=0.05:** d_z ≈ +0.454
- **n required to detect d_z=+0.30 at 80% power:** n ≈ 88
- **n required to detect d_z=+0.30 at 50% power:** n ≈ 45

## Power curve

Power for two-sided paired t-test, α=0.05, at three effect sizes:
- d_z=+0.30 (parity Joern observed)
- d_z=+0.47 (tree-sitter pre-registered observed)
- d_z=+1.34 (strict-prompt observed; for reference)

| n | power@d_z=0.30 | power@d_z=0.47 | power@d_z=1.34 |
|---:|---:|---:|---:|
| 10 | 0.136 | 0.265 | 0.964 |
| 15 | 0.192 | 0.396 | 0.998 |
| 20 | 0.247 | 0.514 | 1.000 |
| 25 | 0.302 | 0.616 | 1.000 |
| 30 | 0.355 | 0.701 | 1.000 |
| 35 | 0.407 | 0.771 | 1.000 |
| 40 | 0.457 | 0.826 | 1.000 |
| 50 | 0.548 | 0.903 | 1.000 |
| 60 | 0.628 | 0.947 | 1.000 |
| 75 | 0.727 | 0.980 | 1.000 |
| 100 | 0.844 | 0.996 | 1.000 |
| 125 | 0.914 | 0.999 | 1.000 |
| 150 | 0.955 | 1.000 | 1.000 |

## Reading

- The pre-registered tree-sitter headline (d_z=+0.47, n=40) had achieved
  power ≈ 0.83, comfortably above the 80% threshold and
  consistent with the observed p=0.006.
- The Joern parity result (d_z=+0.30, n=35) had achieved power ≈
  0.41. To detect d_z=+0.30 at 80% power would have required
  n ≈ 88. We have n=35 because Go-language PRs are excluded
  (Joern frontend lacks call edges).
- The strict-prompt run (d_z=+1.34, n=35) had achieved power ≈
  1.00 — saturated. The strict result reaches significance
  trivially.

## What this means for interpretation

The parity-vs-baseline difference is not a 'failed test'; it's an
under-powered estimate. The point estimate (d_z=+0.30) is positive, the
direction is consistent with the tree-sitter headline (d_z=+0.47), and the
CI [−0.03, +0.65] gives the committee an honest range. The thesis does not
claim p<0.05 on the Joern parity arm.

**The pre-registered RQ2 anchor remains the tree-sitter headline.** That
estimate is adequately powered. Joern parity is an exploratory replication.

## What we'd need to claim p<0.05 on the Joern parity arm

- Either the true d_z is closer to +0.487 (the MDE at n=35)
- Or n grows to ≈ 88 for the observed effect size

Neither is achievable in the current dataset. The honest reading remains:
'consistent direction, sub-significant under-powered replication.'

## Limitations

- These calculations assume a paired-t / parametric framework. The actual
  reported test is Wilcoxon signed-rank. The two are not interchangeable:
  on the observed parity data, paired-t gives p=0.083 while Wilcoxon
  gives p=0.057 — Wilcoxon is *more* powerful here because the per-PR
  KG-rel deltas are bounded integers and ranks are more efficient than
  raw values. The paired-t power numbers above therefore *underestimate*
  the achieved Wilcoxon power on this specific dataset, but the relative
  efficiency of Wilcoxon vs t is data-dependent (≈0.95 of t under
  normality, but can exceed 1 under heavy-tailed or discrete data). The
  qualitative conclusion — 'n=35 is under-powered for d_z=+0.30, an
  exploratory replication, not a failed test' — is unchanged.
- Non-central t CDF is computed via numerical integration on a 2000-point
  chi-square grid. Spot-checked against scipy.stats.nct: matches to 3
  decimals across all reported cells (achieved power, MDE at n=35 and
  n=40, n-for-80%-power).