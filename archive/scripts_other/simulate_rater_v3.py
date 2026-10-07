#!/usr/bin/env python3
"""
simulate_rater_v3.py

End-to-end pipeline test of the v3 human study (Decision 15 layout):

    1. One simulated rater (this assistant) goes through all 4 trials,
       scores each review on the 6 criteria, picks an A/B/both
       preference, fills in the "what differs?" textarea, and records
       a realistic time-spent.
    2. The simulated session is dumped as the same JSON shape that
       human_eval_v3/index.html's "Download my responses (.json)"
       button produces.
    3. `scripts/ingest_exported_payloads.py` converts that JSON into
       the four CSVs the analyzer reads.
    4. `scripts/analyze_human_llm_agreement.py` runs against the v2
       multi-judge LLM-judge file and emits the κ between this rater
       and the LLM panel.

Goal: prove the v3 design+pipeline produces a sensible κ on a single
careful rater BEFORE recruiting humans. If this passes, the bottleneck
is purely participant recruitment + the webhook redeploy.

The 0/1 rubric scores here are the same as
`scripts/rater_walkthrough_v2_vs_v3.py` for v3 — they are this
rater's honest reading of the four `bl_vs_kg` trials.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import random
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SIM_DIR = REPO_ROOT / "human_eval_v3" / "data" / "exported_payloads"
INGEST_DIR = REPO_ROOT / "human_eval_v3" / "data" / "ingested_csv"
LLM_V2_PANEL = REPO_ROOT / "results" / "checklist_evaluation_llm_multi__v2.json"
ANALYZER_OUT = REPO_ROOT / "results" / "human_llm_agreement_pilot_v3.json"

CRITERIA = ["F3*", "F2*", "T3", "Q5", "R1", "C6"]

# ─── This rater's scores (same logic + comments as
#     rater_walkthrough_v2_vs_v3.py for v3, restricted to bl_vs_kg only). ───
SCORES_BY_PR_MODE: dict[tuple[int, str], dict[str, int]] = {
    (12, "baseline"): dict(zip(CRITERIA, [1, 1, 1, 1, 0, 1])),  # 5
    (12, "kg"):       dict(zip(CRITERIA, [1, 1, 1, 1, 0, 1])),  # 5
    (1,  "baseline"): dict(zip(CRITERIA, [1, 1, 1, 1, 0, 0])),  # 4 — missed dup-print
    (1,  "kg"):       dict(zip(CRITERIA, [1, 1, 1, 1, 0, 1])),  # 5
    (3,  "baseline"): dict(zip(CRITERIA, [1, 0, 1, 1, 1, 1])),  # 5
    (3,  "kg"):       dict(zip(CRITERIA, [1, 0, 1, 1, 1, 1])),  # 5
    (14, "baseline"): dict(zip(CRITERIA, [1, 1, 1, 1, 0, 1])),  # 5
    (14, "kg"):       dict(zip(CRITERIA, [1, 1, 1, 1, 0, 1])),  # 5
}

# ─── Per-trial difficulty, time spent, and "what differs?" notes. ───
# Difficulty 1=easy / 5=hard. Times are realistic for a careful read of
# diff + body + two reviews + scoring with the diff-highlight on.
TRIAL_META = {
    12: dict(
        difficulty=2,
        time_spent_ms=145_000,  # ~2.4 min
        notes=(
            "Both flag Math::rand and the missing tests for pick_random; "
            "B (KG) goes further and points to the variant_call.cpp "
            "integration site."
        ),
    ),
    1: dict(
        difficulty=3,
        time_spent_ms=210_000,  # ~3.5 min
        notes=(
            "Both name the new project setting; B (KG) catches the "
            "duplicate-print issue (WARN_PRINT fires regardless of "
            "startup_alert) that A misses."
        ),
    ),
    3: dict(
        difficulty=3,
        time_spent_ms=180_000,  # ~3 min
        notes=(
            "Roughly equivalent — both suggest extracting the "
            "strictModeNotification into its own component and adding "
            "tests. B (KG) also flags the hardcoded docs URL."
        ),
    ),
    14: dict(
        difficulty=4,
        time_spent_ms=240_000,  # ~4 min — biggest diff, 12 kB
        notes=(
            "Both catch the deprecation of `width`; A (baseline) calls "
            "out the inline-drawer removal more clearly, B (KG) flags "
            "the expandable-feature ambiguity from the PR description. "
            "Different angles, similar coverage."
        ),
    ),
}


def preference_from_scores(a: dict[str, int], b: dict[str, int]) -> str:
    sa, sb = sum(a.values()), sum(b.values())
    if sa > sb:
        return "A"
    if sb > sa:
        return "B"
    return "both"


def build_session(rater_id: str, seed: int = 42) -> dict:
    rng = random.Random(seed)
    # Random A/B blind assignment per trial (UI does this in modeMap).
    # We always have A=baseline, B=kg or A=kg, B=baseline.
    started = dt.datetime.now(dt.timezone.utc)
    payloads = []
    cumulative_ms = 0
    for pr_id in [12, 1, 3, 14]:
        if rng.random() < 0.5:
            a_mode, b_mode = "baseline", "kg"
        else:
            a_mode, b_mode = "kg", "baseline"
        a_scores = SCORES_BY_PR_MODE[(pr_id, a_mode)]
        b_scores = SCORES_BY_PR_MODE[(pr_id, b_mode)]
        meta = TRIAL_META[pr_id]
        cumulative_ms += meta["time_spent_ms"]
        completed = started + dt.timedelta(milliseconds=cumulative_ms)
        # The UI's submitTaskToSheet emits two ratings rows per trial
        # (one per blind label) and the demographics on every batch.
        ratings = [
            {
                "pr_id":         pr_id,
                "comparison":    "bl_vs_kg",
                "blind_label":   "A",
                "mode":          a_mode,
                "scores":        a_scores,
                "difficulty":    meta["difficulty"],
                "preference":    preference_from_scores(a_scores, b_scores),
                "time_spent_ms": meta["time_spent_ms"],
                "notes":         meta["notes"],
                "github_clicks": rng.randint(0, 2),
            },
            {
                "pr_id":         pr_id,
                "comparison":    "bl_vs_kg",
                "blind_label":   "B",
                "mode":          b_mode,
                "scores":        b_scores,
                "difficulty":    meta["difficulty"],
                "preference":    preference_from_scores(a_scores, b_scores),
                "time_spent_ms": meta["time_spent_ms"],
                "notes":         meta["notes"],
                "github_clicks": rng.randint(0, 2),
            },
        ]
        payloads.append({
            "queued_at": completed.isoformat(),
            "payload": {
                "study_id":     "human_eval_v3",
                "rater_id":     rater_id,
                "completed_at": completed.isoformat(),
                "demographics": {
                    "role":           "software_engineer",
                    "exp_years":      "5-10",
                    "freq_review_pr": "weekly",
                },
                "ratings": ratings,
            },
        })

    # Quality-flag and feedback POSTs the UI also emits at the end.
    end_ts = (started + dt.timedelta(milliseconds=cumulative_ms)).isoformat()
    payloads.append({
        "queued_at": end_ts,
        "payload": {
            "study_id":     "human_eval_v3",
            "rater_id":     rater_id,
            "completed_at": end_ts,
            "feedback":     "The diff-highlighting was very helpful for "
                            "spotting where A and B diverge — saved me a "
                            "lot of back-and-forth scrolling.",
        },
    })
    return {
        "study_id":    "human_eval_v3",
        "rater_id":    rater_id,
        "exported_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sheet_url":   "https://script.google.com/macros/s/.../exec",
        "payloads":    payloads,
    }


def run(cmd: list[str]) -> str:
    print("\n$ " + " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr, file=sys.stderr)
        raise SystemExit(r.returncode)
    return r.stdout


def main() -> None:
    rater_id = "claude_pilot_001"
    SIM_DIR.mkdir(parents=True, exist_ok=True)
    INGEST_DIR.mkdir(parents=True, exist_ok=True)
    out = SIM_DIR / f"{rater_id}.json"
    out.write_text(json.dumps(build_session(rater_id), indent=2))
    print(f"==> Wrote simulated rater session: {out.relative_to(REPO_ROOT)}")

    print("==> Step 1/2  ingest exported JSON → CSVs")
    print(run(["python3", "scripts/ingest_exported_payloads.py",
              "--in",  str(SIM_DIR.relative_to(REPO_ROOT)),
              "--out", str(INGEST_DIR.relative_to(REPO_ROOT))]))

    print("==> Step 2/2  run analyzer against v2 multi-judge LLM panel")
    print(run([
        "python3", "scripts/analyze_human_llm_agreement.py",
        "--human",         str((INGEST_DIR / "responses.csv").relative_to(REPO_ROOT)),
        "--demographics",  str((INGEST_DIR / "demographics.csv").relative_to(REPO_ROOT)),
        "--feedback",      str((INGEST_DIR / "feedback.csv").relative_to(REPO_ROOT)),
        "--llm-checklist", "results/checklist_evaluation_llm_multi__v2.json",
        "--out",           str(ANALYZER_OUT.relative_to(REPO_ROOT)),
    ]))

    print(f"==> Pilot report saved: {ANALYZER_OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
