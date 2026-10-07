#!/usr/bin/env python3
"""
RQ2.1 Ablation Study: KG Feature Importance.

End-to-end pipeline:
  1. Create ablated evidence packs (remove tests / deps / both)
  2. Regenerate KG reviews from ablated evidence
  3. Evaluate each review with the 25-criterion LLM-as-judge
  4. Load existing full_kg scores as baseline
  5. Compute feature importance and generate report
"""

import json
import os
import re
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from prnote.ablation import (
    ABLATION_CONFIGS,
    create_ablated_evidence,
    get_config,
    get_relevant_pr_ids,
)
from prnote.llm import generate_completion
from prnote.note import (
    SYSTEM_PROMPT_KG,
    format_kg_context,
    get_diff_from_evidence,
)
from scripts.evaluate_reviews import (
    EVALUATION_CRITERIA,
    evaluate_review_with_llm,
    CriterionScore,
)

EVIDENCE_DIR = Path("data/luca_prs_fixed")
ABLATION_EVIDENCE_DIR = Path("data/ablation")
ABLATION_REVIEWS_DIR = Path("outputs/ablation")
RESULTS_DIR = Path("results")

EXISTING_EVAL_PATH = RESULTS_DIR / "checklist_evaluation_llm.json"
ABLATION_RAW_PATH = RESULTS_DIR / "ablation_raw.json"
ABLATION_REPORT_PATH = RESULTS_DIR / "ablation_report.md"

EVAL_MODEL = "openai:gpt-4o-mini"


# ── Step 1: Create ablated evidence ──────────────────────────────────────────

def step_create_evidence() -> Dict[str, List[Dict]]:
    """Create ablated evidence packs for all non-baseline configs."""
    print("\n" + "=" * 60)
    print("STEP 1: Creating ablated evidence packs")
    print("=" * 60)

    manifest: Dict[str, List[Dict]] = {}

    for config in ABLATION_CONFIGS:
        if config.name == "full_kg":
            continue

        pr_ids = get_relevant_pr_ids(config.name)
        manifest[config.name] = []

        for pr_id in pr_ids:
            src = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
            if not src.exists():
                print(f"  SKIP PR{pr_id}: evidence not found")
                continue

            dst = ABLATION_EVIDENCE_DIR / f"pr{pr_id}_{config.name}.json"
            create_ablated_evidence(str(src), config, str(dst))
            manifest[config.name].append({"pr_id": pr_id, "path": str(dst)})

        print(f"  {config.name}: {len(manifest[config.name])} packs")

    return manifest


# ── Step 2: Generate reviews ─────────────────────────────────────────────────

def generate_kg_review(evidence_path: str) -> str:
    """Generate a KG-mode review from an evidence pack."""
    with open(evidence_path, "r") as f:
        evidence = json.load(f)

    diff = get_diff_from_evidence(evidence)
    title = evidence.get("pr", {}).get("title", "Unknown PR")
    context = format_kg_context(evidence)

    user_prompt = (
        f"## Pull Request: {title}\n\n"
        f"## Diff\n```\n{diff}\n```\n"
        f"{context}\n\n"
        "Please generate an evidence-anchored review note following the specified format."
    )

    return generate_completion(
        prompt=user_prompt,
        system=SYSTEM_PROMPT_KG,
        model=None,
        temperature=0.3,
    )


def step_generate_reviews(manifest: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """Generate KG reviews for all ablated evidence packs."""
    print("\n" + "=" * 60)
    print("STEP 2: Generating ablated KG reviews")
    print("=" * 60)

    ABLATION_REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    total = sum(len(v) for v in manifest.values())
    done = 0

    for config_name, entries in manifest.items():
        for entry in entries:
            pr_id = entry["pr_id"]
            evidence_path = entry["path"]
            review_path = ABLATION_REVIEWS_DIR / f"pr{pr_id}_{config_name}.md"

            done += 1
            tag = f"[{done}/{total}]"

            if review_path.exists():
                print(f"  {tag} PR{pr_id} {config_name}: cached")
                entry["review_path"] = str(review_path)
                continue

            print(f"  {tag} PR{pr_id} {config_name}: generating...", end=" ", flush=True)
            try:
                review = generate_kg_review(evidence_path)
                review_path.write_text(review)
                entry["review_path"] = str(review_path)
                print(f"OK ({len(review)} chars)")
            except Exception as exc:
                print(f"FAIL: {exc}")
                entry["review_path"] = None

    return manifest


# ── Step 3: Evaluate reviews ─────────────────────────────────────────────────

def step_evaluate_reviews(manifest: Dict[str, List[Dict]]) -> List[Dict]:
    """Evaluate each ablated review with the 25-criterion LLM judge."""
    print("\n" + "=" * 60)
    print("STEP 3: Evaluating ablated reviews (25-criterion rubric)")
    print("=" * 60)

    all_evals: List[Dict] = []
    total = sum(1 for entries in manifest.values() for e in entries if e.get("review_path"))
    done = 0

    for config_name, entries in manifest.items():
        for entry in entries:
            review_path = entry.get("review_path")
            if not review_path or not Path(review_path).exists():
                continue

            pr_id = entry["pr_id"]
            done += 1
            tag = f"[{done}/{total}]"
            print(f"  {tag} PR{pr_id} {config_name}: evaluating...", end=" ", flush=True)

            review_text = Path(review_path).read_text()
            pr_context = _load_pr_context(pr_id)

            try:
                scores = evaluate_review_with_llm(review_text, pr_context, model=EVAL_MODEL)
            except Exception as exc:
                print(f"FAIL: {exc}")
                scores = [CriterionScore(c.id, 0, f"eval error: {exc}") for c in EVALUATION_CRITERIA]

            total_score = sum(s.score for s in scores)
            kg_ids = {c.id for c in EVALUATION_CRITERIA if c.kg_relevant}
            kg_score = sum(s.score for s in scores if s.criterion_id in kg_ids)

            result = {
                "pr_id": pr_id,
                "config": config_name,
                "total_score": total_score,
                "max_score": len(EVALUATION_CRITERIA),
                "percentage": round(total_score / len(EVALUATION_CRITERIA) * 100, 1),
                "kg_relevant_score": kg_score,
                "kg_relevant_max": len(kg_ids),
                "criteria_scores": [asdict(s) for s in scores],
                "timestamp": datetime.now().isoformat(),
            }
            all_evals.append(result)
            print(f"{total_score}/25 ({result['percentage']}%)")

    return all_evals


def _load_pr_context(pr_id: int) -> Dict[str, Any]:
    """Load PR title/body for the evaluator prompt."""
    evidence_path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    if evidence_path.exists():
        with open(evidence_path) as f:
            ev = json.load(f)
        return {
            "title": ev.get("pr", {}).get("title", ""),
            "body": ev.get("pr", {}).get("body", "")[:500],
            "pr_id": pr_id,
        }
    pr_json = Path(f"luca_thesis/data/baseline_pr_stimuli/{pr_id}/original_pr.json")
    if pr_json.exists():
        with open(pr_json) as f:
            pr = json.load(f)
        return {"title": pr.get("title", ""), "body": pr.get("body", "")[:500], "pr_id": pr_id}
    return {"title": "", "body": "", "pr_id": pr_id}


# ── Step 4: Load baseline & compute importance ──────────────────────────────

def load_full_kg_baseline() -> List[Dict]:
    """Extract full_kg evaluation entries from the existing evaluation JSON."""
    with open(EXISTING_EVAL_PATH) as f:
        data = json.load(f)

    baseline = []
    for ev in data["evaluations"]:
        if ev["mode"] != "kg":
            continue
        baseline.append({
            "pr_id": ev["pr_id"],
            "config": "full_kg",
            "total_score": ev["total_score"],
            "max_score": ev["max_score"],
            "percentage": ev["percentage"],
            "kg_relevant_score": ev["kg_relevant_score"],
            "kg_relevant_max": ev["kg_relevant_max"],
            "criteria_scores": ev["criteria_scores"],
        })
    return baseline


def compute_importance(baseline: List[Dict], ablated: List[Dict]) -> Dict[str, Any]:
    """Compute per-config and per-criterion feature importance."""
    bl_by_pr = {e["pr_id"]: e for e in baseline}
    abl_by_config: Dict[str, List[Dict]] = {}
    for e in ablated:
        abl_by_config.setdefault(e["config"], []).append(e)

    config_importance = []
    criterion_deltas: Dict[str, Dict[str, float]] = {}

    for config_name, entries in sorted(abl_by_config.items()):
        common_pr_ids = [e["pr_id"] for e in entries if e["pr_id"] in bl_by_pr]
        if not common_pr_ids:
            continue

        bl_scores = [bl_by_pr[pid]["percentage"] for pid in common_pr_ids]
        ab_scores = [e["percentage"] for e in entries if e["pr_id"] in set(common_pr_ids)]

        bl_avg = sum(bl_scores) / len(bl_scores)
        ab_avg = sum(ab_scores) / len(ab_scores)
        drop = bl_avg - ab_avg
        pct_drop = (drop / bl_avg * 100) if bl_avg > 0 else 0

        config_importance.append({
            "config": config_name,
            "n_prs": len(common_pr_ids),
            "baseline_avg": round(bl_avg, 2),
            "ablated_avg": round(ab_avg, 2),
            "score_drop_pp": round(drop, 2),
            "relative_drop_pct": round(pct_drop, 1),
        })

        # Per-criterion deltas
        crit_map: Dict[str, List[float]] = {}
        for pr_id in common_pr_ids:
            bl_crit = {s["criterion_id"]: s["score"] for s in bl_by_pr[pr_id]["criteria_scores"]}
            ab_entry = next(e for e in entries if e["pr_id"] == pr_id)
            ab_crit = {s["criterion_id"]: s["score"] for s in ab_entry["criteria_scores"]}
            for cid in bl_crit:
                crit_map.setdefault(cid, []).append(bl_crit.get(cid, 0) - ab_crit.get(cid, 0))

        criterion_deltas[config_name] = {
            cid: round(sum(deltas) / len(deltas), 3) for cid, deltas in crit_map.items()
        }

    config_importance.sort(key=lambda x: x["relative_drop_pct"], reverse=True)

    return {
        "config_importance": config_importance,
        "criterion_deltas": criterion_deltas,
    }


# ── Step 5: Report ──────────────────────────────────────────────────────────

def generate_report(importance: Dict[str, Any], baseline: List[Dict], ablated: List[Dict]) -> str:
    """Produce ablation_report.md."""
    ci = importance["config_importance"]
    cd = importance["criterion_deltas"]

    lines = [
        "# Ablation Study Results — RQ2.1: KG Feature Importance",
        "",
        f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## 1. Experiment Design",
        "",
        "We systematically remove KG features from the evidence pack and regenerate",
        "KG-mode reviews. Each ablated review is evaluated with the same 25-criterion",
        "LLM-as-judge rubric (GPT-4o-mini) used for the main evaluation.",
        "",
        "| Config | Description | PRs |",
        "|--------|-------------|-----|",
    ]
    config_desc = {
        "kg_no_tests": "Remove `nearest_tests`",
        "kg_no_deps": "Remove `dependent_files`",
        "kg_minimal": "Remove both tests + deps",
    }
    for row in ci:
        lines.append(f"| `{row['config']}` | {config_desc.get(row['config'], '')} | {row['n_prs']} |")

    lines += [
        "",
        "## 2. Feature Importance Ranking",
        "",
        "| Rank | Config | Baseline Avg | Ablated Avg | Drop (pp) | Relative Drop |",
        "|------|--------|-------------|-------------|-----------|---------------|",
    ]
    for i, row in enumerate(ci, 1):
        lines.append(
            f"| {i} | `{row['config']}` | {row['baseline_avg']}% "
            f"| {row['ablated_avg']}% | {row['score_drop_pp']:+.2f} | {row['relative_drop_pct']:.1f}% |"
        )

    lines += [
        "",
        "## 3. Per-Criterion Impact",
        "",
        "Average score delta (baseline - ablated) per criterion. Positive = feature helped.",
        "",
    ]
    all_cids = [c.id for c in EVALUATION_CRITERIA]
    cid_cat = {c.id: c.category for c in EVALUATION_CRITERIA}
    cid_kg = {c.id: c.kg_relevant for c in EVALUATION_CRITERIA}

    header = "| Criterion | Category | KG-rel | " + " | ".join(cd.keys()) + " |"
    sep = "|-----------|----------|--------|" + "|".join(["--------"] * len(cd)) + "|"
    lines.append(header)
    lines.append(sep)
    for cid in all_cids:
        kg_flag = "yes" if cid_kg[cid] else ""
        vals = " | ".join(
            f"{cd[cfg].get(cid, 0):+.3f}" if cd[cfg].get(cid, 0) != 0 else "0.000"
            for cfg in cd
        )
        lines.append(f"| {cid} | {cid_cat[cid]} | {kg_flag} | {vals} |")

    # Top affected criteria
    lines += ["", "## 4. Most Affected Criteria", ""]
    for cfg, deltas in cd.items():
        sorted_deltas = sorted(deltas.items(), key=lambda x: x[1], reverse=True)
        top = [(cid, d) for cid, d in sorted_deltas if d > 0][:5]
        if top:
            lines.append(f"**`{cfg}`** — criteria most harmed by removal:")
            for cid, d in top:
                lines.append(f"  - {cid} ({cid_cat[cid]}): delta = {d:+.3f}")
            lines.append("")

    # Key findings
    lines += ["## 5. Key Findings", ""]
    if ci:
        most = ci[0]
        least = ci[-1]
        lines.append(f"1. **Most important KG feature**: `{most['config']}` — removing it causes "
                      f"a **{most['relative_drop_pct']:.1f}%** relative drop in review score.")
        if len(ci) > 1:
            lines.append(f"2. **Least important KG feature** (of those tested): `{least['config']}` "
                          f"— **{least['relative_drop_pct']:.1f}%** relative drop.")

        minimal = next((r for r in ci if r["config"] == "kg_minimal"), None)
        if minimal:
            lines.append(f"3. **Combined removal** (`kg_minimal`): **{minimal['relative_drop_pct']:.1f}%** "
                          f"relative drop, showing features are {'complementary' if minimal['relative_drop_pct'] > most['relative_drop_pct'] else 'partially redundant'}.")

    lines += [
        "",
        "---",
        "*Generated by scripts/run_ablation_study.py*",
    ]
    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    start = time.time()
    print("=" * 60)
    print("  RQ2.1 KG ABLATION STUDY")
    print("=" * 60)

    # Step 1
    manifest = step_create_evidence()

    # Step 2
    manifest = step_generate_reviews(manifest)

    # Step 3
    ablated_evals = step_evaluate_reviews(manifest)

    # Step 4
    print("\n" + "=" * 60)
    print("STEP 4: Computing feature importance")
    print("=" * 60)

    baseline_evals = load_full_kg_baseline()
    print(f"  Loaded {len(baseline_evals)} full_kg baseline evaluations")

    importance = compute_importance(baseline_evals, ablated_evals)

    # Save raw results
    RESULTS_DIR.mkdir(exist_ok=True)
    raw = {
        "metadata": {
            "study": "RQ2.1 KG ablation",
            "eval_model": EVAL_MODEL,
            "timestamp": datetime.now().isoformat(),
            "criteria_count": len(EVALUATION_CRITERIA),
        },
        "baseline": baseline_evals,
        "ablated": ablated_evals,
        "importance": importance,
    }
    with open(ABLATION_RAW_PATH, "w") as f:
        json.dump(raw, f, indent=2)
    print(f"  Raw results saved to {ABLATION_RAW_PATH}")

    # Step 5
    print("\n" + "=" * 60)
    print("STEP 5: Generating report")
    print("=" * 60)

    report = generate_report(importance, baseline_evals, ablated_evals)
    with open(ABLATION_REPORT_PATH, "w") as f:
        f.write(report)
    print(f"  Report saved to {ABLATION_REPORT_PATH}")

    elapsed = time.time() - start
    print(f"\nDone in {elapsed / 60:.1f} minutes.")

    # Quick summary
    print("\n--- QUICK SUMMARY ---")
    for row in importance["config_importance"]:
        print(f"  {row['config']}: {row['baseline_avg']}% -> {row['ablated_avg']}% "
              f"(drop {row['score_drop_pp']:+.2f} pp, {row['relative_drop_pct']:.1f}% relative)")


if __name__ == "__main__":
    main()
