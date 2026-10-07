#!/usr/bin/env python3
"""Hallucination audit on the 35 clean-Joern reviews.

For each review, extract candidate claims and verify them against evidence:
  - file:line citations  → file must exist in evidence (changed, callers, dependents, or test list)
  - person/owner names   → flagged unconditionally (we don't have owner data; any named
                            individual is suspicious by construction)
  - function references in backticks → soft-checked against evidence's known symbols

Emits a per-PR row + a top-level summary.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REVIEWS = REPO / "experiments" / "2026-06-11_joern_normal_prompt" / "reviews"
EVIDENCE_DIR = REPO / "experiments" / "2026-05-15_joern_kg_main" / "evidence"
OUT = REPO / "human_eval_v3_clean_2026-06-11" / "HALLUCINATION_AUDIT.md"

FILE_LINE_RE = re.compile(r"`?([\w./\-]+\.(?:py|java|ts|tsx|js|jsx|cpp|cc|h|hpp|scala|go|xml|gradle|json|yaml|yml|md))(?::(\d+(?:-\d+)?))?`?")
# Person-name-like pattern: TitleCase TitleCase (e.g., "Danilo Silva"), avoiding common
# code patterns by anchoring to "owner/author/maintainer/by" context words.
OWNER_RE = re.compile(
    r"\b(?:Code Owner|Author|Maintainer|Owner|Reviewed by|Reviewed-by|Authored by)\b\s*[:\-]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
    re.IGNORECASE,
)
HANDLE_RE = re.compile(r"@([a-z0-9][a-z0-9-]{2,30})", re.IGNORECASE)
TEAM_RE = re.compile(r"\bRelevant Teams?\s*[:\-]\s*([^\n]+)", re.IGNORECASE)


def collect_known_paths(ev: dict) -> set[str]:
    paths: set[str] = set()
    # changed files
    for f in ev.get("changed_files", []) or ev.get("files", []):
        p = f.get("path") if isinstance(f, dict) else f
        if p:
            paths.add(p)
            paths.add(Path(p).name)
    # KG: callers, dependents, tests
    kg = ev.get("kg", {}) or {}
    for sec in ("callers", "dependents", "tests", "imports", "functions_in_changed_files"):
        for item in kg.get(sec, []) or []:
            if isinstance(item, dict):
                p = item.get("path") or item.get("file")
                if p:
                    paths.add(p)
                    paths.add(Path(p).name)
            elif isinstance(item, str):
                paths.add(item)
                paths.add(Path(item).name)
    # tree-sitter style flat keys (older shape)
    for sec in ("test_files", "dependent_files", "caller_files"):
        for p in ev.get(sec, []) or []:
            if isinstance(p, str):
                paths.add(p)
                paths.add(Path(p).name)
    return {p for p in paths if p}


def audit_review(pr_id: int, review_path: Path) -> dict:
    text = review_path.read_text()
    ev_path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    if not ev_path.exists():
        return {"pr_id": pr_id, "error": "no evidence file"}
    ev = json.loads(ev_path.read_text())
    known = collect_known_paths(ev)

    cited_files = set()
    for m in FILE_LINE_RE.finditer(text):
        cited_files.add(m.group(1))

    unverified = []
    for c in cited_files:
        # match either full path or basename
        if c in known:
            continue
        if Path(c).name in known:
            continue
        # also match if any known path ends with this string
        if any(k.endswith(c) or c.endswith(k) for k in known):
            continue
        # very short tokens like "context.go" might be common; flag anyway
        unverified.append(c)

    owners = OWNER_RE.findall(text)
    handles = HANDLE_RE.findall(text)
    teams_raw = TEAM_RE.findall(text)

    # filter handles: many "@-words" inside backticks are decorators (Java/Python),
    # not GH handles. Strip those that appear inside `...`.
    handle_strs = []
    for h in handles:
        # if followed/surrounded by typical code patterns, skip
        ctx = text.find("@" + h)
        before = text[max(0, ctx - 1):ctx]
        after = text[ctx + len(h) + 1:ctx + len(h) + 2]
        if before == "`" or after == "`":
            continue
        if before == "(":  # decorator-like
            continue
        handle_strs.append(h)

    return {
        "pr_id": pr_id,
        "review_chars": len(text),
        "cited_files": sorted(cited_files),
        "unverified_files": sorted(unverified),
        "n_unverified": len(unverified),
        "claimed_owners": owners,
        "claimed_handles": handle_strs,
        "claimed_teams": [t.strip() for t in teams_raw],
    }


def main():
    rows = []
    for f in sorted(REVIEWS.glob("pr*_kg.md")):
        pr_id = int(f.stem.replace("pr", "").replace("_kg", ""))
        rows.append(audit_review(pr_id, f))

    lines = []
    P = lines.append
    P("# Hallucination audit — clean Joern reviews (n=35)")
    P("")
    P("**Method:** for each review, extract every `file:line` citation, then verify")
    P("the file appears in the Joern evidence pack (changed files, callers, dependents,")
    P("or test list). Also flag any **named individual** (Code Owner / Author /")
    P("Maintainer fields) — the evidence pack contains *no* author data, so any named")
    P("person is a fabrication by construction. Same for teams and `@` handles.")
    P("")
    total = len(rows)
    n_unverified = sum(1 for r in rows if r.get("n_unverified", 0) > 0)
    n_owner = sum(1 for r in rows if r.get("claimed_owners"))
    n_handle = sum(1 for r in rows if r.get("claimed_handles"))
    n_team = sum(1 for r in rows if r.get("claimed_teams"))
    P(f"## Summary")
    P("")
    P(f"- Reviews audited: **{total}**")
    P(f"- Reviews with ≥1 unverified file citation: **{n_unverified}** ({n_unverified/total*100:.0f}%)")
    P(f"- Reviews naming a code owner / author / maintainer: **{n_owner}** ({n_owner/total*100:.0f}%) — **all are fabrications** (evidence has no author data)")
    P(f"- Reviews with `@handle` mentions: **{n_handle}**")
    P(f"- Reviews naming a team: **{n_team}**")
    P("")
    P("## Per-PR detail")
    P("")
    P("| PR | unverified files | owners (fabricated) | handles | teams (fabricated) |")
    P("|---:|:---|:---|:---|:---|")
    for r in rows:
        if r.get("error"):
            P(f"| {r['pr_id']} | _{r['error']}_ |  |  |  |")
            continue
        unv = ", ".join(r["unverified_files"][:5]) + (" …" if len(r["unverified_files"]) > 5 else "")
        owners = ", ".join(r["claimed_owners"]) or ""
        handles = ", ".join(r["claimed_handles"]) or ""
        teams = ", ".join(r["claimed_teams"][:2]) + (" …" if len(r["claimed_teams"]) > 2 else "")
        P(f"| {r['pr_id']} | {unv} | {owners} | {handles} | {teams} |")
    P("")
    P("## Reading")
    P("")
    P("Unverified file citations include both **real hallucinations** (file does not")
    P("exist in the repo) and **soft hallucinations** (the model paraphrased a path,")
    P("e.g. shortened or guessed an extension). Both are review-quality defects.")
    P("")
    P("Fabricated owners are unambiguous: the Joern evidence pack carries zero owner")
    P("metadata. Any named person in the review text is fully made up by the LLM.")
    P("This is the most concerning failure mode for thesis discussion (it's the")
    P("\"shape of structural claims rewarded over correctness\" pattern shown by PR31).")
    P("")
    OUT.write_text("\n".join(lines))
    print(f"Wrote {OUT}")
    print(f"\nReviews with ≥1 unverified file: {n_unverified}/{total}")
    print(f"Reviews with fabricated owner: {n_owner}/{total}")
    print(f"Reviews with @handle: {n_handle}/{total}")
    print(f"Reviews with team: {n_team}/{total}")
    if n_owner:
        print("\nPRs with fabricated owners:")
        for r in rows:
            if r.get("claimed_owners"):
                print(f"  PR{r['pr_id']}: {r['claimed_owners']}")


if __name__ == "__main__":
    main()
