#!/usr/bin/env python3
"""
Retry only the judges that failed in `checklist_evaluation_llm_multi.json`,
with the tolerant fallback parser from `evaluate_reviews.py`, and re-emit all
derived files (legacy-shape JSON, CSV, markdown report, panel metadata).

Motivation: the original multi-judge run left 21 (pr, mode) cells where the
Gemini judge returned malformed JSON. Instead of re-running the full 300 calls,
this script re-scores only the ~21 failed cells and merges.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.evaluate_reviews import (  # noqa: E402
    CRITERIA_BY_ID,
    EVALUATION_CRITERIA,
    RESULTS_DIR,
    REPO_ROOT as _REPO_ROOT,  # noqa: F401 (imported for side-effects on path)
    ReviewEvaluation,
    _now_iso,
    aggregate_panel,
    compute_panel_meta,
    evaluate_single_review,
    generate_markdown_report,
    generate_summary,
    judge_one,
    load_pr_context,
    load_review,
)
from scripts.evaluate_reviews import JudgeVerdict  # noqa: E402


MULTI_PATH = RESULTS_DIR / "checklist_evaluation_llm_multi.json"
LEGACY_PATH = RESULTS_DIR / "checklist_evaluation_llm.json"
CSV_PATH = RESULTS_DIR / "checklist_evaluation_llm.csv"
REPORT_PATH = RESULTS_DIR / "CHECKLIST_EVALUATION_REPORT.md"


def reviews_path_for(pr_id: int, mode: str) -> Path:
    return REPO_ROOT / "outputs" / "luca_prs_fixed" / f"pr{pr_id}_{mode}.md"


def main() -> None:
    if not MULTI_PATH.exists():
        sys.exit(f"Missing {MULTI_PATH}. Run evaluate_reviews.py first.")

    with MULTI_PATH.open() as f:
        detailed = json.load(f)

    judges: list[str] = detailed["metadata"]["judges"]
    evals: list[dict] = detailed["evaluations"]

    # Collect (pr_id, mode, judge) cells that errored (or scored too few criteria)
    retries: list[tuple[int, str, str, int]] = []  # (pr_id, mode, judge, index_in_per_judge)
    for i, e in enumerate(evals):
        for j, pj in enumerate(e.get("per_judge", [])):
            if pj.get("error"):
                retries.append((e["pr_id"], e["mode"], pj["model"], j))

    print(f"Cells to retry: {len(retries)}")
    if not retries:
        print("Nothing to retry — exiting.")
        return

    # Group by file so we only load each review once
    loaded: dict[tuple[int, str], tuple[str, dict]] = {}
    retry_success = 0
    retry_still_failed = 0

    for pr_id, mode, model, _j in retries:
        key = (pr_id, mode)
        if key not in loaded:
            fp = reviews_path_for(pr_id, mode)
            if not fp.exists():
                print(f"  PR#{pr_id} {mode}: review file missing — skip")
                continue
            loaded[key] = (load_review(fp), load_pr_context(pr_id))
        review, pr_context = loaded[key]

        print(f"  PR#{pr_id:<3} {mode:<10} {model}: retry …", end=" ", flush=True)
        verdict = judge_one(review, pr_context, model)
        if verdict.error:
            retry_still_failed += 1
            print(f"still failing ({verdict.error[:80]})")
        else:
            n_yes = sum(1 for s in verdict.scores.values() if s == 1)
            n_valid = sum(1 for s in verdict.scores.values() if s in (0, 1))
            retry_success += 1
            print(f"OK ({n_yes}/{n_valid} yes)")

        # Find the evaluation entry and replace the verdict for this judge
        for e in evals:
            if e["pr_id"] == pr_id and e["mode"] == mode:
                for idx, pj in enumerate(e["per_judge"]):
                    if pj["model"] == model:
                        e["per_judge"][idx] = asdict(verdict)
                        break
                break

    print(f"\nRetry results: {retry_success} recovered, {retry_still_failed} still failed.\n")

    # Re-aggregate every evaluation from scratch (simplest & correct)
    print("Re-aggregating all 100 evaluations via majority vote…")
    new_evaluations: list[ReviewEvaluation] = []
    for e in evals:
        verdicts = [JudgeVerdict(
            model=pj["model"],
            scores={k: int(v) if v in (0, 1, "0", "1") else -1 for k, v in (pj.get("scores") or {}).items()},
            evidence={k: str(v) for k, v in (pj.get("evidence") or {}).items()},
            error=pj.get("error", ""),
        ) for pj in e["per_judge"]]

        # Fill any missing criteria keys (defensive)
        for v in verdicts:
            for c in EVALUATION_CRITERIA:
                v.scores.setdefault(c.id, -1)
                v.evidence.setdefault(c.id, "")

        aggregates = aggregate_panel(verdicts)
        scored_sum = sum(a.score for a in aggregates if a.score in (0, 1))
        max_score = len(EVALUATION_CRITERIA)
        kg_ids = {c.id for c in EVALUATION_CRITERIA if c.kg_relevant}
        kg_aggs = [a for a in aggregates if a.criterion_id in kg_ids]
        kg_sum = sum(a.score for a in kg_aggs if a.score in (0, 1))
        kg_max = len(kg_aggs)
        criteria_scores_flat = [
            {
                "criterion_id": a.criterion_id,
                "score": a.score if a.score in (0, 1) else 0,
                "evidence": a.evidence,
                "n_yes": a.n_yes,
                "n_valid": a.n_valid,
                "unanimous": a.unanimous,
            }
            for a in aggregates
        ]
        new_evaluations.append(ReviewEvaluation(
            pr_id=e["pr_id"],
            mode=e["mode"],
            total_score=scored_sum,
            max_score=max_score,
            percentage=round(scored_sum / max_score * 100, 1),
            kg_relevant_score=kg_sum,
            kg_relevant_max=kg_max,
            kg_relevant_percentage=round(kg_sum / kg_max * 100, 1) if kg_max else 0.0,
            criteria_scores=criteria_scores_flat,
            per_judge=[asdict(v) for v in verdicts],
            evaluation_timestamp=e.get("evaluation_timestamp", _now_iso()),
        ))

    summary = generate_summary(new_evaluations)
    panel_meta = compute_panel_meta(new_evaluations, judges)

    detailed["evaluations"] = [asdict(e) for e in new_evaluations]
    detailed["summary"] = summary
    detailed["panel"] = panel_meta
    detailed["metadata"]["retried_cells"] = len(retries)
    detailed["metadata"]["retried_recovered"] = retry_success
    detailed["metadata"]["retried_still_failed"] = retry_still_failed
    detailed["metadata"]["last_updated"] = _now_iso()

    with MULTI_PATH.open("w") as f:
        json.dump(detailed, f, indent=2)
    print(f"✓ Multi-judge detail → {MULTI_PATH.relative_to(REPO_ROOT)}")

    # Rewrite legacy-shape file
    legacy = {
        "metadata": {
            "evaluation_method": "llm_multi_judge_majority",
            "model": " + ".join(judges),
            "judges": judges,
            "aggregation": "majority_vote (ties → 0)",
            "timestamp": detailed["metadata"]["last_updated"],
            "criteria_count": len(EVALUATION_CRITERIA),
            "kg_relevant_criteria_count": sum(1 for c in EVALUATION_CRITERIA if c.kg_relevant),
        },
        "criteria_definitions": detailed["criteria_definitions"],
        "evaluations": [
            {
                "pr_id": e.pr_id,
                "mode": e.mode,
                "total_score": e.total_score,
                "max_score": e.max_score,
                "percentage": e.percentage,
                "kg_relevant_score": e.kg_relevant_score,
                "kg_relevant_max": e.kg_relevant_max,
                "kg_relevant_percentage": e.kg_relevant_percentage,
                "criteria_scores": [
                    {"criterion_id": cs["criterion_id"], "score": cs["score"], "evidence": cs["evidence"]}
                    for cs in e.criteria_scores
                ],
                "evaluation_timestamp": e.evaluation_timestamp,
            }
            for e in new_evaluations
        ],
        "summary": summary,
    }
    with LEGACY_PATH.open("w") as f:
        json.dump(legacy, f, indent=2)
    print(f"✓ Legacy-shape       → {LEGACY_PATH.relative_to(REPO_ROOT)}")

    # Rewrite CSV
    import csv as _csv
    with CSV_PATH.open("w", newline="") as f:
        w = _csv.writer(f)
        w.writerow(["pr_id", "mode", "total_score", "max_score", "percentage",
                    "kg_relevant_score", "kg_relevant_max", "kg_relevant_percentage"])
        for e in new_evaluations:
            w.writerow([e.pr_id, e.mode, e.total_score, e.max_score, e.percentage,
                        e.kg_relevant_score, e.kg_relevant_max, e.kg_relevant_percentage])
    print(f"✓ CSV                → {CSV_PATH.relative_to(REPO_ROOT)}")

    # Rewrite markdown report
    report = generate_markdown_report(summary, new_evaluations, panel_meta, judges)
    with REPORT_PATH.open("w") as f:
        f.write(report)
    print(f"✓ Markdown report    → {REPORT_PATH.relative_to(REPO_ROOT)}")

    # Print a final summary
    print("\n=== Final summary (after retry) ===")
    for mode in ["baseline", "kg", "rag", "hybrid"]:
        if mode in summary["by_mode"]:
            m = summary["by_mode"][mode]
            print(f"  {mode.upper():<10} total {m['avg_total']:.2f}/{m['max_score']} ({m['avg_percentage']:.1f}%)  "
                  f"KG-rel {m['avg_kg_relevant']:.2f}/{m['kg_max']} ({m['avg_kg_percentage']:.1f}%)")
    print("\n  Inter-judge agreement:")
    for pair, info in panel_meta["inter_judge_agreement"].items():
        print(f"    {pair:<60} {info['agreement_pct']}%  κ={info['cohen_kappa']}  (n={info['cells']})")


if __name__ == "__main__":
    main()
