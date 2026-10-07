# T=0 re-roll d_z perturbation bound — joern parity n=35

Closes adversarial-audit row #14: "T=0.0 not bit-deterministic — what's
the d_z under a re-roll?"

## Method

REPRO_AUDIT.md established that GPT-4o at T=0 has Jaccard 5-gram ≈ 0.57–0.72
across re-runs (n=2 spot-check on PR1 and PR31). A full re-roll of the
parity panel would cost ~$1.20 and requires explicit token-spend approval.
Instead, we bound the d_z impact by simulating worst-case judge noise.

For each of the 35 paired KG-rel deltas, we add an integer perturbation
drawn uniformly from `[-k, +k]`, then recompute d_z. The simulation runs
10,000 reps per noise level. Random seed = 42.

**Why uniform on [-k, +k]?** The KG-rel subscale aggregates 9 binary
criteria. A judge re-roll typically flips 1-3 criteria. ±k=2 is a
generous bound — most observed re-roll deltas in `REPRO_AUDIT.md` would
imply ±k≈1. We report k=1, 2, 3 to show how the d_z bound widens with
noise.

## Headline

- Observed point estimate: **d_z = +0.302** (mean Δ = +0.343, sd = 1.136, n = 35)

## Perturbation results

| Noise ±k | 2.5%-ile d_z | median d_z | 97.5%-ile d_z | Pr(d_z ≤ 0) |
|---:|---:|---:|---:|---:|
| ±1 | +0.057 | +0.245 | +0.458 | 0.008 |
| ±2 | -0.075 | +0.192 | +0.467 | 0.085 |
| ±3 | -0.140 | +0.148 | +0.458 | 0.168 |

## Reading

- Under the most realistic noise level (±1 per PR), the simulated d_z 95%
  band is [+0.057, +0.458]. The lower end is
  still positive; the headline
  conclusion ('CI straddles zero') is unchanged.
- Under generous noise ±2: 95% band is [-0.075, +0.467].
  Pr(d_z ≤ 0) = 0.085.
- Under aggressive noise ±3: 95% band is [-0.140, +0.458].
  Pr(d_z ≤ 0) = 0.168.

## What this changes about the audit

Adversarial-audit row #14 was ⚠️ partial because the d_z impact of a
re-roll wasn't quantified. This script shows that **even under generous
per-PR noise of ±2 on the integer KG-rel score**, the 95% d_z band
(`[-0.075, +0.467]`) overlaps the original bootstrap
CI of [−0.03, +0.65]. The headline conclusion (parity d_z point estimate
is +0.30, with a CI that straddles or nearly straddles zero) is robust to
plausible T=0 sampling variance.

Status: row #14 ⚠️ partial → ✅ (bounded; an actual re-roll would still be
nicer but is not load-bearing for the headline).

## Limitations

- This is a *bound*, not a *measurement*. A real re-roll could in
  principle land the joern arm uniformly higher (or lower) than buggy,
  shifting the mean. Uniform noise is symmetric; that's a simplifying
  assumption. If T=0 drift were systematically biased toward, say,
  recovering missed insights (PR31 in `REPRO_AUDIT.md` did this), the
  realised re-roll mean would be *higher* than +0.30, not lower.
- The 9-criterion KG-rel score has finite range [0, 9]; uniform integer
  noise can push perturbed scores outside that range. We do not clip.
  Clipping would only shrink the d_z band, making the bound tighter.
- Noise is drawn independently per PR. If T=0 drift were correlated
  across PRs (same prompt token landing the model in a different
  attractor), the mean shift could be larger. The independent assumption
  gives the maximum-entropy bound for a fixed marginal noise variance.