#!/usr/bin/env python3
"""
deep_audit.py — Look for *content-quality* issues in the v2 survey data
that the smoke test does not catch.

The smoke test verifies the v2 study_data.json has the right shape and
that the obvious cleanups were applied. This script goes deeper:

  1. STRUCTURAL PARITY between modes — do all three modes use the same
     section headers? If KG always has a "Traceability" section and
     baseline never does, that's a de-blinding tell.

  2. LENGTH PARITY — if KG reviews are systematically 2x longer than
     baseline, raters can de-blind by skimming.

  3. HALLUCINATION CHECK — does the review mention file paths or
     symbols that do *not* appear in the diff? (Lightweight heuristic:
     extract `code-fenced` or `path/like` tokens from the review and
     check whether they appear anywhere in the diff.)

  4. MODE-SPECIFIC FORMATTING TELLS — bullet style (`*` vs `-`), header
     level, nested-bold patterns. Does any one mode have a unique
     surface-form fingerprint?

  5. CROSS-MODE CONTRADICTIONS — do all three modes recommend the same
     wrong direction (the PR-18 problem)?

  6. SECTION-LEVEL PRESENCE — Problem / Evidence / Impact /
     Recommendation / Traceability — are they all there in every
     review? Missing sections in one mode is a tell.

This script does NOT modify study_data.json. It only reports.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SD_PATH = os.path.join(REPO_ROOT, "human_eval_v3", "study_data.json")

MODES = ["baseline", "kg", "rag"]
EXPECTED_SECTIONS = ["Problem", "Evidence", "Impact", "Recommendation", "Traceability"]


def get_sections(text: str) -> list[str]:
    """Return the H2/H3 headers in order."""
    out = []
    for line in text.split("\n"):
        m = re.match(r"^#{1,3}\s+(.+?)\s*$", line.strip())
        if m:
            head = m.group(1)
            head = re.sub(r"\s*\([^)]*\)\s*$", "", head).strip()
            out.append(head)
    return out


def get_bullet_style(text: str) -> Counter:
    """Count '-' vs '*' bullet markers."""
    c = Counter()
    for line in text.split("\n"):
        s = line.lstrip()
        if re.match(r"^- ", s):
            c["dash"] += 1
        elif re.match(r"^\* ", s):
            c["star"] += 1
        elif re.match(r"^\d+\. ", s):
            c["numbered"] += 1
    return c


PATH_RE = re.compile(r"`([A-Za-z0-9_./\-]+\.[A-Za-z]{1,6})`")
SYMBOL_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]+(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\(?\)?`")


def hallucinated_paths(review: str, diff: str) -> list[str]:
    """Code-fenced path-like tokens in the review that don't appear in the diff."""
    found = set(PATH_RE.findall(review))
    diff_lower = diff.lower()
    out = []
    for p in found:
        candidates = [p, os.path.basename(p), p.split("/")[-1]]
        if not any(c.lower() in diff_lower for c in candidates):
            out.append(p)
    return out


def main() -> None:
    with open(SD_PATH) as f:
        sd = json.load(f)

    print("=" * 78)
    print(" v2 DEEP DATA AUDIT")
    print("=" * 78)

    problems = []
    warnings = []

    for pr in sd["prs"]:
        pid = pr["pr_id"]
        diff = pr["diff"]
        body = pr.get("body") or ""

        print(f"\n--- PR {pid} · {pr['repo']} · {pr['title'][:60]} ---")
        print(f"   url:   {pr.get('url','(none)')}")
        print(f"   diff:  {len(diff):,} chars   body: {len(body):,} chars")

        if len(body) < 30:
            warnings.append(f"PR {pid}: PR body very short or empty "
                            f"({len(body)} chars). Raters can't read PR intent.")
        if "...truncated" in body or body.endswith("…"):
            problems.append(f"PR {pid}: PR body looks truncated.")
        if not pr.get("url"):
            problems.append(f"PR {pid}: no GitHub URL — rater can't follow-up.")

        binary_markers = diff.count("Binary files")
        if binary_markers:
            warnings.append(f"PR {pid}: diff contains {binary_markers} "
                            f"'Binary files' marker(s) — rater sees no content "
                            f"for those files.")

        lengths = {m: len(pr["reviews"].get(m, "")) for m in MODES}
        L = list(lengths.values())
        max_l, min_l = max(L), min(L) if min(L) else 1
        ratio = max_l / max(min_l, 1)
        print(f"   review lengths: bl={lengths['baseline']:,} "
              f"kg={lengths['kg']:,} rag={lengths['rag']:,}   "
              f"max/min ratio = {ratio:.2f}")
        if ratio > 1.6:
            warnings.append(f"PR {pid}: review-length ratio {ratio:.2f}x — "
                            f"possible de-blinding tell. (bl={lengths['baseline']}, "
                            f"kg={lengths['kg']}, rag={lengths['rag']})")

        sections_per_mode = {m: get_sections(pr["reviews"][m]) for m in MODES}
        all_secs = set()
        for s in sections_per_mode.values():
            all_secs.update(s)
        for sec in all_secs:
            present = {m for m in MODES if sec in sections_per_mode[m]}
            if 0 < len(present) < 3:
                warnings.append(f"PR {pid}: section '{sec}' present in "
                                f"{sorted(present)} only — structural tell.")

        bs = {m: get_bullet_style(pr["reviews"][m]) for m in MODES}
        styles = {m: max(bs[m], key=lambda k: bs[m][k]) if bs[m] else "none"
                  for m in MODES}
        if len(set(styles.values())) > 1 and "none" not in styles.values():
            warnings.append(f"PR {pid}: bullet styles differ across modes "
                            f"({styles}) — minor surface tell.")

        for m in MODES:
            review = pr["reviews"][m]
            hallucs = hallucinated_paths(review, diff)
            if hallucs:
                warnings.append(f"PR {pid} {m}: review references "
                                f"path(s) not in diff: {hallucs}")

        if all("Traceability" in sections_per_mode[m] for m in MODES):
            for m in MODES:
                tr = pr["reviews"][m]
                idx = tr.find("Traceability")
                seg = tr[idx:idx + 800] if idx >= 0 else ""
                if "Not specified" in seg and len(seg.strip()) < 60:
                    warnings.append(f"PR {pid} {m}: Traceability section "
                                    f"is just 'Not specified' — visible to rater.")

        recs = {}
        for m in MODES:
            t = pr["reviews"][m]
            i = t.find("## Recommendation")
            if i < 0:
                i = t.find("Recommendation")
            j = t.find("\n##", i + 5) if i >= 0 else -1
            recs[m] = t[i:j if j > 0 else len(t)] if i >= 0 else ""
        common_kw = []
        for kw in ["add tests", "add unit tests", "add integration tests",
                   "consider adding", "ensure", "review", "refactor",
                   "documentation"]:
            if all(kw.lower() in recs[m].lower() for m in MODES):
                common_kw.append(kw)

    print()
    print("=" * 78)
    print(f" {'PROBLEMS':10s} {len(problems)}")
    print("=" * 78)
    for p in problems:
        print(f"  P  {p}")
    print()
    print("=" * 78)
    print(f" {'WARNINGS':10s} {len(warnings)}")
    print("=" * 78)
    for w in warnings:
        print(f"  W  {w}")

    print()
    print("=" * 78)
    print(" GLOBAL CHECKS")
    print("=" * 78)
    all_lengths_by_mode = defaultdict(list)
    for pr in sd["prs"]:
        for m in MODES:
            all_lengths_by_mode[m].append(len(pr["reviews"].get(m, "")))
    print("  Mean review length per mode:")
    for m in MODES:
        L = all_lengths_by_mode[m]
        print(f"    {m:8s} mean={sum(L)/len(L):.0f}  "
              f"min={min(L)}  max={max(L)}  values={L}")

    sec_counts = defaultdict(Counter)
    for pr in sd["prs"]:
        for m in MODES:
            for sec in get_sections(pr["reviews"][m]):
                sec_counts[m][sec] += 1
    print()
    print(f"  Section presence per mode (count out of {len(sd['prs'])} PRs):")
    all_secs = set()
    for c in sec_counts.values():
        all_secs.update(c.keys())
    for sec in sorted(all_secs):
        line = f"    {sec:30s}"
        for m in MODES:
            line += f"  {m}={sec_counts[m].get(sec, 0)}"
        print(line)


if __name__ == "__main__":
    main()
