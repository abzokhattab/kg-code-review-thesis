#!/usr/bin/env python3
"""judge_parallel.py — fill the evaluate_reviews judge cache in parallel.

`scripts/evaluate_reviews.py` judges reviews sequentially. For a single-judge
run on 160 reviews that is slow (GPT-4o emits a long 25-criterion JSON per
call). Judge calls are IO-bound, so a thread pool gives a big speedup.

This driver reuses `evaluate_single_review` and writes to the SAME per-review
cache that the sequential evaluator reads, so:
  * already-cached reviews are skipped (no rework, no double spend),
  * after this finishes, a normal `python3 -m scripts.evaluate_reviews` run with
    the same --output-suffix assembles the results JSON from 100% cache hits.

Usage:
  python3 -m scripts.judge_parallel \
    --outputs-dir outputs/luca_prs_v2_concise \
    --output-suffix v2_concise_gpt4o \
    --models openai:gpt-4o \
    --workers 8
"""

from __future__ import annotations

import argparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

from scripts.evaluate_reviews import evaluate_single_review


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outputs-dir", required=True)
    ap.add_argument("--output-suffix", default="")
    ap.add_argument("--models", required=True, help="comma-separated judge models")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    judges = [m.strip() for m in args.models.split(",") if m.strip()]
    outputs_dir = Path(args.outputs_dir)
    cache_dir = outputs_dir / ".judge_cache" / (args.output_suffix or "default") / "_".join(
        j.replace(":", "-").replace("/", "-") for j in judges
    )
    cache_dir.mkdir(parents=True, exist_ok=True)

    review_files = sorted(outputs_dir.glob("pr*_*.md"))
    todo: list[tuple[Path, int, str, Path]] = []
    cached = 0
    for f in review_files:
        m = re.match(r"pr(\d+)_(\w+)\.md", f.name)
        if not m:
            continue
        pr_id, mode = int(m.group(1)), m.group(2)
        cache_path = cache_dir / f"pr{pr_id}_{mode}.json"
        if cache_path.exists():
            cached += 1
            continue
        todo.append((f, pr_id, mode, cache_path))

    print(f"Judges: {judges}")
    print(f"Reviews: {len(review_files)}  cached: {cached}  to judge: {len(todo)}")
    print(f"Cache: {cache_dir}")
    print(f"Workers: {args.workers}\n")

    done = 0
    errors = 0

    def work(item):
        f, pr_id, mode, cache_path = item
        ev = evaluate_single_review(f, pr_id, mode, judges)
        cache_path.write_text(__import__("json").dumps(asdict(ev), indent=2))
        return pr_id, mode, ev

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(work, it): it for it in todo}
        for fut in as_completed(futs):
            it = futs[fut]
            try:
                pr_id, mode, ev = fut.result()
                done += 1
                errs = sum(1 for pj in ev.per_judge if pj.get("error"))
                if errs:
                    errors += 1
                print(f"[{done+cached:>3}/{len(review_files)}] PR#{pr_id:<3} {mode:<10} "
                      f"tot={ev.total_score}/{ev.max_score} kg={ev.kg_relevant_score}"
                      f"{'  ERR' if errs else ''}", flush=True)
            except Exception as e:  # noqa: BLE001
                errors += 1
                print(f"  ERR {it[1]} {it[2]}: {e}", flush=True)

    print(f"\nfilled {done} cache files, {errors} with errors, {cached} pre-cached")


if __name__ == "__main__":
    main()
