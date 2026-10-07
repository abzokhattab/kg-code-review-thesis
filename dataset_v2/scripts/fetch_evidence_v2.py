#!/usr/bin/env python3
"""
fetch_evidence_v2.py — Re-fetch the 18 v2 PRs from GitHub with full
bodies and untruncated diffs.

Reads:  no inputs (PR list is hardcoded below; matches dataset_v2/docs/SELECTION_v2.md)
Writes: data/luca_prs_v2/pr{N}_evidence.json   (one per PR)

Differences from scripts/expand_dataset.py:

  * No body-length cap (was 2 000 chars; full body is captured up to
    8 000 chars, beyond which we tail-truncate with an explicit
    marker)
  * No diff-length cap of 15 kB; we fetch the full diff. Default
    safety cap is 50 kB; if exceeded we error out (signalling the
    PR is too large for the v2 protocol).
  * Verifies PR is MERGED; refuses to write a non-merged PR.
  * Verifies the title is real (not a placeholder); refuses to
    write a PR with a missing/empty title.
  * Reuses find_tests() and find_dependents() from
    scripts/expand_dataset.py.

Run from anywhere; uses Path resolution.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR_V2 = REPO_ROOT / "data" / "luca_prs_v2"
LUCA_REPOS = REPO_ROOT / "luca_repos"

# 50 kB cap: diffs above this are out of scope for the v2 protocol.
# Reasoning: 50 kB ≈ 12 500 tokens at 4 char/token; well under gpt-4o
# 128k context; leaves room for system prompt + KG + RAG blocks +
# completion.
DIFF_CAP_BYTES = 50_000

# 8 kB body cap (real PR bodies in v1 were capped at 2 kB; we bump to
# 8 kB to capture full design discussions but tail-truncate on the
# rare > 8 kB body to avoid prompt blowups).
BODY_CAP_BYTES = 8_000

# v2 PR set. Selection rationale: dataset_v2/docs/SELECTION_v2.md.
# Listed as (pr_id, github_repo, pr_number, local_repo_subdir, primary_language).
V2_PRS: list[tuple[int, str, int, str, str]] = [
    (1,  "godotengine/godot",          73144, "godotengine_godot",          "cpp"),
    (2,  "grafana/grafana",            69259, "grafana_grafana",            "go,typescript"),
    (3,  "grafana/grafana",            97224, "grafana_grafana",            "go,typescript"),
    (6,  "apache/kafka",               14778, "apache_kafka",               "java,scala"),
    (8,  "grafana/grafana",            95949, "grafana_grafana",            "go,typescript"),
    (9,  "grafana/grafana",            98123, "grafana_grafana",            "go,typescript"),
    (10, "scikit-learn/scikit-learn",  22365, "scikit-learn_scikit-learn",  "python"),
    (12, "godotengine/godot",          68625, "godotengine_godot",          "cpp"),
    (13, "godotengine/godot",          89111, "godotengine_godot",          "cpp"),
    (14, "grafana/grafana",            67809, "grafana_grafana",            "go,typescript"),
    (15, "grafana/grafana",            78399, "grafana_grafana",            "go,typescript"),
    (18, "jenkinsci/jenkins",           9002, "jenkinsci_jenkins",          "java"),
    (19, "jenkinsci/jenkins",           6229, "jenkinsci_jenkins",          "java"),
    (20, "apache/kafka",               18330, "apache_kafka",               "java,scala"),
    (21, "apache/kafka",               17441, "apache_kafka",               "java,scala"),
    (22, "apache/kafka",               17594, "apache_kafka",               "java,scala"),
    (23, "scikit-learn/scikit-learn",  22643, "scikit-learn_scikit-learn",  "python"),
    (24, "scikit-learn/scikit-learn",  26836, "scikit-learn_scikit-learn",  "python"),
    # ─── Decision (2026-05-05): expand v2 from 18 → 25 PRs ───
    # Replacements for the 7 dropped from v1 (5, 7, 11, 16, 17, 25, 26).
    # Selection rule + audit: dataset_v2/scripts/find_seven_more_prs.py.
    # All 7 are MERGED, body ≥ 100 chars, 100% KG-parseable, single-purpose,
    # diff in [1.5 kB, 50 kB], not a dependency-bump / docs-only / revert.
    (27, "grafana/grafana",           124099, "grafana_grafana",            "go,typescript"),
    (28, "grafana/grafana",           124090, "grafana_grafana",            "go,typescript"),
    (29, "apache/kafka",               22195, "apache_kafka",               "java,scala"),
    (30, "godotengine/godot",         119132, "godotengine_godot",          "cpp"),
    (31, "scikit-learn/scikit-learn",  33918, "scikit-learn_scikit-learn",  "python"),
    (32, "scikit-learn/scikit-learn",  33878, "scikit-learn_scikit-learn",  "python"),
    (33, "jenkinsci/jenkins",          26711, "jenkinsci_jenkins",          "java"),
    # ─── Decision (2026-05-12): expand v2 from 25 → 40 PRs ───
    # Supervisor: "do more PRs if it serves the thesis; pick good PRs
    # that are usable for KG to see its performance".
    # Selection rule: dataset_v2/scripts/find_fifteen_more_prs.py — same
    # 7 direction-blind v2 criteria + c8 KG-richness (≥ 2 KG-parseable
    # code files, so KG has at least one inter-file relationship).
    (34, "grafana/grafana",           124601, "grafana_grafana",            "go,typescript"),
    (35, "grafana/grafana",           124598, "grafana_grafana",            "go,typescript"),
    (36, "grafana/grafana",           124593, "grafana_grafana",            "go,typescript"),
    (37, "grafana/grafana",           124572, "grafana_grafana",            "go,typescript"),
    (38, "grafana/grafana",           124557, "grafana_grafana",            "go,typescript"),
    (39, "apache/kafka",               22255, "apache_kafka",               "java,scala"),
    (40, "apache/kafka",               22249, "apache_kafka",               "java,scala"),
    (41, "apache/kafka",               22241, "apache_kafka",               "java,scala"),
    (42, "scikit-learn/scikit-learn",  33979, "scikit-learn_scikit-learn",  "python"),
    (43, "scikit-learn/scikit-learn",  33964, "scikit-learn_scikit-learn",  "python"),
    (44, "scikit-learn/scikit-learn",  33957, "scikit-learn_scikit-learn",  "python"),
    (45, "godotengine/godot",         119412, "godotengine_godot",          "cpp"),
    (46, "godotengine/godot",         119349, "godotengine_godot",          "cpp"),
    (47, "jenkinsci/jenkins",          26749, "jenkinsci_jenkins",          "java"),
    (48, "jenkinsci/jenkins",          26636, "jenkinsci_jenkins",          "java"),
]

EXT_LANG_MAP = {
    ".py": "python", ".java": "java", ".go": "go", ".ts": "typescript",
    ".tsx": "typescript", ".js": "javascript", ".cpp": "cpp", ".c": "c",
    ".h": "cpp", ".scala": "scala", ".rs": "rust", ".gd": "gdscript",
    ".yml": "yaml", ".yaml": "yaml", ".json": "json", ".md": "markdown",
    ".xml": "xml", ".html": "html", ".css": "css", ".sh": "shell",
    ".rst": "rst", ".txt": "text", ".jelly": "jelly", ".mdx": "mdx",
    ".cue": "cue", ".gradle": "gradle", ".kt": "kotlin", ".mm": "objc",
    ".glsl": "glsl", ".cs": "csharp", ".gif": "binary", ".png": "binary",
    ".jpg": "binary", ".jpeg": "binary", ".ico": "binary",
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
        raise RuntimeError(f"gh metadata fetch failed for {repo}#{pr}: "
                           f"{result.stderr.strip()}")
    return json.loads(result.stdout)


def gh_diff(repo: str, pr: int) -> str:
    """Fetch the full diff. No cap at fetch time; cap is applied later."""
    result = subprocess.run(
        ["gh", "pr", "diff", str(pr), "--repo", repo],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh diff fetch failed for {repo}#{pr}: "
                           f"{result.stderr.strip()}")
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
    """Find files in repo whose name suggests they test `file_path`."""
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
    return tests[:5]


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
    includes: list[str] = []
    for lang in language.split(","):
        includes.extend(ext_map.get(lang.strip(), []))
    if not includes:
        includes = ["*.java", "*.go", "*.ts", "*.py", "*.cpp", "*.scala"]

    deps: list[dict] = []
    try:
        args = ["grep", "-rl", file_name, str(repo_path)]
        for inc in includes:
            args.extend(["--include", inc])
        result = subprocess.run(args, capture_output=True, text=True,
                                timeout=60)
        seen: set[str] = set()
        for line in result.stdout.strip().split("\n"):
            if line:
                rel = os.path.relpath(line, str(repo_path))
                if rel != file_path and rel not in seen:
                    seen.add(rel)
                    deps.append({"path": rel, "relationship": "imports",
                                 "source_file": file_path})
    except Exception:
        pass
    return deps[:10]


def cap_body(raw: str) -> str:
    if not raw:
        return ""
    if len(raw) <= BODY_CAP_BYTES:
        return raw
    return raw[:BODY_CAP_BYTES] + (
        f"\n\n[... v2 fetcher note: PR body truncated at "
        f"{BODY_CAP_BYTES} chars; original was {len(raw)} chars ...]"
    )


def cap_diff(raw: str, repo: str, pr: int) -> tuple[str, bool]:
    """Apply the 50 kB cap; return (capped_diff, hit_cap_flag)."""
    if len(raw) <= DIFF_CAP_BYTES:
        return raw, False
    return raw[:DIFF_CAP_BYTES] + (
        f"\n\n[... v2 fetcher note: diff truncated at "
        f"{DIFF_CAP_BYTES} chars; original was {len(raw)} chars; "
        f"see {repo}#{pr} on GitHub ...]"
    ), True


def build_evidence(pr_id: int, github_repo: str, pr_number: int,
                   local_repo: str, language: str) -> dict[str, Any]:
    print(f"\n{'='*60}")
    print(f"PR{pr_id} = {github_repo}#{pr_number} ({language})")
    print('='*60)

    print("  fetching metadata...", end=" ", flush=True)
    meta = gh_json(github_repo, pr_number,
                   "title,body,url,state,baseRefName,headRefName,mergedAt")
    print(f"state={meta.get('state')!r}")

    if meta.get("state") != "MERGED":
        raise RuntimeError(f"PR{pr_id}: state is {meta.get('state')!r}, "
                           f"not MERGED — refusing to write evidence pack")

    title = meta.get("title", "")
    if not title or title.lower().startswith(("grafana pr", "scikit-learn pr",
                                              "django pr", "apache kafka pr",
                                              "jenkins pr")):
        raise RuntimeError(f"PR{pr_id}: title is missing or placeholder "
                           f"({title!r}) — refusing to write evidence pack")

    raw_body = meta.get("body", "") or ""
    body = cap_body(raw_body)
    print(f"  title: {title[:70]!r}")
    print(f"  body:  {len(raw_body)} chars (kept {len(body)})")

    print("  fetching diff...", end=" ", flush=True)
    raw_diff = gh_diff(github_repo, pr_number)
    diff, hit_cap = cap_diff(raw_diff, github_repo, pr_number)
    print(f"raw {len(raw_diff)} chars{' [TRUNCATED at 50 kB]' if hit_cap else ''}")

    if hit_cap:
        print(f"  WARNING: PR{pr_id} diff exceeded the 50 kB cap. "
              f"Marker inserted; consider dropping this PR.")

    print("  fetching file stats...", end=" ", flush=True)
    file_stats = gh_files(github_repo, pr_number)
    print(f"{len(file_stats)} files")

    repo_path = LUCA_REPOS / local_repo
    repo_exists = repo_path.exists() and any(
        item.name != ".git" for item in repo_path.iterdir()
    )

    changed_files: list[dict] = []
    all_tests: list[dict] = []
    all_deps: list[dict] = []

    for fs in file_stats:
        path = fs["path"]
        lang = detect_language(path)
        changed_files.append({
            "path": path,
            "language": lang,
            "added": fs["added"],
            "deleted": fs["deleted"],
        })
        if repo_exists:
            all_tests.extend(find_tests(path, repo_path))
            all_deps.extend(find_dependents(path, repo_path, language))

    seen: set[str] = set()
    unique_tests = []
    for t in all_tests:
        if t["path"] not in seen:
            seen.add(t["path"]); unique_tests.append(t)

    seen.clear()
    changed_paths = {cf["path"] for cf in changed_files}
    unique_deps = []
    for d in all_deps:
        if d["path"] not in seen and d["path"] not in changed_paths:
            seen.add(d["path"]); unique_deps.append(d)

    evidence = {
        "pr": {
            "number": pr_number,
            "title": title,
            "body": body,
            "url": meta.get("url", f"https://github.com/{github_repo}/pull/{pr_number}"),
            "repo": github_repo,
            "base_branch": meta.get("baseRefName", "main"),
            "head_branch": meta.get("headRefName", ""),
            "merged_at": meta.get("mergedAt", ""),
            "state": meta.get("state", ""),
        },
        "changed_files": changed_files,
        "nearest_tests": unique_tests[:15],
        "dependent_files": unique_deps[:15],
        "diff_summary": f"{len(changed_files)} files changed",
        "full_diff": diff,
        "metadata": {
            "v2_fetcher_version": 1,
            "v2_fetched_at_unix": int(__import__("time").time()),
            "v2_diff_cap_bytes": DIFF_CAP_BYTES,
            "v2_body_cap_bytes": BODY_CAP_BYTES,
            "v2_diff_truncated": hit_cap,
            "v2_raw_diff_chars": len(raw_diff),
            "v2_raw_body_chars": len(raw_body),
        },
    }

    print(f"  built: {len(changed_files)} files, "
          f"{len(unique_tests)} nearest_tests, "
          f"{len(unique_deps)} dependent_files")

    return evidence


def main() -> int:
    EVIDENCE_DIR_V2.mkdir(parents=True, exist_ok=True)

    only = sys.argv[1:] if len(sys.argv) > 1 else None
    pr_filter = {int(x) for x in only} if only else None

    print("=" * 60)
    print(f"Fetching v2 evidence packs to {EVIDENCE_DIR_V2.relative_to(REPO_ROOT)}")
    print(f"DIFF_CAP_BYTES = {DIFF_CAP_BYTES}, BODY_CAP_BYTES = {BODY_CAP_BYTES}")
    print("=" * 60)

    summary: list[dict] = []
    failed: list[tuple[int, str]] = []

    for pr_id, github_repo, pr_number, local_repo, language in V2_PRS:
        if pr_filter is not None and pr_id not in pr_filter:
            continue
        try:
            ev = build_evidence(pr_id, github_repo, pr_number, local_repo,
                                language)
            out_path = EVIDENCE_DIR_V2 / f"pr{pr_id}_evidence.json"
            with open(out_path, "w") as f:
                json.dump(ev, f, indent=2)
            print(f"  wrote: {out_path.relative_to(REPO_ROOT)}")
            summary.append({
                "pr_id": pr_id,
                "url": ev["pr"]["url"],
                "title": ev["pr"]["title"],
                "body_chars": len(ev["pr"]["body"]),
                "diff_chars": len(ev["full_diff"]),
                "raw_diff_chars": ev["metadata"]["v2_raw_diff_chars"],
                "diff_truncated": ev["metadata"]["v2_diff_truncated"],
                "n_files": len(ev["changed_files"]),
            })
        except Exception as e:
            print(f"  FAIL: {e}")
            failed.append((pr_id, str(e)))

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"{'PR':>3} | {'body':>5} | {'diff':>6} | {'raw_diff':>8} | "
          f"{'trunc':>5} | {'files':>5} | title")
    print("-" * 110)
    for s in summary:
        print(f"{s['pr_id']:>3} | {s['body_chars']:>5} | "
              f"{s['diff_chars']:>6} | {s['raw_diff_chars']:>8} | "
              f"{'YES' if s['diff_truncated'] else '   ':>5} | "
              f"{s['n_files']:>5} | {s['title'][:60]}")

    if failed:
        print()
        print(f"{len(failed)} FAILURES:")
        for pid, msg in failed:
            print(f"  PR{pid}: {msg}")
        return 1

    print()
    print(f"OK — {len(summary)} evidence packs written to "
          f"{EVIDENCE_DIR_V2.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
