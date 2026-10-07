#!/usr/bin/env python3
"""
Experiment B: Stricter prompt for all 7 loss PRs.

The ablation showed that 4/7 loss PRs recover when given a stricter prompt
that mandates full criterion coverage. This experiment runs the stricter
prompt on ALL 7 loss PRs using the EXISTING Joern evidence packs (no re-parse).

Loss PRs: 2, 13, 29, 32, 42, 44, 46
Stricter prompt mandates: test files, architecture, integration, all 9 KG criteria.

Parallelized: all 7 PRs run concurrently.

Usage:
    source load_env.sh && python3 experiments/2026-05-15_joern_kg_main/exp_b_stricter_prompt.py
"""
import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

EVIDENCE_DIR = SCRIPT_DIR / "evidence"
EXP_B_DIR = SCRIPT_DIR / "exp_b"
EXP_B_DIR.mkdir(exist_ok=True)

GENERATOR_MODEL = "gemini:gemini-2.5-flash"
JUDGE_PANEL = ["gemini:gemini-2.5-flash", "gemini:gemini-2.0-flash"]
KG_CRITERIA = {'F3', 'F4', 'T3', 'M1', 'C2', 'T1', 'T2', 'M3', 'Q2'}

LOSS_PRS = [2, 13, 29, 32, 42, 44, 46]

# Stricter prompt — mandates all 9 KG-relevant criteria explicitly
STRICT_SYSTEM_PROMPT = """You are a senior software engineer conducting a thorough code review of a pull request.
You have access to repository-level structural context (test files, dependent code, callers, function signatures).

Your task: produce a review that covers ALL of the following dimensions. Do NOT skip any.

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

MANDATORY COVERAGE — your review MUST address all 9 points below. If you skip any, the review is incomplete:

1. FUNCTIONALITY: Does the change break existing functionality? Check integration with callers.
2. FUNCTIONALITY: Could the change violate existing API contracts or caller expectations?
3. FUNCTIONALITY: What is the integration risk with other components? (name specific callers from context)
4. TESTS: Are there existing unit/integration tests? Name the exact test files from the context.
5. TESTS: Are there missing edge case tests? Be specific about which scenario.
6. TESTS: Does the review reference the specific test files provided in the structural context?
7. MAINTAINABILITY: Does the change fit the existing architecture? Reference callers to justify.
8. MAINTAINABILITY: Are there API documentation gaps?
9. CONSISTENCY: Are there similar patterns elsewhere that should be updated consistently? Name callers.

CRITICAL RULES:
- You MUST name exact test file paths from the structural context (not generic "add tests")
- You MUST name specific caller functions that could be affected
- You MUST assess architecture fit with reference to the call graph
- Do NOT omit any of the 9 mandatory points above
"""


def process_pr(pr_id):
    from prnote.llm import generate_completion
    from prnote.note import format_kg_context, get_diff_from_evidence
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from evaluate_reviews import evaluate_single_review

    # Load existing Joern evidence pack
    ev_file = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    if not ev_file.exists():
        # Fallback to original evidence
        ev_file = REPO_ROOT / "data" / "luca_prs_v2" / f"pr{pr_id}_evidence.json"

    evidence = json.loads(ev_file.read_text())
    diff = get_diff_from_evidence(evidence, max_chars=50000)
    pr_title = evidence.get("pr", {}).get("title", f"PR {pr_id}")
    pr_body = evidence.get("pr", {}).get("body", "")[:500]
    context = format_kg_context(evidence)

    n_callers = evidence.get("metadata", {}).get("joern_callers_count", 0)
    n_funcs = evidence.get("metadata", {}).get("joern_functions_count", 0)
    print(f"  PR{pr_id}: evidence loaded ({n_callers} callers, {n_funcs} funcs)")

    user_prompt = f"""## Pull Request: {pr_title}

## Description
{pr_body}

## Diff
```
{diff}
```

{context}

Generate your review note following the required format. You MUST cover all 9 mandatory points. Reference specific callers, test files, and function signatures from the structural context above."""

    print(f"  PR{pr_id}: generating review (strict prompt)...")
    review = generate_completion(prompt=user_prompt, system=STRICT_SYSTEM_PROMPT,
                                 model=GENERATOR_MODEL, temperature=0.0)
    review_path = EXP_B_DIR / f"pr{pr_id}_exp_b_review.md"
    review_path.write_text(review)

    print(f"  PR{pr_id}: evaluating...")
    ev = evaluate_single_review(review_path, pr_id, "exp_b_strict_prompt", JUDGE_PANEL)
    result = asdict(ev)
    (EXP_B_DIR / f"pr{pr_id}_exp_b_eval.json").write_text(json.dumps(result, indent=2))

    kgrel = sum(cs['score'] for cs in result.get('criteria_scores', [])
                if cs['criterion_id'] in KG_CRITERIA)
    total = result.get('total_score', 0)
    print(f"  PR{pr_id}: total={total}/25, KG-rel={kgrel}/9")
    return pr_id, total, kgrel


def main():
    print("=" * 70)
    print(f"EXPERIMENT B: Stricter Prompt for Loss PRs ({LOSS_PRS})")
    print(f"Generator: {GENERATOR_MODEL} | Judges: {JUDGE_PANEL}")
    print("=" * 70)

    # Load baselines and original Joern scores
    _raw = json.loads((REPO_ROOT / "results" / "checklist_evaluation_llm_multi__v2.json").read_text())
    baseline_json = _raw["evaluations"] if isinstance(_raw, dict) else _raw
    baseline = {e['pr_id']: e for e in baseline_json if e['mode'] == 'baseline'}

    orig_joern = {}
    for pr_id in LOSS_PRS:
        ef = SCRIPT_DIR / "controlled" / f"pr{pr_id}_eval.json"
        if ef.exists():
            d = json.loads(ef.read_text())
            kgrel = sum(cs['score'] for cs in d.get('criteria_scores', [])
                        if cs['criterion_id'] in KG_CRITERIA)
            orig_joern[pr_id] = {'total': d.get('total_score', 0), 'kgrel': kgrel}

    print(f"\nBaseline / Original Joern (before fix):")
    for pr_id in LOSS_PRS:
        bl = baseline.get(pr_id, {})
        oj = orig_joern.get(pr_id, {})
        bl_kg = bl.get('kg_relevant_score', '?')
        oj_kg = oj.get('kgrel', '?')
        delta_orig = (oj_kg - bl_kg) if isinstance(oj_kg, (int,float)) and isinstance(bl_kg, (int,float)) else '?'
        print(f"  PR{pr_id}: baseline={bl_kg} | orig_joern={oj_kg} (Δ={delta_orig:+})" if isinstance(delta_orig, (int,float)) else f"  PR{pr_id}: baseline={bl_kg} | orig_joern={oj_kg}")

    # Run all 7 PRs in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=7) as ex:
        futures = {ex.submit(process_pr, pr_id): pr_id for pr_id in LOSS_PRS}
        for fut in as_completed(futures):
            pr_id, total, kgrel = fut.result()
            results[pr_id] = {'total': total, 'kgrel': kgrel}

    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(f"{'PR':>4} {'BL_kg':>6} {'OrigJ_kg':>9} {'ExpB_kg':>8} {'Δ_BL':>6} {'Δ_Orig':>7} {'Outcome':>8}")
    print("-" * 55)

    recovered = 0
    for pr_id in LOSS_PRS:
        bl_kg = baseline.get(pr_id, {}).get('kg_relevant_score', 0)
        oj_kg = orig_joern.get(pr_id, {}).get('kgrel', 0)
        eb_kg = results.get(pr_id, {}).get('kgrel', 0)
        d_bl = eb_kg - bl_kg
        d_orig = eb_kg - oj_kg
        outcome = "RECOVERED" if d_bl >= 0 else "STILL LOSS"
        if d_bl >= 0:
            recovered += 1
        print(f"pr{pr_id:>2} {bl_kg:>6} {oj_kg:>9} {eb_kg:>8} {d_bl:>+6} {d_orig:>+7} {outcome:>9}")

    print(f"\nRecovered: {recovered}/{len(LOSS_PRS)} loss PRs → now ties or wins vs baseline")

    # Write results
    out = {
        "experiment": "B",
        "description": "Stricter prompt mandating all 9 KG criteria on 7 loss PRs",
        "loss_prs": LOSS_PRS,
        "results": {str(k): v for k, v in results.items()},
        "baseline": {str(k): {'kgrel': baseline[k].get('kg_relevant_score')} for k in LOSS_PRS if k in baseline},
        "orig_joern": {str(k): v for k, v in orig_joern.items()},
        "recovered": recovered,
    }
    (EXP_B_DIR / "results.json").write_text(json.dumps(out, indent=2))
    print(f"\nWrote: {EXP_B_DIR}/results.json")


if __name__ == "__main__":
    main()
