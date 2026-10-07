#!/usr/bin/env python3
"""
judge_human_study_pairs.py

Judges both baseline_strict and joern reviews for the 6 human-study PRs
using a consistent 2-judge panel (gemini-2.5-flash + gemini-2.5-pro).

This produces joern-vs-baseline_strict deltas on the same panel — the
correct basis for win/tie/loss labels matching what raters actually see.

Usage:
    source load_env.sh && python3 experiments/human_study_reviews/judge_human_study_pairs.py
"""
import sys
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

OUT_DIR = Path(__file__).resolve().parent
JOERN_DIR = REPO_ROOT / "experiments" / "2026-05-15_joern_kg_main" / "exp_gpt4o_joern"

STUDY_PRS = [44, 24, 31, 22, 47, 38]
JUDGE_PANEL = ["gemini:gemini-2.5-flash", "gemini:gemini-2.5-pro"]
KG6 = {"C2", "F3", "F4", "M1", "T2", "T3"}


def judge_review(review_path: Path, pr_id: int, mode: str) -> dict:
    from evaluate_reviews import evaluate_single_review
    from dataclasses import asdict
    eval_path = OUT_DIR / f"pr{pr_id}_{mode}_eval.json"
    if eval_path.exists():
        print(f"  PR{pr_id} {mode}: cached")
        return json.loads(eval_path.read_text())
    print(f"  PR{pr_id} {mode}: judging...")
    result = asdict(evaluate_single_review(review_path, pr_id, mode, JUDGE_PANEL))
    eval_path.write_text(json.dumps(result, indent=2))
    print(f"  PR{pr_id} {mode}: done (kg6={sum(c['score'] for c in result['criteria_scores'] if c['criterion_id'] in KG6)})")
    return result


def main():
    print(f"Judge panel: {JUDGE_PANEL}")
    print(f"PRs: {STUDY_PRS}")
    print()

    tasks = []
    for pr_id in STUDY_PRS:
        baseline_path = OUT_DIR / f"pr{pr_id}_baseline_strict.md"
        joern_path = JOERN_DIR / f"pr{pr_id}_review.md"
        tasks.append((baseline_path, pr_id, "baseline_strict"))
        tasks.append((joern_path, pr_id, "joern"))

    # Run in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(judge_review, path, pid, mode): (pid, mode)
                   for path, pid, mode in tasks}
        for fut in as_completed(futures):
            pid, mode = futures[fut]
            results[(pid, mode)] = fut.result()

    # Report win/tie/loss on the correct pair
    print()
    print("Win/Tie/Loss on joern vs baseline_strict (same panel):")
    print(f"{'PR':>4} | {'baseline_strict/6':>18} | {'joern/6':>8} | {'Δ':>4} | outcome")
    print("-" * 60)
    for pr_id in STUDY_PRS:
        b = results.get((pr_id, "baseline_strict"), {})
        j = results.get((pr_id, "joern"), {})
        b_kg6 = sum(c["score"] for c in b.get("criteria_scores", []) if c["criterion_id"] in KG6)
        j_kg6 = sum(c["score"] for c in j.get("criteria_scores", []) if c["criterion_id"] in KG6)
        delta = j_kg6 - b_kg6
        outcome = "WIN" if delta > 0 else ("TIE" if delta == 0 else "LOSS")
        print(f"PR{pr_id:2d} | {b_kg6:>18} | {j_kg6:>8} | {delta:>+4} | {outcome}")

    print()
    print("Balance check:")
    deltas = [
        sum(c["score"] for c in results.get((pid, "joern"), {}).get("criteria_scores", []) if c["criterion_id"] in KG6)
        - sum(c["score"] for c in results.get((pid, "baseline_strict"), {}).get("criteria_scores", []) if c["criterion_id"] in KG6)
        for pid in STUDY_PRS
    ]
    wins = sum(1 for d in deltas if d > 0)
    ties = sum(1 for d in deltas if d == 0)
    losses = sum(1 for d in deltas if d < 0)
    print(f"  Wins: {wins}  Ties: {ties}  Losses: {losses}")


if __name__ == "__main__":
    main()
