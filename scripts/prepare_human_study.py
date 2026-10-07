#!/usr/bin/env python3
"""
Bundle PR context, reviews, and the 5-criterion rubric into study_data.json
for the human evaluation website.

Criteria selection: top 5 by discriminative power (spread) with kappa-
readiness validation. T1 was replaced with Q5 due to a ceiling effect
(96% yes-rate, negative kappa). All 5 criteria have kappa@80% >= 0.47.
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "luca_prs_fixed"
REVIEWS_DIR = BASE_DIR / "outputs" / "luca_prs_fixed"
OUTPUT_DIR = BASE_DIR / "human_eval"
EVAL_JSON = BASE_DIR / "results" / "checklist_evaluation_llm.json"

ALL_PR_IDS = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]

# 6 PRs selected for maximum discrimination between comparison pairs
# (baseline-vs-KG and KG-vs-RAG). Original selection used single-judge LLM
# scores to pick PRs by per-pair "flips" count.
#
# Pre-deployment swap (see results/THREATS_TO_VALIDITY.md §8.2.2):
#   PR26 (Django #18322) was excluded after a weak-stimulus review — it is a
#   revert PR whose descriptive title telegraphs the expected review content,
#   and under the multi-judge data its KG-vs-baseline delta on KG-relevant
#   criteria collapses to zero. It was replaced by PR18 (Jenkins #9002),
#   a real seven-file StringUtils refactor where multi-judge KG scores beat
#   both baseline and RAG on KG-relevant criteria (dKG_B=+1, dKG_R=+2).
#
# Covers 3 repos, 3 languages: Java (kafka, jenkins), TS (grafana), Python (scikit)
# Ordered easy→hard for smooth rater ramp-up:
#   PR18: multi-judge KG-strong, tests-in-diff → clear KG signal for warmup
#   PR10: 4 flips (moderate)
#   PR14: 4 flips (bl_vs_kg only 1 flip)
#   PR22: 6 flips (clear structural differences)
#   PR15: 3 flips (hardest to distinguish)
#   PR21: 6 flips (baseline all-zeros → most obvious contrast, kept last)
SELECTED_PR_IDS = [18, 10, 14, 22, 15, 21]

PR_IDS = SELECTED_PR_IDS

# Fix generic/missing titles and add brief descriptions so raters have context
PR_OVERRIDES = {
    18: {
        "body": "Reduces usage of Apache Commons Lang `StringUtils#capitalize` / "
                "`#uncapitalize` in favour of standard Java Platform equivalents, "
                "part of an effort to eventually remove the outdated Commons Lang 2 "
                "dependency from Jenkins core.",
    },
    22: {
        "body": "Moves AbstractResetIntegrationTest and its subclasses from the "
                "Kafka streams module to the tools module. Updates package names, "
                "build dependencies, and test assertions accordingly.",
    },
    14: {
        "body": "Introduces a `size` property on the Drawer component to set width "
                "as a percentage with a minimum pixel value. Fixes poor scaling on "
                "small screens where a fixed 40-50% width was too narrow.",
    },
    21: {
        "body": "Part of the JDK 8 → 11 migration. Removes usage of the `Java` utility "
                "class for version checks that are no longer needed, and simplifies SSL "
                "config and ByteBuffer unmapping code.",
    },
    15: {
        "body": "Refactors TimeRangePicker to replace `aria-label` selectors with "
                "`data-testid` for E2E tests. Also swaps the close button for an "
                "IconButton component.",
    },
    10: {
        "title": "Bump minimum joblib to 1.0 and remove compat code",
        "body": "Raises the minimum joblib version from 0.11 to 1.0.0, removing "
                "backward-compatibility workarounds for older joblib (CPU affinity "
                "detection, parallel_args helper, Memory caching logic).",
    },
}
MODES = ["baseline", "rag", "kg", "hybrid"]

COMPARISONS = [
    {"id": "bl_vs_kg", "label": "Baseline vs KG", "mode_a": "baseline", "mode_b": "kg"},
    {"id": "kg_vs_rag", "label": "KG vs RAG", "mode_a": "kg", "mode_b": "rag"},
]

MAX_DIFF_CHARS = 8000

# ── 5-criterion rubric ────────────────────────────────────────────────────────
# Selection: 25 original → 14 after item analysis → 5 by spread + kappa-readiness
# T1 replaced with Q5: T1 had 96% yes-rate → kappa prevalence paradox (unusable)
# Q5 has 42% yes-rate, 58% discrimination, kappa@80%=0.59

CRITERIA_5 = [
    {
        "id": "F3*",
        "category": "Functionality",
        "description": "Does the review name concrete components, APIs, or design patterns affected by the changes?",
        "merged_from": ["F3", "M1"],
    },
    {
        "id": "F2*",
        "category": "Functionality",
        "description": "Does the review describe concrete edge cases, boundary conditions, or error-handling gaps?",
        "merged_from": ["F2", "T2"],
    },
    {
        "id": "T3",
        "category": "Tests",
        "description": "Does the review reference concrete test files or suggest which tests should be added/updated?",
    },
    {
        "id": "Q5",
        "category": "Quality",
        "description": "Does the review give a concrete reason for each suggestion (e.g. \u2018X could cause Y\u2019)?",
    },
    {
        "id": "R1",
        "category": "Readability",
        "description": "Does the review comment on code clarity, naming conventions, or function organization?",
    },
]


def load_evidence(pr_id: int) -> dict:
    path = DATA_DIR / f"pr{pr_id}_evidence.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_review(pr_id: int, mode: str) -> str:
    path = REVIEWS_DIR / f"pr{pr_id}_{mode}.md"
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^```\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    text = re.sub(r"\n## Traceability\n.*$", "", text, flags=re.DOTALL)
    text = re.sub(r"^# Review Note\s*[—–-]\s*Evidence[- ]Anchored\s*\n+", "", text)
    text = re.sub(r"^\*\*Scope:\*\*.*?\n+", "", text)
    text = text.replace("## Recommendation (Fix / Tests / Risks)", "## Recommendation")
    # Strip inline bold so all reviews render with the same visual style
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    return text.strip()


def truncate_diff(diff: str) -> str:
    if len(diff) <= MAX_DIFF_CHARS:
        return diff
    cut = diff[:MAX_DIFF_CHARS].rfind("\n")
    if cut < 0:
        cut = MAX_DIFF_CHARS
    return diff[:cut] + "\n\n... (remaining diff omitted) ..."


def extract_pr_meta(evidence: dict) -> dict:
    pr = evidence["pr"]
    # Two evidence formats: old (repo_owner/repo_name) and new (repo)
    if "repo_owner" in pr:
        repo = f"{pr['repo_owner']}/{pr['repo_name']}"
    else:
        repo = pr.get("repo", "")

    return {
        "title": pr.get("title", ""),
        "repo": repo,
        "pr_number": pr.get("number", 0),
        "url": pr.get("url", ""),
        "body": pr.get("body", ""),
    }


def load_llm_scores() -> dict:
    """Load LLM evaluation scores for comparison in results export."""
    with open(EVAL_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    scores = {}
    for ev in data["evaluations"]:
        key = f"pr{ev['pr_id']}_{ev['mode']}"
        criterion_map = {}
        for cs in ev["criteria_scores"]:
            criterion_map[cs["criterion_id"]] = cs["score"]
        scores[key] = criterion_map
    return scores


def compute_5_scores(raw_25: dict) -> dict:
    """Derive 5-criterion scores from 25-criterion raw LLM scores."""
    result = {}
    for crit in CRITERIA_5:
        cid = crit["id"]
        if "merged_from" in crit:
            result[cid] = max(raw_25.get(c, 0) for c in crit["merged_from"])
        else:
            result[cid] = raw_25.get(cid, 0)
    return result


def main():
    prs = []
    llm_raw = load_llm_scores()

    for pr_id in PR_IDS:
        evidence = load_evidence(pr_id)
        meta = extract_pr_meta(evidence)

        reviews = {}
        for mode in MODES:
            reviews[mode] = load_review(pr_id, mode)

        llm_scores = {}
        for mode in MODES:
            key = f"pr{pr_id}_{mode}"
            if key in llm_raw:
                llm_scores[mode] = compute_5_scores(llm_raw[key])

        overrides = PR_OVERRIDES.get(pr_id, {})
        prs.append({
            "pr_id": pr_id,
            "repo": meta["repo"],
            "pr_number": meta["pr_number"],
            "title": overrides.get("title", meta["title"]),
            "url": meta["url"],
            "body": overrides.get("body", meta["body"] or ""),
            "diff": truncate_diff(evidence.get("full_diff", "")),
            "reviews": reviews,
            "llm_scores": llm_scores,
        })

    used_modes = {c["mode_a"] for c in COMPARISONS} | {c["mode_b"] for c in COMPARISONS}

    prs_public = []
    for pr in prs:
        pr_copy = {k: v for k, v in pr.items() if k not in ("llm_scores",)}
        pr_copy["reviews"] = {m: r for m, r in pr["reviews"].items() if m in used_modes}
        prs_public.append(pr_copy)

    study_data_public = {
        "version": "5-criterion-v2-pairwise",
        "criteria": CRITERIA_5,
        "modes": sorted(used_modes),
        "comparisons": COMPARISONS,
        "prs": prs_public,
    }

    study_data_full = {
        "version": "5-criterion-v2-pairwise",
        "criteria": CRITERIA_5,
        "modes": MODES,
        "comparisons": COMPARISONS,
        "prs": prs,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "study_data.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(study_data_public, f, indent=2, ensure_ascii=False)

    analysis_path = BASE_DIR / "results" / "study_data_with_llm_scores.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(study_data_full, f, indent=2, ensure_ascii=False)

    print(f"Wrote {out_path} (public — no LLM scores)")
    print(f"Wrote {analysis_path} (analysis — with LLM scores)")
    print(f"  {len(prs)} PRs × {len(MODES)} modes = {len(prs) * len(MODES)} review tasks")
    print(f"  {len(CRITERIA_5)} criteria per review")
    total = len(prs) * len(MODES) * len(CRITERIA_5)
    print(f"  {total} total judgments per rater")


if __name__ == "__main__":
    main()
