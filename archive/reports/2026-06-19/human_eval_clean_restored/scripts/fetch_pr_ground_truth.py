#!/usr/bin/env python3
"""
fetch_pr_ground_truth.py — Fetch the real maintainer feedback for each
of the 6 v2 PRs from GitHub, so we can anchor criterion C6.

For each PR, we collect:
  * issue-level comments  (general discussion on the PR thread)
  * review-level comments (line-anchored review comments)
  * the linked issue body, if any (e.g. JENKINS-71089)
  * the merge commit message

Output: human_eval_v2/data/pr_ground_truth/pr<N>.json — used both for
the SELECTION_v2.md §5 write-up and for any later "did the AI review
catch what the humans flagged?" analysis.

Run:
    python3 human_eval_v2/scripts/fetch_pr_ground_truth.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(REPO_ROOT, "human_eval_v2", "data", "pr_ground_truth")

PR_TO_FETCH = {
    1: "godotengine/godot/73144",
    3: "grafana/grafana/97224",
    12: "godotengine/godot/68625",
    14: "grafana/grafana/67809",
    17: "jenkinsci/jenkins/7853",
    19: "jenkinsci/jenkins/6229",
}


def gh_get(path: str) -> dict | list:
    url = f"https://api.github.com/{path}"
    req = urllib.request.Request(
        url, headers={"Accept": "application/vnd.github+json"}
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 403 and attempt < 2:
                time.sleep(5)
                continue
            raise


def strip_comment(body: str | None) -> str:
    if not body:
        return ""
    s = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    s = re.sub(r"<img\b[^>]*>", "[image]", s, flags=re.IGNORECASE)
    s = re.sub(r"\r\n", "\n", s).strip()
    return s


def collect(pid: int, slug: str) -> dict:
    owner_repo, num = slug.rsplit("/", 1)
    print(f"\n--- PR {pid}  {owner_repo}#{num} ---")

    pr = gh_get(f"repos/{owner_repo}/pulls/{num}")
    issue_comments = gh_get(f"repos/{owner_repo}/issues/{num}/comments")
    review_comments = gh_get(f"repos/{owner_repo}/pulls/{num}/comments")
    reviews = gh_get(f"repos/{owner_repo}/pulls/{num}/reviews")

    out = {
        "pr_id": pid,
        "owner_repo": owner_repo,
        "pr_number": int(num),
        "title": pr.get("title", ""),
        "url": pr.get("html_url", ""),
        "merged_at": pr.get("merged_at"),
        "body": strip_comment(pr.get("body")),
        "issue_comments": [
            {
                "user": (c.get("user") or {}).get("login", "?"),
                "created_at": c.get("created_at"),
                "body": strip_comment(c.get("body")),
            }
            for c in issue_comments if isinstance(c, dict) and c.get("body")
        ],
        "review_comments": [
            {
                "user": (c.get("user") or {}).get("login", "?"),
                "path": c.get("path"),
                "line": c.get("line") or c.get("original_line"),
                "body": strip_comment(c.get("body")),
            }
            for c in review_comments if isinstance(c, dict) and c.get("body")
        ],
        "review_summaries": [
            {
                "user": (r.get("user") or {}).get("login", "?"),
                "state": r.get("state"),
                "body": strip_comment(r.get("body")),
            }
            for r in reviews
            if isinstance(r, dict) and r.get("body")
        ],
    }

    print(f"  title:           {out['title']}")
    print(f"  merged_at:       {out['merged_at']}")
    print(f"  issue_comments:  {len(out['issue_comments'])}")
    print(f"  review_comments: {len(out['review_comments'])}")
    print(f"  review_summaries:{len(out['review_summaries'])}")
    return out


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    failures = 0
    for pid, slug in PR_TO_FETCH.items():
        try:
            data = collect(pid, slug)
            path = os.path.join(OUT_DIR, f"pr{pid}.json")
            with open(path, "w") as f:
                json.dump(data, f, indent=2, sort_keys=True)
        except Exception as e:
            print(f"  FAILED: {e}", file=sys.stderr)
            failures += 1
    return failures


if __name__ == "__main__":
    sys.exit(main())
