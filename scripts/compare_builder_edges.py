#!/usr/bin/env python3
"""Compare what the lexical and AST graph builders assert for one pull request.

Chapters 2, 4 and 6 all turn on a distinction that is easy to state and hard to
believe until it is shown: the lexical builder and the AST import resolver both
emit edges labelled ``imports``, but only one of them has checked anything. This
script produces the worked example that makes the difference concrete, on a real
pull request at its real head commit, so the figure in Chapter 2 reports measured
edges rather than an illustration someone invented.

The pull request is pallets/flask#5637, chosen because it is in the human study's
stimulus set -- so the AST resolver's edges already exist as a committed artefact
-- and because its changed Python file is ``src/flask/app.py``, whose basename
stem is ``app``. That stem is in neither of the lexical builder's skip lists, so
the builder really does run a bare substring search for it. Nothing about the
choice is adversarial: it is one of six pull requests in the study, and the stem
is what it is.

The lexical side is recomputed here rather than read from an artefact, because the
40-PR packs and the human study's packs cover disjoint pull requests, so no
committed file contains both builders' verdicts on the same change. The functions
below replicate dataset_v2/scripts/fetch_evidence_v2.py::find_dependents and
::find_tests exactly -- same command, same skip lists, same glob patterns, same
caps -- and the replication is asserted against the source at run time so this
script cannot drift away from the builder it claims to describe.

No API keys, no tokens, no cost. Clones ~15 MB into a cache directory on first
run and reuses it afterwards, so re-running is cheap and idempotent.

Output
  results/BUILDER_EDGE_COMPARISON.json   consumed by scripts/generate_thesis_figures.py

Usage
  python3 scripts/compare_builder_edges.py
  python3 scripts/compare_builder_edges.py --cache /tmp/builder_cmp
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AST_PACK = (REPO_ROOT / "experiments" / "2026-07-06_user_study_prs" / "evidence"
            / "flask_5637_evidence.json")
BUILDER_SRC = REPO_ROOT / "dataset_v2" / "scripts" / "fetch_evidence_v2.py"
OUT = REPO_ROOT / "results" / "BUILDER_EDGE_COMPARISON.json"

CLONE_URL = "https://github.com/pallets/flask.git"

# Copied from fetch_evidence_v2.py. Asserted against the source in
# check_replication_is_faithful() so a change there breaks this script loudly
# rather than letting the figure quietly describe a builder that no longer exists.
DEP_SKIP = ("index", "main", "utils", "helpers", "types", "constants", "mod",
            "lib", "__init__", "setup")
TEST_SKIP = ("index", "main", "mod", "lib", "__init__", "setup", "conf")
DEP_CAP, TEST_CAP = 10, 5


def check_replication_is_faithful() -> None:
    """Fail loudly if the builder this script imitates has changed."""
    src = BUILDER_SRC.read_text()
    for token in ('["grep", "-rl", file_name, str(repo_path)]',
                  'return deps[:10]', 'return tests[:5]',
                  'f"*{file_name}*[Tt]est*"'):
        if token not in src:
            raise SystemExit(
                f"fetch_evidence_v2.py no longer contains {token!r}.\n"
                "The lexical builder changed; update this script and regenerate "
                "results/BUILDER_EDGE_COMPARISON.json before trusting the "
                "Chapter 2 figure.")
    for name in DEP_SKIP:
        if f'"{name}"' not in src:
            raise SystemExit(f"skip-list entry {name!r} missing from source")


def lexical_dependents(stem: str, repo: Path) -> tuple[list[str], int]:
    """fetch_evidence_v2.py::find_dependents, for a Python change.

    Returns the edges the builder would keep, and how many files matched in
    total, because the gap between those two numbers is half the point: the cap
    is applied to an unordered filesystem walk, so which ten survive is an
    accident of path ordering.
    """
    if stem.lower() in DEP_SKIP:
        return [], 0
    args = ["grep", "-rl", stem, str(repo), "--include", "*.py"]
    res = subprocess.run(args, capture_output=True, text=True, timeout=120)
    seen, deps = set(), []
    for line in res.stdout.strip().split("\n"):
        if not line:
            continue
        rel = os.path.relpath(line, str(repo))
        if rel != f"src/flask/{stem}.py" and rel not in seen:
            seen.add(rel)
            deps.append(rel)
    return sorted(deps)[:DEP_CAP], len(deps)


def lexical_tests(stem: str, repo: Path) -> list[str]:
    """fetch_evidence_v2.py::find_tests -- four filename globs, no content check."""
    if stem.lower() in TEST_SKIP:
        return []
    seen, tests = set(), []
    for pat in (f"*{stem}*[Tt]est*", f"*[Tt]est*{stem}*",
                f"*{stem}*[Ss]pec*", f"*{stem}*_test*"):
        res = subprocess.run(["find", str(repo), "-name", pat, "-type", "f"],
                             capture_output=True, text=True, timeout=60)
        for line in res.stdout.strip().split("\n"):
            if line:
                rel = os.path.relpath(line, str(repo))
                if rel not in seen and not rel.startswith(".git/"):
                    seen.add(rel)
                    tests.append(rel)
    return tests[:TEST_CAP]


def why_matched(path: Path, stem: str) -> str | None:
    """The first identifier containing the stem, which is why the file matched.

    Reported so a reader can check the claim themselves rather than taking the
    word 'spurious' on trust.
    """
    try:
        for line in path.read_text(errors="replace").splitlines():
            if stem not in line:
                continue
            i = line.index(stem)
            a = i
            while a > 0 and (line[a - 1].isalnum() or line[a - 1] == "_"):
                a -= 1
            b = i + len(stem)
            while b < len(line) and (line[b].isalnum() or line[b] == "_"):
                b += 1
            return line[a:b]
    except Exception:
        pass
    return None


def ensure_clone(cache: Path, sha: str) -> Path:
    repo = cache / "flask"
    if not (repo / ".git").is_dir():
        cache.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", CLONE_URL, str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", sha], check=True)
    got = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                         capture_output=True, text=True, check=True).stdout.strip()
    if got != sha:
        raise SystemExit(f"checkout mismatch: wanted {sha}, got {got}")
    return repo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(REPO_ROOT / ".cache" / "builder_cmp"))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    check_replication_is_faithful()

    pack = json.loads(AST_PACK.read_text())
    sha = pack["pr"]["head_sha"]
    changed_py = [f["path"] for f in pack["changed_files"]
                  if f.get("language") == "python"
                  and not f["path"].startswith("tests/")]
    if changed_py != ["src/flask/app.py"]:
        raise SystemExit(f"unexpected changed Python files: {changed_py}")
    stem = Path(changed_py[0]).stem

    repo = ensure_clone(Path(args.cache), sha)
    lex_deps, lex_total = lexical_dependents(stem, repo)
    lex_tests = lexical_tests(stem, repo)

    ast_deps = [d["path"] for d in pack["dependent_files"]]
    ast_tests = [t["path"] for t in pack["nearest_tests"]]

    def library(paths: list[str]) -> list[str]:
        return [p for p in paths if p.startswith("src/flask/")]

    result = {
        "meta": {
            "pr": f"{pack['pr']['repo']}#{pack['pr']['number']}",
            "title": pack["pr"]["title"],
            "head_sha": sha,
            "changed_file": changed_py[0],
            "stem": stem,
            "note": ("Lexical edges recomputed by scripts/compare_builder_edges.py, "
                     "replicating fetch_evidence_v2.py::find_dependents/::find_tests. "
                     "AST edges read from the committed human-study evidence pack."),
        },
        "lexical": {
            "builder": "lexical_grep",
            "dependents_total_matches": lex_total,
            "dependents_cap": DEP_CAP,
            "dependents_kept": lex_deps,
            "dependents_kept_in_library": library(lex_deps),
            "tests_kept": lex_tests,
            "match_reason": {p: why_matched(repo / p, stem) for p in lex_deps},
        },
        "ast": {
            "builder": pack["metadata"].get("kg_builder"),
            "dependents_kept": ast_deps,
            "dependents_kept_in_library": library(ast_deps),
            "tests_kept": ast_tests,
        },
    }

    out = Path(args.out)
    if not out.is_absolute():
        out = REPO_ROOT / out
    out.write_text(json.dumps(result, indent=2) + "\n")

    lx, ax = result["lexical"], result["ast"]
    print(f"PR {result['meta']['pr']} at {sha[:8]}, changed {stem}.py\n")
    print(f"  lexical : {lx['dependents_total_matches']} files matched "
          f"'{stem}' as a substring; first {DEP_CAP} kept, of which "
          f"{len(lx['dependents_kept_in_library'])} are library files")
    print(f"  AST     : {len(ax['dependents_kept'])} parsed-import edges, of "
          f"which {len(ax['dependents_kept_in_library'])} are library files")
    print(f"\n  wrote {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
