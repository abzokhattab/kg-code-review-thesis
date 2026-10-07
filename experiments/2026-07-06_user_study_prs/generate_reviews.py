#!/usr/bin/env python3
"""
generate_reviews.py — baseline_strict + KG reviews for the 4 new study PRs.

Prompts are verbatim from the human-study generators:
  - baseline_strict: experiments/human_study_reviews/generate_baseline_strict.py
  - kg (joern-arm):  experiments/2026-05-15_joern_kg_main/exp_gpt4o_joern.py
Generator: gpt-4o, temperature 0.0 (matches study stimuli). Idempotent.

Usage: source load_env.sh && python3 generate_reviews.py
"""
import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE = Path(__file__).resolve().parent
REPO_ROOT = BASE.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from prnote.llm import generate_completion
from prnote.note import format_kg_context, get_diff_from_evidence

OUT = BASE / "reviews"
OUT.mkdir(exist_ok=True)
MODEL = "openai:gpt-4o"
KEYS = ["requests_7433", "flask_5637", "click_3493", "requests_7328",
        "flask_5799", "click_3578"]

BASELINE_SYSTEM = """You are a senior software engineer conducting a thorough code review of a pull request.

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

KG_SYSTEM = """You are a senior software engineer conducting a thorough code review of a pull request.
You have access to repository-level structural context (test files, dependent code, callers, function signatures) that is NOT visible in the diff alone.

Your task: produce a review that leverages this structural context to surface issues a diff-only reviewer would miss.

Output Format (follow EXACTLY):

# Review Note — Evidence-Anchored

**Scope:** [One sentence describing what this PR does]

## Problem
[2-4 specific issues, ordered by severity]

## Evidence
[Bullet points with file:line references from the diff AND from the structural context]

## Impact
[Technical impact — what breaks, what regresses, what is untested]

## Recommendation (Fix / Tests / Risks)
[Numbered, actionable recommendations]

## Traceability
[Code owners if available, otherwise "Not specified"]

MANDATORY COVERAGE — your review MUST address all 9 points below. Do NOT skip any:

1. FUNCTIONALITY: Does the change break existing functionality? Check integration with callers.
2. FUNCTIONALITY: Could the change violate existing API contracts or caller expectations?
3. FUNCTIONALITY: What is the integration risk with other components? Name specific callers from the context.
4. TESTS: Are there existing unit/integration tests? Name the exact test files from the structural context.
5. TESTS: Are there missing edge case tests? Be specific about which scenario is untested.
6. TESTS: Reference the specific test files provided in the structural context.
7. MAINTAINABILITY: Does the change fit the existing architecture? Reference callers to justify.
8. MAINTAINABILITY: Are there API documentation gaps introduced by this change?
9. CONSISTENCY: Are there similar patterns elsewhere that should be updated consistently? Name callers.

CRITICAL RULES:
- You MUST name exact test file paths from the structural context (not generic "add tests")
- You MUST name specific caller functions that could be affected
- You MUST assess architecture fit with reference to the call graph
- Do NOT omit any of the 9 mandatory points above
"""


def gen(key, mode):
    out_path = OUT / f"{key}_{mode}.md"
    if out_path.exists():
        print(f"  {key}/{mode}: cached")
        return
    ev = json.loads((BASE / "evidence" / f"{key}_evidence.json").read_text())
    diff = get_diff_from_evidence(ev, max_chars=50000)
    title = ev["pr"]["title"]
    body = (ev["pr"].get("body") or "No description provided.")

    if mode == "baseline_strict":
        system = BASELINE_SYSTEM
        prompt = f"""## Pull Request: {title}

## Description
{body}

## Diff
```
{diff}
```

Generate your review note following the required format. You MUST cover all 9 mandatory points. Reference specific callers, test files, and function signatures visible in the diff above."""
    else:
        system = KG_SYSTEM
        context = format_kg_context(ev)
        prompt = f"""## Pull Request: {title}

## Description
{body}

## Diff
```
{diff}
```

{context}

Generate your review note following the required format. You MUST cover all 9 mandatory points. Reference specific callers, test files, and function signatures from the structural context above."""

    print(f"  {key}/{mode}: generating...")
    review = generate_completion(prompt=prompt, system=system, model=MODEL, temperature=0.0)
    out_path.write_text(review)
    print(f"  {key}/{mode}: saved ({len(review)} chars)")


if __name__ == "__main__":
    jobs = [(k, m) for k in KEYS for m in ("baseline_strict", "kg")]
    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(lambda j: gen(*j), jobs))
    print("done")
