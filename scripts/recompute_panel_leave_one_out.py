#!/usr/bin/env python3
"""Recompute an Experiment 1 headline under judge sub-panels.

gpt-4o is both the review generator and one of the three judges, which is a
self-preference risk. Because `scripts/evaluate_reviews.py` retains every judge's
per-criterion verdict, the headline can be recomputed without that judge -- or
with any single judge alone -- at no API cost.

Projections reported per panel file:

  full            all judges, majority of three, ties to 0 (reproduces the
                  published numbers and therefore validates this script)
  only:<judge>    that judge's verdicts used directly
  drop:<judge>    the remaining two judges. A two-judge panel has no majority,
                  so both bounds are reported: `strict` requires both to agree
                  yes (the conservative analogue of ties-to-0) and `lenient`
                  requires either.

The self-preference question is answered by comparing `only:openai:gpt-4o`
against the other two single-judge projections, and by checking whether the
paired effect survives `drop:openai:gpt-4o`.

Aggregation is the only thing that varies; the CI, permutation and effect-size
machinery is imported from scripts/bootstrap_stats.py so it is identical to every
other number in the project.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts.bootstrap_stats import (  # noqa: E402
    bootstrap_mean_ci,
    paired_bootstrap_diff_ci,
    paired_permutation_p,
)

MODES = ("baseline", "kg", "rag", "hybrid")


def kg_relevant_ids(panel: dict) -> set[str]:
    defs = panel.get("criteria_definitions") or []
    ids = {c["id"] for c in defs if c.get("kg_relevant")}
    if not ids:
        raise SystemExit("panel file has no kg_relevant criterion flags")
    return ids


def project(panel: dict, judges: list[str], rule: str) -> dict:
    """Return {mode: {pr_id: (total, kgrel)}} under the given sub-panel and rule."""
    kg_ids = kg_relevant_ids(panel)
    need = len(judges) if rule == "strict" else (1 if rule == "lenient" else len(judges) // 2 + 1)
    out: dict[str, dict[int, tuple[int, int]]] = {m: {} for m in MODES}
    for ev in panel["evaluations"]:
        mode = ev["mode"]
        if mode not in out:
            continue
        votes = {pj["model"]: pj["scores"] for pj in ev.get("per_judge", [])}
        if not all(j in votes for j in judges):
            continue
        total = kgrel = 0
        for cid in votes[judges[0]]:
            yes = sum(1 for j in judges if votes[j].get(cid) == 1)
            score = 1 if yes >= need else 0
            total += score
            if cid in kg_ids:
                kgrel += score
        out[mode][ev["pr_id"]] = (total, kgrel)
    return out


def analyse(scores: dict, n_boot: int, n_perm: int, seed: int) -> dict:
    rng = random.Random(seed)
    res: dict = {"per_mode": {}, "paired": {}}
    for mode in MODES:
        if not scores[mode]:
            continue
        prs = sorted(scores[mode])
        for key, idx in (("total", 0), ("kgrel", 1)):
            xs = [scores[mode][p][idx] for p in prs]
            mean, lo, hi = bootstrap_mean_ci(xs, n_boot, rng)
            res["per_mode"].setdefault(mode, {})[key] = {
                "n": len(xs), "mean": mean, "lo": lo, "hi": hi
            }
    for mode in MODES:
        if mode == "baseline" or not scores[mode]:
            continue
        prs = sorted(set(scores["baseline"]) & set(scores[mode]))
        for key, idx in (("total", 0), ("kgrel", 1)):
            pairs = [(scores["baseline"][p][idx], scores[mode][p][idx]) for p in prs]
            d, lo, hi, sd = paired_bootstrap_diff_ci(pairs, n_boot, rng)
            p = paired_permutation_p(pairs, n_perm, rng)
            res["paired"].setdefault(mode, {})[key] = {
                "n": len(pairs), "delta": d, "lo": lo, "hi": hi, "p": p,
                "d_z": (d / sd) if sd else 0.0,
            }
    return res


def fmt(v: dict) -> str:
    return f"{v['delta']:+.2f} [{v['lo']:+.2f}, {v['hi']:+.2f}] | {v['p']:.3f} | {v['d_z']:+.2f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp",
                    default=str(REPO / "results" / "checklist_evaluation_llm_multi__v2.json"))
    ap.add_argument("--out-md", default=str(REPO / "results" / "JUDGE_LEAVE_ONE_OUT.md"))
    ap.add_argument("--out-json", default=str(REPO / "results" / "JUDGE_LEAVE_ONE_OUT.json"))
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--n-perm", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    panel = json.loads(Path(args.inp).read_text())
    judges = panel.get("panel", {}).get("judges") or []
    if not judges:
        raise SystemExit("panel file lists no judges")

    projections: list[tuple[str, list[str], str]] = [("full", list(judges), "majority")]
    for j in judges:
        projections.append((f"only:{j}", [j], "majority"))
    for j in judges:
        rest = [x for x in judges if x != j]
        projections.append((f"drop:{j} (strict)", rest, "strict"))
        projections.append((f"drop:{j} (lenient)", rest, "lenient"))

    results = {}
    for label, sub, rule in projections:
        results[label] = analyse(project(panel, sub, rule), args.n_boot, args.n_perm, args.seed)
        print(f"  computed {label}")

    lines = [
        "# Judge sub-panel recomputation — leave-one-out and single-judge",
        "",
        f"**Input:** `{Path(args.inp).relative_to(REPO)}`  ",
        f"**Judges:** {', '.join(judges)}  ",
        f"**Method:** percentile bootstrap (B={args.n_boot}), paired sign-flip "
        f"permutation (B={args.n_perm}), seed={args.seed}. Aggregation varies by row; "
        "everything else is `scripts/bootstrap_stats.py`.",
        "",
        "`full` reproduces the published headline and validates the recomputation. "
        "A two-judge panel has no majority, so `strict` (both judges yes) and "
        "`lenient` (either judge yes) bracket the answer.",
        "",
        "## Baseline mean and paired kg effect by projection",
        "",
        "| Projection | baseline /25 | kg Δ /25 [CI] | p | d_z | baseline /9 | kg Δ /9 [CI] | p | d_z |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, _, _ in projections:
        r = results[label]
        bt = r["per_mode"]["baseline"]["total"]
        bk = r["per_mode"]["baseline"]["kgrel"]
        kt = r["paired"]["kg"]["total"]
        kk = r["paired"]["kg"]["kgrel"]
        lines.append(
            f"| {label} | {bt['mean']:.2f} | {kt['delta']:+.2f} "
            f"[{kt['lo']:+.2f}, {kt['hi']:+.2f}] | {kt['p']:.3f} | {kt['d_z']:+.2f} "
            f"| {bk['mean']:.2f} | {kk['delta']:+.2f} "
            f"[{kk['lo']:+.2f}, {kk['hi']:+.2f}] | {kk['p']:.3f} | {kk['d_z']:+.2f} |"
        )

    lines += ["", "## All modes, per projection", ""]
    for label, _, _ in projections:
        r = results[label]
        lines += [f"### {label}", "",
                  "| Mode | total mean | Δ /25 [CI] | p | d_z | kgrel mean | Δ /9 [CI] | p | d_z |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for mode in MODES:
            pm = r["per_mode"].get(mode)
            if not pm:
                continue
            if mode == "baseline":
                lines.append(f"| {mode} | {pm['total']['mean']:.2f} | — | — | — "
                             f"| {pm['kgrel']['mean']:.2f} | — | — | — |")
            else:
                pt = r["paired"][mode]["total"]
                pk = r["paired"][mode]["kgrel"]
                lines.append(f"| {mode} | {pm['total']['mean']:.2f} | {fmt(pt)} "
                             f"| {pm['kgrel']['mean']:.2f} | {fmt(pk)} |")
        lines.append("")

    Path(args.out_md).write_text("\n".join(lines) + "\n")
    Path(args.out_json).write_text(json.dumps(
        {"input": args.inp, "judges": judges, "seed": args.seed, "projections": results}, indent=1))
    print(f"wrote {Path(args.out_md).relative_to(REPO)}")
    print(f"wrote {Path(args.out_json).relative_to(REPO)}")


if __name__ == "__main__":
    main()
