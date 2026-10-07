#!/usr/bin/env python3
"""
normalize_review_surfaces.py — blinding-safe surface normalization (2026-07-13).

A blinding audit before supervisor submission found two systematic surface
tells that let a rater identify the arm without reading content:

  1. The prompt-scaffolding tail: everything from "## Traceability" to EOF
     ("Code Owners: Not specified", the literal "MANDATORY COVERAGE:" header
     in 2 files, and a 9-point FUNCTIONALITY/TESTS/... checklist present in
     8 of 12 files). This is machine-readable coverage scaffolding required
     by the generation prompt, not review content a human would receive.
  2. Evidence subsection labels ("**Diff References:**", "**Structural
     Context:**", "**Callers:**", "**Test Files:**") present only in KG
     reviews; baselines use flat bullet lists.

Rules (applied uniformly to ALL 12 reviews, defined on the artifact surface,
never on the mode label — direction-blind by construction):

  R1  Truncate each review at the "## Traceability" heading.
  R2  Inside "## Evidence": drop label-only bullets ("- **X:**" with nothing
      after), strip inline "- **X:** content" labels to "- content", and
      de-indent nested bullets to top level. No reference or annotation text
      is added or removed.

Idempotent: re-running on normalized files is a no-op. $0.
Downstream layers (answer key, counts, markers, summaries) must be rebuilt
after this runs — see README pipeline step 4b.
"""
import re
from pathlib import Path

REVIEWS = Path(__file__).resolve().parent / "reviews"

LABEL_ONLY = re.compile(r"^\s*- \*\*[^*]+:\*\*\s*$")
LABEL_INLINE = re.compile(r"^\s*- \*\*[^*]+:\*\*\s+(.*)$")
NESTED_BULLET = re.compile(r"^\s+- (.*)$")


def normalize(text: str) -> str:
    # R1: strip the prompt-scaffolding tail.
    idx = text.find("## Traceability")
    if idx != -1:
        text = text[:idx].rstrip() + "\n"

    # R2: flatten the Evidence section.
    lines = text.split("\n")
    out, in_evidence = [], False
    for line in lines:
        if line.startswith("## "):
            in_evidence = line.strip() == "## Evidence"
            out.append(line)
            continue
        if in_evidence:
            if LABEL_ONLY.match(line):
                continue
            m = LABEL_INLINE.match(line)
            if m:
                out.append(f"- {m.group(1)}")
                continue
            m = NESTED_BULLET.match(line)
            if m:
                out.append(f"- {m.group(1)}")
                continue
        out.append(line)
    return "\n".join(out)


def main():
    changed = 0
    for path in sorted(REVIEWS.glob("*_baseline_strict.md")) + sorted(REVIEWS.glob("*_kg.md")):
        old = path.read_text()
        new = normalize(old)
        if new != old:
            path.write_text(new)
            changed += 1
            print(f"normalized {path.name}")
        else:
            print(f"unchanged  {path.name}")
    print(f"\n{changed} file(s) rewritten")


if __name__ == "__main__":
    main()
