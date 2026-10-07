#!/usr/bin/env python3
"""Stage C: generate reviews for every (injection x arm).  PAID (gpt-4o).

- Idempotent: skips any out/reviews/<inj_id>/<arm>.md that already exists
  and is non-empty.
- Parallel: bounded thread pool (--workers, default 8), exponential backoff
  on rate limits.
- Contexts (pre-reg §7):
    baseline           diff only
    kg                 deployed Joern CPG edges + grep dependent_files
    rag                prnote retrieval, top_k=10, query = first 2KB of changed file
    hybrid             kg + rag
    kg_idealised       manifest true_dependents (symbol-level static resolver)
    kg_joern_inherit   Joern edges + static import/inherits edges (the augmentation)

Usage:
  source load_env.sh && python3 run_modes.py [--arms kg rag] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ALL_ARMS, ARMS, GEN_MODEL, OUT, REPO_ROOT, SCOPES, load_json,  # noqa: E402
                    load_manifest, scope_dir)

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from prnote import note, rag  # noqa: E402
from expand_dataset import find_dependents  # noqa: E402

REVIEWS = OUT / "reviews"
PRINT_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# context builders
# ---------------------------------------------------------------------------
def joern_edges(repo: str) -> dict:
    return load_json(OUT / "joern" / f"edges_{repo}.json", default={}) or {}


def joern_kg_context(inj: dict, edges_all: dict) -> dict:
    """Deployed-pipeline composition: Joern cross-file call edges + grep
    dependent_files (mirrors run_joern_kg.joern_kg_context)."""
    edit_base = Path(inj["edit_file"]).name
    raw = edges_all.get(inj["symbol"] or "", [])
    cross, seen = [], set()
    for e in raw:
        cf = e.get("caller_file", "")
        if not cf or Path(cf).name == edit_base:
            continue
        key = (cf, e.get("caller", ""), e.get("callee", ""))
        if key in seen:
            continue
        seen.add(key)
        cross.append({"from": f"{cf}::{e.get('caller','')}",
                      "to": f"{inj['edit_file']}::{e.get('callee', inj['symbol'])}"})
    deps = find_dependents(inj["edit_file"], str(scope_dir(inj["repo"])),
                           inj["language"])
    return {
        "changed_files": [{"path": inj["edit_file"]}],
        "dependent_files": [{"path": d["path"], "relationship": "imports"} for d in deps],
        "call_graph_edges": cross[:40],
        "functions_changed": [inj["symbol"] or Path(inj["edit_file"]).stem],
    }


def deps_only_kg_context(inj: dict, edges_all: dict) -> dict:
    """Deployed KG minus the Joern call edges: the lexical grep file list only."""
    ctx = joern_kg_context(inj, edges_all)
    ctx["call_graph_edges"] = []
    return ctx


def edges_only_kg_context(inj: dict, edges_all: dict) -> dict:
    """Deployed KG minus the lexical file list: Joern call edges only."""
    ctx = joern_kg_context(inj, edges_all)
    ctx["dependent_files"] = []
    return ctx


def idealised_kg_context(inj: dict) -> dict:
    """Ground-truth static resolver output (the prototype's 8/8 ceiling)."""
    return {
        "changed_files": [{"path": inj["edit_file"]}],
        "dependent_files": [{"path": d, "relationship": "imports/uses"}
                            for d in inj["true_dependents"]],
        "call_graph_edges": [{"from": d,
                              "to": f"{Path(inj['edit_file']).stem}.{inj['symbol']}"}
                             for d in inj["true_dependents"]],
        "functions_changed": [inj["symbol"] or Path(inj["edit_file"]).stem],
    }


def inherit_kg_context(inj: dict, edges_all: dict) -> dict:
    """The pre-registered augmentation arm: deployed Joern edges PLUS
    statically-resolved import/INHERITS_FROM edges from the manifest's
    independent resolver."""
    ctx = joern_kg_context(inj, edges_all)
    existing = {e["from"].split("::")[0] for e in ctx["call_graph_edges"]}
    extra = []
    for d in inj["true_dependents"]:
        if d not in existing:
            rel = ("INHERITS_FROM" if inj["band"] == "S4" else "imports")
            extra.append({"from": d,
                          "to": f"{inj['edit_file']}::{inj['symbol']}",
                          "relationship": rel})
    ctx["call_graph_edges"] = ctx["call_graph_edges"] + extra
    dep_paths = {x["path"] for x in ctx["dependent_files"]}
    for d in inj["true_dependents"]:
        if d not in dep_paths:
            ctx["dependent_files"].append({"path": d, "relationship": "imports"})
    return ctx


class RagIndex:
    """Per-repo query wrapper (loaded once, thread-safe reads)."""
    def __init__(self):
        self._lock = threading.Lock()
        self._loaded = {}

    def context_for(self, inj: dict) -> dict:
        repo = inj["repo"]
        index_dir = OUT / "rag" / repo
        scope = scope_dir(repo)
        changed = (scope / inj["edit_file"]).read_text(errors="ignore")
        with self._lock:  # prnote query loads index from disk; serialize loads
            results = rag.query_rag(index_dir=str(index_dir),
                                    query_code=changed[:2000],
                                    top_k=10, use_openai=True)
        chunks = []
        for r in results:
            m = r["metadata"]
            if m["file"] == inj["edit_file"]:
                continue
            src = scope / m["file"]
            preview = ""
            if src.exists():
                lines = src.read_text(errors="ignore").splitlines()
                preview = "\n".join(
                    lines[max(0, m.get("start_line", 1) - 1):m.get("end_line", 1)])[:800]
            chunks.append({"file": m["file"], "start_line": m.get("start_line"),
                           "end_line": m.get("end_line"),
                           "similarity": r.get("similarity", 0.0),
                           "content_preview": preview})
        retrieved = {Path(c["file"]).name for c in chunks}
        true_dep = {Path(d).name for d in inj["true_dependents"]}
        diag = {"n_retrieved_other_file": len(chunks),
                "true_dependents": sorted(true_dep),
                "dependents_retrieved": sorted(true_dep & retrieved),
                "n_dependents_retrieved": len(true_dep & retrieved)}
        return {"similar_chunks": chunks[:8]}, diag


# ---------------------------------------------------------------------------
# generation
# ---------------------------------------------------------------------------
def generate_one(inj: dict, arm: str, edges_all: dict, ragx: RagIndex) -> str:
    out_md = REVIEWS / inj["id"] / f"{arm}.md"
    if out_md.exists() and out_md.stat().st_size > 200:
        return "cached"
    out_md.parent.mkdir(parents=True, exist_ok=True)

    kg_ctx = rag_ctx = None
    if arm in ("kg", "hybrid"):
        kg_ctx = joern_kg_context(inj, edges_all)
    elif arm == "kg_idealised":
        kg_ctx = idealised_kg_context(inj)
    elif arm == "kg_joern_inherit":
        kg_ctx = inherit_kg_context(inj, edges_all)
    elif arm == "kg_deps_only":
        kg_ctx = deps_only_kg_context(inj, edges_all)
    elif arm == "kg_edges_only":
        kg_ctx = edges_only_kg_context(inj, edges_all)
    if arm in ("rag", "hybrid"):
        rag_ctx, diag = ragx.context_for(inj)
        if arm == "rag":
            (REVIEWS / inj["id"] / "rag_diagnostic.json").write_text(
                json.dumps(diag, indent=2))

    mode = {"baseline": "baseline", "kg": "kg", "rag": "rag", "hybrid": "hybrid",
            "kg_idealised": "kg", "kg_joern_inherit": "kg",
            "kg_deps_only": "kg", "kg_edges_only": "kg"}[arm]

    delay = 2.0
    for attempt in range(6):
        try:
            text = note.generate_review_direct(
                diff=inj["diff"], pr_title=inj["pr_title"], mode=mode,
                kg_context=kg_ctx, rag_context=rag_ctx, model=GEN_MODEL)
            out_md.write_text(text)
            return "generated"
        except Exception as e:
            msg = str(e)
            if attempt == 5:
                return f"ERROR: {msg[:150]}"
            sleep = delay * (2 ** attempt) * (1 + random.random() * 0.3)
            with PRINT_LOCK:
                print(f"  [retry {attempt+1}] {inj['id']}/{arm}: {msg[:90]} "
                      f"(sleep {sleep:.0f}s)", flush=True)
            time.sleep(min(sleep, 90))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", default=ARMS, choices=ALL_ARMS)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    inj_all = load_manifest()
    edges = {repo: joern_edges(repo) for repo in SCOPES}
    ragx = RagIndex()

    tasks = []
    for inj in inj_all:
        for arm in args.arms:
            out_md = REVIEWS / inj["id"] / f"{arm}.md"
            if out_md.exists() and out_md.stat().st_size > 200:
                continue
            tasks.append((inj, arm))

    print(f"{len(tasks)} review generations to run "
          f"({len(inj_all)} injections x {len(args.arms)} arms, cached skipped)")
    if args.dry_run:
        return

    done = failed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(generate_one, inj, arm, edges[inj["repo"]], ragx):
                (inj["id"], arm) for inj, arm in tasks}
        for fut in as_completed(futs):
            inj_id, arm = futs[fut]
            res = fut.result()
            done += 1
            if res.startswith("ERROR"):
                failed += 1
                with PRINT_LOCK:
                    print(f"[{done}/{len(tasks)}] {inj_id}/{arm}: {res}", flush=True)
            elif done % 10 == 0 or done == len(tasks):
                with PRINT_LOCK:
                    print(f"[{done}/{len(tasks)}] latest: {inj_id}/{arm} ({res})",
                          flush=True)
    print(f"DONE_STAGE_C generated={done-failed} failed={failed}")


if __name__ == "__main__":
    main()
