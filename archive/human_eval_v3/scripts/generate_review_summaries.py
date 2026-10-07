#!/usr/bin/env python3
"""generate_review_summaries.py — add a neutral AI TL;DR to each review.

Rationale (2026-06-20): the concise-prompt ablation showed shortening the
reviews does NOT improve quality (precision is statistically unchanged; see
results/SNR_RESULTS_DEDUP.md). So instead of regenerating shorter reviews, we
keep the full reviews and add a short AI summary LAYER in the study UI to cut
rater fatigue without touching the stimulus content.

Design constraints (blinding-safe):
  * The summary is generated from the REVIEW TEXT ALONE — never the mode label —
    in an identical neutral style for every arm, so it cannot de-blind a rater
    beyond what the review itself already reveals.
  * Pre-computed offline and frozen into study_data.json: identical for every
    rater, reproducible, no live API call during the study.
  * Idempotent + cached: re-running skips reviews already summarised unless
    --force is passed.

Writes pr["review_summaries"][mode] = ["bullet", "bullet", ...] for every mode
present in pr["reviews"]. The UI (index.html) renders it as a TL;DR box on top
of each review card.

Usage:
  source load_env.sh
  python3 human_eval_v3/scripts/generate_review_summaries.py            # study_data.json
  python3 human_eval_v3/scripts/generate_review_summaries.py --force
  python3 human_eval_v3/scripts/generate_review_summaries.py --study human_eval_v3/study_data_strict.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
ENV = REPO / ".env"
import os
if ENV.exists():
    for line in ENV.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from prnote.llm import generate_completion  # noqa: E402

SYSTEM = """You compress a code-review note into a neutral TL;DR for a reader who will then read the full note.

Rules:
- Output 2 to 3 bullet points, each a single short sentence (max ~18 words).
- Capture only the review's most important CONCRETE points (the actual concerns/recommendations).
- Neutral, factual tone. Do NOT praise, rank, or judge the review's quality.
- Do NOT add anything not in the review. Do NOT mention "the review" or "this note".
- Output ONLY the bullets, each starting with "- ". No heading, no preamble."""


def summarise(review: str, model: str) -> list[str]:
    raw = generate_completion(
        prompt=f"Code-review note:\n\n{review}\n\nWrite the 2-3 bullet TL;DR.",
        system=SYSTEM, model=model, temperature=0.0,
    )
    bullets = []
    for line in raw.splitlines():
        line = line.strip()
        m = re.match(r"^[-*•]\s+(.*)$", line)
        if m and m.group(1).strip():
            bullets.append(m.group(1).strip())
    return bullets[:3]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--study", default="human_eval_v3/study_data.json")
    ap.add_argument("--model", default="openai:gpt-4o-mini")
    ap.add_argument("--force", action="store_true", help="re-summarise even if present")
    args = ap.parse_args()

    path = REPO / args.study
    data = json.loads(path.read_text())

    n_done = n_skip = 0
    for pr in data["prs"]:
        summ = pr.setdefault("review_summaries", {})
        for mode, review in pr["reviews"].items():
            if not args.force and summ.get(mode):
                n_skip += 1
                continue
            bullets = summarise(review, args.model)
            summ[mode] = bullets
            n_done += 1
            print(f"PR#{pr['pr_id']:<3} {mode:<16} {len(bullets)} bullets: "
                  f"{bullets[0][:60] if bullets else 'EMPTY'}", flush=True)

    data["summary_meta"] = {
        "model": args.model,
        "note": "Neutral TL;DR generated from review text only (blinding-safe). "
                "See generate_review_summaries.py.",
    }
    path.write_text(json.dumps(data, indent=2))
    print(f"\nwrote {path.relative_to(REPO)}  (summarised={n_done}, skipped={n_skip})")


if __name__ == "__main__":
    main()
