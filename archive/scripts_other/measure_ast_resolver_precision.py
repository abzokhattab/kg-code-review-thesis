#!/usr/bin/env python3
"""Measure precision of the human-study AST import resolver.

The thesis reports lexical (grep) dependent-edge precision as 10.2%
(`results/BUILDER_VOLUME_PRECISION.md`).  That number is an upper bound: a
Python edge counts as confirmed if any import's final component matches the
changed file's stem (`scripts/compare_kg_builder_volume_precision.py::
classify_grep_edge`).  This script applies the same test to every displayed
`dependent_files` edge the AST import resolver emitted for the six human-study
pull requests, so the three builders sit on one scale.

A second, stricter check answers the question the human-study write-up actually
turns on: does the flagged file import the *changed module* in a way that could
plausibly reach a changed function (module-level import of the dotted name, or
an ImportFrom of a function the diff added or modified)?  That is not the
headline number; it is reported beside it so the two questions cannot be
conflated.

No model calls.  Cost: $0.  Checkouts the three study repos at each pack's
head SHA and restores the previous HEAD afterwards.

Output
    results/AST_RESOLVER_PRECISION.{md,json}

Usage
    python3 scripts/measure_ast_resolver_precision.py
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
STUDY = REPO_ROOT / "experiments" / "2026-07-06_user_study_prs"
EVIDENCE = STUDY / "evidence"
REPOS = STUDY / "pr_hunt" / "repos"
OUT_JSON = REPO_ROOT / "results" / "AST_RESOLVER_PRECISION.json"
OUT_MD = REPO_ROOT / "results" / "AST_RESOLVER_PRECISION.md"

# Copied from experiments/2026-07-06_user_study_prs/build_evidence.py so the
# precision check reconstructs the same module identifiers the builder used.
PRS = {
    "requests_7433": dict(repo_dir="psf_requests", repo="psf/requests"),
    "flask_5637": dict(repo_dir="pallets_flask", repo="pallets/flask"),
    "click_3493": dict(repo_dir="pallets_click", repo="pallets/click"),
    "requests_7328": dict(repo_dir="psf_requests", repo="psf/requests"),
    "flask_5799": dict(repo_dir="pallets_flask", repo="pallets/flask"),
    "click_3578": dict(repo_dir="pallets_click", repo="pallets/click"),
}


def module_names(path: str) -> set[str]:
    """Module identifiers a file can be imported as: stem and dotted package path.

    Verbatim from build_evidence.py.
    """
    stem = Path(path).stem
    parts = Path(path).with_suffix("").parts
    names = {stem}
    if "src" in parts:
        i = parts.index("src")
        names.add(".".join(parts[i + 1 :]))
    return {n for n in names if n not in ("__init__", "__main__")}


def python_imported_names(path: Path) -> set[str] | None:
    """Final components of every module named by a real import statement.

    Verbatim from compare_kg_builder_volume_precision.py::python_imported_names
    so the headline precision uses the same classifier as the lexical 10.2%.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names.update(a.name.split("."))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.update(node.module.split("."))
            for a in node.names:
                names.add(a.name)
    return names


def _package_of(path: Path, repo: Path) -> list[str]:
    """Dotted package parts of a file under src/, e.g. flask/logging.py -> ['flask']."""
    rel = path.relative_to(repo).with_suffix("")
    parts = list(rel.parts)
    if "src" in parts:
        parts = parts[parts.index("src") + 1 :]
    if parts and parts[-1] != "__init__":
        parts = parts[:-1]
    return parts


def imported_modules(path: Path, repo: Path) -> tuple[set[str], set[str]] | None:
    """Return (resolved imported module strings, ImportFrom alias/name set).

    Relative imports are resolved against the file's package so
    `from .app import Flask` in src/flask/logging.py counts as flask.app.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None
    pkg = _package_of(path, repo)
    mods: set[str] = set()
    from_names: set[str] = set()

    def abs_module(node: ast.ImportFrom) -> str:
        if node.level:
            parent = pkg[: max(0, len(pkg) - (node.level - 1))]
            parts = list(parent)
            if node.module:
                parts.extend(node.module.split("."))
            return ".".join(p for p in parts if p)
        return node.module or ""

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mods.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            resolved = abs_module(node)
            if resolved:
                mods.add(resolved)
            for a in node.names:
                from_names.add(a.name)
                if a.name != "*" and resolved:
                    mods.add(f"{resolved}.{a.name}")
    return mods, from_names


def changed_function_names(diff_text: str, changed_py: list[str]) -> set[str]:
    """Function names the diff added or touched, plus defs in changed files.

    Hunk headers of the form `@@ ... @@ def foo` and added lines `+def foo`.
    Conservative: only syntactically-def-like names.
    """
    names: set[str] = set()
    def_re = re.compile(r"\bdef\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
    for line in diff_text.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("@@") or line.startswith("+"):
            for m in def_re.finditer(line):
                names.add(m.group(1))
    return names


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def checkout(repo: Path, sha: str) -> str:
    """Checkout sha; return the previous HEAD so the caller can restore it."""
    prev = git(repo, "rev-parse", "HEAD").stdout.strip()
    fetched = git(repo, "cat-file", "-t", sha)
    if fetched.returncode != 0:
        git(repo, "fetch", "--depth", "1", "origin", sha)
    r = git(repo, "checkout", "-q", sha)
    if r.returncode != 0:
        raise SystemExit(f"checkout {sha} in {repo.name} failed: {r.stderr}")
    return prev


def classify_stem(edge: dict[str, Any], repo: Path) -> str:
    """Generous stem match: same test as classify_grep_edge for Python."""
    src = edge.get("source_file") or ""
    dst = edge.get("path") or ""
    if not dst.endswith(".py"):
        return "unverifiable"
    f = repo / dst
    if not f.exists():
        return "unverifiable"
    names = python_imported_names(f)
    if names is None:
        return "unverifiable"
    stem = Path(src).stem  # 'app', or 'flask.helpers' when no suffix
    # source_file is a module id, not a path: last dotted component is the stem
    # the lexical classifier would have used for a file named <stem>.py.
    last = src.rsplit(".", 1)[-1]
    return "confirmed" if (stem in names or last in names) else "refuted"


def classify_module_reach(
    edge: dict[str, Any],
    repo: Path,
    targets: set[str],
    changed_funcs: set[str],
) -> dict[str, Any]:
    """Does the flagged file import the changed module, or a changed function?"""
    dst = edge.get("path") or ""
    f = repo / dst
    parsed = imported_modules(f, repo) if f.exists() and dst.endswith(".py") else None
    if parsed is None:
        return {"verdict": "unverifiable", "matched_module": None, "matched_func": None}
    mods, from_names = parsed
    matched_mod = None
    for t in sorted(targets, key=len, reverse=True):
        if t in mods or any(m == t or m.endswith("." + t) for m in mods):
            matched_mod = t
            break
        # from package import module  (ImportFrom names the module as an alias)
        if t.split(".")[-1] in from_names and any(
            m.endswith("." + t.rsplit(".", 1)[0]) or m == t.rsplit(".", 1)[0]
            for m in mods
            if "." in t
        ):
            matched_mod = t
            break
    matched_fn = sorted(changed_funcs & from_names)
    if matched_mod or matched_fn:
        return {
            "verdict": "confirmed",
            "matched_module": matched_mod,
            "matched_func": matched_fn[0] if matched_fn else None,
        }
    return {"verdict": "refuted", "matched_module": None, "matched_func": None}


def main() -> None:
    sys.path.insert(0, str(REPO_ROOT))
    rows: list[dict[str, Any]] = []
    restored: dict[Path, str] = {}

    try:
        for key, cfg in PRS.items():
            pack = json.loads((EVIDENCE / f"{key}_evidence.json").read_text())
            repo = REPOS / cfg["repo_dir"]
            if not repo.exists():
                raise SystemExit(f"missing checkout {repo}")
            sha = pack["pr"]["head_sha"]
            if repo not in restored:
                restored[repo] = checkout(repo, sha)
            elif git(repo, "rev-parse", "HEAD").stdout.strip() != sha:
                checkout(repo, sha)

            changed_py = [
                c["path"]
                for c in pack.get("changed_files", [])
                if c.get("path", "").endswith(".py")
                and not c["path"].startswith(("tests/", "docs/"))
            ]
            targets: set[str] = set()
            for p in changed_py:
                targets |= module_names(p)
            funcs = changed_function_names(pack.get("full_diff", ""), changed_py)

            for kind, field in (("dependent", "dependent_files"), ("test", "nearest_tests")):
                for edge in pack.get(field, []):
                    stem = classify_stem(edge, repo)
                    reach = classify_module_reach(edge, repo, targets, funcs)
                    rows.append({
                        "pack": key,
                        "repo": cfg["repo"],
                        "pr": pack["pr"]["number"],
                        "kind": kind,
                        "path": edge.get("path"),
                        "source_file": edge.get("source_file"),
                        "relationship": edge.get("relationship"),
                        "stem_match": stem,
                        "module_reach": reach["verdict"],
                        "matched_module": reach["matched_module"],
                        "matched_func": reach["matched_func"],
                        "changed_funcs": sorted(funcs),
                        "targets": sorted(targets),
                    })
    finally:
        for repo, prev in restored.items():
            if prev:
                git(repo, "checkout", "-q", prev)

    deps = [r for r in rows if r["kind"] == "dependent"]
    tests = [r for r in rows if r["kind"] == "test"]

    def tally(subset: list[dict[str, Any]], field: str) -> dict[str, Any]:
        c = Counter(r[field] for r in subset)
        checked = c["confirmed"] + c["refuted"]
        return {
            "n": len(subset),
            "confirmed": c["confirmed"],
            "refuted": c["refuted"],
            "unverifiable": c["unverifiable"],
            "checked": checked,
            "precision": round(c["confirmed"] / checked, 4) if checked else None,
        }

    by_pack: dict[str, dict[str, Any]] = {}
    for key in PRS:
        subset = [r for r in deps if r["pack"] == key]
        by_pack[key] = {
            "n_dependents": len(subset),
            "stem": tally(subset, "stem_match"),
            "module_reach": tally(subset, "module_reach"),
        }

    n_func = sum(1 for r in deps if r.get("matched_func"))
    summary = {
        "n_packs": len(PRS),
        "n_dependent_edges": len(deps),
        "n_test_edges": len(tests),
        "stem_match_dependents": tally(deps, "stem_match"),
        "module_reach_dependents": tally(deps, "module_reach"),
        "function_import_dependents": {
            "n": len(deps),
            "confirmed": n_func,
            "precision": round(n_func / len(deps), 4) if deps else None,
        },
        "stem_match_tests": tally(tests, "stem_match"),
        "module_reach_tests": tally(tests, "module_reach"),
        "by_pack": by_pack,
        "method": (
            "Headline precision = generous stem match, identical to "
            "compare_kg_builder_volume_precision.py::classify_grep_edge "
            "(the 10.2% lexical figure).  Module-reach is the stricter "
            "check: the flagged file imports the changed module's dotted "
            "name or an ImportFrom of a function the diff added/modified."
        ),
        "builder": "experiments/2026-07-06_user_study_prs/build_evidence.py",
        "model_calls": 0,
    }

    OUT_JSON.write_text(json.dumps({"summary": summary, "edges": rows}, indent=2))
    write_md(summary, rows)
    s = summary["stem_match_dependents"]
    print(
        f"AST resolver stem-match precision  {s['precision']:.1%}  "
        f"(n={s['n']} displayed dependent edges, "
        f"{s['confirmed']} confirmed / {s['checked']} checked)"
    )
    r = summary["module_reach_dependents"]
    print(
        f"AST resolver module-reach          {r['precision']:.1%}  "
        f"({r['confirmed']} confirmed / {r['checked']} checked)"
    )
    print(f"wrote {OUT_JSON.relative_to(REPO_ROOT)}")
    print(f"wrote {OUT_MD.relative_to(REPO_ROOT)}")


def write_md(summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    s = summary["stem_match_dependents"]
    r = summary["module_reach_dependents"]
    st = summary["stem_match_tests"]
    lines = [
        "# AST import resolver precision (human-study packs)",
        "",
        "Builder: `experiments/2026-07-06_user_study_prs/build_evidence.py` "
        "(Python `ast.Import` / `ast.ImportFrom` at each PR head SHA).",
        f"Census, not a sample: every displayed `dependent_files` edge in the "
        f"six committed packs, n = {s['n']}.  Cost: $0.",
        "",
        "## Headline (same classifier as lexical 10.2%)",
        "",
        "A Python edge is confirmed if any import's final component matches "
        "the builder's `source_file` stem.  That is "
        "`scripts/compare_kg_builder_volume_precision.py::classify_grep_edge`, "
        "the test behind the lexical 10.2% figure.",
        "",
        "| Builder | edges checked | confirmed | refuted | unverifiable | precision |",
        "|---|---:|---:|---:|---:|---:|",
        f"| AST import resolver (human study) | {s['checked']} | "
        f"{s['confirmed']} | {s['refuted']} | {s['unverifiable']} | "
        f"{s['precision']:.1%} |",
        f"| lexical grep (40-PR set, for scale) | 177 | 18 | 56 | 232 | 10.2% |",
        "",
        "The lexical row is quoted from `results/BUILDER_VOLUME_PRECISION.md` "
        "and is not recomputed here.  Its unverifiable count is high because "
        "most 40-PR edges are not Python-to-Python; every human-study edge is.",
        "",
        "## Module-reach (stricter; not the comparable number)",
        "",
        "Confirmed only if the flagged file imports the changed module's dotted "
        "name (`flask.app`, not a coincidental identifier `app`) or an "
        "`ImportFrom` of a function the diff added or modified.  This is the "
        "check that answers 'does the import plausibly reach the changed function?' "
        "at module granularity.",
        "",
        f"| Check | n | confirmed | refuted | precision |",
        "|---|---:|---:|---:|---:|",
        f"| generous stem match (headline) | {s['n']} | {s['confirmed']} | "
        f"{s['refuted']} | {s['precision']:.1%} |",
        f"| module-reach | {r['n']} | {r['confirmed']} | {r['refuted']} | "
        f"{r['precision']:.1%} |",
        f"| ImportFrom of a changed function | {summary['function_import_dependents']['n']} | "
        f"{summary['function_import_dependents']['confirmed']} | "
        f"{summary['function_import_dependents']['n'] - summary['function_import_dependents']['confirmed']} | "
        f"{summary['function_import_dependents']['precision']:.1%} |",
        f"| generous stem match, test edges | {st['n']} | {st['confirmed']} | "
        f"{st['refuted']} | {st['precision']:.1%} |",
        "",
        "## Per-pack dependent edges",
        "",
        "| Pack | n | stem confirmed | module-reach confirmed |",
        "|---|---:|---:|---:|",
    ]
    for key, rec in summary["by_pack"].items():
        lines.append(
            f"| {key} | {rec['n_dependents']} | "
            f"{rec['stem']['confirmed']}/{rec['stem']['n']} | "
            f"{rec['module_reach']['confirmed']}/{rec['module_reach']['n']} |"
        )
    lines += [
        "",
        "## What this does not establish",
        "",
        "Module-level import precision is not function-level relevance.  A file "
        "that imports `flask.app` can still be unaffected by a seven-line change "
        "to `Flask.create_url_adapter`, which is the distinction the human study "
        "raters drew on flask#5637.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
