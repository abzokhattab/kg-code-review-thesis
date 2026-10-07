#!/usr/bin/env python3
"""Regenerate KG reviews with improved prompt that forces evidence utilization.

Motivation (from moderation analysis 2026-05-14):
  - The current KG prompt tells the model "use structural context" but doesn't
    enforce it. The model mentions only 11% of available test files (23/203).
  - When the model DOES use KG evidence (mentions ≥1 test file), KG-rel Δ = +1.25.
  - When it ignores evidence, Δ = +0.10.
  - Fix: restructured output format that requires explicit test/dependency sections.

This script generates ONLY the 'kg' mode reviews for all 40 v2 PRs using:
  1. An improved system prompt with mandatory structural sections
  2. A reformatted KG context block with explicit instructions per section

Output: outputs/luca_prs_v2_kg_v3/pr{N}_kg.md
Cost estimate: 40 reviews × ~$0.10 each = ~$4 (GPT-4o)
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prnote.llm import generate_completion
from prnote.note import get_diff_from_evidence, _rank_tests_by_relevance, _dominant_cohorts, _keep_by_cohort

# =============================================================================
# IMPROVED KG SYSTEM PROMPT — forces explicit structural sections
# =============================================================================

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

# =============================================================================
# IMPROVED KG CONTEXT FORMATTER — sections with explicit instructions
# =============================================================================

def format_kg_context_v3(evidence: dict) -> str:
    """Format KG context with explicit utilization instructions per section."""
    sections = []
    changed_files = evidence.get('changed_files', [])
    cohorts = _dominant_cohorts(changed_files)

    if changed_files:
        if isinstance(changed_files[0], dict):
            file_list = [f.get('path', str(f)) for f in changed_files]
        else:
            file_list = changed_files
        sections.append(f"### Changed Files\n{chr(10).join('- ' + f for f in file_list[:15])}")

    # Tests — explicit instruction
    tests_raw = evidence.get('nearest_tests', evidence.get('kg_evidence', {}).get('nearest_tests', []))
    if tests_raw:
        ranked = _rank_tests_by_relevance(tests_raw, changed_files)
        filtered = _keep_by_cohort(ranked, cohorts)
        if filtered:
            if isinstance(filtered[0], dict):
                test_list = [t.get('path', t.get('file', str(t))) for t in filtered]
            else:
                test_list = filtered
            test_section = "### Test Files Covering Changed Code\n"
            test_section += "⚠️ YOU MUST discuss each of these in your Test Coverage Assessment section:\n"
            test_section += "\n".join(f"- `{t}`" for t in test_list[:12])
            sections.append(test_section)

    # Dependents — explicit instruction
    deps_raw = evidence.get('dependent_files', evidence.get('kg_evidence', {}).get('dependent_files', []))
    if deps_raw:
        filtered = _keep_by_cohort(deps_raw, cohorts)
        if filtered:
            if isinstance(filtered[0], dict):
                dep_list = [d.get('path', str(d)) for d in filtered]
            else:
                dep_list = filtered
            dep_section = "### Files That DEPEND on Changed Code (Callers/Importers)\n"
            dep_section += "⚠️ YOU MUST assess integration risk for each in your Integration Risk section:\n"
            dep_section += "\n".join(f"- `{d}`" for d in dep_list[:15])
            sections.append(dep_section)

    # Owners
    owners = evidence.get('owners', evidence.get('kg_evidence', {}).get('owners', []))
    if owners:
        if isinstance(owners[0], dict):
            owner_list = [o.get('handle', str(o)) for o in owners]
        else:
            owner_list = owners
        sections.append(f"### Code Owners\n{', '.join(owner_list[:5])}")

    # Call graph
    call_edges = evidence.get('call_graph_edges', [])
    callers = evidence.get('callers', [])
    if call_edges and isinstance(call_edges, list) and call_edges and isinstance(call_edges[0], dict):
        rendered = []
        seen = set()
        for e in call_edges:
            src = e.get('from') or e.get('caller') or e.get('src')
            dst = e.get('to') or e.get('callee') or e.get('dst') or e.get('calls_function')
            if not src or not dst:
                continue
            key = (str(src), str(dst))
            if key in seen:
                continue
            seen.add(key)
            rendered.append(f"  {src} → {dst}")
            if len(rendered) >= 10:
                break
        if rendered:
            sections.append(f"### Call Graph (who calls what)\n" + "\n".join(rendered))

    if not sections:
        return ""

    header = "\n---\n## 📊 Repository Structural Context (from Knowledge Graph)\n"
    header += "The following information is NOT visible in the diff. Use it.\n\n"
    return header + "\n\n".join(sections) + "\n---\n"


# =============================================================================
# MAIN
# =============================================================================

def main():
    evidence_dir = Path("data/luca_prs_v2")
    output_dir = Path("outputs/luca_prs_v2_kg_v3")
    output_dir.mkdir(parents=True, exist_ok=True)

    model = os.environ.get("MODEL_NAME", "openai:gpt-4o")

    # Find all evidence files
    evidence_files = sorted(evidence_dir.glob("pr*_evidence.json"))
    if not evidence_files:
        print(f"No evidence files found in {evidence_dir}")
        sys.exit(1)

    print(f"Found {len(evidence_files)} evidence packs")
    print(f"Model: {model}")
    print(f"Output: {output_dir}")
    print()

    # Dry run check
    if "--dry-run" in sys.argv:
        for ef in evidence_files:
            pr_num = ef.stem.replace("_evidence", "").replace("pr", "")
            with open(ef) as f:
                ev = json.load(f)
            ctx = format_kg_context_v3(ev)
            print(f"PR {pr_num}: context = {len(ctx)} chars")
        print("\nDry run complete. Remove --dry-run to generate.")
        return

    generated = 0
    skipped = 0

    for ef in evidence_files:
        pr_num = ef.stem.replace("_evidence", "").replace("pr", "")
        out_file = output_dir / f"pr{pr_num}_kg.md"

        # Skip if already generated (idempotent)
        if out_file.exists() and "--force" not in sys.argv:
            skipped += 1
            continue

        with open(ef) as f:
            evidence = json.load(f)

        diff = get_diff_from_evidence(evidence, max_chars=50000)
        pr_title = evidence.get('pr', {}).get('title', f'PR {pr_num}')
        context = format_kg_context_v3(evidence)

        user_prompt = f"""## Pull Request: {pr_title}

## Diff
```
{diff}
```

{context}

Generate your review note following the required format. Remember: you MUST reference specific test files and dependent files from the structural context above."""

        print(f"  Generating PR {pr_num}...", end=" ", flush=True)

        try:
            review = generate_completion(
                prompt=user_prompt,
                system=SYSTEM_PROMPT_KG_V3,
                model=model,
                temperature=0.3
            )
            with open(out_file, 'w') as f:
                f.write(review)
            generated += 1
            print(f"✓ ({len(review)} chars)")
        except Exception as e:
            print(f"✗ Error: {e}")

    print(f"\nDone: {generated} generated, {skipped} skipped (already exist)")
    print(f"Output: {output_dir}/")
    print(f"\nNext step: evaluate with")
    print(f"  python3 -m scripts.evaluate_reviews --outputs-dir {output_dir} --output-suffix v2_kg_v3")


if __name__ == "__main__":
    main()
