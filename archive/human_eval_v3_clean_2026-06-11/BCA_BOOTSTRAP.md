# BCa bootstrap CI — parity Joern d_z

Bias-corrected accelerated (BCa) bootstrap is more accurate than percentile
bootstrap when the sampling distribution is skewed or biased — common at n=35.
Reports both intervals so the gap is visible.

## KG-rel d_z (n=35)

- Point estimate: **d_z = +0.302**
- Bootstrap mean: **+0.308** (over 10000 resamples)
- **BCa 95% CI: [-0.047, +0.640]**
- Percentile 95% CI: [-0.027, +0.653]  *(for comparison)*
- Bias correction z0 = -0.0150
- Acceleration a   = -0.0127
- Adjusted lower percentile = 2.06%
- Adjusted upper percentile = 97.01%

## Total score d_z (n=35)

- Point estimate: **d_z = +0.324**
- **BCa 95% CI: [-0.049, +0.687]**
- Percentile 95% CI: [+0.000, +0.737]
- z0 = -0.0469, a = -0.0329

## Reading

- If BCa lower bound > 0, the effect is significant in the BCa sense.
- If BCa low < 0 < BCa high, the n=35 sample doesn't rule out null.
- BCa typically tightens by 5-15% at n=35 when bias/acceleration are small.
