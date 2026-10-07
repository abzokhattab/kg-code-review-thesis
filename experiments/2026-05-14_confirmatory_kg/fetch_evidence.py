#!/usr/bin/env python3
"""
fetch_evidence.py — Fetch evidence packs for the 12 confirmatory PRs.

Fetches from GitHub: PR metadata, full diff, changed files.
Finds locally: nearest test files, dependent files (via filename heuristics).

Requires: repo clones in luca_repos/ (already exist from main experiment).

Output: experiments/2026-05-14_confirmatory_kg/evidence/pr{N}_evidence.json
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
EVIDENCE_DIR = SCRIPT_DIR / "evidence"
LUCA_REPOS = REPO_ROOT / "luca_repos"
CANDIDATES_PATH = SCRIPT_DIR / "candidates.json"

DIFF_CAP_BYTES = 50_000
BODY_CAP_BYTES = 8_000

REPO_DIR_MAP = {
    "grafana/grafana": "grafana_grafana",
    "apache/kafka": "apache_kafka",
    "scikit-learn/scikit-learn": "scikit-learn_scikit-learn",
    "godotengine/godot": "godotengine_godot",
    "jenkinsci/jenkins": "jenkinsci_jenkins",
}

EXT_LANG_MAP = {
    ".py": "python", ".java": "java", ".go": "go", ".ts": "typescript",
    ".tsx": "typescript", ".js": "javascript", ".cpp": "cpp", ".c": "c",
    ".h": "cpp", ".scala": "scala", ".rs": "rust", ".gd": "gdscript",
}


def detect_language(path: str) -> str:
    ext = Path(path).suffix.lower()
    return EXT_LANG_MAP.get(ext, "unknown")


def gh_json(repo: str, pr: int, fields: str) -> dict:
    result = subprocess.run(
        ["gh", "pr", "view", str(pr), "--repo", repo, "--json", fields],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh metadata failed for {repo}#{pr}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def gh_diff(repo: str, pr: int) -> str:
    result = subprocess.run(
        ["gh", "pr", "diff", str(pr), "--repo", repo],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh diff failed for {repo}#{pr}: {result.stderr.strip()}")
    return result.stdout


def gh_files(repo: str, pr: int) -> list[dict]:
    data = gh_json(repo, pr, "files")
    files = []
    for f in data.get("files", []):
        files.append({
            "path": f.get("path", ""),
            "added": f.get("additions", 0),
            "deleted": f.get("deletions", 0),
        })
    return files


def find_tests(file_path: str, repo_path: Path) -> list[dict]:
    file_name = Path(file_path).stem
    if file_name.lower() in ("index", "main", "mod", "lib", "__init__",
                             "setup", "conf"):
        return []
    tests: list[dict] = []
    seen: set[str] = set()
    patterns = [
        f"*{file_name}*[Tt]est*",
        f"*[Tt]est*{file_name}*",
        f"*{file_name}*[Ss]pec*",
        f"*{file_name}*_test*",
    ]
    for pat in patterns:
        try:
            result = subprocess.run(
                ["find", str(repo_path), "-name", pat, "-type", "f"],
                capture_output=True, text=True, timeout=20,
            )
            for line in result.stdout.strip().split("\n"):
                if line:
                    rel = os.path.relpath(line, str(repo_path))
                    if rel not in seen:
                        seen.add(rel)
                        tests.append({"path": rel, "relationship": "tests",
                                      "source_file": file_path})
        except Exception:
            pass
    return tests[:8]


def find_dependents(file_path: str, repo_path: Path, language: str) -> list[dict]:
    file_name = Path(file_path).stem
    if file_name.lower() in ("index", "main", "utils", "helpers", "types",
                             "constants", "mod", "lib", "__init__", "setup"):
        return []
    ext_map = {
        "java": ["*.java"], "go": ["*.go"], "typescript": ["*.ts", "*.tsx"],
        "cpp": ["*.cpp", "*.h", "*.hpp"], "scala": ["*.scala"],
        "python": ["*.py"],
    }
    extensions = ext_map.get(language, [])
    if not extensions:
        return []
    dependents: list[dict] = []
    seen: set[str] = set()
    for ext in extensions:
        try:
            result = subprocess.run(
                ["grep", "-rl", file_name, "--include", ext, str(repo_path)],
                capture_output=True, text=True, timeout=30,
            )
            for line in result.stdout.strip().split("\n"):
                if line:
                    rel = os.path.relpath(line, str(repo_path))
                    if rel != file_path and rel not in seen:
                        seen.add(rel)
                        dependents.append({
                            "path": rel,
                            "relationship": "imports",
                            "source_file": file_path,
                        })
        except Exception:
            pass
    return dependents[:10]


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    if not CANDIDATES_PATH.exists():
        sys.exit(f"Run find_confirmatory_prs.py first — {CANDIDATES_PATH} not found")

    data = json.loads(CANDIDATES_PATH.read_text())
    picked = data["picked"]
    print(f"Fetching evidence for {len(picked)} confirmatory PRs\n")

    for i, cand in enumerate(picked, 1):
        repo = cand["repo"]
        number = cand["number"]
        local_id = i
        out_file = EVIDENCE_DIR / f"pr{local_id}_evidence.json"

        if out_file.exists():
            print(f"  [{local_id:>2}] {repo}#{number} — already exists, skipping")
            continue

        print(f"  [{local_id:>2}] {repo}#{number} — {cand['title'][:50]}...", flush=True)

        # Fetch metadata
        meta = gh_json(repo, number, "number,title,body,state,mergedAt,url,headRefName,baseRefName")
        if meta.get("state") != "MERGED":
            print(f"       SKIP: not merged (state={meta.get('state')})")
            continue

        # Fetch diff
        diff = gh_diff(repo, number)
        diff_truncated = len(diff) > DIFF_CAP_BYTES
        if diff_truncated:
            diff = diff[:DIFF_CAP_BYTES] + "\n... [truncated at 50kB]\n"

        # Fetch file list
        files = gh_files(repo, number)
        changed_files = []
        for f in files:
            lang = detect_language(f["path"])
            changed_files.append({
                "path": f["path"],
                "language": lang,
                "added": f["added"],
                "deleted": f["deleted"],
            })

        # Find tests and dependents (requires local repo clone)
        repo_dir = LUCA_REPOS / REPO_DIR_MAP.get(repo, repo.replace("/", "_"))
        nearest_tests = []
        dependent_files = []

        if repo_dir.exists():
            for cf in changed_files:
                lang = cf["language"]
                if lang in ("unknown", "binary"):
                    continue
                nearest_tests.extend(find_tests(cf["path"], repo_dir))
                dependent_files.extend(find_dependents(cf["path"], repo_dir, lang))
        else:
            print(f"       WARNING: repo clone not found at {repo_dir}")

        # Deduplicate
        seen_tests = set()
        deduped_tests = []
        for t in nearest_tests:
            if t["path"] not in seen_tests:
                seen_tests.add(t["path"])
                deduped_tests.append(t)

        seen_deps = set()
        deduped_deps = []
        for d in dependent_files:
            if d["path"] not in seen_deps:
                seen_deps.add(d["path"])
                deduped_deps.append(d)

        # Build body
        body = meta.get("body") or ""
        if len(body) > BODY_CAP_BYTES:
            body = body[:BODY_CAP_BYTES] + "\n... [truncated at 8kB]"

        evidence = {
            "pr": {
                "number": number,
                "title": meta.get("title", ""),
                "body": body,
                "url": meta.get("url", ""),
                "repo": repo,
                "base_branch": meta.get("baseRefName", "main"),
                "head_branch": meta.get("headRefName", ""),
                "merged_at": meta.get("mergedAt", ""),
                "state": "MERGED",
            },
            "changed_files": changed_files,
            "nearest_tests": deduped_tests,
            "dependent_files": deduped_deps,
            "callers": [],
            "call_graph_edges": [],
            "full_diff": diff,
            "diff_summary": f"{len(files)} files changed",
            "similar_chunks": [],
            "metadata": {
                "experiment": "confirmatory_kg_2026-05-14",
                "local_id": local_id,
                "v2_diff_truncated": diff_truncated,
                "v2_raw_diff_chars": len(diff),
                "v2_raw_body_chars": len(body),
            },
        }

        out_file.write_text(json.dumps(evidence, indent=2))
        print(f"       -> {len(deduped_tests)} tests, {len(deduped_deps)} deps, "
              f"{len(diff)//1024}kB diff")

    print(f"\nDone. Evidence packs in {EVIDENCE_DIR}/")


if __name__ == "__main__":
    main()
