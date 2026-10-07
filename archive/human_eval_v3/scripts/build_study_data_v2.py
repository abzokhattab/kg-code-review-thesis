#!/usr/bin/env python3
"""
build_study_data_v2.py  (human_eval_v3 — v2-stimuli edition)

Builds study_data.json for the v3 human-study selection from the **cleaned
dataset_v2 evidence packs and reviews**, so the human raters and the LLM
judge see the same stimuli (essential for RQ3 = LLM-judge ↔ human kappa).

Sources (changed from human_eval_v2):

  - data/luca_prs_v2/pr<N>_evidence.json   (PR metadata + diff;
        full PR body recovered, diff cap raised to 50 kB, RAG context fixed)
  - outputs/luca_prs_v2/pr<N>_<mode>.md    (LLM-generated reviews regenerated
        against the cleaned evidence; this is the same review set the v2
        multi-judge panel scored — see results/V1_VS_V2_COMPARISON.md)

Cleanups applied (carried over from human_eval_v2; still relevant):

  * strip leading/trailing  ```  fences from each review
  * remove the "- Code Owners: ..." line from KG Traceability sections
    (a confirmed mode-leak signal in 4 of 6 v1 PRs)
  * drop empty Traceability sections after the leak strip
  * flatten the Evidence section to a single un-labelled bullet list
    (Decision 19, 2026-06-13): the Joern arm rendered Evidence as
    labelled, nested groups ('**Diff References:**', '**Structural
    Context:**', '**Callers:**', '**Test Files:**') while baseline used
    a flat list — a pure-formatting mode-leak. The flatten drops the
    bold banner words + indentation only; every path, line number,
    caller and test reference is preserved verbatim, so the treatment
    is intact and no LLM rerun is needed. The residual content-level
    tell (Joern cites non-diff files) is intrinsic to the treatment and
    is left in place as a documented limitation, not engineered away.

Diff-truncation marker logic is kept defensively but should never fire
on v2 evidence (50 kB cap, none of the kept PRs hit it).

The output schema is identical to human_eval_v2's study_data.json, so the
UI (index.html) consumes it unchanged.

Usage:
  python3 human_eval_v3/scripts/build_study_data_v2.py
  python3 human_eval_v3/scripts/build_study_data_v2.py --pr-ids 12 1 3 14
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EVIDENCE_DIR = os.path.join(REPO_ROOT, "data", "luca_prs_v2")
REVIEW_DIR = os.path.join(REPO_ROOT, "outputs", "luca_prs_v2")
OUT_PATH = os.path.join(REPO_ROOT, "human_eval_v3", "study_data.json")
PR_BODY_OVERRIDES_PATH = os.path.join(
    REPO_ROOT, "human_eval_v3", "data", "pr_body_overrides.json"
)

FINAL = [1, 14, 22, 24, 30, 42]

# Decision 18 (2026-06-02): prompt-symmetric human study — balanced win/tie/loss
# Uses baseline-strict (strict prompt, no KG context) vs joern (strict prompt + Joern KG).
# Both arms use the exact same STRICT_SYSTEM_PROMPT — only the injected context differs.
# Balanced design so the study can fail (essential for convergent validity):
#   PR44: Δ=-1 (loss)  — Python, scikit-learn
#   PR24: Δ= 0 (tie)   — Python, scikit-learn
#   PR31: Δ=+1 (weak win) — Python, scikit-learn
#   PR22: Δ=+1 (weak win) — Java, Kafka
#   PR47: Δ=+3 (strong win) — Java, Jenkins
#   PR38: Δ=+3 (strong win) — TypeScript, Grafana
FINAL_STRICT = [44, 24, 31, 22, 47, 38]

STRICT_REVIEW_DIR = os.path.join(REPO_ROOT, "experiments", "human_study_reviews")
JOERN_REVIEW_DIR = os.path.join(REPO_ROOT, "experiments", "2026-05-15_joern_kg_main", "exp_gpt4o_joern")
# Decision 17 (2026-05-13): swapped PRs 12, 21, 3 for PRs 30, 22, 42 to
# raise rater discriminability. Empirical measurement on baseline-vs-kg
# review pairs showed the previous selection's mean problem-overlap was
# 58% (with PR12 at 100% — effectively identical reviews); raters fed
# back that "the two feedbacks are mostly the same". The new selection
# has mean overlap ~27% across the same metric.
#
# Swaps (all direction-blind: chosen on overlap + diff size + KG-parseability,
# not on which mode wins):
#   - PR12 (godot, 100% overlap) → PR30 (godot, 0% overlap, unit-tests PR)
#   - PR21 (kafka, 67% overlap)  → PR22 (kafka, 0% overlap, refactor)
#   - PR3  (grafana, 50% overlap) → PR42 (sklearn, 0% overlap, refactor)
#
# Net effect on study composition:
#   - Languages: C++ ×2, TypeScript ×1, Java ×1, Python ×2  (was C++×2 TS×2 Java×1 Py×1)
#   - PR types:  feature ×2, refactor ×3, test-addition ×1   (was feature×4 refactor×2)
#   - Repos:     godot, grafana, kafka, sklearn               (same 4)
#   - Mean problem-overlap (baseline ↔ kg): drops from 58% to ~27%
#
# All 6 PRs still pass the c1-c6 direction-blind criteria from
# HUMAN_STUDY_PR_SELECTION.md (single-purpose, ≤ 50 kB diff, non-empty body,
# 100% KG-parseable, untruncated, no Jelly templates).
# See DECISION_LOG.md §17 for the full rationale.
OPTION_A = [17, 12, 1, 3, 18, 19]
OPTION_B = [17, 12, 1, 3, 14, 19]
OPTION_C_LANG_FILTERED = [12, 1, 3, 14]
OPTION_D_DECISION_16 = [12, 1, 3, 14, 21, 24]
OPTION_E_DISCRIMINATION = FINAL  # Decision 17, current

CRITERIA = [
    {
        "id": "F3*",
        "category": "Functionality",
        "description": (
            "Which review better names concrete components, APIs, or design "
            "patterns affected by the changes?"
        ),
    },
    {
        "id": "F2*",
        "category": "Functionality",
        "description": (
            "Which review better describes concrete edge cases, boundary "
            "conditions, or error-handling gaps?"
        ),
    },
    {
        "id": "T3",
        "category": "Tests",
        "description": (
            "Which review better references concrete test files or suggests "
            "which tests should be added/updated?"
        ),
    },
    {
        "id": "Q5",
        "category": "Quality",
        "description": (
            "Which review better gives a concrete reason for each suggestion "
            "(e.g. 'X could cause Y')?"
        ),
    },
    {
        "id": "R1",
        "category": "Readability",
        "description": (
            "Which review better comments on code clarity, naming "
            "conventions, or function organization?"
        ),
    },
    {
        "id": "C6",
        "category": "Completeness",
        "description": (
            "Which review better covers the obvious issues in the PR without "
            "missing important information?"
        ),
    },
]

COMPARISONS = [
    # Decision 15 (2026-05-05): trimmed to bl_vs_kg only. The kg_vs_rag
    # comparison is a secondary signal that the LLM-judge already covers
    # (results/V1_VS_V2_COMPARISON.md and BOOTSTRAP_STATS_v2.md). Halving
    # the rater session from ~25 min → ~12 min materially reduces
    # skim-and-tick risk; the central thesis question (does KG add value
    # over a vanilla diff-only baseline?) is what this comparison answers.
    {"id": "bl_vs_kg", "label": "Baseline vs KG", "mode_a": "baseline", "mode_b": "kg"},
]

COMPARISONS_STRICT = [
    # Decision 18 (2026-06-01): prompt-symmetric comparison.
    # Both arms use the same strict prompt; only the KG context differs.
    {"id": "bl_vs_joern", "label": "Baseline vs Joern-KG", "mode_a": "baseline_strict", "mode_b": "joern"},
]

MODES = ["baseline", "kg", "rag"]  # rag is still loaded so reviews are kept on disk for any later rerun
MODES_STRICT = ["baseline_strict", "joern"]


# ─── Cleanup helpers ──────────────────────────────────────────────────────


def strip_html_comments(text: str) -> str:
    """Remove GitHub PR-template <!-- ... --> boilerplate from PR bodies.

    Several PRs (e.g. PR2 grafana) carry the full 'Thank you for sending a
    pull request! ...CONTRIBUTING.md...' template comment, which is pure
    reading burden for raters. Strips all HTML comments and collapses the
    blank lines left behind."""
    cleaned = re.sub(r"<!--.*?-->", "", text or "", flags=re.DOTALL)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def strip_code_fence(text: str) -> str:
    """Remove a leading and trailing ``` line if present."""
    s = text.strip("\n")
    lines = s.split("\n")
    if lines and lines[0].strip() == "```":
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def strip_kg_traceability_leak(text: str) -> str:
    """The KG mode emits an extra '- Code Owners: ...' bullet in
    Traceability that v1 reviews of baseline/RAG do not. Strip it so
    the surface form is identical across modes (so a rater cannot
    de-blind by looking for that line)."""

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
    """If the Traceability section has only 'Not specified' (or is
    empty), remove the section entirely.

    Why: the deep audit confirms every PR × mode in the v2 selection
    has 'Not specified' Traceability. The section adds ~35-50 chars of
    visual noise, contributes uniformly to review length, and provides
    zero rater-decision value. Removing it is symmetric across modes
    (no de-blinding) and makes reviews tighter."""
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
            stripped_section = re.sub(
                r"\*+", "", stripped_section
            ).strip()
            # Drop if section is just "Not specified" or any
            # `<label>: Not specified` form (e.g. "Teams: Not specified",
            # "Owners: Not specified", "Code Owners: Not specified").
            # These all carry zero information and just add visual noise
            # uniformly to KG reviews.
            empty_section = (
                not stripped_section
                or stripped_section in {"not specified", "not specified.", "n/a", "none"}
                or re.match(r"^[a-z ]{2,30}\s*:\s*not specified\.?$", stripped_section) is not None
                or re.match(r"^[a-z ]{2,30}\s+not specified\.?$",  stripped_section) is not None
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
    """Neutralise the Joern mode-leak in the Evidence section.

    The Joern arm renders Evidence as labelled, nested bullet groups
    (e.g. '**Diff References:**', '**Structural Context:**',
    '**Callers:**', '**Test Files:**'), some two levels deep. The
    baseline arm renders Evidence as a flat list of top-level bullets
    with no bold banners. That difference is a pure-formatting tell:
    a rater can de-blind after a couple of trials by spotting the
    banner headers, before reading a single word of content.

    This rewrites the Evidence section of *both* arms to the same flat
    template:
      * drop bullets whose only content is a bold label (the banners);
      * strip a leading bold label from any bullet that also carries
        content ('**Callers Affected:** foo' -> 'foo');
      * promote every surviving (leaf) bullet to a top-level '- ' bullet.

    NOTHING is removed except the bold label words and indentation.
    Every file path, line number, caller, and test reference Joern
    produced is preserved verbatim — so the treatment (cross-file
    structural context) is fully intact; only its surface form is
    normalised. Baseline Evidence is already flat, so this is a no-op
    for it beyond '*'->'-' normalisation, which keeps the transform
    symmetric across arms.

    Note: the residual, content-level tell (Joern cites files that are
    not in the diff; baseline does not) is intrinsic to the treatment
    and is intentionally NOT removed here — see the study limitations.
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
                    # header-only banner bullet -> drop entirely
                    continue
                out.append(f"- {content}")
                continue
        out.append(line)
    cleaned = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def neutralise_bold_leadins(text: str) -> str:
    """Strip leading bold sub-labels from list items.

    The KG arm tends to render Problem/Impact/Recommendation items as
    '1. **Backward Compatibility:** text' while the baseline arm writes
    plain '1. text'. Measured across the bl-vs-kg set, KG carried 6-10
    bold sub-labels vs baseline's ~1 in 4 of 6 PRs — a partial formatting
    tell a careful rater could exploit to de-blind.

    This rewrites any 'list-marker **Label:** rest' line to
    'list-marker rest' (keeping the marker and the content, dropping only
    the bold label), matching the baseline's plain style. Symmetric across
    arms. Only leading list-item bold labels ending in ':' are touched;
    mid-sentence bold and bold without a trailing colon are left intact,
    and the standalone '**Scope:**' intro (present in both arms) is not a
    list item so it is preserved identically on both sides."""
    pat = re.compile(r"^(\s*(?:[-*]|\d+\.)\s+)\*\*([^*]+?):\*\*\s*(.*)$")
    out = []
    for line in text.split("\n"):
        m = pat.match(line)
        if m:
            rest = m.group(3).strip()
            if rest:
                out.append(f"{m.group(1)}{rest}")
            # label-only bullet -> drop entirely
            continue
        out.append(line)
    return "\n".join(out)


def normalise_review(raw: str) -> str:
    return neutralise_bold_leadins(
        flatten_evidence_structure(
            drop_empty_traceability_section(
                strip_kg_traceability_leak(strip_code_fence(raw))
            )
        )
    )


def annotate_truncation(diff: str, threshold: int = 50000) -> str:
    """Defensive marker if a PR's diff hits the dataset_v2 50 kB cap.

    The v2 selection (`SELECTION_v2.md`) explicitly excludes PRs with
    diffs above 50 kB, so this should never fire for the current 4-PR
    human-study selection. Kept in case future re-cuts pull in a PR
    that brushes the cap.
    """
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


_BODY_OVERRIDES_CACHE: dict | None = None


def load_pr_body(pr_id: int, ev: dict) -> str:
    """Prefer the override fetched from GitHub (full body, comments
    stripped) over the local evidence-pack body.

    Note: in the v3 stimuli set the v2 evidence packs already contain
    full bodies (recovered as part of the dataset_v2 rebuild), so the
    override file is largely redundant. Kept because (a) the smoke
    tests in human_eval_v2 verified the overrides are clean, and
    (b) override precedence is the same behaviour the v2 study
    advertised, so v2↔v3 differ only in review content, not body
    content."""
    global _BODY_OVERRIDES_CACHE
    if _BODY_OVERRIDES_CACHE is None:
        if os.path.exists(PR_BODY_OVERRIDES_PATH):
            with open(PR_BODY_OVERRIDES_PATH) as f:
                _BODY_OVERRIDES_CACHE = json.load(f)
        else:
            _BODY_OVERRIDES_CACHE = {}
    override = _BODY_OVERRIDES_CACHE.get(str(pr_id))
    if override:
        return strip_html_comments(override)
    return strip_html_comments((ev.get("pr") or {}).get("body") or "")


def load_review(pr_id: int, mode: str) -> str:
    """Loads a generated review.

    For standard modes (baseline/kg/rag): from outputs/luca_prs_v2/.
    For strict modes (baseline_strict/joern): from experiments/human_study_reviews/
    and experiments/2026-05-15_joern_kg_main/exp_gpt4o_joern/ respectively.
    """
    if mode == "baseline_strict":
        path = os.path.join(STRICT_REVIEW_DIR, f"pr{pr_id}_baseline_strict.md")
    elif mode == "joern":
        path = os.path.join(JOERN_REVIEW_DIR, f"pr{pr_id}_review.md")
    else:
        path = os.path.join(REVIEW_DIR, f"pr{pr_id}_{mode}.md")

    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    raise FileNotFoundError(
        f"No review found for PR {pr_id} mode {mode} at {path}."
    )


def load_repo_url(pr_id: int, ev: dict) -> str:
    """Try evidence pack first, fall back to v1 study_data.json which
    has correct repo info for the overlap PRs."""
    pr = ev.get("pr") or {}
    if pr.get("url"):
        return pr["url"]
    v1 = os.path.join(REPO_ROOT, "human_eval", "study_data.json")
    if os.path.exists(v1):
        with open(v1) as f:
            sd = json.load(f)
        for p in sd.get("prs", []):
            if p["pr_id"] == pr_id and p.get("url"):
                return p["url"]
    return ""


PR_NUMBER_TO_REPO = {
    1: "godotengine/godot",
    11: "django/django",
    12: "godotengine/godot",
    13: "godotengine/godot",
    14: "grafana/grafana",
    15: "grafana/grafana",
    16: "grafana/grafana",
    18: "jenkinsci/jenkins",
    20: "apache/kafka",
    21: "apache/kafka",
    23: "scikit-learn/scikit-learn",
    24: "scikit-learn/scikit-learn",
    25: "django/django",
    26: "django/django",
}


def load_repo_name(pr_id: int, ev: dict) -> str:
    pr = ev.get("pr") or {}
    if pr.get("repo_owner") and pr.get("repo_name"):
        return f"{pr['repo_owner']}/{pr['repo_name']}"
    url = pr.get("url") or ""
    m = re.search(r"github\.com/([^/]+/[^/]+)/pull/", url)
    if m:
        return m.group(1)
    md = ev.get("metadata") or {}
    rp = md.get("repo_path") or ""
    m = re.search(r"luca_repos/([^/]+)$", rp)
    if m:
        slug = m.group(1)
        return slug.replace("_", "/", 1) if "_" in slug else slug
    v1 = os.path.join(REPO_ROOT, "human_eval", "study_data.json")
    if os.path.exists(v1):
        with open(v1) as f:
            sd = json.load(f)
        for p in sd.get("prs", []):
            if p["pr_id"] == pr_id and p.get("repo"):
                return p["repo"]
    if pr_id in PR_NUMBER_TO_REPO:
        return PR_NUMBER_TO_REPO[pr_id]
    return "?"


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
        "url": load_repo_url(pr_id, ev),
        "body": load_pr_body(pr_id, ev),
        "diff": diff,
        "reviews": reviews,
    }


def build(pr_ids: list[int], out_path: str, strict: bool = False) -> None:
    modes = MODES_STRICT if strict else MODES
    comparisons = COMPARISONS_STRICT if strict else COMPARISONS
    version = "strict-bl-vs-joern-v1" if strict else "6-criterion-v3-pairwise-v2"
    out = {
        "version": version,
        "criteria": CRITERIA,
        "modes": modes,
        "comparisons": comparisons,
        "prs": [build_pr_block(pid, modes) for pid in pr_ids],
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {out_path}")
    print(f"  {len(out['prs'])} PRs × {len(out['comparisons'])} comparisons "
          f"= {len(out['prs']) * len(out['comparisons'])} trials per rater")


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument(
        "--final",
        action="store_true",
        help="(default) PRs 1,14,22,24,30,42 — original v3 selection.",
    )
    g.add_argument(
        "--strict",
        action="store_true",
        help="Decision 18: PRs 15,22,31,38,40,47 — prompt-symmetric "
             "baseline_strict vs joern comparison for human study.",
    )
    g.add_argument(
        "--option",
        choices=["A", "B", "C"],
        help="A: PRs 17,12,1,3,18,19 (early option, dropped). "
        "B: PRs 17,12,1,3,14,19 (Jelly-included, dropped). "
        "C: PRs 12,1,3,14 (== --final, language-coverage-filtered).",
    )
    g.add_argument(
        "--pr-ids",
        nargs="+",
        type=int,
        help="Custom list of PR IDs (overrides --final/--option).",
    )
    ap.add_argument("--out", default=OUT_PATH)
    a = ap.parse_args()

    if a.option == "A":
        pr_ids = OPTION_A
        strict = False
    elif a.option == "B":
        pr_ids = OPTION_B
        strict = False
    elif a.option == "C":
        pr_ids = OPTION_C_LANG_FILTERED
        strict = False
    elif a.pr_ids:
        pr_ids = a.pr_ids
        strict = False
    elif a.strict:
        pr_ids = FINAL_STRICT
        strict = True
    else:
        pr_ids = FINAL
        strict = False

    build(pr_ids, a.out, strict=strict)


if __name__ == "__main__":
    main()
