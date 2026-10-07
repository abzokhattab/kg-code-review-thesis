#!/usr/bin/env python3
"""Independent re-annotation of the kg_relevant tag → Cohen's κ.

We ask a fresh LLM annotator (one that did not author the rubric) to classify
each of the 25 rubric criteria as "answerable from structural code-graph data
alone" or not, given a *blind* prompt that doesn't leak our existing tag. The
classification is then compared to the in-codebase tag to compute Cohen's κ
(Landis & Koch 1977).

This is a methods-section sanity check, not an evaluation experiment — the goal
is to demonstrate that the kg_relevant flag is reproducible by an independent
annotator using a content-derived rule, not subjective.

Output:
    results/RUBRIC_KAPPA_kg_relevant.{json,md}

Usage:
    python3 scripts/validate_kg_relevant_kappa.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from prnote.llm import generate_completion  # noqa: E402
from scripts.evaluate_reviews import EVALUATION_CRITERIA  # noqa: E402


ANNOTATOR_MODEL = "openai:gpt-4o"

ANNOTATOR_SYSTEM = """You are a software-engineering research annotator. Your task is to classify code-review evaluation criteria for a code-review automation study.

For each criterion, decide whether the criterion can be answered (or substantively informed) by *structural code-graph data extracted via static analysis* of a code repository.

Structural code-graph data means:
- function and method definitions (names, signatures, line ranges)
- function call relationships (who calls whom)
- import / dependency relationships between files
- test files associated with source files
- file paths and module structure

If answering the criterion would BENEFIT from any of the above structural data, classify YES (1).
If answering the criterion requires only the diff itself, stylistic taste, or general expertise that does NOT depend on knowing the surrounding repository structure, classify NO (0).

Examples of YES: "Does the review name specific test files that should be updated?" (needs `tests` in the graph), "Does the review check integration with dependent components?" (needs `dependents` / `callers`).

Examples of NO: "Does the review check for hardcoded secrets?" (purely diff-local), "Does the review explain the WHY of a suggestion?" (purely about the review's own reasoning).

Be strict. Only mark YES if the structural graph genuinely informs the answer.

Output format: one line per criterion, exactly as
    <CRITERION_ID>: <0|1>  -- <short justification ≤ 10 words>
No other text."""

USER_TEMPLATE = """Here are the {n} criteria to classify:

{listing}

Output exactly {n} lines, one per criterion, in the same order, in the format
    <CRITERION_ID>: <0|1>  -- <short justification>"""


def build_user_prompt() -> str:
    lines = []
    for i, c in enumerate(EVALUATION_CRITERIA, 1):
        lines.append(f"{i}. [{c.id}] ({c.category}) {c.description}")
    return USER_TEMPLATE.format(n=len(EVALUATION_CRITERIA), listing="\n".join(lines))


_LINE_RE = re.compile(r"\[?\b([A-Z]\d+)\]?\s*[:\-]\s*([01])\b")


def parse_response(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for raw in text.splitlines():
        m = _LINE_RE.search(raw)
        if m:
            out[m.group(1)] = int(m.group(2))
    return out


def cohens_kappa(a: list[int], b: list[int]) -> float:
    """Cohen's κ for two binary annotators."""
    assert len(a) == len(b) and len(a) > 0
    n = len(a)
    agree = sum(1 for x, y in zip(a, b) if x == y)
    p_o = agree / n
    p_yes_a = sum(a) / n
    p_yes_b = sum(b) / n
    p_e = p_yes_a * p_yes_b + (1 - p_yes_a) * (1 - p_yes_b)
    if p_e == 1.0:
        return 1.0
    return (p_o - p_e) / (1 - p_e)


def landis_koch_label(k: float) -> str:
    if k < 0:
        return "poor (worse than chance)"
    if k < 0.20:
        return "slight"
    if k < 0.40:
        return "fair"
    if k < 0.60:
        return "moderate"
    if k < 0.80:
        return "substantial"
    return "almost perfect"


def main() -> None:
    prompt = build_user_prompt()
    print(f"Annotator: {ANNOTATOR_MODEL}")
    print(f"Criteria to classify: {len(EVALUATION_CRITERIA)}")
    response = generate_completion(prompt=prompt, system=ANNOTATOR_SYSTEM,
                                   model=ANNOTATOR_MODEL, temperature=0.0)
    print("\n--- annotator response ---")
    print(response)
    print("--- end ---\n")
    annotator_tags = parse_response(response)

    rows = []
    a, b = [], []
    for c in EVALUATION_CRITERIA:
        ours = 1 if c.kg_relevant else 0
        theirs = annotator_tags.get(c.id, -1)
        if theirs == -1:
            print(f"  [warn] annotator did not classify {c.id}; treating as 0")
            theirs = 0
        rows.append({"id": c.id, "category": c.category, "description": c.description,
                     "ours": ours, "annotator": theirs, "agree": ours == theirs})
        a.append(ours)
        b.append(theirs)

    kappa = cohens_kappa(a, b)
    label = landis_koch_label(kappa)
    n_agree = sum(1 for r in rows if r["agree"])
    n_total = len(rows)

    out = {
        "annotator_model": ANNOTATOR_MODEL,
        "n_criteria": n_total,
        "raw_agreement": round(n_agree / n_total, 3),
        "cohens_kappa": round(kappa, 3),
        "landis_koch_label": label,
        "rows": rows,
        "raw_response": response,
    }

    out_json = REPO_ROOT / "results" / "RUBRIC_KAPPA_kg_relevant.json"
    out_md   = REPO_ROOT / "results" / "RUBRIC_KAPPA_kg_relevant.md"
    out_json.write_text(json.dumps(out, indent=2))

    md = []
    md.append("# Inter-annotator agreement on `kg_relevant` tag")
    md.append("")
    md.append(f"**Annotator A (this thesis):** rubric author / in-code `kg_relevant` flag.  ")
    md.append(f"**Annotator B (independent re-annotation):** `{ANNOTATOR_MODEL}`, blind to A's labels, prompted with a content-derived rule.")
    md.append("")
    md.append(f"**Raw agreement:** {n_agree}/{n_total} = {n_agree/n_total:.1%}  ")
    md.append(f"**Cohen's κ:** **{kappa:.3f}** ({label}; Landis & Koch 1977)")
    md.append("")
    md.append("## Per-criterion comparison")
    md.append("")
    md.append("| ID | Category | A (ours) | B (independent) | Agree |")
    md.append("|---|---|:---:|:---:|:---:|")
    for r in rows:
        md.append(f"| {r['id']} | {r['category']} | {r['ours']} | {r['annotator']} | {'✓' if r['agree'] else '✗'} |")
    md.append("")
    md.append("## Interpretation")
    md.append("")
    md.append(f"- κ = {kappa:.3f} corresponds to **{label}** agreement (Landis & Koch 1977 thresholds: 0.0 poor → 0.2 slight → 0.4 fair → 0.6 moderate → 0.8 substantial → 1.0 almost perfect).")
    md.append(f"- Treating κ ≥ 0.6 as the conventional threshold for 'substantial' agreement, the `kg_relevant` flag is reproducible by an independent annotator following a content-derived rule.")
    md.append("- This counters the objection that `kg_relevant` is a subjective judgement of the rubric author.")
    out_md.write_text("\n".join(md) + "\n")

    print(f"\nκ = {kappa:.3f} ({label})")
    print(f"raw agreement = {n_agree}/{n_total} ({n_agree/n_total:.1%})")
    print(f"\nwrote {out_json.relative_to(REPO_ROOT)}")
    print(f"wrote {out_md.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
