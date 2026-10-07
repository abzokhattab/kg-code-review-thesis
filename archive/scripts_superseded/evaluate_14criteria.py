#!/usr/bin/env python3
"""
Run 2: Evaluate PR reviews against the refined 14-criterion rubric.

Changes from Run 1 (25 criteria):
  - Dropped 11 floor/ceiling criteria: F1, R3, M2, M3, C1, C2, P2, S2, Q1, Q2, Q4
    (all modes scored <=8% or >=92%, zero discriminative power)
  - Merged 2 pairs of correlated criteria:
    F3 + M1 → F3* (integration + architecture/design-pattern fit)
    F2 + T2 → F2* (edge cases + error-path testing)
  - Net: 25 - 11 dropped - 2 absorbed + 2 merged = 14 criteria

The LLM judge re-evaluates each review from scratch against the new rubric.
This matters because merged criteria have new, broader descriptions that may
produce different scores than simply OR-ing the originals.
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from prnote.llm import generate_completion


@dataclass
class ReviewCriteria:
    id: str
    category: str
    description: str
    merged_from: Optional[List[str]] = None

@dataclass
class CriterionScore:
    criterion_id: str
    score: int
    evidence: str


CRITERIA_14 = [
    ReviewCriteria("F2*", "Functionality",
                   "Does the review identify edge cases, boundary conditions, or error-path testing needs?",
                   merged_from=["F2", "T2"]),
    ReviewCriteria("F3*", "Functionality",
                   "Does the review check integration with existing components, APIs, or architecture/design-pattern fit?",
                   merged_from=["F3", "M1"]),
    ReviewCriteria("F4", "Functionality",
                   "Does the review warn about potential breaking changes or impact on dependent code?"),
    ReviewCriteria("T1", "Tests",
                   "Does the review ask about or discuss the need for unit/integration tests?"),
    ReviewCriteria("T3", "Tests",
                   "Does the review reference specific test files or suggest which tests should be added/updated?"),
    ReviewCriteria("R1", "Readability",
                   "Does the review comment on code clarity, naming conventions, or function organization?"),
    ReviewCriteria("R2", "Readability",
                   "Does the review identify unnecessary complexity or suggest simplification?"),
    ReviewCriteria("P1", "Performance",
                   "Does the review identify potential performance issues or inefficiencies?"),
    ReviewCriteria("S1", "Security",
                   "Does the review check for proper input validation or sanitization?"),
    ReviewCriteria("S3", "Security",
                   "Does the review assess error handling and failure recovery?"),
    ReviewCriteria("Q3", "Quality",
                   "Does the review distinguish between blocking issues and minor suggestions?"),
    ReviewCriteria("Q5", "Quality",
                   "Does the review explain the reasoning behind suggestions (the 'why')?"),
    ReviewCriteria("C2", "Consistency",
                   "Does the review check if similar problems are solved consistently with existing patterns?"),
    ReviewCriteria("F1", "Functionality",
                   "Does the review verify that the change addresses the stated problem or requirement?"),
]

DEFAULT_MODEL = "openai:gpt-4.1-mini"


def load_review(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def load_pr_context(pr_id: int) -> Dict[str, Any]:
    pr_json_path = f'luca_thesis/data/baseline_pr_stimuli/{pr_id}/original_pr.json'
    if Path(pr_json_path).exists():
        with open(pr_json_path, 'r') as f:
            pr = json.load(f)
        return {
            'title': pr.get('title', ''),
            'body': pr.get('body', '')[:500],
            'pr_id': pr_id
        }
    return {'title': '', 'body': '', 'pr_id': pr_id}


def evaluate_review(review: str, pr_context: Dict[str, Any], model: str) -> List[CriterionScore]:
    criteria_text = "\n".join([
        f"{i+1}. [{c.id}] {c.description}"
        for i, c in enumerate(CRITERIA_14)
    ])

    criteria_ids = ", ".join(c.id for c in CRITERIA_14)

    system_prompt = """You are an expert code review evaluator. Your task is to assess whether a PR review meets specific quality criteria.

For each criterion, you must:
1. Determine if the review addresses that criterion (score: 1) or not (score: 0)
2. Provide a brief quote or explanation as evidence

Be strict but fair:
- Score 1 only if the review CLEARLY addresses the criterion
- Score 0 if the criterion is not addressed or only vaguely mentioned
- Base your judgment on meaning and intent, not just keywords"""

    user_prompt = f"""## PR Being Reviewed
Title: {pr_context.get('title', 'Unknown')}
Description: {pr_context.get('body', 'N/A')[:400]}

## Review to Evaluate
{review[:4000]}

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
- Evidence must be VERY SHORT (max 15 words) — a brief phrase, not a full sentence"""

    max_retries = 3
    for attempt in range(max_retries):
      try:
        response = generate_completion(
            prompt=user_prompt,
            system=system_prompt,
            model=model,
            temperature=0.1
        )

        resp_clean = response.strip()
        if resp_clean.startswith('```'):
            resp_clean = re.sub(r'^```\w*\n?', '', resp_clean)
            resp_clean = re.sub(r'\n?```\s*$', '', resp_clean)

        json_match = re.search(r'\{[\s\S]*\}', resp_clean)
        if not json_match:
            raise ValueError("No JSON found in response")

        raw_json = json_match.group()
        try:
            result = json.loads(raw_json)
        except json.JSONDecodeError:
            raw_json = re.sub(r',\s*}', '}', raw_json)
            raw_json = re.sub(r',\s*]', ']', raw_json)
            result = json.loads(raw_json)
        scores = []
        scored_ids = set()

        for item in result.get('scores', []):
            cid = item['id']
            scored_ids.add(cid)
            scores.append(CriterionScore(
                criterion_id=cid,
                score=int(item['score']),
                evidence=item.get('evidence', '')
            ))

        for c in CRITERIA_14:
            if c.id not in scored_ids:
                scores.append(CriterionScore(c.id, 0, "Not scored by LLM"))

        return scores

      except Exception as e:
        is_rate_limit = "429" in str(e) or "rate" in str(e).lower() or "quota" in str(e).lower()
        if is_rate_limit and attempt < max_retries - 1:
            wait = 15 * (attempt + 1)
            print(f"    RATE LIMITED, waiting {wait}s...", end=" ", flush=True)
            time.sleep(wait)
            continue
        if attempt < max_retries - 1:
            print(f"    retry...", end=" ", flush=True)
            continue
        print(f"    ERROR: {e}")
        return [CriterionScore(c.id, 0, f"Evaluation failed: {e}") for c in CRITERIA_14]


def run_evaluation(model: str = DEFAULT_MODEL,
                   outputs_dir: str = "outputs/luca_prs_fixed",
                   results_dir: str = "results/run2_14criteria",
                   delay: float = 0):
    outputs_path = Path(outputs_dir)
    results_path = Path(results_dir)
    results_path.mkdir(parents=True, exist_ok=True)

    print(f"{'='*70}")
    print(f"Run 2: 14-criterion evaluation")
    print(f"Model: {model}")
    print(f"Criteria: {len(CRITERIA_14)}")
    print(f"Output: {results_path}")
    print(f"{'='*70}\n")

    review_files = sorted(outputs_path.glob('pr*_*.md'))
    print(f"Found {len(review_files)} review files\n")

    evaluations = []

    for i, review_file in enumerate(review_files):
        match = re.match(r'pr(\d+)_(\w+)\.md', review_file.name)
        if not match:
            continue

        pr_id = int(match.group(1))
        mode = match.group(2)

        print(f"[{i+1}/{len(review_files)}] PR #{pr_id} - {mode}...", end=" ", flush=True)

        if delay > 0 and i > 0:
            time.sleep(delay)

        review = load_review(str(review_file))
        pr_context = load_pr_context(pr_id)
        scores = evaluate_review(review, pr_context, model)

        total = sum(s.score for s in scores)
        pct = round(total / len(CRITERIA_14) * 100, 1)
        print(f"{total}/{len(CRITERIA_14)} ({pct}%)")

        evaluations.append({
            'pr_id': pr_id,
            'mode': mode,
            'total_score': total,
            'max_score': len(CRITERIA_14),
            'percentage': pct,
            'criteria_scores': [asdict(s) for s in scores],
            'timestamp': datetime.now().isoformat()
        })

    # Save raw results
    output = {
        'metadata': {
            'run': 'run2_14criteria',
            'model': model,
            'timestamp': datetime.now().isoformat(),
            'criteria_count': len(CRITERIA_14),
            'description': '14-criterion refined rubric (dropped floor/ceiling, merged correlated)'
        },
        'criteria_definitions': [
            {
                'id': c.id,
                'category': c.category,
                'description': c.description,
                **({"merged_from": c.merged_from} if c.merged_from else {})
            }
            for c in CRITERIA_14
        ],
        'evaluations': evaluations
    }

    json_path = results_path / 'evaluation_14criteria.json'
    with open(json_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n✓ Results saved to {json_path}")

    # Generate analysis
    analyze_results(evaluations, results_path)

    return output


def analyze_results(evaluations: List[Dict], results_path: Path):
    """Compute spread, KG-delta, and generate report."""
    modes = ['baseline', 'rag', 'kg', 'hybrid']
    criteria_ids = [c.id for c in CRITERIA_14]

    # Per-criterion per-mode pass rates
    crit_rates = {cid: {m: [] for m in modes} for cid in criteria_ids}
    mode_totals = {m: [] for m in modes}

    for ev in evaluations:
        mode = ev['mode']
        if mode not in modes:
            continue
        mode_totals[mode].append(ev['percentage'])
        for cs in ev['criteria_scores']:
            if cs['criterion_id'] in crit_rates:
                crit_rates[cs['criterion_id']][mode].append(cs['score'])

    # Summary by mode
    print(f"\n{'='*70}")
    print("SUMMARY BY MODE")
    print(f"{'='*70}")
    for m in modes:
        scores = mode_totals[m]
        avg = sum(scores) / len(scores) if scores else 0
        print(f"  {m:>10}: {avg:.1f}%  (n={len(scores)})")

    # Per-criterion spread + KG delta
    print(f"\n{'='*70}")
    print("PER-CRITERION: SPREAD + KG DELTA (sorted by spread)")
    print(f"{'='*70}")
    print(f"{'Crit':>6} | {'BL':>6} | {'RAG':>6} | {'KG':>6} | {'HY':>6} | {'Spread':>6} | {'KG-BL':>6}")
    print("-" * 60)

    crit_analysis = []
    for cid in criteria_ids:
        rates = {}
        for m in modes:
            vals = crit_rates[cid][m]
            rates[m] = (sum(vals) / len(vals) * 100) if vals else 0
        spread = max(rates.values()) - min(rates.values())
        kg_delta = rates['kg'] - rates['baseline']
        crit_analysis.append({
            'id': cid,
            'rates': rates,
            'spread': spread,
            'kg_delta': kg_delta
        })

    crit_analysis.sort(key=lambda x: -x['spread'])

    for ca in crit_analysis:
        r = ca['rates']
        print(f"  {ca['id']:>4} | {r['baseline']:>5.1f}% | {r['rag']:>5.1f}% | {r['kg']:>5.1f}% | {r['hybrid']:>5.1f}% | {ca['spread']:>5.1f}% | {ca['kg_delta']:>+5.1f}%")

    total_spread = sum(c['spread'] for c in crit_analysis)
    top5_spread = sum(c['spread'] for c in crit_analysis[:5])
    print(f"\n  Total spread: {total_spread:.1f}%")
    print(f"  Top 5 spread: {top5_spread:.1f}% ({top5_spread/total_spread*100:.0f}%)")
    print(f"\n  Top 5 by spread:    {[c['id'] for c in crit_analysis[:5]]}")

    # KG delta ranking
    by_kg = sorted(crit_analysis, key=lambda x: -x['kg_delta'])
    print(f"  Top 5 by KG delta:  {[c['id'] for c in by_kg[:5]]}")

    overlap = set(c['id'] for c in crit_analysis[:5]) & set(c['id'] for c in by_kg[:5])
    print(f"  Overlap:            {overlap} ({len(overlap)}/5)")

    # Save analysis JSON
    analysis_path = results_path / 'analysis_14criteria.json'
    with open(analysis_path, 'w') as f:
        json.dump({
            'mode_averages': {m: round(sum(mode_totals[m])/len(mode_totals[m]), 1) for m in modes},
            'criteria_analysis': crit_analysis,
            'top5_by_spread': [c['id'] for c in crit_analysis[:5]],
            'top5_by_kg_delta': [c['id'] for c in by_kg[:5]],
            'overlap': list(overlap)
        }, f, indent=2)
    print(f"\n✓ Analysis saved to {analysis_path}")

    # Generate markdown report
    report = generate_report(evaluations, crit_analysis, mode_totals)
    report_path = results_path / 'REPORT.md'
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"✓ Report saved to {report_path}")


def generate_report(evaluations, crit_analysis, mode_totals, model: str = DEFAULT_MODEL) -> str:
    modes = ['baseline', 'rag', 'kg', 'hybrid']
    r = f"""# Run 2: 14-Criterion Evaluation Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Model:** {model} (judge)
**Criteria:** 14 (refined from 25)

---

## Mode Averages

| Mode | Avg Score | n |
|------|-----------|---|
"""
    for m in modes:
        scores = mode_totals[m]
        avg = sum(scores) / len(scores) if scores else 0
        r += f"| {m} | {avg:.1f}% | {len(scores)} |\n"

    r += f"""
---

## Per-Criterion Analysis (sorted by spread)

| Rank | Criterion | Baseline | RAG | KG | Hybrid | Spread | KG-BL |
|------|-----------|----------|-----|-----|--------|--------|-------|
"""
    for i, ca in enumerate(crit_analysis):
        rt = ca['rates']
        r += f"| {i+1} | {ca['id']} | {rt['baseline']:.0f}% | {rt['rag']:.0f}% | {rt['kg']:.0f}% | {rt['hybrid']:.0f}% | {ca['spread']:.0f}% | {ca['kg_delta']:+.0f}% |\n"

    total_spread = sum(c['spread'] for c in crit_analysis)
    top5_spread = sum(c['spread'] for c in crit_analysis[:5])
    top5_ids = [c['id'] for c in crit_analysis[:5]]
    by_kg = sorted(crit_analysis, key=lambda x: -x['kg_delta'])
    top5_kg = [c['id'] for c in by_kg[:5]]
    overlap = set(top5_ids) & set(top5_kg)

    r += f"""
---

## Top 5 Selection

- **By spread:** {top5_ids} (captures {top5_spread/total_spread*100:.0f}% of total spread)
- **By KG delta:** {top5_kg}
- **Overlap:** {list(overlap)} ({len(overlap)}/5)

---

## Comparison with Run 1 (25 criteria)

*Run 1 top 5 by spread:* F3*, R1, T1, T3, Q5
*Run 2 top 5 by spread:* {top5_ids}

Agreement: TBD after comparison

---

## Per-PR Results

"""
    pr_ids = sorted(set(e['pr_id'] for e in evaluations))
    for pid in pr_ids:
        r += f"### PR #{pid}\n\n| Mode | Score | % |\n|------|-------|---|\n"
        for m in modes:
            ev = [e for e in evaluations if e['pr_id'] == pid and e['mode'] == m]
            if ev:
                e = ev[0]
                r += f"| {m} | {e['total_score']}/{e['max_score']} | {e['percentage']}% |\n"
        r += "\n"

    return r


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run 2: 14-criterion evaluation')
    parser.add_argument('--model', type=str, default=DEFAULT_MODEL,
                        help=f'Judge model (default: {DEFAULT_MODEL})')
    parser.add_argument('--outputs-dir', type=str, default='outputs/luca_prs_fixed')
    parser.add_argument('--results-dir', type=str, default='results/run2_14criteria')
    parser.add_argument('--delay', type=float, default=0,
                        help='Delay in seconds between API calls (for rate-limited APIs)')
    args = parser.parse_args()

    run_evaluation(model=args.model,
                   outputs_dir=args.outputs_dir,
                   results_dir=args.results_dir,
                   delay=args.delay)
