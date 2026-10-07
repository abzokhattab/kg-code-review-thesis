#!/usr/bin/env python3
"""
Generate KG reviews using AST-based evidence and compare with grep-based KG reviews.

Uses the same prompt template and LLM as the original experiment,
only the evidence pack changes (AST vs grep).
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from prnote.llm import generate_completion
from prnote.note import (
    SYSTEM_PROMPT_KG,
    format_kg_context,
    get_diff_from_evidence,
)

BASE_DIR = Path(__file__).resolve().parent.parent
AST_EVIDENCE_DIR = BASE_DIR / "data" / "luca_prs_fixed_ast"
GREP_EVIDENCE_DIR = BASE_DIR / "data" / "luca_prs_fixed"
OUTPUT_DIR = BASE_DIR / "outputs" / "luca_prs_fixed_ast"
GREP_OUTPUT_DIR = BASE_DIR / "outputs" / "luca_prs_fixed"

PR_IDS = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]


def generate_review(evidence_path: Path) -> str:
    with open(evidence_path) as f:
        evidence = json.load(f)

    diff = get_diff_from_evidence(evidence)
    pr_title = evidence.get("pr", {}).get("title", "Unknown PR")
    context = format_kg_context(evidence)

    # Show what context is being injected
    context_lines = context.strip().split("\n") if context.strip() else []
    print(f"    Context: {len(context_lines)} lines, {len(context)} chars")

    user_prompt = f"""## Pull Request: {pr_title}

## Diff
```
{diff[:12000]}
```
{context}

Please generate an evidence-anchored review note following the specified format."""

    review = generate_completion(
        prompt=user_prompt,
        system=SYSTEM_PROMPT_KG,
        model=None,
        temperature=0.3,
    )
    return review


def main():
    pr_ids = PR_IDS
    if len(sys.argv) > 1:
        pr_ids = [int(x) for x in sys.argv[1:]]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Generating KG Reviews with AST Evidence")
    print("=" * 60)

    for pr_id in pr_ids:
        ast_path = AST_EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
        if not ast_path.exists():
            print(f"\nPR{pr_id}: No AST evidence, skipping")
            continue

        print(f"\n{'='*50}")
        print(f"PR #{pr_id}")
        print(f"{'='*50}")

        out_path = OUTPUT_DIR / f"pr{pr_id}_kg.md"

        try:
            print(f"  Generating AST-KG review...")
            review = generate_review(ast_path)

            with open(out_path, "w") as f:
                f.write(review)

            print(f"  Saved → {out_path} ({len(review)} chars)")

            # Brief comparison with grep-based review
            grep_review_path = GREP_OUTPUT_DIR / f"pr{pr_id}_kg.md"
            if grep_review_path.exists():
                grep_review = grep_review_path.read_text()
                print(f"  Grep-KG review: {len(grep_review)} chars")
                print(f"  AST-KG review:  {len(review)} chars")

            time.sleep(1)  # rate limit courtesy

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"Done! AST-KG reviews saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
