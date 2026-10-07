#!/usr/bin/env python3
"""
exp_b_full35.py — Re-run ALL 35 non-Go PRs with the strict prompt.

Same Joern evidence packs, same CPGs, same judge panel.
Strict prompt mandates all 9 KG-relevant criteria explicitly.
All 35 PRs run in parallel.

Usage:
    source load_env.sh && python3 experiments/2026-05-15_joern_kg_main/exp_b_full35.py
"""
import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

EVIDENCE_DIR = SCRIPT_DIR / "evidence"
OUT_DIR = SCRIPT_DIR / "exp_b_full35"
OUT_DIR.mkdir(exist_ok=True)

GENERATOR_MODEL = "gemini:gemini-2.5-flash"
JUDGE_PANEL = ["gemini:gemini-2.5-flash", "gemini:gemini-2.0-flash"]
KG_CRITERIA = {'F3', 'F4', 'T3', 'M1', 'C2', 'T1', 'T2', 'M3', 'Q2'}
EXCLUDED_GO = {9, 27, 35, 36, 37}

STRICT_SYSTEM_PROMPT = """You are a senior software engineer conducting a thorough code review of a pull request.
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


def process_pr(pr_id):
    from prnote.llm import generate_completion
    from prnote.note import format_kg_context, get_diff_from_evidence
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from evaluate_reviews import evaluate_single_review

    review_path = OUT_DIR / f"pr{pr_id}_review.md"
    eval_path = OUT_DIR / f"pr{pr_id}_eval.json"

    # Skip if already done
    if eval_path.exists():
        d = json.loads(eval_path.read_text())
        kgrel = sum(c['score'] for c in d.get('criteria_scores', []) if c['criterion_id'] in KG_CRITERIA)
        print(f"  PR{pr_id}: cached (kgrel={kgrel})")
        return pr_id, d.get('total_score', 0), kgrel

    # Load Joern evidence (falls back to base evidence if Joern pack missing)
    ev_file = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    if not ev_file.exists():
        ev_file = REPO_ROOT / "data" / "luca_prs_v2" / f"pr{pr_id}_evidence.json"

    evidence = json.loads(ev_file.read_text())
    diff = get_diff_from_evidence(evidence, max_chars=50000)
    pr_title = evidence.get("pr", {}).get("title", f"PR {pr_id}")
    pr_body = evidence.get("pr", {}).get("body", "")[:500]
    context = format_kg_context(evidence)

    user_prompt = f"""## Pull Request: {pr_title}

## Description
{pr_body}

## Diff
```
{diff}
```

{context}

Generate your review note following the required format. You MUST cover all 9 mandatory points. Reference specific callers, test files, and function signatures from the structural context above."""

    print(f"  PR{pr_id}: generating...")
    review = generate_completion(prompt=user_prompt, system=STRICT_SYSTEM_PROMPT,
                                 model=GENERATOR_MODEL, temperature=0.0)
    review_path.write_text(review)

    print(f"  PR{pr_id}: evaluating...")
    ev = evaluate_single_review(review_path, pr_id, "joern_kg_strict", JUDGE_PANEL)
    result = asdict(ev)
    eval_path.write_text(json.dumps(result, indent=2))

    kgrel = sum(c['score'] for c in result.get('criteria_scores', []) if c['criterion_id'] in KG_CRITERIA)
    total = result.get('total_score', 0)
    print(f"  PR{pr_id}: total={total}/25 kgrel={kgrel}/9")
    return pr_id, total, kgrel


def main():
    pr_config = json.loads((SCRIPT_DIR / "pr_config.json").read_text())
    all_prs = [int(k) for k in pr_config if int(k) not in EXCLUDED_GO]

    print("=" * 70)
    print(f"EXP_B_FULL35: Strict prompt, all {len(all_prs)} non-Go PRs in parallel")
    print(f"Generator: {GENERATOR_MODEL} | Judges: {JUDGE_PANEL}")
    print("=" * 70)

    results = {}
    with ThreadPoolExecutor(max_workers=len(all_prs)) as ex:
        futures = {ex.submit(process_pr, pr_id): pr_id for pr_id in all_prs}
        for fut in as_completed(futures):
            pr_id, total, kgrel = fut.result()
            results[pr_id] = {'total': total, 'kgrel': kgrel}

    # Load baseline for comparison
    _raw = json.loads((REPO_ROOT / "results" / "checklist_evaluation_llm_multi__v2.json").read_text())
    baseline = {e['pr_id']: e['kg_relevant_score'] for e in _raw["evaluations"] if e['mode'] == 'baseline'}

    prs = sorted(results.keys())
    deltas = np.array([results[p]['kgrel'] - baseline[p] for p in prs])
    n = len(deltas)

    rng = np.random.default_rng(2026)
    boot_means = [rng.choice(deltas, n, replace=True).mean() for _ in range(10000)]
    ci_lo, ci_hi = np.percentile(boot_means, [2.5, 97.5])
    obs_mean = deltas.mean()
    count = sum(1 for _ in range(20000) if (rng.choice([-1,1], n) * deltas).mean() >= obs_mean)
    p_val = count / 20000
    dz = obs_mean / np.std(deltas, ddof=1)
    wins = sum(d > 0 for d in deltas)
    ties = sum(d == 0 for d in deltas)
    losses = sum(d < 0 for d in deltas)

    print(f"\n{'='*70}")
    print("FINAL RESULTS — Joern-KG strict prompt (n=35)")
    print(f"{'='*70}")
    print(f"  KG-rel Δ mean:  {obs_mean:+.3f}")
    print(f"  95% CI:         [{ci_lo:+.3f}, {ci_hi:+.3f}]")
    print(f"  p (perm):       {p_val:.4f}")
    print(f"  Cohen's d_z:    {dz:+.3f}")
    print(f"  W/T/L:          {wins}/{ties}/{losses}")

    out = {
        "experiment": "B_full35",
        "description": "Joern-KG strict prompt, all 35 non-Go PRs",
        "n": n,
        "mean_kgrel_delta": float(obs_mean),
        "ci_95": [float(ci_lo), float(ci_hi)],
        "p_permutation": float(p_val),
        "cohens_dz": float(dz),
        "wins": int(wins), "ties": int(ties), "losses": int(losses),
        "per_pr": {str(p): results[p] for p in prs}
    }
    (OUT_DIR / "results.json").write_text(json.dumps(out, indent=2))
    print(f"\n  Wrote: {OUT_DIR}/results.json")


if __name__ == "__main__":
    main()
