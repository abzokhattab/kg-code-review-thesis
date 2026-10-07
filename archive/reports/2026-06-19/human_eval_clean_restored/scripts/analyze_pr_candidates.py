#!/usr/bin/env python3
"""
analyze_pr_candidates.py

Scores every PR in the LUCA 25-PR catalogue against the criteria proposed
for the v2 human-study selection.

The criteria are (in priority order, applied as filters):

  1. Diff <= 5 kB            (safe under the 15 kB truncation limit)
  2. Mainstream stack         (Python / JS-TS / mainstream Java app code)
  3. Single-purpose change    (one file or one focused change)
  4. Rubric divergence >= 2   on the 5 human-overlap criteria
                              (F3* ~ F3, F2* ~ F2, T3, R1, Q5)
                              (C6 is human-only and excluded here)
  5. Repo diversity preserved
  6. Tier mix (FULL_KG vs MARGINAL) preserved

The script does NOT pick the final 6 PRs — it produces a ranked table that
a human can review and override. Selection-on-direction (i.e. picking PRs
where a particular mode wins) is *deliberately* not used; only magnitude
of divergence is.

Outputs:
  human_eval_v2/analysis/pr_candidates.json
  human_eval_v2/analysis/pr_candidates.md  (human-readable table)

Run:
  python3 human_eval_v2/scripts/analyze_pr_candidates.py
"""

from __future__ import annotations

import glob
import json
import os
import re
from collections import defaultdict
from typing import Any

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EVIDENCE_DIR = os.path.join(REPO_ROOT, "data", "luca_prs_fixed")
LLM_EVAL_PATH = os.path.join(
    REPO_ROOT, "results", "checklist_evaluation_llm_multi.json"
)
OUT_JSON = os.path.join(
    REPO_ROOT, "human_eval_v2", "analysis", "pr_candidates.json"
)
OUT_MD = os.path.join(
    REPO_ROOT, "human_eval_v2", "analysis", "pr_candidates.md"
)

HUMAN_OVERLAP_CRITERIA = ["F2", "F3", "T3", "R1", "Q5"]

MAINSTREAM_REPOS = {
    "django/django": "Python",
    "scikit-learn/scikit-learn": "Python",
    "grafana/grafana": "TS/Go",
    "godotengine/godot": "C++",
    "microsoft/TypeScript": "TS",
    "apache/kafka": "Java",
    "jenkinsci/jenkins": "Java/Jelly",
}

NICHE_FRAMEWORKS = {
    "jenkinsci/jenkins": "Jelly templates / niche",
    "apache/kafka": "JVM internals / Gradle / Kafka-specific",
}


def classify_change_type(title: str, diff: str) -> str:
    """Heuristic classifier; flagged for human review."""
    t = (title or "").lower()
    if any(k in t for k in ["fix", "bug", "regression", "broken"]):
        if "fix" in t and ("docstring" in t or "doc " in t or "docs" in t):
            return "docs"
        return "bug-fix"
    if any(k in t for k in ["add", "introduce", "feature", "support for"]):
        return "feature"
    if any(k in t for k in ["docs", "readme", "docstring", "documentation"]):
        return "docs"
    if any(k in t for k in ["revert", "reverted"]):
        return "revert"
    if any(
        k in t
        for k in [
            "refactor",
            "cleanup",
            "clean up",
            "remove",
            "move ",
            "rename",
            "bump",
            "use ",
            "convert ",
            "chore",
            "mnt",
            "cln",
        ]
    ):
        return "refactor"
    return "other"


def load_evidence_packs() -> list[dict[str, Any]]:
    rows = []
    for fn in sorted(glob.glob(os.path.join(EVIDENCE_DIR, "pr*_evidence.json"))):
        with open(fn) as f:
            d = json.load(f)
        m = re.match(r"pr(\d+)_evidence\.json", os.path.basename(fn))
        if not m:
            continue
        pr_id = int(m.group(1))
        pr = d.get("pr") or {}
        full_diff = d.get("full_diff") or ""
        rows.append(
            {
                "pr_id": pr_id,
                "repo": (
                    f"{pr.get('repo_owner', '?')}/{pr.get('repo_name', '?')}"
                    if pr.get("repo_owner") and pr.get("repo_name")
                    else None
                ),
                "pr_number": pr.get("number"),
                "state": pr.get("state"),
                "title": pr.get("title", "") or "",
                "url": pr.get("url", "") or "",
                "diff_chars": len(full_diff),
                "changed_files": len(d.get("changed_files") or []),
                "tests_found": len(d.get("nearest_tests") or []),
                "deps_found": len(d.get("dependent_files") or []),
            }
        )
    return rows


def fill_missing_repo_from_existing_study(rows: list[dict]) -> None:
    """The current study_data.json has correct repo names for some PRs that
    the evidence pack lost. Backfill from there."""
    sd_path = os.path.join(REPO_ROOT, "human_eval", "study_data.json")
    if not os.path.exists(sd_path):
        return
    try:
        with open(sd_path) as f:
            sd = json.load(f)
        by_id = {p["pr_id"]: p for p in sd.get("prs", [])}
        for r in rows:
            if not r.get("repo") and r["pr_id"] in by_id:
                p = by_id[r["pr_id"]]
                r["repo"] = p["repo"]
                if not r.get("pr_number"):
                    r["pr_number"] = p["pr_number"]
                if not r.get("url"):
                    r["url"] = p["url"]
    except Exception:
        return


def load_llm_scores() -> dict[tuple[int, str], dict[str, int]]:
    """Returns {(pr_id, mode): {criterion_id: 0/1}}."""
    with open(LLM_EVAL_PATH) as f:
        d = json.load(f)
    out: dict[tuple[int, str], dict[str, int]] = {}
    for ev in d["evaluations"]:
        key = (ev["pr_id"], ev["mode"])
        crit = {c["criterion_id"]: int(c["score"]) for c in ev["criteria_scores"]}
        out[key] = crit
    return out


def rubric_divergence(
    pr_id: int, scores: dict[tuple[int, str], dict[str, int]]
) -> dict[str, Any]:
    """Compute Σ h6 divergence on the 5 human-overlap criteria
    across both bl_vs_kg and kg_vs_rag comparisons (max 10)."""
    bl = scores.get((pr_id, "baseline"), {})
    kg = scores.get((pr_id, "kg"), {})
    rag = scores.get((pr_id, "rag"), {})
    bl_vs_kg = sum(1 for c in HUMAN_OVERLAP_CRITERIA if bl.get(c) != kg.get(c))
    kg_vs_rag = sum(1 for c in HUMAN_OVERLAP_CRITERIA if kg.get(c) != rag.get(c))
    return {
        "bl_vs_kg_divergence": bl_vs_kg,
        "kg_vs_rag_divergence": kg_vs_rag,
        "total_divergence": bl_vs_kg + kg_vs_rag,
    }


def kg_tier(pr_id: int, ev_pack: dict) -> str:
    """A coarse proxy for FULL_KG vs MARGINAL.
    FULL_KG: tests AND dependents both > 0.
    MARGINAL: at most one of {tests, dependents} populated."""
    t = ev_pack["tests_found"]
    d = ev_pack["deps_found"]
    if t > 0 and d > 0:
        return "FULL_KG"
    return "MARGINAL"


def passes_filters(row: dict) -> dict[str, bool]:
    """Apply each criterion as a separate boolean so we can show
    which PRs pass which subset."""
    f = {}
    f["diff_under_5kb"] = row["diff_chars"] <= 5000
    f["diff_under_8kb"] = row["diff_chars"] <= 8000
    f["not_truncated"] = row["diff_chars"] < 15000
    f["divergence_ge_2"] = (row.get("total_divergence") or 0) >= 2
    f["state_merged"] = (row.get("state") or "").upper() == "MERGED"
    f["not_revert"] = row["change_type"] != "revert"
    f["not_docs_only"] = row["change_type"] != "docs"
    f["mainstream_stack"] = row["repo"] not in NICHE_FRAMEWORKS
    f["single_purpose"] = row["changed_files"] <= 4
    return f


def main() -> None:
    rows = load_evidence_packs()
    fill_missing_repo_from_existing_study(rows)
    scores = load_llm_scores()

    for r in rows:
        r["change_type"] = classify_change_type(r["title"], "")
        r.update(rubric_divergence(r["pr_id"], scores))
        r["kg_tier"] = kg_tier(r["pr_id"], r)
        r["lang"] = MAINSTREAM_REPOS.get(r["repo"], "?")
        r["filters"] = passes_filters(r)
        r["filter_pass_count"] = sum(1 for v in r["filters"].values() if v)

    rows.sort(
        key=lambda r: (
            -r["filter_pass_count"],
            -r.get("total_divergence", 0),
            r["diff_chars"],
        )
    )

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(
            {
                "criteria": {
                    "human_overlap_criteria": HUMAN_OVERLAP_CRITERIA,
                    "filters": [
                        "diff_under_5kb (preferred)",
                        "diff_under_8kb (acceptable)",
                        "not_truncated (mandatory)",
                        "divergence_ge_2 (signal floor)",
                        "state_merged (real PR)",
                        "not_revert",
                        "not_docs_only",
                        "mainstream_stack (excludes Jelly/JVM-internal)",
                        "single_purpose (<=4 changed files)",
                    ],
                },
                "candidates": rows,
            },
            f,
            indent=2,
        )
    print(f"Wrote {OUT_JSON}")

    md_lines = [
        "# v2 PR-selection candidate analysis",
        "",
        f"Generated by `human_eval_v2/scripts/analyze_pr_candidates.py` "
        f"over the {len(rows)} LUCA PRs.",
        "",
        "Filters used (none of which select on which mode wins):",
        "",
        "1. **diff_under_5kb** — preferred (no truncation risk, fast read)",
        "2. **diff_under_8kb** — acceptable upper bound",
        "3. **not_truncated** — mandatory; the 15 kB cap silently truncates "
        "diffs and contaminates the κ computation",
        "4. **divergence_ge_2** — at least 2 of 5 human-overlap rubric criteria "
        "differ between modes (signal floor, magnitude only)",
        "5. **state_merged** — real, accepted PRs (not synthetic)",
        "6. **not_revert** — exclude PRs that were reverted",
        "7. **not_docs_only** — review-meaningful changes",
        "8. **mainstream_stack** — exclude Jelly/JVM-internal niches",
        "9. **single_purpose** — ≤ 4 changed files (a focused change a rater "
        "can hold in their head)",
        "",
        f"Human-overlap criteria used for divergence: "
        f"`{', '.join(HUMAN_OVERLAP_CRITERIA)}` "
        "(C6 is human-only; F3*/F2* mapped to F3/F2 in the LLM rubric).",
        "",
        "## Ranked candidates",
        "",
        "Sorted by (filters passed, divergence, diff size).",
        "",
        "| Rank | PR | Repo | # | Type | Diff | Files | Tier | Σ divergence "
        "| Filters passed | Title |",
        "|----:|---:|------|---|------|-----:|------:|------|---:|------|------|",
    ]
    for i, r in enumerate(rows, 1):
        ttl = (r["title"][:55] + "…") if len(r["title"]) > 55 else r["title"]
        md_lines.append(
            f"| {i} | {r['pr_id']} | {r['repo'] or '?'} | "
            f"{r['pr_number'] or '?'} | {r['change_type']} | "
            f"{r['diff_chars']} | {r['changed_files']} | {r['kg_tier']} | "
            f"{r['total_divergence']} | "
            f"{r['filter_pass_count']}/9 | {ttl} |"
        )

    md_lines += [
        "",
        "## What to look for",
        "",
        "- Top of the table = PRs that pass the most filters.",
        "- A PR with `9/9 filters passed` is a clean candidate; "
        "`<= 6/9` should usually be excluded.",
        "- For tier balance, target 3 FULL_KG + 3 MARGINAL in the final 6.",
        "- For change-type balance, target ≥ 2 features or bug-fixes "
        "(not all refactor).",
        "- For repo diversity, target ≥ 3 distinct repos.",
        "",
        "## Comparison to current v1 selection (PRs 17, 3, 19, 22, 10, 21)",
        "",
    ]
    cur = {17, 3, 19, 22, 10, 21}
    md_lines.append(
        "| PR | Filters passed | Notes |\n"
        "|---:|---:|------|"
    )
    for r in rows:
        if r["pr_id"] in cur:
            issues = []
            if not r["filters"]["diff_under_8kb"]:
                if r["filters"]["not_truncated"]:
                    issues.append("over 8 kB but readable")
                else:
                    issues.append("**truncated**")
            if not r["filters"]["mainstream_stack"]:
                issues.append("niche stack")
            if not r["filters"]["single_purpose"]:
                issues.append("multi-file")
            if not r["filters"]["divergence_ge_2"]:
                issues.append("low divergence")
            md_lines.append(
                f"| {r['pr_id']} | {r['filter_pass_count']}/9 | "
                f"{'; '.join(issues) or 'OK'} |"
            )

    with open(OUT_MD, "w") as f:
        f.write("\n".join(md_lines) + "\n")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
