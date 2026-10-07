#!/usr/bin/env python3
"""Kruskal-Wallis omnibus + Bonferroni-corrected post-hoc on the multi-judge result.

Requested by supervisor (2026-06-19): an omnibus rank-based test across the four
review modes (baseline, kg, rag, hybrid), followed by Bonferroni-corrected
pairwise comparisons.

This script reports TWO families so the analysis is defensible either way:

  1. UNPAIRED (exactly what was asked): Kruskal-Wallis across the 4 modes, then
     Dunn's post-hoc with Bonferroni correction. Treats each (PR, mode) score as
     an observation. This is the textbook KW + post-hoc pipeline.

  2. PAIRED (design-matched): Friedman omnibus across the 4 modes (same PR is
     measured under every mode), then pairwise Wilcoxon signed-rank vs baseline
     with Bonferroni correction. This is the rank-based test that respects the
     repeated-measures structure of the study (the same 40 PRs go through every
     mode), and is the more powerful, more appropriate choice for this design.

Both are run on the total score (/25) and the KG-relevant subscale (/9).

Input schema: results/checklist_evaluation_llm_multi*.json with
  d["evaluations"] = [{pr_id, mode, total_score, kg_relevant_score, ...}, ...]

Usage:
  python3 scripts/kruskal_bonferroni.py \
    --in results/checklist_evaluation_llm_multi__v2.json \
    --out-json results/KRUSKAL_BONFERRONI_v2.json \
    --out-md   results/KRUSKAL_BONFERRONI_v2.md
"""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

from scipy import stats

MODES = ["baseline", "kg", "rag", "hybrid"]
METRICS = [("total_score", "Total /25"), ("kg_relevant_score", "KG-relevant /9")]


def load_scores(path: Path, metric: str) -> tuple[dict[str, list[float]], dict[int, dict[str, float]]]:
    """Return (per-mode score lists, per-PR {mode: score})."""
    evs = json.loads(path.read_text())["evaluations"]
    by_mode: dict[str, list[float]] = {m: [] for m in MODES}
    by_pr: dict[int, dict[str, float]] = {}
    for e in evs:
        m = e["mode"]
        if m not in by_mode:
            continue
        by_mode[m].append(float(e[metric]))
        by_pr.setdefault(e["pr_id"], {})[m] = float(e[metric])
    return by_mode, by_pr


def dunn_bonferroni(by_mode: dict[str, list[float]]) -> list[dict]:
    """Dunn's post-hoc test (pooled ranks, tie-corrected) with Bonferroni.

    z_ij = (Rbar_i - Rbar_j) / sqrt( sigma2 * (1/n_i + 1/n_j) )
    sigma2 = N(N+1)/12 - tie_correction, with
    tie_correction = sum_t (t^3 - t) / (12 (N - 1)).
    """
    groups = {m: by_mode[m] for m in MODES}
    pooled: list[float] = []
    labels: list[str] = []
    for m, xs in groups.items():
        pooled.extend(xs)
        labels.extend([m] * len(xs))
    N = len(pooled)
    ranks = stats.rankdata(pooled)
    # mean rank per group
    rank_by_group: dict[str, list[float]] = {m: [] for m in MODES}
    for lab, r in zip(labels, ranks):
        rank_by_group[lab].append(r)
    mean_rank = {m: sum(rs) / len(rs) for m, rs in rank_by_group.items()}
    n = {m: len(rs) for m, rs in rank_by_group.items()}
    # tie correction
    from collections import Counter
    tie_sum = sum((t ** 3 - t) for t in Counter(pooled).values() if t > 1)
    sigma2 = N * (N + 1) / 12.0 - tie_sum / (12.0 * (N - 1))
    pairs = list(combinations(MODES, 2))
    m_comp = len(pairs)
    out = []
    for a, b in pairs:
        se = (sigma2 * (1.0 / n[a] + 1.0 / n[b])) ** 0.5
        z = (mean_rank[a] - mean_rank[b]) / se if se > 0 else 0.0
        p = 2.0 * (1.0 - stats.norm.cdf(abs(z)))
        out.append({
            "pair": f"{a} vs {b}",
            "z": round(z, 3),
            "p_raw": round(p, 4),
            "p_bonferroni": round(min(1.0, p * m_comp), 4),
            "mean_rank_a": round(mean_rank[a], 1),
            "mean_rank_b": round(mean_rank[b], 1),
        })
    return out


def wilcoxon_vs_baseline_bonferroni(by_pr: dict[int, dict[str, float]]) -> list[dict]:
    """Paired Wilcoxon signed-rank, each mode vs baseline, Bonferroni over the family."""
    comp_modes = [m for m in MODES if m != "baseline"]
    m_comp = len(comp_modes)
    out = []
    for m in comp_modes:
        base, mod = [], []
        for pr, mm in by_pr.items():
            if "baseline" in mm and m in mm:
                base.append(mm["baseline"])
                mod.append(mm[m])
        diffs = [x - y for x, y in zip(mod, base)]
        nonzero = [d for d in diffs if d != 0]
        if not nonzero:
            out.append({"mode": m, "n_pairs": len(base), "note": "all differences zero",
                        "p_raw": 1.0, "p_bonferroni": 1.0})
            continue
        try:
            stat, p = stats.wilcoxon(mod, base, zero_method="wilcox", alternative="two-sided")
        except ValueError as exc:
            out.append({"mode": m, "n_pairs": len(base), "note": str(exc),
                        "p_raw": None, "p_bonferroni": None})
            continue
        out.append({
            "mode": f"{m} vs baseline",
            "n_pairs": len(base),
            "statistic": round(float(stat), 3),
            "median_diff": round(sorted(diffs)[len(diffs) // 2], 3),
            "p_raw": round(float(p), 4),
            "p_bonferroni": round(min(1.0, float(p) * m_comp), 4),
        })
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    path = Path(args.inp)
    result: dict = {"input": str(path), "modes": MODES, "metrics": {}}

    for key, label in METRICS:
        by_mode, by_pr = load_scores(path, key)
        # 1. Kruskal-Wallis omnibus (unpaired)
        h, p_kw = stats.kruskal(*[by_mode[m] for m in MODES])
        # 2. Friedman omnibus (paired) — align PRs present in all modes
        complete = [pr for pr, mm in by_pr.items() if all(m in mm for m in MODES)]
        fr_stat, p_fr = stats.friedmanchisquare(*[[by_pr[pr][m] for pr in complete] for m in MODES])
        result["metrics"][key] = {
            "label": label,
            "n_per_mode": {m: len(by_mode[m]) for m in MODES},
            "kruskal_wallis": {"H": round(float(h), 3), "p": round(float(p_kw), 4),
                               "df": len(MODES) - 1},
            "dunn_bonferroni": dunn_bonferroni(by_mode),
            "friedman": {"stat": round(float(fr_stat), 3), "p": round(float(p_fr), 4),
                         "df": len(MODES) - 1, "n_pairs": len(complete)},
            "wilcoxon_vs_baseline_bonferroni": wilcoxon_vs_baseline_bonferroni(by_pr),
        }

    Path(args.out_json).write_text(json.dumps(result, indent=2))

    # Markdown
    L: list[str] = []
    L.append(f"# Kruskal-Wallis + Bonferroni (and paired Friedman/Wilcoxon) — {path.stem}\n")
    L.append(f"**Input:** `{args.inp}`  ")
    L.append("**Families:** (1) Kruskal-Wallis omnibus + Dunn post-hoc, Bonferroni "
             "(unpaired, as requested); (2) Friedman omnibus + Wilcoxon signed-rank "
             "vs baseline, Bonferroni (paired, design-matched).\n")
    for key, label in METRICS:
        r = result["metrics"][key]
        L.append(f"## {label}\n")
        kw = r["kruskal_wallis"]
        L.append(f"**Kruskal-Wallis (unpaired omnibus):** H={kw['H']:.2f}, "
                 f"df={kw['df']}, p={kw['p']:.4f}  ")
        fr = r["friedman"]
        L.append(f"**Friedman (paired omnibus):** χ²={fr['stat']:.2f}, df={fr['df']}, "
                 f"p={fr['p']:.4f}, n={fr['n_pairs']}\n")
        L.append("### Dunn post-hoc (all pairs), Bonferroni-corrected\n")
        L.append("| Pair | z | p (raw) | p (Bonferroni) |")
        L.append("|---|---:|---:|---:|")
        for d in r["dunn_bonferroni"]:
            L.append(f"| {d['pair']} | {d['z']:+.2f} | {d['p_raw']:.4f} | {d['p_bonferroni']:.4f} |")
        L.append("\n### Wilcoxon signed-rank vs baseline (paired), Bonferroni-corrected\n")
        L.append("| Comparison | n pairs | statistic | median Δ | p (raw) | p (Bonferroni) |")
        L.append("|---|---:|---:|---:|---:|---:|")
        for w in r["wilcoxon_vs_baseline_bonferroni"]:
            if w.get("p_raw") is None:
                L.append(f"| {w.get('mode','?')} | {w.get('n_pairs','?')} | — | — | — | {w.get('note','')} |")
            else:
                L.append(f"| {w['mode']} | {w['n_pairs']} | {w.get('statistic','')} | "
                         f"{w.get('median_diff','')} | {w['p_raw']:.4f} | {w['p_bonferroni']:.4f} |")
        L.append("")
    L.append("## Interpretation key\n")
    L.append("- **Omnibus p < 0.05** → the four modes are not all equal; post-hoc tests localise the differences.")
    L.append("- **Bonferroni** multiplies each raw p by the number of comparisons in its family (capped at 1).")
    L.append("- The **paired** family (Friedman + Wilcoxon) respects that the same PRs pass through every mode "
             "and is the more appropriate test for this repeated-measures design; the **unpaired** "
             "Kruskal-Wallis/Dunn family is reported because it was requested and is more conservative.")
    L.append("")
    Path(args.out_md).write_text("\n".join(L))
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
