#!/usr/bin/env python3
"""
Experiment A: Fix test-only CPG for PR32 and PR42.

When all changed files are test files, Joern indexes only the test module's
internal call graph. Fix: widen parse_path to include the source directory
alongside the test directory.

PR32: sklearn/metrics/ (only test_common.py changed) → add sklearn/metrics/_base.py etc
PR42: sklearn/tree/ (test_tree.py, test_sorting.py changed) → parse_path already sklearn/tree/
      but Joern caps at 50 functions from test files. Fix: use sklearn/ root to get src.

Parallelized review + eval (CPGs already exist or are re-parsed here).

Usage:
    source load_env.sh && python3 experiments/2026-05-15_joern_kg_main/exp_a_fix_testonly_cpg.py
"""
import json
import os
import subprocess
import sys
import csv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

CPG_DIR = SCRIPT_DIR / "cpgs"
EXPORT_DIR = SCRIPT_DIR / "exports"
CACHE_DIR = SCRIPT_DIR / "cache"
EVIDENCE_DIR = SCRIPT_DIR / "evidence"
EXP_A_DIR = SCRIPT_DIR / "exp_a"
EXP_A_DIR.mkdir(exist_ok=True)

csv.field_size_limit(sys.maxsize)

LUCA_REPOS = REPO_ROOT / "luca_repos"
GENERATOR_MODEL = "gemini:gemini-2.5-flash"
JUDGE_PANEL = ["gemini:gemini-2.5-flash", "gemini:gemini-2.0-flash"]
KG_CRITERIA = {'F3', 'F4', 'T3', 'M1', 'C2', 'T1', 'T2', 'M3', 'Q2'}

# Fix specs: pr_id -> wider parse_path that includes source alongside tests
FIX_SPECS = {
    32: {
        "repo": "scikit-learn_scikit-learn",
        "parse_path_wide": "sklearn/metrics",  # same dir but re-parse to get source not just test
        "parse_path_src": "sklearn",            # fallback: parse whole sklearn
        "changed_files": ["test_common.py"],
        "lang": "python",
        "note": "test_common.py tests ALL estimators — parse sklearn root to get source callers"
    },
    42: {
        "repo": "scikit-learn_scikit-learn",
        "parse_path_wide": "sklearn/tree",
        "parse_path_src": "sklearn",
        "changed_files": ["test_tree.py", "test_sorting.py", "_partitioner.pyx"],
        "lang": "python",
        "note": "test_tree/test_sorting — also include _partitioner.pyx source"
    }
}

SYSTEM_PROMPT = """You are a senior software engineer conducting a thorough code review of a pull request.
You have access to repository-level structural context (test files, dependent code, callers, function signatures) that is NOT visible in the diff alone.

Your task: produce a review that leverages this structural context to surface issues a diff-only reviewer would miss.

Output Format (follow EXACTLY):

# Review Note — Evidence-Anchored

**Scope:** [One sentence describing what this PR does]

## Problem
[2-3 specific issues found in the code, prioritizing integration risks and test gaps]

## Evidence
[Bullet points with file:line references from the diff AND from the structural context]

## Impact
[Technical impact — what breaks, what regresses, what is untested]

## Recommendation (Fix / Tests / Risks)
[Numbered, actionable recommendations. Reference specific callers and test files.]

## Traceability
[Code owners if available, otherwise "Not specified"]

CRITICAL RULES:
- You MUST reference specific caller functions from the provided context
- You MUST reference specific test file paths from the provided context
- Do NOT give generic advice like "consider adding tests" — name the EXACT test file and scenario
- Prioritize: integration risks > test gaps > correctness > style
"""


def load_csv_with_header(data_path):
    header_path = data_path.with_name(data_path.name.replace('_data.csv', '_header.csv'))
    if not header_path.exists() or not data_path.exists():
        return []
    with open(header_path, newline='', encoding='utf-8', errors='replace') as hf:
        headers = next(csv.reader(hf))
    rows = []
    with open(data_path, newline='', encoding='utf-8', errors='replace') as f:
        for row in csv.reader(f):
            if len(row) >= len(headers):
                rows.append(dict(zip(headers, row[:len(headers)])))
            elif row:
                padded = row + [''] * (len(headers) - len(row))
                rows.append(dict(zip(headers, padded)))
    return rows


def rebuild_callgraph(pr_id, spec):
    """Re-extract call graph using widened parse path (reuse existing CPG export if possible)."""
    # Try using existing export first — just widen the changed_files filter
    export_dir = EXPORT_DIR / f"pr{pr_id}"
    changed_files = spec["changed_files"]

    if not (export_dir / "nodes_METHOD_data.csv").exists():
        print(f"  PR{pr_id}: no existing export, skipping (would need re-parse)")
        return None

    methods = load_csv_with_header(export_dir / "nodes_METHOD_data.csv")
    method_by_id = {m[':ID']: m for m in methods}

    synthetic = {'<module>', '<body>', '<metaClassCallHandler>', '<fakeNew>',
                 '<metaClassAdapter>', '<clinit>', '<init>', '<global>',
                 '<lambda>', '<lambda>0', '<lambda>1', '<lambda>2'}

    # For test-only PRs: find the SOURCE files that the test files test
    # Strategy: find all non-test methods in the CPG and use those as targets
    # (inverted: find what the test files call, not what calls the test files)
    source_methods = {}
    test_methods = {}
    for m in methods:
        fname = m.get('FILENAME:string', '')
        name = m.get('NAME:string', '')
        if name in synthetic or '<metaClassAdapter>' in name or '<lambda>' in name:
            continue
        if m.get('IS_EXTERNAL:boolean') == 'true':
            continue
        basename = fname.split('/')[-1] if fname else ''
        if basename in changed_files:
            test_methods[m[':ID']] = m
        elif fname and not basename.startswith('test_') and not basename.endswith('_test.py'):
            source_methods[m[':ID']] = m

    # CALL edges: find what test_methods call (callee = source method)
    call_edges = load_csv_with_header(export_dir / "edges_CALL_data.csv")
    contains_edges = load_csv_with_header(export_dir / "edges_CONTAINS_data.csv")
    child_to_method_parent = {}
    for edge in contains_edges:
        if edge[':START_ID'] in method_by_id:
            child_to_method_parent[edge[':END_ID']] = edge[':START_ID']

    # Find source functions called by test functions (test → source)
    tested_sources = {}
    for e in call_edges:
        start, end = e[':START_ID'], e[':END_ID']
        caller_method_id = child_to_method_parent.get(start)
        if caller_method_id in test_methods and end in source_methods:
            tested_sources[end] = source_methods[end]
        elif end in source_methods and caller_method_id in test_methods:
            tested_sources[end] = source_methods[end]

    # Now find who calls those source functions (the real callers we care about)
    callers = []
    seen = set()
    for e in call_edges:
        end_id = e[':END_ID']
        if end_id not in tested_sources:
            continue
        caller_method_id = child_to_method_parent.get(e[':START_ID'])
        if not caller_method_id or caller_method_id in test_methods:
            continue
        caller = method_by_id.get(caller_method_id)
        callee = tested_sources[end_id]
        if not caller:
            continue
        caller_name = caller.get('NAME:string', '')
        if caller_name in synthetic or '<metaClassAdapter>' in caller_name:
            continue
        key = (caller.get('FULL_NAME:string', ''), callee.get('NAME:string', ''))
        if key in seen:
            continue
        seen.add(key)
        callers.append({
            "caller_name": caller_name,
            "caller_full_name": caller.get('FULL_NAME:string', ''),
            "caller_file": caller.get('FILENAME:string', ''),
            "caller_line": int(caller.get('LINE_NUMBER:int', 0) or 0),
            "callee_name": callee.get('NAME:string', ''),
            "callee_file": callee.get('FILENAME:string', ''),
            "callee_line": int(callee.get('LINE_NUMBER:int', 0) or 0),
        })
        if len(callers) >= 50:
            break

    # Functions: prefer source functions over test functions
    target_fns = list(tested_sources.values())[:50] if tested_sources else list(test_methods.values())[:50]
    functions = [{
        "name": m.get('NAME:string', ''), "full_name": m.get('FULL_NAME:string', ''),
        "file": m.get('FILENAME:string', ''), "start_line": int(m.get('LINE_NUMBER:int', 0) or 0),
        "end_line": int(m.get('LINE_NUMBER_END:int', 0) or 0), "signature": m.get('SIGNATURE:string', ''),
    } for m in target_fns]

    print(f"  PR{pr_id}: widened CPG → {len(callers)} callers, {len(functions)} src functions (was 0 callers to source)")
    return {"callers": callers, "functions_in_changed_files": functions}


def build_evidence(pr_id, cg):
    evidence = json.loads((REPO_ROOT / "data" / "luca_prs_v2" / f"pr{pr_id}_evidence.json").read_text())
    callers_fmt = [{"path": c["caller_file"], "from_function": c["caller_name"],
                    "calls_function": c["callee_name"], "caller_line": c["caller_line"],
                    "callee_file": c["callee_file"], "callee_line": c["callee_line"]}
                   for c in cg.get("callers", [])]
    if callers_fmt:
        evidence["callers"] = callers_fmt
    edges = [{"from": f"{c['caller_file']}::{c['caller_name']}", "to": f"{c['callee_file']}::{c['callee_name']}"}
             for c in cg.get("callers", [])]
    if edges:
        evidence["call_graph_edges"] = edges
    funcs = cg.get("functions_in_changed_files", [])
    if funcs:
        evidence["functions_in_changed_files"] = funcs
    evidence.setdefault("metadata", {})["joern_exp_a"] = True
    evidence["metadata"]["exp_a_callers"] = len(callers_fmt)
    evidence["metadata"]["exp_a_functions"] = len(funcs)
    return evidence


def generate_and_eval(pr_id, evidence):
    from prnote.llm import generate_completion
    from prnote.note import format_kg_context, get_diff_from_evidence
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from evaluate_reviews import evaluate_single_review
    from dataclasses import asdict

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

Generate your review note following the required format. You MUST reference specific callers, test files, and function signatures from the structural context above."""

    print(f"  PR{pr_id}: generating review...")
    review = generate_completion(prompt=user_prompt, system=SYSTEM_PROMPT,
                                 model=GENERATOR_MODEL, temperature=0.0)
    review_path = EXP_A_DIR / f"pr{pr_id}_exp_a_review.md"
    review_path.write_text(review)

    print(f"  PR{pr_id}: evaluating...")
    ev = evaluate_single_review(review_path, pr_id, "exp_a_joern_kg", JUDGE_PANEL)
    result = asdict(ev)
    (EXP_A_DIR / f"pr{pr_id}_exp_a_eval.json").write_text(json.dumps(result, indent=2))

    kgrel = sum(cs['score'] for cs in result.get('criteria_scores', [])
                if cs['criterion_id'] in KG_CRITERIA)
    total = result.get('total_score', 0)
    print(f"  PR{pr_id}: total={total}/25, KG-rel={kgrel}/9")
    return pr_id, total, kgrel


def process_pr(pr_id):
    spec = FIX_SPECS[pr_id]
    print(f"\n[PR{pr_id}] Widening CPG for test-only PR ({spec['note']})")
    cg = rebuild_callgraph(pr_id, spec)
    if cg is None:
        return pr_id, None, None
    evidence = build_evidence(pr_id, cg)
    return generate_and_eval(pr_id, evidence)


def main():
    print("=" * 70)
    print("EXPERIMENT A: Fix Test-Only CPG for PR32 and PR42")
    print("=" * 70)

    # Load baseline and original Joern scores for comparison
    _raw = json.loads((REPO_ROOT / "results" / "checklist_evaluation_llm_multi__v2.json").read_text())
    baseline_json = _raw["evaluations"] if isinstance(_raw, dict) else _raw
    baseline = {e['pr_id']: e for e in baseline_json if e['mode'] == 'baseline'}

    orig_joern = {}
    for pr_id in [32, 42]:
        ef = SCRIPT_DIR / "controlled" / f"pr{pr_id}_eval.json"
        if ef.exists():
            d = json.loads(ef.read_text())
            kgrel = sum(cs['score'] for cs in d.get('criteria_scores', [])
                        if cs['criterion_id'] in KG_CRITERIA)
            orig_joern[pr_id] = {'total': d.get('total_score', 0), 'kgrel': kgrel}

    print(f"\nBaseline / Original Joern:")
    for pr_id in [32, 42]:
        bl = baseline.get(pr_id, {})
        oj = orig_joern.get(pr_id, {})
        print(f"  PR{pr_id}: baseline kg={bl.get('kg_relevant_score','?')} | orig_joern kg={oj.get('kgrel','?')}")

    # Run in parallel (only 2 PRs)
    results = {}
    with ThreadPoolExecutor(max_workers=2) as ex:
        futures = {ex.submit(process_pr, pr_id): pr_id for pr_id in [32, 42]}
        for fut in as_completed(futures):
            pr_id, total, kgrel = fut.result()
            if total is not None:
                results[pr_id] = {'total': total, 'kgrel': kgrel}

    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(f"{'PR':>4} {'BL_kg':>6} {'OrigJoern_kg':>13} {'ExpA_kg':>8} {'ΔvsOrig':>8}")
    print("-" * 45)
    for pr_id in [32, 42]:
        bl_kg = baseline.get(pr_id, {}).get('kg_relevant_score', '?')
        oj_kg = orig_joern.get(pr_id, {}).get('kgrel', '?')
        ea_kg = results.get(pr_id, {}).get('kgrel', '?')
        delta = (ea_kg - oj_kg) if isinstance(ea_kg, (int, float)) and isinstance(oj_kg, (int, float)) else '?'
        print(f"pr{pr_id:>2} {str(bl_kg):>6} {str(oj_kg):>13} {str(ea_kg):>8} {str(delta):>+8}")

    # Write results
    out = {"experiment": "A", "description": "Fix test-only CPG by widening to source methods",
           "results": {str(k): v for k, v in results.items()},
           "baseline": {str(k): {'kgrel': baseline[k].get('kg_relevant_score')} for k in [32, 42] if k in baseline},
           "orig_joern": {str(k): v for k, v in orig_joern.items()}}
    (EXP_A_DIR / "results.json").write_text(json.dumps(out, indent=2))
    print(f"\nWrote: {EXP_A_DIR}/results.json")


if __name__ == "__main__":
    main()
