#!/usr/bin/env python3
"""
screen_pr_crossfile_fanout.py — Direction-blind screen for human-study PR
candidates that have REAL cross-file caller fan-out.

Motivation (human_eval_v3 RQ3): every prior human-study PR selection filtered
on *review-text* overlap (a downstream, outcome-adjacent property). The
precondition for a repository knowledge graph to beat a diff-only baseline is
a *structural* property of the CHANGE ITSELF: the changed symbols must have
in-repo callers/callees that are NOT in the diff, so a diff-only reviewer
would plausibly miss them while a call-graph KG names them. This screen
measures that property directly, before any review is generated or judged.

For ONE repo it:
  1. lists recent merged PRs via `gh`,
  2. applies the same direction-blind c1-c7 criteria as
     dataset_v2/scripts/find_seven_more_prs.py (merged, not-revert,
     has-code-change, 100% KG-parseable code files, diff <= ~50kB,
     body >= 100 chars, not already in the 40-PR dataset),
  3. for each passer, parses the PR diff, extracts the definitions it
     changes (language-aware), and counts how many OTHER files in the
     CLONED working tree reference those symbols via `git grep` (grounded
     fan-out — the references provably exist in the repo).

No LLM-judge output, no mode-favouring metric, and no generated review is
consulted. Fully reproducible from the GitHub API + the local clone.

Usage (one repo):
  python3 scripts/screen_pr_crossfile_fanout.py \
      --repo grafana/grafana --clone luca_repos/grafana_grafana --limit 80

Output: human_eval_v3/analysis/fanout/<owner__name>.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "human_eval_v3" / "analysis" / "fanout"

# Tree-sitter / KG-parseable code extensions (per find_seven_more_prs.py).
KG_EXTS = {".py", ".pyi", ".java", ".scala", ".cpp", ".cc", ".c", ".h",
           ".hpp", ".go", ".ts", ".tsx", ".js", ".jsx", ".gd", ".rs"}
NON_KG_CODE_EXTS = {".jelly", ".kt", ".swift", ".m", ".mm", ".rb", ".php",
                    ".elm", ".dart", ".cue", ".gradle", ".groovy"}
NON_CODE_EXTS = {".md", ".rst", ".txt", ".mdx", ".json", ".yaml", ".yml",
                 ".toml", ".ini", ".env", ".xml", ".html", ".css", ".scss",
                 ".lock", ".sum", ".snap", ".golden", ".results", ".png",
                 ".gif", ".jpg", ".jpeg", ".ico", ".svg", ".webp",
                 ".gitignore", ".dockerignore"}

# PRs already in the 40-PR dataset_v2 (exclude — Option B is *outside* the 40).
EXISTING = {
    "grafana/grafana": {67809, 69259, 78399, 95949, 97224, 98123, 124557},
    "apache/kafka": {14778, 17441, 17594, 18330, 22195, 22241, 22249},
    "godotengine/godot": {68625, 73144, 89111},
    "scikit-learn/scikit-learn": {22365, 22643, 26836, 33918, 33957},
    "jenkinsci/jenkins": {6229, 9002, 26749},
    "django/django": {18322, 18523, 18540},
    "microsoft/TypeScript": {57375},
}

# Symbols too generic to be a meaningful fan-out signal.
STOP = {"build", "close", "value", "index", "result", "data", "test", "setup",
        "config", "start", "state", "error", "count", "check", "parse", "name",
        "type", "size", "getinstance", "tostring", "equals", "hashcode", "main",
        "init", "create", "update", "delete", "remove", "handle", "process",
        "render", "format", "validate", "clone", "copy", "reset", "clear"}

DEF_PATTERNS = {
    "py":   [r"^\s*def\s+([A-Za-z_]\w+)", r"^\s*class\s+([A-Za-z_]\w+)"],
    "java": [r"\b(?:public|private|protected|static|final|abstract|synchronized|\s)+[\w<>\[\],.?]+\s+([A-Za-z_]\w+)\s*\(",
             r"\b(?:class|interface|enum|record)\s+([A-Za-z_]\w+)"],
    "scala":[r"\bdef\s+([A-Za-z_]\w+)", r"\b(?:class|object|trait)\s+([A-Za-z_]\w+)"],
    "cpp":  [r"\b([A-Za-z_]\w+)\s*\([^;]*\)\s*(?:const)?\s*\{",
             r"\b(?:class|struct)\s+([A-Za-z_]\w+)"],
    "go":   [r"\bfunc\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w+)\s*\(",
             r"\btype\s+([A-Za-z_]\w+)\s"],
    "ts":   [r"\bfunction\s+([A-Za-z_]\w+)", r"\b(?:class|interface|enum|type)\s+([A-Za-z_]\w+)",
             r"\bexport\s+const\s+([A-Za-z_]\w+)", r"^\s*(?:public|private|protected)?\s*([A-Za-z_]\w+)\s*\("],
}
EXT_LANG = {".py": "py", ".pyi": "py", ".java": "java", ".scala": "scala",
            ".cpp": "cpp", ".cc": "cpp", ".c": "cpp", ".h": "cpp", ".hpp": "cpp",
            ".go": "go", ".ts": "ts", ".tsx": "ts", ".js": "ts", ".jsx": "ts"}


def gh(args: list[str]) -> str:
    r = subprocess.run(["gh"] + args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)}: {r.stderr.strip()[:200]}")
    return r.stdout


def ext_of(path: str) -> str:
    return "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""


def list_recent_merged(repo: str, n: int, merged_before: str | None,
                        merged_after: str | None) -> list[dict]:
    args = ["pr", "list", "--repo", repo, "--state", "merged",
            "--limit", str(n),
            "--json", "number,title,body,additions,deletions,changedFiles,mergedAt,url"]
    if merged_before or merged_after:
        lo = merged_after or "2000-01-01"
        hi = merged_before or "2100-01-01"
        # Restrict to PRs merged inside the window so the frozen clone we grep
        # actually contains the changed code (clones are pinned at fixed SHAs).
        args += ["--search", f"merged:{lo}..{hi} sort:updated-desc"]
    return json.loads(gh(args))


def metadata_ok(pr: dict, repo: str) -> bool:
    body = (pr.get("body") or "").strip()
    title = pr.get("title", "") or ""
    if pr["number"] in EXISTING.get(repo, set()):
        return False
    if len(body) < 100:
        return False
    if re.match(r"^(revert|reapply)\b", title, re.IGNORECASE):
        return False
    if re.match(r"^(bump|chore[: ]|docs?[: ]|doc[: ]|update dependency|"
                r"update peer dependency|i18n|l10n|translations?:)", title, re.IGNORECASE):
        return False
    est = (pr.get("additions", 0) + pr.get("deletions", 0)) * 80
    if est > 60_000 or est < 1_500:
        return False
    nch = pr.get("changedFiles", 0)
    return 1 <= nch <= 25


def parse_diff(patch: str) -> tuple[list[str], dict[str, list[str]]]:
    """Return (changed_paths, {path: [changed symbols]})."""
    paths: list[str] = []
    syms: dict[str, list[str]] = {}
    cur = None
    lang = None
    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            cur = line[6:]
            paths.append(cur)
            lang = EXT_LANG.get(ext_of(cur))
            syms.setdefault(cur, [])
            continue
        if cur is None or lang is None:
            continue
        # look at added or context lines (definitions being touched)
        if line.startswith(("+", " ")) and not line.startswith("+++"):
            content = line[1:]
            for pat in DEF_PATTERNS.get(lang, []):
                for m in re.finditer(pat, content):
                    name = m.group(1)
                    if len(name) >= 4 and name.lower() not in STOP:
                        syms[cur].append(name)
    return paths, syms


def git_grep_files(clone: Path, symbol: str, exclude: set[str]) -> int:
    """Distinct files (excluding the changed paths) that reference `symbol`."""
    r = subprocess.run(
        ["git", "-C", str(clone), "grep", "-l", "--word-regexp",
         "--fixed-strings", "-e", symbol],
        capture_output=True, text=True)
    if r.returncode not in (0, 1):  # 1 = no matches
        return 0
    files = {f for f in r.stdout.splitlines() if f and f not in exclude}
    return len(files)


def screen_repo(repo: str, clone: Path, limit: int, merged_before: str | None,
                merged_after: str | None, max_syms: int = 12) -> dict:
    prs = list_recent_merged(repo, limit, merged_before, merged_after)
    out = []
    for pr in prs:
        if not metadata_ok(pr, repo):
            continue
        try:
            patch = gh(["pr", "diff", str(pr["number"]), "--repo", repo])
        except RuntimeError:
            continue
        paths, syms = parse_diff(patch)
        code_paths = [p for p in paths if ext_of(p) in KG_EXTS]
        non_kg = [p for p in paths if ext_of(p) in NON_KG_CODE_EXTS]
        if non_kg or not code_paths:  # c4: 100% KG-parseable code
            continue
        exclude = set(paths)
        all_syms = []
        for p in code_paths:
            all_syms.extend(syms.get(p, []))
        # dedup, keep most-frequent-first, cap for speed
        uniq = sorted(set(all_syms), key=lambda s: (-all_syms.count(s), s))[:max_syms]
        per_sym = {}
        blast_files: set[str] = set()
        for s in uniq:
            r = subprocess.run(
                ["git", "-C", str(clone), "grep", "-l", "--word-regexp",
                 "--fixed-strings", "-e", s],
                capture_output=True, text=True)
            if r.returncode not in (0, 1):
                continue
            fs = {f for f in r.stdout.splitlines() if f and f not in exclude}
            per_sym[s] = len(fs)
            blast_files |= fs
        n_ext = len(blast_files)
        n_syms_hit = sum(1 for v in per_sym.values() if v > 0)
        top = sorted(per_sym.items(), key=lambda kv: -kv[1])[:6]
        out.append({
            "repo": repo,
            "number": pr["number"],
            "title": pr["title"],
            "url": pr.get("url"),
            "merged_at": pr.get("mergedAt"),
            "n_changed_files": len(paths),
            "n_code_files": len(code_paths),
            "n_changed_symbols": len(set(all_syms)),
            "n_symbols_with_external_refs": n_syms_hit,
            "external_file_fanout": n_ext,   # blast radius (union across symbols)
            "top_symbols": top,
            "exts": sorted({ext_of(p) for p in paths}),
        })
        print(f"    #{pr['number']:>6}  fanout={n_ext:>4}  syms={n_syms_hit}/{len(set(all_syms))}  "
              f"{pr['title'][:56]}", flush=True)
    out.sort(key=lambda c: -c["external_file_fanout"])
    return {"repo": repo, "clone": str(clone), "n_screened": len(prs),
            "n_candidates": len(out), "candidates": out}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--clone", required=True)
    ap.add_argument("--limit", type=int, default=80)
    ap.add_argument("--merged-before", default=None,
                    help="only PRs merged on/before this date (YYYY-MM-DD)")
    ap.add_argument("--merged-after", default=None,
                    help="only PRs merged on/after this date (YYYY-MM-DD)")
    a = ap.parse_args()
    clone = REPO_ROOT / a.clone if not Path(a.clone).is_absolute() else Path(a.clone)
    if not (clone / ".git").exists():
        sys.exit(f"not a git clone: {clone}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    res = screen_repo(a.repo, clone, a.limit, a.merged_before, a.merged_after)
    slug = a.repo.replace("/", "__")
    (OUT_DIR / f"{slug}.json").write_text(json.dumps(res, indent=2))
    print(f"==> {a.repo}: {res['n_candidates']} candidates -> "
          f"{OUT_DIR.relative_to(REPO_ROOT)}/{slug}.json")


if __name__ == "__main__":
    main()
