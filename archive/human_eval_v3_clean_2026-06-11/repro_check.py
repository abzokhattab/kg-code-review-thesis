#!/usr/bin/env python3
"""T=0.0 reproducibility check.

Re-generate the clean-Joern reviews for 2 PRs and compare to the
on-disk versions. At T=0.0 with the same prompt/model/SDK we expect
*identical* output (or very close — OpenAI's T=0.0 is mostly but not
strictly deterministic).
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from prnote.llm import generate_completion  # noqa: E402
from prnote.note import (  # noqa: E402
    SYSTEM_PROMPT_KG, format_kg_context, get_diff_from_evidence,
)

EVIDENCE_DIR = REPO / "experiments" / "2026-05-15_joern_kg_main" / "evidence"
ORIG_REVIEWS = REPO / "experiments" / "2026-06-11_joern_normal_prompt" / "reviews"

def regen(pr_id: int) -> tuple[str, str]:
    ev = json.loads((EVIDENCE_DIR / f"pr{pr_id}_evidence.json").read_text())
    diff = get_diff_from_evidence(ev, max_chars=50000)
    title = ev.get("pr", {}).get("title", f"PR {pr_id}")
    ctx = format_kg_context(ev)
    prompt = (
        f"## Pull Request: {title}\n\n"
        f"## Diff\n```\n{diff}\n```\n"
        f"{ctx}\n\n"
        "Please generate an evidence-anchored review note following the specified format."
    )
    out = generate_completion(prompt=prompt, system=SYSTEM_PROMPT_KG, model="openai:gpt-4o", temperature=0.0)
    orig = (ORIG_REVIEWS / f"pr{pr_id}_kg.md").read_text()
    return orig, out

def chunk_diff(a: str, b: str) -> str:
    if a == b:
        return "IDENTICAL"
    al = a.splitlines()
    bl = b.splitlines()
    diff_lines = []
    n = max(len(al), len(bl))
    for i in range(n):
        la = al[i] if i < len(al) else "<<<EOF>>>"
        lb = bl[i] if i < len(bl) else "<<<EOF>>>"
        if la != lb:
            diff_lines.append(f"  L{i+1}: orig: {la[:100]}")
            diff_lines.append(f"        new:  {lb[:100]}")
            if len(diff_lines) > 12:
                diff_lines.append("  ...")
                break
    return "\n".join(diff_lines)

def main():
    for pr_id in [1, 31]:
        orig, new = regen(pr_id)
        h_orig = hashlib.md5(orig.encode()).hexdigest()
        h_new = hashlib.md5(new.encode()).hexdigest()
        match = "MATCH" if h_orig == h_new else "DIFFERS"
        print(f"PR{pr_id}: orig={h_orig[:8]} new={h_new[:8]} → {match}")
        if h_orig != h_new:
            print(f"  orig len: {len(orig)}, new len: {len(new)}")
            print(f"  Jaccard 5-gram: {jaccard5(orig, new):.3f}")
            print(chunk_diff(orig, new))
        print()

def jaccard5(a: str, b: str) -> float:
    def grams(s):
        return set(s[i:i+5] for i in range(len(s)-4))
    A, B = grams(a), grams(b)
    return len(A & B) / max(1, len(A | B))

if __name__ == "__main__":
    main()
