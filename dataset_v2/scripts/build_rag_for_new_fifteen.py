#!/usr/bin/env python3
"""
build_rag_for_new_fifteen.py — run RAG retrieval for PRs 34–48 (the
2026-05-12 expansion from 25 → 40 PRs).

Mirrors `build_rag_for_new_seven.py`. Uses the same v2 index dir so
all 40 PRs share one consistent set of embeddings.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

ENV_PATH = REPO_ROOT / ".env"
if ENV_PATH.exists():
    for line in ENV_PATH.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

NEW_PRS = list(range(34, 49))  # 34..48 inclusive
V2_EVIDENCE_DIR = REPO_ROOT / "data" / "luca_prs_v2"
V2_INDEX_DIR    = REPO_ROOT / "data" / "rag_indices_v2"
V2_INDEX_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    bre = importlib.import_module("scripts.build_rag_and_enrich")
    bre.EVIDENCE_DIR = V2_EVIDENCE_DIR
    bre.INDEX_DIR    = V2_INDEX_DIR

    print("=" * 60)
    print(f"Running RAG for new v2 PRs: {NEW_PRS}")
    print(f"  V2_EVIDENCE_DIR: {V2_EVIDENCE_DIR.relative_to(REPO_ROOT)}")
    print(f"  V2_INDEX_DIR:    {V2_INDEX_DIR.relative_to(REPO_ROOT)}")
    print("=" * 60)

    client = bre.get_client()

    failed: list[int] = []

    for pr_id in NEW_PRS:
        repo = bre.PR_REPO_MAP.get(pr_id, "?")
        print(f"\n--- PR{pr_id} ({repo}) ---", flush=True)
        try:
            chunks = bre.build_and_query_for_pr(pr_id, client, force_rebuild=True)
            print(f"  retrieved {len(chunks)} similar chunks")
            if chunks:
                top = chunks[0]
                print(f"  top match: {top['file']}:{top['start_line']} "
                      f"(sim={top['similarity']:.3f})")
            bre.enrich_evidence(pr_id, chunks)
            evp = V2_EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
            with open(evp) as f:
                ev = json.load(f)
            ev.setdefault("metadata", {})
            ev["metadata"]["v2_rag_source"] = "fresh_for_v2_40pr_expansion"
            ev["metadata"]["v2_rag_chunks_copied"] = len(chunks)
            with open(evp, "w") as f:
                json.dump(ev, f, indent=2)
            print(f"  enriched: {evp.relative_to(REPO_ROOT)}")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback; traceback.print_exc()
            failed.append(pr_id)

    if failed:
        print(f"\nDone — {len(NEW_PRS) - len(failed)}/{len(NEW_PRS)} succeeded.")
        print(f"Failed: {failed}")
        return 1
    print(f"\nDone — RAG built for all {len(NEW_PRS)} new PRs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
