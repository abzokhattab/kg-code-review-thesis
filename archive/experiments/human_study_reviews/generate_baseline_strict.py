#!/usr/bin/env python3
"""
generate_baseline_strict.py

Generates prompt-symmetric baseline reviews for the human study.
Same STRICT_SYSTEM_PROMPT as exp_gpt4o_joern.py, but NO KG context injected.
This makes the contrast purely about what the LLM can say with vs. without
the knowledge graph — not about prompt differences.

Usage:
    source load_env.sh && python3 experiments/human_study_reviews/generate_baseline_strict.py
"""
import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from prnote.llm import generate_completion
from prnote.note import get_diff_from_evidence

OUT_DIR = Path(__file__).resolve().parent
OUT_DIR.mkdir(exist_ok=True)

GENERATOR_MODEL = "openai:gpt-4o"

# Same 6 PRs selected for human study
# PR9, PR15 (Grafana/TS), PR31, (scikit-learn/Python), PR38 (Grafana/TS), PR41 (Kafka/Java), PR47 (Jenkins/Java)
TARGET_PRS = [15, 22, 24, 29, 31, 38, 40, 44, 47]

STRICT_SYSTEM_PROMPT = """You are a senior software engineer conducting a thorough code review of a pull request.

Your task: produce a thorough review that surfaces integration risks, test gaps, and architecture concerns.

Output Format (follow EXACTLY):

# Review Note — Evidence-Anchored

**Scope:** [One sentence describing what this PR does]

## Problem
[2-4 specific issues, ordered by severity]

## Evidence
[Bullet points with file:line references from the diff]

## Impact
[Technical impact — what breaks, what regresses, what is untested]

## Recommendation (Fix / Tests / Risks)
[Numbered, actionable recommendations]

## Traceability
[Code owners if available, otherwise "Not specified"]

MANDATORY COVERAGE — your review MUST address all 9 points below. Do NOT skip any:

1. FUNCTIONALITY: Does the change break existing functionality? Check integration with callers.
2. FUNCTIONALITY: Could the change violate existing API contracts or caller expectations?
3. FUNCTIONALITY: What is the integration risk with other components? Name specific callers from the diff.
4. TESTS: Are there existing unit/integration tests? Name the exact test files visible in the diff.
5. TESTS: Are there missing edge case tests? Be specific about which scenario is untested.
6. TESTS: Reference the specific test files visible in the diff.
7. MAINTAINABILITY: Does the change fit the existing architecture? Reference callers visible in the diff to justify.
8. MAINTAINABILITY: Are there API documentation gaps introduced by this change?
9. CONSISTENCY: Are there similar patterns elsewhere that should be updated consistently? Name any callers visible in the diff.

CRITICAL RULES:
- You MUST name exact test file paths visible in the diff (not generic "add tests")
- You MUST name specific caller functions visible in the diff that could be affected
- You MUST assess architecture fit with reference to any call relationships visible in the diff
- Do NOT omit any of the 9 mandatory points above
- Do NOT invent file names or callers that are not in the diff — only reference what you can see
"""


def generate_baseline_strict(pr_id: int) -> str:
    out_path = OUT_DIR / f"pr{pr_id}_baseline_strict.md"
    if out_path.exists():
        print(f"  PR{pr_id}: cached, skipping")
        return out_path.read_text()

    ev_path = REPO_ROOT / "data" / "luca_prs_v2" / f"pr{pr_id}_evidence.json"
    evidence = json.loads(ev_path.read_text())

    diff = get_diff_from_evidence(evidence)
    pr = evidence.get("pr", {})
    pr_title = pr.get("title", f"PR {pr_id}")
    pr_body = pr.get("body", "No description provided.")

    user_prompt = f"""## Pull Request: {pr_title}

## Description
{pr_body}

## Diff
```
{diff}
```

Generate your review note following the required format. You MUST cover all 9 mandatory points. Reference specific callers, test files, and function signatures visible in the diff above."""

    print(f"  PR{pr_id}: generating baseline-strict (GPT-4o)...")
    review = generate_completion(
        prompt=user_prompt,
        system=STRICT_SYSTEM_PROMPT,
        model=GENERATOR_MODEL,
        temperature=0.0
    )
    out_path.write_text(review)
    print(f"  PR{pr_id}: saved to {out_path.name}")
    return review


def main():
    print(f"Generating baseline-strict reviews for PRs: {TARGET_PRS}")
    print(f"Output dir: {OUT_DIR}")
    print()
    for pr_id in TARGET_PRS:
        generate_baseline_strict(pr_id)
    print()
    print("Done. Reviews saved to experiments/human_study_reviews/")


if __name__ == "__main__":
    main()
