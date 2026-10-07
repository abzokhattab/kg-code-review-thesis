#!/usr/bin/env python3
"""
Joern-REPLACE-grep experiment: use Joern-resolved callers AS dependent_files,
replacing the grep-based list entirely.

The parity run (2026-06-11) kept grep dependent_files and added Joern callers
on top — diluting rather than replacing. This run tests what happens when
Joern callers ARE the dependent_files list.

Generator: GPT-4o, T=0.0 (matches headline).
Judge panel: GPT-4o-mini + GPT-4o + Gemini 2.5 Flash (matches headline).
Scope: 35 PRs (5 Go PRs excluded).
Idempotent: skips PRs whose review or score already exists on disk.
"""

from __future__ import annotations

import json
import os
import sys
import time
import concurrent.futures
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

ENV_PATH = REPO / ".env"
if ENV_PATH.exists():
    for line in ENV_PATH.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from prnote.llm import generate_completion, _USAGE_LOG  # noqa: E402
from prnote.note import (  # noqa: E402
    SYSTEM_PROMPT_KG,
    format_kg_context,
    get_diff_from_evidence,
)
from scripts.evaluate_reviews import (  # noqa: E402
    DEFAULT_PANEL,
    evaluate_single_review,
)

EXP_DIR = Path(__file__).resolve().parent
JOERN_EVIDENCE_DIR = REPO / "experiments" / "2026-05-15_joern_kg_main" / "evidence"
MODIFIED_EVIDENCE_DIR = EXP_DIR / "evidence"
REVIEWS_DIR = EXP_DIR / "reviews"
SCORES_DIR = EXP_DIR / "scores"
USAGE_LOG_PATH = EXP_DIR / "usage_log.jsonl"
GENERATOR_MODEL = "openai:gpt-4o"
TEMPERATURE = 0.0

TARGET_PRS = [1, 2, 3, 6, 8, 10, 12, 13, 14, 15, 18, 19, 20, 21, 22, 23, 24,
              28, 29, 30, 31, 32, 33, 34, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]

COST_PER_1M = {
    "openai:gpt-4o":            {"in": 2.50, "out": 10.00},
    "openai:gpt-4o-mini":       {"in": 0.15, "out": 0.60},
    "gemini:gemini-2.5-flash":  {"in": 0.30, "out": 2.50},
}

import threading
_usage_lock = threading.Lock()


def flush_usage(pr_id: int) -> None:
    with _usage_lock:
        if not _USAGE_LOG:
            return
        with USAGE_LOG_PATH.open("a") as f:
            for entry in _USAGE_LOG:
                entry = {**entry, "pr_id": pr_id}
                f.write(json.dumps(entry) + "\n")
        _USAGE_LOG.clear()


def build_modified_evidence(pr_id: int) -> Path | None:
    out_path = MODIFIED_EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    if out_path.exists():
        return out_path

    src = JOERN_EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    if not src.exists():
        print(f"  PR{pr_id}: no Joern evidence, skip")
        return None

    ep = json.loads(src.read_text())

    changed_set = set()
    for f in ep.get("changed_files", []):
        if isinstance(f, dict):
            changed_set.add(f.get("path", ""))
        else:
            changed_set.add(f)

    callers = ep.get("callers", [])
    caller_files = set()
    for c in callers:
        if isinstance(c, dict):
            path = c.get("path", "")
            if path and path not in changed_set:
                caller_files.add(path)

    ep["dependent_files"] = sorted(caller_files)

    out_path.write_text(json.dumps(ep, indent=2))
    return out_path


def generate_review(pr_id: int) -> Path | None:
    review_path = REVIEWS_DIR / f"pr{pr_id}_kg.md"
    if review_path.exists() and review_path.stat().st_size > 100:
        print(f"  PR{pr_id}: review exists, skip")
        return review_path

    evidence_path = MODIFIED_EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    if not evidence_path.exists():
        print(f"  PR{pr_id}: no modified evidence, skip")
        return None

    evidence = json.loads(evidence_path.read_text())
    diff = get_diff_from_evidence(evidence, max_chars=50000)
    pr_title = evidence.get("pr", {}).get("title", f"PR {pr_id}")
    pr_body = (evidence.get("pr", {}).get("body") or "").strip()
    body_block = f"\n## PR Description\n{pr_body}\n" if pr_body else ""
    context = format_kg_context(evidence)

    user_prompt = (
        f"## Pull Request: {pr_title}\n"
        f"{body_block}"
        f"## Diff\n```\n{diff}\n```\n"
        f"{context}\n\n"
        "Please generate an evidence-anchored review note following the specified format."
    )

    print(f"  PR{pr_id}: generating...")
    review = generate_completion(
        prompt=user_prompt,
        system=SYSTEM_PROMPT_KG,
        model=GENERATOR_MODEL,
        temperature=TEMPERATURE,
    )
    review_path.write_text(review)
    flush_usage(pr_id)
    print(f"  PR{pr_id}: review OK ({len(review)} chars)")
    return review_path


def score_review(pr_id: int, review_path: Path) -> Path | None:
    score_path = SCORES_DIR / f"pr{pr_id}_kg.json"
    if score_path.exists() and score_path.stat().st_size > 100:
        print(f"  PR{pr_id}: score exists, skip")
        return score_path

    print(f"  PR{pr_id}: scoring (3 judges x 25 criteria)...")
    ev = evaluate_single_review(review_path, pr_id, "kg", DEFAULT_PANEL)
    score_path.write_text(json.dumps(ev.__dict__, indent=2, default=str))
    flush_usage(pr_id)
    print(f"  PR{pr_id}: score OK (kg-rel {ev.kg_relevant_score}/{ev.kg_relevant_max})")
    return score_path


def process_pr(pr_id: int) -> dict | None:
    evidence_path = build_modified_evidence(pr_id)
    if not evidence_path:
        return None
    review_path = generate_review(pr_id)
    if not review_path:
        return None
    score_path = score_review(pr_id, review_path)
    if not score_path:
        return None
    return {"pr_id": pr_id, "review": str(review_path), "score": str(score_path)}


def cost_summary() -> None:
    if not USAGE_LOG_PATH.exists():
        print("No usage log found.")
        return
    by_model: dict[str, dict] = {}
    for line in USAGE_LOG_PATH.read_text().splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        m = e["model"]
        by_model.setdefault(m, {"calls": 0, "in": 0, "out": 0})
        by_model[m]["calls"] += 1
        by_model[m]["in"] += e["prompt_tokens"]
        by_model[m]["out"] += e["completion_tokens"]

    print("\n=== Token usage and cost ===")
    print(f"{'Model':<30} {'Calls':>6} {'In tokens':>12} {'Out tokens':>12} {'Cost':>10}")
    total = 0.0
    for m, s in sorted(by_model.items()):
        rates = COST_PER_1M.get(m, {"in": 0, "out": 0})
        cost = (s["in"] / 1_000_000) * rates["in"] + (s["out"] / 1_000_000) * rates["out"]
        total += cost
        print(f"{m:<30} {s['calls']:>6} {s['in']:>12,} {s['out']:>12,} ${cost:>8.2f}")
    print(f"{'TOTAL':<30} {'':>6} {'':>12} {'':>12} ${total:>8.2f}")


def main():
    MODIFIED_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    SCORES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"=== Joern-REPLACE-grep experiment ===")
    print(f"Target: {len(TARGET_PRS)} PRs")
    print(f"Generator: {GENERATOR_MODEL} (T={TEMPERATURE})")
    print(f"Judges: {DEFAULT_PANEL}")
    print(f"Evidence: Joern callers REPLACE grep dependent_files")
    print()

    # Step 1: build all modified evidence packs (fast, no API calls)
    print("--- Building modified evidence packs ---")
    for pr_id in TARGET_PRS:
        build_modified_evidence(pr_id)
    print()

    # Step 2: generate reviews (sequential — API rate limits)
    print("--- Generating reviews ---")
    for pr_id in TARGET_PRS:
        generate_review(pr_id)
    print()

    # Step 3: score reviews (sequential — API rate limits)
    print("--- Scoring reviews ---")
    for pr_id in TARGET_PRS:
        review_path = REVIEWS_DIR / f"pr{pr_id}_kg.md"
        if review_path.exists():
            score_review(pr_id, review_path)
    print()

    cost_summary()


if __name__ == "__main__":
    main()
