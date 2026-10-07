#!/usr/bin/env python3
"""
generate_reviews.py — Generate baseline + KG v3 reviews for confirmatory PRs.

For each PR in evidence/:
  - Baseline: diff-only review (same as v2 main experiment)
  - KG v3: improved prompt with mandatory structural sections

Output: experiments/2026-05-14_confirmatory_kg/reviews/pr{N}_{baseline,kg}.md

Estimated cost: 12 PRs × 2 modes × ~$0.10 = ~$2.40
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from prnote.llm import generate_completion
from prnote.note import get_diff_from_evidence, _rank_tests_by_relevance, _dominant_cohorts, _keep_by_cohort

EVIDENCE_DIR = SCRIPT_DIR / "evidence"
REVIEWS_DIR = SCRIPT_DIR / "reviews"

# --- Baseline prompt (same as v2 main experiment) ---
SYSTEM_PROMPT_BASELINE = """You are a senior software engineer conducting a thorough code review of a pull request.
You only have access to the PR diff. Provide a detailed review covering:
- Potential bugs or logic errors
- Code quality and readability issues
- Security concerns
- Performance implications
- Test coverage gaps
- Architectural fit

Output Format (follow EXACTLY):

# Review Note — Evidence-Anchored

**Scope:** [One sentence describing what this PR does]

## Problem
[2-3 specific issues found in the code]

## Evidence
[Bullet points with file:line references from the diff]

## Impact
[Technical impact — what could go wrong]

## Recommendation (Fix / Tests / Risks)
[Numbered, actionable recommendations]

## Traceability
[Code owners if available, otherwise "Not specified"]
"""

# --- KG v3 prompt (same as scripts/regenerate_reviews_kg_v3.py) ---
SYSTEM_PROMPT_KG_V3 = """You are a senior software engineer conducting a thorough code review of a pull request.
You have access to repository-level structural context (test files, dependent code, code owners) that is NOT visible in the diff alone.

Your task: produce a review that leverages this structural context to surface issues a diff-only reviewer would miss.

Output Format (follow EXACTLY — every section is MANDATORY):

# Review Note — Evidence-Anchored

**Scope:** [One sentence describing what this PR does]

## Integration Risk
[For EACH dependent file listed in the context, assess whether the change could break it. Name specific files.]

## Test Coverage Assessment
[For EACH test file listed in the context:
 - State whether the test covers the changed behavior
 - If coverage is adequate, say so
 - If coverage gaps exist, name the specific scenario not tested]

## Problem
[2-3 specific issues, prioritizing integration risks and test gaps over style]

## Evidence
[Bullet points with file:line references from the diff AND from the KG context]

## Impact
[Technical impact — what breaks, what regresses, what is untested]

## Recommendation
[Numbered, actionable. At least one must address test coverage. At least one must address integration.]

## Traceability
[Code owners if available, otherwise "Not specified"]

CRITICAL RULES:
- You MUST reference specific test file paths from the provided context
- You MUST reference specific dependent files from the provided context
- Do NOT give generic advice like "consider adding tests" — name the EXACT test file and what scenario to add
- Do NOT ignore the structural context — it is the most valuable part of your input
- Prioritize: integration risks > test gaps > correctness > style
"""


def format_kg_context_v3(evidence: dict) -> str:
    sections = []
    changed_files = evidence.get('changed_files', [])
    cohorts = _dominant_cohorts(changed_files)

    if changed_files:
        if isinstance(changed_files[0], dict):
            file_list = [f.get('path', str(f)) for f in changed_files]
        else:
            file_list = changed_files
        sections.append(f"### Changed Files\n{chr(10).join('- ' + f for f in file_list[:15])}")

    tests_raw = evidence.get('nearest_tests', [])
    if tests_raw:
        ranked = _rank_tests_by_relevance(tests_raw, changed_files)
        filtered = _keep_by_cohort(ranked, cohorts)
        if filtered:
            if isinstance(filtered[0], dict):
                test_list = [t.get('path', t.get('file', str(t))) for t in filtered]
            else:
                test_list = filtered
            test_section = "### Test Files Covering Changed Code\n"
            test_section += "YOU MUST discuss each of these in your Test Coverage Assessment section:\n"
            test_section += "\n".join(f"- `{t}`" for t in test_list[:12])
            sections.append(test_section)

    deps_raw = evidence.get('dependent_files', [])
    if deps_raw:
        filtered = _keep_by_cohort(deps_raw, cohorts)
        if filtered:
            if isinstance(filtered[0], dict):
                dep_list = [d.get('path', str(d)) for d in filtered]
            else:
                dep_list = filtered
            dep_section = "### Files That DEPEND on Changed Code (Callers/Importers)\n"
            dep_section += "YOU MUST assess integration risk for each in your Integration Risk section:\n"
            dep_section += "\n".join(f"- `{d}`" for d in dep_list[:15])
            sections.append(dep_section)

    call_edges = evidence.get('call_graph_edges', [])
    if call_edges and isinstance(call_edges, list) and call_edges and isinstance(call_edges[0], dict):
        rendered = []
        seen = set()
        for e in call_edges:
            src = e.get('from') or e.get('caller') or e.get('src')
            dst = e.get('to') or e.get('callee') or e.get('dst')
            if not src or not dst:
                continue
            key = (str(src), str(dst))
            if key in seen:
                continue
            seen.add(key)
            rendered.append(f"  {src} -> {dst}")
            if len(rendered) >= 10:
                break
        if rendered:
            sections.append(f"### Call Graph (who calls what)\n" + "\n".join(rendered))

    if not sections:
        return ""

    header = "\n---\n## Repository Structural Context (from Knowledge Graph)\n"
    header += "The following information is NOT visible in the diff. Use it.\n\n"
    return header + "\n\n".join(sections) + "\n---\n"


def main():
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    model = os.environ.get("MODEL_NAME", "openai:gpt-4o")
    evidence_files = sorted(EVIDENCE_DIR.glob("pr*_evidence.json"))

    if not evidence_files:
        sys.exit(f"No evidence files in {EVIDENCE_DIR}. Run fetch_evidence.py first.")

    print(f"Generating reviews for {len(evidence_files)} confirmatory PRs")
    print(f"Model: {model}")
    print(f"Modes: baseline, kg (v3 prompt)")
    print(f"Output: {REVIEWS_DIR}/")
    print()

    generated = 0
    skipped = 0

    for ef in evidence_files:
        pr_num = ef.stem.replace("_evidence", "").replace("pr", "")

        with open(ef) as f:
            evidence = json.load(f)

        diff = get_diff_from_evidence(evidence, max_chars=50000)
        pr_title = evidence.get('pr', {}).get('title', f'PR {pr_num}')
        pr_body = evidence.get('pr', {}).get('body', '')[:500]

        # --- Baseline ---
        bl_file = REVIEWS_DIR / f"pr{pr_num}_baseline.md"
        if bl_file.exists() and "--force" not in sys.argv:
            print(f"  PR {pr_num} baseline: exists, skipping")
            skipped += 1
        else:
            user_prompt = f"""## Pull Request: {pr_title}

## Description
{pr_body}

## Diff
```
{diff}
```

Generate your review note following the required format."""

            print(f"  PR {pr_num} baseline...", end=" ", flush=True)
            try:
                review = generate_completion(
                    prompt=user_prompt,
                    system=SYSTEM_PROMPT_BASELINE,
                    model=model,
                    temperature=0.0,
                )
                bl_file.write_text(review)
                generated += 1
                print(f"OK ({len(review)} chars)")
            except Exception as e:
                print(f"ERROR: {e}")

        # --- KG v3 ---
        kg_file = REVIEWS_DIR / f"pr{pr_num}_kg.md"
        if kg_file.exists() and "--force" not in sys.argv:
            print(f"  PR {pr_num} kg: exists, skipping")
            skipped += 1
        else:
            context = format_kg_context_v3(evidence)
            user_prompt = f"""## Pull Request: {pr_title}

## Description
{pr_body}

## Diff
```
{diff}
```

{context}

Generate your review note following the required format. Remember: you MUST reference specific test files and dependent files from the structural context above."""

            print(f"  PR {pr_num} kg...", end=" ", flush=True)
            try:
                review = generate_completion(
                    prompt=user_prompt,
                    system=SYSTEM_PROMPT_KG_V3,
                    model=model,
                    temperature=0.3,
                )
                kg_file.write_text(review)
                generated += 1
                print(f"OK ({len(review)} chars)")
            except Exception as e:
                print(f"ERROR: {e}")

    print(f"\nDone: {generated} generated, {skipped} skipped")
    print(f"Reviews in {REVIEWS_DIR}/")
    print(f"\nNext: evaluate with judge panel")


if __name__ == "__main__":
    main()
