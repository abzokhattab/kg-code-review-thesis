#!/usr/bin/env python3
"""
Experiment C: CPG richness vs KG-relevant delta correlation.
Free analysis — no API calls. Uses existing eval data.

Usage:
    python3 experiments/2026-05-15_joern_kg_main/exp_c_cpg_richness_correlation.py
"""
import json
import numpy as np
from pathlib import Path
from scipy import stats

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
CONTROLLED_DIR = SCRIPT_DIR / "controlled"
CACHE_DIR = SCRIPT_DIR / "cache"
BASELINE_JSON = REPO_ROOT / "results" / "checklist_evaluation_llm_multi__v2.json"

KG_CRITERIA = {'F3', 'F4', 'T3', 'M1', 'C2', 'T1', 'T2', 'M3', 'Q2'}

# PRs that ran (35, excluding Go PRs 9,27,35,36,37)
EXCLUDED_GO = {9, 27, 35, 36, 37}


def load_baseline_scores():
    data = json.loads(BASELINE_JSON.read_text())
    evals = data["evaluations"] if isinstance(data, dict) else data
    scores = {}
    for e in evals:
        if e['mode'] == 'baseline':
            pr_id = e['pr_id']
            scores[pr_id] = {
                'total': e['total_score'],
                'kgrel': e.get('kg_relevant_score', sum(
                    cs['score'] for cs in e.get('criteria_scores', [])
                    if cs['criterion_id'] in KG_CRITERIA
                ))
            }
    return scores


def load_joern_scores():
    scores = {}
    for eval_file in CONTROLLED_DIR.glob("pr*_eval.json"):
        pr_id = int(eval_file.stem.split('_')[0].replace('pr', ''))
        data = json.loads(eval_file.read_text())
        kgrel = sum(
            cs['score'] for cs in data.get('criteria_scores', [])
            if cs['criterion_id'] in KG_CRITERIA
        )
        scores[pr_id] = {
            'total': data.get('total_score', 0),
            'kgrel': kgrel
        }
    return scores


def load_cpg_richness():
    richness = {}
    for cg_file in CACHE_DIR.glob("pr*_callgraph.json"):
        pr_id = int(cg_file.stem.split('_')[0].replace('pr', ''))
        cg = json.loads(cg_file.read_text())
        richness[pr_id] = {
            'n_callers': len(cg.get('callers', [])),
            'n_functions': len(cg.get('functions_in_changed_files', []))
        }
    return richness


def main():
    baseline = load_baseline_scores()
    joern = load_joern_scores()
    richness = load_cpg_richness()

    # Build per-PR table
    rows = []
    for pr_id in sorted(joern.keys()):
        if pr_id in EXCLUDED_GO:
            continue
        if pr_id not in baseline:
            continue
        bl_kg = baseline[pr_id]['kgrel']
        jo_kg = joern[pr_id]['kgrel']
        bl_tot = baseline[pr_id]['total']
        jo_tot = joern[pr_id]['total']
        n_cal = richness.get(pr_id, {}).get('n_callers', 0)
        n_fun = richness.get(pr_id, {}).get('n_functions', 0)
        rows.append({
            'pr_id': pr_id,
            'bl_kg': bl_kg, 'jo_kg': jo_kg, 'delta_kg': jo_kg - bl_kg,
            'bl_tot': bl_tot, 'jo_tot': jo_tot, 'delta_tot': jo_tot - bl_tot,
            'n_callers': n_cal, 'n_functions': n_fun,
        })

    print(f"\n{'='*70}")
    print(f"EXPERIMENT C: CPG RICHNESS vs KG-RELEVANT DELTA (n={len(rows)})")
    print(f"{'='*70}")

    # Per-PR table
    print(f"\n{'PR':>4} {'BL_kg':>6} {'Jo_kg':>6} {'Δkg':>5} {'n_cal':>6} {'n_fun':>6}")
    print("-" * 40)
    for r in rows:
        print(f"pr{r['pr_id']:>2} {r['bl_kg']:>6} {r['jo_kg']:>6} {r['delta_kg']:>+5} {r['n_callers']:>6} {r['n_functions']:>6}")

    # Correlations
    delta_kg = np.array([r['delta_kg'] for r in rows])
    delta_tot = np.array([r['delta_tot'] for r in rows])
    n_cal = np.array([r['n_callers'] for r in rows], dtype=float)
    n_fun = np.array([r['n_functions'] for r in rows], dtype=float)
    bl_kg = np.array([r['bl_kg'] for r in rows], dtype=float)

    print(f"\n{'='*70}")
    print("SPEARMAN CORRELATIONS")
    print(f"{'='*70}")

    for label, x, y in [
        ("n_callers vs delta_kg", n_cal, delta_kg),
        ("n_callers vs delta_tot", n_cal, delta_tot),
        ("n_functions vs delta_kg", n_fun, delta_kg),
        ("baseline_kg vs delta_kg (floor effect?)", bl_kg, delta_kg),
    ]:
        r, p = stats.spearmanr(x, y)
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."
        print(f"  {label:<45} r={r:+.3f}  p={p:.4f}  {sig}")

    # Bin analysis: empty (0), sparse (1-10), moderate (11-49), capped (50)
    print(f"\n{'='*70}")
    print("BINNED ANALYSIS BY N_CALLERS")
    print(f"{'='*70}")
    bins = [
        ("empty (0)",     lambda r: r['n_callers'] == 0),
        ("sparse (1-9)",  lambda r: 1 <= r['n_callers'] <= 9),
        ("moderate (10-49)", lambda r: 10 <= r['n_callers'] <= 49),
        ("capped (50)",   lambda r: r['n_callers'] == 50),
    ]
    print(f"  {'Bin':<20} {'n':>4} {'mean Δkg':>9} {'mean Δtot':>10} {'wins':>6}")
    for label, fn in bins:
        subset = [r for r in rows if fn(r)]
        if not subset:
            continue
        mean_dkg = np.mean([r['delta_kg'] for r in subset])
        mean_dtot = np.mean([r['delta_tot'] for r in subset])
        wins = sum(1 for r in subset if r['delta_kg'] > 0)
        print(f"  {label:<20} {len(subset):>4} {mean_dkg:>+9.2f} {mean_dtot:>+10.2f} {wins:>4}/{len(subset)}")

    # Non-linear hypothesis: does adding callers on top of 0 help, but very high hurts?
    print(f"\n{'='*70}")
    print("NON-LINEARITY CHECK: empty vs non-empty CPG")
    print(f"{'='*70}")
    empty = [r['delta_kg'] for r in rows if r['n_callers'] == 0]
    nonempty = [r['delta_kg'] for r in rows if r['n_callers'] > 0]
    if empty and nonempty:
        stat, p = stats.mannwhitneyu(nonempty, empty, alternative='greater')
        print(f"  empty (n={len(empty)}): mean={np.mean(empty):+.2f}")
        print(f"  non-empty (n={len(nonempty)}): mean={np.mean(nonempty):+.2f}")
        print(f"  Mann-Whitney non-empty > empty: p={p:.4f}")

    # Write results to markdown
    out_path = REPO_ROOT / "results" / "EXP_C_CPG_RICHNESS.md"
    lines = [
        "# Experiment C: CPG Richness vs KG-relevant Delta",
        "",
        f"**n={len(rows)} PRs** (5 Go PRs excluded)",
        "",
        "## Spearman Correlations",
        "",
        "| Variable | r | p | sig |",
        "|---|---:|---:|---|",
    ]
    for label, x, y in [
        ("n_callers vs Δkg", n_cal, delta_kg),
        ("n_callers vs Δtot", n_cal, delta_tot),
        ("n_functions vs Δkg", n_fun, delta_kg),
        ("baseline_kg vs Δkg", bl_kg, delta_kg),
    ]:
        r, p = stats.spearmanr(x, y)
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."
        lines.append(f"| {label} | {r:+.3f} | {p:.4f} | {sig} |")

    lines += ["", "## Binned Analysis by n_callers", "",
              "| Bin | n | Mean Δkg | Mean Δtot | Wins |",
              "|---|---:|---:|---:|---:|"]
    for label, fn in bins:
        subset = [r for r in rows if fn(r)]
        if not subset:
            continue
        mean_dkg = np.mean([r['delta_kg'] for r in subset])
        mean_dtot = np.mean([r['delta_tot'] for r in subset])
        wins = sum(1 for r in subset if r['delta_kg'] > 0)
        lines.append(f"| {label} | {len(subset)} | {mean_dkg:+.2f} | {mean_dtot:+.2f} | {wins}/{len(subset)} |")

    out_path.write_text("\n".join(lines) + "\n")
    print(f"\nWrote: {out_path}")


if __name__ == "__main__":
    main()
