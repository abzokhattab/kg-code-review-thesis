#!/usr/bin/env python3
"""
judge_reviews.py — LLM-judge panel on the 8 new study reviews.

Same panel as experiments/human_study_reviews/judge_human_study_pairs.py
(gemini-2.5-flash + gemini-2.5-pro) so deltas are comparable with the
existing human-study stimuli. Idempotent (skips existing eval files).

Usage: source load_env.sh && python3 judge_reviews.py
"""
import json
import sys
from dataclasses import asdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE = Path(__file__).resolve().parent
REPO_ROOT = BASE.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from evaluate_reviews import judge_one, aggregate_panel, EVALUATION_CRITERIA

JUDGE_PANEL = ["gemini:gemini-2.5-flash", "gemini:gemini-2.5-pro"]
KEYS = ["requests_7433", "flask_5637", "click_3493", "requests_7328",
        "flask_5799", "click_3578"]
KG_IDS = {c.id for c in EVALUATION_CRITERIA if c.kg_relevant}


def judge(key, mode):
    out_path = BASE / "reviews" / f"{key}_{mode}_eval.json"
    if out_path.exists():
        d = json.loads(out_path.read_text())
        print(f"  {key}/{mode}: cached (total={d['total']}, kgrel={d['kg_relevant']})")
        return
    ev = json.loads((BASE / "evidence" / f"{key}_evidence.json").read_text())
    ctx = {"title": ev["pr"]["title"], "body": (ev["pr"].get("body") or "")[:500],
           "pr_id": key}
    review = (BASE / "reviews" / f"{key}_{mode}.md").read_text()

    verdicts = [judge_one(review, ctx, m) for m in JUDGE_PANEL]
    aggs = aggregate_panel(verdicts)
    total = sum(a.score for a in aggs if a.score in (0, 1))
    kgrel = sum(a.score for a in aggs if a.criterion_id in KG_IDS and a.score in (0, 1))
    out = {
        "pr": key, "mode": mode, "judges": JUDGE_PANEL,
        "total": total, "max": len(EVALUATION_CRITERIA),
        "kg_relevant": kgrel, "kg_max": len(KG_IDS),
        "criteria": [{"id": a.criterion_id, "score": a.score if a.score in (0, 1) else 0}
                     for a in aggs],
    }
    out_path.write_text(json.dumps(out, indent=1))
    print(f"  {key}/{mode}: total={total}/25 kgrel={kgrel}/{len(KG_IDS)}")


if __name__ == "__main__":
    jobs = [(k, m) for k in KEYS for m in ("baseline_strict", "kg")]
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(lambda j: judge(*j), jobs))
    print("\nSummary (kg vs baseline_strict):")
    for k in KEYS:
        b = json.loads((BASE / "reviews" / f"{k}_baseline_strict_eval.json").read_text())
        g = json.loads((BASE / "reviews" / f"{k}_kg_eval.json").read_text())
        print(f"  {k:16} total {b['total']:>2} -> {g['total']:>2} | "
              f"kgrel {b['kg_relevant']} -> {g['kg_relevant']}")
