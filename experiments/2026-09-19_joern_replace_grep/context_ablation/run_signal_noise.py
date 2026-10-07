#!/usr/bin/env python3
"""Signal vs. noise ablation on Experiment 2 structural injections.

Controlled design inspired by GSM-DC (Yang et al., EMNLP 2025):
hold context QUANTITY constant, vary RELEVANCE.

Arms:
  baseline      = diff only                              (reuse Exp2)
  kg_deployed   = diff + Joern edges + grep deps         (reuse Exp2)
  kg_idealised  = diff + ground-truth dependents         (reuse Exp2)
  relevant_only = diff + only Joern edges that point at true dependents
  noise_matched = diff + same NUMBER of edges as kg_deployed, but
                  drawn from OTHER symbols in the same repo

If relevant_only >> kg_deployed, the signal is diluted by irrelevant edges.
If noise_matched ≈ baseline, the LLM needs real edges, not just "something."
If noise_matched ≈ kg_deployed, the LLM is cued by the mere presence of
dependency info regardless of correctness — a weaker finding.

Only relevant_only and noise_matched need new generations.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
import threading
from collections import defaultdict
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

from common import OUT as EXP2_OUT, SCOPES, load_manifest, scope_dir, load_json  # noqa: E402
from expand_dataset import find_dependents  # noqa: E402
from prnote import note  # noqa: E402
from prnote.llm import generate_completion  # noqa: E402

HERE = Path(__file__).resolve().parent
REVIEWS_DIR = HERE / "reviews_signal"
JUDGMENTS_DIR = HERE / "judgments_signal"

GEN_MODEL = "openai:gpt-4o"
JUDGES = ["openai:gpt-4o-mini", "openai:gpt-4o", "gemini:gemini-2.5-flash"]
SEED = 2026
NEW_ARMS = ["relevant_only", "noise_matched"]
PRINT_LOCK = threading.Lock()


def joern_edges(repo: str) -> dict:
    return load_json(EXP2_OUT / "joern" / f"edges_{repo}.json", default={}) or {}


def deployed_kg_context(inj: dict, edges_all: dict) -> dict:
    """Reproduce the deployed KG arm's context (same as run_modes.joern_kg_context)."""
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
        cross.append({"from": f"{cf}::{e.get('caller', '')}",
                      "to": f"{inj['edit_file']}::{e.get('callee', inj['symbol'])}"})
    deps = find_dependents(inj["edit_file"], str(scope_dir(inj["repo"])),
                           inj["language"])
    dep_list = [{"path": d["path"], "relationship": "imports"} for d in deps]
    return {
        "changed_files": [{"path": inj["edit_file"]}],
        "dependent_files": dep_list,
        "call_graph_edges": cross[:40],
        "functions_changed": [inj["symbol"] or Path(inj["edit_file"]).stem],
    }


def relevant_only_context(inj: dict, edges_all: dict) -> dict:
    """Only Joern edges whose caller_file is a true dependent."""
    true_bases = {Path(d).name for d in inj["true_dependents"]}
    edit_base = Path(inj["edit_file"]).name
    raw = edges_all.get(inj["symbol"] or "", [])
    cross, seen = [], set()
    for e in raw:
        cf = e.get("caller_file", "")
        if not cf or Path(cf).name == edit_base:
            continue
        if Path(cf).name not in true_bases:
            continue
        key = (cf, e.get("caller", ""), e.get("callee", ""))
        if key in seen:
            continue
        seen.add(key)
        cross.append({"from": f"{cf}::{e.get('caller', '')}",
                      "to": f"{inj['edit_file']}::{e.get('callee', inj['symbol'])}"})
    # Also filter deps to only true dependents
    true_paths = set(inj["true_dependents"])
    deps = find_dependents(inj["edit_file"], str(scope_dir(inj["repo"])),
                           inj["language"])
    dep_list = [{"path": d["path"], "relationship": "imports"}
                for d in deps if d["path"] in true_paths]
    return {
        "changed_files": [{"path": inj["edit_file"]}],
        "dependent_files": dep_list,
        "call_graph_edges": cross,
        "functions_changed": [inj["symbol"] or Path(inj["edit_file"]).stem],
    }


def noise_matched_context(inj: dict, edges_all: dict, all_repo_edges: dict) -> dict:
    """Same number of edges as deployed kg, but from WRONG symbols."""
    # First, count how many edges + deps the deployed arm gives
    deployed = deployed_kg_context(inj, edges_all)
    n_edges = len(deployed["call_graph_edges"])
    n_deps = len(deployed["dependent_files"])

    # Collect edges from OTHER symbols in the same repo
    rng = random.Random(SEED + hash(inj["id"]))
    noise_pool = []
    for sym, elist in all_repo_edges.items():
        if sym == inj["symbol"]:
            continue
        edit_base = Path(inj["edit_file"]).name
        for e in elist:
            cf = e.get("caller_file", "")
            if not cf or Path(cf).name == edit_base:
                continue
            noise_pool.append({"from": f"{cf}::{e.get('caller', '')}",
                               "to": f"{inj['edit_file']}::{e.get('callee', sym)}"})

    rng.shuffle(noise_pool)
    noise_edges = noise_pool[:n_edges]

    # For deps: use random files from the scope that are NOT true dependents
    true_paths = set(inj["true_dependents"])
    scope = scope_dir(inj["repo"])
    lang_ext = {"python": ".py", "java": ".java", "typescript": ".ts"}[inj["language"]]
    all_files = [str(p.relative_to(scope)) for p in scope.rglob(f"*{lang_ext}")
                 if p.is_file()]
    noise_dep_pool = [f for f in all_files
                      if f not in true_paths and f != inj["edit_file"]]
    rng.shuffle(noise_dep_pool)
    noise_deps = [{"path": f, "relationship": "imports"} for f in noise_dep_pool[:n_deps]]

    return {
        "changed_files": [{"path": inj["edit_file"]}],
        "dependent_files": noise_deps,
        "call_graph_edges": noise_edges,
        "functions_changed": [inj["symbol"] or Path(inj["edit_file"]).stem],
    }


# ── Generation ──────────────────────────────────────────────────────────
def generate_review(inj: dict, arm: str, edges_all: dict, all_repo_edges: dict) -> str:
    out_md = REVIEWS_DIR / inj["id"] / f"{arm}.md"
    if out_md.exists() and out_md.stat().st_size > 200:
        return "cached"
    out_md.parent.mkdir(parents=True, exist_ok=True)

    if arm == "relevant_only":
        kg_ctx = relevant_only_context(inj, edges_all)
    elif arm == "noise_matched":
        kg_ctx = noise_matched_context(inj, edges_all, all_repo_edges)
    else:
        return "unknown arm"

    delay = 2.0
    for attempt in range(6):
        try:
            text = note.generate_review_direct(
                diff=inj["diff"], pr_title=inj["pr_title"], mode="kg",
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


def judge_one(inj: dict, arm: str, judge_model: str) -> dict | None:
    jm_safe = judge_model.replace(":", "_").replace("/", "_")
    out_j = JUDGMENTS_DIR / inj["id"] / f"{arm}__{jm_safe}.json"
    if out_j.exists():
        try:
            return json.loads(out_j.read_text())
        except Exception:
            pass
    out_j.parent.mkdir(parents=True, exist_ok=True)

    review_md = REVIEWS_DIR / inj["id"] / f"{arm}.md"
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


def majority_detected(inj_id: str, arm: str) -> bool:
    votes = 0
    for jm in JUDGES:
        jm_safe = jm.replace(":", "_").replace("/", "_")
        jf = JUDGMENTS_DIR / inj_id / f"{arm}__{jm_safe}.json"
        if jf.exists():
            d = json.loads(jf.read_text())
            if d.get("detected"):
                votes += 1
    return votes >= 2


def exp2_majority(inj_id: str, arm: str) -> bool:
    """Read detection from original Experiment 2 judgments."""
    votes = 0
    for jm in JUDGES:
        jm_safe = jm.replace(":", "_").replace("/", "_")
        jf = EXP2_OUT / "judgments" / inj_id / f"{arm}__{jm_safe}.json"
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
    edges = {repo: joern_edges(repo) for repo in SCOPES}

    print("=== Signal vs. Noise Ablation ===")
    print(f"Injections: {len(structural)} structural")
    print(f"New arms: {NEW_ARMS}")
    print(f"Reusing from Exp2: baseline, kg, kg_idealised")
    print()

    # Diagnostic: how many edges per arm per injection
    print("Context size per injection:")
    for inj in structural:
        deployed = deployed_kg_context(inj, edges[inj["repo"]])
        relevant = relevant_only_context(inj, edges[inj["repo"]])
        n_dep = len(deployed["call_graph_edges"]) + len(deployed["dependent_files"])
        n_rel = len(relevant["call_graph_edges"]) + len(relevant["dependent_files"])
        print(f"  {inj['id']:25s}  deployed={n_dep:3d}  relevant={n_rel:3d}")
    print()

    # Stage 1: generate reviews for new arms
    for arm in NEW_ARMS:
        gen_tasks = []
        for inj in structural:
            out_md = REVIEWS_DIR / inj["id"] / f"{arm}.md"
            if out_md.exists() and out_md.stat().st_size > 200:
                continue
            gen_tasks.append(inj)
        if not gen_tasks:
            print(f"[gen] {arm}: all {len(structural)} cached")
            continue
        print(f"[gen] {arm}: {len(gen_tasks)} to generate...", flush=True)
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = {ex.submit(generate_review, inj, arm, edges[inj["repo"]],
                              edges[inj["repo"]]): inj["id"]
                    for inj in gen_tasks}
            done = 0
            for fut in as_completed(futs):
                done += 1
                res = fut.result()
                if done % 10 == 0 or done == len(gen_tasks):
                    with PRINT_LOCK:
                        print(f"  [{done}/{len(gen_tasks)}] {futs[fut]}: {res}", flush=True)
        print()

    # Stage 2: judge new arms
    for arm in NEW_ARMS:
        judge_tasks = []
        for inj in structural:
            for jm in JUDGES:
                jm_safe = jm.replace(":", "_").replace("/", "_")
                out_j = JUDGMENTS_DIR / inj["id"] / f"{arm}__{jm_safe}.json"
                if out_j.exists():
                    try:
                        if json.loads(out_j.read_text()).get("detected") is not None:
                            continue
                    except Exception:
                        pass
                judge_tasks.append((inj, jm))
        if not judge_tasks:
            print(f"[judge] {arm}: all cached")
            continue
        print(f"[judge] {arm}: {len(judge_tasks)} calls...", flush=True)
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(judge_one, inj, arm, jm): (inj["id"], jm)
                    for inj, jm in judge_tasks}
            done = 0
            for fut in as_completed(futs):
                done += 1
                if done % 20 == 0 or done == len(judge_tasks):
                    with PRINT_LOCK:
                        print(f"  [{done}/{len(judge_tasks)}]", flush=True)
        print()

    # ── Combined results table ──
    print("=" * 65)
    print("RESULTS: Signal vs. Noise Ablation (structural, n=28)")
    print("=" * 65)
    print(f"{'Arm':>20} {'Context':>10} {'Detected':>10} {'Rate':>8}")
    print("-" * 55)

    # Reuse Exp2 results for baseline, kg, kg_idealised
    for arm_label, exp2_arm in [("baseline", "baseline"),
                                 ("noise_matched", None),
                                 ("kg_deployed", "kg"),
                                 ("relevant_only", None),
                                 ("kg_idealised", "kg_idealised")]:
        if exp2_arm:
            detected = sum(1 for inj in structural
                          if exp2_majority(inj["id"], exp2_arm))
            ctx = "—" if exp2_arm == "baseline" else "mixed"
        else:
            detected = sum(1 for inj in structural
                          if majority_detected(inj["id"], arm_label))
            ctx = "noise" if arm_label == "noise_matched" else "signal"

        rate = detected / len(structural)
        print(f"{arm_label:>20} {ctx:>10} {detected:>6}/28   {rate:.1%}")

    # McNemar-style pairwise: noise vs baseline, relevant vs deployed
    print()
    print("Pairwise contrasts:")
    for a_label, a_fn, b_label, b_fn in [
        ("noise_matched", lambda i: majority_detected(i["id"], "noise_matched"),
         "baseline", lambda i: exp2_majority(i["id"], "baseline")),
        ("relevant_only", lambda i: majority_detected(i["id"], "relevant_only"),
         "kg_deployed", lambda i: exp2_majority(i["id"], "kg")),
        ("noise_matched", lambda i: majority_detected(i["id"], "noise_matched"),
         "kg_deployed", lambda i: exp2_majority(i["id"], "kg")),
    ]:
        a_yes_b_no = sum(1 for inj in structural if a_fn(inj) and not b_fn(inj))
        a_no_b_yes = sum(1 for inj in structural if not a_fn(inj) and b_fn(inj))
        both_yes = sum(1 for inj in structural if a_fn(inj) and b_fn(inj))
        both_no = sum(1 for inj in structural if not a_fn(inj) and not b_fn(inj))
        print(f"  {a_label} vs {b_label}:")
        print(f"    both_yes={both_yes} both_no={both_no} "
              f"a_only={a_yes_b_no} b_only={a_no_b_yes}")


if __name__ == "__main__":
    main()
