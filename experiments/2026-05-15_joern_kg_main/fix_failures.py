#!/usr/bin/env python3
"""
fix_failures.py — Fix and re-run the 4 failed PRs from the main experiment.

Issues:
- PR9, PR37 (Go): Go not installed. Replace with PR21 (kafka/Java) and PR34 (grafana/TS).
- PR47, PR33 (Jenkins): joern-parse doesn't accept multiple input paths. Use single core path.
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

CPG_DIR = SCRIPT_DIR / "cpgs"
EXPORT_DIR = SCRIPT_DIR / "exports"
EVIDENCE_DIR = SCRIPT_DIR / "evidence"
REVIEWS_DIR = SCRIPT_DIR / "reviews"
CACHE_DIR = SCRIPT_DIR / "cache"
PROGRESS_FILE = SCRIPT_DIR / "progress.json"
LUCA_REPOS = REPO_ROOT / "luca_repos"

GENERATOR_MODEL = "gemini:gemini-2.5-flash"
JUDGE_PANEL = ["gemini:gemini-2.5-flash", "gemini:gemini-2.0-flash"]

csv.field_size_limit(sys.maxsize)

# Fixed PR configurations
FIX_PRS = {
    # Replace Go PRs with supported languages
    21: {"repo": "apache_kafka", "lang": "java",
         "parse_path": "clients/src/"},
    34: {"repo": "grafana_grafana", "lang": "typescript",
         "parse_path": "public/app/features/"},
    # Fix Jenkins PRs - single path only
    47: {"repo": "jenkinsci_jenkins", "lang": "java",
         "parse_path": "core/src/main/java/"},
    33: {"repo": "jenkinsci_jenkins", "lang": "java",
         "parse_path": "core/src/main/java/"},
}


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_progress():
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"steps_completed": {}, "errors": []}


def save_progress(progress):
    progress["last_updated"] = datetime.now(timezone.utc).isoformat()
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


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


def run_pr(pr_id, config, progress):
    """Run the full pipeline for a single PR."""
    repo_dir = LUCA_REPOS / config["repo"]
    parse_path = str(repo_dir / config["parse_path"])

    if not Path(parse_path).exists():
        log(f"  PR{pr_id}: ERROR - path not found: {parse_path}")
        return False

    # Step 1: CPG
    cpg_file = CPG_DIR / f"pr{pr_id}.bin"
    step = f"cpg_pr{pr_id}"
    if not progress["steps_completed"].get(step):
        log(f"  PR{pr_id}: generating CPG...")
        cmd = ["joern-parse", parse_path, "--output", str(cpg_file)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0 or not cpg_file.exists():
            log(f"  PR{pr_id}: CPG FAILED - {result.stderr[-200:]}")
            return False
        size_mb = cpg_file.stat().st_size / (1024 * 1024)
        log(f"  PR{pr_id}: CPG done ({size_mb:.1f} MB)")
        progress["steps_completed"][step] = datetime.now(timezone.utc).isoformat()
        save_progress(progress)

    # Step 2: Export
    export_dir = EXPORT_DIR / f"pr{pr_id}"
    step = f"export_pr{pr_id}"
    if not progress["steps_completed"].get(step):
        if export_dir.exists():
            subprocess.run(["rm", "-rf", str(export_dir)])
        log(f"  PR{pr_id}: exporting CPG...")
        cmd = ["joern-export", "--repr", "all", "--format", "neo4jcsv",
               "--out", str(export_dir), str(cpg_file)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if not (export_dir / "nodes_METHOD_data.csv").exists():
            log(f"  PR{pr_id}: export FAILED")
            return False
        log(f"  PR{pr_id}: export done")
        progress["steps_completed"][step] = datetime.now(timezone.utc).isoformat()
        save_progress(progress)

    # Step 3: Extract call graph
    step = f"callgraph_pr{pr_id}"
    if not progress["steps_completed"].get(step):
        orig_evidence = json.loads((REPO_ROOT / "data" / "luca_prs_v2" / f"pr{pr_id}_evidence.json").read_text())
        changed_files = [f['path'].split('/')[-1] for f in orig_evidence.get('changed_files', [])
                         if f.get('language') not in ('', 'unknown', 'xml', 'gradle', 'rst', 'markdown', 'json', 'yaml')]

        log(f"  PR{pr_id}: extracting call graph for {changed_files}...")

        methods = load_csv_with_header(export_dir / "nodes_METHOD_data.csv")
        method_by_id = {m[':ID']: m for m in methods}

        synthetic = {'<module>', '<body>', '<metaClassCallHandler>', '<fakeNew>',
                     '<metaClassAdapter>', '<clinit>', '<init>', '<global>'}

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

        if not target_methods:
            # Partial match fallback
            for m in methods:
                fname = m.get('FILENAME:string', '')
                name = m.get('NAME:string', '')
                if (any(cf.replace('.java','').replace('.py','').replace('.go','').replace('.ts','').replace('.tsx','').replace('.scala','') in fname
                        for cf in changed_files)
                    and name not in synthetic
                    and '<metaClassAdapter>' not in name
                    and m.get('IS_EXTERNAL:boolean') != 'true'):
                    target_methods[m[':ID']] = m

        log(f"  PR{pr_id}: {len(target_methods)} target methods")

        call_edges = load_csv_with_header(export_dir / "edges_CALL_data.csv")
        calls_to_targets = [(e[':START_ID'], e[':END_ID']) for e in call_edges if e[':END_ID'] in target_methods]

        contains_edges = load_csv_with_header(export_dir / "edges_CONTAINS_data.csv")
        child_to_method_parent = {}
        for edge in contains_edges:
            if edge[':START_ID'] in method_by_id:
                child_to_method_parent[edge[':END_ID']] = edge[':START_ID']

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

        functions = [{"name": m.get('NAME:string', ''), "full_name": m.get('FULL_NAME:string', ''),
                      "file": m.get('FILENAME:string', ''), "start_line": int(m.get('LINE_NUMBER:int', 0) or 0),
                      "end_line": int(m.get('LINE_NUMBER_END:int', 0) or 0), "signature": m.get('SIGNATURE:string', '')}
                     for m in target_methods.values()]

        output = {"callers": callers, "functions_in_changed_files": functions}
        (CACHE_DIR / f"pr{pr_id}_callgraph.json").write_text(json.dumps(output, indent=2))
        log(f"  PR{pr_id}: {len(callers)} callers, {len(functions)} functions")
        progress["steps_completed"][step] = datetime.now(timezone.utc).isoformat()
        save_progress(progress)

    # Step 4: Build evidence
    step = f"evidence_pr{pr_id}"
    if not progress["steps_completed"].get(step):
        cg = json.loads((CACHE_DIR / f"pr{pr_id}_callgraph.json").read_text())
        evidence = json.loads((REPO_ROOT / "data" / "luca_prs_v2" / f"pr{pr_id}_evidence.json").read_text())

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

        (EVIDENCE_DIR / f"pr{pr_id}_evidence.json").write_text(json.dumps(evidence, indent=2))
        log(f"  PR{pr_id}: evidence built ({len(callers_fmt)} callers)")
        progress["steps_completed"][step] = datetime.now(timezone.utc).isoformat()
        save_progress(progress)

    # Step 5: Generate review
    step = f"review_pr{pr_id}"
    if not progress["steps_completed"].get(step):
        from prnote.llm import generate_completion
        from prnote.note import format_kg_context, get_diff_from_evidence

        evidence = json.loads((EVIDENCE_DIR / f"pr{pr_id}_evidence.json").read_text())
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

        log(f"  PR{pr_id}: generating review...")
        review = generate_completion(prompt=user_prompt, system=system_prompt, model=GENERATOR_MODEL, temperature=0.0)
        (REVIEWS_DIR / f"pr{pr_id}_joern_kg.md").write_text(review)
        log(f"  PR{pr_id}: review done ({len(review)} chars)")
        progress["steps_completed"][step] = datetime.now(timezone.utc).isoformat()
        save_progress(progress)

    # Step 6: Evaluate
    step = f"eval_pr{pr_id}"
    if not progress["steps_completed"].get(step):
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from evaluate_reviews import evaluate_single_review
        from dataclasses import asdict

        review_file = REVIEWS_DIR / f"pr{pr_id}_joern_kg.md"
        log(f"  PR{pr_id}: evaluating...")
        ev = evaluate_single_review(review_file, pr_id, "joern_kg", JUDGE_PANEL)
        result = asdict(ev)
        (CACHE_DIR / f"pr{pr_id}_eval.json").write_text(json.dumps(result, indent=2))
        log(f"  PR{pr_id}: total={result['total_score']}/25, KG-rel={result['kg_relevant_score']}/9")
        progress["steps_completed"][step] = datetime.now(timezone.utc).isoformat()
        save_progress(progress)

    return True


def main():
    progress = load_progress()

    # Remove old error entries for the PRs we're fixing
    old_prs = {9, 37}  # replaced
    progress["errors"] = [e for e in progress.get("errors", [])
                          if not any(f"pr{p}" in e.get("step", "") for p in old_prs | set(FIX_PRS.keys()))]
    # Clear old steps for replaced/fixed PRs
    for pr_id in list(FIX_PRS.keys()) + [9, 37]:
        for prefix in ["cpg_", "export_", "callgraph_", "evidence_", "review_", "eval_"]:
            progress["steps_completed"].pop(f"{prefix}pr{pr_id}", None)
    save_progress(progress)

    log("Fixing 4 failed PRs: 21 (replaces 9), 34 (replaces 37), 47, 33")

    for pr_id, config in FIX_PRS.items():
        log(f"\n{'='*40} PR{pr_id} {'='*40}")
        try:
            run_pr(pr_id, config, progress)
        except Exception as e:
            log(f"  PR{pr_id}: EXCEPTION - {e}")
            progress["errors"].append({"step": f"pr{pr_id}", "error": str(e)})
            save_progress(progress)

    log("\nDone fixing failures!")


if __name__ == "__main__":
    main()
