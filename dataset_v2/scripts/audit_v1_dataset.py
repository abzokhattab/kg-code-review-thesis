#!/usr/bin/env python3
"""
audit_v1_dataset.py — Reproduce the v1 dataset audit.

Scans every evidence pack in data/luca_prs_fixed/ and reports the
specific data-quality issues that motivated the v2 rebuild:

  * empty PR body (LLM never saw maintainer description)
  * placeholder PR title (LLM never saw real title)
  * truncated diff (at the 15 kB cap)
  * docs-only change
  * revert PR
  * closed/not-merged PR
  * tiny single-Jelly stimulus (KG-unparseable)
  * binary-asset-heavy diff

Output is human-readable + a JSON file consumed by SELECTION_v2.md.

This script reads only data/luca_prs_fixed/ and does not modify
anything. Safe to run any time; output is deterministic.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = REPO_ROOT / "data" / "luca_prs_fixed"
OUT_PATH = REPO_ROOT / "dataset_v2" / "docs" / "audit_v1.json"

PLACEHOLDER_TITLE_PREFIXES = (
    "Grafana PR", "scikit-learn PR", "Django PR",
    "Apache Kafka PR", "Jenkins PR", "TypeScript PR", "Godot PR",
)

DOCS_ONLY_EXT_SETS = (
    {".md"}, {".txt"}, {".rst"}, {".mdx"},
)

BINARY_EXTS = {".gif", ".png", ".jpg", ".jpeg", ".ico", ".zip", ".bin"}

# v1 truncation cap from scripts/expand_dataset.py
V1_DIFF_CAP = 15000


def file_exts(changed_files):
    out = set()
    for c in changed_files:
        path = c.get("path", "")
        if "." in path:
            out.add("." + path.rsplit(".", 1)[1].lower())
    return out


def is_docstring_only(diff: str) -> bool:
    """True if every modified hunk is wrapped inside a Python docstring."""
    if not diff:
        return False
    relevant = []
    for line in diff.splitlines():
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            relevant.append(line)
    if not relevant:
        return False
    # heuristic: count modified lines that are inside docstrings vs outside
    in_docstring = False
    inside = 0
    outside = 0
    for line in diff.splitlines():
        stripped = line.strip()
        if stripped.startswith(('"""', "'''", '+    """', '-    """')):
            in_docstring = not in_docstring
            continue
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            if in_docstring:
                inside += 1
            else:
                outside += 1
    if outside == 0 and inside > 0:
        return True
    return inside > outside * 4


def audit_pr(pr_id: int) -> dict:
    path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    if not path.exists():
        return {"pr_id": pr_id, "missing": True}
    with open(path) as f:
        ev = json.load(f)

    pr = ev.get("pr", {})
    cf = ev.get("changed_files", [])
    diff = ev.get("full_diff", "")
    title = (pr.get("title") or "")
    body = (pr.get("body") or "")
    url = pr.get("url", "")

    exts = file_exts(cf)
    n_binary = sum(1 for c in cf if any(c.get("path", "").endswith(b) for b in BINARY_EXTS))

    issues = []
    if not body.strip():
        issues.append("empty_body")
    if title.startswith(PLACEHOLDER_TITLE_PREFIXES):
        issues.append("placeholder_title")
    if len(diff) >= V1_DIFF_CAP:
        issues.append("truncated_diff")
    if any(exts <= s for s in DOCS_ONLY_EXT_SETS):
        issues.append("docs_only_extensions")
    if exts == {".py"} and is_docstring_only(diff):
        issues.append("docstring_only")
    if "revert" in title.lower():
        issues.append("revert_pr")
    if exts == {".jelly"}:
        issues.append("jelly_only")
    if n_binary > 0 and len(cf) > 0 and n_binary / len(cf) > 0.3:
        issues.append("binary_heavy")
    # closed/not-merged is hard to check from the evidence pack alone;
    # PR 7 is the only known case (microsoft/TypeScript#57375)
    if pr.get("number") == 57375:
        issues.append("not_merged")

    return {
        "pr_id": pr_id,
        "url": url,
        "title": title[:80],
        "title_real": not title.startswith(PLACEHOLDER_TITLE_PREFIXES),
        "body_chars": len(body),
        "diff_chars": len(diff),
        "n_files": len(cf),
        "extensions": sorted(exts),
        "n_binary": n_binary,
        "issues": issues,
    }


def main() -> int:
    pr_ids = sorted(
        int(f.replace("pr", "").replace("_evidence.json", ""))
        for f in os.listdir(EVIDENCE_DIR)
        if f.startswith("pr") and f.endswith("_evidence.json")
    )

    results = [audit_pr(pid) for pid in pr_ids]

    print(f"{'PR':>3} | {'issues':<60} | {'body':>5} | {'diff_kB':>7} | url")
    print("-" * 130)

    issue_counts: dict[str, int] = {}
    for r in results:
        if r.get("missing"):
            print(f"{r['pr_id']:>3} | (missing evidence file)")
            continue
        for iss in r["issues"]:
            issue_counts[iss] = issue_counts.get(iss, 0) + 1
        print(
            f"{r['pr_id']:>3} | "
            f"{', '.join(r['issues']) or '(clean)':<60} | "
            f"{r['body_chars']:>5} | "
            f"{r['diff_chars']/1024:>7.1f} | "
            f"{r['url']}"
        )

    print()
    print("Issue counts (out of 25 PRs):")
    for issue, n in sorted(issue_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {issue:<25s} {n:>2}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(
            {"prs": results, "issue_counts": issue_counts},
            f, indent=2,
        )
    print(f"\nWrote {OUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
