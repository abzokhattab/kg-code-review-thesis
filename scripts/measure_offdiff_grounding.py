#!/usr/bin/env python3
"""Measure how often each review mode cites OFF-DIFF structural facts.

A baseline review only sees the diff, so it can only name files inside it.
KG/hybrid reviews are given callers/dependents/nearest_tests that live
*outside* the diff. If the KG context is actually used, KG reviews should
mention off-diff file names that the diff never contains; baseline should not.

For each PR we build the set of distinctive file stems from the KG pack's
`nearest_tests` + `dependent_files` whose stem does NOT appear in the diff
(off-diff facts), then count how many each review mentions.

Usage:
    python3 scripts/measure_offdiff_grounding.py --out results/OFFDIFF_GROUNDING.md
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from collections import defaultdict

REPO = Path(__file__).resolve().parents[1]
PACKS = REPO / "data/luca_prs_v2"
REVIEWS = REPO / "outputs/luca_prs_v2"
MODES = ["baseline", "kg", "rag", "hybrid"]


def stems_from(items):
    out = set()
    for it in items or []:
        p = it.get("path", it) if isinstance(it, dict) else it
        stem = Path(str(p)).stem
        if len(stem) >= 5:  # distinctive enough to avoid spurious substring hits
            out.add(stem)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="results/OFFDIFF_GROUNDING.md")
    args = ap.parse_args()

    per_mode_hits = defaultdict(list)   # mode -> [off-diff facts cited per PR]
    per_mode_offdiff_avail = []
    detail = []

    packs = sorted(PACKS.glob("pr*_evidence.json"),
                   key=lambda p: int(re.search(r"pr(\d+)_", p.name).group(1)))
    for pk in packs:
        pr = int(re.search(r"pr(\d+)_", pk.name).group(1))
        d = json.loads(pk.read_text())
        diff = d.get("full_diff", "")
        kg_stems = stems_from(d.get("nearest_tests")) | stems_from(d.get("dependent_files"))
        offdiff = {s for s in kg_stems if s not in diff}
        if not offdiff:
            continue
        per_mode_offdiff_avail.append(len(offdiff))
        row = {"pr": pr, "offdiff_avail": len(offdiff)}
        for mode in MODES:
            rp = REVIEWS / f"pr{pr}_{mode}.md"
            if not rp.exists():
                row[mode] = None
                continue
            txt = rp.read_text()
            hits = sum(1 for s in offdiff if s in txt)
            per_mode_hits[mode].append(hits)
            row[mode] = hits
        detail.append(row)

    def avg(xs):
        xs = [x for x in xs if x is not None]
        return sum(xs) / len(xs) if xs else 0.0

    lines = []
    lines.append("# Off-diff structural grounding by mode\n")
    lines.append("How many KG-pack file stems that are **absent from the diff** each review "
                 "cites. Baseline cannot see these; a high count for KG/hybrid means the "
                 "structural context is genuinely used.\n")
    lines.append(f"PRs with ≥1 off-diff fact available: **{len(detail)}** "
                 f"(mean off-diff facts available per PR: {avg(per_mode_offdiff_avail):.1f}).\n")
    lines.append("| Mode | mean off-diff facts cited / PR | PRs with ≥1 |")
    lines.append("|---|---:|---:|")
    for mode in MODES:
        hits = per_mode_hits[mode]
        n_any = sum(1 for h in hits if h > 0)
        lines.append(f"| {mode} | {avg(hits):.2f} | {n_any}/{len(hits)} |")
    lines.append("")
    lines.append("## Per-PR detail (off-diff facts cited)\n")
    lines.append("| PR | off-diff avail | baseline | kg | rag | hybrid |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for r in detail:
        lines.append(f"| {r['pr']} | {r['offdiff_avail']} | "
                     f"{r.get('baseline')} | {r.get('kg')} | {r.get('rag')} | {r.get('hybrid')} |")
    lines.append("")

    (REPO / args.out).write_text("\n".join(lines))
    print("mean off-diff facts cited per PR:")
    for mode in MODES:
        print(f"  {mode:<9} {avg(per_mode_hits[mode]):.2f}  "
              f"(>=1 on {sum(1 for h in per_mode_hits[mode] if h>0)}/{len(per_mode_hits[mode])} PRs)")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
