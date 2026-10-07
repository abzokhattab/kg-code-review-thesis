#!/usr/bin/env python3
"""KG-signal-leakage audit: how often does the clean-prompt review explicitly
cite a Joern caller/dependent that was in the evidence pack?

This is the quantitative version of the STRICT_VS_CLEAN_COMPARISON.md
finding. Strict prompt: "MUST cover the 9 KG criteria" → forces caller
names into the text. Clean prompt: free to ignore.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REVIEWS = REPO / "experiments" / "2026-06-11_joern_normal_prompt" / "reviews"
EVIDENCE_DIR = REPO / "experiments" / "2026-05-15_joern_kg_main" / "evidence"
OUT = REPO / "human_eval_v3_clean_2026-06-11" / "KG_LEAKAGE_AUDIT.md"


def caller_signals(ev: dict) -> list[str]:
    """Return list of distinct caller-side identifiers (file basenames + function names)."""
    sigs: set[str] = set()
    for c in ev.get("callers", []) or []:
        if isinstance(c, dict):
            p = c.get("path") or c.get("file")
            fn = c.get("from_function") or c.get("function") or c.get("name")
            if p:
                sigs.add(Path(p).name)
            if fn and len(fn) >= 4:
                sigs.add(fn)
    for d in ev.get("dependent_files", []) or []:
        if isinstance(d, dict):
            p = d.get("path") or d.get("file")
            if p:
                sigs.add(Path(p).name)
    return sorted(sigs)


def has_caller_in_review(review_text: str, sigs: list[str]) -> list[str]:
    found = []
    for s in sigs:
        if not s or len(s) < 3:
            continue
        # word-boundary match
        if re.search(r"\b" + re.escape(s) + r"\b", review_text):
            found.append(s)
    return found


def main():
    rows = []
    for f in sorted(REVIEWS.glob("pr*_kg.md")):
        pr_id = int(f.stem.replace("pr", "").replace("_kg", ""))
        ev_path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
        if not ev_path.exists():
            continue
        ev = json.loads(ev_path.read_text())
        sigs = caller_signals(ev)
        text = f.read_text()
        found = has_caller_in_review(text, sigs)
        rows.append({
            "pr_id": pr_id,
            "n_caller_signals_available": len(sigs),
            "n_cited_in_review": len(found),
            "cited": found,
            "available_sample": sigs[:5],
        })

    n = len(rows)
    with_callers = sum(1 for r in rows if r["n_caller_signals_available"] > 0)
    cite_any = sum(1 for r in rows if r["n_cited_in_review"] > 0 and r["n_caller_signals_available"] > 0)

    lines = []
    P = lines.append
    P("# KG-signal leakage audit — clean Joern reviews")
    P("")
    P("**Question:** when Joern's evidence pack supplies caller/dependent symbols,")
    P("how often does the clean-prompt review actually cite them in the text?")
    P("")
    P("This is the quantitative companion to `STRICT_VS_CLEAN_COMPARISON.md`.")
    P("If the clean prompt routinely *omits* the caller signal, the d_z=+0.58")
    P("effect is being driven by something other than visible structural")
    P("citations — and the human study under the clean prompt will struggle.")
    P("")
    P(f"## Summary")
    P("")
    P(f"- Reviews audited: **{n}**")
    P(f"- PRs whose Joern pack supplied ≥1 caller/dependent signal: **{with_callers}**")
    P(f"- Of those, reviews that **cited** ≥1 such signal: **{cite_any} / {with_callers}** = **{cite_any/max(1,with_callers)*100:.0f}%**")
    P("")
    P("## Per-PR detail")
    P("")
    P("| PR | Joern signals available | Cited in review | Citation rate | Cited symbols |")
    P("|---:|---:|---:|---:|:---|")
    for r in rows:
        avail = r["n_caller_signals_available"]
        cited = r["n_cited_in_review"]
        rate = (cited / avail * 100) if avail else 0
        sym = ", ".join(r["cited"][:5]) + (" …" if len(r["cited"]) > 5 else "")
        P(f"| {r['pr_id']} | {avail} | {cited} | {rate:.0f}% | {sym} |")
    P("")
    P("## Reading")
    P("")
    P("Lower citation rate = clean prompt is letting the LLM ignore the structural")
    P("context. This is exactly what the strict-prompt forced via MUSTs and what")
    P("the user-study NAMED_ENTITY_AUDIT noticed at the rater level (PR38: 2 entities).")
    P("")
    P("If overall citation rate is below 50%, the d_z=+0.58 effect is happening")
    P("through the LLM's *implicit* use of the structural context — re-phrasing,")
    P("framing, hedging — not through explicit citations the rater can see.")
    P("That tracks with the user's complaint that some reviews 'look similar'.")
    P("")
    OUT.write_text("\n".join(lines))
    print(f"Wrote {OUT}")
    print(f"Caller-citation rate: {cite_any}/{with_callers} = {cite_any/max(1,with_callers)*100:.0f}%")


if __name__ == "__main__":
    main()
