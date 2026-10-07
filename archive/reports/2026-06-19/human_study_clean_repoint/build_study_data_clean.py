#!/usr/bin/env python3
"""
build_study_data_clean.py  (Decision 19 — clean normal-prompt re-point)

Rebuilds the human-study stimulus file using the CLEAN, normal-prompt
comparison instead of the strict-prompt comparison locked by Decision 18.

  mode_a = baseline   (normal production prompt)  -> outputs/luca_prs_v2/pr<N>_baseline.md
  mode_b = joern      (normal production prompt)  -> experiments/2026-06-11_joern_normal_prompt/reviews/pr<N>_kg.md

Why this exists
---------------
Decision 18 (2026-06-13) pointed the live human study at `baseline_strict`
vs `joern`, both under a STRICT prompt that mandates coverage of the 9
KG-relevant criteria. That prompt is the documented confound behind the
inflated d_z=+1.07/+1.34 Joern numbers (THESIS_OVERVIEW_FOR_JUDGE.md
lines 154-181). Validating the judge against humans on the confounded
arm does not validate the thesis HEADLINE, which is the normal-prompt
result.

The clean Joern run (experiments/2026-06-11_joern_normal_prompt/, dated
2026-06-11, two days BEFORE Decision 18) produced a clean, significant,
NON-confounded effect: KG-relevant d_z=+0.58, p=0.003, total d_z=+0.61,
p=0.001 (RESULTS.md). This build re-points the human study at THAT
comparison so RQ3 validates the defensible headline.

No LLM calls. Cost $0. Idempotent. Reads only review markdown that
already exists on disk; assembles JSON.

The 6-criterion human-rating subscale {F3*, F2*, T3, Q5, R1, C6} and all
surface-form cleanups are carried over verbatim from
human_eval_v3/scripts/build_study_data_v2.py (no criteria added/removed).

Usage:
  python3 reports/2026-06-19/human_study_clean_repoint/build_study_data_clean.py
  python3 reports/2026-06-19/human_study_clean_repoint/build_study_data_clean.py --pr-ids 22 24 31 38 44 47
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any

# This file lives in reports/2026-06-19/human_study_clean_repoint/, so the
# repo root is three levels up.
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
EVIDENCE_DIR = os.path.join(REPO_ROOT, "data", "luca_prs_v2")
BASELINE_REVIEW_DIR = os.path.join(REPO_ROOT, "outputs", "luca_prs_v2")
JOERN_CLEAN_REVIEW_DIR = os.path.join(
    REPO_ROOT, "experiments", "2026-06-11_joern_normal_prompt", "reviews"
)
OUT_PATH = os.path.join(os.path.dirname(__file__), "study_data.json")

# Default: the Decision-18 PR set, re-pointed to the clean comparison
# (faithful arm-swap). NOTE: under clean scoring this set is 5W/0T/1L;
# see DECISION_19_repoint.md for the balance caveat and the recommended
# balanced re-selection.
FINAL = [22, 24, 31, 38, 44, 47]

CRITERIA = [
    {
        "id": "F3*",
        "category": "Functionality",
        "description": (
            "Does the review name concrete components, APIs, or design "
            "patterns affected by the changes?"
        ),
    },
    {
        "id": "F2*",
        "category": "Functionality",
        "description": (
            "Does the review describe concrete edge cases, boundary "
            "conditions, or error-handling gaps?"
        ),
    },
    {
        "id": "T3",
        "category": "Tests",
        "description": (
            "Does the review reference concrete test files or suggest "
            "which tests should be added/updated?"
        ),
    },
    {
        "id": "Q5",
        "category": "Quality",
        "description": (
            "Does the review give a concrete reason for each suggestion "
            "(e.g. 'X could cause Y')?"
        ),
    },
    {
        "id": "R1",
        "category": "Readability",
        "description": (
            "Does the review comment on code clarity, naming "
            "conventions, or function organization?"
        ),
    },
    {
        "id": "C6",
        "category": "Completeness",
        "description": (
            "Does the review cover the obvious issues in the PR without "
            "obvious missing information?"
        ),
    },
]

COMPARISONS = [
    {
        "id": "bl_vs_joern_normal",
        "label": "Baseline vs Joern-KG (normal prompt)",
        "mode_a": "baseline",
        "mode_b": "joern",
    },
]

MODES = ["baseline", "joern"]


# ─── Cleanup helpers (verbatim from build_study_data_v2.py) ────────────────


def strip_code_fence(text: str) -> str:
    s = text.strip("\n")
    lines = s.split("\n")
    if lines and lines[0].strip() == "```":
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def strip_kg_traceability_leak(text: str) -> str:
    lines = text.split("\n")
    out = []
    in_traceability = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"^#{1,3}\s*Traceability\b", stripped):
            in_traceability = True
            out.append(line)
            continue
        if in_traceability and re.match(r"^#{1,3}\s+\S", stripped):
            in_traceability = False
        if in_traceability and re.match(
            r"^[-*]\s*\**Code\s*Owners?\**\s*[:\-]", stripped, re.IGNORECASE
        ):
            continue
        out.append(line)
    return "\n".join(out).strip()


def drop_empty_traceability_section(text: str) -> str:
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if re.match(r"^#{1,3}\s*Traceability\b", stripped):
            j = i + 1
            section_lines = []
            while j < len(lines) and not re.match(
                r"^#{1,3}\s+\S", lines[j].strip()
            ):
                section_lines.append(lines[j])
                j += 1
            section_text = "\n".join(section_lines).strip()
            stripped_section = re.sub(
                r"[-*\s]+", " ", section_text, flags=re.IGNORECASE
            ).strip().lower()
            stripped_section = re.sub(r"\*+", "", stripped_section).strip()
            empty_section = (
                not stripped_section
                or stripped_section in {"not specified", "not specified.", "n/a", "none"}
                or re.match(r"^[a-z ]{2,30}\s*:\s*not specified\.?$", stripped_section) is not None
                or re.match(r"^[a-z ]{2,30}\s+not specified\.?$", stripped_section) is not None
            )
            if empty_section:
                i = j
                continue
        out.append(line)
        i += 1
    cleaned = "\n".join(out).rstrip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def flatten_evidence_structure(text: str) -> str:
    """Neutralise the Joern Evidence-section formatting mode-leak.

    Drops bold banner labels and indentation only; every path, line
    number, caller and test reference is preserved verbatim. Symmetric
    across both arms. (Verbatim from build_study_data_v2.py.)
    """
    lines = text.split("\n")
    out = []
    in_evidence = False
    bold_label_prefix = re.compile(r"^\*\*[^*]+?\*\*\s*:?\s*")
    bullet = re.compile(r"^(\s*)([-*])\s+(.*)$")
    for line in lines:
        stripped = line.strip()
        if re.match(r"^#{1,3}\s*Evidence\b", stripped):
            in_evidence = True
            out.append(line)
            continue
        if in_evidence and re.match(r"^#{1,3}\s+\S", stripped):
            in_evidence = False
        if in_evidence:
            m = bullet.match(line)
            if m:
                content = bold_label_prefix.sub("", m.group(3)).strip()
                if not content:
                    continue
                out.append(f"- {content}")
                continue
        out.append(line)
    cleaned = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def normalise_review(raw: str) -> str:
    return flatten_evidence_structure(
        drop_empty_traceability_section(
            strip_kg_traceability_leak(strip_code_fence(raw))
        )
    )


def annotate_truncation(diff: str, threshold: int = 50000) -> str:
    if len(diff) >= threshold:
        return (
            diff.rstrip()
            + "\n\n[... diff truncated at 50 kB. Real PR contains more "
            "files than shown above. Judge only on the visible content.]\n"
        )
    return diff


# ─── Loaders ──────────────────────────────────────────────────────────────


def load_evidence(pr_id: int) -> dict[str, Any]:
    path = os.path.join(EVIDENCE_DIR, f"pr{pr_id}_evidence.json")
    with open(path) as f:
        return json.load(f)


def load_pr_body(ev: dict) -> str:
    return (ev.get("pr") or {}).get("body") or ""


def load_review(pr_id: int, mode: str) -> str:
    if mode == "joern":
        path = os.path.join(JOERN_CLEAN_REVIEW_DIR, f"pr{pr_id}_kg.md")
    elif mode == "baseline":
        path = os.path.join(BASELINE_REVIEW_DIR, f"pr{pr_id}_baseline.md")
    else:
        raise ValueError(f"Unsupported mode for clean re-point: {mode}")
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    raise FileNotFoundError(
        f"No review found for PR {pr_id} mode {mode} at {path}."
    )


PR_NUMBER_TO_REPO = {
    1: "godotengine/godot",
    14: "grafana/grafana",
    22: "apache/kafka",
    24: "scikit-learn/scikit-learn",
    30: "godotengine/godot",
    31: "scikit-learn/scikit-learn",
    38: "grafana/grafana",
    42: "scikit-learn/scikit-learn",
    44: "scikit-learn/scikit-learn",
    47: "jenkinsci/jenkins",
}


def load_repo_name(pr_id: int, ev: dict) -> str:
    pr = ev.get("pr") or {}
    if pr.get("repo_owner") and pr.get("repo_name"):
        return f"{pr['repo_owner']}/{pr['repo_name']}"
    url = pr.get("url") or ""
    m = re.search(r"github\.com/([^/]+/[^/]+)/pull/", url)
    if m:
        return m.group(1)
    return PR_NUMBER_TO_REPO.get(pr_id, "?")


def load_repo_url(ev: dict) -> str:
    return (ev.get("pr") or {}).get("url") or ""


# ─── Builder ──────────────────────────────────────────────────────────────


def build_pr_block(pr_id: int, modes: list[str]) -> dict[str, Any]:
    ev = load_evidence(pr_id)
    pr = ev.get("pr") or {}
    diff = annotate_truncation(ev.get("full_diff") or "")
    reviews = {}
    for mode in modes:
        try:
            raw = load_review(pr_id, mode)
        except FileNotFoundError as e:
            print(f"WARNING: {e}", file=sys.stderr)
            continue
        reviews[mode] = normalise_review(raw)
    return {
        "pr_id": pr_id,
        "repo": load_repo_name(pr_id, ev),
        "pr_number": pr.get("number"),
        "title": pr.get("title", ""),
        "url": load_repo_url(ev),
        "body": load_pr_body(ev),
        "diff": diff,
        "reviews": reviews,
    }


def build(pr_ids: list[int], out_path: str) -> None:
    out = {
        "version": "clean-bl-vs-joern-normal-v1",
        "decision": "Decision 19 (2026-06-19) — clean normal-prompt re-point",
        "criteria": CRITERIA,
        "modes": MODES,
        "comparisons": COMPARISONS,
        "prs": [build_pr_block(pid, MODES) for pid in pr_ids],
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {out_path}")
    print(
        f"  {len(out['prs'])} PRs x {len(out['comparisons'])} comparison "
        f"= {len(out['prs']) * len(out['comparisons'])} trials per rater"
    )
    for blk in out["prs"]:
        have = sorted(blk["reviews"].keys())
        print(f"  PR{blk['pr_id']:>3}  {blk['repo']:<28}  reviews: {have}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr-ids", nargs="+", type=int, default=FINAL)
    ap.add_argument("--out", default=OUT_PATH)
    a = ap.parse_args()
    build(a.pr_ids, a.out)


if __name__ == "__main__":
    main()
