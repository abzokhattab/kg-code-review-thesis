#!/usr/bin/env python3
"""Does the KG effect track the presence of graph edges, or the presence of a block?

This addresses RQ2.1 --- which parts of the context carry the effect --- using only
data already on disk, at no cost. It is the cheap half of the answer, and it is run
first because it tells you whether the expensive half is worth running.

The observation it exploits is a quirk of the deployed lexical builder. For 8 of the
40 pull requests, after the cohort filter in prnote/note.py::format_kg_context, the
rendered graph block contains no Related Tests line and no depends-on line: it is a
bare list of the changed files, which the diff already names. Those 8 pull requests
therefore passed through the full kg pipeline, received a block headed as repository
structure, and got no structural facts in it. They are a naturally occurring control
for the possibility that the effect comes from the framing rather than the content.

What this is not. This is an observational split, not an ablation. The 8 edge-free
pull requests are not a random subset: a change touching one file cannot have an
inter-file edge, so edge presence is entangled with change size, and any difference
between the groups is confounded with it. The script measures that confound rather
than waiting to be accused of it. Removing the confound requires holding the pull
request fixed and deleting one field at a time, which costs generation and judging;
this script is what justifies that spend, not a substitute for it.

Statistics. Per-PR paired differences (kg minus baseline) within each group, tested
by two-sided paired sign-flip permutation, with percentile bootstrap intervals. The
between-group contrast is tested by permuting group labels, since the two groups are
different pull requests and nothing pairs across them.

Input
  results/checklist_evaluation_llm_multi__v2.json   judged panel, 40 PRs x 4 arms
  data/luca_prs_v2/pr*_evidence.json               to re-render the graph block

Output
  results/KG_EDGE_PRESENCE.md / .json

Usage
  python3 scripts/decompose_kg_effect_by_edges.py
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from prnote.note import format_kg_context  # noqa: E402

PANEL = REPO_ROOT / "results" / "checklist_evaluation_llm_multi__v2.json"
PACKS = REPO_ROOT / "data" / "luca_prs_v2"
N_PERM, N_BOOT, SEED = 20000, 20000, 2026

TESTS_MARK = "**Related Tests:**"
DEPS_MARK = "**Files that depend on changes:**"


def perm_p_paired(s: np.ndarray, rng: np.random.Generator) -> float:
    obs = abs(s.mean())
    signs = rng.choice((-1.0, 1.0), size=(N_PERM, s.size))
    return float((np.sum(np.abs((signs * s).mean(axis=1)) >= obs - 1e-12) + 1)
                 / (N_PERM + 1))


def perm_p_groups(a: np.ndarray, b: np.ndarray,
                  rng: np.random.Generator) -> float:
    """Two-sided test that two independent groups have the same mean difference."""
    obs = abs(a.mean() - b.mean())
    pool = np.concatenate([a, b])
    na = a.size
    hits = 0
    for _ in range(N_PERM):
        rng.shuffle(pool)
        if abs(pool[:na].mean() - pool[na:].mean()) >= obs - 1e-12:
            hits += 1
    return (hits + 1) / (N_PERM + 1)


def boot_ci(s: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    means = np.array([rng.choice(s, size=s.size, replace=True).mean()
                      for _ in range(N_BOOT)])
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/KG_EDGE_PRESENCE")
    args = ap.parse_args()

    panel = json.loads(PANEL.read_text())
    tot: dict[tuple, float] = {}
    kgr: dict[tuple, float] = {}
    for e in panel["evaluations"]:
        tot[(e["pr_id"], e["mode"])] = e["total_score"]
        kgr[(e["pr_id"], e["mode"])] = e["kg_relevant_score"]
    prs = sorted({p for p, _ in tot})

    # Re-render the block rather than reading the raw fields, because the cohort
    # filter can drop a non-empty field before it reaches the prompt. What matters
    # is what the model saw.
    have_edges, n_files, composition = {}, {}, {}
    for n in prs:
        d = json.loads((PACKS / f"pr{n}_evidence.json").read_text())
        block = format_kg_context(d)
        t, dep = TESTS_MARK in block, DEPS_MARK in block
        have_edges[n] = t or dep
        n_files[n] = len(d.get("changed_files") or [])
        composition[n] = {"tests_line": t, "deps_line": dep,
                          "block_chars": len(block),
                          "changed_files": n_files[n]}

    rng = np.random.default_rng(SEED)
    result = {"meta": {"n_perm": N_PERM, "n_boot": N_BOOT, "seed": SEED,
                       "contrast": "kg minus baseline",
                       "grouping": "rendered graph block contains a tests or "
                                   "depends-on line, after the cohort filter"},
              "composition": composition, "scales": {}}

    for scale, d in (("total", tot), ("kgrel", kgr)):
        entry = {}
        groups = {}
        for lab, sel in (("with_edges", True), ("file_list_only", False)):
            arr = np.array([d[(p, "kg")] - d[(p, "baseline")]
                            for p in prs if have_edges[p] == sel], dtype=float)
            groups[lab] = arr
            lo, hi = boot_ci(arr, rng)
            entry[lab] = {"n": int(arr.size), "mean": float(arr.mean()),
                          "sd": float(arr.std(ddof=1)),
                          "d_z": float(arr.mean() / arr.std(ddof=1)),
                          "ci95": [lo, hi],
                          "p_paired": perm_p_paired(arr, rng)}
        allx = np.array([d[(p, "kg")] - d[(p, "baseline")] for p in prs],
                        dtype=float)
        entry["all"] = {"n": int(allx.size), "mean": float(allx.mean())}
        entry["between_groups"] = {
            "difference": float(groups["with_edges"].mean()
                                - groups["file_list_only"].mean()),
            "p": perm_p_groups(groups["with_edges"].copy(),
                               groups["file_list_only"].copy(), rng)}
        result["scales"][scale] = entry

    # The confound, stated as a number rather than as a worry.
    fw = [n_files[p] for p in prs if have_edges[p]]
    fo = [n_files[p] for p in prs if not have_edges[p]]
    result["confound_change_size"] = {
        "changed_files_median_with_edges": statistics.median(fw),
        "changed_files_median_file_list_only": statistics.median(fo),
        "note": "Edge presence is entangled with change size: a single-file change "
                "cannot have an inter-file edge. The group difference below is "
                "therefore not attributable to the edges alone."}

    (REPO_ROOT / (args.out + ".json")).write_text(
        json.dumps(result, indent=2) + "\n")

    L = ["# Does the KG effect track edges, or just the block?", "",
         "Contrast: kg minus baseline, per pull request. Grouping is by what the "
         "*rendered* graph block contained, after the cohort filter in "
         "`format_kg_context`, so it reflects what the model was shown.", "",
         "**Observational, not an ablation.** See the confound note at the end.", ""]
    for scale, lab in (("kgrel", "KG-relevant /9"), ("total", "Total /25")):
        s = result["scales"][scale]
        L += [f"## {lab}", "",
              "| Group | n | Δ | 95 % CI | d_z | p |", "|---|---|---|---|---|---|"]
        for k, name in (("with_edges", "Graph block has edges"),
                        ("file_list_only", "Graph block is a file list only")):
            g = s[k]
            L.append(f"| {name} | {g['n']} | {g['mean']:+.3f} | "
                     f"[{g['ci95'][0]:+.3f}, {g['ci95'][1]:+.3f}] | "
                     f"{g['d_z']:+.2f} | {g['p_paired']:.4f} |")
        L.append(f"| _all pull requests_ | {s['all']['n']} | "
                 f"{s['all']['mean']:+.3f} | | | |")
        bg = s["between_groups"]
        L += ["", f"Between-group difference: {bg['difference']:+.3f}, "
                  f"label-permutation p = {bg['p']:.4f}.", ""]
    c = result["confound_change_size"]
    L += ["## The confound", "",
          f"Median changed files: {c['changed_files_median_with_edges']:.0f} in the "
          f"group with edges against "
          f"{c['changed_files_median_file_list_only']:.0f} in the group without. "
          + c["note"], ""]
    (REPO_ROOT / (args.out + ".md")).write_text("\n".join(L) + "\n")

    for scale in ("kgrel", "total"):
        s = result["scales"][scale]
        print(f"{scale}: with edges n={s['with_edges']['n']} "
              f"{s['with_edges']['mean']:+.3f} (p={s['with_edges']['p_paired']:.4f}) | "
              f"file list only n={s['file_list_only']['n']} "
              f"{s['file_list_only']['mean']:+.3f} "
              f"(p={s['file_list_only']['p_paired']:.4f}) | "
              f"between p={s['between_groups']['p']:.4f}")
    print(f"confound: median changed files "
          f"{c['changed_files_median_with_edges']:.0f} vs "
          f"{c['changed_files_median_file_list_only']:.0f}")
    print(f"wrote {args.out}.md and .json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
