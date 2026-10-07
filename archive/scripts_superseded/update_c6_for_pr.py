#!/usr/bin/env python3
"""Incrementally merge C6 (Completeness) multi-judge scores for one PR.

Used when a stimulus PR is swapped into ``human_eval/study_data.json`` after
the main C6 evaluation has already run, so we only pay the API cost for the
newly added PR and preserve existing verdicts for the untouched ones.

Usage:
    python3 scripts/update_c6_for_pr.py --pr-id 18
    python3 scripts/update_c6_for_pr.py --pr-id 18 --drop-pr 26

Recomputes the summary/agreement blocks from the merged score set before
writing the file back.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.evaluate_completeness import (  # noqa: E402
    OUTPUT_PATH,
    STUDY_DATA_PATH,
    CompletenessScore,
    _now_iso,
    score_one,
)


def _recompute_summary(scores: list[dict], modes: list[str], models: list[str]) -> dict:
    by_mode: dict[str, dict] = {}
    for mode in modes:
        mscores = [s for s in scores if s["mode"] == mode and s["score"] in (0, 1)]
        if not mscores:
            continue
        by_mode[mode] = {
            "n": len(mscores),
            "yes_count_majority": sum(1 for s in mscores if s["score"] == 1),
            "yes_rate_pct_majority": round(
                100.0 * sum(1 for s in mscores if s["score"] == 1) / len(mscores), 1
            ),
            "unanimous_count": sum(1 for s in mscores if s["unanimous"]),
        }

    by_judge: dict[str, dict] = {m: {} for m in models}
    for m in models:
        for mode in modes:
            vals = [
                v["score"]
                for s in scores
                if s["mode"] == mode
                for v in s["verdicts"]
                if v["model"] == m and v["score"] in (0, 1)
            ]
            if not vals:
                continue
            by_judge[m][mode] = {
                "n": len(vals),
                "yes_count": sum(vals),
                "yes_rate_pct": round(100.0 * sum(vals) / len(vals), 1),
            }

    agreement: dict[str, dict] = {}
    for i, m1 in enumerate(models):
        for m2 in models[i + 1 :]:
            both, agreed = 0, 0
            for s in scores:
                v1 = next(
                    (v for v in s["verdicts"] if v["model"] == m1 and v["score"] in (0, 1)),
                    None,
                )
                v2 = next(
                    (v for v in s["verdicts"] if v["model"] == m2 and v["score"] in (0, 1)),
                    None,
                )
                if v1 and v2:
                    both += 1
                    if v1["score"] == v2["score"]:
                        agreed += 1
            if both:
                agreement[f"{m1} vs {m2}"] = {
                    "pairs": both,
                    "agreed": agreed,
                    "agreement_pct": round(100.0 * agreed / both, 1),
                }

    return {
        "by_mode_majority": by_mode,
        "by_judge": by_judge,
        "inter_judge_agreement": agreement,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr-id", type=int, required=True, help="PR id to (re)score")
    parser.add_argument(
        "--drop-pr",
        type=int,
        action="append",
        default=[],
        help="PR id to remove from the existing output (can repeat)",
    )
    args = parser.parse_args()

    existing = json.loads(OUTPUT_PATH.read_text())
    models: list[str] = existing["metadata"]["judges"]
    study = json.loads(STUDY_DATA_PATH.read_text())
    modes: list[str] = study["modes"]

    target = next((p for p in study["prs"] if p["pr_id"] == args.pr_id), None)
    if target is None:
        parser.error(f"PR {args.pr_id} not found in {STUDY_DATA_PATH}")

    drop_ids = set(args.drop_pr + [args.pr_id])
    kept = [s for s in existing["scores"] if s["pr_id"] not in drop_ids]
    print(
        f"Keeping {len(kept)} existing scores; dropping pr_id in {sorted(drop_ids)}; "
        f"scoring PR {args.pr_id} on {modes} with {len(models)} judges."
    )

    new_scores: list[CompletenessScore] = []
    for mode in modes:
        if mode not in (target.get("reviews") or {}):
            print(f"PR {args.pr_id} {mode}: SKIP (no review)")
            continue
        print(f"PR {args.pr_id} {mode}: ", end="", flush=True)
        s = score_one(target, mode, models)
        new_scores.append(s)
        agg = "Y" if s.score == 1 else ("N" if s.score == 0 else "?")
        per_judge = " ".join(
            f"{v['model'].split(':')[-1]}={'Y' if v['score']==1 else ('N' if v['score']==0 else 'err')}"
            for v in s.verdicts
        )
        print(f"{agg} ({s.n_yes}/{s.n_valid}) {per_judge}")

    merged = kept + [asdict(s) for s in new_scores]
    merged.sort(key=lambda r: (r["pr_id"], r["mode"]))

    existing["scores"] = merged
    existing["summary"] = _recompute_summary(merged, modes, models)
    existing["metadata"]["timestamp"] = _now_iso()
    existing["metadata"]["study_data_version"] = study.get("version")

    OUTPUT_PATH.write_text(json.dumps(existing, indent=2))
    print(f"\nWrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    by_mode = existing["summary"]["by_mode_majority"]
    print("Yes rate by mode (majority vote):")
    for mode, info in by_mode.items():
        print(
            f"  {mode:<10} {info['yes_count_majority']}/{info['n']}  "
            f"({info['yes_rate_pct_majority']}%)  unanimous: {info['unanimous_count']}/{info['n']}"
        )


if __name__ == "__main__":
    main()
