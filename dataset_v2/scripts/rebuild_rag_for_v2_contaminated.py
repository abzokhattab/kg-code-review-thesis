#!/usr/bin/env python3
"""
rebuild_rag_for_v2_contaminated.py — re-run RAG retrieval for the 2
PRs whose v1 changed_files list was contaminated.

Reads:  data/luca_prs_v2/pr{1,2}_evidence.json (clean changed_files)
Writes: data/luca_prs_v2/pr{1,2}_evidence.json (similar_chunks + rag_evidence)
        data/rag_indices/v2_pr{1,2}/...                  (cached embeddings)

For the other 16 v2 PRs, the v1 RAG context is reusable (their
changed_files lists are byte-identical between v1 and v2; verified by
audit). Those packs are filled in by
`merge_rag_context_from_v1.py`.

Cost: ~$0.005 per PR (text-embedding-3-small @ $0.02/1M tokens).

Why this is needed:

Audit (`dataset_v2/scripts/audit_v1_dataset.py` follow-up) showed
that v1 evidence for PR 1 contains 165 changed_files when the actual
GitHub PR has 3, and v1 PR 2 contains 30 when the actual PR has 10.
The v1 RAG retrieval for these PRs ran against the contaminated
file list — so the chunks it surfaced are not anchored to the
files that actually changed. Reusing the v1 RAG context in v2 would
inherit this defect.

This script imports `scripts/build_rag_and_enrich.py` and overrides
its module globals so the same retrieval pipeline runs against the
v2 evidence packs.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# Load .env early so OPENAI_API_KEY is available for the embedding calls.
ENV_PATH = REPO_ROOT / ".env"
if ENV_PATH.exists():
    for line in ENV_PATH.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

CONTAMINATED_PRS = [1, 2]

V2_EVIDENCE_DIR = REPO_ROOT / "data" / "luca_prs_v2"
V2_INDEX_DIR = REPO_ROOT / "data" / "rag_indices_v2"
V2_INDEX_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    bre = importlib.import_module("scripts.build_rag_and_enrich")
    bre.EVIDENCE_DIR = V2_EVIDENCE_DIR
    bre.INDEX_DIR = V2_INDEX_DIR

    print("=" * 60)
    print(f"Re-running RAG for v2 contaminated PRs: {CONTAMINATED_PRS}")
    print(f"  V2_EVIDENCE_DIR: {V2_EVIDENCE_DIR.relative_to(REPO_ROOT)}")
    print(f"  V2_INDEX_DIR:    {V2_INDEX_DIR.relative_to(REPO_ROOT)}")
    print("=" * 60)

    client = bre.get_client()

    for pr_id in CONTAMINATED_PRS:
        print(f"\n--- PR{pr_id} ({bre.PR_REPO_MAP[pr_id]}) ---")
        try:
            chunks = bre.build_and_query_for_pr(pr_id, client, force_rebuild=True)
            print(f"  retrieved {len(chunks)} similar chunks")
            if chunks:
                top = chunks[0]
                print(f"  top match: {top['file']}:{top['start_line']} "
                      f"(sim={top['similarity']:.3f})")
            bre.enrich_evidence(pr_id, chunks)

            # Annotate provenance
            import json
            evp = V2_EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
            with open(evp) as f:
                ev = json.load(f)
            ev.setdefault("metadata", {})
            ev["metadata"]["v2_rag_source"] = "rebuilt_v2_clean_changed_files"
            ev["metadata"]["v2_rag_chunks_copied"] = len(chunks)
            with open(evp, "w") as f:
                json.dump(ev, f, indent=2)

            print(f"  enriched: {evp.relative_to(REPO_ROOT)}")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback; traceback.print_exc()
            return 1

    print()
    print(f"Done — RAG re-built for {CONTAMINATED_PRS}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
