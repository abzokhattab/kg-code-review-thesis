#!/usr/bin/env python3
"""Compare v1 (25-PR, contaminated) vs v2 (18-PR, cleaned) LLM-judge panel.

The v2 panel re-judges the same 18 PRs from v1 but with:
- recovered PR titles (no placeholders)
- recovered PR bodies (10/18 PRs had empty bodies in v1)
- untruncated 50 kB diffs (9/18 PRs were silently capped at 15 kB in v1)
- repaired RAG context (4/18 PRs had contaminated changed_files in v1)

This script reads both panel JSONs, restricts the v1 panel to the
18-PR subset shared with v2, and emits a side-by-side report of:

  1. Per-judge yes-rate by mode (v1 18-PR subset vs v2)
  2. By-mode mean total %  (majority-vote, paired by PR)
  3. By-mode mean KG-relevant %  (majority-vote, paired by PR)
  4. Δ-vs-baseline by mode (v1 vs v2, paired by PR within each version)
  5. Inter-judge Cohen's κ (v1 18-PR subset vs v2)

Usage:
    python3 dataset_v2/scripts/compare_v1_v2.py \
        --v1 results/checklist_evaluation_llm_multi.json \
        --v2 results/checklist_evaluation_llm_multi__v2.json \
        --out-md results/V1_VS_V2_COMPARISON.md \
        --out-json results/V1_VS_V2_COMPARISON.json
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

V2_PRS = {1, 2, 3, 6, 8, 9, 10, 12, 13, 14, 15, 18, 19, 20, 21, 22, 23, 24,
          27, 28, 29, 30, 31, 32, 33,                                    # +7 (2026-05-05)
          34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48}    # +15 (2026-05-12)
V1_OVERLAP = {1, 2, 3, 6, 8, 9, 10, 12, 13, 14, 15, 18, 19, 20, 21, 22, 23, 24}
MODES = ["baseline", "kg", "rag", "hybrid"]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def filter_to_v2_prs(evals: list[dict]) -> list[dict]:
    """Filter v1 to the 18-PR subset that v1 and v2 share.

    v2 (25 PRs) = the original 18 audited PRs + 7 added in the
    2026-05-05 expansion (PRs 27-33). PRs 27-33 don't exist in v1
    (they were added fresh from GitHub), so the apples-to-apples
    comparison can only happen on V1_OVERLAP = the 18 PRs both have.
    The full 25-PR v2 stats are reported separately.
    """
    return [e for e in evals if e["pr_id"] in V1_OVERLAP]


def by_mode_means(evals: list[dict]) -> dict[str, dict[str, float]]:
    """Mean total%, KG-relevant% per mode (majority-vote already in eval)."""
    out: dict[str, dict[str, float]] = {}
    for m in MODES:
        es = [e for e in evals if e["mode"] == m]
        if not es:
            out[m] = {"n": 0, "total_pct": 0.0, "kg_rel_pct": 0.0}
            continue
        total_pct = sum(e["percentage"] for e in es) / len(es)
        kg_pct = sum(e["kg_relevant_percentage"] for e in es) / len(es)
        out[m] = {
            "n": len(es),
            "total_pct": round(total_pct, 1),
            "kg_rel_pct": round(kg_pct, 1),
        }
    return out


def vs_baseline_paired(evals: list[dict]) -> dict[str, dict[str, float]]:
    """Per-PR paired diffs vs baseline, averaged."""
    by_pr_mode: dict[tuple[int, str], dict] = {}
    for e in evals:
        by_pr_mode[(e["pr_id"], e["mode"])] = e

    out: dict[str, dict[str, float]] = {}
    for m in [x for x in MODES if x != "baseline"]:
        diffs_total: list[float] = []
        diffs_kg: list[float] = []
        for pr_id in sorted({e["pr_id"] for e in evals}):
            base = by_pr_mode.get((pr_id, "baseline"))
            mode = by_pr_mode.get((pr_id, m))
            if base is None or mode is None:
                continue
            diffs_total.append(mode["percentage"] - base["percentage"])
            diffs_kg.append(mode["kg_relevant_percentage"] - base["kg_relevant_percentage"])
        n = len(diffs_total)
        out[m] = {
            "n_pairs": n,
            "total_diff_pp": round(sum(diffs_total) / n, 2) if n else 0.0,
            "kg_rel_diff_pp": round(sum(diffs_kg) / n, 2) if n else 0.0,
        }
    return out


def per_judge_yes_rate(evals: list[dict]) -> dict[str, dict[str, dict[str, float]]]:
    """{judge_model: {mode: {n_cells, yes, yes_rate}}}.

    `per_judge` in evaluate_reviews.py is a list of JudgeVerdict dicts with
    shape {model, scores: {criterion_id -> 0/1/-1}, evidence, error}. -1 marks
    a cell the judge failed to score (treated as an error, not as a 'no').
    """
    out: dict[str, dict[str, dict[str, float]]] = defaultdict(
        lambda: {m: {"n_cells": 0, "yes": 0, "errors": 0} for m in MODES}
    )
    for e in evals:
        for pj in e.get("per_judge") or []:
            judge_name = pj.get("model", "?")
            row = out[judge_name][e["mode"]]
            for cid, score in (pj.get("scores") or {}).items():
                if score in (0, 1):
                    row["n_cells"] += 1
                    row["yes"] += score
                else:
                    row["errors"] += 1
    rates: dict[str, dict[str, dict[str, float]]] = {}
    for judge, modes in out.items():
        rates[judge] = {}
        for m, row in modes.items():
            n = row["n_cells"]
            rates[judge][m] = {
                "n_cells": n,
                "yes": row["yes"],
                "errors": row["errors"],
                "yes_rate_pct": round(100 * row["yes"] / n, 1) if n else 0.0,
            }
    return rates


def cohen_kappa(judge_a: list[int | None], judge_b: list[int | None]) -> dict[str, Any]:
    """Standard 2x2 Cohen's κ over paired binary cells (skip None)."""
    a, b = [], []
    for x, y in zip(judge_a, judge_b):
        if x in (0, 1) and y in (0, 1):
            a.append(x)
            b.append(y)
    n = len(a)
    if n == 0:
        return {"n": 0, "agreement_pct": 0.0, "kappa": 0.0}
    yy = sum(1 for x, y in zip(a, b) if x == 1 and y == 1)
    nn = sum(1 for x, y in zip(a, b) if x == 0 and y == 0)
    yn = sum(1 for x, y in zip(a, b) if x == 1 and y == 0)
    ny = sum(1 for x, y in zip(a, b) if x == 0 and y == 1)
    po = (yy + nn) / n
    pa1 = (yy + yn) / n
    pa0 = 1 - pa1
    pb1 = (yy + ny) / n
    pb0 = 1 - pb1
    pe = pa1 * pb1 + pa0 * pb0
    kappa = 0.0 if pe == 1 else (po - pe) / (1 - pe)
    return {
        "n": n,
        "agreement_pct": round(100 * po, 1),
        "kappa": round(kappa, 3),
        "yes_yes": yy,
        "no_no": nn,
        "a_yes_b_no": yn,
        "a_no_b_yes": ny,
    }


def collect_judge_cells(evals: list[dict], judge: str) -> list[int | None]:
    """Flatten cells across all (pr, mode, criterion) for one judge.

    Iteration order is fixed by (pr_id, mode, criterion_id) so two judges'
    cell vectors line up cell-for-cell for Cohen's κ.
    """
    cells: list[int | None] = []
    for e in sorted(evals, key=lambda x: (x["pr_id"], x["mode"])):
        pj_match = next(
            (pj for pj in (e.get("per_judge") or []) if pj.get("model") == judge),
            None,
        )
        scores = (pj_match or {}).get("scores") or {}
        for cid in sorted(scores.keys()):
            v = scores[cid]
            cells.append(v if v in (0, 1) else None)
    return cells


def inter_judge_table(evals: list[dict], judges: list[str]) -> dict[str, dict[str, Any]]:
    cells_by_judge = {j: collect_judge_cells(evals, j) for j in judges}
    out: dict[str, dict[str, Any]] = {}
    for i, ja in enumerate(judges):
        for jb in judges[i + 1:]:
            out[f"{ja} vs {jb}"] = cohen_kappa(cells_by_judge[ja], cells_by_judge[jb])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--v1", default="results/checklist_evaluation_llm_multi.json")
    ap.add_argument("--v2", default="results/checklist_evaluation_llm_multi__v2.json")
    ap.add_argument("--out-md", default="results/V1_VS_V2_COMPARISON.md")
    ap.add_argument("--out-json", default="results/V1_VS_V2_COMPARISON.json")
    args = ap.parse_args()

    v1 = load(Path(args.v1))
    v2 = load(Path(args.v2))

    v1_evals_full = v1["evaluations"]
    v1_evals_18 = filter_to_v2_prs(v1_evals_full)  # the 18-PR overlap with v2
    v2_evals_full = v2["evaluations"]               # 25 PRs total (18 + 7 added)
    v2_evals_18 = [e for e in v2_evals_full if e["pr_id"] in V1_OVERLAP]

    judges = v1["metadata"]["judges"]
    v2_judges = v2["metadata"]["judges"]
    if set(judges) != set(v2_judges):
        print(f"WARNING: judge panels differ.\n  v1: {judges}\n  v2: {v2_judges}")

    report = {
        "v1_input": str(args.v1),
        "v2_input": str(args.v2),
        "v1_pr_set": sorted({e["pr_id"] for e in v1_evals_full}),
        "v2_pr_set": sorted({e["pr_id"] for e in v2_evals_full}),
        "v1_18pr_subset": sorted({e["pr_id"] for e in v1_evals_18}),
        "judges": judges,
        "by_mode_means": {
            "v1_25pr_full":   by_mode_means(v1_evals_full),
            "v1_18pr_subset": by_mode_means(v1_evals_18),
            "v2_25pr_full":   by_mode_means(v2_evals_full),
            "v2_18pr_subset": by_mode_means(v2_evals_18),
        },
        "vs_baseline_paired": {
            "v1_25pr_full":   vs_baseline_paired(v1_evals_full),
            "v1_18pr_subset": vs_baseline_paired(v1_evals_18),
            "v2_25pr_full":   vs_baseline_paired(v2_evals_full),
            "v2_18pr_subset": vs_baseline_paired(v2_evals_18),
        },
        "per_judge_yes_rate": {
            "v1_18pr_subset": per_judge_yes_rate(v1_evals_18),
            "v2_25pr_full":   per_judge_yes_rate(v2_evals_full),
        },
        "inter_judge_kappa": {
            "v1_18pr_subset": inter_judge_table(v1_evals_18, judges),
            "v2_25pr_full":   inter_judge_table(v2_evals_full, v2_judges),
        },
    }
    Path(args.out_json).write_text(json.dumps(report, indent=2))

    n_v2_full = len(report["v2_pr_set"])
    md: list[str] = []
    md.append("# v1 vs v2 LLM-judge comparison\n")
    md.append(
        f"_v1 (25 PRs, contaminated) vs v2 (now **{n_v2_full} PRs** after two "
        "expansions: 18 audit-survivor PRs + 7 fresh ones added by "
        "`dataset_v2/scripts/find_seven_more_prs.py` (2026-05-05) + 15 more "
        "added by `dataset_v2/scripts/find_fifteen_more_prs.py` (2026-05-12, "
        "with an added KG-richness criterion: ≥ 2 KG-parseable code files). "
        "The first three rows below are an apples-to-apples comparison on the "
        "18 PRs that exist in both datasets — those 18 are where v1 saw "
        "truncated diffs and empty PR bodies for 10 of them, and where v2 "
        f"sees the recovered, untruncated context. The fourth row is the "
        f"full {n_v2_full}-PR v2 headline, which is what the thesis's RQ2 "
        "sentence quotes._\n"
    )
    md.append(f"- **v1 panel:** `{args.v1}` ({len(v1_evals_full)} reviews, {len(report['v1_pr_set'])} PRs)")
    md.append(f"- **v1 → 18-PR overlap:** {len(v1_evals_18)} reviews, {len(report['v1_18pr_subset'])} PRs")
    md.append(f"- **v2 panel:** `{args.v2}` ({len(v2_evals_full)} reviews, {n_v2_full} PRs)")
    md.append(f"- **v2 → 18-PR overlap:** {len(v2_evals_18)} reviews (the same 18 PRs as v1's overlap)")
    md.append(f"- **Judges:** {', '.join(judges)}\n")

    rows = [
        ("v1 (25 PRs, contaminated)",     "v1_25pr_full"),
        ("v1 (18-PR overlap)",            "v1_18pr_subset"),
        ("v2 (18-PR overlap, cleaned)",   "v2_18pr_subset"),
        (f"**v2 ({n_v2_full} PRs, cleaned + expansions) — headline**", "v2_25pr_full"),
    ]

    md.append("## 1. By-mode mean coverage (% of 25-criterion checklist marked yes by majority vote)\n")
    md.append("| Dataset | Baseline | KG | RAG | Hybrid |")
    md.append("|---|---:|---:|---:|---:|")
    for label, key in rows:
        d = report["by_mode_means"][key]
        md.append(
            f"| {label} | {d['baseline']['total_pct']:.1f}% | {d['kg']['total_pct']:.1f}% | "
            f"{d['rag']['total_pct']:.1f}% | {d['hybrid']['total_pct']:.1f}% |"
        )

    md.append("\n## 2. KG-relevant coverage (% of 9 KG-relevant criteria marked yes)\n")
    md.append("| Dataset | Baseline | KG | RAG | Hybrid |")
    md.append("|---|---:|---:|---:|---:|")
    for label, key in rows:
        d = report["by_mode_means"][key]
        md.append(
            f"| {label} | {d['baseline']['kg_rel_pct']:.1f}% | {d['kg']['kg_rel_pct']:.1f}% | "
            f"{d['rag']['kg_rel_pct']:.1f}% | {d['hybrid']['kg_rel_pct']:.1f}% |"
        )

    md.append("\n## 3. Δ vs baseline (paired per-PR, percentage points)\n")
    md.append("### Total coverage Δ\n")
    md.append("| Dataset | KG − base | RAG − base | Hybrid − base |")
    md.append("|---|---:|---:|---:|")
    for label, key in rows:
        d = report["vs_baseline_paired"][key]
        md.append(
            f"| {label} | {d['kg']['total_diff_pp']:+.2f} | "
            f"{d['rag']['total_diff_pp']:+.2f} | {d['hybrid']['total_diff_pp']:+.2f} |"
        )

    md.append("\n### KG-relevant Δ\n")
    md.append("| Dataset | KG − base | RAG − base | Hybrid − base |")
    md.append("|---|---:|---:|---:|")
    for label, key in rows:
        d = report["vs_baseline_paired"][key]
        md.append(
            f"| {label} | {d['kg']['kg_rel_diff_pp']:+.2f} | "
            f"{d['rag']['kg_rel_diff_pp']:+.2f} | {d['hybrid']['kg_rel_diff_pp']:+.2f} |"
        )

    md.append("\n## 4. Per-judge yes-rate by mode (raw cells, before majority vote)\n")
    for version_label, key in [
        ("v1 (18-PR overlap)",                   "v1_18pr_subset"),
        (f"v2 ({n_v2_full} PRs, cleaned)",       "v2_25pr_full"),
    ]:
        md.append(f"\n### {version_label}\n")
        md.append("| Judge | Baseline | KG | RAG | Hybrid |")
        md.append("|---|---:|---:|---:|---:|")
        for judge in judges:
            row = report["per_judge_yes_rate"][key].get(judge, {})
            cells = [row.get(m, {}).get("yes_rate_pct", float("nan")) for m in MODES]
            md.append(f"| {judge} | " + " | ".join(f"{c:.1f}%" for c in cells) + " |")

    md.append(f"\n## 5. Inter-judge agreement (Cohen's κ)\n")
    md.append(f"| Judge pair | v1 (18-PR overlap) | v2 ({n_v2_full} PRs, cleaned + expansions) | Δκ |")
    md.append("|---|---:|---:|---:|")
    for pair in report["inter_judge_kappa"]["v1_18pr_subset"]:
        v1k = report["inter_judge_kappa"]["v1_18pr_subset"][pair]["kappa"]
        v2k = report["inter_judge_kappa"]["v2_25pr_full"].get(pair, {}).get("kappa", float("nan"))
        md.append(f"| {pair} | {v1k:.3f} | {v2k:.3f} | {v2k - v1k:+.3f} |")

    md.append("\n## How to read this report\n")
    md.append(
        "- **Section 1–2:** Headline coverage by mode. The v1-subset row controls for "
        "PR composition; the v2 row adds the data-quality fix on top. The diff between "
        "those two rows is the contribution of cleaning the data."
    )
    md.append(
        "- **Section 3:** The directional question (does extra context help?). "
        "If a positive Δ in v1 disappears in v2, the v1 effect was a data artefact. "
        "If it survives or grows, the effect is real."
    )
    md.append(
        "- **Section 4:** Each judge's individual yes-rate. Diverging columns "
        "across judges hint at hard-to-judge items; they don't directly affect the "
        "majority-vote totals in §1–3."
    )
    md.append(
        "- **Section 5:** Whether judges agree more on cleaner data. "
        "Δκ > 0 means the v2 inputs are easier to judge consistently."
    )
    md.append(
        "\n_Run bootstrap CIs and paired permutation tests on the v2 effects with:_  \n"
        "`python3 scripts/bootstrap_stats.py --in results/checklist_evaluation_llm_multi__v2.json "
        "--out-json results/BOOTSTRAP_STATS_v2.json --out-md results/BOOTSTRAP_STATS_v2.md --label 'v2 (18 PRs, cleaned)'`"
    )

    Path(args.out_md).write_text("\n".join(md))
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
