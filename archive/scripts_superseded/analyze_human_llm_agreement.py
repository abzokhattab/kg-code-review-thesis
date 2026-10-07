#!/usr/bin/env python3
"""
Human ↔ LLM agreement analysis for the thesis human study.

Reads raw human-rater data exported from the Google Sheet (one row per
(rater, pr_id, blind_label) task), unblinds to `mode`, and computes
per-criterion Cohen's κ against the multi-judge LLM majority vote. Also
reports inter-rater agreement (κ) when more than one human rater is
present, flags high-disagreement cells for qualitative inspection, and
summarises the overall-preference comparison (human A/B/Both vs. the
mode-level LLM verdict).

Design notes
------------
* Criterion mapping. The human study uses a 6-criterion rubric:
    F3*, F2*, T3, Q5, R1, C6.
  The LLM checklist evaluation (`results/checklist_evaluation_llm.json`)
  covers 25 criteria; C6 has its own multi-judge file
  (`results/c6_completeness_llm.json`). The mapping from human criterion
  IDs to LLM sources is:
    F3*  → LLM `F3`   (note: F3* is a tightened version; expect LLM to
                       be somewhat more lenient)
    F2*  → LLM `F2`
    T3   → LLM `T3`
    Q5   → LLM `Q5`
    R1   → LLM `R1`
    C6   → results/c6_completeness_llm.json (multi-judge)
  This asymmetry is reported explicitly.
* Aggregation. The LLM side uses the 3-judge majority vote (ties → 0)
  already written to disk.
* No human data yet? The script accepts --sample to run on a synthetic
  CSV produced by _write_sample_csv().
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"
CHECKLIST_PATH = RESULTS_DIR / "checklist_evaluation_llm.json"
C6_PATH = RESULTS_DIR / "c6_completeness_llm.json"

HUMAN_TO_LLM_CRITERION = {
    "F3*": "F3",
    "F2*": "F2",
    "T3":  "T3",
    "Q5":  "Q5",
    "R1":  "R1",
    "C6":  "C6",   # served from c6_completeness_llm.json
}
TIGHTENED = {"F3*", "F2*"}  # human criterion is stricter than LLM's


# ---------------------------------------------------------------------------
# LLM-side loading
# ---------------------------------------------------------------------------


def load_llm_scores(checklist_path: Path | None = None) -> dict[tuple[int, str, str], int]:
    """Return {(pr_id, mode, llm_criterion_id): 0|1} from the checklist file.

    The default file (`results/checklist_evaluation_llm.json`) is the v1
    single-judge canonical run. For the human_eval_v3 study (which uses
    the cleaned dataset_v2 reviews), point this at the v2 multi-judge
    output `results/checklist_evaluation_llm_multi__v2.json` so the
    human↔LLM comparison is on the same review set both sides actually
    saw.
    """
    path = checklist_path or CHECKLIST_PATH
    if not path.exists():
        sys.exit(f"Missing {path}. Run scripts/evaluate_reviews.py first.")
    with path.open() as f:
        data = json.load(f)
    out: dict[tuple[int, str, str], int] = {}
    for ev in data["evaluations"]:
        for cs in ev["criteria_scores"]:
            cid = cs["criterion_id"]
            s = cs.get("score")
            if s in (0, 1):
                out[(int(ev["pr_id"]), ev["mode"], cid)] = int(s)
    return out


def load_llm_c6() -> dict[tuple[int, str, str], int]:
    """Return {(pr_id, mode, 'C6'): 0|1} from the C6 multi-judge file."""
    if not C6_PATH.exists():
        return {}
    with C6_PATH.open() as f:
        data = json.load(f)
    out: dict[tuple[int, str, str], int] = {}
    for s in data.get("scores", []):
        if s.get("score") in (0, 1):
            out[(int(s["pr_id"]), s["mode"], "C6")] = int(s["score"])
    return out


def llm_verdict(pr_id: int, mode: str, human_cid: str,
                checklist: dict[tuple[int, str, str], int],
                c6: dict[tuple[int, str, str], int]) -> int | None:
    if human_cid == "C6":
        return c6.get((pr_id, mode, "C6"))
    llm_cid = HUMAN_TO_LLM_CRITERION.get(human_cid)
    if not llm_cid:
        return None
    return checklist.get((pr_id, mode, llm_cid))


# ---------------------------------------------------------------------------
# Human-side loading
# ---------------------------------------------------------------------------


@dataclass
class HumanCell:
    rater_id: str
    pr_id: int
    mode: str                     # unblinded
    comparison: str
    blind_label: str              # A / B
    scores: dict[str, int]        # criterion_id → 0/1
    difficulty: int | None
    preference: str | None        # "A" / "B" / "Both"
    time_spent_ms: int | None
    notes: str
    github_clicks: int | None


def load_demographics_csv(path: Path) -> dict[str, dict[str, str]]:
    """Parse the `demographics` Sheet tab.

    Expected columns (case-insensitive): rater_id, role, exp_years,
    freq_review_pr, completed_at. Unknown columns are preserved.
    Returns {rater_id: {field: value}} (last write wins, since the UI
    re-emits demographics on every task submit).
    """
    out: dict[str, dict[str, str]] = {}
    if not path.exists():
        return out
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rid = (row.get("rater_id") or row.get("Rater_id") or "").strip()
            if not rid:
                continue
            out[rid] = {k: (v or "").strip() for k, v in row.items() if k}
    return out


def load_quality_flags_csv(path: Path) -> dict[str, list[str]]:
    """Parse the `quality_flags` tab. Expected columns: rater_id,
    quality_flags (comma-separated or JSON list), completed_at."""
    out: dict[str, list[str]] = {}
    if not path.exists():
        return out
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rid = (row.get("rater_id") or "").strip()
            if not rid:
                continue
            raw = (row.get("quality_flags") or "").strip()
            flags: list[str] = []
            if raw.startswith("["):
                try:
                    flags = [str(x) for x in json.loads(raw)]
                except Exception:
                    flags = [raw]
            elif raw:
                flags = [s.strip() for s in raw.split(",") if s.strip()]
            out[rid] = flags
    return out


def load_feedback_csv(path: Path) -> dict[str, str]:
    """Parse the `feedback` tab. Expected columns: rater_id, feedback,
    completed_at."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rid = (row.get("rater_id") or "").strip()
            if not rid:
                continue
            txt = (row.get("feedback") or "").strip()
            if txt:
                out[rid] = txt
    return out


def load_human_csv(path: Path) -> list[HumanCell]:
    """Parse the Google-Sheet-exported CSV.

    Expected columns (case-insensitive, order-agnostic):
      rater_id, pr_id, comparison, blind_label, mode,
      F3*, F2*, T3, Q5, R1, C6,        (or a JSON `scores` column)
      difficulty, preference, time_spent_ms, notes, github_clicks

    Missing criterion cells are treated as "not answered" (dropped from
    agreement math); they are NOT treated as 0.
    """
    if not path.exists():
        sys.exit(f"Human data file not found: {path}")

    cells: list[HumanCell] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Build a case-insensitive column lookup
        headers_lc = {h.lower(): h for h in (reader.fieldnames or [])}

        def col(row: dict[str, str], *names: str, default: str = "") -> str:
            for n in names:
                h = headers_lc.get(n.lower())
                if h is not None and row.get(h) not in (None, ""):
                    return row[h]
            return default

        for row in reader:
            try:
                pr_id = int(col(row, "pr_id"))
            except Exception:
                continue
            mode = col(row, "mode").strip().lower()
            if not mode:
                continue
            scores: dict[str, int] = {}
            # Two possible shapes: per-criterion columns, or a JSON blob
            blob = col(row, "scores")
            if blob:
                try:
                    obj = json.loads(blob)
                    for k, v in obj.items():
                        if v in (0, 1, "0", "1", True, False):
                            scores[k] = int(v)
                except Exception:
                    pass
            for hc in HUMAN_TO_LLM_CRITERION:
                v = col(row, hc)
                if v in ("0", "1"):
                    scores[hc] = int(v)
                elif v.lower() in ("y", "yes", "true"):
                    scores[hc] = 1
                elif v.lower() in ("n", "no", "false"):
                    scores[hc] = 0

            try:
                diff = int(col(row, "difficulty")) if col(row, "difficulty") else None
            except Exception:
                diff = None
            try:
                t_ms = int(col(row, "time_spent_ms")) if col(row, "time_spent_ms") else None
            except Exception:
                t_ms = None
            try:
                gh = int(col(row, "github_clicks")) if col(row, "github_clicks") else None
            except Exception:
                gh = None

            cells.append(HumanCell(
                rater_id=col(row, "rater_id"),
                pr_id=pr_id,
                mode=mode,
                comparison=col(row, "comparison"),
                blind_label=col(row, "blind_label").upper(),
                scores=scores,
                difficulty=diff,
                preference=(col(row, "preference") or None),
                time_spent_ms=t_ms,
                notes=col(row, "notes"),
                github_clicks=gh,
            ))
    return cells


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def cohen_kappa(pairs: Iterable[tuple[int, int]]) -> tuple[float, int, float]:
    """Return (kappa, n, raw_agreement_pct) for a list of (rater_a, rater_b) 0/1 pairs."""
    pairs = [(a, b) for (a, b) in pairs if a in (0, 1) and b in (0, 1)]
    n = len(pairs)
    if n == 0:
        return float("nan"), 0, float("nan")
    agreed = sum(1 for a, b in pairs if a == b)
    p_o = agreed / n
    p_a_yes = sum(1 for a, _ in pairs if a == 1) / n
    p_b_yes = sum(1 for _, b in pairs if b == 1) / n
    p_e = p_a_yes * p_b_yes + (1 - p_a_yes) * (1 - p_b_yes)
    kappa = (p_o - p_e) / (1 - p_e) if p_e < 1 else 1.0
    return kappa, n, 100.0 * p_o


def interpret_kappa(k: float) -> str:
    """Landis & Koch (1977)."""
    if k != k:  # NaN
        return "N/A"
    if k < 0:
        return "poor"
    if k < 0.21:
        return "slight"
    if k < 0.41:
        return "fair"
    if k < 0.61:
        return "moderate"
    if k < 0.81:
        return "substantial"
    return "almost perfect"


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


def analyze(cells: list[HumanCell],
            checklist: dict[tuple[int, str, str], int],
            c6: dict[tuple[int, str, str], int],
            demographics: dict[str, dict[str, str]] | None = None,
            quality_flags: dict[str, list[str]] | None = None,
            feedback: dict[str, str] | None = None,
            excluded_raters: set[str] | None = None) -> dict[str, Any]:

    excluded_raters = excluded_raters or set()
    if excluded_raters:
        cells = [c for c in cells if c.rater_id not in excluded_raters]

    raters = sorted({c.rater_id for c in cells})
    modes = sorted({c.mode for c in cells})
    criteria = list(HUMAN_TO_LLM_CRITERION.keys())

    # ---- Human vs LLM: per-criterion ----
    per_criterion: dict[str, Any] = {}
    unmatched: list[str] = []  # criteria with no LLM source

    for cid in criteria:
        pairs: list[tuple[int, int]] = []
        pairs_by_rater: dict[str, list[tuple[int, int]]] = defaultdict(list)
        pairs_by_mode: dict[str, list[tuple[int, int]]] = defaultdict(list)
        flips: list[dict[str, Any]] = []

        for c in cells:
            h = c.scores.get(cid)
            if h not in (0, 1):
                continue
            llm = llm_verdict(c.pr_id, c.mode, cid, checklist, c6)
            if llm not in (0, 1):
                unmatched.append(f"{cid}@PR#{c.pr_id}/{c.mode}")
                continue
            pairs.append((h, llm))
            pairs_by_rater[c.rater_id].append((h, llm))
            pairs_by_mode[c.mode].append((h, llm))
            if h != llm:
                flips.append({
                    "rater_id": c.rater_id,
                    "pr_id": c.pr_id,
                    "mode": c.mode,
                    "human": h,
                    "llm": llm,
                    "notes": c.notes,
                })

        k, n, pct = cohen_kappa(pairs)
        per_criterion[cid] = {
            "llm_source": HUMAN_TO_LLM_CRITERION[cid],
            "tightened_on_human_side": cid in TIGHTENED,
            "n": n,
            "agreement_pct": round(pct, 1) if n else None,
            "cohen_kappa": round(k, 3) if n else None,
            "interpretation": interpret_kappa(k) if n else "N/A",
            "by_rater": {
                r: {
                    "n": len(p),
                    "agreement_pct": round(cohen_kappa(p)[2], 1) if p else None,
                    "kappa": round(cohen_kappa(p)[0], 3) if p else None,
                }
                for r, p in pairs_by_rater.items()
            },
            "by_mode": {
                m: {
                    "n": len(p),
                    "agreement_pct": round(cohen_kappa(p)[2], 1) if p else None,
                    "kappa": round(cohen_kappa(p)[0], 3) if p else None,
                    "human_yes_rate_pct": round(100.0 * sum(a for a, _ in p) / len(p), 1) if p else None,
                    "llm_yes_rate_pct": round(100.0 * sum(b for _, b in p) / len(p), 1) if p else None,
                }
                for m, p in pairs_by_mode.items()
            },
            "flips": flips,
        }

    # ---- Overall human vs LLM across all criteria ----
    all_pairs: list[tuple[int, int]] = []
    for info in per_criterion.values():
        for r, meta in info["by_rater"].items():
            pass
    for c in cells:
        for cid, h in c.scores.items():
            if h not in (0, 1):
                continue
            llm = llm_verdict(c.pr_id, c.mode, cid, checklist, c6)
            if llm in (0, 1):
                all_pairs.append((h, llm))
    k, n, pct = cohen_kappa(all_pairs)
    overall = {
        "n": n,
        "agreement_pct": round(pct, 1) if n else None,
        "cohen_kappa": round(k, 3) if n else None,
        "interpretation": interpret_kappa(k) if n else "N/A",
    }

    # ---- Inter-rater agreement (per criterion) ----
    inter_rater: dict[str, Any] = {}
    if len(raters) >= 2:
        for cid in criteria:
            # Build {(pr_id, mode): {rater: score}}
            bucket: dict[tuple[int, str], dict[str, int]] = defaultdict(dict)
            for c in cells:
                h = c.scores.get(cid)
                if h in (0, 1):
                    bucket[(c.pr_id, c.mode)][c.rater_id] = h
            pairs_per: dict[str, list[tuple[int, int]]] = defaultdict(list)
            for _, rs in bucket.items():
                rids = sorted(rs.keys())
                for i in range(len(rids)):
                    for j in range(i + 1, len(rids)):
                        pair_key = f"{rids[i]} vs {rids[j]}"
                        pairs_per[pair_key].append((rs[rids[i]], rs[rids[j]]))
            inter_rater[cid] = {
                pk: {
                    "n": len(p),
                    "agreement_pct": round(cohen_kappa(p)[2], 1) if p else None,
                    "kappa": round(cohen_kappa(p)[0], 3) if p else None,
                }
                for pk, p in pairs_per.items()
            }

    # ---- Preference analysis ----
    # For each (rater, pr_id, comparison) we should have two rows (A, B) with
    # one preference value. Use the first row to read the preference.
    # NOTE: the UI emits "A"/"B"/"both" (lowercase). Normalise here so that
    # "both" / "Both" / "BOTH" all bucket to the same canonical key.
    def _canon_pref(raw: str | None) -> str | None:
        if not raw:
            return None
        s = raw.strip()
        if not s:
            return None
        sl = s.lower()
        if sl == "a":
            return "A"
        if sl == "b":
            return "B"
        if sl == "both":
            return "Both"
        return None  # unrecognised → counted as "none"

    preference: dict[str, Any] = {"by_comparison": {}, "total": {"A": 0, "B": 0, "Both": 0, "none": 0}}
    seen: set[tuple[str, int, str]] = set()
    for c in cells:
        key = (c.rater_id, c.pr_id, c.comparison)
        if key in seen or not c.preference:
            continue
        seen.add(key)
        p = _canon_pref(c.preference)
        comp = c.comparison or "unknown"
        preference["by_comparison"].setdefault(comp, {"A": 0, "B": 0, "Both": 0, "none": 0})
        if p in ("A", "B", "Both"):
            preference["by_comparison"][comp][p] += 1
            preference["total"][p] += 1
        else:
            preference["by_comparison"][comp]["none"] += 1
            preference["total"]["none"] += 1

    # ---- Difficulty & time descriptive stats (per-task, deduplicated) ----
    # Each task pair has duplicate (difficulty, time, github_clicks) on the
    # A and B rows. Read once per (rater, pr, comparison).
    diff_seen: set[tuple[str, int, str]] = set()
    diffs: list[int] = []
    times: list[int] = []
    gh_clicks: list[int] = []
    by_rater_time: dict[str, list[int]] = defaultdict(list)
    by_comparison_diff: dict[str, list[int]] = defaultdict(list)
    for c in cells:
        key = (c.rater_id, c.pr_id, c.comparison)
        if key in diff_seen:
            continue
        diff_seen.add(key)
        if isinstance(c.difficulty, int) and 1 <= c.difficulty <= 5:
            diffs.append(c.difficulty)
            by_comparison_diff[c.comparison or "unknown"].append(c.difficulty)
        if isinstance(c.time_spent_ms, int) and c.time_spent_ms > 0:
            times.append(c.time_spent_ms)
            by_rater_time[c.rater_id].append(c.time_spent_ms)
        if isinstance(c.github_clicks, int) and c.github_clicks >= 0:
            gh_clicks.append(c.github_clicks)

    def _stats(xs: list[int | float]) -> dict[str, Any]:
        if not xs:
            return {"n": 0}
        ys = sorted(xs)
        n = len(ys)
        mean = sum(ys) / n
        median = ys[n // 2] if n % 2 else (ys[n // 2 - 1] + ys[n // 2]) / 2
        return {"n": n, "mean": round(mean, 2), "median": round(median, 2),
                "min": ys[0], "max": ys[-1]}

    descriptive = {
        "difficulty": _stats(diffs),
        "difficulty_by_comparison": {
            k: _stats(v) for k, v in by_comparison_diff.items()
        },
        "time_spent_ms": _stats(times),
        "time_spent_ms_by_rater": {
            r: _stats(v) for r, v in by_rater_time.items()
        },
        "github_clicks_per_task": _stats(gh_clicks),
    }

    # ---- Per-rater agreement summary (for quality auditing) ----
    by_rater_summary: dict[str, Any] = {}
    for r in raters:
        rater_pairs: list[tuple[int, int]] = []
        for c in cells:
            if c.rater_id != r:
                continue
            for cid, h in c.scores.items():
                if h not in (0, 1):
                    continue
                llm = llm_verdict(c.pr_id, c.mode, cid, checklist, c6)
                if llm in (0, 1):
                    rater_pairs.append((h, llm))
        k, n, pct = cohen_kappa(rater_pairs)
        by_rater_summary[r] = {
            "n_pairs": n,
            "agreement_pct": round(pct, 1) if n else None,
            "kappa_vs_llm": round(k, 3) if n else None,
            "interpretation": interpret_kappa(k) if n else "N/A",
            "demographics": (demographics or {}).get(r, {}),
            "quality_flags": (quality_flags or {}).get(r, []),
            "feedback": (feedback or {}).get(r, ""),
        }

    # ---- Slice agreement by demographic if available ----
    by_demographic: dict[str, Any] = {}
    if demographics:
        for field in ("role", "exp_years", "freq_review_pr"):
            buckets: dict[str, list[tuple[int, int]]] = defaultdict(list)
            for c in cells:
                demo = demographics.get(c.rater_id) or {}
                bucket = demo.get(field) or "unknown"
                for cid, h in c.scores.items():
                    if h not in (0, 1):
                        continue
                    llm = llm_verdict(c.pr_id, c.mode, cid, checklist, c6)
                    if llm in (0, 1):
                        buckets[bucket].append((h, llm))
            by_demographic[field] = {
                b: {
                    "n": len(p),
                    "agreement_pct": round(cohen_kappa(p)[2], 1) if p else None,
                    "kappa": round(cohen_kappa(p)[0], 3) if p else None,
                }
                for b, p in buckets.items()
            }

    return {
        "meta": {
            "n_cells": len(cells),
            "n_raters": len(raters),
            "raters": raters,
            "modes": modes,
            "unmatched_cells": len(unmatched),
            "excluded_raters": sorted(excluded_raters),
        },
        "overall_human_vs_llm": overall,
        "per_criterion": per_criterion,
        "inter_rater": inter_rater,
        "preference": preference,
        "descriptive": descriptive,
        "by_rater_summary": by_rater_summary,
        "by_demographic": by_demographic,
        "feedback": feedback or {},
        "quality_flags": quality_flags or {},
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_report(result: dict[str, Any]) -> None:
    meta = result["meta"]
    print("=" * 78)
    print("Human ↔ LLM agreement analysis")
    print("=" * 78)
    print(f"Cells (rater × PR × mode × criterion): {meta['n_cells']}")
    print(f"Raters: {meta['n_raters']}  {meta['raters']}")
    print(f"Modes: {meta['modes']}")
    if meta["unmatched_cells"]:
        print(f"⚠ Unmatched cells (no LLM source): {meta['unmatched_cells']}")

    o = result["overall_human_vs_llm"]
    if o["n"]:
        print(f"\nOverall (all criteria, all raters, all modes):")
        print(f"  n = {o['n']}  agreement = {o['agreement_pct']}%  κ = {o['cohen_kappa']}  ({o['interpretation']})")

    print("\n--- Per-criterion human ↔ LLM ---")
    print(f"{'crit':<5} {'n':>4} {'agree%':>7} {'κ':>6} {'interp':<14} {'human-strict?':<14} {'LLM src':<8}")
    for cid, info in result["per_criterion"].items():
        if not info["n"]:
            print(f"{cid:<5} {'—':>4} {'—':>7} {'—':>6} {'(no data)':<14}")
            continue
        tight = "stricter" if info["tightened_on_human_side"] else ""
        print(f"{cid:<5} {info['n']:>4} {info['agreement_pct']:>6.1f}% {info['cohen_kappa']:>6.2f} "
              f"{info['interpretation']:<14} {tight:<14} {info['llm_source']:<8}")

    # Most divergent cells
    print("\n--- Largest human↔LLM flips (first 10) ---")
    all_flips: list[dict[str, Any]] = []
    for cid, info in result["per_criterion"].items():
        for f in info["flips"]:
            all_flips.append({**f, "criterion": cid})
    for f in all_flips[:10]:
        print(f"  {f['criterion']:<4} PR#{f['pr_id']:<3} {f['mode']:<10} rater={f['rater_id']:<15} "
              f"H={f['human']} LLM={f['llm']}"
              + (f"  note: {f['notes'][:60]}" if f.get("notes") else ""))
    if len(all_flips) > 10:
        print(f"  … {len(all_flips) - 10} more flips — see JSON output")

    # Inter-rater (if any)
    if result["inter_rater"]:
        print("\n--- Inter-rater κ per criterion ---")
        for cid, pairs in result["inter_rater"].items():
            if not pairs:
                continue
            print(f"  {cid}:")
            for pk, info in pairs.items():
                if info["n"]:
                    print(f"    {pk:<40} n={info['n']:<3} agree={info['agreement_pct']}%  κ={info['kappa']}")

    # Preference
    pref = result["preference"]
    if pref["total"]:
        print("\n--- Overall preference distribution ---")
        for comp, dist in pref["by_comparison"].items():
            total = sum(dist.values())
            if not total:
                continue
            print(f"  {comp}: " + "  ".join(
                f"{k}={v} ({100*v/total:.0f}%)" for k, v in dist.items() if v
            ))

    # Descriptive task stats (difficulty, time, github clicks)
    desc = result.get("descriptive") or {}
    if desc:
        print("\n--- Task descriptive stats (deduplicated per task pair) ---")
        d = desc.get("difficulty") or {}
        if d.get("n"):
            print(f"  Difficulty (1-5): n={d['n']}  mean={d['mean']}  median={d['median']}  "
                  f"min={d['min']}  max={d['max']}")
        for comp, ds in (desc.get("difficulty_by_comparison") or {}).items():
            if ds.get("n"):
                print(f"    · {comp}: mean={ds['mean']} (n={ds['n']})")
        t = desc.get("time_spent_ms") or {}
        if t.get("n"):
            print(f"  Time/task (ms): n={t['n']}  mean={t['mean']:.0f}  median={t['median']:.0f}  "
                  f"min={t['min']}  max={t['max']}")
        for r, ts in (desc.get("time_spent_ms_by_rater") or {}).items():
            if ts.get("n"):
                print(f"    · {r}: median={ts['median']:.0f}ms over {ts['n']} tasks")
        gh = desc.get("github_clicks_per_task") or {}
        if gh.get("n"):
            print(f"  GitHub clicks/task: mean={gh['mean']}  median={gh['median']}  max={gh['max']}")

    # Per-rater quality summary
    brs = result.get("by_rater_summary") or {}
    if brs:
        print("\n--- Per-rater audit (κ vs LLM, demographics, flags) ---")
        for r, info in brs.items():
            demo = info.get("demographics") or {}
            demo_str = ", ".join(f"{k}={v}" for k, v in demo.items()
                                 if k in ("role", "exp_years", "freq_review_pr") and v)
            flags = info.get("quality_flags") or []
            flag_str = (" FLAGS=" + ",".join(flags)) if flags else ""
            print(f"  {r}: n={info.get('n_pairs', 0)}  κ={info.get('kappa_vs_llm')}  "
                  f"agree={info.get('agreement_pct')}%  ({info.get('interpretation')}){flag_str}")
            if demo_str:
                print(f"      demo: {demo_str}")
            fb = info.get("feedback") or ""
            if fb:
                print(f"      feedback: {fb[:120]}{'…' if len(fb) > 120 else ''}")

    # Demographic slices
    bd = result.get("by_demographic") or {}
    if bd:
        print("\n--- Human↔LLM agreement sliced by demographic ---")
        for field, buckets in bd.items():
            if not buckets:
                continue
            print(f"  {field}:")
            for b, info in buckets.items():
                if info["n"]:
                    print(f"    {b:<20} n={info['n']:<4} agree={info['agreement_pct']}%  κ={info['kappa']}")

    # Excluded raters
    ex = (result.get("meta") or {}).get("excluded_raters") or []
    if ex:
        print(f"\n--- Excluded raters: {', '.join(ex)} ---")

    print()


# ---------------------------------------------------------------------------
# Sample data (for dry-runs before real pilot data arrives)
# ---------------------------------------------------------------------------


def _write_sample_csv(path: Path, checklist, c6) -> None:
    """Produce a small synthetic CSV so the script can be dry-run."""
    import random
    rng = random.Random(42)

    path.parent.mkdir(parents=True, exist_ok=True)
    # 6 PRs × 2 comparisons × 2 rows (A, B) × 2 raters = 48 rows
    PRS = [10, 14, 15, 21, 22, 26]
    COMPS = [("bl_vs_kg", "baseline", "kg"), ("kg_vs_rag", "kg", "rag")]
    RATERS = ["christian", "abdu"]
    header = ["rater_id", "pr_id", "comparison", "blind_label", "mode",
              *HUMAN_TO_LLM_CRITERION.keys(),
              "difficulty", "preference", "time_spent_ms", "notes", "github_clicks"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for rater in RATERS:
            for pr in PRS:
                for comp_id, ma, mb in COMPS:
                    pref = rng.choice(["A", "B", "Both"])
                    diff = rng.randint(1, 5)
                    for label, mode in (("A", ma), ("B", mb)):
                        scores: list[str] = []
                        for cid in HUMAN_TO_LLM_CRITERION:
                            # 75% of the time, agree with the LLM; otherwise flip
                            llm = (llm_verdict(pr, mode, cid, checklist, c6))
                            if llm in (0, 1):
                                base = llm
                            else:
                                base = rng.choice([0, 1])
                            flip_bias = 0.3 if rater == "christian" else 0.25
                            v = base if rng.random() > flip_bias else (1 - base)
                            scores.append(str(v))
                        w.writerow([
                            rater, pr, comp_id, label, mode,
                            *scores,
                            diff, pref, rng.randint(20_000, 300_000),
                            "", rng.randint(0, 3),
                        ])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Human ↔ LLM agreement analysis for the human study.")
    parser.add_argument("--human", type=str, default=None,
                        help="CSV exported from the Google Sheet (one row per task).")
    parser.add_argument("--demographics", type=str, default=None,
                        help="Optional demographics tab CSV (rater_id, role, exp_years, freq_review_pr).")
    parser.add_argument("--quality-flags", type=str, default=None,
                        help="Optional quality_flags tab CSV (rater_id, quality_flags).")
    parser.add_argument("--feedback", type=str, default=None,
                        help="Optional feedback tab CSV (rater_id, feedback).")
    parser.add_argument("--exclude-rater", action="append", default=[],
                        help="Drop a rater_id from the analysis (repeatable). "
                             "Use to exclude raters auto-flagged for low quality.")
    parser.add_argument("--exclude-flagged", action="store_true",
                        help="Auto-exclude any rater present in the quality_flags CSV.")
    parser.add_argument("--sample", action="store_true",
                        help="Generate and analyse a synthetic sample CSV (for dry-runs).")
    parser.add_argument("--out", type=str,
                        default=str(RESULTS_DIR / "human_llm_agreement.json"),
                        help="Where to write the JSON report (default: results/human_llm_agreement.json).")
    parser.add_argument("--llm-checklist", type=str, default=None,
                        help="Override the LLM-judge checklist file. Default is "
                             "`results/checklist_evaluation_llm.json` (v1 single-judge). "
                             "For the human_eval_v3 study (cleaned dataset_v2 reviews) pass "
                             "`results/checklist_evaluation_llm_multi__v2.json` so both sides "
                             "are scoring the same review set.")
    args = parser.parse_args()

    llm_path = Path(args.llm_checklist) if args.llm_checklist else None
    if llm_path and not llm_path.is_absolute():
        llm_path = REPO_ROOT / llm_path
    checklist = load_llm_scores(llm_path)
    c6 = load_llm_c6()

    if args.sample:
        sample_path = RESULTS_DIR / "human_eval_sample.csv"
        _write_sample_csv(sample_path, checklist, c6)
        print(f"Wrote synthetic sample CSV → {sample_path.relative_to(REPO_ROOT)}\n")
        human_path = sample_path
    else:
        if not args.human:
            parser.error("--human <csv> required (or pass --sample for a dry-run)")
        human_path = Path(args.human)
        if not human_path.is_absolute():
            human_path = REPO_ROOT / human_path

    cells = load_human_csv(human_path)

    def _resolve(p: str | None) -> Path | None:
        if not p:
            return None
        pp = Path(p)
        return pp if pp.is_absolute() else REPO_ROOT / pp

    demo_path = _resolve(args.demographics)
    qf_path = _resolve(args.quality_flags)
    fb_path = _resolve(args.feedback)

    demographics = load_demographics_csv(demo_path) if demo_path else {}
    quality_flags = load_quality_flags_csv(qf_path) if qf_path else {}
    feedback = load_feedback_csv(fb_path) if fb_path else {}

    excluded: set[str] = set(args.exclude_rater or [])
    if args.exclude_flagged:
        excluded |= {r for r, fl in quality_flags.items() if fl}

    result = analyze(cells, checklist, c6,
                     demographics=demographics,
                     quality_flags=quality_flags,
                     feedback=feedback,
                     excluded_raters=excluded)
    print_report(result)

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote full JSON report → {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
