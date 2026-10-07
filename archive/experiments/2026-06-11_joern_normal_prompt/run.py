#!/usr/bin/env python3
"""
Clean Joern run — Joern KG evidence + normal SYSTEM_PROMPT_KG (no MUSTs).

This fills the missing cell in the headline matrix: Joern KG context under the
same prompt that the headline (tree-sitter) used. Without this, the Joern
d_z=+1.34 is confounded by the strict prompt that mandates coverage of the
9 KG-relevant criteria.

Generator: GPT-4o, T=0.0 (matches headline configuration).
Judge panel: GPT-4o-mini + GPT-4o + Gemini 2.5 Flash (matches headline).
Scope: 35 PRs (5 Go PRs excluded — Joern Go frontend has no call edges).

Idempotent: skips PRs whose review or score already exists on disk.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

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
EVIDENCE_DIR = REPO / "experiments" / "2026-05-15_joern_kg_main" / "evidence"
REVIEWS_DIR = EXP_DIR / "reviews"
SCORES_DIR = EXP_DIR / "scores"
USAGE_LOG_PATH = EXP_DIR / "usage_log.jsonl"
GENERATOR_MODEL = "openai:gpt-4o"
TEMPERATURE = 0.0


# Per-1M-token rates (USD), as of 2026-06.
# Sources: openai.com/api/pricing, ai.google.dev/pricing
COST_PER_1M = {
    "openai:gpt-4o":            {"in": 2.50, "out": 10.00},
    "openai:gpt-4o-mini":       {"in": 0.15, "out": 0.60},
    "gemini:gemini-2.5-flash":  {"in": 0.30, "out": 2.50},
}


def flush_usage(pr_id: int) -> None:
    """Drain _USAGE_LOG to disk, tagged with the PR that produced the calls."""
    if not _USAGE_LOG:
        return
    with USAGE_LOG_PATH.open("a") as f:
        for entry in _USAGE_LOG:
            entry = {**entry, "pr_id": pr_id}
            f.write(json.dumps(entry) + "\n")
    _USAGE_LOG.clear()


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


def generate_review(pr_id: int) -> Path | None:
    review_path = REVIEWS_DIR / f"pr{pr_id}_kg.md"
    if review_path.exists() and review_path.stat().st_size > 100:
        print(f"  PR{pr_id}: review exists, skip")
        return review_path

    evidence_path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    if not evidence_path.exists():
        print(f"  PR{pr_id}: no Joern evidence, skip")
        return None

    evidence = json.loads(evidence_path.read_text())
    diff = get_diff_from_evidence(evidence, max_chars=50000)
    pr_title = evidence.get("pr", {}).get("title", f"PR {pr_id}")
    context = format_kg_context(evidence)

    user_prompt = (
        f"## Pull Request: {pr_title}\n\n"
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
    print(f"  PR{pr_id}: review OK ({len(review)} chars)")
    return review_path


def score_review(pr_id: int, review_path: Path) -> Path | None:
    score_path = SCORES_DIR / f"pr{pr_id}_kg.json"
    if score_path.exists() and score_path.stat().st_size > 100:
        print(f"  PR{pr_id}: score exists, skip")
        return score_path

    print(f"  PR{pr_id}: scoring (3 judges × 25 criteria)...")
    ev = evaluate_single_review(review_path, pr_id, "kg", DEFAULT_PANEL)
    score_path.write_text(json.dumps(ev.__dict__, indent=2, default=str))
    print(f"  PR{pr_id}: score OK (kg-rel {ev.kg_relevant_score}/{ev.kg_relevant_max})")
    return score_path


def aggregate_2openai_only() -> Path:
    """Sensitivity check: re-aggregate using only the 2 OpenAI judges.

    Per-judge verdicts are already on disk in scores/pr{N}_kg.json. We just
    re-run majority vote with Gemini dropped. Tie (1-1) → 0, matching the
    headline aggregation rule. Result lets us check whether Gemini drives
    the headline number.
    """
    out_path = EXP_DIR / "scores_2openai_only.json"
    rows = []
    for score_file in sorted(SCORES_DIR.glob("pr*_kg.json")):
        ev = json.loads(score_file.read_text())
        pr_id = ev["pr_id"]
        per_judge = ev["per_judge"]
        openai_judges = [j for j in per_judge if j["model"].startswith("openai:")]
        if len(openai_judges) != 2:
            print(f"  PR{pr_id}: expected 2 OpenAI judges, got {len(openai_judges)} — skip")
            continue

        # Re-aggregate per criterion: 2-of-2 yes → 1, else → 0
        crit_scores: dict[str, list[int]] = {}
        for j in openai_judges:
            for cid, score in j["scores"].items():
                crit_scores.setdefault(cid, []).append(1 if score == 1 else 0)

        total = 0
        kg_rel = 0
        kg_ids = {"F3", "F4", "T1", "T2", "T3", "M1", "M3", "C2", "Q2"}
        for cid, scores in crit_scores.items():
            cell = 1 if sum(scores) >= 2 else 0  # 2-of-2 majority
            total += cell
            if cid in kg_ids:
                kg_rel += cell
        rows.append({"pr_id": pr_id, "total_2openai": total, "kg_rel_2openai": kg_rel})

    out_path.write_text(json.dumps(rows, indent=2))
    print(f"Wrote 2-OpenAI-only aggregate: {out_path}")
    return out_path


def main():
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    SCORES_DIR.mkdir(parents=True, exist_ok=True)

    pr_ids = sorted(
        int(p.stem.replace("pr", "").replace("_evidence", ""))
        for p in EVIDENCE_DIR.glob("pr*_evidence.json")
    )
    print(f"Found {len(pr_ids)} Joern evidence packs: {pr_ids}")
    print(f"Generator: {GENERATOR_MODEL} (T={TEMPERATURE})")
    print(f"Prompt: SYSTEM_PROMPT_KG (normal, from prnote/note.py)")
    print(f"Judges: {DEFAULT_PANEL}")
    print()

    for pr_id in pr_ids:
        review = generate_review(pr_id)
        if review is not None:
            score_review(pr_id, review)
        flush_usage(pr_id)

    print("\n=== Sensitivity: re-aggregate with 2 OpenAI judges only ===")
    aggregate_2openai_only()

    cost_summary()


if __name__ == "__main__":
    main()
