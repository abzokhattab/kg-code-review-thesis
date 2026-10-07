#!/usr/bin/env python3
"""
ingest_exported_payloads.py

Re-hydrate participant data from manually-exported localStorage JSONs into
the same shape the analyzer (`scripts/analyze_human_llm_agreement.py`)
expects to read from the Sheet.

Use this when the Apps Script webhook was unhealthy during a study run
and raters submitted via the "Download my responses (.json)" button on
the completion screen. Drop their .json files into a folder, point this
script at it, and it will write the equivalent CSV tabs.

Output CSVs match the column layout of the live Sheet tabs:

  - responses.csv      ← the per-task ratings rows
  - demographics.csv   ← the demographics rows (one per rater, last-write-wins)
  - feedback.csv       ← free-text feedback
  - quality_flags.csv  ← end-of-study quality flags

Usage:
    python3 scripts/ingest_exported_payloads.py \\
        --in human_eval_v3/data/exported_payloads \\
        --out human_eval_v3/data/ingested_csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

RESPONSES_HEADER = [
    "received_at", "rater_id", "completed_at",
    "study_id", "pr_id", "comparison", "blind_label", "mode",
    "F3*", "F2*", "T3", "Q5", "R1", "C6",
    "difficulty", "preference", "time_spent_ms",
    "notes", "github_clicks",
]
DEMOGRAPHICS_HEADER = [
    "received_at", "rater_id", "study_id",
    "role", "exp_years", "freq_review_pr",
    "completed_at",
]
FEEDBACK_HEADER = [
    "received_at", "rater_id", "study_id", "feedback", "completed_at",
]
QFLAGS_HEADER = [
    "received_at", "rater_id", "study_id", "quality_flags", "completed_at",
]


def _zo(v: Any) -> str:
    """Coerce 0/1/True/False/'0'/'1' → '0'/'1'; else empty string."""
    if v in (0, 1):
        return str(v)
    if v in ("0", "1"):
        return v
    if v is True:
        return "1"
    if v is False:
        return "0"
    return ""


def write_csv(path: Path, header: list[str], rows: list[list[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def ingest_one(export_path: Path) -> tuple[list[list], list[list], list[list], list[list]]:
    """Return (responses, demographics, feedback, qflags) rows for one file."""
    with export_path.open() as f:
        data = json.load(f)
    rater_id = data.get("rater_id") or ""
    study_id = data.get("study_id") or ""
    payloads = data.get("payloads") or []

    responses: list[list] = []
    demographics: list[list] = []
    feedback: list[list] = []
    qflags: list[list] = []

    for entry in payloads:
        recv = entry.get("queued_at") or ""
        body = entry.get("payload") or {}
        completed_at = body.get("completed_at") or ""
        b_rid = body.get("rater_id") or rater_id
        b_sid = body.get("study_id") or study_id

        for r in body.get("ratings") or []:
            sc = r.get("scores") or {}
            responses.append([
                recv, b_rid, completed_at, b_sid,
                r.get("pr_id", ""), r.get("comparison", ""),
                r.get("blind_label", ""), r.get("mode", ""),
                _zo(sc.get("F3*")), _zo(sc.get("F2*")), _zo(sc.get("T3")),
                _zo(sc.get("Q5")),  _zo(sc.get("R1")),  _zo(sc.get("C6")),
                r.get("difficulty", ""), r.get("preference", ""),
                r.get("time_spent_ms", ""), r.get("notes", ""),
                r.get("github_clicks", 0),
            ])

        d = body.get("demographics") or {}
        if d:
            demographics.append([
                recv, b_rid, b_sid,
                d.get("role", ""), d.get("exp_years", ""),
                d.get("freq_review_pr", ""), completed_at,
            ])

        if isinstance(body.get("feedback"), str) and body["feedback"].strip():
            feedback.append([recv, b_rid, b_sid, body["feedback"], completed_at])

        if isinstance(body.get("quality_flags"), list) and body["quality_flags"]:
            qflags.append([
                recv, b_rid, b_sid,
                json.dumps(body["quality_flags"], ensure_ascii=False),
                completed_at,
            ])

    return responses, demographics, feedback, qflags


def dedup_demographics(rows: list[list]) -> list[list]:
    """Keep last-write per (study_id, rater_id) ordered by received_at."""
    by_key: dict[tuple[str, str], list] = {}
    for row in sorted(rows, key=lambda r: r[0]):  # sort by received_at
        by_key[(row[2], row[1])] = row
    return list(by_key.values())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="indir", required=True,
                    help="folder of exported .json files")
    ap.add_argument("--out", dest="outdir", required=True,
                    help="folder to write the four CSVs into")
    args = ap.parse_args()

    indir = Path(args.indir)
    outdir = Path(args.outdir)
    if not indir.is_dir():
        print(f"input dir not found: {indir}", file=sys.stderr)
        return 1

    files = sorted(indir.glob("*.json"))
    if not files:
        print(f"no .json files found in {indir}", file=sys.stderr)
        return 1
    print(f"==> ingesting {len(files)} export file(s) from {indir}")

    all_resp: list[list] = []
    all_demo: list[list] = []
    all_fb:   list[list] = []
    all_qf:   list[list] = []
    per_rater = defaultdict(int)

    for fp in files:
        try:
            r, d, f, q = ingest_one(fp)
        except Exception as exc:
            print(f"  warn: {fp.name} skipped: {exc}", file=sys.stderr)
            continue
        per_rater[fp.name] = len(r)
        all_resp.extend(r)
        all_demo.extend(d)
        all_fb.extend(f)
        all_qf.extend(q)

    all_demo_dedup = dedup_demographics(all_demo)

    write_csv(outdir / "responses.csv",     RESPONSES_HEADER,     all_resp)
    write_csv(outdir / "demographics.csv",  DEMOGRAPHICS_HEADER,  all_demo_dedup)
    write_csv(outdir / "feedback.csv",      FEEDBACK_HEADER,      all_fb)
    write_csv(outdir / "quality_flags.csv", QFLAGS_HEADER,        all_qf)

    print(f"==> wrote {len(all_resp)} response rows")
    print(f"==> wrote {len(all_demo_dedup)} demographics rows ({len(all_demo)} before dedup)")
    print(f"==> wrote {len(all_fb)} feedback rows")
    print(f"==> wrote {len(all_qf)} quality_flags rows")
    print(f"==> output: {outdir}")
    print()
    print("Per-file response counts:")
    for name, n in sorted(per_rater.items()):
        print(f"    {name}: {n}")
    print()
    print("Feed these into the analyzer with:")
    print(f"    python3 scripts/analyze_human_llm_agreement.py \\")
    print(f"        --human         {outdir}/responses.csv \\")
    print(f"        --demographics  {outdir}/demographics.csv \\")
    print(f"        --feedback      {outdir}/feedback.csv \\")
    print(f"        --quality-flags {outdir}/quality_flags.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
