#!/usr/bin/env python3
"""Context-size ablation on Experiment 2 structural injections.

Vary the TOTAL number of context items (call_graph_edges + dependent_files)
given to the KG arm:
  cap_0   = no context (baseline)
  cap_3   = 3 items total
  cap_5   = 5 items
  cap_10  = 10 items
  cap_20  = 20 items
  cap_all = no cap (the deployed KG arm, which itself caps edges at 40)

For each level, generate a review with gpt-4o and judge with the 3-model
panel, using the same oracle as Experiment 2.  Idempotent: skips existing
outputs.
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

from common import OUT as EXP2_OUT, SCOPES, load_manifest, scope_dir, load_json  # noqa: E402
from expand_dataset import find_dependents  # noqa: E402
from prnote import note  # noqa: E402
from prnote.llm import generate_completion  # noqa: E402

HERE = Path(__file__).resolve().parent
REVIEWS_DIR = HERE / "reviews"
JUDGMENTS_DIR = HERE / "judgments"

GEN_MODEL = "openai:gpt-4o"
JUDGES = ["openai:gpt-4o-mini", "openai:gpt-4o", "gemini:gemini-2.5-flash"]
CAP_LEVELS = [0, 3, 5, 10, 20, 999]
PRINT_LOCK = threading.Lock()


def joern_edges(repo: str) -> dict:
    return load_json(EXP2_OUT / "joern" / f"edges_{repo}.json", default={}) or {}


def build_capped_context(inj: dict, edges_all: dict, cap: int) -> dict | None:
    if cap == 0:
        return None

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

    if cap < 999:
        # Prioritize call edges (more precise), then deps
        if len(cross) >= cap:
            cross = cross[:cap]
            dep_list = []
        else:
            remaining = cap - len(cross)
            dep_list = dep_list[:remaining]
    else:
        cross = cross[:40]  # match deployed arm's cap

    return {
        "changed_files": [{"path": inj["edit_file"]}],
        "dependent_files": dep_list,
        "call_graph_edges": cross,
        "functions_changed": [inj["symbol"] or Path(inj["edit_file"]).stem],
    }


# ── Generation ──────────────────────────────────────────────────────────
def arm_name(cap: int) -> str:
    return f"cap_{cap}" if cap < 999 else "cap_all"


def generate_review(inj: dict, cap: int, edges_all: dict) -> str:
    an = arm_name(cap)
    out_md = REVIEWS_DIR / inj["id"] / f"{an}.md"
    if out_md.exists() and out_md.stat().st_size > 200:
        return "cached"
    out_md.parent.mkdir(parents=True, exist_ok=True)

    kg_ctx = build_capped_context(inj, edges_all, cap)
    mode = "baseline" if cap == 0 else "kg"

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


# ── Judging (same oracle as Experiment 2) ───────────────────────────────
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


def judge_one(inj: dict, cap: int, judge_model: str) -> dict | None:
    an = arm_name(cap)
    jm_safe = judge_model.replace(":", "_").replace("/", "_")
    out_j = JUDGMENTS_DIR / inj["id"] / f"{an}__{jm_safe}.json"
    if out_j.exists():
        try:
            return json.loads(out_j.read_text())
        except Exception:
            pass
    out_j.parent.mkdir(parents=True, exist_ok=True)

    review_md = REVIEWS_DIR / inj["id"] / f"{an}.md"
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


def majority_detected(inj: dict, cap: int) -> bool:
    an = arm_name(cap)
    votes = 0
    for jm in JUDGES:
        jm_safe = jm.replace(":", "_").replace("/", "_")
        jf = JUDGMENTS_DIR / inj["id"] / f"{an}__{jm_safe}.json"
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

    print(f"=== Context-size ablation ===")
    print(f"Injections: {len(structural)} structural")
    print(f"Cap levels: {CAP_LEVELS}")
    print(f"Generator: {GEN_MODEL}")
    print(f"Judges: {JUDGES}")
    print()

    # Stage 1: generate reviews
    for cap in CAP_LEVELS:
        an = arm_name(cap)
        gen_tasks = []
        for inj in structural:
            out_md = REVIEWS_DIR / inj["id"] / f"{an}.md"
            if out_md.exists() and out_md.stat().st_size > 200:
                continue
            gen_tasks.append(inj)
        if not gen_tasks:
            print(f"[gen] {an}: all {len(structural)} cached")
            continue
        print(f"[gen] {an}: {len(gen_tasks)} to generate...", flush=True)
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = {ex.submit(generate_review, inj, cap, edges[inj["repo"]]): inj["id"]
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
    for cap in CAP_LEVELS:
        an = arm_name(cap)
        judge_tasks = []
        for inj in structural:
            for jm in JUDGES:
                jm_safe = jm.replace(":", "_").replace("/", "_")
                out_j = JUDGMENTS_DIR / inj["id"] / f"{an}__{jm_safe}.json"
                if out_j.exists():
                    try:
                        if json.loads(out_j.read_text()).get("detected") is not None:
                            continue
                    except Exception:
                        pass
                judge_tasks.append((inj, jm))
        if not judge_tasks:
            print(f"[judge] {an}: all cached")
            continue
        print(f"[judge] {an}: {len(judge_tasks)} calls...", flush=True)
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(judge_one, inj, cap, jm): (inj["id"], jm)
                    for inj, jm in judge_tasks}
            done = 0
            for fut in as_completed(futs):
                done += 1
                if done % 20 == 0 or done == len(judge_tasks):
                    with PRINT_LOCK:
                        print(f"  [{done}/{len(judge_tasks)}]", flush=True)
        print()

    # Summary
    print("=" * 50)
    print("RESULTS: Context-size ablation (structural, n=28)")
    print("=" * 50)
    print(f"{'Cap':>8} {'Items':>6} {'Detected':>10} {'Rate':>8}")
    print("-" * 40)
    for cap in CAP_LEVELS:
        an = arm_name(cap)
        detected = sum(1 for inj in structural if majority_detected(inj, cap))
        rate = detected / len(structural) if structural else 0
        label = "∞" if cap == 999 else str(cap)
        print(f"{an:>8} {label:>6} {detected:>6}/28   {rate:.1%}")


if __name__ == "__main__":
    main()
