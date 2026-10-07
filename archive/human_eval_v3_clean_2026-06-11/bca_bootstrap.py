#!/usr/bin/env python3
"""BCa (bias-corrected accelerated) bootstrap CI on parity d_z.

Percentile bootstrap (currently in robustness_battery.py) is known to under-cover
with small samples and skewed sampling distributions. BCa corrects for both bias
(z0) and skewness (acceleration a) using a jackknife.

Reference: Efron (1987), DiCiccio & Efron (1996). Two-sided 95%.
"""
from __future__ import annotations
import json
import math
import random
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PARITY = REPO / "experiments" / "2026-06-11_joern_normal_prompt_parity" / "scores"
HEADLINE = REPO / "results" / "checklist_evaluation_llm_multi__v2.json"
OUT = REPO / "human_eval_v3_clean_2026-06-11" / "BCA_BOOTSTRAP.md"

random.seed(42)


def dz(deltas):
    if not deltas:
        return 0.0
    m = sum(deltas) / len(deltas)
    sd = statistics.stdev(deltas) if len(deltas) > 1 else 0.0
    return m / sd if sd > 0 else 0.0


def normal_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def normal_inv(p):
    # Acklam's inverse normal CDF approximation.
    a = [-39.696830279, 220.946098424, -275.928510446, 138.357751867,
         -30.664798066, 2.506628277]
    b = [-54.476098798, 161.585836858, -155.698979859, 66.801311887,
         -13.280681552, 1.0]
    c = [-0.007784894002, -0.32239645, -2.400758278, -2.549732540,
         4.374664141, 2.938163983]
    d = [0.007784695709, 0.32246712, 2.445134137, 3.754408661, 1.0]
    plow = 0.02425
    phigh = 1 - plow
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + d[4]
        )
    if p <= phigh:
        q = p - 0.5
        r = q * q
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (
            ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + b[5]
        )
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
        (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + d[4]
    )


def bca_ci(deltas, n_boot=10000, alpha=0.05):
    n = len(deltas)
    theta_hat = dz(deltas)

    # bootstrap distribution
    boots = []
    for _ in range(n_boot):
        sample = [random.choice(deltas) for _ in range(n)]
        sd = statistics.stdev(sample) if n > 1 else 0.0
        if sd > 0:
            boots.append(statistics.mean(sample) / sd)
    boots.sort()

    # bias-correction z0
    n_below = sum(1 for b in boots if b < theta_hat)
    p0 = n_below / len(boots)
    p0 = max(min(p0, 1 - 1e-9), 1e-9)
    z0 = normal_inv(p0)

    # acceleration a (jackknife)
    jacks = []
    for i in range(n):
        loo = deltas[:i] + deltas[i + 1:]
        jacks.append(dz(loo))
    j_mean = sum(jacks) / n
    num = sum((j_mean - j) ** 3 for j in jacks)
    den = 6 * (sum((j_mean - j) ** 2 for j in jacks)) ** 1.5
    a = num / den if den > 0 else 0.0

    # adjusted percentiles
    z_lo = normal_inv(alpha / 2)
    z_hi = normal_inv(1 - alpha / 2)
    al_lo = normal_cdf(z0 + (z0 + z_lo) / (1 - a * (z0 + z_lo)))
    al_hi = normal_cdf(z0 + (z0 + z_hi) / (1 - a * (z0 + z_hi)))

    lo = boots[max(0, min(len(boots) - 1, int(al_lo * len(boots))))]
    hi = boots[max(0, min(len(boots) - 1, int(al_hi * len(boots))))]

    # also percentile for comparison
    pct_lo = boots[int(alpha / 2 * len(boots))]
    pct_hi = boots[int((1 - alpha / 2) * len(boots))]

    return {
        "theta_hat": theta_hat,
        "n_boot": len(boots),
        "z0": z0, "a": a,
        "alpha_lo_adj": al_lo, "alpha_hi_adj": al_hi,
        "bca_lo": lo, "bca_hi": hi,
        "pct_lo": pct_lo, "pct_hi": pct_hi,
        "boot_mean": statistics.mean(boots),
    }


def main():
    parity = {json.loads(f.read_text())["pr_id"]: json.loads(f.read_text())
              for f in PARITY.glob("pr*_kg.json")}
    bl = {e["pr_id"]: e for e in json.loads(HEADLINE.read_text())["evaluations"]
          if e["mode"] == "baseline"}
    common = sorted(set(parity) & set(bl))

    kg_deltas = [parity[p]["kg_relevant_score"] - bl[p]["kg_relevant_score"] for p in common]
    tot_deltas = [parity[p]["total_score"] - bl[p]["total_score"] for p in common]

    res_kg = bca_ci(kg_deltas)
    res_tot = bca_ci(tot_deltas)

    lines = []
    P = lines.append
    P("# BCa bootstrap CI — parity Joern d_z")
    P("")
    P("Bias-corrected accelerated (BCa) bootstrap is more accurate than percentile")
    P("bootstrap when the sampling distribution is skewed or biased — common at n=35.")
    P("Reports both intervals so the gap is visible.")
    P("")
    P(f"## KG-rel d_z (n={len(kg_deltas)})")
    P("")
    P(f"- Point estimate: **d_z = {res_kg['theta_hat']:+.3f}**")
    P(f"- Bootstrap mean: **{res_kg['boot_mean']:+.3f}** (over {res_kg['n_boot']} resamples)")
    P(f"- **BCa 95% CI: [{res_kg['bca_lo']:+.3f}, {res_kg['bca_hi']:+.3f}]**")
    P(f"- Percentile 95% CI: [{res_kg['pct_lo']:+.3f}, {res_kg['pct_hi']:+.3f}]  *(for comparison)*")
    P(f"- Bias correction z0 = {res_kg['z0']:+.4f}")
    P(f"- Acceleration a   = {res_kg['a']:+.4f}")
    P(f"- Adjusted lower percentile = {res_kg['alpha_lo_adj']*100:.2f}%")
    P(f"- Adjusted upper percentile = {res_kg['alpha_hi_adj']*100:.2f}%")
    P("")
    P(f"## Total score d_z (n={len(tot_deltas)})")
    P("")
    P(f"- Point estimate: **d_z = {res_tot['theta_hat']:+.3f}**")
    P(f"- **BCa 95% CI: [{res_tot['bca_lo']:+.3f}, {res_tot['bca_hi']:+.3f}]**")
    P(f"- Percentile 95% CI: [{res_tot['pct_lo']:+.3f}, {res_tot['pct_hi']:+.3f}]")
    P(f"- z0 = {res_tot['z0']:+.4f}, a = {res_tot['a']:+.4f}")
    P("")
    P("## Reading")
    P("")
    P("- If BCa lower bound > 0, the effect is significant in the BCa sense.")
    P("- If BCa low < 0 < BCa high, the n=35 sample doesn't rule out null.")
    P("- BCa typically tightens by 5-15% at n=35 when bias/acceleration are small.")
    P("")
    OUT.write_text("\n".join(lines))
    print(f"Wrote {OUT}")
    print(f"\nKG-rel d_z = {res_kg['theta_hat']:+.3f}")
    print(f"  BCa CI:  [{res_kg['bca_lo']:+.3f}, {res_kg['bca_hi']:+.3f}]")
    print(f"  Pct CI:  [{res_kg['pct_lo']:+.3f}, {res_kg['pct_hi']:+.3f}]")
    print(f"Total d_z = {res_tot['theta_hat']:+.3f}")
    print(f"  BCa CI:  [{res_tot['bca_lo']:+.3f}, {res_tot['bca_hi']:+.3f}]")
    print(f"  Pct CI:  [{res_tot['pct_lo']:+.3f}, {res_tot['pct_hi']:+.3f}]")


if __name__ == "__main__":
    main()
