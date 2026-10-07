#!/usr/bin/env python3
"""
analyze_human_study_criteria.py — SUPERSEDED. DO NOT USE FOR THE v4 STUDY.

This analyser targets an earlier stimulus set: KG_ARM == "joern" and
STUDY_PRS == [44, 24, 31, 22, 47, 38]. The human study actually reported in the
thesis (v4) uses six Python pull requests from requests/flask/click, an AST
import resolver rather than Joern, and different PR ids. Pointed at v4 data this
script silently matches nothing or mislabels arms, so it is guarded at import
time and refuses to run without --i-know-this-is-superseded.

The analyser of record for every human-study number in the thesis is
    experiments/2026-07-06_user_study_prs/analyze_responses.py

Original purpose, retained for the record: analysis for the per-criterion +
overall human study (baseline_strict vs Joern-KG, the design from the 2026-06-19
supervisor meeting with C. Adriano).

The study UI (human_eval_v3/index.html) collects, per PR:
  • for each of 6 criteria, which review better addresses it:
        "A" | "B" | "both" | "neither"
  • one holistic overall preference: "A" | "equal" | "B"
  • a free-text reason, a 1-5 difficulty rating, time, and github clicks.

"A"/"B" are blind labels; mode_A / mode_B say which arm each was. This script
normalises every A/B vote to the ARM that received it (joern vs baseline_strict),
so positive numbers always mean "leans Joern-KG".

What it reports (all computable from human data alone):
  1. Per-criterion preference: how often raters judged Joern / baseline / both /
     neither better, the net lean, and % preferring Joern among decisive votes —
     overall and per PR.
  2. Overall holistic preference per PR (% Joern / equal / baseline, mean net).
  3. Inter-rater reliability: Krippendorff's α per criterion (nominal over
     {joern, baseline, both, neither}) and for the overall preference (ordinal
     over {-1, 0, +1}).
  4. Rater quality flags (rushed < 60 s), difficulty per PR, github clicks,
     demographic breakdown.

Human ↔ LLM-judge agreement (Chris's convergent-validity idea) is implemented
but OFF by default: the per-criterion judge scores for the exact baseline_strict
/joern reviews are not in the shipped checklist files (those score
baseline/kg/rag/hybrid), and the 6 rater criteria use ids F3*/F2*/T3/Q5/R1/C6
whose mapping to the 25-criterion rubric (esp. C6) needs sign-off. So agreement
runs only when you pass --llm-judge plus --kg-mode/--baseline-mode (mapping the
study arms to judge modes); otherwise it prints exactly what's missing. This is
deliberate — we don't guess the mapping.

Input: CSV exported from the Google Sheet `responses_criteria` tab written by
apps_script_webhook.gs. Required columns (read by name):
  rater_id, pr_id, mode_A, mode_B, F3*, F2*, T3, Q5, R1, C6,
  overall, why, difficulty, time_spent_ms, github_clicks, received_at, completed_at

Usage:
  python3 scripts/analyze_human_study_criteria.py --human responses_criteria.csv
  python3 scripts/analyze_human_study_criteria.py --sample          # synthetic dry-run
  python3 scripts/analyze_human_study_criteria.py --human r.csv \\
      --demographics demographics.csv --out results/human_study_criteria.json
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"

# ── Study design constants ──────────────────────────────────────────────────
CRITERIA_IDS = ["F3*", "F2*", "T3", "Q5", "R1", "C6"]
CRITERIA_LABEL = {
    "F3*": "names concrete components/APIs/patterns",
    "F2*": "describes concrete edge cases / error handling",
    "T3":  "references concrete test files / which tests",
    "Q5":  "gives a concrete reason per suggestion",
    "R1":  "comments on clarity / naming / organization",
    "C6":  "covers obvious issues without gaps",
}
KG_ARM = "joern"            # the treatment (strict prompt + Joern KG)
BASELINE_ARM = "baseline_strict"  # the control (strict prompt, no KG)
STUDY_PRS = [44, 24, 31, 22, 47, 38]
MIN_TIME_MS = 60_000        # < 1 min per PR → flag as rushed

# Per-PR judge scores for the EXACT reviews raters see (baseline_strict vs joern).
# These are the right convergent-validity reference (the shipped multi-judge
# checklist files score baseline/kg/rag/hybrid, not these strict reviews).
STRICT_EVAL_DIR = REPO_ROOT / "experiments" / "human_study_reviews"
# study criterion id -> judge rubric id (C6 has no rubric equivalent)
CRITERION_TO_JUDGE = {"F3*": "F3", "F2*": "F2", "T3": "T3", "Q5": "Q5", "R1": "R1", "C6": None}

VALID_CRIT = {"A", "B", "both", "neither"}
VALID_OVERALL = {"A", "equal", "B"}


# ── Normalisation: blind A/B → arm name ─────────────────────────────────────
def vote_to_arm(value: str, mode_a: str, mode_b: str) -> str | None:
    """Map a blind vote to the arm that received it (or 'both'/'neither')."""
    if value == "A":
        return mode_a
    if value == "B":
        return mode_b
    if value in ("both", "neither"):
        return value
    return None


def overall_to_signed(value: str, mode_a: str, mode_b: str) -> int | None:
    """Overall preference → +1 leans Joern, -1 leans baseline, 0 equal."""
    if value == "equal":
        return 0
    arm = vote_to_arm(value, mode_a, mode_b)
    if arm == KG_ARM:
        return 1
    if arm == BASELINE_ARM:
        return -1
    return None


# ── Data loading ────────────────────────────────────────────────────────────
def load_responses(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        sys.exit(f"Human responses file not found: {path}")
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = {h.lower().strip(): h for h in (reader.fieldnames or [])}

        def col(row: dict, name: str, default: str = "") -> str:
            h = headers.get(name.lower())
            if h and row.get(h) not in (None, ""):
                return str(row[h]).strip()
            return default

        for row in reader:
            try:
                pr_id = int(col(row, "pr_id"))
            except ValueError:
                continue
            mode_a = (col(row, "mode_A") or BASELINE_ARM).strip()
            mode_b = (col(row, "mode_B") or KG_ARM).strip()

            criteria = {}
            for cid in CRITERIA_IDS:
                v = col(row, cid)
                criteria[cid] = v if v in VALID_CRIT else None

            overall_raw = col(row, "overall")
            overall_raw = overall_raw if overall_raw in VALID_OVERALL else None

            def _int(name: str) -> int | None:
                try:
                    return int(col(row, name)) if col(row, name) else None
                except ValueError:
                    return None

            rows.append({
                "rater_id":      col(row, "rater_id"),
                "pr_id":         pr_id,
                "mode_A":        mode_a,
                "mode_B":        mode_b,
                "criteria":      criteria,
                "overall_raw":   overall_raw,
                "overall_signed": overall_to_signed(overall_raw, mode_a, mode_b) if overall_raw else None,
                "why":           col(row, "why"),
                "difficulty":    _int("difficulty"),
                "time_spent_ms": _int("time_spent_ms"),
                "github_clicks": _int("github_clicks") or 0,
                "received_at":   col(row, "received_at"),
                "completed_at":  col(row, "completed_at"),
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
        for row in csv.DictReader(f):
            rid = (row.get("rater_id") or "").strip()
            if rid:
                out[rid] = {k.strip(): (v or "").strip() for k, v in row.items() if k}
    return out


# ── Statistics ────────────────────────────────────────────────────────────────
def krippendorff_alpha(ratings_by_unit: dict[Any, list], metric: str = "nominal") -> float:
    """Krippendorff's α (standard coincidence formulation).

    ratings_by_unit: {unit: [coder values]} (None dropped). metric: 'nominal'
    (0/1 distance) or 'ordinal' (squared difference). Returns α ∈ [-1, 1]
    (1 = perfect, 0 = chance, < 0 = worse than chance).
    """
    def d(a, b) -> float:
        if metric == "nominal":
            return 0.0 if a == b else 1.0
        return float((a - b) ** 2)

    units = {u: [v for v in vs if v is not None] for u, vs in ratings_by_unit.items()}
    units = {u: vs for u, vs in units.items() if len(vs) >= 2}
    if not units:
        return float("nan")

    n = sum(len(vs) for vs in units.values())   # total pairable values
    # Observed disagreement: ordered within-unit pairs, weighted 1/(m_u - 1).
    D_o = 0.0
    for vs in units.values():
        m = len(vs)
        for a, b in itertools.permutations(vs, 2):
            D_o += d(a, b) / (m - 1)
    D_o /= n

    # Expected disagreement: all ordered pairs drawn from the global marginals.
    counts: dict[Any, int] = defaultdict(int)
    for vs in units.values():
        for v in vs:
            counts[v] += 1
    if n < 2:
        return float("nan")
    D_e = 0.0
    for v1, c1 in counts.items():
        for v2, c2 in counts.items():
            D_e += c1 * c2 * d(v1, v2)
    D_e /= n * (n - 1)
    if D_e == 0:
        return 1.0
    return round(1 - D_o / D_e, 4)


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def _ranks(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1  # 1-based average rank for ties
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(x: list[float], y: list[float]) -> float:
    n = len(x)
    if n < 2:
        return float("nan")
    mx, my = _mean(x), _mean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    dx = math.sqrt(sum((a - mx) ** 2 for a in x))
    dy = math.sqrt(sum((b - my) ** 2 for b in y))
    return num / (dx * dy) if dx > 0 and dy > 0 else float("nan")


def spearman(x: list[float], y: list[float]) -> float:
    if len(x) < 2:
        return float("nan")
    return round(_pearson(_ranks(x), _ranks(y)), 4)


def kendall_tau_b(x: list[float], y: list[float]) -> float:
    n = len(x)
    if n < 2:
        return float("nan")
    c = d = tx = ty = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx, dy = x[i] - x[j], y[i] - y[j]
            p = dx * dy
            if p > 0:
                c += 1
            elif p < 0:
                d += 1
            else:
                if dx == 0:
                    tx += 1
                if dy == 0:
                    ty += 1
    denom = math.sqrt((c + d + tx) * (c + d + ty))
    return round((c - d) / denom, 4) if denom > 0 else float("nan")


def load_strict_judge(prs: list[int], eval_dir: Path = STRICT_EVAL_DIR) -> dict[int, dict[str, Any]]:
    """Per-PR judge scores for the baseline_strict and joern reviews raters see."""
    out: dict[int, dict[str, Any]] = {}
    for pr in prs:
        bp = eval_dir / f"pr{pr}_baseline_strict_eval.json"
        jp = eval_dir / f"pr{pr}_joern_eval.json"
        if not (bp.exists() and jp.exists()):
            continue
        b, j = json.loads(bp.read_text()), json.loads(jp.read_text())
        bc = {c["criterion_id"]: c["score"] for c in b.get("criteria_scores", [])}
        jc = {c["criterion_id"]: c["score"] for c in j.get("criteria_scores", [])}
        out[pr] = {
            "delta_total": j["total_score"] - b["total_score"],
            "delta_kgrel": j["kg_relevant_score"] - b["kg_relevant_score"],
            "per_criterion_delta": {
                cid: (jc.get(jid, 0) - bc.get(jid, 0))
                for cid, jid in CRITERION_TO_JUDGE.items() if jid
            },
        }
    return out


def compute_convergent_validity(result: dict, judge: dict[int, dict[str, Any]]) -> dict[str, Any]:
    """Human↔judge agreement at the level that has signal (whole-review delta),
    plus a per-criterion 'does the judge even differentiate?' diagnostic."""
    prs = [p for p in result["overall_per_pr"] if p in judge]
    human = [result["overall_per_pr"][p]["mean_signed"] for p in prs]
    jt = [judge[p]["delta_total"] for p in prs]
    jk = [judge[p]["delta_kgrel"] for p in prs]

    # Per-criterion: how many of the PRs does the judge actually differentiate
    # joern vs baseline on? (If mostly 0, per-criterion agreement is not viable.)
    per_crit_signal = {}
    for cid in CRITERIA_IDS:
        if not CRITERION_TO_JUDGE.get(cid):
            per_crit_signal[cid] = {"judge_differentiates_prs": None, "note": "no rubric equivalent"}
            continue
        n_nonzero = sum(1 for p in prs if judge[p]["per_criterion_delta"].get(cid, 0) != 0)
        per_crit_signal[cid] = {"judge_differentiates_prs": n_nonzero, "of": len(prs)}

    return {
        "n_prs": len(prs),
        "level_with_signal": {
            "spearman_human_vs_judge_total": spearman(human, jt),
            "kendall_human_vs_judge_total": kendall_tau_b(human, jt),
            "spearman_human_vs_judge_kgrel": spearman(human, jk),
            "kendall_human_vs_judge_kgrel": kendall_tau_b(human, jk),
            "note": "human = mean overall preference per PR (+=joern); judge = total/kgrel "
                    "score delta (joern - baseline_strict). n=6 → pilot-level correlation.",
        },
        "per_criterion_judge_signal": per_crit_signal,
        "per_criterion_note": "Where 'judge_differentiates_prs' is ~0, the binary rubric scores "
                              "both reviews equal on that criterion, so a per-criterion human↔judge "
                              "agreement is not computable — report human per-criterion data as "
                              "descriptive (humans can detect richness the binary rubric scores as tie).",
    }


# ── Core analysis ─────────────────────────────────────────────────────────────
def analyze(
    responses: list[dict[str, Any]],
    demographics: dict[str, dict[str, str]] | None = None,
    excluded_raters: set[str] | None = None,
) -> dict[str, Any]:
    excluded_raters = excluded_raters or set()
    responses = [r for r in responses if r["rater_id"] not in excluded_raters]
    raters = sorted({r["rater_id"] for r in responses})
    pr_ids = sorted({r["pr_id"] for r in responses})

    def arm_counts(votes: list[str]) -> dict[str, int]:
        c = {KG_ARM: 0, BASELINE_ARM: 0, "both": 0, "neither": 0}
        for v in votes:
            if v in c:
                c[v] += 1
        return c

    def summarise(counts: dict[str, int]) -> dict[str, Any]:
        decisive = counts[KG_ARM] + counts[BASELINE_ARM]
        n = sum(counts.values())
        return {
            "counts": counts,
            "n": n,
            "net_joern": counts[KG_ARM] - counts[BASELINE_ARM],
            "pct_prefer_joern_of_decisive": round(100 * counts[KG_ARM] / decisive, 1) if decisive else None,
            "pct_both": round(100 * counts["both"] / n, 1) if n else None,
            "pct_neither": round(100 * counts["neither"] / n, 1) if n else None,
        }

    # ── 1. Per-criterion preference (overall + per PR) ───────────────────────
    per_criterion: dict[str, Any] = {}
    for cid in CRITERIA_IDS:
        all_votes = [vote_to_arm(r["criteria"][cid], r["mode_A"], r["mode_B"])
                     for r in responses if r["criteria"].get(cid)]
        per_pr_breakdown = {}
        for pr in pr_ids:
            votes = [vote_to_arm(r["criteria"][cid], r["mode_A"], r["mode_B"])
                     for r in responses if r["pr_id"] == pr and r["criteria"].get(cid)]
            per_pr_breakdown[pr] = summarise(arm_counts(votes))
        per_criterion[cid] = {
            "label": CRITERIA_LABEL[cid],
            "overall": summarise(arm_counts(all_votes)),
            "per_pr": per_pr_breakdown,
        }

    # ── 2. Overall holistic preference per PR ────────────────────────────────
    overall_per_pr: dict[int, Any] = {}
    for pr in pr_ids:
        signed = [r["overall_signed"] for r in responses
                  if r["pr_id"] == pr and r["overall_signed"] is not None]
        n = len(signed)
        overall_per_pr[pr] = {
            "n": n,
            "mean_signed": round(_mean(signed), 3) if signed else None,
            "pct_prefer_joern": round(100 * sum(1 for s in signed if s > 0) / n, 1) if n else None,
            "pct_equal": round(100 * sum(1 for s in signed if s == 0) / n, 1) if n else None,
            "pct_prefer_baseline": round(100 * sum(1 for s in signed if s < 0) / n, 1) if n else None,
        }

    # ── 3. Inter-rater reliability ───────────────────────────────────────────
    alpha_per_criterion: dict[str, float] = {}
    for cid in CRITERIA_IDS:
        units = {
            pr: [vote_to_arm(r["criteria"][cid], r["mode_A"], r["mode_B"])
                 for r in responses if r["pr_id"] == pr and r["criteria"].get(cid)]
            for pr in pr_ids
        }
        alpha_per_criterion[cid] = krippendorff_alpha(units, metric="nominal")
    overall_units = {
        pr: [r["overall_signed"] for r in responses
             if r["pr_id"] == pr and r["overall_signed"] is not None]
        for pr in pr_ids
    }
    alpha_overall = krippendorff_alpha(overall_units, metric="ordinal")

    # ── 4. Rater quality / difficulty / engagement ───────────────────────────
    rater_stats: dict[str, Any] = {}
    for r_id in raters:
        rr = [row for row in responses if row["rater_id"] == r_id]
        times = [row["time_spent_ms"] for row in rr if row["time_spent_ms"]]
        rushed = [row["pr_id"] for row in rr if row["time_spent_ms"] and row["time_spent_ms"] < MIN_TIME_MS]
        whys = [len(row["why"]) for row in rr if row["why"]]
        rater_stats[r_id] = {
            "n_prs": len(rr),
            "mean_time_ms": round(_mean(times)) if times else None,
            "min_time_ms": min(times) if times else None,
            "rushed_prs": rushed,
            "flagged": len(rushed) > 0,
            "mean_why_chars": round(_mean(whys)) if whys else None,
            "demographics": (demographics or {}).get(r_id, {}),
        }

    diffs_by_pr: dict[int, list[int]] = defaultdict(list)
    gh_by_pr: dict[int, list[int]] = defaultdict(list)
    for r in responses:
        if r["difficulty"]:
            diffs_by_pr[r["pr_id"]].append(r["difficulty"])
        gh_by_pr[r["pr_id"]].append(r["github_clicks"] or 0)

    return {
        "meta": {
            "n_raters": len(raters),
            "raters": raters,
            "n_prs": len(pr_ids),
            "pr_ids": pr_ids,
            "kg_arm": KG_ARM,
            "baseline_arm": BASELINE_ARM,
            "excluded_raters": sorted(excluded_raters),
            "min_time_flag_ms": MIN_TIME_MS,
        },
        "per_criterion": per_criterion,
        "overall_per_pr": overall_per_pr,
        "reliability": {
            "krippendorff_alpha_per_criterion": alpha_per_criterion,
            "krippendorff_alpha_overall_ordinal": alpha_overall,
            "note": "α per criterion is nominal over {joern, baseline_strict, both, neither}; "
                    "overall is ordinal over {-1 baseline, 0 equal, +1 joern}.",
        },
        "difficulty_per_pr": {pr: {"mean": round(_mean(v), 2), "n": len(v)} for pr, v in diffs_by_pr.items()},
        "github_clicks_per_pr": {pr: round(_mean(v), 2) for pr, v in gh_by_pr.items()},
        "rater_stats": rater_stats,
    }


# ── Human ↔ LLM agreement (opt-in; needs explicit mode mapping) ──────────────
# Maps the 6 rater criteria to the 25-criterion judge rubric. C6 has no direct
# judge equivalent (the rubric's completeness criteria are C1/C2), so it is
# excluded from agreement until a mapping is agreed.
CRITERION_TO_JUDGE = {"F3*": "F3", "F2*": "F2", "T3": "T3", "Q5": "Q5", "R1": "R1", "C6": None}


def agreement_with_llm(result: dict, responses: list[dict], judge_path: Path,
                       kg_mode: str, baseline_mode: str) -> dict[str, Any]:
    data = json.loads(judge_path.read_text())
    evs = data.get("evaluations", [])
    modes_present = sorted({e.get("mode") for e in evs})
    if kg_mode not in modes_present or baseline_mode not in modes_present:
        return {"status": "skipped",
                "reason": f"judge file modes {modes_present} do not include "
                          f"kg_mode={kg_mode!r} / baseline_mode={baseline_mode!r}"}
    # per (pr, judge_criterion) score for each mode
    scores: dict[tuple[int, str], dict[str, int]] = {}
    for e in evs:
        if e.get("mode") not in (kg_mode, baseline_mode):
            continue
        for c in e.get("criteria_scores", []):
            scores.setdefault((int(e["pr_id"]), c["criterion_id"]), {})[e["mode"]] = c.get("score")

    rows = []
    agree = total = 0
    for cid in CRITERIA_IDS:
        jid = CRITERION_TO_JUDGE.get(cid)
        if not jid:
            continue
        for pr, pp in result["per_criterion"][cid]["per_pr"].items():
            net = pp["net_joern"]
            sc = scores.get((pr, jid))
            if sc is None or kg_mode not in sc or baseline_mode not in sc:
                continue
            llm_delta = (sc[kg_mode] or 0) - (sc[baseline_mode] or 0)
            h_sign = 1 if net > 0 else (-1 if net < 0 else 0)
            l_sign = 1 if llm_delta > 0 else (-1 if llm_delta < 0 else 0)
            ok = h_sign == l_sign
            agree += int(ok)
            total += 1
            rows.append({"pr_id": pr, "criterion": cid, "judge_criterion": jid,
                         "human_net_joern": net, "llm_delta": llm_delta,
                         "human_sign": h_sign, "llm_sign": l_sign, "agrees": ok})
    return {
        "status": "computed",
        "kg_mode": kg_mode, "baseline_mode": baseline_mode,
        "excluded_criteria": [c for c in CRITERIA_IDS if not CRITERION_TO_JUDGE.get(c)],
        "n_cells": total, "n_agree": agree,
        "pct_agree": round(100 * agree / total, 1) if total else None,
        "cells": rows,
    }


# ── Reporting ─────────────────────────────────────────────────────────────────
def print_report(result: dict[str, Any]) -> None:
    meta = result["meta"]
    print("=" * 74)
    print("Human Study (per-criterion + overall) — baseline_strict vs Joern-KG")
    print("=" * 74)
    print(f"Raters: {meta['n_raters']}  PRs: {meta['n_prs']} {meta['pr_ids']}")
    if meta["excluded_raters"]:
        print(f"Excluded: {', '.join(meta['excluded_raters'])}")
    print("(positive 'net' / 'signed' = leans Joern-KG)")

    def pct(v: Any) -> str:
        return f"{v:.0f}%" if v is not None else "--"

    print("\n─── Per-criterion preference (all PRs) ─────────────────────────────")
    print(f"{'crit':<5} {'description':<46} {'net':>4} {'%Joern*':>8} {'%both':>6} {'%neither':>8}")
    for cid in CRITERIA_IDS:
        o = result["per_criterion"][cid]["overall"]
        print(f"{cid:<5} {CRITERIA_LABEL[cid][:44]:<46} {o['net_joern']:>+4} "
              f"{pct(o['pct_prefer_joern_of_decisive']):>8} "
              f"{pct(o['pct_both']):>6} {pct(o['pct_neither']):>8}")
    print("  *%Joern = share of decisive (Joern-vs-baseline) votes that chose Joern")

    print("\n─── Overall preference per PR ──────────────────────────────────────")
    print(f"{'PR':>4} {'n':>3} {'mean':>6} {'%Joern':>7} {'%equal':>7} {'%base':>6}")
    for pr, o in sorted(result["overall_per_pr"].items()):
        ms = o["mean_signed"]
        mean_s = f"{ms:+.2f}" if ms is not None else "--"
        print(f"{pr:>4} {o['n']:>3} {mean_s:>6} "
              f"{pct(o['pct_prefer_joern']):>7} {pct(o['pct_equal']):>7} "
              f"{pct(o['pct_prefer_baseline']):>6}")

    print("\n─── Inter-rater reliability (Krippendorff α) ───────────────────────")
    for cid, a in result["reliability"]["krippendorff_alpha_per_criterion"].items():
        print(f"  {cid:<5} α = {a}")
    print(f"  overall (ordinal) α = {result['reliability']['krippendorff_alpha_overall_ordinal']}")

    print("\n─── Rater quality ──────────────────────────────────────────────────")
    for r, info in result["rater_stats"].items():
        flag = "  ⚠ RUSHED" if info["flagged"] else ""
        mt = info["mean_time_ms"]
        print(f"  {r:<18} n={info['n_prs']} mean_time={mt//1000 if mt else '--'}s "
              f"mean_why={info['mean_why_chars'] or '--'}c{flag}")

    print("\n─── Difficulty per PR ──────────────────────────────────────────────")
    for pr, info in sorted(result["difficulty_per_pr"].items()):
        print(f"  PR{pr:>2} mean={info['mean']:.2f} (n={info['n']})")

    if "convergent_validity" in result:
        cv = result["convergent_validity"]
        lv = cv["level_with_signal"]
        print("\n─── Convergent validity vs LLM judge (whole-review level) ───────────")
        print(f"  n PRs with judge scores: {cv['n_prs']}")
        print(f"  Spearman ρ  human pref vs judge Δtotal: {lv['spearman_human_vs_judge_total']}")
        print(f"  Kendall  τ  human pref vs judge Δtotal: {lv['kendall_human_vs_judge_total']}")
        print(f"  Spearman ρ  human pref vs judge Δkgrel: {lv['spearman_human_vs_judge_kgrel']}")
        print(f"  Kendall  τ  human pref vs judge Δkgrel: {lv['kendall_human_vs_judge_kgrel']}")
        print("  Per-criterion — PRs where the judge differentiates joern vs baseline:")
        for cid, s in cv["per_criterion_judge_signal"].items():
            d = s.get("judge_differentiates_prs")
            extra = "  (no rubric equivalent)" if d is None else f" / {s.get('of')} PRs"
            print(f"    {cid:<5} {('--' if d is None else d)}{extra}")
        print("  → criteria at ~0 are scored as ties by the rubric; treat human per-criterion")
        print("    data there as descriptive (humans catch richness the binary rubric misses).")

    if "agreement" in result:
        ag = result["agreement"]
        print("\n─── Human ↔ LLM-judge agreement ────────────────────────────────────")
        if ag.get("status") != "computed":
            print(f"  SKIPPED — {ag.get('reason')}")
            print("  To enable: provide a judge run on the baseline_strict/joern reviews and")
            print("  pass --llm-judge <file> --kg-mode <m> --baseline-mode <m>.")
        else:
            print(f"  modes: joern→{ag['kg_mode']}, baseline_strict→{ag['baseline_mode']}")
            print(f"  excluded criteria (no judge id): {ag['excluded_criteria']}")
            print(f"  agreement: {ag['n_agree']}/{ag['n_cells']} cells ({ag['pct_agree']}%)")
    print()


# ── Synthetic sample (dry-run) ────────────────────────────────────────────────
def _write_sample_csv(path: Path) -> None:
    import random
    rng = random.Random(42)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (["received_at", "rater_id", "completed_at", "pr_id", "comparison",
               "mode_A", "mode_B"] + CRITERIA_IDS +
              ["criteria_net", "overall", "why", "difficulty", "time_spent_ms", "github_clicks"])
    # Joern lean per criterion (richer structural context helps the concrete ones most)
    crit_lean = {"F3*": 0.6, "F2*": 0.4, "T3": 0.7, "Q5": 0.3, "R1": 0.0, "C6": 0.4}
    raters = [f"rater_{i:02d}" for i in range(1, 13)]

    def sample_crit(lean: float) -> str:
        x = rng.random()
        p_joern = 0.30 + 0.30 * lean
        p_base = 0.30 - 0.15 * lean
        p_both = 0.25
        if x < p_joern:   return "joern_vote"
        if x < p_joern + p_base: return "baseline_vote"
        if x < p_joern + p_base + p_both: return "both"
        return "neither"

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for rater in raters:
            for pr in STUDY_PRS:
                flip = rng.choice([True, False])
                mode_a = KG_ARM if flip else BASELINE_ARM
                mode_b = BASELINE_ARM if flip else KG_ARM

                def arm_to_blind(arm: str) -> str:
                    return "A" if arm == mode_a else "B"

                cells, net = [], 0
                for cid in CRITERIA_IDS:
                    s = sample_crit(crit_lean[cid])
                    if s == "joern_vote":
                        val = arm_to_blind(KG_ARM)
                    elif s == "baseline_vote":
                        val = arm_to_blind(BASELINE_ARM)
                    else:
                        val = s
                    cells.append(val)
                    if val == "A":
                        net += 1 if mode_a == KG_ARM else -1
                    elif val == "B":
                        net += 1 if mode_b == KG_ARM else -1
                ov_arm = KG_ARM if rng.random() < 0.55 else (BASELINE_ARM if rng.random() < 0.6 else None)
                overall = "equal" if ov_arm is None else arm_to_blind(ov_arm)
                w.writerow(["2026-06-30T10:00:00Z", rater, "2026-06-30T10:30:00Z",
                            pr, "bl_vs_joern", mode_a, mode_b] + cells +
                           [net, overall, "Review named the exact test file; the other was vague.",
                            rng.randint(2, 5), rng.randint(90_000, 400_000), rng.randint(0, 2)])
    print(f"Wrote synthetic sample CSV ({len(raters)} raters × {len(STUDY_PRS)} PRs) → {path}")


# ── CLI ───────────────────────────────────────────────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser(description="Per-criterion + overall human study analysis.")
    ap.add_argument("--human", help="responses_criteria CSV from the Google Sheet")
    ap.add_argument("--demographics", help="demographics CSV (optional)")
    ap.add_argument("--exclude-rater", action="append", default=[])
    ap.add_argument("--exclude-rushed", action="store_true")
    ap.add_argument("--sample", action="store_true", help="synthetic dry-run")
    ap.add_argument("--out", default=str(RESULTS_DIR / "human_study_criteria.json"))
    ap.add_argument("--llm-judge", help="judge checklist JSON for agreement (opt-in)")
    ap.add_argument("--kg-mode", help="judge mode name corresponding to Joern arm")
    ap.add_argument("--baseline-mode", help="judge mode name corresponding to baseline_strict arm")
    ap.add_argument("--i-know-this-is-superseded", action="store_true",
                    help="Required. This analyser targets the old joern/[44,24,31,22,47,38] "
                         "stimuli, not the v4 study reported in the thesis.")
    args = ap.parse_args()

    if not args.i_know_this_is_superseded:
        ap.error(
            "SUPERSEDED ANALYSER.\n"
            f"  This script assumes KG_ARM={KG_ARM!r} and STUDY_PRS={STUDY_PRS}.\n"
            "  The human study reported in the thesis (v4) uses six Python PRs from\n"
            "  requests/flask/click with an AST import resolver, not Joern, and\n"
            "  different PR ids. Pointed at v4 data this script matches nothing or\n"
            "  mislabels arms.\n\n"
            "  Use instead:\n"
            "    python3 experiments/2026-07-06_user_study_prs/analyze_responses.py\n\n"
            "  If you genuinely want the old analysis, pass --i-know-this-is-superseded."
        )

    if args.sample:
        sample_path = RESULTS_DIR / "human_study_criteria_sample.csv"
        _write_sample_csv(sample_path)
        responses = load_responses(sample_path)
    else:
        if not args.human:
            ap.error("--human <csv> required (or --sample for dry-run)")
        p = Path(args.human)
        responses = load_responses(p if p.is_absolute() else REPO_ROOT / p)

    demo_path = Path(args.demographics) if args.demographics else None
    if demo_path and not demo_path.is_absolute():
        demo_path = REPO_ROOT / demo_path
    demographics = load_demographics(demo_path)

    excluded: set[str] = set(args.exclude_rater)
    result = analyze(responses, demographics=demographics, excluded_raters=excluded)
    if args.exclude_rushed:
        rushed = {r for r, info in result["rater_stats"].items() if info["flagged"]}
        if rushed:
            print(f"Auto-excluding rushed raters: {rushed}")
            result = analyze(responses, demographics=demographics, excluded_raters=excluded | rushed)

    # Convergent validity at the whole-review level (default reference = the
    # strict joern/baseline eval files for the exact reviews raters see).
    strict_judge = load_strict_judge(result["meta"]["pr_ids"])
    if strict_judge:
        result["convergent_validity"] = compute_convergent_validity(result, strict_judge)

    # Optional agreement
    if args.llm_judge:
        jp = Path(args.llm_judge)
        jp = jp if jp.is_absolute() else REPO_ROOT / jp
        if not (args.kg_mode and args.baseline_mode):
            result["agreement"] = {"status": "skipped",
                                   "reason": "pass --kg-mode and --baseline-mode to map study arms to judge modes"}
        elif not jp.exists():
            result["agreement"] = {"status": "skipped", "reason": f"judge file not found: {jp}"}
        else:
            result["agreement"] = agreement_with_llm(result, responses, jp, args.kg_mode, args.baseline_mode)

    print_report(result)

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote JSON report → {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
