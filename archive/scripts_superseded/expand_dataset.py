#!/usr/bin/env python3
"""
Expand dataset from 10 to 25 PRs.

For each new PR:
1. Fetch PR metadata and diff from GitHub (gh CLI)
2. Find related tests and dependents in cloned repos
3. Create evidence pack with full_diff, changed_files, nearest_tests, dependent_files
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any

EVIDENCE_DIR = Path("/Users/akhattab/ai/data/luca_prs_fixed")
LUCA_REPOS = Path("/Users/akhattab/ai/luca_repos")

NEW_PRS = {
    12: {"github_repo": "godotengine/godot",          "pr_number": 68625,  "local_repo": "godotengine_godot",          "language": "cpp"},
    13: {"github_repo": "godotengine/godot",          "pr_number": 89111,  "local_repo": "godotengine_godot",          "language": "cpp"},
    14: {"github_repo": "grafana/grafana",            "pr_number": 67809,  "local_repo": "grafana_grafana",            "language": "go,typescript"},
    15: {"github_repo": "grafana/grafana",            "pr_number": 78399,  "local_repo": "grafana_grafana",            "language": "go,typescript"},
    16: {"github_repo": "grafana/grafana",            "pr_number": 96722,  "local_repo": "grafana_grafana",            "language": "go,typescript"},
    17: {"github_repo": "jenkinsci/jenkins",          "pr_number": 7853,   "local_repo": "jenkinsci_jenkins",          "language": "java"},
    18: {"github_repo": "jenkinsci/jenkins",          "pr_number": 9002,   "local_repo": "jenkinsci_jenkins",          "language": "java"},
    19: {"github_repo": "jenkinsci/jenkins",          "pr_number": 6229,   "local_repo": "jenkinsci_jenkins",          "language": "java"},
    20: {"github_repo": "apache/kafka",               "pr_number": 18330,  "local_repo": "apache_kafka",               "language": "java,scala"},
    21: {"github_repo": "apache/kafka",               "pr_number": 17441,  "local_repo": "apache_kafka",               "language": "java,scala"},
    22: {"github_repo": "apache/kafka",               "pr_number": 17594,  "local_repo": "apache_kafka",               "language": "java,scala"},
    23: {"github_repo": "scikit-learn/scikit-learn",  "pr_number": 22643,  "local_repo": "scikit-learn_scikit-learn",   "language": "python"},
    24: {"github_repo": "scikit-learn/scikit-learn",  "pr_number": 26836,  "local_repo": "scikit-learn_scikit-learn",   "language": "python"},
    25: {"github_repo": "django/django",              "pr_number": 18540,  "local_repo": "django_django",              "language": "python"},
    26: {"github_repo": "django/django",              "pr_number": 18322,  "local_repo": "django_django",              "language": "python"},
}


def gh_json(repo: str, pr: int, fields: str) -> Dict:
    result = subprocess.run(
        ["gh", "pr", "view", str(pr), "--repo", repo, "--json", fields],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def get_pr_diff(repo: str, pr: int, max_chars: int = 15000) -> str:
    result = subprocess.run(
        ["gh", "pr", "diff", str(pr), "--repo", repo],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        return ""
    return result.stdout[:max_chars]


def get_file_stats(repo: str, pr: int) -> List[Dict]:
    data = gh_json(repo, pr, "files")
    files = []
    for f in data.get("files", []):
        files.append({
            "path": f.get("path", ""),
            "added": f.get("additions", 0),
            "deleted": f.get("deletions", 0),
        })
    return files


def find_tests(file_path: str, repo_path: str) -> List[Dict]:
    file_name = Path(file_path).stem
    if file_name.lower() in ("index", "main", "mod", "lib", "__init__", "setup", "conf"):
        return []

    tests = []
    seen = set()
    patterns = [
        f"*{file_name}*[Tt]est*",
        f"*[Tt]est*{file_name}*",
        f"*{file_name}*[Ss]pec*",
        f"*{file_name}*_test*",
    ]
    for pat in patterns:
        try:
            result = subprocess.run(
                ["find", repo_path, "-name", pat, "-type", "f"],
                capture_output=True, text=True, timeout=20,
            )
            for line in result.stdout.strip().split("\n"):
                if line:
                    rel = os.path.relpath(line, repo_path)
                    if rel not in seen:
                        seen.add(rel)
                        tests.append({"path": rel, "relationship": "tests", "source_file": file_path})
        except Exception:
            pass
    return tests[:5]


def find_dependents(file_path: str, repo_path: str, language: str) -> List[Dict]:
    file_name = Path(file_path).stem
    if file_name.lower() in ("index", "main", "utils", "helpers", "types", "constants", "mod", "lib", "__init__", "setup"):
        return []

    ext_map = {
        "java": ["*.java"], "go": ["*.go"], "typescript": ["*.ts", "*.tsx"],
        "cpp": ["*.cpp", "*.h", "*.hpp"], "scala": ["*.scala"], "python": ["*.py"],
    }
    includes = []
    for lang in language.split(","):
        includes.extend(ext_map.get(lang.strip(), []))
    if not includes:
        includes = ["*.java", "*.go", "*.ts", "*.py", "*.cpp", "*.scala"]

    deps = []
    try:
        args = ["grep", "-rl", file_name, repo_path]
        for inc in includes:
            args.extend(["--include", inc])
        result = subprocess.run(args, capture_output=True, text=True, timeout=60)
        seen = set()
        for line in result.stdout.strip().split("\n"):
            if line:
                rel = os.path.relpath(line, repo_path)
                if rel != file_path and rel not in seen:
                    seen.add(rel)
                    deps.append({"path": rel, "relationship": "imports", "source_file": file_path})
    except Exception:
        pass
    return deps[:10]


def detect_language(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {
        ".py": "python", ".java": "java", ".go": "go", ".ts": "typescript",
        ".tsx": "typescript", ".js": "javascript", ".cpp": "cpp", ".c": "c",
        ".h": "cpp", ".scala": "scala", ".rs": "rust", ".gd": "gdscript",
        ".yml": "yaml", ".yaml": "yaml", ".json": "json", ".md": "markdown",
        ".xml": "xml", ".html": "html", ".css": "css", ".sh": "shell",
        ".rst": "rst", ".txt": "text",
    }.get(ext, "unknown")


def build_evidence_for_pr(pr_id: int, config: Dict) -> bool:
    github_repo = config["github_repo"]
    pr_number = config["pr_number"]
    local_repo = str(LUCA_REPOS / config["local_repo"])
    language = config["language"]

    print(f"  Fetching metadata from {github_repo}#{pr_number}...")
    try:
        meta = gh_json(github_repo, pr_number, "title,body,url,state,baseRefName,headRefName")
    except Exception as e:
        print(f"  ERROR fetching metadata: {e}")
        return False

    print(f"  Fetching diff...")
    full_diff = get_pr_diff(github_repo, pr_number)
    if not full_diff:
        print(f"  WARNING: empty diff")

    print(f"  Fetching file stats...")
    file_stats = get_file_stats(github_repo, pr_number)

    has_working_tree = any((LUCA_REPOS / config["local_repo"]).iterdir()
                          for _ in [1]
                          if (LUCA_REPOS / config["local_repo"]).exists())
    src_files_exist = False
    if has_working_tree:
        for item in (LUCA_REPOS / config["local_repo"]).iterdir():
            if item.name != ".git":
                src_files_exist = True
                break

    all_tests = []
    all_deps = []
    changed_files = []

    for fs in file_stats:
        path = fs["path"]
        lang = detect_language(path)
        changed_files.append({
            "path": path,
            "language": lang,
            "added": fs["added"],
            "deleted": fs["deleted"],
        })

        if src_files_exist:
            tests = find_tests(path, local_repo)
            all_tests.extend(tests)
            deps = find_dependents(path, local_repo, language)
            all_deps.extend(deps)

    seen_tests = set()
    unique_tests = []
    for t in all_tests:
        if t["path"] not in seen_tests:
            seen_tests.add(t["path"])
            unique_tests.append(t)

    seen_deps = set()
    unique_deps = []
    changed_paths = {cf["path"] for cf in changed_files}
    for d in all_deps:
        if d["path"] not in seen_deps and d["path"] not in changed_paths:
            seen_deps.add(d["path"])
            unique_deps.append(d)

    evidence = {
        "pr": {
            "number": pr_number,
            "title": meta.get("title", ""),
            "body": (meta.get("body", "") or "")[:2000],
            "url": meta.get("url", f"https://github.com/{github_repo}/pull/{pr_number}"),
            "repo": github_repo,
            "base_branch": meta.get("baseRefName", "main"),
            "head_branch": meta.get("headRefName", ""),
        },
        "changed_files": changed_files,
        "nearest_tests": unique_tests[:15],
        "dependent_files": unique_deps[:15],
        "diff_summary": f"{len(changed_files)} files changed",
        "full_diff": full_diff,
    }

    out_path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    with open(out_path, "w") as f:
        json.dump(evidence, f, indent=2)

    print(f"  Saved: {len(changed_files)} files, {len(unique_tests)} tests, {len(unique_deps)} deps, diff={len(full_diff)} chars")
    return True


def main():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    pr_ids = sorted(NEW_PRS.keys())
    if len(sys.argv) > 1 and sys.argv[1] != "--force":
        pr_ids = [int(x) for x in sys.argv[1:]]

    print("=" * 60)
    print(f"Expanding Dataset: Building evidence for {len(pr_ids)} new PRs")
    print("=" * 60)

    ok = 0
    fail = 0
    for pr_id in pr_ids:
        config = NEW_PRS.get(pr_id)
        if not config:
            print(f"PR{pr_id}: unknown, skipping")
            continue

        print(f"\n{'='*40}")
        print(f"PR #{pr_id} ({config['github_repo']}#{config['pr_number']})")
        print(f"{'='*40}")

        if build_evidence_for_pr(pr_id, config):
            ok += 1
        else:
            fail += 1

    print(f"\n{'='*60}")
    print(f"Done! {ok} succeeded, {fail} failed")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
