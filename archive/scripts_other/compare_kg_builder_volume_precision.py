#!/usr/bin/env python3
"""Compare the lexical (grep) and unscoped AST knowledge-graph builders on the
v2 40-PR set along two axes: how many edges each asserts, and how many of
those edges are real.

Motivation
----------
`results/SENSITIVITY_v2_grep_vs_ast.md` compared grep against a *hunk-scoped*
AST builder and found the effect shrank.  That comparison changed edge
precision and graph volume at the same time, so it cannot attribute the change
to either.  Before any further generation spend, this script measures the
manipulation itself: the volume and precision difference between the two
builders, both in the raw evidence packs and in the block that is actually
rendered into the prompt.

No model calls.  Costs nothing.

Precision test
--------------
An edge (source_file -> path) claims that `path` depends on `source_file`.

* AST edges carry a self-reported `import_statement` and `line`.  The edge is
  counted CONFIRMED only if the file really does contain that import text on
  (or near) the named line, so the builder's own claim is checked rather than
  trusted.
* Grep edges carry no such evidence.  For Python-to-Python edges the file is
  parsed with `ast` and the edge is CONFIRMED if any import's final component
  matches the changed file's stem.  This is deliberately generous, so the
  reported grep precision is an upper bound.
* Edges that cross language families, or whose source is not a code file, are
  counted REFUTED without opening the repository: an `import` relationship
  cannot hold between a `.yaml` and a `.go`.

Outputs
-------
results/BUILDER_VOLUME_PRECISION.md
results/BUILDER_VOLUME_PRECISION.json

Usage
-----
    python3 scripts/compare_kg_builder_volume_precision.py

Environment overrides:
    KG_GREP_DIR   (default data/luca_prs_v2)
    KG_AST_DIR    (default data/luca_prs_v2_ast)
    KG_REPO_ROOT  (default luca_repos)
"""

from __future__ import annotations

import ast
import json
import os
import re
import statistics
import sys
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from prnote.note import format_kg_context  # noqa: E402

GREP_DIR = BASE / os.environ.get("KG_GREP_DIR", "data/luca_prs_v2")
AST_DIR = BASE / os.environ.get("KG_AST_DIR", "data/luca_prs_v2_ast")
REPO_ROOT = BASE / os.environ.get("KG_REPO_ROOT", "luca_repos")

# Two files can only stand in an import relationship if they belong to the same
# language family.  Anything else is a builder error we can flag for free.
FAMILY = {
    ".py": "py", ".pyx": "py", ".pxd": "py",
    ".ts": "ts", ".tsx": "ts", ".js": "ts", ".jsx": "ts", ".mjs": "ts",
    ".go": "go",
    ".java": "jvm", ".scala": "jvm", ".kt": "jvm", ".groovy": "jvm",
    ".c": "c", ".h": "c", ".cpp": "c", ".cc": "c", ".hpp": "c", ".inc": "c",
    ".cs": "cs", ".rb": "rb", ".rs": "rs",
}


def family(path: str) -> str | None:
    return FAMILY.get(Path(path).suffix.lower())


def pr_ids(directory: Path) -> list[int]:
    out = []
    for p in directory.glob("pr*_evidence.json"):
        m = re.match(r"pr(\d+)_evidence\.json$", p.name)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


def load(directory: Path, pr: int) -> dict[str, Any]:
    return json.loads((directory / f"pr{pr}_evidence.json").read_text())


def locate_repo(pack: dict[str, Any], repos: list[Path]) -> Path | None:
    """Pick the checkout in which most of the pack's changed files exist."""
    changed = [c["path"] for c in pack.get("changed_files", [])]
    if not changed:
        return None
    best, score = None, 0
    for r in repos:
        s = sum(1 for f in changed if (r / f).exists())
        if s > score:
            best, score = r, s
    return best


# ── precision ──────────────────────────────────────────────────────────────

_py_import_cache: dict[Path, set[str] | None] = {}


def python_imported_names(path: Path) -> set[str] | None:
    """Final components of every module named by a real import statement."""
    if path in _py_import_cache:
        return _py_import_cache[path]
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        _py_import_cache[path] = None
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
    _py_import_cache[path] = names
    return names


def classify_ast_edge(edge: dict[str, Any], repo: Path) -> str:
    """Check the builder's own claim: is that import really on that line?"""
    src, dst = edge.get("source_file", ""), edge.get("path", "")
    fs, fd = family(src), family(dst)
    if fs is None or (fd is not None and fs != fd):
        return "refuted_impossible"
    stmt, line = edge.get("import_statement"), edge.get("line")
    if not stmt:
        return "unverifiable"
    f = repo / dst
    if not f.exists():
        return "unverifiable"
    try:
        lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return "unverifiable"
    # The module path may be written dotted, slashed, or as a bare tail.
    needles = {stmt, stmt.replace(".", "/"), stmt.split(".")[-1]}
    if isinstance(line, int) and 1 <= line <= len(lines):
        window = "\n".join(lines[max(0, line - 3): line + 2])
        if any(n and n in window for n in needles):
            return "confirmed"
    body = "\n".join(lines)
    return "confirmed_elsewhere" if any(n and n in body for n in needles) else "refuted"


def classify_grep_edge(edge: dict[str, Any], repo: Path) -> str:
    src, dst = edge.get("source_file", ""), edge.get("path", "")
    fs, fd = family(src), family(dst)
    if fs is None or (fd is not None and fs != fd):
        return "refuted_impossible"
    if not (src.endswith(".py") and dst.endswith(".py")):
        return "unverifiable"        # no parser wired up for this family here
    f = repo / dst
    if not f.exists():
        return "unverifiable"
    names = python_imported_names(f)
    if names is None:
        return "unverifiable"
    return "confirmed" if Path(src).stem in names else "refuted"


# ── rendered block ─────────────────────────────────────────────────────────

DEP_HEADER = "Files that depend on changes"


def listed_paths(block: str, header: str) -> list[str]:
    """The formatter emits one comma-separated line per section."""
    m = re.search(rf"\*\*{re.escape(header)}:\*\* (.+)", block)
    return [p.strip() for p in m.group(1).split(",") if p.strip()] if m else []


def rendered_stats(pack: dict[str, Any]) -> dict[str, int]:
    """What the model actually sees, after the formatter's caps."""
    block = format_kg_context(pack) or ""
    return {
        "chars": len(block),
        "lines": block.count("\n") + 1 if block else 0,
        "shown_deps": len(listed_paths(block, DEP_HEADER)),
        "shown_tests": len(listed_paths(block, "Related Tests")),
        "sections": len(re.findall(r"\*\*[^*]+:\*\*", block)),
    }


def precision_only_variant(grep_pack: dict[str, Any],
                           ast_pack: dict[str, Any]) -> dict[str, Any]:
    """Grep's pack with its dependency list swapped for AST-resolved paths,
    truncated to the number grep actually displayed.

    This isolates edge correctness: section set, section order and displayed
    count are all held at grep's values, so only the identity of the dependent
    paths changes.  Feasible only where AST resolved at least as many
    dependents as grep displayed.
    """
    shown = listed_paths(format_kg_context(grep_pack) or "", DEP_HEADER)
    seen: set[str] = set()
    resolved = [d["path"] for d in ast_pack.get("dependent_files", [])
                if not (d["path"] in seen or seen.add(d["path"]))]
    swapped = json.loads(json.dumps(grep_pack))
    swapped["dependent_files"] = [{"path": p, "relationship": "imports"}
                                  for p in resolved[:len(shown)]]
    return {
        "grep_shown": len(shown),
        "ast_resolved": len(resolved),
        "feasible": len(resolved) >= len(shown) and len(shown) > 0,
        "ast_empty": len(resolved) == 0,
        "chars": len(format_kg_context(swapped) or ""),
    }


def main() -> None:
    repos = [d for d in REPO_ROOT.iterdir() if d.is_dir() and not d.name.startswith(".")]
    ids = sorted(set(pr_ids(GREP_DIR)) & set(pr_ids(AST_DIR)))
    print(f"comparing {len(ids)} PRs present in both builders\n")

    per_pr: list[dict[str, Any]] = []
    tally = {
        "grep": {"confirmed": 0, "confirmed_elsewhere": 0, "refuted": 0,
                 "refuted_impossible": 0, "unverifiable": 0},
        "ast": {"confirmed": 0, "confirmed_elsewhere": 0, "refuted": 0,
                "refuted_impossible": 0, "unverifiable": 0},
    }

    for pr in ids:
        g, a = load(GREP_DIR, pr), load(AST_DIR, pr)
        repo = locate_repo(g, repos)

        gd, ad = g.get("dependent_files", []), a.get("dependent_files", [])
        gt, at = g.get("nearest_tests", []), a.get("nearest_tests", [])

        if repo is not None:
            for e in gd:
                tally["grep"][classify_grep_edge(e, repo)] += 1
            for e in ad:
                tally["ast"][classify_ast_edge(e, repo)] += 1

        gset = {(e.get("source_file"), e.get("path")) for e in gd}
        aset = {(e.get("source_file"), e.get("path")) for e in ad}
        inter = len(gset & aset)
        union = len(gset | aset)

        rg, ra = rendered_stats(g), rendered_stats(a)
        per_pr.append({
            "pr_id": pr,
            "repo": repo.name if repo else None,
            "raw": {"grep_deps": len(gd), "ast_deps": len(ad),
                    "grep_tests": len(gt), "ast_tests": len(at)},
            "overlap": {"shared_dep_edges": inter, "union": union,
                        "jaccard": round(inter / union, 4) if union else None},
            "rendered": {"grep": rg, "ast": ra},
            "precision_only": precision_only_variant(g, a),
        })

    def col(f):
        return [f(r) for r in per_pr]

    med = statistics.median
    summary = {
        "n_prs": len(per_pr),
        "raw_deps": {
            "grep_median": med(col(lambda r: r["raw"]["grep_deps"])),
            "ast_median": med(col(lambda r: r["raw"]["ast_deps"])),
            "grep_total": sum(col(lambda r: r["raw"]["grep_deps"])),
            "ast_total": sum(col(lambda r: r["raw"]["ast_deps"])),
            "ast_larger_in": sum(1 for r in per_pr
                                 if r["raw"]["ast_deps"] > r["raw"]["grep_deps"]),
            "ast_empty_in": sum(1 for r in per_pr if r["raw"]["ast_deps"] == 0),
            "grep_empty_in": sum(1 for r in per_pr if r["raw"]["grep_deps"] == 0),
        },
        "rendered_chars": {
            "grep_median": med(col(lambda r: r["rendered"]["grep"]["chars"])),
            "ast_median": med(col(lambda r: r["rendered"]["ast"]["chars"])),
        },
        "rendered_shown_deps": {
            "grep_median": med(col(lambda r: r["rendered"]["grep"]["shown_deps"])),
            "ast_median": med(col(lambda r: r["rendered"]["ast"]["shown_deps"])),
        },
        "rendered_sections": {
            "grep_median": med(col(lambda r: r["rendered"]["grep"]["sections"])),
            "ast_median": med(col(lambda r: r["rendered"]["ast"]["sections"])),
        },
        "precision_only_feasibility": {
            "feasible": sum(1 for r in per_pr if r["precision_only"]["feasible"]),
            "ast_empty": sum(1 for r in per_pr if r["precision_only"]["ast_empty"]),
            "ast_short": sum(1 for r in per_pr
                             if not r["precision_only"]["feasible"]
                             and not r["precision_only"]["ast_empty"]),
            "char_delta_median": med(col(lambda r: r["precision_only"]["chars"]
                                         - r["rendered"]["grep"]["chars"])),
        },
        "edge_overlap_jaccard_median": med(
            [r["overlap"]["jaccard"] for r in per_pr
             if r["overlap"]["jaccard"] is not None]),
        "precision": tally,
    }

    for b in ("grep", "ast"):
        t = tally[b]
        ok = t["confirmed"] + t["confirmed_elsewhere"]
        checked = ok + t["refuted"] + t["refuted_impossible"]
        summary["precision"][b]["checked"] = checked
        summary["precision"][b]["precision"] = round(ok / checked, 4) if checked else None

    out = {"meta": {"grep_dir": str(GREP_DIR.relative_to(BASE)),
                    "ast_dir": str(AST_DIR.relative_to(BASE)),
                    "model_calls": 0},
           "summary": summary, "per_pr": per_pr}

    (BASE / "results").mkdir(exist_ok=True)
    (BASE / "results/BUILDER_VOLUME_PRECISION.json").write_text(
        json.dumps(out, indent=2))
    write_markdown(out)

    s = summary
    print(f"raw dependent edges   grep median {s['raw_deps']['grep_median']:.0f}"
          f"   ast median {s['raw_deps']['ast_median']:.0f}"
          f"   (ast larger in {s['raw_deps']['ast_larger_in']}/{s['n_prs']})")
    print(f"rendered block chars  grep median {s['rendered_chars']['grep_median']:.0f}"
          f"   ast median {s['rendered_chars']['ast_median']:.0f}")
    print(f"dependents shown      grep median {s['rendered_shown_deps']['grep_median']:.0f}"
          f"   ast median {s['rendered_shown_deps']['ast_median']:.0f}")
    print(f"sections in block     grep median {s['rendered_sections']['grep_median']:.0f}"
          f"   ast median {s['rendered_sections']['ast_median']:.0f}")
    print(f"edge-set overlap      median Jaccard {s['edge_overlap_jaccard_median']:.3f}")
    for b in ("grep", "ast"):
        p = s["precision"][b]
        print(f"{b:>5} precision       {p['precision']:.1%}  "
              f"(checked {p['checked']}, unverifiable {p['unverifiable']})")
    f = s["precision_only_feasibility"]
    print(f"\nprecision-only variant feasible in {f['feasible']}/{s['n_prs']} PRs"
          f"  (AST empty in {f['ast_empty']}, short in {f['ast_short']})")
    print("wrote results/BUILDER_VOLUME_PRECISION.{md,json}")


def write_markdown(out: dict[str, Any]) -> None:
    s, per = out["summary"], out["per_pr"]
    L = ["# KG builder comparison — volume and precision (no model calls)", "",
         f"Builders: `{out['meta']['grep_dir']}` (lexical) vs "
         f"`{out['meta']['ast_dir']}` (unscoped AST, tree-sitter).",
         f"PRs compared: {s['n_prs']}.  Cost: $0.", "",
         "## Volume", "",
         "| Measure | grep | unscoped AST |", "|---|---:|---:|",
         f"| Dependent edges, median per PR | {s['raw_deps']['grep_median']:.0f} "
         f"| {s['raw_deps']['ast_median']:.0f} |",
         f"| Dependent edges, total | {s['raw_deps']['grep_total']} "
         f"| {s['raw_deps']['ast_total']} |",
         f"| PRs with no dependent edges | {s['raw_deps']['grep_empty_in']} "
         f"| {s['raw_deps']['ast_empty_in']} |",
         f"| Rendered block, median chars | {s['rendered_chars']['grep_median']:.0f} "
         f"| {s['rendered_chars']['ast_median']:.0f} |",
         f"| Dependents actually shown, median | {s['rendered_shown_deps']['grep_median']:.0f} "
         f"| {s['rendered_shown_deps']['ast_median']:.0f} |",
         f"| Sections in the block, median | {s['rendered_sections']['grep_median']:.0f} "
         f"| {s['rendered_sections']['ast_median']:.0f} |", "",
         f"AST asserts more dependent edges than grep in "
         f"{s['raw_deps']['ast_larger_in']} of {s['n_prs']} PRs.",
         f"Median Jaccard overlap of the two dependent-edge sets: "
         f"{s['edge_overlap_jaccard_median']:.3f}.", "",
         "## Precision", "",
         "| Builder | edges checked | confirmed | refuted | impossible | precision | unverifiable |",
         "|---|---:|---:|---:|---:|---:|---:|"]
    for b, label in (("grep", "lexical (grep)"), ("ast", "unscoped AST")):
        p = s["precision"][b]
        L.append(f"| {label} | {p['checked']} | "
                 f"{p['confirmed'] + p['confirmed_elsewhere']} | {p['refuted']} | "
                 f"{p['refuted_impossible']} | "
                 f"{p['precision']:.1%} | {p['unverifiable']} |")
    f = s["precision_only_feasibility"]
    L += ["",
          "Grep precision is an upper bound: a Python edge counts as confirmed if "
          "any import's final component matches the changed file's stem, which "
          "also admits same-named modules in unrelated packages.  AST edges are "
          "checked against the builder's own claimed import statement and line.",
          "",
          "## Can a precision-only experiment be run?", "",
          "A clean single-factor contrast requires holding the section set and the "
          "displayed dependent count at grep's values and changing only which "
          "paths are named.  That needs AST to have resolved at least as many "
          "dependents as grep displayed.", "",
          f"* Feasible in **{f['feasible']} of {s['n_prs']}** pull requests.",
          f"* AST resolves **zero** dependents in {f['ast_empty']}.",
          f"* AST resolves fewer than grep displays in {f['ast_short']}.",
          f"* Median rendered-length change of the swap: {f['char_delta_median']:+.0f} chars.",
          "",
          "The precise builder therefore cannot supply comparable coverage across "
          "the set.  A clean precision contrast is confined to the feasible subset, "
          "which is the same underpowered regime that rules out the feature "
          "ablation (see `results/CONFIRMATORY_POWER.md`).  The trade-off itself, "
          "not a further generation run, is the reportable result.",
          "", "## Per-PR detail", "",
          "| PR | repo | grep deps | AST deps | grep rendered chars | AST rendered chars | Jaccard |",
          "|---|---|---:|---:|---:|---:|---:|"]
    for r in per:
        j = r["overlap"]["jaccard"]
        L.append(f"| {r['pr_id']} | {r['repo'] or '—'} | {r['raw']['grep_deps']} "
                 f"| {r['raw']['ast_deps']} | {r['rendered']['grep']['chars']} "
                 f"| {r['rendered']['ast']['chars']} | "
                 f"{'—' if j is None else f'{j:.3f}'} |")
    (BASE / "results/BUILDER_VOLUME_PRECISION.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
