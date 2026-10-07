#!/usr/bin/env python3
"""Compare KG v3 (improved prompt) against KG v2 (current headline) and baseline.

Run AFTER:
  1. python3 scripts/regenerate_reviews_kg_v3.py
  2. python3 -m scripts.evaluate_reviews --outputs-dir outputs/luca_prs_v2_kg_v3 --output-suffix v2_kg_v3

This script:
  - Loads the v2 multi-judge evaluation (baseline + kg + rag + hybrid)
  - Loads the v3 kg evaluation
  - Computes paired deltas and bootstrap stats
  - Reports: does the prompt fix close the utilization gap?
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def load_scores(json_path, mode_filter=None):
    """Load per-PR scores from multi-judge JSON."""
    with open(json_path) as f:
        data = json.load(f)

    scores = {}
    for ev in data['evaluations']:
        pr_id = ev['pr_id']
        mode = ev['mode']
        if mode_filter and mode != mode_filter:
            continue
        scores[pr_id] = {
            'total': ev['total_score'],
            'kg_rel': ev['kg_relevant_score']
        }
    return scores


def bootstrap_compare(deltas, label, seed=2026, B=20000):
    """Bootstrap CI + permutation test."""
    import random
    random.seed(seed)
    n = len(deltas)
    obs = sum(deltas) / n

    boot = sorted([sum(deltas[random.randint(0, n-1)] for _ in range(n))/n for _ in range(10000)])
    ci_lo, ci_hi = boot[250], boot[9749]

    count = sum(1 for _ in range(B) if abs(sum(d * random.choice([-1, 1]) for d in deltas)/n) >= abs(obs))
    p = count / B

    var = sum((d - obs)**2 for d in deltas) / (n - 1) if n > 1 else 1
    dz = obs / var**0.5 if var > 0 else 0

    print(f"  {label}: Δ = {obs:+.3f} [{ci_lo:+.3f}, {ci_hi:+.3f}], p = {p:.4f}, d_z = {dz:+.2f} (n={n})")
    return obs, ci_lo, ci_hi, p, dz


def main():
    v2_path = Path("results/checklist_evaluation_llm_multi__v2.json")
    v3_path = Path("results/checklist_evaluation_llm_multi__v2_kg_v3.json")

    if not v2_path.exists():
        print(f"Missing: {v2_path}")
        sys.exit(1)
    if not v3_path.exists():
        print(f"Missing: {v3_path}")
        print("Run the evaluation first:")
        print("  python3 -m scripts.evaluate_reviews --outputs-dir outputs/luca_prs_v2_kg_v3 --output-suffix v2_kg_v3")
        sys.exit(1)

    # Load baseline scores from v2
    baseline = load_scores(v2_path, 'baseline')
    kg_v2 = load_scores(v2_path, 'kg')

    # Load kg_v3 scores
    kg_v3 = load_scores(v3_path, 'kg')

    # Common PRs
    common_prs = sorted(set(baseline.keys()) & set(kg_v2.keys()) & set(kg_v3.keys()))
    print(f"Common PRs: {len(common_prs)}")
    print()

    # KG v2 vs baseline
    print("=== KG v2 (current headline) vs Baseline ===")
    deltas_kg_rel = [kg_v2[pr]['kg_rel'] - baseline[pr]['kg_rel'] for pr in common_prs]
    deltas_total = [kg_v2[pr]['total'] - baseline[pr]['total'] for pr in common_prs]
    bootstrap_compare(deltas_kg_rel, "KG-rel")
    bootstrap_compare(deltas_total, "Total")

    print()
    print("=== KG v3 (improved prompt) vs Baseline ===")
    deltas_kg_rel_v3 = [kg_v3[pr]['kg_rel'] - baseline[pr]['kg_rel'] for pr in common_prs]
    deltas_total_v3 = [kg_v3[pr]['total'] - baseline[pr]['total'] for pr in common_prs]
    bootstrap_compare(deltas_kg_rel_v3, "KG-rel")
    bootstrap_compare(deltas_total_v3, "Total")

    print()
    print("=== KG v3 vs KG v2 (direct, same baseline) ===")
    deltas_v3_v2_kg = [kg_v3[pr]['kg_rel'] - kg_v2[pr]['kg_rel'] for pr in common_prs]
    deltas_v3_v2_t = [kg_v3[pr]['total'] - kg_v2[pr]['total'] for pr in common_prs]
    bootstrap_compare(deltas_v3_v2_kg, "KG-rel (v3 − v2)")
    bootstrap_compare(deltas_v3_v2_t, "Total (v3 − v2)")

    # Per-PR comparison
    print()
    print("=== Per-PR: KG v3 vs v2 ===")
    print(f"{'PR':>3} {'v2 KG-rel':>9} {'v3 KG-rel':>9} {'Δ':>4} {'v2 Total':>8} {'v3 Total':>8} {'Δ':>4}")
    print("-" * 55)
    v3_better = 0
    v3_worse = 0
    for pr in common_prs:
        v2_kg = kg_v2[pr]['kg_rel']
        v3_kg = kg_v3[pr]['kg_rel']
        d = v3_kg - v2_kg
        v2_t = kg_v2[pr]['total']
        v3_t = kg_v3[pr]['total']
        dt = v3_t - v2_t
        if d > 0: v3_better += 1
        elif d < 0: v3_worse += 1
        print(f"{pr:3d} {v2_kg:9d} {v3_kg:9d} {d:+3d}  {v2_t:7d} {v3_t:7d} {dt:+3d}")

    print()
    print(f"v3 better on KG-rel: {v3_better}/{len(common_prs)}")
    print(f"v3 worse on KG-rel: {v3_worse}/{len(common_prs)}")


if __name__ == "__main__":
    main()
