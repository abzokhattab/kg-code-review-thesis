#!/usr/bin/env python3
"""run_concise_prompt_experiment.py — concise-prompt sensitivity run.

Supervisor experiment (2026-06-19): append a "be concise" instruction to the
review-generation system prompt, regenerate the 40 x 4 = 160 reviews, then
re-judge and re-run the stats to see whether forcing terse reviews changes
(hopefully sharpens) the KG-vs-baseline significance.

This script is a thin fork of `dataset_v2/scripts/regenerate_reviews_v2.py`.
It deliberately does NOT edit the production prompts in `prnote/note.py`; it
imports them and appends `CONCISE_SUFFIX` at generation time, so the headline
pipeline is untouched.

Reads:
  data/luca_prs_v2/pr{N}_evidence.json
Writes (isolated — never the headline `outputs/luca_prs_v2/`):
  outputs/luca_prs_v2_concise/pr{N}_{baseline,kg,rag,hybrid}.md

Generation model/params are inherited from the headline run: gpt-4o, T=0.0,
no seed (prnote.llm default). Idempotent: skips a (PR, mode) whose file exists
unless --force.

Usage:
  source load_env.sh
  python3 scripts/run_concise_prompt_experiment.py            # full 160
  python3 scripts/run_concise_prompt_experiment.py --pr 1 --pr 2 --force  # smoke
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
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

# The ONLY treatment of this experiment: a conciseness instruction appended to
# every mode's system prompt. Same output schema (Problem/Evidence/Impact/
# Recommendation/Traceability) so the judge rubric still applies unchanged.
CONCISE_SUFFIX = """

Conciseness requirement (important):
- Be concise and high-signal. Use the SAME section structure as above, but keep
  every point short — one or two sentences per bullet, no filler or restating.
- Do not pad. If a section has nothing substantive, keep it to a single line
  rather than inventing content.
- Prefer the most important 2-3 points per section over an exhaustive list.
- Avoid repeating the same concern across Problem / Impact / Recommendation."""

EVIDENCE_DIR = REPO_ROOT / "data" / "luca_prs_v2"
OUTPUT_DIR = Path(
    os.environ.get("REGEN_OUTPUT_DIR", REPO_ROOT / "outputs" / "luca_prs_v2_concise")
)
if not OUTPUT_DIR.is_absolute():
    OUTPUT_DIR = REPO_ROOT / OUTPUT_DIR
DIFF_MAX_CHARS = 50_000

# Locked v2 PR list (mirrors regenerate_reviews_v2.py).
ALL_PRS = [1, 2, 3, 6, 8, 9, 10, 12, 13, 14, 15, 18, 19, 20, 21, 22, 23, 24,
           27, 28, 29, 30, 31, 32, 33,
           34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]
ALL_MODES = ["baseline", "rag", "kg", "hybrid"]

PROMPTS = {
    "baseline": SYSTEM_PROMPT_BASELINE + CONCISE_SUFFIX,
    "rag": SYSTEM_PROMPT_RAG + CONCISE_SUFFIX,
    "kg": SYSTEM_PROMPT_KG + CONCISE_SUFFIX,
    "hybrid": SYSTEM_PROMPT_HYBRID + CONCISE_SUFFIX,
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
                    help="Sampling temperature. Matches headline run (0.0).")
    args = ap.parse_args()

    pr_ids = args.pr or ALL_PRS
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    for m in modes:
        if m not in ALL_MODES:
            print(f"unknown mode: {m!r}; valid: {ALL_MODES}", file=sys.stderr)
            return 2

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("CONCISE-PROMPT experiment — review regeneration")
    print(f"  {len(pr_ids)} PR(s) x {len(modes)} mode(s) = "
          f"{len(pr_ids) * len(modes)} review(s)")
    print(f"  evidence dir: {EVIDENCE_DIR.relative_to(REPO_ROOT)}")
    print(f"  output dir:   {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    print(f"  temperature:  {args.temperature}")
    print(f"  force:        {args.force}")
    print("=" * 60)

    n_generated = n_skipped = n_errors = 0
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
        print(f"total time: {total_t:5.1f}s  avg/review: {total_t/n_generated:5.1f}s")
    if pair_metas:
        all_reviews = sorted(m["review_chars"] for _, _, m, _ in pair_metas)
        print(f"review size  min={all_reviews[0]} "
              f"med={all_reviews[len(all_reviews)//2]} max={all_reviews[-1]}")
    return 1 if n_errors else 0


if __name__ == "__main__":
    sys.exit(main())
