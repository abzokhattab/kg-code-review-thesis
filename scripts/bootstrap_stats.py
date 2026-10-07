#!/usr/bin/env python3
"""Paired bootstrap CIs + paired permutation tests for the 25-PR multi-judge result.

Produces per-mode mean ± 95% CI on (total, kg-relevant) scores, paired
(mode − baseline) per-PR differences with 95% CI, and a permutation p-value
for the null "no mean difference between mode and baseline."

Output: JSON + a short markdown table, suitable to drop into the thesis.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class PairedSample:
    pr_id: int
    baseline_total: int
    baseline_kg: int
    mode_total: int
    mode_kg: int


def load_eval(path: Path) -> dict:
    return json.loads(path.read_text())


def build_pairs(evs: list[dict], mode: str) -> list[PairedSample]:
    by_pr: dict[int, dict[str, dict]] = {}
    for e in evs:
        by_pr.setdefault(e["pr_id"], {})[e["mode"]] = e
    out: list[PairedSample] = []
    for pr, mm in by_pr.items():
        if "baseline" not in mm or mode not in mm:
            continue
        out.append(PairedSample(
            pr_id=pr,
            baseline_total=mm["baseline"]["total_score"],
            baseline_kg=mm["baseline"]["kg_relevant_score"],
            mode_total=mm[mode]["total_score"],
            mode_kg=mm[mode]["kg_relevant_score"],
        ))
    return out


def bootstrap_mean_ci(xs: list[float], n_boot: int, rng: random.Random, alpha: float = 0.05) -> tuple[float, float, float]:
    """Return (mean, lo, hi) from a percentile bootstrap on the mean."""
    n = len(xs)
    means: list[float] = []
    for _ in range(n_boot):
        sample = [xs[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(alpha / 2 * n_boot)]
    hi = means[int((1 - alpha / 2) * n_boot)]
    return mean(xs), lo, hi


def paired_bootstrap_diff_ci(pairs: list[tuple[float, float]], n_boot: int, rng: random.Random, alpha: float = 0.05) -> tuple[float, float, float, float]:
    """Paired bootstrap on (mode − baseline). Returns (mean_diff, lo, hi, std_obs)."""
    diffs = [b - a for a, b in pairs]
    n = len(diffs)
    means: list[float] = []
    for _ in range(n_boot):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(alpha / 2 * n_boot)]
    hi = means[int((1 - alpha / 2) * n_boot)]
    # unbiased sample std
    m = sum(diffs) / n
    var = sum((d - m) ** 2 for d in diffs) / max(1, n - 1)
    return m, lo, hi, var ** 0.5


def paired_permutation_p(pairs: list[tuple[float, float]], n_perm: int, rng: random.Random) -> float:
    """Exact-when-possible paired sign-flip permutation test, two-sided.

    Tests H0: mean(mode − baseline) = 0 by randomly flipping the sign of each
    paired difference and counting |permuted mean| ≥ |observed mean|.
    """
    diffs = [b - a for a, b in pairs]
    n = len(diffs)
    observed = sum(diffs) / n
    abs_obs = abs(observed)
    # Exact enumeration only feasible up to n ≈ 20. For n = 25 use sampling.
    if n <= 20:
        total = 1 << n
        count = 0
        for mask in range(total):
            s = 0.0
            for i, d in enumerate(diffs):
                s += d if (mask >> i) & 1 else -d
            if abs(s / n) >= abs_obs - 1e-12:
                count += 1
        return count / total
    count = 0
    for _ in range(n_perm):
        s = 0.0
        for d in diffs:
            s += d if rng.random() < 0.5 else -d
        if abs(s / n) >= abs_obs - 1e-12:
            count += 1
    return count / n_perm


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="inp", required=True, help="path to checklist_evaluation_llm_multi*.json")
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--n-perm", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--label", default="", help="optional label for the markdown header")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    d = load_eval(Path(args.inp))
    evs = d["evaluations"]
    modes = ["baseline", "kg", "rag", "hybrid"]

    result: dict = {"n_boot": args.n_boot, "n_perm": args.n_perm, "seed": args.seed,
                    "input": str(args.inp), "by_mode": {}, "vs_baseline": {}}

    # Per-mode mean + CI
    for m in modes:
        totals = [e["total_score"] for e in evs if e["mode"] == m]
        kgrel  = [e["kg_relevant_score"] for e in evs if e["mode"] == m]
        # Two-arm runs (e.g. the held-out confirmatory test) carry only
        # baseline + kg; absent arms are skipped rather than divided by zero.
        if not totals:
            continue
        mt, lo_t, hi_t = bootstrap_mean_ci(totals, args.n_boot, rng)
        mk, lo_k, hi_k = bootstrap_mean_ci(kgrel, args.n_boot, rng)
        result["by_mode"][m] = {
            "n": len(totals),
            "total": {"mean": round(mt, 3), "ci_lo": round(lo_t, 3), "ci_hi": round(hi_t, 3)},
            "kg_relevant": {"mean": round(mk, 3), "ci_lo": round(lo_k, 3), "ci_hi": round(hi_k, 3)},
        }

    # Paired vs baseline
    for m in [x for x in modes if x != "baseline"]:
        pairs = build_pairs(evs, m)
        if not pairs:
            continue
        pairs_total = [(p.baseline_total, p.mode_total) for p in pairs]
        pairs_kg    = [(p.baseline_kg, p.mode_kg) for p in pairs]
        dt, lo_t, hi_t, std_t = paired_bootstrap_diff_ci(pairs_total, args.n_boot, rng)
        dk, lo_k, hi_k, std_k = paired_bootstrap_diff_ci(pairs_kg,    args.n_boot, rng)
        p_total = paired_permutation_p(pairs_total, args.n_perm, rng)
        p_kg    = paired_permutation_p(pairs_kg,    args.n_perm, rng)
        # Cohen's d_z on the paired differences
        import math
        d_z_total = dt / std_t if std_t > 0 else 0.0
        d_z_kg    = dk / std_k if std_k > 0 else 0.0
        result["vs_baseline"][m] = {
            "n_pairs": len(pairs),
            "total_diff": {"mean": round(dt, 3), "ci_lo": round(lo_t, 3), "ci_hi": round(hi_t, 3),
                           "std": round(std_t, 3), "d_z": round(d_z_total, 3), "p_value": round(p_total, 4)},
            "kg_relevant_diff": {"mean": round(dk, 3), "ci_lo": round(lo_k, 3), "ci_hi": round(hi_k, 3),
                                 "std": round(std_k, 3), "d_z": round(d_z_kg, 3), "p_value": round(p_kg, 4)},
        }

    Path(args.out_json).write_text(json.dumps(result, indent=2))

    # Markdown table
    label = args.label or Path(args.inp).stem
    lines: list[str] = []
    lines.append(f"# Bootstrap CIs + paired permutation tests — {label}\n")
    lines.append(f"**Input:** `{args.inp}`  ")
    lines.append(f"**Method:** percentile bootstrap (B={args.n_boot}), paired sign-flip permutation (B={args.n_perm}), seed={args.seed}.\n")

    lines.append("## Per-mode mean scores with 95% bootstrap CI\n")
    lines.append("| Mode | n | Total mean [95% CI] | KG-relevant mean [95% CI] |")
    lines.append("|---|---:|---:|---:|")
    for m in [x for x in modes if x in result["by_mode"]]:
        s = result["by_mode"][m]
        t = s["total"]; k = s["kg_relevant"]
        lines.append(f"| {m} | {s['n']} | {t['mean']:.2f} [{t['ci_lo']:.2f}, {t['ci_hi']:.2f}] | {k['mean']:.2f} [{k['ci_lo']:.2f}, {k['ci_hi']:.2f}] |")

    lines.append("\n## Paired differences vs baseline (mode − baseline, same PR)\n")
    lines.append("| Mode vs baseline | n pairs | Total Δ [95% CI] | p (perm, two-sided) | Cohen's d_z | KG-rel Δ [95% CI] | p (perm) | d_z |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for m in [x for x in modes if x != "baseline" and x in result["vs_baseline"]]:
        r = result["vs_baseline"][m]
        t = r["total_diff"]; k = r["kg_relevant_diff"]
        lines.append(
            f"| {m} | {r['n_pairs']} | "
            f"{t['mean']:+.2f} [{t['ci_lo']:+.2f}, {t['ci_hi']:+.2f}] | {t['p_value']:.3f} | {t['d_z']:+.2f} | "
            f"{k['mean']:+.2f} [{k['ci_lo']:+.2f}, {k['ci_hi']:+.2f}] | {k['p_value']:.3f} | {k['d_z']:+.2f} |"
        )

    lines.append("\n## Interpretation key\n")
    lines.append("- **CI crosses 0 → not significant.** The effect cannot be distinguished from zero at the 95% level.")
    lines.append("- **p < 0.05** on the paired permutation test → we reject the null of no per-PR mean difference.")
    lines.append("- **Cohen's d_z**: 0.2 = small, 0.5 = medium, 0.8 = large (paired).")
    lines.append("")
    Path(args.out_md).write_text("\n".join(lines))
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
