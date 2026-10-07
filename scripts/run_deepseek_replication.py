#!/usr/bin/env python3
"""
run_deepseek_replication.py — Generate + evaluate 40 PR reviews with DeepSeek-V3.

Step 1: Generate 160 reviews (40 PRs × 4 modes) using deepseek:deepseek-chat.
Step 2: Evaluate all 160 reviews with the same 3-judge panel as the headline run.
Step 3: Run bootstrap stats and write results/BOOTSTRAP_STATS_v2_deepseek.md.

Idempotent: skips existing review files and cached judge evaluations.

Usage:
    source load_env.sh
    python3 scripts/run_deepseek_replication.py
    python3 scripts/run_deepseek_replication.py --step generate
    python3 scripts/run_deepseek_replication.py --step evaluate
    python3 scripts/run_deepseek_replication.py --step stats
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

# Load .env
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

# ── Config ────────────────────────────────────────────────────────────────────

GENERATOR_MODEL = "deepseek:deepseek-chat"
TEMPERATURE     = 0.0
EVIDENCE_DIR    = REPO_ROOT / "data" / "luca_prs_v2"
OUTPUT_DIR      = REPO_ROOT / "outputs" / "luca_prs_v2_deepseek"
RESULTS_DIR     = REPO_ROOT / "results"
DIFF_MAX_CHARS  = 50_000

ALL_PRS = [1, 2, 3, 6, 8, 9, 10, 12, 13, 14, 15, 18, 19, 20, 21, 22, 23, 24,
           27, 28, 29, 30, 31, 32, 33,
           34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]

ALL_MODES = ["baseline", "rag", "kg", "hybrid"]

PROMPTS = {
    "baseline": SYSTEM_PROMPT_BASELINE,
    "rag":      SYSTEM_PROMPT_RAG,
    "kg":       SYSTEM_PROMPT_KG,
    "hybrid":   SYSTEM_PROMPT_HYBRID,
}
CONTEXT_BUILDERS = {
    "baseline": lambda _ev: "",
    "rag":      format_rag_context,
    "kg":       format_kg_context,
    "hybrid":   format_hybrid_context,
}

JUDGE_PANEL = [
    "openai:gpt-4o-mini",
    "openai:gpt-4o",
    "gemini:gemini-2.5-flash",
]

# ── Step 1: Generate reviews ──────────────────────────────────────────────────

def generate_reviews():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total   = len(ALL_PRS) * len(ALL_MODES)
    done    = 0
    skipped = 0
    errors  = 0
    t0      = time.time()

    print(f"\n{'='*60}")
    print(f"STEP 1: Generating {total} reviews with {GENERATOR_MODEL}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'='*60}\n")

    for pr_id in ALL_PRS:
        evidence_path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
        if not evidence_path.exists():
            print(f"  [SKIP] pr{pr_id} — evidence file not found")
            skipped += len(ALL_MODES)
            continue

        with open(evidence_path) as f:
            ev = json.load(f)

        diff     = get_diff_from_evidence(ev, max_chars=DIFF_MAX_CHARS)
        pr_meta  = ev.get("pr", {})
        title    = pr_meta.get("title", f"PR #{pr_id}")
        body     = (pr_meta.get("body") or "").strip()
        body_block = f"\n## PR Description\n{body}\n" if body else ""

        for mode in ALL_MODES:
            out_path = OUTPUT_DIR / f"pr{pr_id}_{mode}.md"
            if out_path.exists():
                skipped += 1
                continue

            context    = CONTEXT_BUILDERS[mode](ev)
            user_prompt = (
                f"## Pull Request: {title}\n"
                f"{body_block}"
                f"## Diff\n```\n{diff}\n```\n"
                f"{context}\n\n"
                f"Please generate an evidence-anchored review note following "
                f"the specified format."
            )

            try:
                review = generate_completion(
                    prompt=user_prompt,
                    system=PROMPTS[mode],
                    model=GENERATOR_MODEL,
                    temperature=TEMPERATURE,
                )
                out_path.write_text(review)
                done += 1
                elapsed = time.time() - t0
                rate    = done / elapsed
                eta     = (total - done - skipped) / rate if rate > 0 else 0
                print(f"  [OK] pr{pr_id} {mode:8s} — {len(review):5d} chars "
                      f"({done}/{total-skipped} done, ETA {eta/60:.1f}min)")
            except Exception as e:
                errors += 1
                print(f"  [ERR] pr{pr_id} {mode}: {e}")
                time.sleep(5)

    print(f"\nGeneration complete: {done} new, {skipped} skipped, {errors} errors")
    print(f"Total time: {(time.time()-t0)/60:.1f} min\n")


# ── Step 2: Evaluate reviews ──────────────────────────────────────────────────

def evaluate_reviews():
    eval_script = REPO_ROOT / "scripts" / "evaluate_reviews.py"
    if not eval_script.exists():
        print(f"[ERROR] {eval_script} not found")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"STEP 2: Evaluating reviews with judge panel")
    print(f"Panel: {JUDGE_PANEL}")
    print(f"{'='*60}\n")

    import subprocess
    result = subprocess.run(
        [sys.executable, str(eval_script),
         "--outputs-dir", str(OUTPUT_DIR),
         "--output-suffix", "v2_deepseek"],
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print("[ERROR] Evaluation script failed")
        sys.exit(1)


# ── Step 3: Bootstrap stats ───────────────────────────────────────────────────

def run_stats():
    stats_script = REPO_ROOT / "scripts" / "bootstrap_stats.py"
    if not stats_script.exists():
        print(f"[ERROR] {stats_script} not found")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("STEP 3: Computing bootstrap CIs + permutation tests")
    print(f"{'='*60}\n")

    import subprocess
    in_json  = RESULTS_DIR / "checklist_evaluation_llm_multi__v2_deepseek.json"
    out_json = RESULTS_DIR / "BOOTSTRAP_STATS_v2_deepseek.json"
    out_md   = RESULTS_DIR / "BOOTSTRAP_STATS_v2_deepseek.md"

    if not in_json.exists():
        print(f"[ERROR] {in_json} not found — run evaluate step first")
        sys.exit(1)

    result = subprocess.run(
        [sys.executable, str(stats_script),
         "--in", str(in_json),
         "--out-json", str(out_json),
         "--out-md",   str(out_md),
         "--label",    "v2_deepseek (40 PRs, DeepSeek-V3 generator)"],
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print("[ERROR] Stats script failed")
        sys.exit(1)

    print(f"\nResults written to {out_md}")
    print(out_md.read_text())


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", choices=["generate", "evaluate", "stats", "all"],
                    default="all")
    args = ap.parse_args()

    if args.step in ("generate", "all"):
        generate_reviews()
    if args.step in ("evaluate", "all"):
        evaluate_reviews()
    if args.step in ("stats", "all"):
        run_stats()


if __name__ == "__main__":
    main()
