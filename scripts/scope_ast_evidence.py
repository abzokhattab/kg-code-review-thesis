#!/usr/bin/env python3
"""Change-scope an AST evidence pack.

Reads ``data/luca_prs_fixed_ast/pr{N}_evidence.json`` and rewrites
``functions_in_changed_files`` and ``callers`` so that only entries actually
touched by the PR diff survive.

Why: the AST builder dumps *every* function defined in any changed file, plus
every call-site of any of those functions. For PRs that touch a few lines of a
large class, ~95% of that data is noise (unchanged sibling methods and their
call-sites). The KG context window then gets dominated by irrelevant entries,
which weak generators get distracted by and strong generators ignore.

How: the unified diff in ``full_diff`` carries ``@@ -a,b +c,d @@`` headers per
hunk, which tell us which line ranges in the *post-diff* file are touched.
Function definitions whose ``[start_line, end_line]`` intersects any hunk are
"changed"; everything else is unchanged sibling code that we now drop.

Output: ``data/luca_prs_fixed_ast_scoped/pr{N}_evidence.json`` with the same
top-level schema. Diff, RAG chunks, tests, and dependent files are passed
through untouched.

Usage:
    python3 scripts/scope_ast_evidence.py            # all PRs
    python3 scripts/scope_ast_evidence.py 3 6 14 18 21
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
# Default paths are v1 (luca_prs_fixed_ast) for backwards compatibility
# with the original v1 sensitivity runs. For the v2 (40-PR) scoped-AST
# sensitivity analysis, override via environment variables:
#   AST_SCOPE_SRC_DIR=data/luca_prs_v2_ast
#   AST_SCOPE_DST_DIR=data/luca_prs_v2_ast_scoped
# (added 2026-05-13; see dataset_v2/docs/PRE_REGISTRATION_scoped_ast.md).
SRC_DIR = Path(os.environ.get("AST_SCOPE_SRC_DIR", REPO_ROOT / "data" / "luca_prs_fixed_ast"))
if not SRC_DIR.is_absolute():
    SRC_DIR = REPO_ROOT / SRC_DIR
DST_DIR = Path(os.environ.get("AST_SCOPE_DST_DIR", REPO_ROOT / "data" / "luca_prs_fixed_ast_scoped"))
if not DST_DIR.is_absolute():
    DST_DIR = REPO_ROOT / DST_DIR

# unified-diff file header -- captures the post-diff path
_FILE_HEADER_RE = re.compile(r"^diff --git a/(?P<old>[^ \n]+) b/(?P<new>[^ \n]+)\s*$")
# new-file marker (handles renames / additions)
_PLUS_HEADER_RE = re.compile(r"^\+\+\+ (?:b/)?(?P<path>[^\t\n]+)\s*$")
# hunk header: we want the "+c,d" side -- post-diff line range
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")


def parse_hunks(full_diff: str) -> dict[str, list[tuple[int, int]]]:
    """Return {file_path: [(start_line, end_line), ...]} from a unified diff.

    Line ranges are in the *post-diff* coordinate system, matching how the AST
    builder records ``functions_in_changed_files`` (it parses files as they sit
    on disk, i.e. the post-diff state). When a hunk has count=0 (pure deletion),
    we still record (start, start) so the caller can decide to drop it; we
    simply lose the chance to flag the deletion as "changed" because there's
    no surviving line to overlap. That's an acceptable degradation.
    """
    hunks: dict[str, list[tuple[int, int]]] = {}
    current: str | None = None
    for line in full_diff.splitlines():
        m = _FILE_HEADER_RE.match(line)
        if m:
            current = m.group("new")
            hunks.setdefault(current, [])
            continue
        m = _PLUS_HEADER_RE.match(line)
        if m and m.group("path") != "/dev/null":
            current = m.group("path")
            hunks.setdefault(current, [])
            continue
        m = _HUNK_RE.match(line)
        if m and current:
            start = int(m.group("start"))
            count = int(m.group("count")) if m.group("count") else 1
            if count <= 0:
                continue  # pure deletion; no surviving lines to overlap
            hunks[current].append((start, start + count - 1))
    return hunks


def _overlaps(fn_start: int, fn_end: int, ranges: Iterable[tuple[int, int]]) -> bool:
    return any(not (fn_end < s or fn_start > e) for s, e in ranges)


def _parse_lines_field(lines_field: str) -> tuple[int, int] | None:
    """Parse the AST builder's "start-end" string into ints."""
    try:
        a, b = lines_field.split("-", 1)
        return int(a), int(b)
    except (ValueError, AttributeError):
        return None


def scope_one(ev: dict) -> tuple[dict, dict]:
    """Return (scoped_evidence, stats_dict) for a single PR evidence pack."""
    diff = ev.get("full_diff", "") or ""
    hunks = parse_hunks(diff)
    # Index hunks by the file path the AST builder uses (relative repo path).
    # Diff paths and AST file paths should match by virtue of both being repo-
    # relative. If a function's file isn't in the hunks dict we keep nothing
    # for that file (truly unrelated).
    funcs_in = ev.get("functions_in_changed_files", []) or []
    callers_in = ev.get("callers", []) or []

    funcs_out: list[dict] = []
    for fn in funcs_in:
        file_path = fn.get("file") or ""
        rng = _parse_lines_field(fn.get("lines", ""))
        file_hunks = hunks.get(file_path, [])
        if not file_hunks or rng is None:
            continue
        if _overlaps(rng[0], rng[1], file_hunks):
            funcs_out.append(fn)

    # Build two sets:
    #   - qualified_changed: "ClassName.method" — strict, class-aware match
    #   - bare_unique: bare method names that belong to exactly one changed
    #     class. We can safely accept bare-name matches for these because
    #     there's no ambiguity.
    qualified_changed: set[str] = set()
    bare_to_classes: dict[str, set[str]] = {}
    for fn in funcs_out:
        bare = fn["name"]
        if fn.get("class"):
            qualified_changed.add(f"{fn['class']}.{bare}")
            bare_to_classes.setdefault(bare, set()).add(fn["class"])
        else:
            qualified_changed.add(bare)
            bare_to_classes.setdefault(bare, set()).add("")

    # Bare names safe to accept: only if the bare name belongs to a SINGLE
    # changed class AND it isn't a generic ubiquitous method we know is noisy.
    NOISY_BARE = {"build", "update", "get", "set", "init", "close", "open",
                  "create", "destroy", "start", "stop", "run", "execute",
                  "process", "handle", "configDef", "toString", "hashCode",
                  "equals", "compute", "apply", "test"}
    bare_safe = {b for b, classes in bare_to_classes.items()
                 if len(classes) == 1 and b not in NOISY_BARE}

    callers_out: list[dict] = []
    for c in callers_in:
        target = c.get("calls_function") or ""
        bare = target.split(".")[-1]
        # Strict 1: full qualified target matches a changed qualified name.
        if target in qualified_changed:
            callers_out.append(c); continue
        # Strict 2: receiver looks like a class (CapitalCase) and qualified
        # form matches.
        if "." in target:
            receiver, _, _ = target.rpartition(".")
            # last segment of receiver chain
            recv_last = receiver.split(".")[-1]
            if recv_last and recv_last[0].isupper():
                if f"{recv_last}.{bare}" in qualified_changed:
                    callers_out.append(c); continue
        # Soft 3: bare name is unique within the changed set and not a
        # ubiquitous noisy verb (build/update/get/...).
        if bare in bare_safe:
            callers_out.append(c); continue
        # Otherwise drop -- name collision with unrelated code.

    scoped = dict(ev)  # shallow copy; we only replace two fields
    scoped["functions_in_changed_files"] = funcs_out
    scoped["callers"] = callers_out
    scoped["scoping"] = {
        "method": "diff-hunk overlap (post-diff line ranges)",
        "hunk_files": len(hunks),
        "funcs_before": len(funcs_in),
        "funcs_after": len(funcs_out),
        "callers_before": len(callers_in),
        "callers_after": len(callers_out),
    }
    stats = scoped["scoping"]
    return scoped, stats


def main() -> None:
    DST_DIR.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 1:
        pr_ids = [int(x) for x in sys.argv[1:]]
    else:
        pr_ids = sorted(int(p.stem.removeprefix("pr").removesuffix("_evidence"))
                        for p in SRC_DIR.glob("pr*_evidence.json"))

    print(f"{'pr':>4}  {'hunk_files':>10}  {'funcs':>14}  {'callers':>14}")
    for pr_id in pr_ids:
        src = SRC_DIR / f"pr{pr_id}_evidence.json"
        if not src.exists():
            print(f"  pr{pr_id}: missing source, skipping")
            continue
        ev = json.loads(src.read_text())
        scoped, stats = scope_one(ev)
        dst = DST_DIR / f"pr{pr_id}_evidence.json"
        dst.write_text(json.dumps(scoped, indent=2))
        funcs_str = f"{stats['funcs_before']:>4} → {stats['funcs_after']:>4}"
        callers_str = f"{stats['callers_before']:>5} → {stats['callers_after']:>5}"
        print(f"  pr{pr_id:>2}  {stats['hunk_files']:>10}  {funcs_str:>14}  {callers_str:>14}")

    print(f"\nwrote → {DST_DIR}")


if __name__ == "__main__":
    main()
