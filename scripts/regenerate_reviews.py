#!/usr/bin/env python3
"""
Regenerate PR reviews using the fixed KG evidence packs.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for prnote imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from prnote.llm import generate_completion
from prnote.note import (
    SYSTEM_PROMPT_BASELINE, 
    SYSTEM_PROMPT_KG, 
    SYSTEM_PROMPT_RAG,
    SYSTEM_PROMPT_HYBRID,
    format_kg_context,
    format_rag_context,
    format_hybrid_context,
    get_diff_from_evidence,
)

# Configuration
EVIDENCE_DIR = Path("/Users/akhattab/ai/data/luca_prs_fixed")
OUTPUT_DIR = Path("/Users/akhattab/ai/outputs/luca_prs_fixed")

# PRs to process (skip PR4 - not merged)
PR_IDS = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11]

# All four modes for the 4-way comparison
MODES = ["baseline", "rag", "kg", "hybrid"]


def generate_review(evidence_path: Path, mode: str) -> str:
    """Generate a review for the given evidence and mode."""
    with open(evidence_path, 'r') as f:
        evidence_data = json.load(f)
    
    # Get diff from evidence
    diff = get_diff_from_evidence(evidence_data)
    pr_title = evidence_data.get('pr', {}).get('title', 'Unknown PR')
    
    # Select system prompt and context based on mode
    if mode == "baseline":
        system_prompt = SYSTEM_PROMPT_BASELINE
        context = ""
    elif mode == "rag":
        system_prompt = SYSTEM_PROMPT_RAG
        context = format_rag_context(evidence_data)
    elif mode == "kg":
        system_prompt = SYSTEM_PROMPT_KG
        context = format_kg_context(evidence_data)
    elif mode == "hybrid":
        system_prompt = SYSTEM_PROMPT_HYBRID
        context = format_hybrid_context(evidence_data)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    user_prompt = f"""## Pull Request: {pr_title}

## Diff
```
{diff}
```
{context}

Please generate an evidence-anchored review note following the specified format."""
    
    # Generate review
    review = generate_completion(
        prompt=user_prompt,
        system=system_prompt,
        model=None,
        temperature=0.3
    )
    
    return review


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Regenerating PR Reviews with Fixed KG Evidence")
    print("=" * 60)
    
    total_generated = 0
    total_errors = 0
    
    for pr_id in PR_IDS:
        evidence_path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
        
        if not evidence_path.exists():
            print(f"\n⚠️ PR{pr_id}: Evidence file not found, skipping")
            continue
        
        print(f"\n{'='*40}")
        print(f"PR #{pr_id}")
        print(f"{'='*40}")
        
        for mode in MODES:
            output_path = OUTPUT_DIR / f"pr{pr_id}_{mode}.md"
            
            try:
                print(f"  Generating {mode} review...", end=" ", flush=True)
                
                review = generate_review(evidence_path, mode)
                
                # Save review
                with open(output_path, 'w') as f:
                    f.write(review)
                
                print(f"✓ ({len(review)} chars)")
                total_generated += 1
                
            except Exception as e:
                print(f"✗ Error: {e}")
                total_errors += 1
    
    print("\n" + "=" * 60)
    print(f"Done! Generated {total_generated} reviews, {total_errors} errors")
    print(f"Reviews saved to: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
