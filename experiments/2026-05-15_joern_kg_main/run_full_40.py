#!/usr/bin/env python3
"""
run_full_40.py — Full 40-PR Joern-KG experiment.

Uses Joern CPG for precise call graph extraction on ALL 40 PRs.
Fully checkpointed — safe to interrupt and resume.

Usage:
    source load_env.sh && python3 experiments/2026-05-15_joern_kg_main/run_full_40.py
"""
import csv
import json
import os
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
PROGRESS_FILE = SCRIPT_DIR / "progress_full40.json"
LUCA_REPOS = REPO_ROOT / "luca_repos"

# Models
GENERATOR_MODEL = "gemini:gemini-2.5-flash"
JUDGE_PANEL = ["gemini:gemini-2.5-flash", "gemini:gemini-2.0-flash"]
KG_REFINED = {'F3', 'F4', 'T3', 'M1', 'C2'}

csv.field_size_limit(sys.maxsize)

# Load PR config
PR_CONFIG = json.loads((SCRIPT_DIR / "pr_config.json").read_text())
ALL_PRS = sorted(int(k) for k in PR_CONFIG.keys())


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_progress():
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"steps_completed": {}, "errors": [], "started_at": datetime.now(timezone.utc).isoformat()}


def save_progress(progress):
    progress["last_updated"] = datetime.now(timezone.utc).isoformat()
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


def step_done(progress, step):
    return bool(progress["steps_completed"].get(step))


def mark_done(progress, step):
    progress["steps_completed"][step] = datetime.now(timezone.utc).isoformat()
    save_progress(progress)


def record_error(progress, step, error):
    progress["errors"].append({"step": step, "error": error[:300], "time": datetime.now(timezone.utc).isoformat()})
    save_progress(progress)


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


def _cpg_key(pr_id):
    """Unique key for a CPG (repo+parse_path). PRs sharing this reuse a CPG."""
    config = PR_CONFIG[str(pr_id)]
    return f"{config['repo']}__{config['parse_path'].replace('/', '_')}"


def generate_cpg(pr_id, progress):
    step = f"cpg_pr{pr_id}"
    if step_done(progress, step):
        return True

    config = PR_CONFIG[str(pr_id)]
    repo_dir = LUCA_REPOS / config["repo"]
    parse_path = str(repo_dir / config["parse_path"])
    cpg_file = CPG_DIR / f"pr{pr_id}.bin"

    if not Path(parse_path).exists():
        record_error(progress, step, f"Path not found: {parse_path}")
        return False

    # Check if another PR with same repo+parse_path already has a CPG
    my_key = _cpg_key(pr_id)
    for other_id in ALL_PRS:
        if other_id == pr_id:
            continue
        if _cpg_key(other_id) == my_key:
            other_cpg = CPG_DIR / f"pr{other_id}.bin"
            if other_cpg.exists() and other_cpg.stat().st_size > 1000:
                # Symlink to existing CPG
                if cpg_file.exists():
                    cpg_file.unlink()
                cpg_file.symlink_to(other_cpg)
                log(f"  PR{pr_id}: CPG reused from PR{other_id}")
                mark_done(progress, step)
                return True

    lang = config["lang"]
    cmd = ["joern-parse", parse_path, "--output", str(cpg_file)]
    # Add language hint for Go
    if lang == "go":
        cmd = ["joern-parse", "--language", "golang", parse_path, "--output", str(cpg_file)]

    log(f"  PR{pr_id}: CPG ({lang}, {config['parse_path']})...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                               env={**os.environ, "PATH": "/opt/homebrew/bin:" + os.environ.get("PATH", "")})
        if not cpg_file.exists() or cpg_file.stat().st_size < 1000:
            record_error(progress, step, f"CPG generation failed: {result.stderr[-200:]}")
            return False
        size_mb = cpg_file.stat().st_size / (1024 * 1024)
        log(f"  PR{pr_id}: CPG OK ({size_mb:.1f} MB)")
        mark_done(progress, step)
        return True
    except subprocess.TimeoutExpired:
        record_error(progress, step, "Timeout (600s)")
        return False
    except Exception as e:
        record_error(progress, step, str(e))
        return False


def export_cpg(pr_id, progress):
    step = f"export_pr{pr_id}"
    if step_done(progress, step):
        return True

    cpg_file = CPG_DIR / f"pr{pr_id}.bin"
    export_dir = EXPORT_DIR / f"pr{pr_id}"

    if not cpg_file.exists():
        record_error(progress, step, "CPG not found")
        return False

    # Check if another PR with same CPG already has an export
    my_key = _cpg_key(pr_id)
    for other_id in ALL_PRS:
        if other_id == pr_id:
            continue
        if _cpg_key(other_id) == my_key:
            other_export = EXPORT_DIR / f"pr{other_id}"
            if (other_export / "nodes_METHOD_data.csv").exists():
                # Symlink to existing export
                if export_dir.exists():
                    subprocess.run(["rm", "-rf", str(export_dir)])
                export_dir.symlink_to(other_export)
                log(f"  PR{pr_id}: export reused from PR{other_id}")
                mark_done(progress, step)
                return True

    if export_dir.exists():
        subprocess.run(["rm", "-rf", str(export_dir)])

    cmd = ["joern-export", "--repr", "all", "--format", "neo4jcsv",
           "--out", str(export_dir), str(cpg_file)]
    log(f"  PR{pr_id}: exporting...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if not (export_dir / "nodes_METHOD_data.csv").exists():
            record_error(progress, step, "No METHOD nodes in export")
            return False
        log(f"  PR{pr_id}: export OK")
        mark_done(progress, step)
        return True
    except subprocess.TimeoutExpired:
        record_error(progress, step, "Timeout (600s)")
        return False
    except Exception as e:
        record_error(progress, step, str(e))
        return False


def extract_call_graph(pr_id, progress):
    step = f"callgraph_pr{pr_id}"
    if step_done(progress, step):
        return True

    export_dir = EXPORT_DIR / f"pr{pr_id}"
    config = PR_CONFIG[str(pr_id)]

    changed_files = config.get("changed_files", [])
    if not changed_files:
        output = {"callers": [], "functions_in_changed_files": []}
        (CACHE_DIR / f"pr{pr_id}_callgraph.json").write_text(json.dumps(output))
        mark_done(progress, step)
        return True

    log(f"  PR{pr_id}: call graph ({len(changed_files)} files)...")

    methods = load_csv_with_header(export_dir / "nodes_METHOD_data.csv")
    method_by_id = {m[':ID']: m for m in methods}

    synthetic = {'<module>', '<body>', '<metaClassCallHandler>', '<fakeNew>',
                 '<metaClassAdapter>', '<clinit>', '<init>', '<global>',
                 '<lambda>', '<lambda>0', '<lambda>1', '<lambda>2'}

    # Find target methods by exact filename match
    target_methods = {}
    for m in methods:
        fname = m.get('FILENAME:string', '')
        name = m.get('NAME:string', '')
        basename = fname.split('/')[-1] if fname else ''
        if (basename in changed_files
            and name not in synthetic
            and '<metaClassAdapter>' not in name
            and '<lambda>' not in name
            and m.get('IS_EXTERNAL:boolean') != 'true'):
            target_methods[m[':ID']] = m

    # Fallback: partial match (strip extension)
    if not target_methods:
        for m in methods:
            fname = m.get('FILENAME:string', '')
            name = m.get('NAME:string', '')
            if (any(cf.rsplit('.', 1)[0] in fname for cf in changed_files if '.' in cf)
                and name not in synthetic
                and '<metaClassAdapter>' not in name
                and '<lambda>' not in name
                and m.get('IS_EXTERNAL:boolean') != 'true'):
                target_methods[m[':ID']] = m

    # Cap at 200 target methods to avoid explosion
    if len(target_methods) > 200:
        # Keep only methods whose filename exactly matches a changed file
        exact = {mid: m for mid, m in target_methods.items()
                 if m.get('FILENAME:string', '').split('/')[-1] in changed_files}
        if exact:
            target_methods = exact

    # Load CALL edges
    call_edges = load_csv_with_header(export_dir / "edges_CALL_data.csv")
    calls_to_targets = [(e[':START_ID'], e[':END_ID']) for e in call_edges if e[':END_ID'] in target_methods]

    # Load CONTAINS edges
    contains_edges = load_csv_with_header(export_dir / "edges_CONTAINS_data.csv")
    child_to_method_parent = {}
    for edge in contains_edges:
        if edge[':START_ID'] in method_by_id:
            child_to_method_parent[edge[':END_ID']] = edge[':START_ID']

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
        if caller_name in synthetic or '<metaClassAdapter>' in caller_name or '<lambda>' in caller_name:
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
        if len(callers) >= 50:  # cap callers to keep context manageable
            break

    # Function definitions (cap at 50)
    functions = []
    for mid, m in list(target_methods.items())[:50]:
        functions.append({
            "name": m.get('NAME:string', ''), "full_name": m.get('FULL_NAME:string', ''),
            "file": m.get('FILENAME:string', ''), "start_line": int(m.get('LINE_NUMBER:int', 0) or 0),
            "end_line": int(m.get('LINE_NUMBER_END:int', 0) or 0), "signature": m.get('SIGNATURE:string', ''),
        })

    output = {"callers": callers, "functions_in_changed_files": functions}
    (CACHE_DIR / f"pr{pr_id}_callgraph.json").write_text(json.dumps(output, indent=2))
    log(f"  PR{pr_id}: {len(callers)} callers, {len(functions)} functions")
    mark_done(progress, step)
    return True


def build_evidence(pr_id, progress):
    step = f"evidence_pr{pr_id}"
    if step_done(progress, step):
        return True

    cg_file = CACHE_DIR / f"pr{pr_id}_callgraph.json"
    if not cg_file.exists():
        record_error(progress, step, "Call graph not found")
        return False

    evidence = json.loads((REPO_ROOT / "data" / "luca_prs_v2" / f"pr{pr_id}_evidence.json").read_text())
    cg = json.loads(cg_file.read_text())

    raw_callers = cg.get("callers", [])
    callers_fmt = [{"path": c["caller_file"], "from_function": c["caller_name"],
                    "calls_function": c["callee_name"], "caller_line": c["caller_line"],
                    "callee_file": c["callee_file"], "callee_line": c["callee_line"]} for c in raw_callers]
    if callers_fmt:
        evidence["callers"] = callers_fmt

    edges = [{"from": f"{c['caller_file']}::{c['caller_name']}", "to": f"{c['callee_file']}::{c['callee_name']}"} for c in raw_callers]
    if edges:
        evidence["call_graph_edges"] = edges

    funcs = cg.get("functions_in_changed_files", [])
    if funcs:
        evidence["functions_in_changed_files"] = funcs

    evidence.setdefault("metadata", {})["joern_enriched"] = True
    evidence["metadata"]["joern_callers_count"] = len(callers_fmt)
    evidence["metadata"]["joern_functions_count"] = len(funcs)

    (EVIDENCE_DIR / f"pr{pr_id}_evidence.json").write_text(json.dumps(evidence, indent=2))
    log(f"  PR{pr_id}: evidence ({len(callers_fmt)}c, {len(funcs)}f)")
    mark_done(progress, step)
    return True


def generate_review(pr_id, progress):
    step = f"review_pr{pr_id}"
    if step_done(progress, step):
        return True

    from prnote.llm import generate_completion
    from prnote.note import format_kg_context, get_diff_from_evidence

    ev_file = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    if not ev_file.exists():
        record_error(progress, step, "Evidence not found")
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

    log(f"  PR{pr_id}: review...")
    try:
        review = generate_completion(prompt=user_prompt, system=system_prompt,
                                     model=GENERATOR_MODEL, temperature=0.0)
        (REVIEWS_DIR / f"pr{pr_id}_joern_kg.md").write_text(review)
        log(f"  PR{pr_id}: review OK ({len(review)} chars)")
        mark_done(progress, step)
        return True
    except Exception as e:
        record_error(progress, step, str(e))
        return False


def evaluate_review(pr_id, progress):
    step = f"eval_pr{pr_id}"
    if step_done(progress, step):
        return True

    review_file = REVIEWS_DIR / f"pr{pr_id}_joern_kg.md"
    if not review_file.exists():
        record_error(progress, step, "Review not found")
        return False

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from evaluate_reviews import evaluate_single_review
    from dataclasses import asdict

    log(f"  PR{pr_id}: eval...")
    try:
        ev = evaluate_single_review(review_file, pr_id, "joern_kg", JUDGE_PANEL)
        result = asdict(ev)
        (CACHE_DIR / f"pr{pr_id}_eval.json").write_text(json.dumps(result, indent=2))
        total = result.get('total_score', 0)
        kg_c = {cs['criterion_id']: cs['score'] for cs in result.get('criteria_scores', [])}
        kg_rel = sum(kg_c.get(k, 0) for k in KG_REFINED)
        log(f"  PR{pr_id}: total={total}/25, KG-rel={kg_rel}/5")
        mark_done(progress, step)
        return True
    except Exception as e:
        record_error(progress, step, str(e))
        return False


def main():
    log("=" * 70)
    log(f"JOERN-KG FULL EXPERIMENT — {len(ALL_PRS)} PRs")
    log(f"Generator: {GENERATOR_MODEL} | Judges: {JUDGE_PANEL}")
    log("=" * 70)

    progress = load_progress()

    for phase_name, phase_fn in [
        ("STEP 1: Generate CPGs", generate_cpg),
        ("STEP 2: Export CPGs", export_cpg),
        ("STEP 3: Extract call graphs", extract_call_graph),
        ("STEP 4: Build evidence", build_evidence),
        ("STEP 5: Generate reviews", generate_review),
        ("STEP 6: Evaluate reviews", evaluate_review),
    ]:
        log(f"\n━━━ {phase_name} ━━━")
        for pr_id in ALL_PRS:
            # Check prerequisite
            prereqs = {
                "STEP 2": f"cpg_pr{pr_id}",
                "STEP 3": f"export_pr{pr_id}",
                "STEP 4": f"callgraph_pr{pr_id}",
                "STEP 5": f"evidence_pr{pr_id}",
                "STEP 6": f"review_pr{pr_id}",
            }
            phase_num = phase_name.split(":")[0]
            prereq = prereqs.get(phase_num)
            if prereq and not step_done(progress, prereq):
                continue
            phase_fn(pr_id, progress)

    # Final summary
    total_steps = len(ALL_PRS) * 6
    completed = sum(1 for pr_id in ALL_PRS for s in
                    [f"cpg_pr{pr_id}", f"export_pr{pr_id}", f"callgraph_pr{pr_id}",
                     f"evidence_pr{pr_id}", f"review_pr{pr_id}", f"eval_pr{pr_id}"]
                    if step_done(progress, s))
    errors = len(progress.get("errors", []))
    log(f"\n{'='*70}")
    log(f"COMPLETED: {completed}/{total_steps} steps, {errors} errors")
    if errors:
        log(f"Errors on: {set(e['step'] for e in progress['errors'])}")
    log(f"{'='*70}")


if __name__ == "__main__":
    main()
