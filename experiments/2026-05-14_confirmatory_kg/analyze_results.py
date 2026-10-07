#!/usr/bin/env python3
"""
analyze_results.py — Statistical analysis for the confirmatory KG experiment.

Compares KG v3 vs baseline on the refined 5-item KG subscale {F3, F4, T3, M1, C2}.
Reports: bootstrap CI, permutation test, Cohen's d_z, and comparison to exploratory.

Input: experiments/2026-05-14_confirmatory_kg/evaluation_results.json
Output: experiments/2026-05-14_confirmatory_kg/RESULTS.md
"""
from __future__ import annotations

import json
import random
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
EVAL_PATH = SCRIPT_DIR / "evaluation_results.json"
RESULTS_PATH = SCRIPT_DIR / "RESULTS.md"

KG_REFINED = {'F3', 'F4', 'T3', 'M1', 'C2'}
ALL_CRITERIA = 25


def extract_scores(evaluations: list, mode: str) -> dict:
    scores = {}
    for ev in evaluations:
        if ev['mode'] != mode:
            continue
        pr_id = ev['pr_id']
        kg_rel = sum(1 for cs in ev['criteria_scores']
                     if cs['criterion_id'] in KG_REFINED and cs['score'] == 1)
        total = ev['total_score']
        scores[pr_id] = {'total': total, 'kg_rel': kg_rel}
    return scores


def bootstrap_ci(deltas: list, B: int = 10000, seed: int = 2026) -> tuple:
    random.seed(seed)
    n = len(deltas)
    boots = sorted([
        sum(deltas[random.randint(0, n-1)] for _ in range(n)) / n
        for _ in range(B)
    ])
    return boots[int(B * 0.025)], boots[int(B * 0.975)]


def permutation_test(deltas: list, B: int = 20000, seed: int = 2026) -> float:
    random.seed(seed)
    n = len(deltas)
    obs = abs(sum(deltas) / n)
    count = sum(
        1 for _ in range(B)
        if abs(sum(d * random.choice([-1, 1]) for d in deltas) / n) >= obs
    )
    return count / B


def cohen_dz(deltas: list) -> float:
    n = len(deltas)
    mean = sum(deltas) / n
    var = sum((d - mean) ** 2 for d in deltas) / (n - 1) if n > 1 else 1
    return mean / var ** 0.5 if var > 0 else 0


def main():
    if not EVAL_PATH.exists():
        # Try alternate name
        alt = SCRIPT_DIR / "checklist_evaluation_llm_multi__confirmatory.json"
        if alt.exists():
            data = json.loads(alt.read_text())
        else:
            print(f"ERROR: No evaluation results found at {EVAL_PATH}")
            print(f"  Run evaluation first, then copy results here as evaluation_results.json")
            return
    else:
        data = json.loads(EVAL_PATH.read_text())

    evaluations = data['evaluations']
    bl_scores = extract_scores(evaluations, 'baseline')
    kg_scores = extract_scores(evaluations, 'kg')

    common = sorted(set(bl_scores) & set(kg_scores))
    n = len(common)

    if n < 3:
        print(f"ERROR: Only {n} common PRs found. Need at least 3.")
        return

    # KG-relevant subscale
    kg_deltas = [kg_scores[pr]['kg_rel'] - bl_scores[pr]['kg_rel'] for pr in common]
    kg_mean = sum(kg_deltas) / n
    kg_ci = bootstrap_ci(kg_deltas)
    kg_p = permutation_test(kg_deltas)
    kg_dz = cohen_dz(kg_deltas)

    # Total score
    total_deltas = [kg_scores[pr]['total'] - bl_scores[pr]['total'] for pr in common]
    total_mean = sum(total_deltas) / n
    total_ci = bootstrap_ci(total_deltas)
    total_p = permutation_test(total_deltas)
    total_dz = cohen_dz(total_deltas)

    # Raw means
    bl_kg_mean = sum(bl_scores[pr]['kg_rel'] for pr in common) / n
    kg_kg_mean = sum(kg_scores[pr]['kg_rel'] for pr in common) / n
    bl_total_mean = sum(bl_scores[pr]['total'] for pr in common) / n
    kg_total_mean = sum(kg_scores[pr]['total'] for pr in common) / n

    # Per-PR detail
    pr_details = []
    for pr in common:
        pr_details.append({
            "pr": pr,
            "bl_kg": bl_scores[pr]['kg_rel'],
            "kg_kg": kg_scores[pr]['kg_rel'],
            "delta_kg": kg_scores[pr]['kg_rel'] - bl_scores[pr]['kg_rel'],
            "bl_total": bl_scores[pr]['total'],
            "kg_total": kg_scores[pr]['total'],
            "delta_total": kg_scores[pr]['total'] - bl_scores[pr]['total'],
        })

    # Write results
    sig_kg = "YES" if kg_p < 0.05 else "NO"
    sig_total = "YES" if total_p < 0.05 else "NO"

    report = f"""# Confirmatory KG Experiment — Results

**Date:** 2026-05-14
**Design:** {n} held-out PRs, baseline vs KG v3, 5-item refined subscale {{F3, F4, T3, M1, C2}}
**Pre-registered criterion:** KG-rel Delta > 0, p < 0.05

---

## Headline Result

| Metric | Delta | 95% CI | p | d_z | Significant? |
|---|---|---|---|---|---|
| **KG-relevant (5 items)** | {kg_mean:+.3f} | [{kg_ci[0]:+.3f}, {kg_ci[1]:+.3f}] | {kg_p:.4f} | {kg_dz:+.2f} | **{sig_kg}** |
| Total (25 items) | {total_mean:+.3f} | [{total_ci[0]:+.3f}, {total_ci[1]:+.3f}] | {total_p:.4f} | {total_dz:+.2f} | {sig_total} |

---

## Comparison to Exploratory (n=40)

| | Exploratory (n=40) | Confirmatory (n={n}) |
|---|---|---|
| KG-rel Delta | +0.60 | {kg_mean:+.3f} |
| KG-rel p | 0.007 | {kg_p:.4f} |
| KG-rel d_z | +0.47 | {kg_dz:+.2f} |
| Sample | Original 40 PRs | {n} held-out PRs |
| Prompt | KG v2 (old) | KG v3 (improved) |

---

## Raw Means

| Condition | KG-rel (of 5) | Total (of 25) |
|---|---|---|
| Baseline | {bl_kg_mean:.2f} ({bl_kg_mean/5*100:.0f}%) | {bl_total_mean:.2f} ({bl_total_mean/25*100:.0f}%) |
| KG v3 | {kg_kg_mean:.2f} ({kg_kg_mean/5*100:.0f}%) | {kg_total_mean:.2f} ({kg_total_mean/25*100:.0f}%) |

---

## Per-PR Detail

| PR | BL KG-rel | KG KG-rel | Delta | BL Total | KG Total | Delta |
|---|---|---|---|---|---|---|
"""
    for d in pr_details:
        report += f"| {d['pr']} | {d['bl_kg']} | {d['kg_kg']} | {d['delta_kg']:+d} | {d['bl_total']} | {d['kg_total']} | {d['delta_total']:+d} |\n"

    report += f"""
---

## Interpretation

"""
    if kg_p < 0.05:
        report += f"""The confirmatory experiment **replicates** the exploratory finding.
KG augmentation with the v3 prompt produces a significant improvement on KG-relevant
criteria (Delta = {kg_mean:+.2f}, p = {kg_p:.4f}, d_z = {kg_dz:+.2f}) on {n} held-out PRs
that were never part of the original 40-PR dataset.

This confirms that the KG effect generalizes beyond the training set and is not an
artifact of overfitting to the original PR selection.
"""
    else:
        report += f"""The confirmatory experiment does **not** reach significance at p < 0.05
(Delta = {kg_mean:+.2f}, p = {kg_p:.4f}, d_z = {kg_dz:+.2f}).

Possible explanations:
- Underpowered (n={n} may be too small for d_z < 0.5)
- The KG effect is real but smaller on this particular set of PRs
- The original finding was partially due to characteristics of the exploratory set

The direction of the effect ({'+' if kg_mean > 0 else '-'}) is {'consistent' if kg_mean > 0 else 'inconsistent'}
with the exploratory finding.
"""

    RESULTS_PATH.write_text(report)
    print(report)
    print(f"\nSaved to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
