#!/usr/bin/env python3
"""
smoke_test.py — Sanity-check the study artefacts before deployment.

study_data.json checks:
  * PR set matches Decision 18 locked selection {22,24,31,38,44,47}
  * Modes are {baseline_strict, joern}
  * Single comparison bl_vs_joern present
  * Criteria set matches {F3*, F2*, T3, Q5, R1, C6}
  * All PRs have repo, url, title, non-empty body, non-truncated diff
  * No stray ``` fences, no Code Owners leaks, no Traceability sections

index.html checks:
  * Declares STUDY_ID = "human_eval_v4"
  * Uses heval4_ localStorage namespace
  * Fetches study_data.json (relative path)
  * Tags webhook payloads with study_id

Exit code 0 = all checks passed = safe to deploy.
"""

from __future__ import annotations

import json
import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
V3_DIR = os.path.join(REPO_ROOT, "human_eval_v3")
SD_PATH = os.path.join(V3_DIR, "study_data.json")
HTML_PATH = os.path.join(V3_DIR, "index.html")

# Decision 18: pivot to strict-baseline vs Joern on new 6 PRs
EXPECTED_PRS = {22, 24, 31, 38, 44, 47}
EXPECTED_MODES = {"baseline_strict", "joern"}
EXPECTED_COMPARISON_ID = "bl_vs_joern"
EXPECTED_CRITERIA = {"F3*", "F2*", "T3", "Q5", "R1", "C6"}


def fail(msg: str) -> None:
    print(f"  FAIL: {msg}")


def check_study_data() -> int:
    print("=" * 64)
    print("study_data.json checks")
    print("=" * 64)
    with open(SD_PATH) as f:
        sd = json.load(f)

    failures = 0

    # PR set
    pr_ids = {p["pr_id"] for p in sd["prs"]}
    if pr_ids != EXPECTED_PRS:
        fail(f"PR set mismatch: got {sorted(pr_ids)}, expected {sorted(EXPECTED_PRS)}")
        failures += 1
    else:
        print(f"  OK  PR set matches Decision 18 locked selection {sorted(EXPECTED_PRS)}")

    # Criteria
    crit_ids = {c["id"] for c in sd.get("criteria", [])}
    if crit_ids != EXPECTED_CRITERIA:
        fail(f"Criteria mismatch: got {sorted(crit_ids)}, expected {sorted(EXPECTED_CRITERIA)}")
        failures += 1
    else:
        print(f"  OK  Criteria set: {sorted(EXPECTED_CRITERIA)}")

    # Modes
    if set(sd.get("modes", [])) != EXPECTED_MODES:
        fail(f"Modes mismatch: got {sd.get('modes')}, expected {sorted(EXPECTED_MODES)}")
        failures += 1
    else:
        print(f"  OK  Modes: {sorted(EXPECTED_MODES)}")

    # Comparison
    comps = sd.get("comparisons", [])
    if len(comps) != 1:
        fail(f"Expected 1 comparison, got {len(comps)}")
        failures += 1
    elif comps[0]["id"] != EXPECTED_COMPARISON_ID:
        fail(f"Comparison id mismatch: got '{comps[0]['id']}', expected '{EXPECTED_COMPARISON_ID}'")
        failures += 1
    else:
        print(f"  OK  1 comparison: {EXPECTED_COMPARISON_ID}")

    # Per-PR checks
    pr_failures = 0
    for p in sd["prs"]:
        pid = p["pr_id"]

        if not p.get("repo") or p["repo"] == "?":
            fail(f"PR {pid}: missing repo"); pr_failures += 1
        if not p.get("url"):
            fail(f"PR {pid}: missing url"); pr_failures += 1
        if not p.get("title"):
            fail(f"PR {pid}: missing title"); pr_failures += 1

        body = p.get("body") or ""
        if len(body) < 50:
            fail(f"PR {pid}: body is {len(body)} chars, expected ≥ 50")
            pr_failures += 1

        diff = p.get("diff", "")
        if len(diff) >= 50000:
            fail(f"PR {pid}: diff at/over 50 kB cap ({len(diff)} chars)")
            pr_failures += 1
        if "[... diff truncated" in diff:
            fail(f"PR {pid}: diff has truncation marker")
            pr_failures += 1

        reviews = p.get("reviews", {})
        if set(reviews.keys()) != EXPECTED_MODES:
            fail(f"PR {pid}: reviews present={set(reviews.keys())}, expected={EXPECTED_MODES}")
            pr_failures += 1
            continue

        for mode, txt in reviews.items():
            if txt.startswith("```") or txt.endswith("```"):
                fail(f"PR {pid} {mode}: stray ``` fence")
                pr_failures += 1
            if re.search(r"^[-*]\s*\**Code\s*Owners?\**\s*[:\-]",
                         txt, re.IGNORECASE | re.MULTILINE):
                fail(f"PR {pid} {mode}: Code Owners leak present")
                pr_failures += 1
            if re.search(r"#{1,3}\s*Traceability\b", txt, re.IGNORECASE):
                fail(f"PR {pid} {mode}: Traceability section present (should be stripped)")
                pr_failures += 1

    failures += pr_failures
    if pr_failures == 0:
        n = len(sd["prs"])
        print(f"  OK  All {n} PRs × {len(EXPECTED_MODES)} modes = {n * len(EXPECTED_MODES)} reviews clean")
        print(f"  OK  All {n} PR bodies non-empty, diffs non-truncated")
        print(f"  OK  No Code Owners leaks, no Traceability sections")

    return failures


def check_html() -> int:
    print()
    print("=" * 64)
    print("index.html checks")
    print("=" * 64)
    failures = 0
    with open(HTML_PATH) as f:
        html = f.read()

    checks = [
        ('STUDY_ID = "human_eval_v4"',
         'declares STUDY_ID = "human_eval_v4"'),
        ('"heval4_"',
         'uses heval4_ localStorage namespace'),
        ('fetch("study_data.json")',
         'fetches study_data.json (relative path)'),
        ('study_id:STUDY_ID',
         'tags webhook payloads with study_id'),
    ]
    for needle, desc in checks:
        if needle in html:
            print(f"  OK  {desc}")
        else:
            fail(f"{desc} — needle not found: {needle!r}")
            failures += 1

    # Collision guards — old namespaces must not still be present
    for old in ['STUDY_ID = "human_eval_v2"', 'STUDY_ID = "human_eval_v3"',
                'heval3_v2_', 'heval3_v3_']:
        if old in html:
            fail(f"Old identifier still present (would collide): {old!r}")
            failures += 1

    if failures == 0:
        print("  OK  No old study namespace collisions")

    return failures


def main() -> int:
    failures = 0
    failures += check_study_data()
    failures += check_html()
    print()
    if failures == 0:
        print("ALL CHECKS PASSED — study is ready to deploy.")
        return 0
    print(f"{failures} check(s) FAILED — fix before deploying.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
