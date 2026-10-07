#!/usr/bin/env python3
"""
fetch_pr_bodies.py — Recover real PR bodies from GitHub for PRs whose
local evidence pack has an empty body.

Why: PR 1 (godot/73144) and PR 3 (grafana/97224) have empty bodies in
data/luca_prs_fixed/pr*_evidence.json. A rater who clicks "Read PR
description" sees nothing, which corrupts criterion C6 (completeness)
and reduces the rater's ability to ground judgments in PR intent.

This script fetches the real bodies once, strips HTML comments and
template boilerplate, and writes them to:

    human_eval_v2/data/pr_body_overrides.json

The build script (build_study_data_v2.py) reads this override file
when assembling study_data.json. The override is preferred over the
local evidence-pack body when both are present, so this also rescues
PRs whose local body is truncated.

Run:
    python3 human_eval_v2/scripts/fetch_pr_bodies.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OVERRIDES_PATH = os.path.join(
    REPO_ROOT, "human_eval_v2", "data", "pr_body_overrides.json"
)

PR_TO_FETCH = {
    1: "godotengine/godot/pulls/73144",
    3: "grafana/grafana/pulls/97224",
    12: "godotengine/godot/pulls/68625",
    14: "grafana/grafana/pulls/67809",
    17: "jenkinsci/jenkins/pulls/7853",
    19: "jenkinsci/jenkins/pulls/6229",
}


def strip_html_comments_and_boilerplate(body: str) -> str:
    s = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    s = re.sub(r"<img\b[^>]*>", "[image]", s, flags=re.IGNORECASE)
    s = re.sub(r"\r\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def fetch_pr_body(slug: str) -> str:
    url = f"https://api.github.com/repos/{slug}"
    req = urllib.request.Request(
        url, headers={"Accept": "application/vnd.github+json"}
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.loads(r.read())
    return d.get("body") or ""


def main() -> int:
    os.makedirs(os.path.dirname(OVERRIDES_PATH), exist_ok=True)
    out = {}
    failures = 0
    for pid, slug in PR_TO_FETCH.items():
        try:
            raw = fetch_pr_body(slug)
            cleaned = strip_html_comments_and_boilerplate(raw)
            out[str(pid)] = cleaned
            print(f"PR {pid:>2}  {slug:<48} {len(raw):>5} -> "
                  f"{len(cleaned):>5} chars")
        except Exception as e:
            print(f"PR {pid}: FAILED to fetch ({e})", file=sys.stderr)
            failures += 1

    with open(OVERRIDES_PATH, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print(f"\nWrote {OVERRIDES_PATH}")
    print(f"  {len(out)} bodies recovered, {failures} failure(s)")
    return failures


if __name__ == "__main__":
    sys.exit(main())
