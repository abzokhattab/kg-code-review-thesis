#!/usr/bin/env python3
"""Per-hop-level ablation on Experiment 2 structural injections.

Instead of capping by count, give the LLM edges at specific call-graph
distances:
  hop_0   = no context (baseline)
  hop_1   = only direct callers of the changed function
  hop_1_2 = direct callers + callers of callers
  hop_all = all hops (1+2+3) — the full BFS

This tests: how far into the call graph does the LLM need to see?

Uses multi-hop edges extracted by extract_hops.py.
Idempotent.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path("/Users/akhattab/ai")
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "2026-07-05_injection_exp2" / "harness"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

ENV_PATH = REPO_ROOT / ".env"
if ENV_PATH.exists():
    for line in ENV_PATH.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from common import SCOPES, load_manifest, scope_dir, load_json  # noqa: E402
from expand_dataset import find_dependents  # noqa: E402
from prnote import note  # noqa: E402
from prnote.llm import generate_completion  # noqa: E402

HERE = Path(__file__).resolve().parent
REVIEWS_DIR = HERE / "reviews_hops"
JUDGMENTS_DIR = HERE / "judgments_hops"

GEN_MODEL = "openai:gpt-4o"
JUDGES = ["openai:gpt-4o-mini", "openai:gpt-4o", "gemini:gemini-2.5-flash"]
HOP_LEVELS = ["hop_0", "hop_1", "hop_1_2", "hop_all"]
PRINT_LOCK = threading.Lock()


def load_hops(repo: str) -> dict:
    hf = HERE / f"hops_{repo}.json"
    if hf.exists():
        return json.loads(hf.read_text())
    return {}


def build_hop_context(inj: dict, hops_all: dict, level: str) -> dict | None:
    if level == "hop_0":
        return None

    sym = inj["symbol"]
    all_edges = hops_all.get(sym, [])
    edit_base = Path(inj["edit_file"]).name

    # Filter by hop level
    if level == "hop_1":
        max_hop = 1
    elif level == "hop_1_2":
        max_hop = 2
    else:
        max_hop = 3

    cross, seen = [], set()
    for e in all_edges:
        hop = int(e.get("hop", "1"))
        if hop > max_hop:
            continue
        cf = e.get("caller_file", "")
        if not cf or Path(cf).name == edit_base:
            continue
        key = (cf, e.get("caller", ""), e.get("callee", ""))
        if key in seen:
            continue
        seen.add(key)
        cross.append({
            "from": f"{cf}::{e.get('caller', '')}",
            "to": f"{inj['edit_file']}::{e.get('callee', sym)}",
            "hop": hop,
        })

    # Include grep deps at all levels (they're hop-agnostic)
    deps = find_dependents(inj["edit_file"], str(scope_dir(inj["repo"])),
                           inj["language"])
    dep_list = [{"path": d["path"], "relationship": "imports"} for d in deps]

    if not cross and not dep_list:
        return {
            "changed_files": [{"path": inj["edit_file"]}],
            "dependent_files": [],
            "call_graph_edges": [],
            "functions_changed": [sym or Path(inj["edit_file"]).stem],
        }

    return {
        "changed_files": [{"path": inj["edit_file"]}],
        "dependent_files": dep_list,
        "call_graph_edges": cross,
        "functions_changed": [sym or Path(inj["edit_file"]).stem],
    }


# ── Generation ──────────────────────────────────────────────────────────
def generate_review(inj: dict, level: str, hops_all: dict) -> str:
    out_md = REVIEWS_DIR / inj["id"] / f"{level}.md"
    if out_md.exists() and out_md.stat().st_size > 200:
        return "cached"
    out_md.parent.mkdir(parents=True, exist_ok=True)

    kg_ctx = build_hop_context(inj, hops_all, level)
    mode = "baseline" if level == "hop_0" else "kg"

    delay = 2.0
    for attempt in range(6):
        try:
            text = note.generate_review_direct(
                diff=inj["diff"], pr_title=inj["pr_title"], mode=mode,
                kg_context=kg_ctx, model=GEN_MODEL)
            out_md.write_text(text)
            return "generated"
        except Exception as e:
            if attempt == 5:
                out_md.write_text(f"ERROR: {e}")
                return f"ERROR: {str(e)[:120]}"
            sleep = delay * (2 ** attempt) * (1 + random.random() * 0.3)
            time.sleep(min(sleep, 90))


# ── Judging ─────────────────────────────────────────────────────────────
JUDGE_SYSTEM = (
    "You are a strict evaluator of code-review quality. You will be given a "
    "ground-truth defect that was deliberately injected into a pull request, "
    "and a generated review. Decide whether the review DETECTS this specific "
    "defect.\n\n"
    "Rules:\n"
    "- DETECTED only if the review identifies the cross-file breakage: it must "
    "point at the dependent code in the OTHER file that the change breaks, or "
    "name that file/usage specifically.\n"
    "- A generic hedge like 'make sure callers are updated' or 'add tests' with "
    "no specific dependent identified is NOT detection.\n"
    'Respond with strict JSON only: {"detected": true|false, "reason": "<one sentence>"}'
)


def judge_one(inj: dict, level: str, judge_model: str) -> dict | None:
    jm_safe = judge_model.replace(":", "_").replace("/", "_")
    out_j = JUDGMENTS_DIR / inj["id"] / f"{level}__{jm_safe}.json"
    if out_j.exists():
        try:
            return json.loads(out_j.read_text())
        except Exception:
            pass
    out_j.parent.mkdir(parents=True, exist_ok=True)

    review_md = REVIEWS_DIR / inj["id"] / f"{level}.md"
    if not review_md.exists():
        return None
    review_text = review_md.read_text()
    if review_text.startswith("ERROR"):
        result = {"detected": False, "error": True, "judge": judge_model}
        out_j.write_text(json.dumps(result, indent=2))
        return result

    deps = [Path(d).name for d in inj["true_dependents"]]
    prompt = (
        f"GROUND-TRUTH INJECTED DEFECT\n"
        f"- operator: {inj['operator']}\n"
        f"- edit site: {inj['edit_file']} "
        f"({inj['old'].strip()[:120]} -> {inj['new'].strip()[:120]})\n"
        f"- breaks at: {', '.join(deps)}\n"
        f"- known dependents of the changed file: {deps}\n"
        f"- what a correct review must say: {inj['ground_truth']}\n\n"
        f"GENERATED REVIEW\n```\n{review_text[:6000]}\n```\n\n"
        "Does the review DETECT the injected cross-file defect per the rules?")

    delay = 2.0
    for attempt in range(6):
        try:
            raw = generate_completion(prompt=prompt, system=JUDGE_SYSTEM,
                                      model=judge_model, temperature=0.0)
            txt = raw.strip()
            if txt.startswith("```"):
                txt = txt.strip("`")
            start, end = txt.find("{"), txt.rfind("}") + 1
            data = json.loads(txt[start:end])
            result = {"detected": bool(data.get("detected")),
                      "reason": data.get("reason", ""), "judge": judge_model}
            out_j.write_text(json.dumps(result, indent=2))
            return result
        except Exception as e:
            if attempt == 5:
                result = {"detected": None, "reason": f"error: {str(e)[:150]}",
                          "judge": judge_model}
                out_j.write_text(json.dumps(result, indent=2))
                return result
            time.sleep(min(delay * (2 ** attempt) * (1 + random.random() * 0.3), 90))


def majority_detected(inj: dict, level: str) -> bool:
    votes = 0
    for jm in JUDGES:
        jm_safe = jm.replace(":", "_").replace("/", "_")
        jf = JUDGMENTS_DIR / inj["id"] / f"{level}__{jm_safe}.json"
        if jf.exists():
            d = json.loads(jf.read_text())
            if d.get("detected"):
                votes += 1
    return votes >= 2


# ── Main ────────────────────────────────────────────────────────────────
def main():
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    JUDGMENTS_DIR.mkdir(parents=True, exist_ok=True)

    inj_all = load_manifest()
    structural = [i for i in inj_all if i["band"].startswith("S")]
    hops = {repo: load_hops(repo) for repo in SCOPES}

    # Report edge counts
    print(f"=== Per-hop ablation ===")
    print(f"Injections: {len(structural)} structural")
    print(f"Hop levels: {HOP_LEVELS}")
    print()

    for inj in structural:
        sym = inj["symbol"]
        repo_hops = hops[inj["repo"]].get(sym, [])
        h1 = len([e for e in repo_hops if e["hop"] == "1"])
        h2 = len([e for e in repo_hops if e["hop"] == "2"])
        h3 = len([e for e in repo_hops if e["hop"] == "3"])
        print(f"  {inj['id']:25s}  h1={h1:3d}  h2={h2:3d}  h3={h3:3d}")
    print()

    # Stage 1: generate reviews
    for level in HOP_LEVELS:
        gen_tasks = []
        for inj in structural:
            out_md = REVIEWS_DIR / inj["id"] / f"{level}.md"
            if out_md.exists() and out_md.stat().st_size > 200:
                continue
            gen_tasks.append(inj)
        if not gen_tasks:
            print(f"[gen] {level}: all {len(structural)} cached")
            continue
        print(f"[gen] {level}: {len(gen_tasks)} to generate...", flush=True)
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = {ex.submit(generate_review, inj, level, hops[inj["repo"]]): inj["id"]
                    for inj in gen_tasks}
            done = 0
            for fut in as_completed(futs):
                done += 1
                res = fut.result()
                if done % 10 == 0 or done == len(gen_tasks):
                    with PRINT_LOCK:
                        print(f"  [{done}/{len(gen_tasks)}] {futs[fut]}: {res}", flush=True)
        print()

    # Stage 2: judge reviews
    for level in HOP_LEVELS:
        judge_tasks = []
        for inj in structural:
            for jm in JUDGES:
                jm_safe = jm.replace(":", "_").replace("/", "_")
                out_j = JUDGMENTS_DIR / inj["id"] / f"{level}__{jm_safe}.json"
                if out_j.exists():
                    try:
                        if json.loads(out_j.read_text()).get("detected") is not None:
                            continue
                    except Exception:
                        pass
                judge_tasks.append((inj, jm))
        if not judge_tasks:
            print(f"[judge] {level}: all cached")
            continue
        print(f"[judge] {level}: {len(judge_tasks)} calls...", flush=True)
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(judge_one, inj, level, jm): (inj["id"], jm)
                    for inj, jm in judge_tasks}
            done = 0
            for fut in as_completed(futs):
                done += 1
                if done % 20 == 0 or done == len(judge_tasks):
                    with PRINT_LOCK:
                        print(f"  [{done}/{len(judge_tasks)}]", flush=True)
        print()

    # Summary — all 28
    print("=" * 55)
    print("RESULTS: Per-hop ablation (all 28 structural)")
    print("=" * 55)
    print(f"{'Level':>10} {'Detected':>10} {'Rate':>8}")
    print("-" * 35)
    for level in HOP_LEVELS:
        detected = sum(1 for inj in structural if majority_detected(inj, level))
        rate = detected / len(structural)
        print(f"{level:>10} {detected:>6}/28   {rate:.1%}")

    # Summary — only the ones with hop-1 edges (non-zero signal)
    has_edges = [inj for inj in structural
                 if len(hops[inj["repo"]].get(inj["symbol"], [])) > 0]
    print()
    print(f"RESULTS: Per-hop ablation (only injections with Joern edges, n={len(has_edges)})")
    print("=" * 55)
    print(f"{'Level':>10} {'Detected':>10} {'Rate':>8}")
    print("-" * 35)
    for level in HOP_LEVELS:
        detected = sum(1 for inj in has_edges if majority_detected(inj, level))
        rate = detected / len(has_edges) if has_edges else 0
        print(f"{level:>10} {detected:>6}/{len(has_edges)}   {rate:.1%}")


if __name__ == "__main__":
    main()
