#!/usr/bin/env python3
"""
build_rag_for_new_seven.py — run RAG retrieval for PRs 27–33 (the v2
expansion).

Mirrors `rebuild_rag_for_v2_contaminated.py` but for the new 7 PRs
added when going from 18 → 25.

Cost: ~$0.005–0.02 per PR (text-embedding-3-small).
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

NEW_PRS = [27, 28, 29, 30, 31, 32, 33]
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
            ev["metadata"]["v2_rag_source"] = "fresh_for_v2_25pr_expansion"
            ev["metadata"]["v2_rag_chunks_copied"] = len(chunks)
            with open(evp, "w") as f:
                json.dump(ev, f, indent=2)
            print(f"  enriched: {evp.relative_to(REPO_ROOT)}")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback; traceback.print_exc()
            return 1

    print(f"\nDone — RAG built for {NEW_PRS}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
