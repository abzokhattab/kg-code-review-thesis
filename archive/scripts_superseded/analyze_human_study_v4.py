#!/usr/bin/env python3
"""
analyze_human_study_v4.py — Human ↔ LLM judge agreement analysis for the v4 study.

The v4 study asks raters to choose a 5-point preference score (-2..+2) for each
PR comparing baseline vs KG. This script answers the core thesis question:

  Do human preference rankings agree with LLM judge rankings?

Primary statistic: Kendall's τ between the per-PR human preference mean and the
per-PR LLM judge delta (kg_total - baseline_total). Computed at two levels:
  1. Per-PR (6 data points): do humans rank the PRs in the same order as judges?
  2. Per-rater-per-PR: intraclass correlation / mean preference by expected outcome.

Also reports:
  - Agreement by expected outcome (kg_wins / tie / kg_loses)
  - Inter-rater reliability (Krippendorff's α)
  - Rater quality flags (time < 60s per PR → likely rushed)
  - Demographic breakdown

Input: CSV exported from the Google Sheet `responses` tab.
  Required columns: rater_id, pr_id, preference_score, why, difficulty,
                    time_spent_ms, github_clicks, completed_at
  (comparison, mode_A, mode_B are present but not needed for the core analysis
   since the study is fixed: baseline vs KG, blinded)

LLM judge reference: results/checklist_evaluation_llm_multi__v2.json

SUPERSEDED, and its only committed output is fabricated. This script has never
been run against real responses; the v4 design was replaced by the per-criterion
design in experiments/2026-07-06_user_study_prs/analyze_responses.py, which is
what produced every human-study number in the thesis. The --sample flag below
analyses data invented by _write_sample_csv(). Its output is written under a
SYNTHETIC_ prefix and stamped, because an earlier version wrote it to
results/human_study_v4_agreement.json, where it read as a genuine result.

Usage:
    python3 scripts/analyze_human_study_v4.py --human human_eval/responses.csv
    python3 scripts/analyze_human_study_v4.py --sample   # fabricated data; never cite
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"
CHECKLIST_PATH = RESULTS_DIR / "checklist_evaluation_llm_multi__v2.json"

# Study design constants
STUDY_PRS = [31, 20, 47, 23, 22, 27]
COMPARISON = "bl_vs_kg"
MODE_A_CANONICAL = "baseline"
MODE_B_CANONICAL = "kg"

# Expected direction: positive = humans should prefer B (KG), negative = prefer A (baseline)
# Based on LLM judge delta (kg_total - baseline_total)
EXPECTED_DIRECTION = {
    31: +4,   # strong KG win
    47: +3,   # moderate KG win
    22: +4,   # moderate KG win
    27:  0,   # tie
    20: -3,   # KG loses
    23: -3,   # KG loses
}

EXPECTED_LABEL = {
    31: "kg_wins_strong",
    47: "kg_wins_moderate",
    22: "kg_wins_moderate",
    27: "tie",
    20: "kg_loses",
    23: "kg_loses",
}

MIN_TIME_MS = 60_000   # < 1 min per PR → flag as rushed


# ── LLM judge scores ──────────────────────────────────────────────────────────

def load_llm_deltas(path: Path = CHECKLIST_PATH) -> dict[int, dict[str, Any]]:
    """Return per-PR LLM scores: {pr_id: {kg_total, baseline_total, delta_total,
    kg_kgrel, baseline_kgrel, delta_kgrel}}."""
    if not path.exists():
        sys.exit(f"LLM checklist not found: {path}")
    with path.open() as f:
        data = json.load(f)
    scores: dict[int, dict[str, int]] = {}
    for ev in data["evaluations"]:
        pr = int(ev["pr_id"])
        mode = ev["mode"]
        if mode in ("baseline", "kg"):
            scores.setdefault(pr, {})[mode] = {
                "total": ev["total_score"],
                "kgrel": ev["kg_relevant_score"],
            }
    out: dict[int, dict[str, Any]] = {}
    for pr, modes in scores.items():
        if "baseline" in modes and "kg" in modes:
            b, k = modes["baseline"], modes["kg"]
            out[pr] = {
                "baseline_total":  b["total"],
                "kg_total":        k["total"],
                "delta_total":     k["total"] - b["total"],
                "baseline_kgrel":  b["kgrel"],
                "kg_kgrel":        k["kgrel"],
                "delta_kgrel":     k["kgrel"] - b["kgrel"],
            }
    return out


# ── Human data loading ────────────────────────────────────────────────────────

def load_responses(path: Path) -> list[dict[str, Any]]:
    """Parse the responses CSV from the Google Sheet.

    The webhook writes one row per task per submit. Columns:
      received_at, rater_id, completed_at, pr_id, comparison,
      mode_A, mode_B, preference_score, why, difficulty,
      time_spent_ms, github_clicks

    Returns list of dicts with typed fields. Duplicate rows for the same
    (rater_id, pr_id) are de-duplicated by keeping the latest received_at.
    """
    if not path.exists():
        sys.exit(f"Human responses file not found: {path}")

    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = {h.lower().strip(): h for h in (reader.fieldnames or [])}

        def col(row: dict, *names: str, default: str = "") -> str:
            for n in names:
                h = headers.get(n.lower())
                if h and row.get(h) not in (None, ""):
                    return str(row[h]).strip()
            return default

        for row in reader:
            try:
                pr_id = int(col(row, "pr_id"))
            except ValueError:
                continue
            try:
                pref = int(col(row, "preference_score"))
                if pref not in range(-2, 3):
                    continue
            except ValueError:
                continue

            # Unblind: the webhook stores mode_A and mode_B.
            # preference_score > 0 means rater preferred A (whatever mode that was).
            # We normalise so positive = prefers KG over baseline.
            mode_a = col(row, "mode_a", "mode_A").lower() or MODE_A_CANONICAL
            mode_b = col(row, "mode_b", "mode_B").lower() or MODE_B_CANONICAL

            # If A=kg and B=baseline, flip the sign so positive always = prefers KG
            if mode_a == "kg" and mode_b == "baseline":
                normalised_pref = -pref
            elif mode_a == "baseline" and mode_b == "kg":
                normalised_pref = pref
            else:
                # Unexpected assignment — keep raw score, note it
                normalised_pref = pref

            try:
                diff = int(col(row, "difficulty")) if col(row, "difficulty") else None
            except ValueError:
                diff = None
            try:
                t_ms = int(col(row, "time_spent_ms")) if col(row, "time_spent_ms") else None
            except ValueError:
                t_ms = None
            try:
                gh = int(col(row, "github_clicks")) if col(row, "github_clicks") else 0
            except ValueError:
                gh = 0

            rows.append({
                "rater_id":         col(row, "rater_id"),
                "pr_id":            pr_id,
                "comparison":       col(row, "comparison") or COMPARISON,
                "mode_A":           mode_a,
                "mode_B":           mode_b,
                "preference_score": pref,           # raw (A positive)
                "pref_kg":          normalised_pref, # normalised (KG positive)
                "why":              col(row, "why"),
                "difficulty":       diff,
                "time_spent_ms":    t_ms,
                "github_clicks":    gh,
                "received_at":      col(row, "received_at"),
                "completed_at":     col(row, "completed_at"),
            })

    # Dedup: keep latest per (rater_id, pr_id)
    latest: dict[tuple[str, int], dict] = {}
    for r in rows:
        key = (r["rater_id"], r["pr_id"])
        if key not in latest or r["received_at"] > latest[key]["received_at"]:
            latest[key] = r
    return list(latest.values())


def load_demographics(path: Path | None) -> dict[str, dict[str, str]]:
    if not path or not path.exists():
        return {}
    out: dict[str, dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rid = (row.get("rater_id") or "").strip()
            if not rid:
                continue
            out[rid] = {k.strip(): (v or "").strip() for k, v in row.items() if k}
    return out


# ── Statistics ────────────────────────────────────────────────────────────────

def kendall_tau_b(x: list[float], y: list[float]) -> tuple[float, float]:
    """Kendall's τ-b and two-tailed p-value (exact for small n)."""
    n = len(x)
    if n < 2:
        return float("nan"), float("nan")
    concordant = discordant = ties_x = ties_y = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = x[i] - x[j]
            dy = y[i] - y[j]
            prod = dx * dy
            if prod > 0:
                concordant += 1
            elif prod < 0:
                discordant += 1
            else:
                if dx == 0:
                    ties_x += 1
                if dy == 0:
                    ties_y += 1
    denom = math.sqrt(
        (concordant + discordant + ties_x) * (concordant + discordant + ties_y)
    )
    tau = (concordant - discordant) / denom if denom > 0 else float("nan")

    # Approximate p-value via normal approximation (valid for n >= 8)
    # For small n we report it but flag it
    n0 = n * (n - 1) / 2
    var_tau = (2 * (2 * n + 5)) / (9 * n * (n - 1))
    z = tau / math.sqrt(var_tau) if var_tau > 0 else float("nan")
    # two-tailed p from standard normal
    p = 2 * (1 - _norm_cdf(abs(z))) if not math.isnan(z) else float("nan")
    return round(tau, 4), round(p, 4)


def _norm_cdf(z: float) -> float:
    return (1 + math.erf(z / math.sqrt(2))) / 2


def krippendorff_alpha_ordinal(ratings: dict[str, dict[int, int | None]]) -> float:
    """Krippendorff's α for ordinal data.

    ratings: {rater_id: {pr_id: score_or_None}}
    Score scale: -2..+2 ordinal.
    Returns α ∈ [-1, 1] (1 = perfect, 0 = chance, <0 = worse than chance).
    """
    # Build coincidence matrix
    # For ordinal metric: d²(v,w) = (v - w)²
    rater_ids = list(ratings.keys())
    pr_ids = sorted({pr for r in ratings.values() for pr in r})

    # Collect all paired observations
    D_o = 0.0   # observed disagreement
    D_e = 0.0   # expected disagreement
    n_pairs = 0
    value_counts: dict[int, int] = defaultdict(int)
    total_values = 0

    for pr in pr_ids:
        vals = [ratings[r].get(pr) for r in rater_ids if ratings[r].get(pr) is not None]
        if len(vals) < 2:
            continue
        mu = len(vals)
        for i in range(len(vals)):
            for j in range(i + 1, len(vals)):
                d2 = (vals[i] - vals[j]) ** 2
                D_o += d2 / (mu - 1)
                n_pairs += 1
        for v in vals:
            value_counts[v] += 1
            total_values += 1

    if n_pairs == 0 or total_values < 2:
        return float("nan")

    # Expected disagreement using distribution of all values
    N = total_values
    for v1 in value_counts:
        for v2 in value_counts:
            d2 = (v1 - v2) ** 2
            D_e += d2 * value_counts[v1] * value_counts[v2]
    D_e /= N * (N - 1)

    if D_e == 0:
        return 1.0
    return round(1 - D_o / (n_pairs * D_e), 4)


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")

def _std(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyze(
    responses: list[dict[str, Any]],
    llm: dict[int, dict[str, Any]],
    demographics: dict[str, dict[str, str]] | None = None,
    excluded_raters: set[str] | None = None,
) -> dict[str, Any]:

    excluded_raters = excluded_raters or set()
    responses = [r for r in responses if r["rater_id"] not in excluded_raters]

    raters = sorted({r["rater_id"] for r in responses})
    pr_ids = sorted({r["pr_id"] for r in responses})

    # ── Per-PR human preference mean (normalised so +ve = prefers KG) ─────────
    per_pr: dict[int, dict[str, Any]] = {}
    by_pr: dict[int, list[int]] = defaultdict(list)
    for r in responses:
        by_pr[r["pr_id"]].append(r["pref_kg"])

    for pr in pr_ids:
        scores = by_pr[pr]
        llm_info = llm.get(pr, {})
        per_pr[pr] = {
            "pr_id":              pr,
            "expected":           EXPECTED_LABEL.get(pr, "unknown"),
            "llm_delta_total":    llm_info.get("delta_total"),
            "llm_delta_kgrel":    llm_info.get("delta_kgrel"),
            "n_raters":           len(scores),
            "mean_pref_kg":       round(_mean(scores), 3),
            "std_pref_kg":        round(_std(scores), 3),
            "raw_scores":         scores,
            "pct_prefer_kg":      round(100 * sum(1 for s in scores if s > 0) / len(scores), 1) if scores else None,
            "pct_prefer_baseline":round(100 * sum(1 for s in scores if s < 0) / len(scores), 1) if scores else None,
            "pct_no_preference":  round(100 * sum(1 for s in scores if s == 0) / len(scores), 1) if scores else None,
        }

    # ── Kendall's τ: human mean pref vs LLM delta ─────────────────────────────
    study_prs = [p for p in STUDY_PRS if p in per_pr and llm.get(p)]
    human_means  = [per_pr[p]["mean_pref_kg"]   for p in study_prs]
    llm_deltas_t = [llm[p]["delta_total"]        for p in study_prs]
    llm_deltas_k = [llm[p]["delta_kgrel"]        for p in study_prs]

    tau_total, p_total = kendall_tau_b(human_means, llm_deltas_t)
    tau_kgrel, p_kgrel = kendall_tau_b(human_means, llm_deltas_k)

    # ── Agreement direction per PR ─────────────────────────────────────────────
    # "agree" = human mean sign matches LLM delta sign (both positive, both negative, or both ~0)
    direction_agreement: list[dict[str, Any]] = []
    for p in study_prs:
        hm = per_pr[p]["mean_pref_kg"]
        ld = llm[p]["delta_total"]
        # sign: +1 / -1 / 0
        h_sign = 1 if hm > 0.2 else (-1 if hm < -0.2 else 0)
        l_sign = 1 if ld > 0 else (-1 if ld < 0 else 0)
        agree = h_sign == l_sign
        direction_agreement.append({
            "pr_id":        p,
            "expected":     EXPECTED_LABEL.get(p, "unknown"),
            "human_mean":   per_pr[p]["mean_pref_kg"],
            "llm_delta":    ld,
            "human_sign":   h_sign,
            "llm_sign":     l_sign,
            "agrees":       agree,
        })

    n_agree = sum(1 for d in direction_agreement if d["agrees"])

    # ── Agreement by category ──────────────────────────────────────────────────
    by_category: dict[str, dict[str, Any]] = {}
    for label in ("kg_wins_strong", "kg_wins_moderate", "tie", "kg_loses"):
        prs_in = [p for p in study_prs if EXPECTED_LABEL.get(p) == label]
        means  = [per_pr[p]["mean_pref_kg"] for p in prs_in]
        by_category[label] = {
            "pr_ids":   prs_in,
            "n_prs":    len(prs_in),
            "mean_pref_kg": round(_mean(means), 3) if means else None,
        }

    # ── Krippendorff's α (inter-rater reliability) ────────────────────────────
    ratings_matrix: dict[str, dict[int, int | None]] = {
        r: {row["pr_id"]: row["pref_kg"] for row in responses if row["rater_id"] == r}
        for r in raters
    }
    alpha = krippendorff_alpha_ordinal(ratings_matrix)

    # ── Rater quality flags ────────────────────────────────────────────────────
    rater_stats: dict[str, dict[str, Any]] = {}
    for r in raters:
        rater_rows = [row for row in responses if row["rater_id"] == r]
        times = [row["time_spent_ms"] for row in rater_rows if row["time_spent_ms"]]
        rushed = [row["pr_id"] for row in rater_rows
                  if row["time_spent_ms"] and row["time_spent_ms"] < MIN_TIME_MS]
        why_lengths = [len(row["why"]) for row in rater_rows if row["why"]]
        demo = (demographics or {}).get(r, {})
        rater_stats[r] = {
            "n_prs":          len(rater_rows),
            "mean_time_ms":   round(_mean(times)) if times else None,
            "min_time_ms":    min(times) if times else None,
            "rushed_prs":     rushed,
            "flagged":        len(rushed) > 0,
            "mean_why_chars": round(_mean(why_lengths)) if why_lengths else None,
            "demographics":   demo,
        }

    # ── Difficulty stats ───────────────────────────────────────────────────────
    diffs_by_pr: dict[int, list[int]] = defaultdict(list)
    for r in responses:
        if r["difficulty"]:
            diffs_by_pr[r["pr_id"]].append(r["difficulty"])
    difficulty_per_pr = {
        pr: {"mean": round(_mean(v), 2), "n": len(v)}
        for pr, v in diffs_by_pr.items()
    }

    # ── GitHub clicks (proxy for diff engagement) ──────────────────────────────
    gh_by_pr: dict[int, list[int]] = defaultdict(list)
    for r in responses:
        gh_by_pr[r["pr_id"]].append(r["github_clicks"] or 0)
    gh_mean_by_pr = {pr: round(_mean(v), 2) for pr, v in gh_by_pr.items()}

    return {
        "meta": {
            "n_raters":         len(raters),
            "raters":           raters,
            "n_prs":            len(study_prs),
            "study_prs":        study_prs,
            "excluded_raters":  sorted(excluded_raters),
            "min_time_flag_ms": MIN_TIME_MS,
        },
        "core_result": {
            "kendall_tau_vs_llm_total":    tau_total,
            "p_value_tau_total":           p_total,
            "kendall_tau_vs_llm_kgrel":    tau_kgrel,
            "p_value_tau_kgrel":           p_kgrel,
            "direction_agreement_n":       n_agree,
            "direction_agreement_of":      len(study_prs),
            "direction_agreement_pct":     round(100 * n_agree / len(study_prs), 1) if study_prs else None,
            "krippendorff_alpha":          alpha,
            "note": (
                "tau > 0 means human preference ranking matches LLM ranking direction. "
                "direction_agreement counts PRs where sign(human_mean) == sign(llm_delta)."
            ),
        },
        "per_pr":               per_pr,
        "direction_agreement":  direction_agreement,
        "by_category":          by_category,
        "rater_stats":          rater_stats,
        "difficulty_per_pr":    difficulty_per_pr,
        "github_clicks_per_pr": gh_mean_by_pr,
    }


# ── Reporting ─────────────────────────────────────────────────────────────────

def print_report(result: dict[str, Any]) -> None:
    meta = result["meta"]
    core = result["core_result"]

    print("=" * 70)
    print("Human Study v4 — Agreement Analysis")
    print("=" * 70)
    print(f"Raters: {meta['n_raters']}  ({', '.join(meta['raters'])})")
    print(f"PRs:    {meta['n_prs']}  ({meta['study_prs']})")
    if meta["excluded_raters"]:
        print(f"Excluded: {', '.join(meta['excluded_raters'])}")

    print()
    print("─── Core result ───────────────────────────────────────────────────")
    tau_t = core["kendall_tau_vs_llm_total"]
    p_t   = core["p_value_tau_total"]
    tau_k = core["kendall_tau_vs_llm_kgrel"]
    p_k   = core["p_value_tau_kgrel"]
    print(f"Kendall τ (human pref vs LLM total delta):  {tau_t:+.3f}  p={p_t:.3f}")
    print(f"Kendall τ (human pref vs LLM kgrel delta):  {tau_k:+.3f}  p={p_k:.3f}")
    n_ag = core["direction_agreement_n"]
    of   = core["direction_agreement_of"]
    print(f"Direction agreement: {n_ag}/{of} PRs ({core['direction_agreement_pct']}%)")
    print(f"Krippendorff α (inter-rater, ordinal -2..+2): {core['krippendorff_alpha']}")

    print()
    print("─── Per-PR breakdown ──────────────────────────────────────────────")
    print(f"{'PR':>4}  {'expected':<20}  {'n':>3}  {'human_mean':>10}  {'llm_Δ':>6}  {'agree':>6}  {'%prefKG':>7}  {'%no_pref':>8}")
    for d in result["direction_agreement"]:
        pr   = d["pr_id"]
        pp   = result["per_pr"][pr]
        print(
            f"{pr:>4}  {d['expected']:<20}  {pp['n_raters']:>3}  "
            f"{pp['mean_pref_kg']:>+10.3f}  {d['llm_delta']:>+6d}  "
            f"{'✓' if d['agrees'] else '✗':>6}  "
            f"{pp['pct_prefer_kg']:>6.1f}%  {pp['pct_no_preference']:>7.1f}%"
        )

    print()
    print("─── By category ───────────────────────────────────────────────────")
    for label, info in result["by_category"].items():
        if not info["n_prs"]:
            continue
        m = info["mean_pref_kg"]
        direction = "→ prefers KG" if m and m > 0.2 else ("→ prefers baseline" if m and m < -0.2 else "→ no clear preference")
        print(f"  {label:<22}  mean_pref_kg={m:>+6.3f}  {direction}")

    print()
    print("─── Rater quality ─────────────────────────────────────────────────")
    for r, info in result["rater_stats"].items():
        demo = info.get("demographics") or {}
        demo_str = " | ".join(
            f"{k}={v}" for k, v in demo.items()
            if k in ("role", "exp_years", "freq_review_pr") and v
        )
        flag = "  ⚠ RUSHED" if info["flagged"] else ""
        print(
            f"  {r:<20}  n={info['n_prs']}  "
            f"mean_time={info['mean_time_ms'] and info['mean_time_ms']//1000 or '--'}s  "
            f"mean_why={info['mean_why_chars'] or '--'}chars{flag}"
        )
        if demo_str:
            print(f"    {demo_str}")

    print()
    print("─── Difficulty per PR ─────────────────────────────────────────────")
    for pr, info in sorted(result["difficulty_per_pr"].items()):
        print(f"  PR{pr:>2}  mean_difficulty={info['mean']:.2f}  (n={info['n']})")

    print()


# ── Synthetic sample (dry-run) ────────────────────────────────────────────────

def _write_sample_csv(path: Path) -> None:
    """Generate synthetic data that mimics realistic human responses."""
    import random
    rng = random.Random(42)

    path.parent.mkdir(parents=True, exist_ok=True)
    # 15 simulated raters, each rating all 6 study PRs
    rater_ids = [f"rater_{i:02d}" for i in range(1, 16)]
    header = [
        "received_at", "rater_id", "completed_at", "pr_id", "comparison",
        "mode_A", "mode_B", "preference_score", "why", "difficulty",
        "time_spent_ms", "github_clicks",
    ]

    # Realistic expected human scores: positive = prefer B (KG), direction from LLM deltas
    # With noise: strong wins are detected 80% of the time, weak 60%, ties 50%, losses 70%
    pr_signal = {31: +1.5, 20: -1.2, 47: +1.0, 23: -1.0, 22: +0.8, 27: 0.0}
    pr_noise  = {31: 0.6,  20: 0.7,  47: 0.8,  23: 0.9,  22: 0.9,  27: 1.0}

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for rater in rater_ids:
            # 50% chance mode_A=baseline (else KG) — random blinding
            flip_pr = {pr: rng.choice([True, False]) for pr in STUDY_PRS}
            for pr in STUDY_PRS:
                flip = flip_pr[pr]
                mode_a = "kg" if flip else "baseline"
                mode_b = "baseline" if flip else "kg"
                # Sample preference toward signal with noise
                signal = pr_signal[pr]
                noise = rng.gauss(0, pr_noise[pr])
                raw = signal + noise
                # Clip and round to -2..+2
                pref_kg = max(-2, min(2, round(raw)))
                # If flipped (A=KG), the raw pref score (A positive) is -pref_kg
                pref_score = -pref_kg if flip else pref_kg

                why_templates = [
                    "Review A named the specific file; Review B was more general.",
                    "Both reviews said similar things but B was slightly more concrete.",
                    "Review B identified the exact test missing; A was vague.",
                    "I couldn't tell a difference between them.",
                    "Review A gave more actionable recommendations with line numbers.",
                ]
                w.writerow([
                    "2026-05-31T10:00:00Z", rater, "2026-05-31T10:30:00Z",
                    pr, COMPARISON, mode_a, mode_b, pref_score,
                    rng.choice(why_templates),
                    rng.randint(2, 5),
                    rng.randint(90_000, 400_000),
                    rng.randint(0, 2),
                ])

    print(f"Wrote synthetic sample CSV ({len(rater_ids)} raters × {len(STUDY_PRS)} PRs) → {path}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="Human study v4 agreement analysis.")
    ap.add_argument("--human", help="responses CSV from Google Sheet")
    ap.add_argument("--demographics", help="demographics CSV (optional)")
    ap.add_argument("--exclude-rater", action="append", default=[],
                    help="Drop rater_id from analysis (repeatable)")
    ap.add_argument("--exclude-rushed", action="store_true",
                    help="Auto-exclude raters with any PR < 60s")
    ap.add_argument("--sample", action="store_true",
                    help="Generate synthetic data and analyse (dry-run)")
    ap.add_argument("--out", default=str(RESULTS_DIR / "human_study_v4_agreement.json"),
                    help="Output JSON path")
    ap.add_argument("--llm-checklist", default=None,
                    help="Override LLM checklist JSON path")
    args = ap.parse_args()

    llm_path = Path(args.llm_checklist) if args.llm_checklist else CHECKLIST_PATH
    if not llm_path.is_absolute():
        llm_path = REPO_ROOT / llm_path
    llm = load_llm_deltas(llm_path)

    if args.sample:
        sample_path = RESULTS_DIR / "SYNTHETIC_human_eval_v4_sample.csv"
        _write_sample_csv(sample_path)
        responses = load_responses(sample_path)
    else:
        if not args.human:
            ap.error("--human <csv> required (or --sample for dry-run)")
        p = Path(args.human)
        if not p.is_absolute():
            p = REPO_ROOT / p
        responses = load_responses(p)

    demo_path = Path(args.demographics) if args.demographics else None
    if demo_path and not demo_path.is_absolute():
        demo_path = REPO_ROOT / demo_path
    demographics = load_demographics(demo_path)

    excluded: set[str] = set(args.exclude_rater)

    result = analyze(responses, llm, demographics=demographics, excluded_raters=excluded)

    if args.exclude_rushed:
        rushed = {r for r, info in result["rater_stats"].items() if info["flagged"]}
        if rushed:
            print(f"Auto-excluding rushed raters: {rushed}")
            result = analyze(responses, llm, demographics=demographics,
                             excluded_raters=excluded | rushed)

    print_report(result)

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path

    # A --sample run analyses fabricated responses. Its output must never be
    # reachable under the filename a real run writes, and must announce itself
    # to anyone who opens it, because a previous version of this script wrote
    # synthetic results to results/human_study_v4_agreement.json.
    if args.sample:
        out_path = out_path.with_name("SYNTHETIC_" + out_path.name.removeprefix("SYNTHETIC_"))
        result["meta"]["SYNTHETIC"] = True
        result["meta"]["WARNING"] = (
            "FABRICATED DATA. Produced by --sample from _write_sample_csv(), not "
            "from human raters. Never cite, quote, or copy into the thesis."
        )
        print("\n" + "!" * 72)
        print("!! SYNTHETIC DRY-RUN. Every number above is fabricated. Do not cite. !!")
        print("!" * 72)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote JSON report → {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
