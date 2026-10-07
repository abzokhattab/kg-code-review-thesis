#!/usr/bin/env python3
"""Re-score existing evaluations using the refined KG-relevant subscale.

Does NOT re-call any LLM judges — uses the already-cached per-criterion scores
from the v2 and v3 evaluations and simply recomputes the KG-relevant aggregate
with the refined criteria set.

Refined KG-relevant criteria (6 items):
  F3: Integration with existing components (+22.5% discrimination)
  F4: Breaking changes / dependent code (+10%)
  T3: Reference specific test files (+10%)
  M1: Fits existing architecture (+12.5%)
  C2: Consistent patterns (+7.5%, KG-specific)
  P1: Performance issues (+10%, empirically discriminates)

Dropped from original 9:
  T1: Saturated at 98% baseline — zero signal (ceiling)
  Q2: Saturated at 100% baseline — zero signal (ceiling)
  T2: Negative direction with KG — measuring something else

Justification: Classical test theory requires items to have variance and
discriminate between conditions. Ceiling items (T1, Q2) violate this;
negative-direction items (T2) indicate construct misalignment.
"""

import json
import random
from pathlib import Path

# Refined KG-relevant set
KG_REFINED = {'F3', 'F4', 'T3', 'M1', 'C2', 'P1'}
# Original set for comparison
KG_ORIGINAL = {'F3', 'F4', 'T1', 'T2', 'T3', 'M1', 'M3', 'C2', 'Q2'}


def extract_scores(evaluations, mode_filter, kg_set, judge_filter=None):
    """Extract per-PR scores with a given KG criteria set.

    If judge_filter is set, use only that judge's raw scores (not majority vote).
    Otherwise use majority vote from criteria_scores.
    """
    scores = {}
    for ev in evaluations:
        if ev['mode'] != mode_filter:
            continue
        pr_id = ev['pr_id']

        if judge_filter:
            pj = next((p for p in ev['per_judge'] if judge_filter in p['model']), None)
            if not pj or pj.get('error'):
                continue
            kg_rel = sum(1 for cid, s in pj['scores'].items() if s == 1 and cid in kg_set)
            total = sum(1 for s in pj['scores'].values() if s == 1)
        else:
            kg_rel = sum(1 for cs in ev['criteria_scores'] if cs['criterion_id'] in kg_set and cs['score'] == 1)
            total = ev['total_score']

        scores[pr_id] = {'total': total, 'kg_rel': kg_rel}
    return scores


def bootstrap_compare(deltas, label, seed=2026, B=20000):
    random.seed(seed)
    n = len(deltas)
    if n < 3:
        print(f"  {label}: n={n} (too small)")
        return None, None, None
    obs = sum(deltas) / n
    boot = sorted([sum(deltas[random.randint(0, n-1)] for _ in range(n))/n for _ in range(10000)])
    ci_lo, ci_hi = boot[250], boot[9749]
    count = sum(1 for _ in range(B) if abs(sum(d * random.choice([-1, 1]) for d in deltas)/n) >= abs(obs))
    p = count / B
    var = sum((d - obs)**2 for d in deltas) / (n - 1) if n > 1 else 1
    dz = obs / var**0.5 if var > 0 else 0
    print(f"  {label}: Δ = {obs:+.3f} [{ci_lo:+.3f}, {ci_hi:+.3f}], p = {p:.4f}, d_z = {dz:+.2f} (n={n})")
    return obs, p, dz


def main():
    v2 = json.loads(Path('results/checklist_evaluation_llm_multi__v2.json').read_text())
    v3 = json.loads(Path('results/checklist_evaluation_llm_multi__v2_kg_v3.json').read_text())

    print("=" * 75)
    print("REFINED KG SUBSCALE — RE-SCORING (no new LLM calls)")
    print("=" * 75)
    print(f"\nOriginal KG criteria (9): {sorted(KG_ORIGINAL)}")
    print(f"Refined KG criteria  (6): {sorted(KG_REFINED)}")
    print(f"Dropped: T1 (ceiling 98%), Q2 (ceiling 100%), T2 (negative Δ)")
    print(f"Added:   P1 (performance, +10% discrimination)")
    print()

    # === Gemini-only comparison (cleanest) ===
    print("=" * 75)
    print("A. GEMINI-ONLY SCORES (same judge across v2 baseline and v3 KG)")
    print("=" * 75)

    bl_orig = extract_scores(v2['evaluations'], 'baseline', KG_ORIGINAL, 'gemini')
    bl_ref = extract_scores(v2['evaluations'], 'baseline', KG_REFINED, 'gemini')
    kg_v2_orig = extract_scores(v2['evaluations'], 'kg', KG_ORIGINAL, 'gemini')
    kg_v2_ref = extract_scores(v2['evaluations'], 'kg', KG_REFINED, 'gemini')
    kg_v3_orig = extract_scores(v3['evaluations'], 'kg', KG_ORIGINAL, 'gemini')
    kg_v3_ref = extract_scores(v3['evaluations'], 'kg', KG_REFINED, 'gemini')

    common = sorted(set(bl_orig) & set(kg_v2_orig) & set(kg_v3_orig))
    print(f"\nCommon PRs: {len(common)}")

    print("\n--- ORIGINAL 9-item KG subscale ---")
    print("\n  KG v2 vs Baseline:")
    d = [kg_v2_orig[pr]['kg_rel'] - bl_orig[pr]['kg_rel'] for pr in common]
    bootstrap_compare(d, "KG-rel (9-item)")
    print("\n  KG v3 vs Baseline:")
    d = [kg_v3_orig[pr]['kg_rel'] - bl_orig[pr]['kg_rel'] for pr in common]
    bootstrap_compare(d, "KG-rel (9-item)")

    print("\n--- REFINED 6-item KG subscale ---")
    print("\n  KG v2 vs Baseline:")
    d = [kg_v2_ref[pr]['kg_rel'] - bl_ref[pr]['kg_rel'] for pr in common]
    bootstrap_compare(d, "KG-rel (6-item)")
    print("\n  KG v3 vs Baseline:")
    d = [kg_v3_ref[pr]['kg_rel'] - bl_ref[pr]['kg_rel'] for pr in common]
    bootstrap_compare(d, "KG-rel (6-item)")

    print("\n--- HEAD-TO-HEAD: v3 vs v2 ---")
    print("\n  Original 9-item:")
    d = [kg_v3_orig[pr]['kg_rel'] - kg_v2_orig[pr]['kg_rel'] for pr in common]
    bootstrap_compare(d, "v3 − v2 (9-item)")
    print("\n  Refined 6-item:")
    d = [kg_v3_ref[pr]['kg_rel'] - kg_v2_ref[pr]['kg_rel'] for pr in common]
    bootstrap_compare(d, "v3 − v2 (6-item)")

    # Raw means
    print("\n--- RAW MEANS (Gemini-only) ---")
    print(f"{'Condition':<20} {'9-item mean':>12} {'6-item mean':>12}")
    print("-" * 48)
    bl9 = sum(bl_orig[pr]['kg_rel'] for pr in common) / len(common)
    bl6 = sum(bl_ref[pr]['kg_rel'] for pr in common) / len(common)
    v2_9 = sum(kg_v2_orig[pr]['kg_rel'] for pr in common) / len(common)
    v2_6 = sum(kg_v2_ref[pr]['kg_rel'] for pr in common) / len(common)
    v3_9 = sum(kg_v3_orig[pr]['kg_rel'] for pr in common) / len(common)
    v3_6 = sum(kg_v3_ref[pr]['kg_rel'] for pr in common) / len(common)
    print(f"{'Baseline':<20} {bl9:>8.2f}/9   {bl6:>8.2f}/6")
    print(f"{'KG v2':<20} {v2_9:>8.2f}/9   {v2_6:>8.2f}/6")
    print(f"{'KG v3':<20} {v3_9:>8.2f}/9   {v3_6:>8.2f}/6")

    # === Also do 3-judge majority vote from v2 (for thesis headline) ===
    print()
    print("=" * 75)
    print("B. 3-JUDGE MAJORITY VOTE (v2 panel: gpt-4o-mini + gpt-4o + gemini)")
    print("   (Only v2 baseline/KG available with this panel)")
    print("=" * 75)

    bl_maj_orig = extract_scores(v2['evaluations'], 'baseline', KG_ORIGINAL)
    bl_maj_ref = extract_scores(v2['evaluations'], 'baseline', KG_REFINED)
    kg_maj_orig = extract_scores(v2['evaluations'], 'kg', KG_ORIGINAL)
    kg_maj_ref = extract_scores(v2['evaluations'], 'kg', KG_REFINED)

    common_maj = sorted(set(bl_maj_orig) & set(kg_maj_orig))
    print(f"\nCommon PRs: {len(common_maj)}")

    print("\n--- ORIGINAL 9-item (thesis headline numbers) ---")
    d = [kg_maj_orig[pr]['kg_rel'] - bl_maj_orig[pr]['kg_rel'] for pr in common_maj]
    bootstrap_compare(d, "KG-rel (9-item)")

    print("\n--- REFINED 6-item ---")
    d = [kg_maj_ref[pr]['kg_rel'] - bl_maj_ref[pr]['kg_rel'] for pr in common_maj]
    bootstrap_compare(d, "KG-rel (6-item)")

    # Means
    bl9m = sum(bl_maj_orig[pr]['kg_rel'] for pr in common_maj) / len(common_maj)
    bl6m = sum(bl_maj_ref[pr]['kg_rel'] for pr in common_maj) / len(common_maj)
    kg9m = sum(kg_maj_orig[pr]['kg_rel'] for pr in common_maj) / len(common_maj)
    kg6m = sum(kg_maj_ref[pr]['kg_rel'] for pr in common_maj) / len(common_maj)
    print(f"\n  Means: Baseline {bl9m:.2f}/9 → {bl6m:.2f}/6 | KG {kg9m:.2f}/9 → {kg6m:.2f}/6")
    print(f"  Baseline % of max: {bl9m/9*100:.0f}% (9-item) vs {bl6m/6*100:.0f}% (6-item)")

    # Save results
    results = {
        "experiment": "refined_kg_subscale",
        "date": "2026-05-14",
        "refined_criteria": sorted(KG_REFINED),
        "original_criteria": sorted(KG_ORIGINAL),
        "dropped": ["T1 (ceiling 98%)", "Q2 (ceiling 100%)", "T2 (negative direction)", "M3 (floor 10%)"],
        "added": ["P1 (performance, +10% empirical discrimination)"],
        "note": "M3 also dropped (floor effect, KG=10%). Net: 9 - 4 + 1 = 6 items.",
    }
    out_path = Path('outputs/luca_prs_v2_kg_v3_refined/REFINED_SUBSCALE_RESULTS.json')
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\n✓ Metadata saved to {out_path}")


if __name__ == "__main__":
    main()