#!/usr/bin/env python3
"""
regenerate_reviews_v2.py — Regenerate the 18 × 4 = 72 v2 reviews
against the cleaned evidence packs in `data/luca_prs_v2/`.

Reads:
  data/luca_prs_v2/pr{N}_evidence.json — v2 evidence packs
                                         (dataset_v2/docs/SELECTION_v2.md)
Writes:
  outputs/luca_prs_v2/pr{N}_{baseline,kg,rag,hybrid}.md

Differences from `scripts/regenerate_reviews.py`:

  * Uses the v2 evidence directory.
  * Passes max_chars=50000 to get_diff_from_evidence (v1 hardcoded
    15000, which would re-truncate the now-recovered diffs).
  * Idempotent: skips a (PR, mode) pair whose review file already
    exists. Use `--force` to overwrite.
  * `--pr N`: regenerate just one PR (for smoke testing).
  * `--modes baseline,kg`: regenerate just a subset of modes.
  * Per-pair timing + a final cost-summary banner.

Cost (per the README): the full v1 generation cost ~$5-8 for 100
reviews on gpt-4o @ temperature 0. v2 has 72 reviews on slightly
larger prompts; expected total ~$5-10.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# Load .env so OPENAI_API_KEY etc. are visible to prnote.llm
ENV_PATH = REPO_ROOT / ".env"
if ENV_PATH.exists():
    for line in ENV_PATH.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from prnote.llm import generate_completion  # noqa: E402
from prnote.note import (  # noqa: E402
    SYSTEM_PROMPT_BASELINE,
    SYSTEM_PROMPT_KG,
    SYSTEM_PROMPT_RAG,
    SYSTEM_PROMPT_HYBRID,
    format_kg_context,
    format_rag_context,
    format_hybrid_context,
    get_diff_from_evidence,
)

# Default paths are v2 grep-based (data/luca_prs_v2, outputs/luca_prs_v2),
# matching the canonical 40-PR headline. For the scoped-AST sensitivity run
# (or any other variant that must NOT overwrite the headline reviews),
# override via environment variables:
#   REGEN_EVIDENCE_DIR=data/luca_prs_v2_ast_scoped
#   REGEN_OUTPUT_DIR=outputs/luca_prs_v2_scoped_ast
# (added 2026-05-13; see dataset_v2/docs/PRE_REGISTRATION_scoped_ast.md).
EVIDENCE_DIR = Path(os.environ.get("REGEN_EVIDENCE_DIR", REPO_ROOT / "data" / "luca_prs_v2"))
if not EVIDENCE_DIR.is_absolute():
    EVIDENCE_DIR = REPO_ROOT / EVIDENCE_DIR
OUTPUT_DIR = Path(os.environ.get("REGEN_OUTPUT_DIR", REPO_ROOT / "outputs" / "luca_prs_v2"))
if not OUTPUT_DIR.is_absolute():
    OUTPUT_DIR = REPO_ROOT / OUTPUT_DIR
DIFF_MAX_CHARS = 50_000

# Locked v2 PR list (from dataset_v2/docs/SELECTION_v2.md)
ALL_PRS = [1, 2, 3, 6, 8, 9, 10, 12, 13, 14, 15, 18, 19, 20, 21, 22, 23, 24,
           27, 28, 29, 30, 31, 32, 33,                                # 25-PR expansion (2026-05-05)
           34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]  # 40-PR expansion (2026-05-12)
ALL_MODES = ["baseline", "rag", "kg", "hybrid"]

PROMPTS = {
    "baseline": SYSTEM_PROMPT_BASELINE,
    "rag": SYSTEM_PROMPT_RAG,
    "kg": SYSTEM_PROMPT_KG,
    "hybrid": SYSTEM_PROMPT_HYBRID,
}
CONTEXT_BUILDERS = {
    "baseline": lambda _ev: "",
    "rag": format_rag_context,
    "kg": format_kg_context,
    "hybrid": format_hybrid_context,
}


def generate_one(evidence_path: Path, mode: str, temperature: float) -> tuple[str, dict]:
    with open(evidence_path) as f:
        ev = json.load(f)

    diff = get_diff_from_evidence(ev, max_chars=DIFF_MAX_CHARS)
    pr = ev.get("pr", {})
    title = pr.get("title", "Unknown PR")
    body = (pr.get("body") or "").strip()

    system = PROMPTS[mode]
    context = CONTEXT_BUILDERS[mode](ev)

    # v2 prompt template: title + body (real, recovered) + diff + context.
    # v1 omitted body for half the dataset because it was empty.
    body_block = f"\n## PR Description\n{body}\n" if body else ""
    user_prompt = (
        f"## Pull Request: {title}\n"
        f"{body_block}"
        f"## Diff\n```\n{diff}\n```\n"
        f"{context}\n\n"
        f"Please generate an evidence-anchored review note following "
        f"the specified format."
    )

    review = generate_completion(
        prompt=user_prompt,
        system=system,
        model=None,
        temperature=temperature,
    )
    meta = {
        "diff_chars": len(diff),
        "body_chars": len(body),
        "context_chars": len(context),
        "prompt_chars": len(user_prompt),
        "review_chars": len(review),
    }
    return review, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", type=int, action="append", default=None,
                    help="Run only this PR (repeatable). Default: all v2 PRs.")
    ap.add_argument("--modes", default=",".join(ALL_MODES),
                    help="Comma-separated modes. Default: baseline,rag,kg,hybrid.")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite existing review files.")
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="Sampling temperature. v2 default 0.0 matches v1 baseline.")
    args = ap.parse_args()

    pr_ids = args.pr or ALL_PRS
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    for m in modes:
        if m not in ALL_MODES:
            print(f"unknown mode: {m!r}; valid: {ALL_MODES}", file=sys.stderr)
            return 2

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"v2 regeneration — {len(pr_ids)} PR(s) × {len(modes)} mode(s) = "
          f"{len(pr_ids) * len(modes)} review(s)")
    print(f"  evidence dir: {EVIDENCE_DIR.relative_to(REPO_ROOT)}")
    print(f"  output dir:   {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    print(f"  diff cap:     {DIFF_MAX_CHARS} chars")
    print(f"  temperature:  {args.temperature}")
    print(f"  force:        {args.force}")
    print("=" * 60)

    n_generated = 0
    n_skipped = 0
    n_errors = 0
    total_t = 0.0
    pair_metas: list[tuple[int, str, dict, float]] = []

    for pr_id in pr_ids:
        evidence_path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
        if not evidence_path.exists():
            print(f"\nPR{pr_id}: SKIP (no evidence pack)")
            continue

        print(f"\n--- PR{pr_id} ---")
        for mode in modes:
            out_path = OUTPUT_DIR / f"pr{pr_id}_{mode}.md"
            if out_path.exists() and not args.force:
                print(f"  {mode:<8} SKIP (exists, use --force to overwrite)")
                n_skipped += 1
                continue

            t0 = time.time()
            retries = 0
            max_retries = 6
            while True:
                try:
                    review, meta = generate_one(evidence_path, mode, args.temperature)
                    out_path.write_text(review)
                    dt = time.time() - t0
                    total_t += dt
                    pair_metas.append((pr_id, mode, meta, dt))
                    print(f"  {mode:<8} OK  {dt:5.1f}s  "
                          f"prompt={meta['prompt_chars']:>5}  "
                          f"review={meta['review_chars']:>5}", flush=True)
                    n_generated += 1
                    break
                except Exception as e:
                    msg = str(e)
                    # Retry on TPM rate-limit errors (HTTP 429).
                    if "429" in msg and "rate_limit" in msg.lower() and retries < max_retries:
                        sleep_s = 10 + 5 * retries
                        print(f"  {mode:<8} 429  sleep {sleep_s}s and retry "
                              f"({retries+1}/{max_retries})", flush=True)
                        time.sleep(sleep_s)
                        retries += 1
                        t0 = time.time()
                        continue
                    dt = time.time() - t0
                    print(f"  {mode:<8} ERR {dt:5.1f}s  {e}", flush=True)
                    n_errors += 1
                    break

    print()
    print("=" * 60)
    print(f"generated: {n_generated}, skipped: {n_skipped}, errors: {n_errors}")
    if n_generated:
        print(f"total time: {total_t:5.1f}s  "
              f"avg/review: {total_t/n_generated:5.1f}s")
    if pair_metas:
        all_prompts = sorted(m["prompt_chars"] for _, _, m, _ in pair_metas)
        all_reviews = sorted(m["review_chars"] for _, _, m, _ in pair_metas)
        print(f"prompt size  min={all_prompts[0]} med={all_prompts[len(all_prompts)//2]} "
              f"max={all_prompts[-1]}")
        print(f"review size  min={all_reviews[0]} med={all_reviews[len(all_reviews)//2]} "
              f"max={all_reviews[-1]}")
    return 1 if n_errors else 0


if __name__ == "__main__":
    sys.exit(main())
