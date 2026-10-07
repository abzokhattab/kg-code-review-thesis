#!/usr/bin/env python3
"""
run_experiment.py — Full Joern-KG experiment pipeline.

Runs all steps with checkpointing: CPG generation, call graph extraction,
evidence building, review generation, and evaluation.

Each step checks for cached outputs and skips if already done.
Progress is logged to progress.json for recovery.
"""
import csv
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Directories
CPG_DIR = SCRIPT_DIR / "cpgs"
EXPORT_DIR = SCRIPT_DIR / "exports"
EVIDENCE_DIR = SCRIPT_DIR / "evidence"
REVIEWS_DIR = SCRIPT_DIR / "reviews"
CACHE_DIR = SCRIPT_DIR / "cache"
PROGRESS_FILE = SCRIPT_DIR / "progress.json"

# Source repos
LUCA_REPOS = REPO_ROOT / "luca_repos"

# Selected PRs (top 10 by grep-KG improvement)
TARGET_PRS = [9, 31, 22, 40, 41, 47, 15, 33, 37, 38]

# PR metadata (repo, language, parse paths)
PR_META = {
    9:  {"repo": "grafana_grafana", "lang": "go",
         "parse_paths": ["pkg/"]},
    31: {"repo": "scikit-learn_scikit-learn", "lang": "python",
         "parse_paths": ["sklearn/linear_model/"]},
    22: {"repo": "apache_kafka", "lang": "java",
         "parse_paths": ["tools/src/"]},
    40: {"repo": "apache_kafka", "lang": "java",
         "parse_paths": ["clients/src/"]},
    41: {"repo": "apache_kafka", "lang": "java",
         "parse_paths": ["streams/src/"]},
    47: {"repo": "jenkinsci_jenkins", "lang": "java",
         "parse_paths": ["core/src/", "test/src/"]},
    15: {"repo": "grafana_grafana", "lang": "typescript",
         "parse_paths": ["public/app/"]},
    33: {"repo": "jenkinsci_jenkins", "lang": "java",
         "parse_paths": ["core/src/", "test/src/"]},
    37: {"repo": "grafana_grafana", "lang": "go",
         "parse_paths": ["pkg/"]},
    38: {"repo": "grafana_grafana", "lang": "typescript",
         "parse_paths": ["public/app/"]},
}

# Models
GENERATOR_MODEL = "gemini:gemini-2.5-flash"
JUDGE_PANEL = ["gemini:gemini-2.5-flash", "gemini:gemini-2.0-flash"]

# Evaluation criteria (KG-refined subscale)
KG_REFINED = {'F3', 'F4', 'T3', 'M1', 'C2'}

csv.field_size_limit(sys.maxsize)


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"steps_completed": {}, "errors": [], "started_at": datetime.now(timezone.utc).isoformat()}


def save_progress(progress: dict):
    progress["last_updated"] = datetime.now(timezone.utc).isoformat()
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


def step_done(progress: dict, step: str) -> bool:
    return progress["steps_completed"].get(step, False)


def mark_done(progress: dict, step: str):
    progress["steps_completed"][step] = datetime.now(timezone.utc).isoformat()
    save_progress(progress)


def record_error(progress: dict, step: str, error: str):
    progress["errors"].append({"step": step, "error": error, "time": datetime.now(timezone.utc).isoformat()})
    save_progress(progress)


# ============================================================
# STEP 1: Generate CPGs
# ============================================================

def generate_cpg(pr_id: int, progress: dict) -> bool:
    """Generate Joern CPG for a PR's relevant source paths."""
    step = f"cpg_pr{pr_id}"
    if step_done(progress, step):
        log(f"  PR{pr_id}: CPG already generated, skipping")
        return True

    meta = PR_META[pr_id]
    repo_dir = LUCA_REPOS / meta["repo"]
    cpg_file = CPG_DIR / f"pr{pr_id}.bin"

    # Build full paths
    parse_paths = [str(repo_dir / p) for p in meta["parse_paths"]]

    # Check paths exist
    for p in parse_paths:
        if not Path(p).exists():
            error = f"Path not found: {p}"
            log(f"  PR{pr_id}: ERROR - {error}")
            record_error(progress, step, error)
            return False

    cmd = ["joern-parse"] + parse_paths + ["--output", str(cpg_file)]
    log(f"  PR{pr_id}: generating CPG from {meta['parse_paths']}...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0 or not cpg_file.exists():
            error = f"joern-parse failed: {result.stderr[-500:]}"
            log(f"  PR{pr_id}: ERROR - {error}")
            record_error(progress, step, error)
            return False
        size_mb = cpg_file.stat().st_size / (1024 * 1024)
        log(f"  PR{pr_id}: CPG generated ({size_mb:.1f} MB)")
        mark_done(progress, step)
        return True
    except subprocess.TimeoutExpired:
        error = "joern-parse timed out (600s)"
        log(f"  PR{pr_id}: ERROR - {error}")
        record_error(progress, step, error)
        return False
    except Exception as e:
        error = str(e)
        log(f"  PR{pr_id}: ERROR - {error}")
        record_error(progress, step, error)
        return False


# ============================================================
# STEP 2: Export CPGs to CSV
# ============================================================

def export_cpg(pr_id: int, progress: dict) -> bool:
    """Export CPG to neo4jcsv for Python parsing."""
    step = f"export_pr{pr_id}"
    if step_done(progress, step):
        log(f"  PR{pr_id}: export already done, skipping")
        return True

    cpg_file = CPG_DIR / f"pr{pr_id}.bin"
    export_dir = EXPORT_DIR / f"pr{pr_id}"

    if not cpg_file.exists():
        error = "CPG file not found"
        log(f"  PR{pr_id}: ERROR - {error}")
        record_error(progress, step, error)
        return False

    # Clean old export
    if export_dir.exists():
        subprocess.run(["rm", "-rf", str(export_dir)])

    cmd = ["joern-export", "--repr", "all", "--format", "neo4jcsv",
           "--out", str(export_dir), str(cpg_file)]
    log(f"  PR{pr_id}: exporting CPG to CSV...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        # Check export produced files
        method_file = export_dir / "nodes_METHOD_data.csv"
        if not method_file.exists():
            error = f"Export produced no METHOD nodes: {result.stderr[-300:]}"
            log(f"  PR{pr_id}: ERROR - {error}")
            record_error(progress, step, error)
            return False
        log(f"  PR{pr_id}: export done")
        mark_done(progress, step)
        return True
    except subprocess.TimeoutExpired:
        error = "joern-export timed out (600s)"
        log(f"  PR{pr_id}: ERROR - {error}")
        record_error(progress, step, error)
        return False
    except Exception as e:
        error = str(e)
        log(f"  PR{pr_id}: ERROR - {error}")
        record_error(progress, step, error)
        return False


# ============================================================
# STEP 3: Extract call graph from CSV export
# ============================================================

def load_csv_with_header(data_path: Path) -> list[dict]:
    """Load neo4jcsv data file with companion header file."""
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


def extract_call_graph(pr_id: int, progress: dict) -> bool:
    """Parse CPG export to extract call graph for changed functions."""
    step = f"callgraph_pr{pr_id}"
    if step_done(progress, step):
        log(f"  PR{pr_id}: call graph already extracted, skipping")
        return True

    export_dir = EXPORT_DIR / f"pr{pr_id}"
    if not export_dir.exists():
        error = "Export directory not found"
        log(f"  PR{pr_id}: ERROR - {error}")
        record_error(progress, step, error)
        return False

    # Load the original evidence to find changed files
    orig_evidence = json.loads((REPO_ROOT / "data" / "luca_prs_v2" / f"pr{pr_id}_evidence.json").read_text())
    changed_files = [f['path'].split('/')[-1] for f in orig_evidence.get('changed_files', [])
                     if f.get('language') not in ('', 'unknown', 'xml', 'gradle', 'rst', 'markdown', 'json', 'yaml')]

    if not changed_files:
        log(f"  PR{pr_id}: no code files changed, writing empty call graph")
        output = {"callers": [], "functions_in_changed_files": []}
        (CACHE_DIR / f"pr{pr_id}_callgraph.json").write_text(json.dumps(output, indent=2))
        mark_done(progress, step)
        return True

    log(f"  PR{pr_id}: extracting call graph for {changed_files}...")

    # Load METHOD nodes
    methods = load_csv_with_header(export_dir / "nodes_METHOD_data.csv")
    method_by_id = {m[':ID']: m for m in methods}

    # Synthetic node names to filter
    synthetic = {'<module>', '<body>', '<metaClassCallHandler>', '<fakeNew>',
                 '<metaClassAdapter>', '<clinit>', '<init>', '<global>',
                 '<metaClassAdapter>'}

    # Find target methods in changed files
    target_methods = {}
    for m in methods:
        fname = m.get('FILENAME:string', '')
        name = m.get('NAME:string', '')
        basename = fname.split('/')[-1] if fname else ''
        if (basename in changed_files
            and name not in synthetic
            and '<metaClassAdapter>' not in name
            and m.get('IS_EXTERNAL:boolean') != 'true'):
            target_methods[m[':ID']] = m

    log(f"  PR{pr_id}: found {len(target_methods)} target methods in changed files")

    if not target_methods:
        # Try partial filename matching
        for m in methods:
            fname = m.get('FILENAME:string', '')
            name = m.get('NAME:string', '')
            if (any(cf.replace('.java', '').replace('.py', '').replace('.go', '').replace('.ts', '').replace('.tsx', '') in fname
                    for cf in changed_files)
                and name not in synthetic
                and '<metaClassAdapter>' not in name
                and m.get('IS_EXTERNAL:boolean') != 'true'):
                target_methods[m[':ID']] = m
        if target_methods:
            log(f"  PR{pr_id}: found {len(target_methods)} target methods (partial match)")

    # Load CALL edges
    call_edges = load_csv_with_header(export_dir / "edges_CALL_data.csv")
    calls_to_targets = [(e[':START_ID'], e[':END_ID']) for e in call_edges if e[':END_ID'] in target_methods]

    # Load CONTAINS edges for parent resolution
    contains_edges = load_csv_with_header(export_dir / "edges_CONTAINS_data.csv")
    child_to_method_parent = {}
    for edge in contains_edges:
        parent_id = edge[':START_ID']
        child_id = edge[':END_ID']
        if parent_id in method_by_id:
            child_to_method_parent[child_id] = parent_id

    # Resolve callers
    callers = []
    seen = set()
    for call_node_id, target_method_id in calls_to_targets:
        caller_method_id = child_to_method_parent.get(call_node_id)
        if not caller_method_id or caller_method_id == target_method_id:
            continue
        caller = method_by_id[caller_method_id]
        callee = target_methods[target_method_id]

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

    # Function definitions
    functions = []
    for mid, m in target_methods.items():
        functions.append({
            "name": m.get('NAME:string', ''),
            "full_name": m.get('FULL_NAME:string', ''),
            "file": m.get('FILENAME:string', ''),
            "start_line": int(m.get('LINE_NUMBER:int', 0) or 0),
            "end_line": int(m.get('LINE_NUMBER_END:int', 0) or 0),
            "signature": m.get('SIGNATURE:string', ''),
        })

    output = {"callers": callers, "functions_in_changed_files": functions}
    (CACHE_DIR / f"pr{pr_id}_callgraph.json").write_text(json.dumps(output, indent=2))

    log(f"  PR{pr_id}: {len(callers)} callers, {len(functions)} functions extracted")
    mark_done(progress, step)
    return True


# ============================================================
# STEP 4: Build enriched evidence packs
# ============================================================

def build_evidence(pr_id: int, progress: dict) -> bool:
    """Merge Joern call graph into grep-based evidence pack."""
    step = f"evidence_pr{pr_id}"
    if step_done(progress, step):
        log(f"  PR{pr_id}: evidence already built, skipping")
        return True

    cg_file = CACHE_DIR / f"pr{pr_id}_callgraph.json"
    if not cg_file.exists():
        error = "Call graph file not found"
        log(f"  PR{pr_id}: ERROR - {error}")
        record_error(progress, step, error)
        return False

    # Load original evidence
    orig_path = REPO_ROOT / "data" / "luca_prs_v2" / f"pr{pr_id}_evidence.json"
    evidence = json.loads(orig_path.read_text())

    # Load Joern call graph
    joern_data = json.loads(cg_file.read_text())

    # Convert callers to format_kg_context expected format
    raw_callers = joern_data.get("callers", [])
    callers = []
    for c in raw_callers:
        callers.append({
            "path": c.get("caller_file", ""),
            "from_function": c.get("caller_name", ""),
            "calls_function": c.get("callee_name", ""),
            "caller_line": c.get("caller_line", 0),
            "callee_file": c.get("callee_file", ""),
            "callee_line": c.get("callee_line", 0),
        })
    if callers:
        evidence["callers"] = callers

    # Call graph edges in {from, to} format
    edges = []
    for c in raw_callers:
        caller_label = f"{c.get('caller_file', '')}::{c.get('caller_name', '')}"
        callee_label = f"{c.get('callee_file', '')}::{c.get('callee_name', '')}"
        edges.append({"from": caller_label, "to": callee_label})
    if edges:
        evidence["call_graph_edges"] = edges

    # Function definitions
    funcs = joern_data.get("functions_in_changed_files", [])
    if funcs:
        evidence["functions_in_changed_files"] = funcs

    # Metadata
    evidence.setdefault("metadata", {})
    evidence["metadata"]["joern_enriched"] = True
    evidence["metadata"]["joern_callers_count"] = len(callers)
    evidence["metadata"]["joern_functions_count"] = len(funcs)

    out_file = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    out_file.write_text(json.dumps(evidence, indent=2))

    log(f"  PR{pr_id}: evidence built ({len(callers)} callers, {len(funcs)} functions)")
    mark_done(progress, step)
    return True


# ============================================================
# STEP 5: Generate reviews
# ============================================================

def generate_review(pr_id: int, progress: dict) -> bool:
    """Generate Joern-KG review using LLM."""
    step = f"review_pr{pr_id}"
    if step_done(progress, step):
        log(f"  PR{pr_id}: review already generated, skipping")
        return True

    from prnote.llm import generate_completion
    from prnote.note import format_kg_context, get_diff_from_evidence

    ev_file = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    if not ev_file.exists():
        error = "Evidence file not found"
        log(f"  PR{pr_id}: ERROR - {error}")
        record_error(progress, step, error)
        return False

    evidence = json.loads(ev_file.read_text())
    diff = get_diff_from_evidence(evidence, max_chars=50000)
    pr_title = evidence.get("pr", {}).get("title", f"PR {pr_id}")
    pr_body = evidence.get("pr", {}).get("body", "")[:500]
    context = format_kg_context(evidence)

    system_prompt = """You are a senior software engineer conducting a thorough code review of a pull request.
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

    user_prompt = f"""## Pull Request: {pr_title}

## Description
{pr_body}

## Diff
```
{diff}
```

{context}

Generate your review note following the required format. You MUST reference specific callers, test files, and function signatures from the structural context above."""

    log(f"  PR{pr_id}: generating review ({GENERATOR_MODEL})...")

    try:
        review = generate_completion(
            prompt=user_prompt,
            system=system_prompt,
            model=GENERATOR_MODEL,
            temperature=0.0,
        )
        out_file = REVIEWS_DIR / f"pr{pr_id}_joern_kg.md"
        out_file.write_text(review)
        log(f"  PR{pr_id}: review generated ({len(review)} chars)")
        mark_done(progress, step)
        return True
    except Exception as e:
        error = f"Generation failed: {e}"
        log(f"  PR{pr_id}: ERROR - {error}")
        record_error(progress, step, error)
        return False


# ============================================================
# STEP 6: Evaluate reviews
# ============================================================

def evaluate_review(pr_id: int, progress: dict) -> bool:
    """Evaluate Joern-KG review with judge panel."""
    step = f"eval_pr{pr_id}"
    if step_done(progress, step):
        log(f"  PR{pr_id}: evaluation already done, skipping")
        return True

    review_file = REVIEWS_DIR / f"pr{pr_id}_joern_kg.md"
    if not review_file.exists():
        error = "Review file not found"
        log(f"  PR{pr_id}: ERROR - {error}")
        record_error(progress, step, error)
        return False

    # Import evaluate_single_review from the evaluation script
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from evaluate_reviews import evaluate_single_review

    log(f"  PR{pr_id}: evaluating with {JUDGE_PANEL}...")

    try:
        from dataclasses import asdict
        ev = evaluate_single_review(review_file, pr_id, "joern_kg", JUDGE_PANEL)
        result = asdict(ev)

        # Cache result
        cache_file = CACHE_DIR / f"pr{pr_id}_eval.json"
        cache_file.write_text(json.dumps(result, indent=2))

        total = result.get('total_score', 0)
        kg_rel = result.get('kg_relevant_score', 0)
        log(f"  PR{pr_id}: total={total}/25, KG-rel={kg_rel}/9")
        mark_done(progress, step)
        return True
    except Exception as e:
        error = f"Evaluation failed: {e}"
        log(f"  PR{pr_id}: ERROR - {error}")
        record_error(progress, step, error)
        return False


# ============================================================
# STEP 7: Compile results
# ============================================================

def compile_results(progress: dict):
    """Compile all evaluation results into a single file and comparison."""
    log("\nCompiling results...")

    # Load all evaluation results
    evaluations = []
    for pr_id in TARGET_PRS:
        cache_file = CACHE_DIR / f"pr{pr_id}_eval.json"
        if cache_file.exists():
            ev = json.loads(cache_file.read_text())
            evaluations.append(ev)

    # Save combined results
    combined = {"evaluations": evaluations, "panel": JUDGE_PANEL, "generator": GENERATOR_MODEL}
    (SCRIPT_DIR / "evaluation_results.json").write_text(json.dumps(combined, indent=2))

    # Load existing baseline/grep-KG scores for comparison
    existing_file = REPO_ROOT / "results" / "checklist_evaluation_llm_multi__v2.json"
    existing = json.loads(existing_file.read_text())

    existing_scores = {}
    for ev in existing["evaluations"]:
        pr_id = ev["pr_id"]
        mode = ev["mode"]
        if pr_id in TARGET_PRS and mode in ("baseline", "kg"):
            kg_rel = sum(1 for cs in ev["criteria_scores"]
                         if cs["criterion_id"] in KG_REFINED and cs["score"] == 1)
            existing_scores.setdefault(pr_id, {})[mode] = {
                "kg_rel": kg_rel,
                "total": ev["total_score"],
                "criteria": {cs["criterion_id"]: cs["score"] for cs in ev["criteria_scores"]}
            }

    # Print comparison table
    print("\n" + "=" * 80)
    print("JOERN-KG MAIN EXPERIMENT — RESULTS (n=10)")
    print("=" * 80)
    print(f"\nGenerator: {GENERATOR_MODEL}")
    print(f"Judges: {', '.join(JUDGE_PANEL)}")
    print()
    print(f"| {'PR':>3} | {'Mode':<12} | {'KG-rel':>7} | {'Total':>6} | {'F3':>2} | {'F4':>2} | {'T3':>2} | {'M1':>2} | {'C2':>2} |")
    print(f"|{'---':>4}|{'---':<13}|{'---':>8}|{'---':>7}|{'--':>3}|{'--':>3}|{'--':>3}|{'--':>3}|{'--':>3}|")

    joern_totals = []
    grep_totals = []
    baseline_totals = []
    joern_kg_rels = []
    grep_kg_rels = []
    baseline_kg_rels = []

    for pr_id in TARGET_PRS:
        ex = existing_scores.get(pr_id, {})
        bl = ex.get("baseline", {})
        gk = ex.get("kg", {})

        # Baseline
        bl_kg = bl.get("kg_rel", "?")
        bl_tot = bl.get("total", "?")
        bl_c = bl.get("criteria", {})
        print(f"| {pr_id:>3} | {'baseline':<12} | {bl_kg:>7} | {bl_tot:>6} | {bl_c.get('F3','?'):>2} | {bl_c.get('F4','?'):>2} | {bl_c.get('T3','?'):>2} | {bl_c.get('M1','?'):>2} | {bl_c.get('C2','?'):>2} |")

        # grep-KG
        gk_kg = gk.get("kg_rel", "?")
        gk_tot = gk.get("total", "?")
        gk_c = gk.get("criteria", {})
        print(f"| {pr_id:>3} | {'grep-KG':<12} | {gk_kg:>7} | {gk_tot:>6} | {gk_c.get('F3','?'):>2} | {gk_c.get('F4','?'):>2} | {gk_c.get('T3','?'):>2} | {gk_c.get('M1','?'):>2} | {gk_c.get('C2','?'):>2} |")

        # Joern-KG
        cache_file = CACHE_DIR / f"pr{pr_id}_eval.json"
        if cache_file.exists():
            ev = json.loads(cache_file.read_text())
            jk_c = {cs["criterion_id"]: cs["score"] for cs in ev.get("criteria_scores", [])}
            jk_kg = sum(jk_c.get(k, 0) for k in KG_REFINED)
            jk_tot = ev.get("total_score", 0)
            print(f"| {pr_id:>3} | {'**joern-KG**':<12} | {jk_kg:>7} | {jk_tot:>6} | {jk_c.get('F3','?'):>2} | {jk_c.get('F4','?'):>2} | {jk_c.get('T3','?'):>2} | {jk_c.get('M1','?'):>2} | {jk_c.get('C2','?'):>2} |")

            joern_totals.append(jk_tot)
            joern_kg_rels.append(jk_kg)
        else:
            print(f"| {pr_id:>3} | {'joern-KG':<12} | {'?':>7} | {'?':>6} | {'?':>2} | {'?':>2} | {'?':>2} | {'?':>2} | {'?':>2} |")

        if isinstance(bl_tot, int):
            baseline_totals.append(bl_tot)
            baseline_kg_rels.append(bl_kg)
        if isinstance(gk_tot, int):
            grep_totals.append(gk_tot)
            grep_kg_rels.append(gk_kg)

        print(f"|{'---':>4}|{'---':<13}|{'---':>8}|{'---':>7}|{'--':>3}|{'--':>3}|{'--':>3}|{'--':>3}|{'--':>3}|")

    # Summary statistics
    print("\n## Summary Statistics")
    if joern_totals and grep_totals and baseline_totals:
        n = len(joern_totals)
        print(f"\nn = {n} PRs evaluated")
        print(f"\n{'Metric':<20} | {'Baseline':>10} | {'grep-KG':>10} | {'Joern-KG':>10}")
        print(f"{'-'*20}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")
        print(f"{'Mean Total':.<20} | {sum(baseline_totals)/len(baseline_totals):>10.2f} | {sum(grep_totals)/len(grep_totals):>10.2f} | {sum(joern_totals)/n:>10.2f}")
        print(f"{'Mean KG-rel':.<20} | {sum(baseline_kg_rels)/len(baseline_kg_rels):>10.2f} | {sum(grep_kg_rels)/len(grep_kg_rels):>10.2f} | {sum(joern_kg_rels)/n:>10.2f}")
        print(f"{'Δ vs baseline (tot)':.<20} | {'—':>10} | {sum(grep_totals)/len(grep_totals)-sum(baseline_totals)/len(baseline_totals):>+10.2f} | {sum(joern_totals)/n-sum(baseline_totals)/len(baseline_totals):>+10.2f}")
        print(f"{'Δ vs baseline (KG)':.<20} | {'—':>10} | {sum(grep_kg_rels)/len(grep_kg_rels)-sum(baseline_kg_rels)/len(baseline_kg_rels):>+10.2f} | {sum(joern_kg_rels)/n-sum(baseline_kg_rels)/len(baseline_kg_rels):>+10.2f}")
        print(f"{'Δ vs grep-KG (tot)':.<20} | {'—':>10} | {'—':>10} | {sum(joern_totals)/n-sum(grep_totals)/len(grep_totals):>+10.2f}")
        print(f"{'Δ vs grep-KG (KG)':.<20} | {'—':>10} | {'—':>10} | {sum(joern_kg_rels)/n-sum(grep_kg_rels)/len(grep_kg_rels):>+10.2f}")

    log("\nResults compiled!")


# ============================================================
# MAIN
# ============================================================

def main():
    log("=" * 60)
    log("JOERN-KG MAIN EXPERIMENT")
    log(f"PRs: {TARGET_PRS}")
    log(f"Generator: {GENERATOR_MODEL}")
    log(f"Judges: {JUDGE_PANEL}")
    log("=" * 60)

    progress = load_progress()

    # Step 1: Generate CPGs
    log("\n━━━ STEP 1: Generate CPGs ━━━")
    for pr_id in TARGET_PRS:
        generate_cpg(pr_id, progress)

    # Step 2: Export CPGs
    log("\n━━━ STEP 2: Export CPGs to CSV ━━━")
    for pr_id in TARGET_PRS:
        if step_done(progress, f"cpg_pr{pr_id}"):
            export_cpg(pr_id, progress)

    # Step 3: Extract call graphs
    log("\n━━━ STEP 3: Extract call graphs ━━━")
    for pr_id in TARGET_PRS:
        if step_done(progress, f"export_pr{pr_id}"):
            extract_call_graph(pr_id, progress)

    # Step 4: Build evidence packs
    log("\n━━━ STEP 4: Build enriched evidence ━━━")
    for pr_id in TARGET_PRS:
        if step_done(progress, f"callgraph_pr{pr_id}"):
            build_evidence(pr_id, progress)

    # Step 5: Generate reviews
    log("\n━━━ STEP 5: Generate reviews ━━━")
    for pr_id in TARGET_PRS:
        if step_done(progress, f"evidence_pr{pr_id}"):
            generate_review(pr_id, progress)

    # Step 6: Evaluate reviews
    log("\n━━━ STEP 6: Evaluate reviews ━━━")
    for pr_id in TARGET_PRS:
        if step_done(progress, f"review_pr{pr_id}"):
            evaluate_review(pr_id, progress)

    # Step 7: Compile results
    compile_results(progress)

    # Final status
    total_steps = len(TARGET_PRS) * 6  # 6 steps per PR
    completed = sum(1 for pr_id in TARGET_PRS for s in
                    [f"cpg_pr{pr_id}", f"export_pr{pr_id}", f"callgraph_pr{pr_id}",
                     f"evidence_pr{pr_id}", f"review_pr{pr_id}", f"eval_pr{pr_id}"]
                    if step_done(progress, s))
    errors = len(progress.get("errors", []))
    log(f"\n{'='*60}")
    log(f"DONE: {completed}/{total_steps} steps completed, {errors} errors")
    if errors:
        log("Errors:")
        for e in progress["errors"]:
            log(f"  {e['step']}: {e['error'][:100]}")
    log(f"{'='*60}")


if __name__ == "__main__":
    main()
