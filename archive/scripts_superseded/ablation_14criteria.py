#!/usr/bin/env python3
"""
Re-evaluate ablated KG reviews with the 14-criterion rubric (GPT-4.1-mini).

Reads the existing ablated review .md files from outputs/ablation/,
evaluates them with the same 14-criterion rubric used in Run 2,
then compares against full_kg scores from Run 2 to compute per-criterion deltas.
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.evaluate_14criteria import (
    CRITERIA_14, evaluate_review, load_review, load_pr_context, DEFAULT_MODEL
)

ABLATION_DIR = Path("outputs/ablation")
RESULTS_DIR = Path("results/run2_14criteria")


def run_ablation_eval(model: str = DEFAULT_MODEL):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    review_files = sorted(ABLATION_DIR.glob("pr*_kg_*.md"))
    print(f"Found {len(review_files)} ablated reviews to evaluate")
    print(f"Model: {model}\n")

    evaluations = []
    for i, rf in enumerate(review_files):
        match = re.match(r'pr(\d+)_(kg_\w+)\.md', rf.name)
        if not match:
            continue
        pr_id = int(match.group(1))
        config = match.group(2)

        print(f"[{i+1}/{len(review_files)}] PR #{pr_id} - {config}...", end=" ", flush=True)

        review = load_review(str(rf))
        pr_ctx = load_pr_context(pr_id)

        for attempt in range(3):
            scores = evaluate_review(review, pr_ctx, model)
            total = sum(s.score for s in scores)
            if total > 0 or attempt == 2:
                break
            print(f"retry...", end=" ", flush=True)

        pct = round(total / len(CRITERIA_14) * 100, 1)
        print(f"{total}/{len(CRITERIA_14)} ({pct}%)")

        evaluations.append({
            'pr_id': pr_id,
            'config': config,
            'total_score': total,
            'max_score': len(CRITERIA_14),
            'percentage': pct,
            'criteria_scores': [{'criterion_id': s.criterion_id, 'score': s.score, 'evidence': s.evidence} for s in scores]
        })

    # Save raw ablation results
    out = {
        'metadata': {
            'run': 'ablation_14criteria',
            'model': model,
            'timestamp': datetime.now().isoformat(),
            'criteria_count': len(CRITERIA_14)
        },
        'evaluations': evaluations
    }
    raw_path = RESULTS_DIR / 'ablation_14criteria.json'
    with open(raw_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\n✓ Raw results saved to {raw_path}")

    # Load full_kg scores from Run 2
    with open(RESULTS_DIR / 'evaluation_14criteria.json') as f:
        run2 = json.load(f)

    full_kg = {}
    for ev in run2['evaluations']:
        if ev['mode'] == 'kg':
            full_kg[ev['pr_id']] = {cs['criterion_id']: cs['score'] for cs in ev['criteria_scores']}

    # Compute deltas per config per criterion
    configs = sorted(set(e['config'] for e in evaluations))
    criteria_ids = [c.id for c in CRITERIA_14]

    print(f"\n{'='*80}")
    print("ABLATION RESULTS — 14 CRITERIA (per-criterion delta: full_kg - ablated)")
    print(f"{'='*80}")

    config_deltas = {}
    for config in configs:
        config_evals = [e for e in evaluations if e['config'] == config]
        pr_ids = [e['pr_id'] for e in config_evals]

        crit_deltas = {}
        for cid in criteria_ids:
            deltas = []
            for e in config_evals:
                pid = e['pr_id']
                if pid not in full_kg:
                    continue
                abl_score = next((cs['score'] for cs in e['criteria_scores'] if cs['criterion_id'] == cid), 0)
                full_score = full_kg[pid].get(cid, 0)
                deltas.append(full_score - abl_score)
            crit_deltas[cid] = sum(deltas) / len(deltas) if deltas else 0

        config_deltas[config] = crit_deltas

        # Overall drop
        full_avg = sum(full_kg[e['pr_id']].get(cid, 0) for e in config_evals for cid in criteria_ids) / (len(config_evals) * len(criteria_ids)) * 100
        abl_avg = sum(e['percentage'] for e in config_evals) / len(config_evals)
        drop = full_avg - abl_avg

        print(f"\n  {config} ({len(config_evals)} PRs): full_kg={full_avg:.1f}% → ablated={abl_avg:.1f}% (drop={drop:+.1f}pp)")

    # Per-criterion impact table
    print(f"\n{'Crit':>6} | ", end="")
    for config in configs:
        print(f"{config:>14} | ", end="")
    print(f"{'Σ|delta|':>8} | {'Σ(positive)':>11}")
    print("-" * (8 + 17 * len(configs) + 25))

    crit_sensitivity = []
    for cid in criteria_ids:
        total_abs = sum(abs(config_deltas[c][cid]) for c in configs)
        total_pos = sum(max(0, config_deltas[c][cid]) for c in configs)
        crit_sensitivity.append((cid, total_abs, total_pos, {c: config_deltas[c][cid] for c in configs}))

    crit_sensitivity.sort(key=lambda x: -x[1])

    for cid, ta, tp, deltas in crit_sensitivity:
        print(f"  {cid:>4} | ", end="")
        for config in configs:
            d = deltas[config]
            print(f"{d:>+13.3f} | ", end="")
        print(f"{ta:>8.3f} | {tp:>11.3f}")

    # Top 5 by ablation sensitivity
    abl_top5 = [c[0] for c in crit_sensitivity[:5]]
    print(f"\n  Ablation top 5 (by Σ|delta|): {abl_top5}")

    # Compare with spread and KG-delta from Run 2
    with open(RESULTS_DIR / 'analysis_14criteria.json') as f:
        analysis = json.load(f)
    spread_top5 = analysis['top5_by_spread']
    kg_top5 = analysis['top5_by_kg_delta']

    print(f"\n{'='*80}")
    print("FINAL COMPARISON — ALL 3 METHODS ON SAME DATA (14 crit, GPT-4.1-mini)")
    print(f"{'='*80}")
    print(f"\n  Spread top 5:    {spread_top5}")
    print(f"  KG-delta top 5:  {kg_top5}")
    print(f"  Ablation top 5:  {abl_top5}")

    all_crit = set(spread_top5 + kg_top5 + abl_top5)
    print(f"\n  {'Criterion':>10} | {'Spread':>8} | {'KG-δ':>8} | {'Ablation':>8} | {'Count':>5}")
    print("  " + "-" * 52)
    count_2plus = []
    for c in sorted(all_crit):
        in_sp = "✓" if c in spread_top5 else ""
        in_kg = "✓" if c in kg_top5 else ""
        in_ab = "✓" if c in abl_top5 else ""
        count = (c in spread_top5) + (c in kg_top5) + (c in abl_top5)
        print(f"  {c:>10} | {in_sp:>8} | {in_kg:>8} | {in_ab:>8} | {count:>5}")
        if count >= 2:
            count_2plus.append(c)

    print(f"\n  Appears in 2+ methods: {sorted(count_2plus)}")
    print(f"  → These are the most robust criteria for the human study")

    # Save ablation analysis
    abl_analysis = {
        'model': model,
        'configs': configs,
        'config_deltas': config_deltas,
        'criteria_sensitivity': [{'id': c[0], 'total_abs': c[1], 'total_pos': c[2], 'deltas': c[3]} for c in crit_sensitivity],
        'ablation_top5': abl_top5,
        'comparison': {
            'spread_top5': spread_top5,
            'kg_delta_top5': kg_top5,
            'ablation_top5': abl_top5,
            'appears_in_2plus': sorted(count_2plus)
        }
    }
    abl_path = RESULTS_DIR / 'ablation_analysis_14criteria.json'
    with open(abl_path, 'w') as f:
        json.dump(abl_analysis, f, indent=2)
    print(f"\n✓ Ablation analysis saved to {abl_path}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default=DEFAULT_MODEL)
    args = parser.parse_args()
    run_ablation_eval(model=args.model)
