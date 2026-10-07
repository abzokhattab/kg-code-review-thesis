#!/usr/bin/env python3
"""Stages A+B: copy scopes, discover targets (direction-blind, top fan-out
first), apply operators, verify, write manifest + diffs.  $0 — no API calls.

Idempotent: if out/manifest.json exists, exits unless --force.

Selection discipline (pre-reg §5): within each (repo, band), candidates are
ranked by structural fan-out (verified dependents) and taken top-first until
the band quota is filled. No review is generated or consulted here.
"""
from __future__ import annotations

import argparse
import difflib
import random
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (BAND_QUOTA, BAND_TITLES, LOCAL_BANDS, OUT, PR_BODY, SCOPES,  # noqa: E402
                    SEED, dump_json, manifest_path, scope_dir)
from analyzers import ANALYZERS, EXCLUDE_PAT  # noqa: E402
from operators import OPERATORS  # noqa: E402


def copy_scope(repo: str) -> Path:
    cfg = SCOPES[repo]
    dst = scope_dir(repo)
    if dst.exists():
        return dst
    for sub in cfg["subdirs"]:
        src = cfg["src"] / sub
        for p in sorted(src.rglob("*")):
            if not p.is_file():
                continue
            r = p.relative_to(cfg["src"])
            if EXCLUDE_PAT.search(str(r)):
                continue
            out = dst / r
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(p, out)
    for f in cfg["extra_files"]:
        out = dst / f
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(cfg["src"] / f, out)
    return dst


def find_barrel(scope: Path, sym: dict, language: str) -> str | None:
    """Package barrel (__init__.py / index.ts) that re-exports the symbol."""
    d = (scope / sym["file"]).parent
    name = sym["name"]
    barrels = {"python": "__init__.py", "typescript": "index.ts"}.get(language)
    if not barrels:
        return None
    while True:
        b = d / barrels
        if b.exists() and re.search(rf"\b{re.escape(name)}\b", b.read_text(errors="ignore")):
            return str(b.relative_to(scope))
        if d == scope:
            return None
        d = d.parent


def local_sites(scope: Path, analyzer, band: str, language: str, rng):
    """Candidate edit sites for the local control bands, inside functions of
    files that HAVE importers (so context volume is comparable to S-bands)."""
    pats = {
        "L1": re.compile(r"^\s+(?:if|while|for)\b.*(?:<=|>=|<|>)"),
        "L2": {"python": re.compile(r"^\s+if\b.* is None\b(?!.*is not None).*:"),
               "java": re.compile(r"^\s+if\s*\(.*== null"),
               "typescript": re.compile(r"^\s+if\s*\(.*(?:== null|=== undefined)")}[language],
    }[band]
    comment_marker = "#" if language == "python" else "//"
    sites = []
    for p in analyzer.files:
        r = str(p.relative_to(scope))
        text = p.read_text(errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            # match only the code portion — never a comparison inside a comment
            code = line.split(comment_marker)[0]
            if pats.search(code) and len(line.strip()) < 120:
                sites.append({"file": r, "lineno": i, "line": line})
    rng.shuffle(sites)
    return sites


def build_diff(scope: Path, edit: dict) -> str | None:
    f = scope / edit["file"]
    clean = f.read_text(errors="ignore")
    if clean.count(edit["old"]) != 1:
        return None
    mutant = clean.replace(edit["old"], edit["new"], 1)
    return "".join(difflib.unified_diff(
        clean.splitlines(keepends=True), mutant.splitlines(keepends=True),
        fromfile=f"a/{edit['file']}", tofile=f"b/{edit['file']}", n=3))


def discover_repo(repo: str, rng) -> tuple[list[dict], dict]:
    cfg = SCOPES[repo]
    lang = cfg["language"]
    scope = copy_scope(repo)
    analyzer = ANALYZERS[lang](scope)
    syms = analyzer.symbols()
    print(f"[{repo}] scope={scope.name} files={len(analyzer.files)} symbols={len(syms)}")

    chosen, used_files, used_symbols, shortfall = [], set(), set(), {}

    def take(band: str, candidates: list[tuple[dict, dict]]):
        """candidates: [(sym_or_site, dependents_dict)] ranked; fill quota."""
        need = BAND_QUOTA[band]
        got = 0
        for item, deps in candidates:
            if got >= need:
                break
            key = (item["file"], band)
            if key in used_files:
                continue
            # cross-band dedup: a symbol may carry at most one injection
            sym_key = (item["file"], item.get("name"))
            if item.get("name") and sym_key in used_symbols:
                continue
            op = OPERATORS[band]
            edit = op(scope, item, lang)
            if edit is None:
                continue
            diff = build_diff(scope, edit)
            if diff is None or len(diff) > 6000:
                continue
            inj_id = f"{repo}_{band}_{got+1:02d}"
            dep_files = sorted(f for f in deps.keys() if f != edit["file"])
            if band not in LOCAL_BANDS and not dep_files:
                continue  # structural injection must have real off-edit dependents
            chosen.append({
                "id": inj_id, "repo": repo, "language": lang, "band": band,
                "operator": edit["detail"],
                "edit_file": edit["file"], "old": edit["old"], "new": edit["new"],
                "symbol": item.get("name"),
                "true_dependents": dep_files,
                "dependent_evidence": {f: deps[f][:4] for f in dep_files},
                "fanout": len(dep_files),
                "resolver": analyzer.resolver,
                "oracle": "static-structural",
                "edge_type": {"S1": "IMPORTS", "S2": "CALLS", "S3": "CALLS+dataflow",
                              "S4": "INHERITS_FROM", "S5": "IMPORTS",
                              "L1": "none-local", "L2": "none-local"}[band],
                "pr_title": BAND_TITLES[band].format(
                    mod=Path(edit["file"]).stem, sym=item.get("name", "")),
                "pr_body": PR_BODY,
                "diff": diff,
                "ground_truth": (
                    f"The edit breaks these dependent files (not shown in the diff): "
                    f"{', '.join(Path(f).name for f in dep_files)}."
                    if band not in LOCAL_BANDS else
                    f"The edit introduces a local defect at {edit['file']} "
                    f"({edit['detail']}); no cross-file breakage exists."),
            })
            used_files.add(key)
            if item.get("name"):
                used_symbols.add(sym_key)
            got += 1
        if got < need:
            shortfall[band] = f"{got}/{need}"
        print(f"  {band}: {got}/{need}")

    # ---- structural bands: rank by fan-out, top-first (direction-blind) ----
    def ranked(dep_fn, pred=lambda s: True):
        out = []
        for s in syms:
            if not pred(s):
                continue
            deps = dep_fn(s)
            if deps:
                out.append((s, deps))
        out.sort(key=lambda x: len(x[1]), reverse=True)
        return out

    # scarce bands pick first so cross-band symbol dedup doesn't starve them
    take("S4", ranked(analyzer.subclasses, lambda s: s["kind"] == "class"))
    take("S3", ranked(analyzer.callers, lambda s: s["kind"] == "function"))
    take("S2", ranked(analyzer.callers,
                      lambda s: s["kind"] in ("function", "method")))
    take("S1", ranked(analyzer.importers, lambda s: not s.get("private")))

    s5_cands = []
    for s in syms:
        b = find_barrel(scope, s, lang)
        if not b:
            continue
        deps = analyzer.importers(s)
        if deps:
            s5 = dict(s)
            s5["_barrel"] = b
            s5_cands.append((s5, deps))
    s5_cands.sort(key=lambda x: len(x[1]), reverse=True)
    take("S5", s5_cands)

    # ---- local control bands: random eligible sites in imported files ------
    importer_counts = {}
    for s in syms:
        importer_counts.setdefault(s["file"], 0)
        importer_counts[s["file"]] += len(analyzer.importers(s))
    imported_files = {f for f, n in importer_counts.items() if n > 0}
    for band in LOCAL_BANDS:
        sites = [s for s in local_sites(scope, analyzer, band, lang, rng)
                 if s["file"] in imported_files]
        take(band, [(s, {}) for s in sites])

    return chosen, shortfall


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if manifest_path().exists() and not args.force:
        print(f"manifest exists: {manifest_path()} — use --force to rebuild")
        return

    rng = random.Random(SEED)
    all_inj, all_short = [], {}
    for repo in SCOPES:
        inj, short = discover_repo(repo, rng)
        all_inj.extend(inj)
        if short:
            all_short[repo] = short

    dump_json(manifest_path(), {
        "seed": SEED, "created": "2026-07-13",
        "n": len(all_inj),
        "quota": BAND_QUOTA, "shortfalls": all_short,
        "injections": all_inj,
    })
    for inj in all_inj:
        d = OUT / "diffs" / f"{inj['id']}.diff"
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_text(inj["diff"])

    from collections import Counter
    by_band = Counter(i["band"] for i in all_inj)
    by_repo = Counter(i["repo"] for i in all_inj)
    print(f"\nTOTAL: {len(all_inj)} injections")
    print("  per band:", dict(sorted(by_band.items())))
    print("  per repo:", dict(by_repo))
    if all_short:
        print("  SHORTFALLS (reported, not back-filled):", all_short)
    print(f"manifest: {manifest_path()}")


if __name__ == "__main__":
    main()
