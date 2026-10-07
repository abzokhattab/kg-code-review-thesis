#!/usr/bin/env python3
"""How many held-out pull requests a confirmatory test of the KG effect would need.

Chapter 6 reports that the 12-PR held-out test had roughly an 8 % chance (total
scale) and 16 % chance (KG-relevant subscale) of reaching p < 0.05 even if the
exploratory effect were exactly real, and concludes that the confirmatory endpoint
is unresolved rather than refuted. The obvious next question -- how big would an
adequate test have to be -- was answered in a \\todo with the guess "roughly
80--100 PRs". This script replaces the guess with a number computed the same way
the 12-PR figure was: resample pull requests from the observed paired differences
and run the same paired permutation test on each resample.

Method. The 40 observed per-PR paired differences (kg minus baseline, panel score)
are treated as the population. For each candidate sample size n, draw n of them,
run a two-sided paired permutation test by random sign flipping, and record whether
p < 0.05. Power at n is the fraction of simulations that reach significance. This
inherits the effect size and the difference distribution from the data rather than
assuming normality, which matters because rubric sums are small integers and their
differences are not close to normal.

Two resampling schemes appear below, and the difference between them is not
cosmetic. Drawing *without* replacement reproduces what Chapter 6 already reports
for the 12-PR test (about 8 % on the total scale and 16 % on the subscale), but it
cannot answer the question this script exists for, since one cannot draw 85 pull
requests out of 40. Drawing *with* replacement extends to any n and is what the
curve uses. Both are reported at n = 12 so the reader can see how much the choice
of scheme is worth; it is a few percentage points, in the same direction for both
scales.

Two caveats on how the answer should be read. It is an optimistic bound, because
the resampling assumes the exploratory point estimate is the truth, and that
estimate is itself the largest of the values this project has measured for the
effect. And bootstrap resampling from 40 observations cannot represent variability
the 40 do not contain. The number is therefore a design aid, not a promise.

No API keys, no cost, no network. Runs in about a minute.

Input
  results/checklist_evaluation_llm_multi__v2.json   the judged panel, n = 40

Output
  results/CONFIRMATORY_POWER.md / .json

Usage
  python3 scripts/estimate_confirmatory_power.py
  python3 scripts/estimate_confirmatory_power.py --sims 5000 --seed 7
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
PANEL = REPO_ROOT / "results" / "checklist_evaluation_llm_multi__v2.json"

# Matches the exploratory analysis in scripts/bootstrap_stats.py.
ALPHA = 0.05
N_PERM = 2000
TARGETS = (0.80, 0.90)
GRID = list(range(10, 205, 5))


def paired_differences(panel: dict, mode: str = "kg") -> dict[str, list[float]]:
    """Per-PR (mode minus baseline) on both scales, panel score per cell."""
    tot: dict[tuple, list[float]] = {}
    kgr: dict[tuple, list[float]] = {}
    for e in panel["evaluations"]:
        tot.setdefault((e["pr_id"], e["mode"]), []).append(e["total_score"])
        kgr.setdefault((e["pr_id"], e["mode"]), []).append(e["kg_relevant_score"])
    prs = sorted({p for p, _ in tot})
    out = {}
    for name, d in (("total", tot), ("kgrel", kgr)):
        out[name] = [statistics.mean(d[(p, mode)])
                     - statistics.mean(d[(p, "baseline")]) for p in prs]
    return out


def perm_p(sample: np.ndarray, rng: np.random.Generator,
           n_perm: int = N_PERM) -> float:
    """Two-sided paired permutation p by sign flipping, as in the main analysis.

    The +1 in numerator and denominator is the standard correction that keeps the
    p-value from ever being exactly 0, which an estimate from a finite number of
    permutations cannot justify.
    """
    obs = abs(sample.mean())
    signs = rng.choice((-1.0, 1.0), size=(n_perm, sample.size))
    null = np.abs((signs * sample).mean(axis=1))
    return (np.sum(null >= obs) + 1) / (n_perm + 1)


def power_at(diffs: np.ndarray, n: int, sims: int, rng: np.random.Generator,
             replace: bool = True) -> float:
    if not replace and n > diffs.size:
        raise ValueError(f"cannot draw {n} of {diffs.size} without replacement")
    hits = 0
    for _ in range(sims):
        sample = rng.choice(diffs, size=n, replace=replace)
        # A resample with zero variance makes the sign-flip test degenerate: every
        # permutation gives the same |mean|, so p = 1 unless the mean is also 0.
        # Count it as a miss rather than dividing by zero.
        if sample.std() == 0:
            continue
        if perm_p(sample, rng) < ALPHA:
            hits += 1
    return hits / sims


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default="results/CONFIRMATORY_POWER")
    args = ap.parse_args()

    panel = json.loads(PANEL.read_text())
    diffs = paired_differences(panel)
    rng = np.random.default_rng(args.seed)

    result = {"meta": {"alpha": ALPHA, "n_perm": N_PERM, "sims": args.sims,
                       "seed": args.seed, "source": str(PANEL.relative_to(REPO_ROOT)),
                       "contrast": "kg minus baseline"},
              "scales": {}}

    for scale in ("total", "kgrel"):
        d = np.asarray(diffs[scale], dtype=float)
        mean, sd = d.mean(), d.std(ddof=1)
        curve = {}
        print(f"\n{scale}: n = {d.size}, mean = {mean:+.3f}, "
              f"sd = {sd:.3f}, d_z = {mean / sd:+.3f}")
        print(f"{'n':>5}  {'power':>6}")
        needed = {}
        for n in GRID:
            p = power_at(d, n, args.sims, rng)
            curve[n] = p
            print(f"{n:5d}  {p:6.3f}")
            for t in TARGETS:
                if t not in needed and p >= t:
                    needed[t] = n
        result["scales"][scale] = {
            "n_observed": int(d.size), "mean": mean, "sd": sd,
            "d_z": mean / sd, "power_curve": curve,
            "n_for_power": {str(t): needed.get(t) for t in TARGETS},
        }
        # n = 12 is what the thesis actually ran, and is not on the grid. Both
        # schemes are reported: without replacement to check this script against
        # the figures already in Chapter 6, with replacement for comparability
        # with the curve above.
        result["scales"][scale]["power_at_n12"] = power_at(d, 12, args.sims, rng)
        result["scales"][scale]["power_at_n12_no_replacement"] = power_at(
            d, 12, args.sims, rng, replace=False)

    out_json = REPO_ROOT / (args.out + ".json")
    out_json.write_text(json.dumps(result, indent=2) + "\n")

    L = ["# Power of a confirmatory test of the KG effect", "",
         f"Contrast: kg minus baseline. alpha = {ALPHA}, "
         f"{N_PERM} sign-flip permutations per test, {args.sims} simulations per "
         f"sample size, seed {args.seed}.", "",
         "Resampled from the 40 observed per-PR paired differences, so the effect "
         "size is inherited from the data. Optimistic by construction: it assumes "
         "the exploratory point estimate is the truth. The curve draws **with** "
         "replacement, which is the only scheme that extends past n = 40.", "",
         "| Scale | observed d_z | power at n = 12 (subsample) | power at n = 12 "
         "(bootstrap) | n for 80 % | n for 90 % |",
         "|---|---|---|---|---|---|"]
    for scale, lab in (("total", "Total /25"), ("kgrel", "KG-relevant /9")):
        s = result["scales"][scale]
        L.append(f"| {lab} | {s['d_z']:+.2f} | "
                 f"{s['power_at_n12_no_replacement']:.0%} | "
                 f"{s['power_at_n12']:.0%} | "
                 f"{s['n_for_power']['0.8'] or '> 200'} | "
                 f"{s['n_for_power']['0.9'] or '> 200'} |")
    L += ["", "The subsample column is the check against Chapter 6, which reports "
              "about 8 % and 16 % for this design from the same scheme."]
    L += ["", "## Full curves", "",
          "| n | total | KG-relevant |", "|---|---|---|"]
    for n in GRID:
        L.append(f"| {n} | {result['scales']['total']['power_curve'][n]:.3f} | "
                 f"{result['scales']['kgrel']['power_curve'][n]:.3f} |")
    (REPO_ROOT / (args.out + ".md")).write_text("\n".join(L) + "\n")

    print(f"\nwrote {args.out}.md and .json")
    for scale in ("total", "kgrel"):
        s = result["scales"][scale]
        print(f"  {scale}: power at n=12 is {s['power_at_n12']:.0%}; "
              f"80 % needs n = {s['n_for_power']['0.8']}, "
              f"90 % needs n = {s['n_for_power']['0.9']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
