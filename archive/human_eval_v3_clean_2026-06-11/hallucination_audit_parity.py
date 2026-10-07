#!/usr/bin/env python3
"""Hallucination audit on the 35 PARITY-corrected Joern reviews.

Differs from the buggy-run audit in one critical way: under parity, the LLM
is given the PR body in the prompt. PR bodies frequently contain Reviewers:
or `cc @user` lines (Apache Kafka convention). So an "Author/Owner" name in
the review is *only* a fabrication if it does not appear in the PR body.

For each review, we:
  - extract file:line citations (verify against evidence pack)
  - extract owner/author/maintainer names (cross-check against PR body)
  - extract @handles (cross-check against PR body)

Output: HALLUCINATION_AUDIT_PARITY.md
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REVIEWS = REPO / "experiments" / "2026-06-11_joern_normal_prompt_parity" / "reviews"
EVIDENCE_DIR = REPO / "experiments" / "2026-05-15_joern_kg_main" / "evidence"
OUT = REPO / "human_eval_v3_clean_2026-06-11" / "HALLUCINATION_AUDIT_PARITY.md"

FILE_LINE_RE = re.compile(
    r"`?([\w./\-]+\.(?:py|java|ts|tsx|js|jsx|cpp|cc|h|hpp|scala|go|xml|gradle|json|yaml|yml|md))(?::(\d+(?:-\d+)?))?`?"
)
# Match the label only; capture the rest of the line as the claim payload.
OWNER_LINE_RE = re.compile(
    r"(?:^|\n)\s*(?:[-*]\s*)?\*?\*?(Code Owners?|Owners?|Authors?|Maintainers?|Reviewers?)\*?\*?\s*[:\-]\s*([^\n]+)",
    re.IGNORECASE,
)
HANDLE_RE = re.compile(r"@([a-z0-9][a-z0-9-]{2,30})", re.IGNORECASE)
TEAM_RE = re.compile(r"\bRelevant Teams?\s*[:\-]\s*([^\n]+)", re.IGNORECASE)
NOT_SPECIFIED_RE = re.compile(r"^\s*(not\s+specified|n/?a|none|unknown|tbd)\s*\.?\s*$", re.IGNORECASE)


def collect_known_paths(ev: dict) -> set[str]:
    paths: set[str] = set()
    for f in ev.get("changed_files", []) or ev.get("files", []):
        p = f.get("path") if isinstance(f, dict) else f
        if p:
            paths.add(p)
            paths.add(Path(p).name)
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
    for sec in ("test_files", "dependent_files", "caller_files"):
        for p in ev.get(sec, []) or []:
            if isinstance(p, str):
                paths.add(p)
                paths.add(Path(p).name)
    return {p for p in paths if p}


def get_pr_body(ev: dict) -> str:
    return (ev.get("pr", {}).get("body") or "").strip()


def audit_review(pr_id: int, review_path: Path) -> dict:
    text = review_path.read_text()
    ev_path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    if not ev_path.exists():
        return {"pr_id": pr_id, "error": "no evidence file"}
    ev = json.loads(ev_path.read_text())
    known = collect_known_paths(ev)
    body = get_pr_body(ev)
    body_lower = body.lower()

    cited_files = set()
    for m in FILE_LINE_RE.finditer(text):
        cited_files.add(m.group(1))

    unverified = []
    for c in cited_files:
        if c in known or Path(c).name in known:
            continue
        if any(k.endswith(c) or c.endswith(k) for k in known):
            continue
        unverified.append(c)

    raw_owner_lines = OWNER_LINE_RE.findall(text)
    raw_handles = HANDLE_RE.findall(text)
    raw_teams = TEAM_RE.findall(text)

    # Cross-check owner *claims* against body. Three buckets:
    #   - "Not specified" (or similar): honest abstain, not flagged
    #   - claim grounded in body (substring match, normalized): verified
    #   - claim not grounded in body: fabricated
    verified_owners = []
    fabricated_owners = []
    abstain_owners = []
    for label, claim in raw_owner_lines:
        c = claim.strip().rstrip(".").strip()
        # strip any leading/trailing asterisks (markdown bold artefacts) and whitespace
        c_clean = c.strip("*").strip()
        if NOT_SPECIFIED_RE.match(c_clean):
            abstain_owners.append(f"{label}: {c_clean}")
            continue
        # check if any token of length >= 4 in the claim appears in body
        # (handles names, team names, partial attributions)
        clean = re.sub(r"[^\w@/\-]+", " ", c_clean).split()
        substantive = [t for t in clean if len(t) >= 4]
        if not substantive:
            abstain_owners.append(f"{label}: {c_clean}")
            continue
        if any(t.lower() in body_lower for t in substantive):
            verified_owners.append(f"{label}: {c_clean}")
        else:
            fabricated_owners.append(f"{label}: {c_clean}")

    # Cross-check handles against body
    verified_handles = []
    fabricated_handles = []
    for h in raw_handles:
        ctx = text.find("@" + h)
        before = text[max(0, ctx - 1):ctx]
        after = text[ctx + len(h) + 1:ctx + len(h) + 2]
        if before == "`" or after == "`" or before == "(":
            continue
        if h.lower() in body_lower:
            verified_handles.append(h)
        else:
            fabricated_handles.append(h)

    return {
        "pr_id": pr_id,
        "review_chars": len(text),
        "body_chars": len(body),
        "cited_files": sorted(cited_files),
        "unverified_files": sorted(unverified),
        "n_unverified": len(unverified),
        "verified_owners": verified_owners,
        "fabricated_owners": fabricated_owners,
        "abstain_owners": abstain_owners,
        "verified_handles": verified_handles,
        "fabricated_handles": fabricated_handles,
        "claimed_teams": [t.strip() for t in raw_teams],
    }


def main():
    rows = []
    for f in sorted(REVIEWS.glob("pr*_kg.md")):
        pr_id = int(f.stem.replace("pr", "").replace("_kg", ""))
        rows.append(audit_review(pr_id, f))

    lines = []
    P = lines.append
    P("# Hallucination audit — PARITY Joern reviews (n=35)")
    P("")
    P("**Difference from the buggy-run audit:** under parity the LLM has the PR body")
    P("in its prompt. PR bodies often contain `Reviewers:` lines (Apache Kafka)")
    P("or `cc @user` mentions. An owner/author/handle is therefore only a fabrication")
    P("if the name does **not** appear in the body.")
    P("")
    total = len(rows)
    n_unverified_files = sum(1 for r in rows if r.get("n_unverified", 0) > 0)
    n_verified_owner = sum(1 for r in rows if r.get("verified_owners"))
    n_fabricated_owner = sum(1 for r in rows if r.get("fabricated_owners"))
    n_abstain_owner = sum(1 for r in rows if r.get("abstain_owners"))
    n_verified_handle = sum(1 for r in rows if r.get("verified_handles"))
    n_fabricated_handle = sum(1 for r in rows if r.get("fabricated_handles"))
    n_team = sum(1 for r in rows if r.get("claimed_teams"))
    P(f"## Summary")
    P("")
    P(f"- Reviews audited: **{total}**")
    P(f"- Reviews with ≥1 unverified file citation: **{n_unverified_files}** ({n_unverified_files/total*100:.0f}%)")
    P(f"- Owner claim *grounded in body*: **{n_verified_owner}** | *fabricated*: **{n_fabricated_owner}** | *abstained (\"Not specified\")*: **{n_abstain_owner}**")
    P(f"- Reviews with `@handle`: **verified-from-body {n_verified_handle}**, **fabricated {n_fabricated_handle}**")
    P(f"- Reviews naming a team: **{n_team}** (manually inspect for fabrication)")
    P("")
    P("## Per-PR detail")
    P("")
    P("| PR | unverified files | verified owner-claim | **fabricated owner-claim** | abstain |")
    P("|---:|:---|:---|:---|:---|")
    for r in rows:
        if r.get("error"):
            P(f"| {r['pr_id']} | _{r['error']}_ |  |  |  |")
            continue
        unv = ", ".join(r["unverified_files"][:4]) + (" …" if len(r["unverified_files"]) > 4 else "")
        vo = "; ".join(r["verified_owners"]) or ""
        fo = "; ".join(r["fabricated_owners"]) or ""
        ab = "; ".join(r["abstain_owners"]) or ""
        P(f"| {r['pr_id']} | {unv} | {vo} | **{fo}** | {ab} |")
    P("")
    P("## Reading")
    P("")
    P("**File-citation hallucination rate** is the headline number — it does not depend")
    P("on body access (the LLM cannot infer *paths* from the body if they aren't there).")
    P("Compare to the buggy-run rate (10/35, 29%) to see whether body access reduces")
    P("path-fabrication.")
    P("")
    P("**Fabricated owners** are the most damning failure: even with the body in")
    P("context, the LLM invents authorial metadata. PR31's `Danilo Silva` was the")
    P("buggy-run example; check the parity column for whether it persists.")
    P("")
    OUT.write_text("\n".join(lines))
    print(f"Wrote {OUT}")
    print(f"\nFile-citation hallucination: {n_unverified_files}/{total}")
    print(f"Owner verified-from-body:    {n_verified_owner}/{total}")
    print(f"Owner fabricated:            {n_fabricated_owner}/{total}")
    print(f"Owner abstained:             {n_abstain_owner}/{total}")
    print(f"Handles verified-from-body:  {n_verified_handle}/{total}")
    print(f"Handles fabricated:          {n_fabricated_handle}/{total}")
    if n_fabricated_owner:
        print("\nPRs with fabricated owner claims (parity):")
        for r in rows:
            if r.get("fabricated_owners"):
                print(f"  PR{r['pr_id']}: {r['fabricated_owners']}")


if __name__ == "__main__":
    main()
