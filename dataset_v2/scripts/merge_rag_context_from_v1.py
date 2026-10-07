#!/usr/bin/env python3
"""
merge_rag_context_from_v1.py — Copy similar_chunks and rag_evidence
from the v1 evidence packs into the v2 packs.

Why this is safe:

  RAG retrieval is a function of (changed_files, repo state at PR
  time). Both are identical between v1 and v2 — only the PR body
  and the diff body changed in v2. So the RAG retrieval result is
  the same in both versions; copying avoids needing to re-run
  scripts/build_rag_and_enrich.py (which depends on a vector
  embedding index that is not always set up locally).

What is *not* copied:

  * pr.title — v2 has the recovered real title, v1 had a
    placeholder for some PRs.
  * pr.body — v2 has the recovered full body, v1 was empty or
    truncated for many.
  * full_diff — v2 has the untruncated diff, v1 was capped at
    15 kB.
  * changed_files — already identical (we verified for PRs 14, 18;
    extend if needed).

What *is* copied:
  * similar_chunks
  * rag_evidence

If a PR has no v1 counterpart (it does not in the current 18-PR
set), this script logs and skips it.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
V1_DIR = REPO_ROOT / "data" / "luca_prs_fixed"
V2_DIR = REPO_ROOT / "data" / "luca_prs_v2"


def merge_one(pr_id: int) -> tuple[bool, str]:
    v1_path = V1_DIR / f"pr{pr_id}_evidence.json"
    v2_path = V2_DIR / f"pr{pr_id}_evidence.json"

    if not v2_path.exists():
        return False, f"v2 evidence missing"
    if not v1_path.exists():
        return False, f"no v1 counterpart at {v1_path.relative_to(REPO_ROOT)}"

    with open(v1_path) as f:
        v1 = json.load(f)
    with open(v2_path) as f:
        v2 = json.load(f)

    # Verify changed_files paths line up (sanity)
    v1_paths = {c.get("path", "") for c in v1.get("changed_files", []) if isinstance(c, dict)}
    v2_paths = {c.get("path", "") for c in v2.get("changed_files", []) if isinstance(c, dict)}
    if v1_paths != v2_paths:
        return False, (f"changed_files mismatch — v1 has "
                       f"{len(v1_paths - v2_paths)} extra, v2 has "
                       f"{len(v2_paths - v1_paths)} extra")

    # Copy RAG fields
    similar = v1.get("similar_chunks", [])
    rag_ev = v1.get("rag_evidence", {})
    v2["similar_chunks"] = similar
    v2["rag_evidence"] = rag_ev

    # Annotate provenance
    v2.setdefault("metadata", {})
    v2["metadata"]["v2_rag_source"] = "merged_from_v1"
    v2["metadata"]["v2_rag_chunks_copied"] = len(similar)

    with open(v2_path, "w") as f:
        json.dump(v2, f, indent=2)

    return True, f"copied {len(similar)} similar_chunks + rag_evidence"


def main() -> int:
    pr_ids = sorted(
        int(f.replace("pr", "").replace("_evidence.json", ""))
        for f in os.listdir(V2_DIR)
        if f.startswith("pr") and f.endswith("_evidence.json")
    )

    print(f"Merging v1 RAG context into {len(pr_ids)} v2 evidence packs")
    print(f"V1: {V1_DIR.relative_to(REPO_ROOT)}")
    print(f"V2: {V2_DIR.relative_to(REPO_ROOT)}")
    print("-" * 70)

    failed: list[tuple[int, str]] = []
    for pid in pr_ids:
        ok, msg = merge_one(pid)
        marker = "OK  " if ok else "FAIL"
        print(f"  {marker}  PR{pid:>2}: {msg}")
        if not ok:
            failed.append((pid, msg))

    print()
    if failed:
        print(f"{len(failed)} failures. Address before regenerating reviews.")
        return 1
    print(f"All {len(pr_ids)} v2 packs now carry RAG context.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
