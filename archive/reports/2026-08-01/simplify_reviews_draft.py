#!/usr/bin/env python3
"""
simplify_reviews_draft.py — DRAFT readability pass on the 12 study reviews
(2026-08-01, prompted by pilot-rater feedback: "too much text, rambles").

This does NOT touch the live study. It writes simplified copies to
reports/2026-08-01/simplified_reviews/ for inspection.

Rules — uniform, direction-blind, defined on the template surface (same
class of operation as normalize_review_surfaces.py, 2026-07-13):

  R1  Drop the boilerplate title "# Review Note — Evidence-Anchored"
      (the UI already labels the texts Review A / Review B).
  R2  Drop the "**Scope:** ..." line — it restates the PR description
      shown directly above in the UI.
  R3  In "## Problem" and "## Impact": strip the bold jargon label from
      each bullet ("1. **Integration Risk:** The change..." -> "1. The
      change...").  The category label is restated by the sentence in
      every instance; the labels are the main source of the "harsh
      consultant text" feel.  Labels in "## Recommendation" (Fix /
      Tests / Risks / Documentation) are plain action words and are KEPT.
  R4  Plain-language section headers:
        "## Problem" -> "## Problems found"
        "## Evidence" -> "## Files and lines referenced"
        "## Impact" -> "## What could go wrong"
        "## Recommendation (Fix / Tests / Risks)" -> "## Suggestions"

No sentence is reworded, added, or removed. Content order unchanged.

Verification printed at the end:
  V1  The set of file/line references is IDENTICAL before/after, per file.
  V2  Word-count reduction is reported per arm (must be symmetric).
"""
import re
from pathlib import Path

SRC = Path("/Users/akhattab/ai/experiments/2026-07-06_user_study_prs/reviews")
DST = Path(__file__).resolve().parent / "simplified_reviews"

HEADER_MAP = {
    "## Problem": "## Problems found",
    "## Evidence": "## Files and lines referenced",
    "## Impact": "## What could go wrong",
    "## Recommendation (Fix / Tests / Risks)": "## Suggestions",
}
STRIP_LABEL_SECTIONS = {"## Problem", "## Impact"}

NUM_LABEL = re.compile(r"^(\d+\.) \*\*[^:*]+:\*\*\s*(.+)$")
DASH_LABEL = re.compile(r"^(-) \*\*[^:*]+:\*\*\s*(.+)$")
FILE_REF = re.compile(r"[\w./-]+\.(?:py|md|txt|rst|cfg|toml|json)(?::[\d–-]+)?")


def simplify(text: str) -> str:
    out, section = [], None
    for line in text.split("\n"):
        if line.startswith("# ") and "Review Note" in line:
            continue  # R1
        if line.startswith("**Scope:**"):
            continue  # R2
        if line.startswith("## "):
            section = line.strip()
            out.append(HEADER_MAP.get(section, line))  # R4
            continue
        if section in STRIP_LABEL_SECTIONS:  # R3
            m = NUM_LABEL.match(line) or DASH_LABEL.match(line)
            if m:
                out.append(f"{m.group(1)} {m.group(2)}")
                continue
        out.append(line)
    # collapse the blank lines left behind by R1/R2
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"
    return result


def main():
    DST.mkdir(parents=True, exist_ok=True)
    stats = {"baseline_strict": [0, 0], "kg": [0, 0]}
    problems = []
    for f in sorted(SRC.glob("*_baseline_strict.md")) + sorted(SRC.glob("*_kg.md")):
        old = f.read_text()
        new = simplify(old)
        (DST / f.name).write_text(new)

        refs_old = sorted(set(FILE_REF.findall(old)))
        refs_new = sorted(set(FILE_REF.findall(new)))
        if refs_old != refs_new:
            problems.append((f.name, set(refs_old) ^ set(refs_new)))

        arm = "kg" if f.stem.endswith("_kg") else "baseline_strict"
        stats[arm][0] += len(old.split())
        stats[arm][1] += len(new.split())
        print(f"{f.name:35s} {len(old.split()):4d}w -> {len(new.split()):4d}w")

    print("\n=== V1 file-reference integrity ===")
    if problems:
        for name, diff in problems:
            print(f"  MISMATCH {name}: {diff}")
    else:
        print("  OK — reference sets identical in all 12 files")

    print("\n=== V2 symmetry ===")
    for arm, (o, n) in stats.items():
        print(f"  {arm:16s} {o}w -> {n}w  (-{100*(o-n)/o:.1f}%)")


if __name__ == "__main__":
    main()
