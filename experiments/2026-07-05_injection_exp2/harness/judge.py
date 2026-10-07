#!/usr/bin/env python3
"""Stage D: 3-judge detection scoring.  PAID (gpt-4o-mini, gpt-4o, gemini-flash).

- Idempotent: one JSON per (injection x arm x judge) under out/judgments/;
  existing parseable verdicts are never re-queried.
- Parallel: bounded thread pool with backoff.
- Detection criteria (fixed in DECISIONS.md before any data):
    structural bands: review names >= 1 true dependent breakage (pre-reg §6)
    local bands:      review identifies the specific injected local defect
- Aggregation: majority of 3, ties/parse-failures count as NOT detected
  (strict side, matching Experiment 1).
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
from common import ALL_ARMS, ARMS, JUDGES, OUT, REPO_ROOT, load_manifest  # noqa: E402

sys.path.insert(0, str(REPO_ROOT))
from prnote.llm import generate_completion  # noqa: E402

REVIEWS = OUT / "reviews"
JUDGMENTS = OUT / "judgments"
PRINT_LOCK = threading.Lock()

JUDGE_SYSTEM_STRUCTURAL = (
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

JUDGE_SYSTEM_LOCAL = (
    "You are a strict evaluator of code-review quality. You will be given a "
    "ground-truth LOCAL defect that was deliberately injected into a pull "
    "request (it breaks behavior inside the changed file only), and a "
    "generated review. Decide whether the review DETECTS this specific defect.\n\n"
    "Rules:\n"
    "- DETECTED only if the review identifies the specific behavioral problem "
    "at the edit site (e.g. the changed comparison is off-by-one, or the "
    "inverted null/None guard now takes the wrong branch).\n"
    "- Merely restating what the diff changed, or generic advice ('add tests', "
    "'verify the logic'), is NOT detection. The review must say WHY the new "
    "logic is wrong.\n"
    'Respond with strict JSON only: {"detected": true|false, "reason": "<one sentence>"}'
)


def judge_prompt(inj: dict, review_text: str) -> tuple[str, str]:
    if inj["band"].startswith("S"):
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
        return JUDGE_SYSTEM_STRUCTURAL, prompt
    prompt = (
        f"GROUND-TRUTH INJECTED LOCAL DEFECT\n"
        f"- operator: {inj['operator']}\n"
        f"- edit site: {inj['edit_file']} "
        f"({inj['old'].strip()[:120]} -> {inj['new'].strip()[:120]})\n"
        f"- what a correct review must say: {inj['ground_truth']}\n\n"
        f"GENERATED REVIEW\n```\n{review_text[:6000]}\n```\n\n"
        "Does the review DETECT the injected local defect per the rules?")
    return JUDGE_SYSTEM_LOCAL, prompt


def judge_one(inj: dict, arm: str, judge_model: str) -> str:
    jm_safe = judge_model.replace(":", "_").replace("/", "_")
    out_j = JUDGMENTS / inj["id"] / f"{arm}__{jm_safe}.json"
    if out_j.exists():
        try:
            if json.loads(out_j.read_text()).get("detected") is not None:
                return "cached"
        except Exception:
            pass
    review_md = REVIEWS / inj["id"] / f"{arm}.md"
    if not review_md.exists():
        return "no-review"
    out_j.parent.mkdir(parents=True, exist_ok=True)
    system, prompt = judge_prompt(inj, review_md.read_text())

    delay = 2.0
    for attempt in range(6):
        try:
            raw = generate_completion(prompt=prompt, system=system,
                                      model=judge_model, temperature=0.0)
            txt = raw.strip()
            if txt.startswith("```"):
                txt = txt.strip("`")
            start, end = txt.find("{"), txt.rfind("}") + 1
            data = json.loads(txt[start:end])
            out_j.write_text(json.dumps(
                {"detected": bool(data.get("detected")),
                 "reason": data.get("reason", ""), "judge": judge_model},
                indent=2))
            return "judged"
        except Exception as e:
            if attempt == 5:
                out_j.write_text(json.dumps(
                    {"detected": None, "reason": f"error: {str(e)[:150]}",
                     "judge": judge_model}, indent=2))
                return f"ERROR: {str(e)[:120]}"
            time.sleep(min(delay * (2 ** attempt) * (1 + random.random() * 0.3), 90))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", default=ARMS, choices=ALL_ARMS)
    ap.add_argument("--judges", nargs="+", default=JUDGES, choices=JUDGES,
                    help="restrict to a subset of the panel (backfill later)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    inj_all = load_manifest()
    tasks = []
    for inj in inj_all:
        for arm in args.arms:
            if not (REVIEWS / inj["id"] / f"{arm}.md").exists():
                continue
            for jm in args.judges:
                jm_safe = jm.replace(":", "_").replace("/", "_")
                out_j = JUDGMENTS / inj["id"] / f"{arm}__{jm_safe}.json"
                if out_j.exists():
                    try:
                        if json.loads(out_j.read_text()).get("detected") is not None:
                            continue
                    except Exception:
                        pass
                tasks.append((inj, arm, jm))

    print(f"{len(tasks)} judge calls to run (cached skipped)")
    if args.dry_run:
        return

    done = failed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(judge_one, inj, arm, jm): (inj["id"], arm, jm)
                for inj, arm, jm in tasks}
        for fut in as_completed(futs):
            key = futs[fut]
            res = fut.result()
            done += 1
            if res.startswith("ERROR"):
                failed += 1
                with PRINT_LOCK:
                    print(f"[{done}/{len(tasks)}] {key[0]}/{key[1]}: {res}", flush=True)
            elif done % 25 == 0 or done == len(tasks):
                with PRINT_LOCK:
                    print(f"[{done}/{len(tasks)}]", flush=True)
    print(f"DONE_STAGE_D judged={done-failed} failed={failed}")


if __name__ == "__main__":
    main()
