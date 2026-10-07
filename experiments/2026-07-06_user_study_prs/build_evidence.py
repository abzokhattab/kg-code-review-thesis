#!/usr/bin/env python3
"""
build_evidence.py — evidence packs for the 4 new user-study PRs.

Produces packs in the exact schema of data/luca_prs_v2/pr*_evidence.json:
  pr, changed_files, nearest_tests, dependent_files, diff_summary, full_diff, metadata

KG edges (dependent_files / nearest_tests) are built by AST import analysis
on the repo checked out at the PR head SHA. For Python this resolves the
same relation the deployed Joern+grep pipeline approximates: which files
import the changed modules / symbols. Builder recorded in metadata.

$0 — no LLM calls. Idempotent (skips existing packs).
"""
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
EVIDENCE = BASE / "evidence"

PRS = {
    "requests_7433": dict(repo_dir="psf_requests", repo="psf/requests", src_root="src"),
    "flask_5637":    dict(repo_dir="pallets_flask", repo="pallets/flask", src_root="src"),
    "click_3493":    dict(repo_dir="pallets_click", repo="pallets/click", src_root="src"),
    "requests_7328": dict(repo_dir="psf_requests", repo="psf/requests", src_root="src"),
    "flask_5799":    dict(repo_dir="pallets_flask", repo="pallets/flask", src_root="src"),
    "click_3578":    dict(repo_dir="pallets_click", repo="pallets/click", src_root="src"),
}

LANG = {".py": "python"}


def changed_files_from_diff(diff_text):
    files = []
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            p = line[6:]
            added = deleted = 0
            files.append(p)
    return files


def diff_stats(meta):
    return [
        dict(path=f["path"], language=LANG.get(os.path.splitext(f["path"])[1], "other"),
             added=f.get("additions", 0), deleted=f.get("deletions", 0))
        for f in meta["files"]
    ]


def module_names(path):
    """Module identifiers a file can be imported as: stem and dotted package path."""
    stem = Path(path).stem
    parts = Path(path).with_suffix("").parts
    names = {stem}
    # e.g. src/requests/models.py -> requests.models
    if "src" in parts:
        i = parts.index("src")
        names.add(".".join(parts[i + 1:]))
    return {n for n in names if n not in ("__init__", "__main__")}


def imports_of(pyfile):
    """Set of imported module strings in a python file (AST-based, robust)."""
    try:
        tree = ast.parse(Path(pyfile).read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return set()
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.add(node.module)
            mods.update(a.name for a in node.names)  # from x import models
    return mods


def build_pack(key, cfg):
    out = EVIDENCE / f"{key}_evidence.json"
    if out.exists():
        print(f"{key}: cached")
        return
    meta = json.load(open(EVIDENCE / f"{key}_meta.json"))
    diff = (EVIDENCE / f"{key}.diff").read_text()
    repo = BASE / "pr_hunt" / "repos" / cfg["repo_dir"]

    # ensure repo is at this PR's head SHA
    sha = meta["headRefOid"]
    subprocess.run(["git", "-C", str(repo), "fetch", "--depth", "1", "origin", sha],
                   capture_output=True)
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", sha], check=True)

    changed = diff_stats(meta)
    changed_src = [c["path"] for c in changed
                   if c["path"].endswith(".py") and not c["path"].startswith(("tests/", "docs/"))]
    targets = set()
    for p in changed_src:
        targets |= module_names(p)

    dependents, tests = [], []
    for py in repo.rglob("*.py"):
        rel = str(py.relative_to(repo))
        if any(os.path.basename(rel) == os.path.basename(c) for c in changed_src):
            continue
        mods = imports_of(py)
        hit_targets = {t for t in targets
                       if t in mods or any(m.endswith("." + t) or m == t for m in mods)}
        if not hit_targets:
            continue
        entry_src = sorted(hit_targets)[0]
        rec = dict(path=rel, relationship="imports", source_file=entry_src)
        if "test" in rel.lower():
            rec["relationship"] = "tests"
            tests.append(rec)
        else:
            dependents.append(rec)

    pack = {
        "pr": {"number": meta["number"], "title": meta["title"], "body": meta["body"],
               "repo": cfg["repo"], "head_sha": sha, "merged_at": meta["mergedAt"]},
        "changed_files": changed,
        "nearest_tests": tests[:12],
        "dependent_files": dependents[:12],
        "diff_summary": f"{len(changed)} files changed",
        "full_diff": diff,
        "metadata": {"kg_builder": "ast_import_resolver",
                     "built": "2026-07-06",
                     "note": "AST ImportFrom/Import resolution at PR head SHA; "
                             "same relation class as deployed Joern+grep pipeline"},
    }
    out.write_text(json.dumps(pack, indent=1))
    print(f"{key}: {len(dependents)} dependents, {len(tests)} test files -> {out.name}")


if __name__ == "__main__":
    for key, cfg in PRS.items():
        build_pack(key, cfg)
