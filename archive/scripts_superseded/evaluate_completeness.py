#!/usr/bin/env python3
"""
Completeness (C6) LLM scoring — post-pilot addition, multi-judge panel.

Added after pilot feedback from the supervisor: "Some reviews have more
information than others — should we add a criterion for 'no obvious
missing information'?"

This criterion corresponds to DeepCRCEval's C6 (Completeness, Lu et al.,
2024) but is operationalized as a binary judgment ("no obvious omissions")
to be tractable without ground-truth review references.

Reads the exact review texts shown to human raters from
human_eval/study_data.json (so LLM and human evaluators see the same
material), scores C6 for every (PR, mode) pair with one or more judge
models, then aggregates via majority vote. Writes:
  results/c6_completeness_llm.json

Multi-judge motivation: single-judge LLM-as-a-judge has known biases
(model family, verbosity, position). A small cross-provider panel with
majority vote mitigates this, per Zheng et al. (2023, NeurIPS).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from prnote.llm import generate_completion  # noqa: E402


STUDY_DATA_PATH = REPO_ROOT / "human_eval" / "study_data.json"
OUTPUT_PATH = REPO_ROOT / "results" / "c6_completeness_llm.json"

# Keep the diff bounded so we don't blow the token budget. 6k chars ~
# matches what a careful human reviewer would skim before judging
# completeness, and matches the envelope used by evaluate_reviews.py.
MAX_DIFF_CHARS = 6000
MAX_REVIEW_CHARS = 4000
MAX_BODY_CHARS = 500

SYSTEM_PROMPT = """You are an expert code reviewer judging the COMPLETENESS of AI-generated code review comments.

Your single task: decide whether the review has any OBVIOUS missing information that a competent human reviewer looking at this PR would be expected to mention.

Scoring rules:
- Score 1 (Y) if the review has NO obvious omissions — it covers the issues a competent reviewer would be expected to flag for this PR.
- Score 0 (N) if there is an OBVIOUS omission — the review clearly misses something visible in the diff that a competent reviewer would flag.

Be strict but fair:
- "Obvious" means visible in the diff or trivially inferable from it. Do not penalise for speculative omissions.
- Do not reward verbose but generic reviews. A short review that covers the obvious can score 1.
- Do not penalise brevity per se. Penalise only when something visibly important was missed.

Output format: a single JSON object on one line. No prose outside the JSON.
"""


USER_PROMPT_TEMPLATE = """## PR Context
Title: {title}
Description: {body}

## PR Diff (truncated to first {diff_limit} characters)
```diff
{diff}
```

## Review Under Evaluation
{review}

## Judgment
Apply the Completeness (C6) criterion: "Does the review cover the obvious issues in the PR without obvious missing information?"

Respond with exactly this JSON:
{{"id": "C6", "score": 0 or 1, "evidence": "short explanation (<=200 chars) citing what was or was not covered"}}
"""


@dataclass
class JudgeVerdict:
    """One judge's verdict for a single (pr, mode) pair."""
    model: str
    score: int  # 0 or 1; -1 on error
    evidence: str
    error: str = ""


@dataclass
class CompletenessScore:
    """Aggregated verdict across the judge panel for one (pr, mode) pair."""
    pr_id: int
    mode: str
    score: int  # majority vote (0 or 1); -1 if no valid verdicts
    unanimous: bool
    n_judges: int
    n_valid: int
    n_yes: int
    verdicts: list[dict[str, Any]]  # per-judge details
    timestamp: str


def build_prompt(pr: dict, mode: str) -> str:
    review = (pr.get("reviews") or {}).get(mode, "")
    return USER_PROMPT_TEMPLATE.format(
        title=pr.get("title", "") or "(no title)",
        body=(pr.get("body") or "")[:MAX_BODY_CHARS] or "(no description)",
        diff_limit=MAX_DIFF_CHARS,
        diff=(pr.get("diff") or "")[:MAX_DIFF_CHARS] or "(diff unavailable)",
        review=review[:MAX_REVIEW_CHARS] or "(empty review)",
    )


JSON_OBJECT_RE = re.compile(r"\{[\s\S]*\}")


def parse_response(raw: str) -> tuple[int, str]:
    """Extract (score, evidence) from an LLM response; tolerant to extra prose."""
    match = JSON_OBJECT_RE.search(raw or "")
    if not match:
        raise ValueError(f"no JSON object in response: {raw[:200]!r}")
    payload = json.loads(match.group())
    score = int(payload.get("score", 0))
    if score not in (0, 1):
        raise ValueError(f"invalid score {score!r}, expected 0 or 1")
    evidence = str(payload.get("evidence", "")).strip()[:500]
    return score, evidence


def judge_one(pr: dict, mode: str, model: str) -> JudgeVerdict:
    """Ask a single judge to score this (pr, mode) pair."""
    prompt = build_prompt(pr, mode)
    try:
        raw = generate_completion(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            model=model,
            temperature=0.0,
        )
    except Exception as exc:
        return JudgeVerdict(model=model, score=-1, evidence="", error=f"api_error: {exc}")
    try:
        score, evidence = parse_response(raw)
    except Exception as exc:
        return JudgeVerdict(model=model, score=-1, evidence=(raw or "")[:200], error=f"parse_error: {exc}")
    return JudgeVerdict(model=model, score=score, evidence=evidence)


def score_one(pr: dict, mode: str, models: list[str]) -> CompletenessScore:
    """Run the full judge panel and aggregate via majority vote."""
    verdicts = [judge_one(pr, mode, m) for m in models]
    valid = [v for v in verdicts if v.score in (0, 1)]
    n_yes = sum(1 for v in valid if v.score == 1)
    n_valid = len(valid)

    if n_valid == 0:
        agg_score = -1
        unanimous = False
    else:
        # Majority vote; ties break towards N (strict: needs majority Yes to get Yes).
        agg_score = 1 if n_yes > n_valid - n_yes else 0
        unanimous = (n_yes == n_valid) or (n_yes == 0)

    return CompletenessScore(
        pr_id=pr["pr_id"],
        mode=mode,
        score=agg_score,
        unanimous=unanimous,
        n_judges=len(verdicts),
        n_valid=n_valid,
        n_yes=n_yes,
        verdicts=[asdict(v) for v in verdicts],
        timestamp=_now_iso(),
    )


def run(models: list[str]) -> dict[str, Any]:
    with STUDY_DATA_PATH.open() as f:
        study = json.load(f)

    modes = study.get("modes", [])
    prs = study.get("prs", [])

    total_pairs = len(prs) * len(modes)
    total_calls = total_pairs * len(models)
    print(f"Scoring C6 (Completeness) — multi-judge panel")
    print(f"  Judges ({len(models)}): {', '.join(models)}")
    print(f"  Rubric version: {study.get('version')}")
    print(f"  PRs: {len(prs)} | Modes: {modes}")
    print(f"  Total pairs: {total_pairs} × {len(models)} judges = {total_calls} calls\n")

    scores: list[CompletenessScore] = []
    for i, pr in enumerate(prs, start=1):
        for mode in modes:
            if mode not in (pr.get("reviews") or {}):
                print(f"[{i}] PR#{pr['pr_id']} {mode}: SKIP (no review)")
                continue
            print(f"[{i}] PR#{pr['pr_id']} {mode}: ", end="", flush=True)
            s = score_one(pr, mode, models)
            scores.append(s)
            agg = "Y" if s.score == 1 else ("N" if s.score == 0 else "?")
            per_judge = " ".join(
                f"{v['model'].split(':')[-1]}={'Y' if v['score']==1 else ('N' if v['score']==0 else 'err')}"
                for v in s.verdicts
            )
            u = " [unanimous]" if s.unanimous and s.n_valid == len(models) else ""
            print(f"{agg} ({s.n_yes}/{s.n_valid}) {per_judge}{u}")

    # Summary
    by_mode: dict[str, dict[str, Any]] = {}
    for mode in modes:
        mscores = [s for s in scores if s.mode == mode and s.score in (0, 1)]
        if not mscores:
            continue
        by_mode[mode] = {
            "n": len(mscores),
            "yes_count_majority": sum(1 for s in mscores if s.score == 1),
            "yes_rate_pct_majority": round(100.0 * sum(1 for s in mscores if s.score == 1) / len(mscores), 1),
            "unanimous_count": sum(1 for s in mscores if s.unanimous),
        }

    by_judge: dict[str, dict[str, dict[str, Any]]] = {m: {} for m in models}
    for m in models:
        for mode in modes:
            judge_scores = []
            for s in scores:
                if s.mode != mode:
                    continue
                for v in s.verdicts:
                    if v["model"] == m and v["score"] in (0, 1):
                        judge_scores.append(v["score"])
            if not judge_scores:
                continue
            by_judge[m][mode] = {
                "n": len(judge_scores),
                "yes_count": sum(judge_scores),
                "yes_rate_pct": round(100.0 * sum(judge_scores) / len(judge_scores), 1),
            }

    # Inter-judge agreement (pairwise, across all (pr, mode) pairs where both voted validly)
    agreement: dict[str, dict[str, Any]] = {}
    for i, m1 in enumerate(models):
        for m2 in models[i + 1:]:
            both_valid = 0
            agreed = 0
            for s in scores:
                v1 = next((v for v in s.verdicts if v["model"] == m1 and v["score"] in (0, 1)), None)
                v2 = next((v for v in s.verdicts if v["model"] == m2 and v["score"] in (0, 1)), None)
                if v1 and v2:
                    both_valid += 1
                    if v1["score"] == v2["score"]:
                        agreed += 1
            if both_valid:
                agreement[f"{m1} vs {m2}"] = {
                    "pairs": both_valid,
                    "agreed": agreed,
                    "agreement_pct": round(100.0 * agreed / both_valid, 1),
                }

    output = {
        "metadata": {
            "criterion_id": "C6",
            "criterion_name": "Completeness",
            "criterion_description": (
                "Does the review cover the obvious issues in the PR without "
                "obvious missing information?"
            ),
            "origin": (
                "Added post-pilot following supervisor feedback; aligns with "
                "DeepCRCEval C6 (Lu et al., 2024). Multi-judge panel per "
                "Zheng et al. (2023) to mitigate single-judge bias."
            ),
            "judges": models,
            "aggregation": "majority_vote (ties → N)",
            "study_data_version": study.get("version"),
            "study_data_path": str(STUDY_DATA_PATH.relative_to(REPO_ROOT)),
            "timestamp": _now_iso(),
            "max_review_chars": MAX_REVIEW_CHARS,
            "max_diff_chars": MAX_DIFF_CHARS,
            "max_body_chars": MAX_BODY_CHARS,
        },
        "scores": [asdict(s) for s in scores],
        "summary": {
            "by_mode_majority": by_mode,
            "by_judge": by_judge,
            "inter_judge_agreement": agreement,
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWrote {OUTPUT_PATH.relative_to(REPO_ROOT)}\n")
    print("Yes rate by mode (majority vote):")
    for mode, info in by_mode.items():
        print(f"  {mode:<10} {info['yes_count_majority']}/{info['n']}  ({info['yes_rate_pct_majority']}%)  unanimous: {info['unanimous_count']}/{info['n']}")

    print("\nYes rate by judge × mode:")
    for m, mode_info in by_judge.items():
        if not mode_info:
            continue
        parts = [f"{mode}: {info['yes_count']}/{info['n']} ({info['yes_rate_pct']}%)" for mode, info in mode_info.items()]
        print(f"  {m:<32} {' | '.join(parts)}")

    if agreement:
        print("\nInter-judge agreement (raw %):")
        for pair, info in agreement.items():
            print(f"  {pair:<60} {info['agreed']}/{info['pairs']}  ({info['agreement_pct']}%)")

    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Score C6 (Completeness) for all (PR, mode) pairs in study_data.json using a multi-judge LLM panel")
    parser.add_argument(
        "--models",
        default="openai:gpt-4o-mini,openai:gpt-4o,gemini:gemini-2.5-flash",
        help="Comma-separated judge models (default: openai:gpt-4o-mini,openai:gpt-4o,gemini:gemini-2.5-flash)",
    )
    args = parser.parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not models:
        parser.error("at least one model is required")
    run(models)


if __name__ == "__main__":
    main()
