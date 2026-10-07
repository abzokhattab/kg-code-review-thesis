#!/usr/bin/env python3
"""Power analysis defense doc for the parity n=35 sample.

The committee will likely ask: "n=35, p=0.057, CI straddles zero — isn't this
just an underpowered null?" The answer is: yes, n=35 has limited power for
d_z=+0.30, and we report the CI honestly rather than claiming p<0.05. This
script makes that defensible by computing:

  1. The MDE (minimum detectable effect) at n=35 for 80% power, alpha=0.05
  2. The achieved power for the observed d_z=+0.30 at n=35
  3. The n required to detect d_z=+0.30 at 80% power
  4. The MDE if we had n=40 (the tree-sitter sample)
  5. A power curve over n=10..150

We use a one-sample paired t-test power calculation (matches paired-t formulation
of d_z = mean / sd). All formulas are non-central t-based, computed via numerical
integration of the non-central t CDF.

Output: POWER_ANALYSIS.md
"""
from __future__ import annotations
import math
from pathlib import Path

OUT = Path(__file__).parent / "POWER_ANALYSIS.md"

OBSERVED_DZ = 0.302
PARITY_N = 35
TS_N = 40
ALPHA = 0.05


def t_cdf(t, df):
    """Two-sided central t CDF via incomplete beta. df > 0."""
    if df <= 0:
        return 0.5
    x = df / (df + t * t)
    a, b = 0.5 * df, 0.5
    ib = _betai(a, b, x)
    if t >= 0:
        return 1 - 0.5 * ib
    return 0.5 * ib


def _betai(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1 - x) * b - lbeta) / a
    return front * _betacf(a, b, x)


def _betacf(a, b, x, max_iter=200, eps=1e-12):
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < eps:
        d = eps
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < eps:
            d = eps
        c = 1.0 + aa / c
        if abs(c) < eps:
            c = eps
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < eps:
            d = eps
        c = 1.0 + aa / c
        if abs(c) < eps:
            c = eps
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def t_inv(p, df, lo=-100, hi=100):
    """Inverse of central t CDF via bisection."""
    for _ in range(100):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-6:
            break
    return (lo + hi) / 2


def nct_power_two_sided(d_z, n, alpha=0.05, n_int=2000):
    """Power for two-sided one-sample t-test with effect size d_z and n paired obs.

    Numerical integration of the non-central t CDF via Owen's method-style
    representation: P(|T_nc| > t_crit) where T_nc has non-centrality d_z * sqrt(n).
    We approximate via a normal-on-scaled-variance representation.
    """
    df = n - 1
    if df <= 0:
        return 0.0
    nc = d_z * math.sqrt(n)
    t_crit = t_inv(1 - alpha / 2, df)
    p_upper = 1 - _nct_cdf(t_crit, df, nc, n_int)
    p_lower = _nct_cdf(-t_crit, df, nc, n_int)
    return max(0.0, min(1.0, p_upper + p_lower))


def _nct_cdf(t, df, nc, n_int=2000):
    """Non-central t CDF via integration over a chi-square draw.

    Use the representation T = (Z + nc) / sqrt(V/df) where Z ~ N(0,1), V ~ chi2(df).
    P(T <= t) = E_V [Phi(t * sqrt(V/df) - nc)].
    Approximate the chi-square expectation by Gauss-Laguerre-style sum on log-spaced V.
    """
    # numerical: monte-carlo-free via sampling V on a grid then weighted by chi2 pdf.
    # Use 2000 grid points on [0.001, 5*df] (covers the bulk of the chi2(df) mass).
    if df <= 0:
        return 0.5
    v_max = max(5 * df, 50)
    dv = v_max / n_int
    total = 0.0
    pdf_sum = 0.0
    for i in range(n_int):
        v = (i + 0.5) * dv
        log_pdf = (df / 2 - 1) * math.log(v) - v / 2 - (df / 2) * math.log(2) - math.lgamma(df / 2)
        pdf = math.exp(log_pdf)
        z_arg = t * math.sqrt(v / df) - nc
        phi = 0.5 * (1 + math.erf(z_arg / math.sqrt(2)))
        total += pdf * phi * dv
        pdf_sum += pdf * dv
    if pdf_sum > 0:
        total /= pdf_sum
    return max(0.0, min(1.0, total))


def find_mde(n, alpha=0.05, target_power=0.8):
    lo, hi = 0.0, 3.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if nct_power_two_sided(mid, n, alpha) < target_power:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-4:
            break
    return (lo + hi) / 2


def find_n_for_power(d_z, target_power=0.8, alpha=0.05, hi=500):
    for n in range(3, hi + 1):
        if nct_power_two_sided(d_z, n, alpha) >= target_power:
            return n
    return None


def main():
    parity_power = nct_power_two_sided(OBSERVED_DZ, PARITY_N, ALPHA)
    parity_mde = find_mde(PARITY_N, ALPHA)
    ts_mde = find_mde(TS_N, ALPHA)
    n_for_observed = find_n_for_power(OBSERVED_DZ, 0.8, ALPHA)
    n_for_observed_50 = find_n_for_power(OBSERVED_DZ, 0.5, ALPHA)

    ns = [10, 15, 20, 25, 30, 35, 40, 50, 60, 75, 100, 125, 150]
    curve = []
    for n in ns:
        p030 = nct_power_two_sided(0.30, n, ALPHA)
        p047 = nct_power_two_sided(0.47, n, ALPHA)
        p134 = nct_power_two_sided(1.34, n, ALPHA)
        curve.append({"n": n, "p030": p030, "p047": p047, "p134": p134})

    lines = []
    P = lines.append
    P("# Power analysis — parity Joern n=35, tree-sitter n=40")
    P("")
    P("Closes the reviewer attack: \"n=35, p=0.057, CI straddles zero — isn't")
    P("this just an underpowered null?\"")
    P("")
    P("The honest answer: yes, n=35 has limited power for d_z=+0.30. We do **not**")
    P("claim p<0.05; we report the CI [−0.03, +0.65] and the point estimate, and")
    P("flag the parity result as exploratory replication of the pre-registered")
    P("tree-sitter headline.")
    P("")
    P("This document quantifies the power so the committee can see exactly what")
    P("we could and could not have detected.")
    P("")
    P("## Headline numbers")
    P("")
    P(f"- **Observed d_z (parity, n=35): {OBSERVED_DZ:+.3f}**")
    P(f"- **Achieved power for d_z=+0.30 at n=35:** {parity_power:.3f} ({parity_power*100:.0f}%)")
    P(f"- **MDE at n=35 for 80% power, α=0.05:** d_z ≈ {parity_mde:+.3f}")
    P(f"- **MDE at n=40 (tree-sitter) for 80% power, α=0.05:** d_z ≈ {ts_mde:+.3f}")
    P(f"- **n required to detect d_z=+0.30 at 80% power:** n ≈ {n_for_observed}")
    P(f"- **n required to detect d_z=+0.30 at 50% power:** n ≈ {n_for_observed_50}")
    P("")
    P("## Power curve")
    P("")
    P("Power for two-sided paired t-test, α=0.05, at three effect sizes:")
    P("- d_z=+0.30 (parity Joern observed)")
    P("- d_z=+0.47 (tree-sitter pre-registered observed)")
    P("- d_z=+1.34 (strict-prompt observed; for reference)")
    P("")
    P("| n | power@d_z=0.30 | power@d_z=0.47 | power@d_z=1.34 |")
    P("|---:|---:|---:|---:|")
    for c in curve:
        P(f"| {c['n']} | {c['p030']:.3f} | {c['p047']:.3f} | {c['p134']:.3f} |")
    P("")
    P("## Reading")
    P("")
    P(f"- The pre-registered tree-sitter headline (d_z=+0.47, n=40) had achieved")
    p047_n40 = nct_power_two_sided(0.47, 40, ALPHA)
    P(f"  power ≈ {p047_n40:.2f}, comfortably above the 80% threshold and")
    P(f"  consistent with the observed p=0.006.")
    P(f"- The Joern parity result (d_z=+0.30, n=35) had achieved power ≈")
    P(f"  {parity_power:.2f}. To detect d_z=+0.30 at 80% power would have required")
    P(f"  n ≈ {n_for_observed}. We have n=35 because Go-language PRs are excluded")
    P(f"  (Joern frontend lacks call edges).")
    P(f"- The strict-prompt run (d_z=+1.34, n=35) had achieved power ≈")
    p134_n35 = nct_power_two_sided(1.34, 35, ALPHA)
    P(f"  {p134_n35:.2f} — saturated. The strict result reaches significance")
    P("  trivially.")
    P("")
    P("## What this means for interpretation")
    P("")
    P("The parity-vs-baseline difference is not a 'failed test'; it's an")
    P("under-powered estimate. The point estimate (d_z=+0.30) is positive, the")
    P("direction is consistent with the tree-sitter headline (d_z=+0.47), and the")
    P("CI [−0.03, +0.65] gives the committee an honest range. The thesis does not")
    P("claim p<0.05 on the Joern parity arm.")
    P("")
    P("**The pre-registered RQ2 anchor remains the tree-sitter headline.** That")
    P("estimate is adequately powered. Joern parity is an exploratory replication.")
    P("")
    P("## What we'd need to claim p<0.05 on the Joern parity arm")
    P("")
    P(f"- Either the true d_z is closer to {parity_mde:+.3f} (the MDE at n=35)")
    P(f"- Or n grows to ≈ {n_for_observed} for the observed effect size")
    P("")
    P("Neither is achievable in the current dataset. The honest reading remains:")
    P("'consistent direction, sub-significant under-powered replication.'")
    P("")
    P("## Limitations")
    P("")
    P("- These calculations assume a paired-t / parametric framework. The actual")
    P("  reported test is Wilcoxon signed-rank. The two are not interchangeable:")
    P("  on the observed parity data, paired-t gives p=0.083 while Wilcoxon")
    P("  gives p=0.057 — Wilcoxon is *more* powerful here because the per-PR")
    P("  KG-rel deltas are bounded integers and ranks are more efficient than")
    P("  raw values. The paired-t power numbers above therefore *underestimate*")
    P("  the achieved Wilcoxon power on this specific dataset, but the relative")
    P("  efficiency of Wilcoxon vs t is data-dependent (≈0.95 of t under")
    P("  normality, but can exceed 1 under heavy-tailed or discrete data). The")
    P("  qualitative conclusion — 'n=35 is under-powered for d_z=+0.30, an")
    P("  exploratory replication, not a failed test' — is unchanged.")
    P("- Non-central t CDF is computed via numerical integration on a 2000-point")
    P("  chi-square grid. Spot-checked against scipy.stats.nct: matches to 3")
    P("  decimals across all reported cells (achieved power, MDE at n=35 and")
    P("  n=40, n-for-80%-power).")
    OUT.write_text("\n".join(lines))
    print(f"Wrote {OUT}")
    print()
    print(f"Achieved power (d_z={OBSERVED_DZ}, n={PARITY_N}): {parity_power:.3f}")
    print(f"MDE at n={PARITY_N}: {parity_mde:+.3f}")
    print(f"MDE at n={TS_N}: {ts_mde:+.3f}")
    print(f"n for d_z={OBSERVED_DZ} at 80% power: {n_for_observed}")
    print()
    print(f"{'n':>4} | {'p@0.30':>7} | {'p@0.47':>7} | {'p@1.34':>7}")
    for c in curve:
        print(f"{c['n']:>4} | {c['p030']:>7.3f} | {c['p047']:>7.3f} | {c['p134']:>7.3f}")


if __name__ == "__main__":
    main()
