#!/usr/bin/env python3
"""Compare parity-corrected clean-Joern run to the buggy original.

Runs against:
  - experiments/2026-06-11_joern_normal_prompt_parity/scores/  (parity, body included)
  - results/checklist_evaluation_llm_multi__v2.json (baseline w/ body)

Computes:
  - new d_z for KG-rel and total
  - per-PR delta shift (parity - bug)
  - per-criterion delta in the KG-rel set
  - signed rank test p-value approximation (Wilcoxon paired)

Writes: human_eval_v3_clean_2026-06-11/PARITY_RESULTS.md
"""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PARITY_SCORES = REPO / "experiments" / "2026-06-11_joern_normal_prompt_parity" / "scores"
BUG_SCORES = REPO / "experiments" / "2026-06-11_joern_normal_prompt" / "scores"
HEADLINE = REPO / "results" / "checklist_evaluation_llm_multi__v2.json"
OUT = REPO / "human_eval_v3_clean_2026-06-11" / "PARITY_RESULTS.md"

KG_IDS = {"F3", "F4", "T1", "T2", "T3", "M1", "M3", "C2", "Q2"}


def load_kg(score_dir: Path) -> dict[int, dict]:
    out = {}
    for f in sorted(score_dir.glob("pr*_kg.json")):
        d = json.loads(f.read_text())
        out[d["pr_id"]] = d
    return out


def load_baseline() -> dict[int, dict]:
    d = json.loads(HEADLINE.read_text())
    return {e["pr_id"]: e for e in d["evaluations"] if e["mode"] == "baseline"}


def dz_stats(deltas: list[int]) -> tuple[int, float, float, float]:
    n = len(deltas)
    if n == 0:
        return 0, 0, 0, 0
    m = sum(deltas) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in deltas) / max(1, n - 1))
    return n, m, sd, (m / sd if sd > 0 else 0)


def wilcoxon_signed_rank(deltas: list[int]) -> float | None:
    """Two-sided Wilcoxon p via normal approximation with tie variance correction.

    Matches scipy.stats.wilcoxon(method='approx', correction=False) to four
    decimals. The tie correction subtracts sum(t**3 - t)/48 from sigma**2,
    where t iterates over tie-group sizes. Without this correction, p-values
    on tied data are biased upward (too conservative)."""
    deltas = [d for d in deltas if d != 0]
    n = len(deltas)
    if n < 5:
        return None
    abs_d = sorted([(abs(d), 1 if d > 0 else -1) for d in deltas])
    ranks = []
    tie_groups = []
    i = 0
    while i < n:
        j = i
        while j < n and abs_d[j][0] == abs_d[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2
        for k in range(i, j):
            ranks.append((avg_rank, abs_d[k][1]))
        if j - i > 1:
            tie_groups.append(j - i)
        i = j
    W = sum(r * s for r, s in ranks if s > 0)
    mu = n * (n + 1) / 4
    sigma2 = n * (n + 1) * (2 * n + 1) / 24
    tie_correction = sum(t ** 3 - t for t in tie_groups) / 48.0
    sigma2 -= tie_correction
    if sigma2 <= 0:
        return None
    sigma = math.sqrt(sigma2)
    z = (W - mu) / sigma
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return p


def main():
    parity = load_kg(PARITY_SCORES)
    bug = load_kg(BUG_SCORES)
    baseline = load_baseline()

    parity_prs = sorted(parity)
    bug_prs = sorted(bug)
    print(f"Parity PRs: {len(parity_prs)} / {bug_prs and len(bug_prs)}")
    if not parity_prs:
        print("Parity run not yet started.")
        return

    common = sorted(set(parity) & set(baseline))
    print(f"Parity ∩ baseline: {len(common)}")

    deltas_kgrel = []
    deltas_total = []
    bug_deltas_kgrel = []
    bug_deltas_total = []
    for pr in common:
        deltas_kgrel.append(parity[pr]["kg_relevant_score"] - baseline[pr]["kg_relevant_score"])
        deltas_total.append(parity[pr]["total_score"] - baseline[pr]["total_score"])
        if pr in bug:
            bug_deltas_kgrel.append(bug[pr]["kg_relevant_score"] - baseline[pr]["kg_relevant_score"])
            bug_deltas_total.append(bug[pr]["total_score"] - baseline[pr]["total_score"])

    n_p, m_p, sd_p, dz_p = dz_stats(deltas_kgrel)
    n_pt, m_pt, sd_pt, dz_pt = dz_stats(deltas_total)
    n_b, m_b, sd_b, dz_b = dz_stats(bug_deltas_kgrel)
    n_bt, m_bt, sd_bt, dz_bt = dz_stats(bug_deltas_total)

    p_kg = wilcoxon_signed_rank(deltas_kgrel)
    p_tot = wilcoxon_signed_rank(deltas_total)

    lines = []
    P = lines.append
    P("# Parity-corrected clean-Joern results")
    P("")
    P(f"**Parity run scope:** n={n_p} PRs (all clean-Joern PRs that have parity scores).")
    P("")
    P("## Headline numbers")
    P("")
    P("| Metric | Buggy (no body) | Parity (body included) | Shift |")
    P("|---|---:|---:|---:|")
    if n_b > 0:
        P(f"| n | {n_b} | {n_p} | — |")
        P(f"| Mean Δ KG-rel | {m_b:+.3f} | {m_p:+.3f} | {m_p-m_b:+.3f} |")
        P(f"| SD Δ KG-rel | {sd_b:.3f} | {sd_p:.3f} | — |")
        P(f"| **d_z KG-rel** | **{dz_b:+.3f}** | **{dz_p:+.3f}** | **{dz_p-dz_b:+.3f}** |")
        P(f"| Mean Δ total | {m_bt:+.3f} | {m_pt:+.3f} | {m_pt-m_bt:+.3f} |")
        P(f"| **d_z total** | **{dz_bt:+.3f}** | **{dz_pt:+.3f}** | **{dz_pt-dz_bt:+.3f}** |")
    P("")
    if p_kg is not None:
        P(f"**Wilcoxon paired test p-value (KG-rel, parity vs baseline):** p = {p_kg:.4f}")
    if p_tot is not None:
        P(f"**Wilcoxon paired test p-value (total, parity vs baseline):** p = {p_tot:.4f}")
    P("")
    P("## Per-PR shifts (parity − bug)")
    P("")
    P("| PR | Buggy Δ KG-rel | Parity Δ KG-rel | Shift | Buggy Δ total | Parity Δ total | Shift |")
    P("|---:|---:|---:|---:|---:|---:|---:|")
    for pr in common:
        if pr not in bug:
            continue
        b_kg = bug[pr]["kg_relevant_score"] - baseline[pr]["kg_relevant_score"]
        p_kg2 = parity[pr]["kg_relevant_score"] - baseline[pr]["kg_relevant_score"]
        b_t = bug[pr]["total_score"] - baseline[pr]["total_score"]
        p_t = parity[pr]["total_score"] - baseline[pr]["total_score"]
        P(f"| {pr} | {b_kg:+d} | {p_kg2:+d} | {p_kg2-b_kg:+d} | {b_t:+d} | {p_t:+d} | {p_t-b_t:+d} |")
    P("")
    P("## Reading")
    P("")
    if dz_p > dz_b:
        P(f"The parity correction **raises** the headline KG-rel d_z from "
          f"{dz_b:+.3f} to {dz_p:+.3f}. This is the expected direction: the")
        P("bug penalised the joern arm by withholding the PR body.")
    elif dz_p < dz_b:
        P(f"The parity correction **lowers** the headline KG-rel d_z from "
          f"{dz_b:+.3f} to {dz_p:+.3f}. This is unexpected: it suggests the")
        P("PR body was actually *helping* the baseline arm more than the joern")
        P("arm in the original comparison. Investigate.")
    else:
        P(f"The parity correction does not move the headline (d_z stays at "
          f"{dz_p:+.3f}). The body had no detectable effect on the comparison.")
    P("")
    OUT.write_text("\n".join(lines))
    print(f"Wrote {OUT}")
    print(f"\nParity d_z KG-rel: {dz_p:+.3f}  (was {dz_b:+.3f})")
    print(f"Parity d_z total:  {dz_pt:+.3f}  (was {dz_bt:+.3f})")
    if p_kg is not None:
        print(f"Wilcoxon p (KG-rel): {p_kg:.4f}")


if __name__ == "__main__":
    main()
