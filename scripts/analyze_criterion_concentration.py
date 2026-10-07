#!/usr/bin/env python3
"""analyze_criterion_concentration.py — where does the context effect actually land?

Experiment 1 reports a mode's advantage as two aggregates: total score (/25) and
the KG-relevant subscale (/9). Neither shows *which* criteria moved, so neither
can distinguish "the intervention did the specific thing it was designed to do"
from "everything drifted up a little", even though those two situations imply
very different conclusions.

This script decomposes the paired advantage criterion by criterion and asks one
question: is the gain concentrated in the criteria pre-specified as KG-relevant,
more than a random subset of the same size would be? If a mode's advantage is
noise or a generic verbosity/agreeableness artefact, it should spread roughly in
proportion to subset size (9/25 = 36% of the gain). If it reflects the mechanism
the context is supposed to supply, it should concentrate.

The concentration test is a permutation test over *criteria*, not over PRs, so it
is independent of the per-PR permutation tests in `scripts/bootstrap_stats.py`
and answers a different question (localisation, not magnitude).

Also reported, because both bear on how the aggregates should be read:
  * floor/ceiling criteria — scored identically in both arms at 0% or 100%, so
    they can never register a difference and only dilute the /25 aggregate;
  * mean review length per arm, since a length difference is the standard
    confound for "more context looks more thorough".

Reads:
  results/checklist_evaluation_llm_multi__v2.json  (any panel file of that shape)
  outputs/luca_prs_v2/pr{N}_{mode}.md              (optional, for length)
Writes:
  results/CRITERION_CONCENTRATION.md

Usage:
  python3 scripts/analyze_criterion_concentration.py
  python3 scripts/analyze_criterion_concentration.py --mode rag --mode hybrid
  python3 scripts/analyze_criterion_concentration.py \
      --in results/checklist_evaluation_llm_multi__confirmatory_clean.json \
      --reviews-dir experiments/2026-05-14_confirmatory_kg/reviews_clean \
      --out results/CRITERION_CONCENTRATION_confirmatory.md
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def yes_rate(evals: list[dict], mode: str, cid: str) -> float:
    """Majority-vote yes-rate for one criterion in one arm."""
    scores = [
        cs["score"]
        for e in evals if e["mode"] == mode
        for cs in e["criteria_scores"] if cs["criterion_id"] == cid
    ]
    return sum(scores) / len(scores) if scores else 0.0


def review_lengths(evals: list[dict], mode: str, reviews_dir: Path | None):
    if reviews_dir is None:
        return None
    out = []
    for e in evals:
        if e["mode"] != mode:
            continue
        p = reviews_dir / f"pr{e['pr_id']}_{mode}.md"
        if p.exists():
            out.append(len(p.read_text()))
    return out or None


def concentration_p(delta: dict[str, float], target_ids: list[str],
                    n_iter: int, rng: random.Random) -> tuple[float, float]:
    """P(a random subset of the same size captures >= the observed gain).

    Sampling subsets of criteria, so this asks whether the *localisation* of the
    effect is surprising, holding the observed per-criterion deltas fixed.
    """
    observed = sum(delta[c] for c in target_ids)
    all_ids = list(delta)
    k = len(target_ids)
    hits = sum(
        1 for _ in range(n_iter)
        if sum(delta[c] for c in rng.sample(all_ids, k)) >= observed - 1e-12
    )
    return observed, hits / n_iter


def analyse_mode(evals: list[dict], defs: dict[str, dict], mode: str,
                 baseline: str, n_iter: int, seed: int,
                 reviews_dir: Path | None) -> dict:
    base_rate = {cid: yes_rate(evals, baseline, cid) for cid in defs}
    mode_rate = {cid: yes_rate(evals, mode, cid) for cid in defs}
    delta = {cid: mode_rate[cid] - base_rate[cid] for cid in defs}

    kg_ids = [c for c in defs if defs[c]["kg_relevant"]]
    total_gain = sum(delta.values())
    observed, p = concentration_p(delta, kg_ids, n_iter, random.Random(seed))
    expected = total_gain * len(kg_ids) / len(defs)

    dead = sorted(
        c for c in defs
        if base_rate[c] in (0.0, 1.0) and mode_rate[c] == base_rate[c]
    )

    lengths = {}
    for m in (baseline, mode):
        L = review_lengths(evals, m, reviews_dir)
        if L:
            lengths[m] = L

    return {
        "mode": mode,
        "n_prs": len([e for e in evals if e["mode"] == mode]),
        "base_rate": base_rate, "mode_rate": mode_rate, "delta": delta,
        "kg_ids": kg_ids,
        "gain_in_target": observed,
        "gain_total": total_gain,
        "gain_elsewhere": total_gain - observed,
        "gain_expected_if_diffuse": expected,
        "share": observed / total_gain if total_gain else float("nan"),
        "p_concentration": p,
        "dead_criteria": dead,
        "lengths": lengths,
    }


def emit(results: list[dict], defs: dict[str, dict], src: str,
         n_iter: int, seed: int) -> str:
    L: list[str] = []
    L.append("# Where the context effect lands — per-criterion decomposition\n")
    L.append(f"**Input:** `{src}`  ")
    L.append(f"**Script:** `scripts/analyze_criterion_concentration.py`  ")
    L.append(f"**Method:** majority-vote yes-rate per criterion per arm; "
             f"concentration tested by sampling random criterion subsets of the "
             f"same size (B={n_iter:,}, seed={seed}).\n")
    L.append("The concentration test permutes *criteria*, not PRs. It asks "
             "whether the advantage is localised where the mechanism predicts, "
             "which is a separate question from whether the aggregate "
             "difference is non-zero (`scripts/bootstrap_stats.py`).\n")

    L.append("## Summary\n")
    L.append("| Mode | n | gain in the 9 KG-relevant | gain in the other 16 | "
             "total | share in KG-relevant | expected if diffuse | p |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in results:
        L.append(
            f"| {r['mode']} | {r['n_prs']} | {r['gain_in_target']:+.3f} | "
            f"{r['gain_elsewhere']:+.3f} | {r['gain_total']:+.3f} | "
            f"{r['share']*100:.0f}% | {r['gain_expected_if_diffuse']:+.3f} | "
            f"{r['p_concentration']:.4f} |"
        )
    L.append("\nGains are in rubric points on the /25 scale, so the "
             "KG-relevant column is directly comparable to the /9 subscale "
             "difference reported in the bootstrap tables.\n")

    for r in results:
        m = r["mode"]
        L.append(f"\n## {m} vs baseline — per criterion\n")
        L.append("| ID | KG-relevant | Category | baseline | "
                 f"{m} | Δ |")
        L.append("|---|---|---|---:|---:|---:|")
        for c in sorted(defs, key=lambda x: r["delta"][x], reverse=True):
            L.append(
                f"| {c} | {'yes' if defs[c]['kg_relevant'] else '—'} | "
                f"{defs[c]['category']} | {r['base_rate'][c]*100:.1f}% | "
                f"{r['mode_rate'][c]*100:.1f}% | {r['delta'][c]*100:+.1f}pp |"
            )
        if r["dead_criteria"]:
            L.append(f"\n**Floor/ceiling criteria** (identical in both arms at "
                     f"0% or 100%, cannot register any difference): "
                     f"{len(r['dead_criteria'])} of {len(defs)} — "
                     f"{', '.join(r['dead_criteria'])}. These enter the /25 "
                     f"denominator while contributing no variance, so the total "
                     f"score understates any real effect by construction.")
        if r["lengths"]:
            L.append("\n**Review length** (characters):\n")
            L.append("| Arm | mean | median |")
            L.append("|---|---:|---:|")
            for arm, vals in r["lengths"].items():
                L.append(f"| {arm} | {statistics.mean(vals):.0f} | "
                         f"{statistics.median(vals):.0f} |")
            if len(r["lengths"]) == 2:
                a, b = list(r["lengths"])
                longer = sum(1 for x, y in zip(r["lengths"][a], r["lengths"][b])
                             if y > x)
                L.append(f"\n`{b}` is longer than `{a}` on {longer} of "
                         f"{len(r['lengths'][a])} PRs.")
    L.append("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp",
                    default="results/checklist_evaluation_llm_multi__v2.json")
    ap.add_argument("--out", default="results/CRITERION_CONCENTRATION.md")
    ap.add_argument("--json-out", default="results/CRITERION_CONCENTRATION.json",
                    help="Machine-readable copy of the same decomposition, so "
                         "figures plot the numbers the table reports rather "
                         "than recomputing them. Pass '' to skip.")
    ap.add_argument("--mode", action="append", default=None,
                    help="Treatment arm(s) to decompose. Default: kg, rag, hybrid.")
    ap.add_argument("--baseline", default="baseline")
    ap.add_argument("--reviews-dir", default="outputs/luca_prs_v2",
                    help="For the length comparison; pass '' to skip.")
    ap.add_argument("--n-iter", type=int, default=200_000)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    inp = Path(args.inp)
    if not inp.is_absolute():
        inp = REPO_ROOT / inp
    d = json.loads(inp.read_text())
    defs = {c["id"]: c for c in d["criteria_definitions"]}
    evals = d["evaluations"]

    reviews_dir = None
    if args.reviews_dir:
        reviews_dir = Path(args.reviews_dir)
        if not reviews_dir.is_absolute():
            reviews_dir = REPO_ROOT / reviews_dir
        if not reviews_dir.is_dir():
            reviews_dir = None

    present = {e["mode"] for e in evals}
    modes = args.mode or [m for m in ("kg", "rag", "hybrid") if m in present]
    modes = [m for m in modes if m in present]
    if not modes:
        print(f"no treatment arms found; file has {sorted(present)}")
        return 2

    results = [
        analyse_mode(evals, defs, m, args.baseline, args.n_iter, args.seed,
                     reviews_dir)
        for m in modes
    ]

    out = Path(args.out)
    if not out.is_absolute():
        out = REPO_ROOT / out
    out.write_text(emit(results, defs, args.inp, args.n_iter, args.seed))

    if args.json_out:
        jout = Path(args.json_out)
        if not jout.is_absolute():
            jout = REPO_ROOT / jout
        jout.write_text(json.dumps({
            "input": args.inp,
            "script": "scripts/analyze_criterion_concentration.py",
            "n_iter": args.n_iter,
            "seed": args.seed,
            "criteria": {c: {"kg_relevant": defs[c]["kg_relevant"],
                             "category": defs[c]["category"],
                             "text": defs[c].get("text", "")}
                         for c in defs},
            "modes": {r["mode"]: {k: v for k, v in r.items() if k != "lengths"}
                      | {"lengths": {a: {"mean": statistics.mean(v),
                                         "median": statistics.median(v),
                                         "n": len(v)}
                                     for a, v in r["lengths"].items()}}
                      for r in results},
        }, indent=1))

    for r in results:
        print(f"{r['mode']:<8} {r['gain_in_target']:+.3f} of "
              f"{r['gain_total']:+.3f} ({r['share']*100:.0f}%) in the "
              f"{len(r['kg_ids'])} KG-relevant criteria, "
              f"p={r['p_concentration']:.4f}")
    try:
        shown = out.relative_to(REPO_ROOT)
    except ValueError:
        shown = out
    print(f"\nwrote {shown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
