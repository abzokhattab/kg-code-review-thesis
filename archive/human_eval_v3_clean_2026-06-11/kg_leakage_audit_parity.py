#!/usr/bin/env python3
"""KG-signal leakage on PARITY reviews.

Same metric as the buggy-run audit, but on the parity reviews (body included
in prompt). Hypothesis from the redundancy framing: with body present, the
LLM has more ways to satisfy the rubric, so caller-citation rate may *drop*
even further. Or it may stay flat if the LLM has stable habits.

Also computes a per-PR delta (parity_rate - buggy_rate) so we can see whether
adding body shifts the surfacing of structural signal.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PARITY_REVIEWS = REPO / "experiments" / "2026-06-11_joern_normal_prompt_parity" / "reviews"
BUGGY_REVIEWS = REPO / "experiments" / "2026-06-11_joern_normal_prompt" / "reviews"
EVIDENCE_DIR = REPO / "experiments" / "2026-05-15_joern_kg_main" / "evidence"
OUT = REPO / "human_eval_v3_clean_2026-06-11" / "KG_LEAKAGE_AUDIT_PARITY.md"


def caller_signals(ev: dict) -> list[str]:
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


def found_in(text: str, sigs: list[str]) -> list[str]:
    found = []
    for s in sigs:
        if not s or len(s) < 3:
            continue
        if re.search(r"\b" + re.escape(s) + r"\b", text):
            found.append(s)
    return found


def main():
    rows = []
    for f in sorted(PARITY_REVIEWS.glob("pr*_kg.md")):
        pr_id = int(f.stem.replace("pr", "").replace("_kg", ""))
        ev_path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
        if not ev_path.exists():
            continue
        ev = json.loads(ev_path.read_text())
        sigs = caller_signals(ev)
        ptext = f.read_text()
        btext_path = BUGGY_REVIEWS / f.name
        btext = btext_path.read_text() if btext_path.exists() else ""
        p_found = found_in(ptext, sigs)
        b_found = found_in(btext, sigs)
        rows.append({
            "pr_id": pr_id,
            "n_signals": len(sigs),
            "parity_cited": len(p_found),
            "buggy_cited": len(b_found),
            "delta": len(p_found) - len(b_found),
            "parity_symbols": p_found[:5],
            "buggy_symbols": b_found[:5],
        })

    n = len(rows)
    with_sigs = sum(1 for r in rows if r["n_signals"] > 0)
    parity_cite_any = sum(1 for r in rows if r["parity_cited"] > 0 and r["n_signals"] > 0)
    buggy_cite_any = sum(1 for r in rows if r["buggy_cited"] > 0 and r["n_signals"] > 0)
    total_avail = sum(r["n_signals"] for r in rows)
    total_parity = sum(r["parity_cited"] for r in rows)
    total_buggy = sum(r["buggy_cited"] for r in rows)

    lines = []
    P = lines.append
    P("# KG-signal leakage — PARITY reviews")
    P("")
    P("Same metric as `KG_LEAKAGE_AUDIT.md` (buggy run), but on the parity reviews.")
    P("Reports both rates side-by-side so we can see whether adding the PR body to")
    P("the prompt shifts how often the LLM surfaces caller/dependent symbols.")
    P("")
    P(f"## Summary")
    P("")
    P(f"- Reviews audited: **{n}** (parity vs buggy, same 35 PRs)")
    P(f"- PRs with ≥1 caller signal in evidence: **{with_sigs}**")
    P("")
    P("**Binary citation rate (≥1 signal cited in review):**")
    P("")
    P(f"- Parity: **{parity_cite_any} / {with_sigs}** = **{parity_cite_any/max(1,with_sigs)*100:.0f}%**")
    P(f"- Buggy : **{buggy_cite_any} / {with_sigs}** = **{buggy_cite_any/max(1,with_sigs)*100:.0f}%**")
    P("")
    P("**Aggregate signal density (total cited / total available):**")
    P("")
    P(f"- Parity: **{total_parity} / {total_avail}** = **{total_parity/max(1,total_avail)*100:.1f}%**")
    P(f"- Buggy : **{total_buggy} / {total_avail}** = **{total_buggy/max(1,total_avail)*100:.1f}%**")
    P("")
    delta_total = total_parity - total_buggy
    P(f"**Parity − buggy delta in symbols cited: {delta_total:+d}** "
      f"({'parity surfaces more' if delta_total > 0 else 'parity surfaces fewer' if delta_total < 0 else 'unchanged'})")
    P("")
    P("## Per-PR detail")
    P("")
    P("| PR | Signals available | Parity cited | Buggy cited | Δ (parity − buggy) |")
    P("|---:|---:|---:|---:|---:|")
    for r in rows:
        P(f"| {r['pr_id']} | {r['n_signals']} | {r['parity_cited']} | {r['buggy_cited']} | {r['delta']:+d} |")
    P("")
    P("## Reading")
    P("")
    P("If parity cites *fewer* caller signals than buggy, that supports the claim")
    P("that PR body and KG context are partially substitutable: when the body is")
    P("available, the LLM leans on body content and surfaces less of the caller")
    P("graph.")
    P("")
    P("If the rates are similar, the LLM has stable surfacing habits and the")
    P("body acts as a *separate* source rather than a substitute. In that case the")
    P("d_z drop from +0.58 to +0.30 is still real but the redundancy mechanism")
    P("isn't load-bearing — the bug just inflated the buggy number for some other")
    P("reason (e.g., baseline judges scored body-less reviews more harshly).")
    P("")
    OUT.write_text("\n".join(lines))
    print(f"Wrote {OUT}")
    print(f"\nParity binary citation rate: {parity_cite_any}/{with_sigs} = {parity_cite_any/max(1,with_sigs)*100:.0f}%")
    print(f"Buggy  binary citation rate: {buggy_cite_any}/{with_sigs} = {buggy_cite_any/max(1,with_sigs)*100:.0f}%")
    print(f"Parity total cites: {total_parity} / {total_avail}")
    print(f"Buggy  total cites: {total_buggy} / {total_avail}")
    print(f"Delta (parity − buggy): {delta_total:+d} symbols")


if __name__ == "__main__":
    main()
