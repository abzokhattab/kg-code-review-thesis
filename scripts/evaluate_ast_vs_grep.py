#!/usr/bin/env python3
"""
Evaluate AST-KG reviews vs grep-KG reviews using the 14-criterion rubric
(the same one used in the thesis evaluation), then compare the 5 human-study criteria.
"""

import json
import re
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from prnote.llm import generate_completion

BASE_DIR = Path(__file__).resolve().parent.parent
AST_REVIEWS_DIR = BASE_DIR / "outputs" / "luca_prs_fixed_ast"
GREP_REVIEWS_DIR = BASE_DIR / "outputs" / "luca_prs_fixed"
EVIDENCE_DIR = BASE_DIR / "data" / "luca_prs_fixed"
RESULTS_FILE = BASE_DIR / "results" / "ast_vs_grep_comparison.json"

PR_IDS = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]

# The 14 criteria from evaluate_14criteria.py
CRITERIA_14 = [
    {"id": "F2*", "desc": "Does the review identify edge cases, boundary conditions, or error-path testing needs?"},
    {"id": "F3*", "desc": "Does the review check integration with existing components, APIs, or architecture/design-pattern fit?"},
    {"id": "F4",  "desc": "Does the review warn about potential breaking changes or impact on dependent code?"},
    {"id": "T1",  "desc": "Does the review ask about or discuss the need for unit/integration tests?"},
    {"id": "T3",  "desc": "Does the review reference specific test files or suggest which tests should be added/updated?"},
    {"id": "R1",  "desc": "Does the review comment on code clarity, naming conventions, or function organization?"},
    {"id": "R2",  "desc": "Does the review identify unnecessary complexity or suggest simplification?"},
    {"id": "P1",  "desc": "Does the review identify potential performance issues or inefficiencies?"},
    {"id": "S1",  "desc": "Does the review check for proper input validation or sanitization?"},
    {"id": "S3",  "desc": "Does the review assess error handling and failure recovery?"},
    {"id": "Q3",  "desc": "Does the review distinguish between blocking issues and minor suggestions?"},
    {"id": "Q5",  "desc": "Does the review explain the reasoning behind suggestions (the 'why')?"},
    {"id": "C2",  "desc": "Does the review check if similar problems are solved consistently with existing patterns?"},
    {"id": "F1",  "desc": "Does the review verify that the change addresses the stated problem or requirement?"},
]

# The 5 human-study criteria (subset of 14)
CRITERIA_5 = ["F3*", "F2*", "T3", "Q5", "R1"]


def evaluate_review(review_text: str, diff: str, pr_title: str) -> dict:
    criteria_text = "\n".join(
        f"{i+1}. [{c['id']}] {c['desc']}" for i, c in enumerate(CRITERIA_14)
    )
    criteria_ids = ", ".join(c["id"] for c in CRITERIA_14)

    system_prompt = """You are an expert code review evaluator. Your task is to assess whether a PR review meets specific quality criteria.

For each criterion, you must:
1. Determine if the review addresses that criterion (score: 1) or not (score: 0)
2. Provide a brief quote or explanation as evidence

Be strict but fair:
- Score 1 only if the review CLEARLY addresses the criterion
- Score 0 if the criterion is not addressed or only vaguely mentioned
- Base your judgment on meaning and intent, not just keywords"""

    user_prompt = f"""## PR Being Reviewed
Title: {pr_title}

## Diff (excerpt)
```
{diff[:6000]}
```

## Review to Evaluate
{review_text[:4000]}

## Criteria to Check
{criteria_text}

## Instructions
Evaluate the review against each criterion. Respond with a JSON object:

```json
{{
  "scores": [
    {{"id": "F2*", "score": 0, "evidence": "Review does not identify edge cases"}},
    {{"id": "F3*", "score": 1, "evidence": "Review checks API integration: 'the endpoint contract...'"}},
    ...continue for all {len(CRITERIA_14)} criteria...
  ]
}}
```

Important:
- Include ALL {len(CRITERIA_14)} criteria ({criteria_ids})
- Each score must be 0 or 1
- Evidence must be VERY SHORT (max 15 words)"""

    response = generate_completion(
        prompt=user_prompt,
        system=system_prompt,
        model="gpt-4o-mini",
        temperature=0.0,
    )

    text = response.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)

    json_match = re.search(r"\{[\s\S]*\}", text)
    if not json_match:
        raise ValueError("No JSON found in response")

    raw_json = json_match.group()
    try:
        result = json.loads(raw_json)
    except json.JSONDecodeError:
        raw_json = re.sub(r",\s*}", "}", raw_json)
        raw_json = re.sub(r",\s*]", "]", raw_json)
        result = json.loads(raw_json)

    scores = {}
    for item in result.get("scores", []):
        scores[item["id"]] = {
            "score": int(item["score"]),
            "evidence": item.get("evidence", ""),
        }

    # Fill missing criteria with 0
    for c in CRITERIA_14:
        if c["id"] not in scores:
            scores[c["id"]] = {"score": 0, "evidence": "Not scored by LLM"}

    return scores


def main():
    pr_ids = PR_IDS
    if len(sys.argv) > 1:
        pr_ids = [int(x) for x in sys.argv[1:]]

    results = []

    print("=" * 70)
    print("AST-KG vs Grep-KG: 14-Criterion LLM-as-Judge Evaluation")
    print("=" * 70)

    for pr_id in pr_ids:
        ast_path = AST_REVIEWS_DIR / f"pr{pr_id}_kg.md"
        grep_path = GREP_REVIEWS_DIR / f"pr{pr_id}_kg.md"
        evidence_path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"

        if not ast_path.exists() or not grep_path.exists():
            print(f"PR{pr_id}: Missing review files, skipping")
            continue

        with open(evidence_path) as f:
            evidence = json.load(f)

        diff = evidence.get("full_diff", "")
        pr_title = evidence.get("pr", {}).get("title", f"PR #{pr_id}")

        ast_review = ast_path.read_text()
        grep_review = grep_path.read_text()

        print(f"\nPR #{pr_id}: {pr_title}")
        print(f"  Evaluating grep-KG review...")
        grep_scores = evaluate_review(grep_review, diff, pr_title)

        time.sleep(1)

        print(f"  Evaluating AST-KG review...")
        ast_scores = evaluate_review(ast_review, diff, pr_title)

        time.sleep(1)

        # Extract scores
        grep_14 = {cid: grep_scores[cid]["score"] for cid in [c["id"] for c in CRITERIA_14]}
        ast_14 = {cid: ast_scores[cid]["score"] for cid in [c["id"] for c in CRITERIA_14]}

        grep_total_14 = sum(grep_14.values())
        ast_total_14 = sum(ast_14.values())

        # Print 14-criteria comparison
        print(f"\n  14-Criteria Scores: grep={grep_total_14}/14, ast={ast_total_14}/14 ({ast_total_14 - grep_total_14:+d})")

        # Print 5-criteria comparison (human study subset)
        print(f"\n  {'Criterion':<8s} {'Grep-KG':>8s} {'AST-KG':>8s} {'Diff':>6s}")
        print(f"  {'─'*8} {'─'*8} {'─'*8} {'─'*6}")
        grep_5_total = 0
        ast_5_total = 0
        for cid in CRITERIA_5:
            g = grep_14[cid]
            a = ast_14[cid]
            grep_5_total += g
            ast_5_total += a
            diff_str = "=" if g == a else ("+" if a > g else "-")
            print(f"  {cid:<8s} {g:>8d} {a:>8d} {diff_str:>6s}")
        print(f"  {'─'*8} {'─'*8} {'─'*8} {'─'*6}")
        print(f"  {'5-total':<8s} {grep_5_total:>8d} {ast_5_total:>8d} {ast_5_total - grep_5_total:>+6d}")

        results.append({
            "pr_id": pr_id,
            "pr_title": pr_title,
            "grep_scores_14": grep_14,
            "ast_scores_14": ast_14,
            "grep_evidence": {cid: grep_scores[cid]["evidence"] for cid in [c["id"] for c in CRITERIA_14]},
            "ast_evidence": {cid: ast_scores[cid]["evidence"] for cid in [c["id"] for c in CRITERIA_14]},
        })

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY: AST-KG vs Grep-KG across all PRs")
    print(f"{'='*70}")

    print(f"\n  5 Human-Study Criteria:")
    for cid in CRITERIA_5:
        grep_sum = sum(r["grep_scores_14"].get(cid, 0) for r in results)
        ast_sum = sum(r["ast_scores_14"].get(cid, 0) for r in results)
        print(f"    {cid:<6s}: grep={grep_sum}/{len(results)}, ast={ast_sum}/{len(results)} ({ast_sum - grep_sum:+d})")

    grep_5 = sum(sum(r["grep_scores_14"].get(c, 0) for c in CRITERIA_5) for r in results)
    ast_5 = sum(sum(r["ast_scores_14"].get(c, 0) for c in CRITERIA_5) for r in results)
    print(f"\n    Total 5-criteria: grep={grep_5}/{len(results)*5}, ast={ast_5}/{len(results)*5} ({ast_5 - grep_5:+d})")

    print(f"\n  All 14 Criteria:")
    all_14_ids = [c["id"] for c in CRITERIA_14]
    for cid in all_14_ids:
        grep_sum = sum(r["grep_scores_14"].get(cid, 0) for r in results)
        ast_sum = sum(r["ast_scores_14"].get(cid, 0) for r in results)
        delta = ast_sum - grep_sum
        marker = " ◄" if abs(delta) >= 2 else ""
        print(f"    {cid:<6s}: grep={grep_sum}/{len(results)}, ast={ast_sum}/{len(results)} ({delta:+d}){marker}")

    grep_total = sum(sum(r["grep_scores_14"].values()) for r in results)
    ast_total = sum(sum(r["ast_scores_14"].values()) for r in results)
    print(f"\n    Total 14-criteria: grep={grep_total}/{len(results)*14}, ast={ast_total}/{len(results)*14} ({ast_total - grep_total:+d})")

    # Save
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "metadata": {
            "run": "ast_vs_grep_comparison",
            "criteria_count": 14,
            "timestamp": datetime.now().isoformat(),
            "judge_model": "gpt-4o-mini",
        },
        "criteria_definitions": CRITERIA_14,
        "results": results,
        "summary": {
            "grep_total_14": grep_total,
            "ast_total_14": ast_total,
            "delta_14": ast_total - grep_total,
            "grep_total_5": grep_5,
            "ast_total_5": ast_5,
            "delta_5": ast_5 - grep_5,
        },
    }
    with open(RESULTS_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved → {RESULTS_FILE}")


if __name__ == "__main__":
    main()
