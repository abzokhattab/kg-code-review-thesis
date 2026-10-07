#!/usr/bin/env python3
"""rerun_confirmatory_heldout.py — clean re-run of the pre-registered confirmatory test.

The 2026-05-14 confirmatory run on the 12 held-out PRs failed to replicate the
exploratory KG effect, but it is not interpretable, for four reasons:

  1. Wrong PR context. It judged through `scripts/evaluate_reviews.py`, whose
     `load_pr_context` resolved `pr<N>_evidence.json` against `data/luca_prs_v2`.
     The held-out set numbers its PRs 1..12 and so collides with the canonical
     dataset: every review was scored against a different pull request's title
     and body. Fixed here by setting PR_CONTEXT_DIR.
  2. Different judge panel. It used [gemini-2.5-flash, claude-sonnet-4] and so
     omitted gpt-4o — the judge that `results/JUDGE_LEAVE_ONE_OUT.md` shows is
     carrying most of the effect. Fixed here by using the headline DEFAULT_PANEL.
  3. Different prompt. It used the bespoke templates in that experiment's own
     `generate_reviews.py`, not the v2 prompt. Fixed here by importing
     `generate_one` from the headline generator so the prompt is identical.
  4. Different generator settings. Fixed here by pinning gpt-4o at T=0.0.

This script therefore holds generator, prompt, KG context builder, judge panel
and temperature at their headline values and varies only the dataset, which is
what a confirmatory test is supposed to do.

Both stages are parallel and idempotent:
  * generation skips a (PR, mode) whose review .md already exists;
  * judging skips a (PR, mode) whose per-review cache entry already exists, and
    writes into the exact cache path `run_full_evaluation` reads, so the final
    assembly pass costs no API calls.

Reads:
  experiments/2026-05-14_confirmatory_kg/evidence/pr{1..12}_evidence.json
Writes:
  experiments/2026-05-14_confirmatory_kg/reviews_clean/pr{N}_{baseline,kg}.md
  results/checklist_evaluation_llm_multi__confirmatory_clean.json  (+ .csv/.md)

Usage:
  source load_env.sh
  python3 scripts/rerun_confirmatory_heldout.py                 # full run
  python3 scripts/rerun_confirmatory_heldout.py --dry-run       # cost/plan only
  python3 scripts/rerun_confirmatory_heldout.py --stage generate
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

EXP_DIR = REPO_ROOT / "experiments" / "2026-05-14_confirmatory_kg"
EVIDENCE_DIR = EXP_DIR / "evidence"
REVIEW_DIR = EXP_DIR / "reviews_clean"
SUFFIX = "confirmatory_clean"

PR_IDS = list(range(1, 13))
MODES = ["baseline", "kg"]
TEMPERATURE = 0.0
GENERATOR = "openai:gpt-4o"

_print_lock = threading.Lock()


def log(msg: str) -> None:
    with _print_lock:
        print(msg, flush=True)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def with_retries(fn, label: str, max_retries: int = 6):
    """Retry on 429/5xx/transient transport errors with linear backoff."""
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - provider SDKs raise many types
            msg = str(exc)
            transient = (
                "429" in msg
                or "rate_limit" in msg.lower()
                or "500" in msg
                or "502" in msg
                or "503" in msg
                or "529" in msg
                or "overloaded" in msg.lower()
                or "timeout" in msg.lower()
                or "connection" in msg.lower()
            )
            if transient and attempt < max_retries:
                sleep_s = 10 + 5 * attempt
                log(f"    {label}: transient ({msg[:70]}); sleep {sleep_s}s "
                    f"[{attempt + 1}/{max_retries}]")
                time.sleep(sleep_s)
                continue
            raise


# ---------------------------------------------------------------------------
# Stage 1 — generation (parallel, idempotent)
# ---------------------------------------------------------------------------

def stage_generate(workers: int, force: bool) -> int:
    # regenerate_reviews_v2 resolves its evidence/output dirs from the
    # environment at import time, so these must be set before loading it.
    os.environ["REGEN_EVIDENCE_DIR"] = str(EVIDENCE_DIR)
    os.environ["REGEN_OUTPUT_DIR"] = str(REVIEW_DIR)
    os.environ.setdefault("MODEL_NAME", GENERATOR)

    regen = _load_module(
        REPO_ROOT / "dataset_v2" / "scripts" / "regenerate_reviews_v2.py",
        "regenerate_reviews_v2",
    )
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    jobs = []
    skipped = 0
    for pr_id in PR_IDS:
        pack = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
        if not pack.exists():
            log(f"  pr{pr_id}: no evidence pack, skipping")
            continue
        for mode in MODES:
            out = REVIEW_DIR / f"pr{pr_id}_{mode}.md"
            if out.exists() and out.stat().st_size > 0 and not force:
                skipped += 1
                continue
            jobs.append((pr_id, mode, pack, out))

    log(f"  {len(jobs)} to generate, {skipped} already present")
    if not jobs:
        return 0

    errors = 0

    def run(job):
        pr_id, mode, pack, out = job
        t0 = time.time()
        review, meta = with_retries(
            lambda: regen.generate_one(pack, mode, TEMPERATURE),
            f"pr{pr_id}_{mode}",
        )
        # Write via a temp file so an interrupted run cannot leave a truncated
        # review that the idempotency check would later treat as complete.
        tmp = out.with_suffix(".md.part")
        tmp.write_text(review)
        tmp.replace(out)
        return pr_id, mode, meta, time.time() - t0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(run, j): j for j in jobs}
        for fut in as_completed(futs):
            pr_id, mode, _, _ = futs[fut]
            try:
                pr_id, mode, meta, dt = fut.result()
                log(f"  pr{pr_id:<3} {mode:<9} OK {dt:5.1f}s  "
                    f"prompt={meta['prompt_chars']:>6} review={meta['review_chars']:>5} "
                    f"ctx={meta['context_chars']:>5}")
            except Exception as exc:  # noqa: BLE001
                errors += 1
                log(f"  pr{pr_id:<3} {mode:<9} ERR {exc}")
    return errors


# ---------------------------------------------------------------------------
# Stage 2 — judging (parallel, idempotent, warms the evaluator's own cache)
# ---------------------------------------------------------------------------

def stage_judge(workers: int) -> int:
    # Point the judge at the held-out packs. Without this the PR ids collide
    # with data/luca_prs_v2 and the panel scores each review against the wrong
    # pull request -- the defect that invalidated the 2026-05-14 run.
    os.environ["PR_CONTEXT_DIR"] = str(EVIDENCE_DIR)

    ev = _load_module(REPO_ROOT / "scripts" / "evaluate_reviews.py", "evaluate_reviews")
    judges = list(ev.DEFAULT_PANEL)

    # Mirror run_full_evaluation's cache layout exactly so the assembly pass
    # below is a pure cache read.
    cache_dir = REVIEW_DIR / ".judge_cache" / SUFFIX / "_".join(
        j.replace(":", "-").replace("/", "-") for j in judges
    )
    cache_dir.mkdir(parents=True, exist_ok=True)

    sanity = ev.load_pr_context(1)
    log(f"  judges: {', '.join(judges)}")
    log(f"  PR#1 context resolves to: {sanity['title'][:70]!r}")
    log(f"  cache: {cache_dir.relative_to(REPO_ROOT)}")

    jobs, skipped = [], 0
    for pr_id in PR_IDS:
        for mode in MODES:
            review = REVIEW_DIR / f"pr{pr_id}_{mode}.md"
            if not review.exists():
                continue
            if (cache_dir / f"pr{pr_id}_{mode}.json").exists():
                skipped += 1
                continue
            jobs.append((pr_id, mode, review))

    log(f"  {len(jobs)} to judge, {skipped} already cached")
    if not jobs:
        return 0

    errors = 0

    def run(job):
        pr_id, mode, review = job
        t0 = time.time()
        result = with_retries(
            lambda: ev.evaluate_single_review(review, pr_id, mode, judges),
            f"pr{pr_id}_{mode}",
        )
        tmp = cache_dir / f"pr{pr_id}_{mode}.json.part"
        tmp.write_text(json.dumps(asdict(result), indent=2))
        tmp.replace(cache_dir / f"pr{pr_id}_{mode}.json")
        return result, time.time() - t0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(run, j): j for j in jobs}
        for fut in as_completed(futs):
            pr_id, mode, _ = futs[fut]
            try:
                result, dt = fut.result()
                log(f"  pr{pr_id:<3} {mode:<9} OK {dt:5.1f}s  "
                    f"total={result.total_score}/{result.max_score} "
                    f"kg_rel={result.kg_relevant_score}/{result.kg_relevant_max}")
            except Exception as exc:  # noqa: BLE001
                errors += 1
                log(f"  pr{pr_id:<3} {mode:<9} ERR {exc}")

    if errors:
        return errors

    # Let the project's own code assemble the panel artefacts; every cell is
    # cached, so this makes no API calls and cannot drift from the headline
    # file schema that the bootstrap analyser expects.
    log("\n  assembling panel artefacts from cache ...")
    ev.run_full_evaluation(judges, REVIEW_DIR, output_suffix=SUFFIX)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6,
                    help="Concurrent API calls per stage (default 6).")
    ap.add_argument("--stage", choices=["generate", "judge", "all"], default="all")
    ap.add_argument("--force", action="store_true",
                    help="Regenerate reviews even if they already exist.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the plan and cost estimate, then exit.")
    args = ap.parse_args()

    n_reviews = len(PR_IDS) * len(MODES)
    print("=" * 68)
    print("Clean confirmatory re-run — 12 held-out PRs, headline configuration")
    print("=" * 68)
    print(f"  generator : {GENERATOR} @ T={TEMPERATURE} (v2 prompt, v2 KG builder)")
    print(f"  judges    : headline 3-judge panel (DEFAULT_PANEL)")
    print(f"  arms      : {', '.join(MODES)}")
    print(f"  reviews   : {n_reviews}   judge calls: {n_reviews * 3}")
    print(f"  evidence  : {EVIDENCE_DIR.relative_to(REPO_ROOT)}")
    print(f"  reviews   -> {REVIEW_DIR.relative_to(REPO_ROOT)}")
    print(f"  results   -> results/checklist_evaluation_llm_multi__{SUFFIX}.json")
    print(f"  workers   : {args.workers}   idempotent: yes")
    print("  est. cost : ~$3   est. wall-clock: ~8-12 min")
    print("=" * 68)
    if args.dry_run:
        return 0

    if not (os.environ.get("OPENAI_API_KEY") or (REPO_ROOT / ".env").exists()):
        print("error: no OPENAI_API_KEY and no .env; run `source load_env.sh`",
              file=sys.stderr)
        return 2

    t0 = time.time()
    if args.stage in ("generate", "all"):
        print("\n[1/2] generating reviews")
        if stage_generate(args.workers, args.force):
            print("\nerrors during generation; re-run to retry (idempotent)",
                  file=sys.stderr)
            return 1

    if args.stage in ("judge", "all"):
        print("\n[2/2] judging with the headline panel")
        if stage_judge(args.workers):
            print("\nerrors during judging; re-run to retry (idempotent)",
                  file=sys.stderr)
            return 1

    print(f"\ndone in {time.time() - t0:.0f}s")
    print("\nnext:")
    print(f"  python3 scripts/bootstrap_stats.py "
          f"--input results/checklist_evaluation_llm_multi__{SUFFIX}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
