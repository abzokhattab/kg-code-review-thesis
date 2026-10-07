#!/usr/bin/env python3
"""
evaluate_reviews_graded.py — Graded 0-3 scale judge for 5 clean KG-relevant criteria.

Motivation: binary 0/1 scoring creates a ceiling effect — the judge cannot
distinguish "vaguely mentions integration" (deserves 1/3) from "names 3 exact
callers with file:line references" (deserves 3/3). This suppresses the true
effect size of Joern context.

Criteria scored on 0-3 with anchored descriptors:
  F3 — Integration awareness
  F4 — Broken contracts / dependent code impact
  P1 — Performance issues (active criteria, high kappa)
  R2 — Complexity / simplification
  T3 — Specific test files named

Design:
  - Pilot: KG-rich PRs only (n=31, PRs with n_tests>0 OR n_deps>2)
  - Same 2-judge panel as Joern experiment: gemini-2.5-flash + gemini-2.0-flash
  - Compare: binary d_z vs graded d_z on same criterion set
  - Check inter-rater agreement (Spearman ρ) for 0-3 vs kappa for 0/1

Usage:
    source load_env.sh && python3 scripts/evaluate_reviews_graded.py [--pilot] [--all]

Estimated cost (pilot, 31 PRs × 2 modes × 2 judges × 5 criteria):
  ~$1.50 at Gemini Flash pricing (context is short — just the review + rubric)

Output:
  results/GRADED_PILOT_RESULTS.json
  results/GRADED_PILOT_REPORT.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from prnote.llm import generate_completion  # noqa: E402

RESULTS_DIR = REPO_ROOT / "results"

# ---------------------------------------------------------------------------
# Graded criteria — 5 clean criteria with anchored 0-3 descriptors
# ---------------------------------------------------------------------------

GRADED_CRITERIA = [
    {
        "id": "F3",
        "category": "Functionality",
        "description": "Integration awareness — how the change interacts with callers/dependents",
        "anchors": {
            0: "No mention of integration or impact on other components.",
            1: "Vaguely notes that integration may be affected, but names no specific component.",
            2: "Names at least one specific caller, module, or dependent file that is affected.",
            3: "Names multiple specific callers or dependent components with file paths or function "
               "names, and explains the concrete integration risk for each.",
        },
    },
    {
        "id": "F4",
        "category": "Functionality",
        "description": "Broken contracts — potential breaking changes or impact on dependent code",
        "anchors": {
            0: "No mention of breaking changes or API contract violations.",
            1: "Generically warns that callers or API consumers may be affected, without specifics.",
            2: "Identifies at least one specific API contract or caller expectation that could break.",
            3: "Identifies multiple specific contract violations with file/function references and "
               "explains exactly what downstream behavior would change.",
        },
    },
    {
        "id": "P1",
        "category": "Performance",
        "description": "Performance issues — identifies potential inefficiencies in the changed code",
        "anchors": {
            0: "No mention of performance.",
            1: "Generic comment that performance could be affected (e.g., 'this might be slow').",
            2: "Identifies a specific operation, loop, or data structure that introduces a "
               "performance concern, with a brief explanation.",
            3: "Identifies multiple specific performance issues with code references, explains "
               "the complexity or bottleneck, and suggests a concrete alternative or fix.",
        },
    },
    {
        "id": "R2",
        "category": "Readability",
        "description": "Complexity — identifies unnecessary complexity or suggests simplification",
        "anchors": {
            0: "No comment on complexity or code structure.",
            1: "Generic remark that the code is complex or could be simplified.",
            2: "Points to a specific function or block that is unnecessarily complex and "
               "suggests a concrete simplification.",
            3: "Identifies multiple instances of unnecessary complexity with code-level "
               "references, explains why each is problematic, and offers specific refactoring "
               "suggestions.",
        },
    },
    {
        "id": "T3",
        "category": "Tests",
        "description": "Specific test files — names exact test files that should be added or updated",
        "anchors": {
            0: "No mention of test files, or only says 'add tests' generically.",
            1: "Mentions that tests should exist but does not name a file (e.g., 'the test suite').",
            2: "Names at least one specific test file path from the repository.",
            3: "Names multiple specific test file paths, references the exact test scenarios "
               "or functions within those files that need coverage, and explains what edge "
               "cases are currently missing.",
        },
    },
]

GRADED_IDS = {c["id"] for c in GRADED_CRITERIA}

# ---------------------------------------------------------------------------
# KG-rich PR list (n_tests>0 OR n_deps>2 — precomputed from evidence packs)
# Excluded Go PRs: 9, 27, 35, 36, 37
# ---------------------------------------------------------------------------

KG_RICH_PRS = [
    1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    21, 22, 23, 24, 25, 26, 28, 29, 30, 31, 32, 33, 34, 38, 39, 40,
]

# ---------------------------------------------------------------------------
# Judge prompts
# ---------------------------------------------------------------------------

GRADED_SYSTEM_PROMPT = """You are an expert code review evaluator. Your task is to score a code review on a 0-3 graded scale for specific quality criteria.

For each criterion, you will be given:
- The criterion name and description
- Anchored descriptors for scores 0, 1, 2, and 3

Score EXACTLY according to the anchors. Do NOT round up — score the highest anchor that is FULLY satisfied.

Be strict: a review that only partially meets an anchor gets the score below it.

Respond with a JSON object. Do NOT include any text outside the JSON."""


def build_graded_user_prompt(review: str, pr_context: dict[str, Any]) -> str:
    criteria_blocks = []
    for i, c in enumerate(GRADED_CRITERIA):
        anchors = "\n".join(
            f"  {score}: {desc}" for score, desc in c["anchors"].items()
        )
        criteria_blocks.append(
            f"{i+1}. [{c['id']}] {c['description']}\n"
            f"  Anchors:\n{anchors}"
        )
    criteria_text = "\n\n".join(criteria_blocks)

    example_scores = ", ".join(
        f'{{"id": "{c["id"]}", "score": 0, "evidence": "..."}}'
        for c in GRADED_CRITERIA[:2]
    )

    return f"""## PR Being Reviewed
Title: {pr_context.get('title', 'Unknown') or '(no title)'}
Description: {(pr_context.get('body') or 'N/A')[:400]}

## Review to Evaluate
{review[:5000]}

## Criteria to Score (0-3)

{criteria_text}

## Instructions
Score EACH criterion from 0 to 3 using the anchors above. Respond ONLY with this JSON:

```json
{{
  "scores": [
    {example_scores},
    ...
  ]
}}
```

Include ALL {len(GRADED_CRITERIA)} criteria. Each score MUST be 0, 1, 2, or 3.
Evidence should be a direct quote or paraphrase from the review that justifies your score."""


# ---------------------------------------------------------------------------
# Parse graded judge output
# ---------------------------------------------------------------------------

JSON_OBJECT_RE = re.compile(r"\{[\s\S]*\}")
GRADED_ENTRY_RE = re.compile(
    r'"id"\s*:\s*"([A-Za-z]\d+)"[\s\S]{0,400}?"score"\s*:\s*([0-3])',
)
EVIDENCE_RE = re.compile(
    r'"id"\s*:\s*"([A-Za-z]\d+)"[\s\S]{0,400}?"score"\s*:\s*[0-3][\s\S]{0,50}?"evidence"\s*:\s*"([^\n]{0,400}?)"\s*[,}]',
)


def _parse_graded_output(raw: str) -> tuple[dict[str, int], dict[str, str], str]:
    scores: dict[str, int] = {}
    evidence: dict[str, str] = {}

    match = JSON_OBJECT_RE.search(raw)
    if match:
        try:
            payload = json.loads(match.group())
            for item in payload.get("scores", []) or []:
                cid = str(item.get("id", "")).strip()
                if cid not in GRADED_IDS:
                    continue
                try:
                    s = int(item.get("score", -1))
                except Exception:
                    s = -1
                if s not in (0, 1, 2, 3):
                    continue
                scores[cid] = s
                evidence[cid] = str(item.get("evidence", ""))[:500]
            if scores:
                return scores, evidence, ""
        except Exception:
            pass

    # Regex fallback
    for m in GRADED_ENTRY_RE.finditer(raw):
        cid = m.group(1)
        if cid in GRADED_IDS:
            scores[cid] = int(m.group(2))

    for m in EVIDENCE_RE.finditer(raw):
        cid = m.group(1)
        if cid in GRADED_IDS and cid not in evidence:
            evidence[cid] = m.group(2).strip()[:500]

    if not scores:
        return scores, evidence, f"parse_error: no graded scores extracted: {raw[:300]!r}"
    return scores, evidence, ""


# ---------------------------------------------------------------------------
# Single judge call
# ---------------------------------------------------------------------------


@dataclass
class GradedJudgeVerdict:
    model: str
    scores: dict[str, int]   # criterion_id -> 0-3; -1 = not scored
    evidence: dict[str, str]
    error: str = ""


def judge_graded(review: str, pr_context: dict[str, Any], model: str) -> GradedJudgeVerdict:
    prompt = build_graded_user_prompt(review, pr_context)
    try:
        raw = generate_completion(
            prompt=prompt,
            system=GRADED_SYSTEM_PROMPT,
            model=model,
            temperature=0.0,
        )
    except Exception as exc:
        return GradedJudgeVerdict(model=model, scores={}, evidence={}, error=f"api_error: {exc}")

    scores, evidence, err = _parse_graded_output(raw or "")
    for c in GRADED_CRITERIA:
        scores.setdefault(c["id"], -1)
        evidence.setdefault(c["id"], "")

    n_valid = sum(1 for s in scores.values() if s in (0, 1, 2, 3))
    if n_valid < len(GRADED_CRITERIA):
        return GradedJudgeVerdict(
            model=model, scores=scores, evidence=evidence,
            error=err or f"parse_error: only {n_valid}/{len(GRADED_CRITERIA)} graded"
        )
    return GradedJudgeVerdict(model=model, scores=scores, evidence=evidence)


# ---------------------------------------------------------------------------
# Panel aggregation — mean score (not majority vote; graded scale)
# ---------------------------------------------------------------------------


def aggregate_graded_panel(verdicts: list[GradedJudgeVerdict]) -> dict[str, float]:
    """Mean score per criterion across valid judges."""
    result: dict[str, float] = {}
    for c in GRADED_CRITERIA:
        valid = [v.scores[c["id"]] for v in verdicts if v.scores.get(c["id"]) in (0, 1, 2, 3)]
        result[c["id"]] = sum(valid) / len(valid) if valid else -1.0
    return result


# ---------------------------------------------------------------------------
# Evaluate one (pr_id, mode) cell
# ---------------------------------------------------------------------------


def load_review(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_pr_context(pr_id: int) -> dict[str, Any]:
    for p in [
        REPO_ROOT / "data" / "luca_prs_v2" / f"pr{pr_id}_evidence.json",
        REPO_ROOT / "data" / "luca_prs_fixed" / f"pr{pr_id}_evidence.json",
    ]:
        if p.exists():
            ev = json.loads(p.read_text())
            pr = ev.get("pr", {})
            return {"title": pr.get("title", ""), "body": (pr.get("body") or "")[:500], "pr_id": pr_id}
    return {"title": "", "body": "", "pr_id": pr_id}


def evaluate_cell(
    pr_id: int,
    mode: str,
    judges: list[str],
    review_path: Path,
    cache_dir: Path,
) -> dict[str, Any] | None:
    cache_path = cache_dir / f"pr{pr_id}_{mode}.json"
    if cache_path.exists():
        result = json.loads(cache_path.read_text())
        print(f"  PR{pr_id} {mode}: cached  graded={result.get('mean_graded_total', '?'):.2f}")
        return result

    if not review_path.exists():
        print(f"  PR{pr_id} {mode}: SKIP — review not found at {review_path}")
        return None

    review = load_review(review_path)
    pr_context = load_pr_context(pr_id)

    verdicts = [judge_graded(review, pr_context, m) for m in judges]
    mean_scores = aggregate_graded_panel(verdicts)

    errors = [v.error for v in verdicts if v.error]
    if errors:
        print(f"  PR{pr_id} {mode}: WARN judge errors: {errors}")

    mean_total = sum(v for v in mean_scores.values() if v >= 0)
    result = {
        "pr_id": pr_id,
        "mode": mode,
        "mean_scores": mean_scores,
        "mean_graded_total": mean_total,
        "per_judge": [asdict(v) for v in verdicts],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    cache_path.write_text(json.dumps(result, indent=2))
    score_str = " ".join(f"{c['id']}={mean_scores.get(c['id'], -1):.1f}" for c in GRADED_CRITERIA)
    print(f"  PR{pr_id} {mode}: {score_str}  total={mean_total:.2f}")
    return result


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def compute_stats(deltas: list[float]) -> dict[str, Any]:
    import numpy as np
    from scipy import stats as sp_stats

    d = np.array(deltas)
    n = len(d)
    if n == 0:
        return {}

    rng = np.random.default_rng(2026)
    boot = [rng.choice(d, n, replace=True).mean() for _ in range(10000)]
    ci_lo, ci_hi = np.percentile(boot, [2.5, 97.5])
    obs = d.mean()
    p_perm = sum(
        1 for _ in range(20000) if (rng.choice([-1, 1], n) * d).mean() >= obs
    ) / 20000
    _, p_wilc = sp_stats.wilcoxon(d, alternative="greater")
    dz = obs / np.std(d, ddof=1)
    wins = int((d > 0).sum())
    ties = int((d == 0).sum())
    losses = int((d < 0).sum())

    return {
        "n": n,
        "mean_delta": float(obs),
        "ci_95": [float(ci_lo), float(ci_hi)],
        "p_perm": float(p_perm),
        "p_wilcoxon": float(p_wilc),
        "cohens_dz": float(dz),
        "wins": wins, "ties": ties, "losses": losses,
    }


def spearman_icc(scores_a: list[float], scores_b: list[float]) -> float:
    from scipy import stats as sp_stats
    if len(scores_a) < 3:
        return float("nan")
    r, _ = sp_stats.spearmanr(scores_a, scores_b)
    return float(r)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def resolve_review_path(pr_id: int, mode: str, mode_dirs: dict[str, Path]) -> Path:
    """Find the review file for a given (pr_id, mode) across configured directories.

    For 'baseline': looks for pr{N}_baseline.md in the baseline dir.
    For Joern modes: looks for pr{N}_review.md in the joern dir (exp_b_full35 naming).
    """
    if mode in mode_dirs:
        d = mode_dirs[mode]
        # Try canonical name first, then Joern's pr{N}_review.md naming
        for name in [f"pr{pr_id}_{mode}.md", f"pr{pr_id}_review.md"]:
            p = d / name
            if p.exists():
                return p
    # Fallback: any configured directory
    for d in mode_dirs.values():
        for name in [f"pr{pr_id}_{mode}.md", f"pr{pr_id}_review.md"]:
            p = d / name
            if p.exists():
                return p
    # Return expected path even if missing (evaluate_cell will SKIP with a message)
    return mode_dirs.get(mode, REPO_ROOT) / f"pr{pr_id}_{mode}.md"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", action="store_true",
                        help="Run on KG-rich PRs only (n=31) — default")
    parser.add_argument("--all", dest="all_prs", action="store_true",
                        help="Run on all 40 PRs (ignores --pilot)")
    parser.add_argument("--judges", type=str,
                        default="openai:gpt-4o,openai:gpt-4o-mini",
                        help="Comma-separated judge models")
    parser.add_argument("--baseline-dir", type=str,
                        default=str(REPO_ROOT / "outputs" / "luca_prs_v2"),
                        help="Directory containing pr{N}_baseline.md reviews")
    parser.add_argument("--joern-dir", type=str,
                        default=str(REPO_ROOT / "experiments" / "2026-05-15_joern_kg_main" / "exp_b_full35"),
                        help="Directory containing Joern-KG reviews (pr{N}_review.md)")
    parser.add_argument("--joern-mode-label", type=str, default="joern_kg",
                        help="Label for the Joern treatment mode in output (default: joern_kg)")
    args = parser.parse_args()

    judges = [j.strip() for j in args.judges.split(",") if j.strip()]
    baseline_dir = Path(args.baseline_dir)
    joern_dir = Path(args.joern_dir)
    joern_label = args.joern_mode_label

    mode_dirs = {
        "baseline": baseline_dir,
        joern_label: joern_dir,
    }
    modes = ["baseline", joern_label]

    # PR list — exclude Go PRs (9, 27, 35, 36, 37) always
    GO_PRS = {9, 27, 35, 36, 37}
    if args.all_prs:
        prs = [p for p in range(1, 41) if p not in GO_PRS]
        label = f"all non-Go PRs (n={len(prs)})"
    else:
        prs = [p for p in KG_RICH_PRS if p not in GO_PRS]
        label = f"KG-rich non-Go PRs (n={len(prs)})"

    cache_dir = RESULTS_DIR / "graded_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print(f"GRADED 0-3 PILOT — {label}")
    print(f"Criteria: {', '.join(c['id'] for c in GRADED_CRITERIA)}")
    print(f"Modes: {modes}")
    print(f"Judges: {judges}")
    print(f"Baseline dir: {baseline_dir.relative_to(REPO_ROOT)}")
    print(f"Joern dir:    {joern_dir.relative_to(REPO_ROOT)}")
    print(f"Cache: {cache_dir.relative_to(REPO_ROOT)}")

    est_cells = len(prs) * len(modes)
    est_api_calls = est_cells * len(judges)
    print(f"\nEstimated cost: ~${est_api_calls * 0.003:.2f}  "
          f"({est_api_calls} API calls × ~$0.003 avg)")
    print("=" * 72)

    # Run all (pr_id, mode) cells in parallel
    cells = [(pr_id, mode) for pr_id in prs for mode in modes]
    results: dict[tuple[int, str], dict] = {}

    with ThreadPoolExecutor(max_workers=min(len(cells), 20)) as ex:
        futures = {
            ex.submit(
                evaluate_cell, pr_id, mode, judges,
                resolve_review_path(pr_id, mode, mode_dirs),
                cache_dir,
            ): (pr_id, mode)
            for pr_id, mode in cells
        }
        for fut in as_completed(futures):
            key = futures[fut]
            try:
                r = fut.result()
                if r is not None:
                    results[key] = r
            except Exception as exc:
                print(f"  ERROR {key}: {exc}")

    # ----------------------------------------------------------------
    # Statistics: compare baseline vs each treatment mode
    # ----------------------------------------------------------------
    print(f"\n{'='*72}")
    print("GRADED SCALE STATISTICS")
    print(f"{'='*72}")

    all_stats: dict[str, Any] = {}

    treatment_modes = [m for m in modes if m != "baseline"]
    for mode in treatment_modes:
        print(f"\n  Mode: {mode} vs baseline")
        # Per-criterion deltas
        per_criterion_stats: dict[str, Any] = {}
        for c in GRADED_CRITERIA:
            cid = c["id"]
            deltas = []
            for pr_id in prs:
                key_t = (pr_id, mode)
                key_b = (pr_id, "baseline")
                if key_t in results and key_b in results:
                    t_score = results[key_t]["mean_scores"].get(cid, -1)
                    b_score = results[key_b]["mean_scores"].get(cid, -1)
                    if t_score >= 0 and b_score >= 0:
                        deltas.append(t_score - b_score)
            if deltas:
                st = compute_stats(deltas)
                sig = ("***" if st["p_perm"] < 0.001 else
                       "**" if st["p_perm"] < 0.01 else
                       "*" if st["p_perm"] < 0.05 else "n.s.")
                print(f"    {cid}: Δ={st['mean_delta']:+.3f}  95%CI=[{st['ci_95'][0]:+.2f},{st['ci_95'][1]:+.2f}]  "
                      f"p={st['p_perm']:.4f}{sig}  d_z={st['cohens_dz']:+.3f}  W/T/L={st['wins']}/{st['ties']}/{st['losses']}")
                per_criterion_stats[cid] = st

        # Aggregate: sum of 5 criteria deltas
        total_deltas = []
        for pr_id in prs:
            key_t = (pr_id, mode)
            key_b = (pr_id, "baseline")
            if key_t in results and key_b in results:
                t_tot = results[key_t]["mean_graded_total"]
                b_tot = results[key_b]["mean_graded_total"]
                total_deltas.append(t_tot - b_tot)

        if total_deltas:
            agg_st = compute_stats(total_deltas)
            sig = ("***" if agg_st["p_perm"] < 0.001 else
                   "**" if agg_st["p_perm"] < 0.01 else
                   "*" if agg_st["p_perm"] < 0.05 else "n.s.")
            print(f"\n    AGGREGATE (5 criteria, /15): Δ={agg_st['mean_delta']:+.3f}  "
                  f"95%CI=[{agg_st['ci_95'][0]:+.2f},{agg_st['ci_95'][1]:+.2f}]  "
                  f"p={agg_st['p_perm']:.4f}{sig}  d_z={agg_st['cohens_dz']:+.3f}  "
                  f"W/T/L={agg_st['wins']}/{agg_st['ties']}/{agg_st['losses']}")
            all_stats[mode] = {
                "per_criterion": per_criterion_stats,
                "aggregate": agg_st,
            }

    # ----------------------------------------------------------------
    # Inter-rater agreement on graded scale (Spearman ρ between judges)
    # ----------------------------------------------------------------
    print(f"\n{'='*72}")
    print("INTER-RATER AGREEMENT (Spearman ρ, graded 0-3)")
    print(f"{'='*72}")

    if len(judges) >= 2:
        for mode in modes:
            print(f"\n  Mode: {mode}")
            for c in GRADED_CRITERIA:
                cid = c["id"]
                j0_scores, j1_scores = [], []
                for pr_id in prs:
                    key = (pr_id, mode)
                    if key not in results:
                        continue
                    pj = results[key]["per_judge"]
                    if len(pj) < 2:
                        continue
                    s0 = pj[0]["scores"].get(cid, -1)
                    s1 = pj[1]["scores"].get(cid, -1)
                    if s0 in (0, 1, 2, 3) and s1 in (0, 1, 2, 3):
                        j0_scores.append(s0)
                        j1_scores.append(s1)
                rho = spearman_icc(j0_scores, j1_scores)
                agreement_label = (
                    "excellent" if rho >= 0.8 else
                    "good" if rho >= 0.6 else
                    "moderate" if rho >= 0.4 else
                    "weak"
                )
                print(f"    {cid}: ρ={rho:.3f} ({agreement_label}, n={len(j0_scores)})")

    # ----------------------------------------------------------------
    # Write output
    # ----------------------------------------------------------------
    out = {
        "experiment": "graded_pilot",
        "prs": prs,
        "judges": judges,
        "modes": modes,
        "joern_mode_label": joern_label,
        "graded_criteria": [c["id"] for c in GRADED_CRITERIA],
        "stats": all_stats,
        "per_cell": {
            f"pr{pr_id}_{mode}": results.get((pr_id, mode))
            for pr_id in prs
            for mode in modes
            if (pr_id, mode) in results
        },
    }

    out_path = RESULTS_DIR / "GRADED_PILOT_RESULTS.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n  Wrote: {out_path.relative_to(REPO_ROOT)}")

    # Markdown summary
    _write_report(all_stats, prs, modes, judges)


def _write_report(all_stats: dict, prs: list[int], modes: list[str], judges: list[str]) -> None:
    lines = [
        "# Graded 0-3 Scale Pilot — Results",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
        f"**PRs:** {len(prs)}  |  **Judges:** {', '.join(judges)}",
        f"**Criteria:** F3, F4, P1, R2, T3 (clean subscale, graded 0-3 with anchors)",
        "",
        "---",
        "",
        "## Motivation",
        "",
        "Binary 0/1 scoring cannot distinguish a review that vaguely mentions integration",
        "from one that names 3 exact callers with file:line references. This pilot replaces",
        "binary judgment with anchored 0-3 descriptors to test whether a richer signal",
        "increases effect size (d_z).",
        "",
        "---",
        "",
        "## Results",
        "",
    ]

    treatment_modes = [m for m in modes if m != "baseline"]
    for mode in treatment_modes:
        if mode not in all_stats:
            continue
        st = all_stats[mode]
        agg = st.get("aggregate", {})
        sig = ("***" if agg.get("p_perm", 1) < 0.001 else
               "**" if agg.get("p_perm", 1) < 0.01 else
               "*" if agg.get("p_perm", 1) < 0.05 else "n.s.")
        lines += [
            f"### {mode} vs baseline",
            "",
            f"**Aggregate (5 criteria, /15):** Δ={agg.get('mean_delta', 0):+.3f}  "
            f"95%CI=[{agg.get('ci_95', [0,0])[0]:+.2f}, {agg.get('ci_95', [0,0])[1]:+.2f}]  "
            f"p={agg.get('p_perm', 1):.4f}{sig}  **d_z={agg.get('cohens_dz', 0):+.3f}**  "
            f"W/T/L={agg.get('wins', 0)}/{agg.get('ties', 0)}/{agg.get('losses', 0)}",
            "",
            "| Criterion | Δ mean | 95% CI | p | d_z | W/T/L |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for c in GRADED_CRITERIA:
            cid = c["id"]
            cs = st.get("per_criterion", {}).get(cid, {})
            if not cs:
                continue
            csig = ("***" if cs.get("p_perm", 1) < 0.001 else
                    "**" if cs.get("p_perm", 1) < 0.01 else
                    "*" if cs.get("p_perm", 1) < 0.05 else "")
            ci = cs.get("ci_95", [0, 0])
            lines.append(
                f"| {cid} — {c['description'][:35]} | "
                f"{cs.get('mean_delta', 0):+.3f} | "
                f"[{ci[0]:+.2f}, {ci[1]:+.2f}] | "
                f"{cs.get('p_perm', 1):.4f}{csig} | "
                f"{cs.get('cohens_dz', 0):+.3f} | "
                f"{cs.get('wins', 0)}/{cs.get('ties', 0)}/{cs.get('losses', 0)} |"
            )
        lines.append("")

    lines += [
        "---",
        "",
        "## Anchor Definitions (0-3)",
        "",
    ]
    for c in GRADED_CRITERIA:
        lines.append(f"### {c['id']} — {c['description']}")
        lines.append("")
        for score, desc in c["anchors"].items():
            lines.append(f"- **{score}:** {desc}")
        lines.append("")

    report_path = RESULTS_DIR / "GRADED_PILOT_REPORT.md"
    report_path.write_text("\n".join(lines))
    print(f"  Wrote: {report_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
