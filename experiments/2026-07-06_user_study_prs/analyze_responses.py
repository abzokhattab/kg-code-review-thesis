#!/usr/bin/env python3
"""
analyze_responses.py — implements ANALYSIS_PLAN.md for the v4 human study.

Input: CSV export of the Google Sheet (one JSON payload per row, as posted
by the study UI), or a directory of the UI's "Download my responses" JSON
backups. Handles both.

Usage:
  python3 analyze_responses.py responses.csv
  python3 analyze_responses.py backups_dir/
  python3 analyze_responses.py --selftest     # synthetic-data check, $0

No API calls. Requires numpy/scipy (already pinned in requirements-eval.txt).
"""
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

STUDY_ID = "human_eval_v4_python_20260808"
INSTRUMENT_VERSION = "python-prs-study-v4-diff-default-r14"
EXCLUDE_PREFIXES = ("pilot", "smoke", "test")
CRITERIA = ["F3*", "F2*", "T3", "Q5", "R1", "C6"]
PRIMARY = "F3*"
EXPLORATORY = [c for c in CRITERIA if c != PRIMARY]
EXPECTED_PRS = set(range(101, 107))
EXPECTED_COMPARISON = "bl_vs_kg"
EXPECTED_MODES = {"baseline_strict", "kg"}
CRITERION_CHOICES = {"A", "B", "both", "neither"}
OVERALL_CHOICES = {"A", "B", "equal"}
MIN_TASKS = 6
N_PRS = 6
BOOT = 10_000
rng = np.random.default_rng(2026)


# ── ingestion ────────────────────────────────────────────────────────────
def _unwrap_payload(value):
    """Accept a raw payload or the UI outbox's {queued_at, payload} wrapper."""
    if not isinstance(value, dict):
        return None
    nested = value.get("payload")
    return nested if isinstance(nested, dict) else value


def iter_payloads(src: Path):
    """Yield payload dicts from a sheet CSV or a folder of backup JSONs."""
    if src.is_dir():
        for f in sorted(src.glob("*.json")):
            try:
                d = json.loads(f.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            for p in d.get("payloads", [d]):
                p = _unwrap_payload(p)
                if p is not None:
                    yield p
    else:
        with src.open() as fh:
            for row in csv.reader(fh):
                for cell in row:
                    cell = cell.strip()
                    if cell.startswith("{"):
                        try:
                            p = _unwrap_payload(json.loads(cell))
                            if p is not None:
                                yield p
                        except json.JSONDecodeError:
                            pass


def load_ratings(src: Path):
    """Plan steps 1-4: filter, exclude, dedupe (latest wins), un-blind."""
    latest = {}
    feedback = []
    audit = Counter()
    for p in iter_payloads(src):
        audit["payloads_seen"] += 1
        if (p.get("study_id") != STUDY_ID
                or p.get("instrument_version") != INSTRUMENT_VERSION):
            audit["wrong_instrument"] += 1
            continue
        rid = str(p.get("rater_id", "")).strip()
        if not rid or any(rid.lower().startswith(x) for x in EXCLUDE_PREFIXES):
            audit["excluded_rater"] += 1
            continue
        if "feedback" in p:
            text = p.get("feedback")
            if isinstance(text, str) and text.strip():
                item = (rid, text.strip())
                if item not in feedback:
                    feedback.append(item)
                audit["feedback_accepted"] += 1
            else:
                audit["rows_rejected"] += 1
            continue
        rows = p.get("ratings")
        if not isinstance(rows, list):
            audit["rows_rejected"] += 1
            continue
        for r in rows:
            audit["rating_rows_seen"] += 1
            if not _valid_rating(r):
                audit["rows_rejected"] += 1
                continue
            key = (rid, r["pr_id"], r["comparison"])
            ts = p.get("completed_at", "")
            if not isinstance(ts, str):
                ts = ""
            if key not in latest or ts >= latest[key][0]:
                latest[key] = (ts, rid, r)
                audit["rows_accepted"] += 1
    ratings = defaultdict(list)   # rater -> list of un-blinded task dicts
    for (_, _, _), (ts, rid, r) in sorted(latest.items(), key=str):
        side_of_kg = "A" if r["mode_A"] == "kg" else "B"
        choices = r["criteria"]
        task = {
            "pr_id": r["pr_id"],
            "overall": _score(r.get("overall"), side_of_kg),
            "overall_choice": r["overall"],
            "difficulty": int(r["difficulty"]),
            "time_ms": float(r.get("time_spent_ms", 0)),
            "github_clicks": int(r.get("github_clicks", 0)),
            "why": r.get("why", ""),
            "highlight_used": bool(r.get("highlight_used", False)),
            "kg_side": side_of_kg,
            "choices": choices,
        }
        for c in CRITERIA:
            task[c] = _score(choices[c], side_of_kg)
        ratings[rid].append(task)
    return ratings, feedback, dict(audit)


def _valid_rating(r):
    """Reject malformed/foreign rows before they can enter confirmatory data."""
    if not isinstance(r, dict):
        return False
    if r.get("pr_id") not in EXPECTED_PRS:
        return False
    if r.get("comparison") != EXPECTED_COMPARISON:
        return False
    if {r.get("mode_A"), r.get("mode_B")} != EXPECTED_MODES:
        return False
    criteria = r.get("criteria")
    if not isinstance(criteria, dict):
        return False
    if set(criteria) != set(CRITERIA):
        return False
    if any(criteria[c] not in CRITERION_CHOICES for c in CRITERIA):
        return False
    if r.get("overall") not in OVERALL_CHOICES:
        return False
    if not isinstance(r.get("why", ""), str):
        return False
    difficulty = r.get("difficulty")
    if (isinstance(difficulty, bool)
            or not isinstance(difficulty, (int, float))
            or difficulty not in range(1, 6)):
        return False
    time_ms = r.get("time_spent_ms", 0)
    clicks = r.get("github_clicks", 0)
    if (isinstance(time_ms, bool)
            or not isinstance(time_ms, (int, float))
            or not math.isfinite(time_ms) or time_ms < 0):
        return False
    if (isinstance(clicks, bool) or not isinstance(clicks, int)
            or clicks < 0):
        return False
    if "highlight_used" in r and not isinstance(r["highlight_used"], bool):
        return False
    return True


def _score(choice, side_of_kg):
    """kg pick=1, baseline pick=0, both/neither/equal=0.5, missing=None."""
    if choice in ("both", "neither", "equal"):
        return 0.5
    if choice in ("A", "B"):
        return 1.0 if choice == side_of_kg else 0.0
    return None


# ── statistics ───────────────────────────────────────────────────────────
def rater_scores(ratings, endpoint):
    out = []
    for rid, tasks in ratings.items():
        vals = [t[endpoint] for t in tasks if t[endpoint] is not None]
        if vals:
            out.append(np.mean(vals))
    return np.array(out)


def wilcoxon_vs_half(scores):
    d = scores - 0.5
    d = d[d != 0]
    if len(d) < 5:
        return None, None, len(d)
    res = stats.wilcoxon(d, alternative="two-sided", method="approx")
    # Signed matched-pairs rank-biserial correlation. scipy's two-sided
    # statistic is min(W+, W-), which loses direction; compute both rank
    # sums explicitly so baseline-favouring effects remain negative.
    ranks = stats.rankdata(np.abs(d), method="average")
    w_pos = np.sum(ranks[d > 0])
    w_neg = np.sum(ranks[d < 0])
    r_rb = (w_pos - w_neg) / (w_pos + w_neg)
    return res.pvalue, r_rb, len(d)


def boot_ci(scores):
    means = [np.mean(rng.choice(scores, len(scores), replace=True)) for _ in range(BOOT)]
    return np.percentile(means, [2.5, 97.5])


def holm(pairs):
    """pairs: [(name, p)] -> dict name -> adjusted p."""
    # Keep the preregistered family size fixed. An endpoint with too few
    # non-ties to test receives conservative p=1 rather than shrinking m.
    pairs = sorted([(1.0 if p is None else p, n) for n, p in pairs])
    out, m, prev = {}, len(pairs), 0.0
    for i, (p, n) in enumerate(pairs):
        adj = min(1.0, max(prev, (m - i) * p))
        out[n] = prev = adj
    return out


def pseudonyms(*groups) -> dict[str, str]:
    """Map each rater id to P01, P02, ... in a stable order.

    The prefix is P for participant, not R for rater: R1 is already a rubric
    criterion in this instrument, and two label spaces one character apart in
    the same report is how a number ends up attributed to the wrong thing.

    Raters self-identified with real names, so the report this script writes is
    the last point at which those names can be stopped from spreading into the
    thesis, a figure, or a quoted rationale. The mapping is written to a
    separate local file rather than inlined here, so the report itself carries
    no way back to a person.
    """
    ids = sorted({rid for g in groups for rid in g})
    return {rid: f"P{i:02d}" for i, rid in enumerate(ids, start=1)}


# ── report ───────────────────────────────────────────────────────────────
def analyze(ratings, feedback, out_path: Path, audit=None, real_ids=False):
    complete = {
        r: t for r, t in ratings.items()
        if len(t) == MIN_TASKS and {x["pr_id"] for x in t} == EXPECTED_PRS
    }
    partial = {r: t for r, t in ratings.items() if r not in complete and t}
    pmap = pseudonyms(complete, partial, [r for r, _ in feedback])
    if real_ids:
        pmap = {k: k for k in pmap}

    def who(rid: str) -> str:
        return pmap.get(rid, "P??")

    L = [f"# Human study v4 — results ({len(complete)} raters analysed, "
         f"{len(partial)} partial excluded)\n"]
    if not real_ids:
        L.append("Rater ids are pseudonyms. The mapping to the self-reported "
                 "names is in `RATER_PSEUDONYM_MAP.txt`, which must not be "
                 "committed or quoted in the thesis.\n")
    if len(complete) < 5:
        L.append(f"**Not enough raters yet ({len(complete)}; need >=5 for the "
                 "Wilcoxon to run, 18-20 complete raters planned). "
                 "Descriptives only.**\n")
    elif len(complete) < 18:
        L.append(f"**Interim only: {len(complete)} complete raters; the "
                 "pre-confirmatory target is 18-20.**\n")

    # primary
    s = rater_scores(complete, PRIMARY)
    if len(s):
        p, r_rb, n_eff = wilcoxon_vs_half(s)
        lo, hi = boot_ci(s)
        L += [f"## Primary — {PRIMARY}",
              f"- mean KG-preference **{np.mean(s):.3f}** (95% boot CI {lo:.3f}-{hi:.3f}), n={len(s)} raters",
              f"- Wilcoxon vs 0.5: p={'NA (n<5 non-ties)' if p is None else f'{p:.4f}'}"
              + f", effective non-tie n={n_eff}"
              + (f", rank-biserial r={r_rb:.2f}" if r_rb is not None else ""), ""]

    # secondary
    s = rater_scores(complete, "overall")
    if len(s):
        lo, hi = boot_ci(s)
        L += ["## Secondary — overall usefulness (estimation only)",
              f"- mean KG-preference **{np.mean(s):.3f}** (95% boot CI {lo:.3f}-{hi:.3f})", ""]

    # exploratory
    rows, ps = [], []
    for c in EXPLORATORY:
        sc = rater_scores(complete, c)
        if not len(sc):
            continue
        p, _, n_eff = wilcoxon_vs_half(sc)
        ps.append((c, p))
        rows.append((c, np.mean(sc), p, n_eff))
    adj = holm(ps)
    # Bootstrap intervals for the exploratory criteria are not in the markdown
    # table, which reports the corrected test, but the figure plots intervals
    # for all six criteria on one axis and needs them here.
    expl_ci = {c: boot_ci(rater_scores(complete, c)) for c, *_ in rows}
    L += ["## Exploratory — remaining criteria (Holm-corrected)",
          "| criterion | mean | non-tie n | p (raw) | p (Holm) |",
          "|---|---|---|---|---|"]
    for c, m, p, n_eff in rows:
        L.append(f"| {c} | {m:.3f} | {n_eff} | "
                 f"{'NA' if p is None else f'{p:.4f}'} | "
                 f"{adj.get(c, 1):.4f} |")

    # descriptives
    L += ["", "## Descriptives",
          "| PR | mean overall | mean F3* | mean difficulty | highlight used | n |",
          "|---|---|---|---|---|---|"]
    by_pr = defaultdict(list)
    for tasks in complete.values():
        for t in tasks:
            by_pr[t["pr_id"]].append(t)
    for pid in sorted(by_pr):
        ts = by_pr[pid]
        ov = [t["overall"] for t in ts if t["overall"] is not None]
        f3 = [t[PRIMARY] for t in ts if t[PRIMARY] is not None]
        df = [t["difficulty"] for t in ts if t["difficulty"]]
        hu = sum(t["highlight_used"] for t in ts)
        L.append(f"| {pid} | {np.mean(ov):.2f} | {np.mean(f3):.2f} | "
                 f"{np.mean(df):.1f} | {hu}/{len(ts)} | {len(ts)} |")
    all_tasks = [t for tasks in complete.values() for t in tasks]
    if all_tasks:
        difficulty = Counter(t["difficulty"] for t in all_tasks)
        f3_choices = Counter(
            t["choices"][PRIMARY]
            if t["choices"][PRIMARY] in ("both", "neither")
            else ("kg" if t["choices"][PRIMARY] == t["kg_side"] else "baseline")
            for t in all_tasks
        )
        L += [
            "",
            f"- median task time: {np.median([t['time_ms'] for t in all_tasks]) / 1000:.1f}s",
            f"- total GitHub-link clicks: {sum(t['github_clicks'] for t in all_tasks)}",
            "- difficulty distribution (1–5): "
            + ", ".join(f"{k}={difficulty.get(k, 0)}" for k in range(1, 6)),
            "- F3* choices normalised to mode: "
            + ", ".join(f"{k}={f3_choices.get(k, 0)}"
                        for k in ("kg", "baseline", "both", "neither")),
        ]
        L += ["", "### Both / neither by criterion",
              "| criterion | both | neither |", "|---|---|---|"]
        for criterion in CRITERIA:
            choices = Counter(t["choices"][criterion] for t in all_tasks)
            L.append(f"| {criterion} | {choices['both']} | {choices['neither']} |")
        L += ["", "## A/B side balance",
              "| PR | KG on A | KG on B |", "|---|---|---|"]
        for pid in sorted(by_pr):
            sides = Counter(t["kg_side"] for t in by_pr[pid])
            L.append(f"| {pid} | {sides['A']} | {sides['B']} |")
        rationales = [
            (rid, t["pr_id"], t["why"])
            for rid, tasks in complete.items() for t in tasks if t["why"].strip()
        ]
        if rationales:
            L += ["", "## Rationale audit (for post-hoc coding)",
                  "| rater | PR | rationale |", "|---|---|---|"]
            for rid, pid, text in rationales:
                safe = text.replace("|", "\\|").replace("\n", " ")
                L.append(f"| {who(rid)} | {pid} | {safe} |")
    if audit:
        L += ["", "## Ingestion audit"] + [
            f"- {k}: {audit[k]}" for k in sorted(audit)
        ]
    if partial:
        L += ["", "## Partial sessions (excluded from inference)"] + [
            f"- {who(rid)}: {len(tasks)}/6 tasks"
            for rid, tasks in sorted(partial.items())
        ]
    if feedback:
        L += ["", "## Free-text feedback"] + [
            f"- **{who(r)}**: {t}" for r, t in feedback
        ]

    out_path.write_text("\n".join(L) + "\n")

    # Machine-readable copy for the thesis figure, so the figure and this report
    # cannot disagree. Contains no rater identifiers of any kind.
    prim = rater_scores(complete, PRIMARY)
    ovr = rater_scores(complete, "overall")
    p_prim, r_prim, n_prim = wilcoxon_vs_half(prim)
    summary = {
        "n_raters": len(complete),
        "n_partial_excluded": len(partial),
        "primary": {
            "criterion": PRIMARY, "mean": float(np.mean(prim)),
            "ci": list(boot_ci(prim)), "p": p_prim,
            "rank_biserial": r_prim, "non_tie_n": n_prim,
        },
        "secondary_overall": {
            "mean": float(np.mean(ovr)), "ci": list(boot_ci(ovr)),
        },
        "exploratory": {
            c: {"mean": float(m), "ci": list(expl_ci[c]),
                "p_raw": p, "p_holm": adj.get(c), "non_tie_n": n_eff}
            for c, m, p, n_eff in rows
        },
    }
    (out_path.parent / "RESULTS_HUMAN_V4.json").write_text(
        json.dumps(summary, indent=1))

    if not real_ids:
        (out_path.parent / "RATER_PSEUDONYM_MAP.txt").write_text(
            "# Personal data. Do not commit. Do not quote in the thesis.\n"
            + "".join(f"{v}\t{k}\n" for k, v in sorted(pmap.items(),
                                                       key=lambda kv: kv[1]))
        )
    print("\n".join(L))
    print(f"\nwrote {out_path}")


# ── self-test on synthetic data ──────────────────────────────────────────
def selftest():
    payloads = []
    for i in range(16):
        rid = f"rater{i:02d}"
        for pid in range(101, 107):
            flip = rng.random() < 0.5
            kg_side = "A" if flip else "B"
            crit = {}
            for c in CRITERIA:
                p_kg = 0.65 if c == PRIMARY else 0.45
                u = rng.random()
                crit[c] = kg_side if u < p_kg else ("both" if u < p_kg + 0.2
                          else ("A" if kg_side == "B" else "B"))
            u = rng.random()
            overall = kg_side if u < 0.5 else ("equal" if u < 0.7
                      else ("A" if kg_side == "B" else "B"))
            payloads.append({"study_id": STUDY_ID,
                             "instrument_version": INSTRUMENT_VERSION,
                             "rater_id": rid,
                             "completed_at": f"2026-07-10T10:{i:02d}:00Z",
                             "ratings": [{"pr_id": pid, "comparison": "bl_vs_kg",
                                          "mode_A": "kg" if flip else "baseline_strict",
                                          "mode_B": "baseline_strict" if flip else "kg",
                                          "criteria": crit, "overall": overall,
                                          "why": "synthetic", "difficulty": 2,
                                          "time_spent_ms": 120000,
                                          "highlight_used": False}]})
    # noise rows the pipeline must drop
    payloads.append({"study_id": "human_eval_v4", "rater_id": "raterXX",
                     "ratings": []})
    payloads.append({"study_id": STUDY_ID,
                     "instrument_version": INSTRUMENT_VERSION,
                     "rater_id": "pilot_agent",
                     "ratings": [{"pr_id": 101, "mode_A": "kg",
                                  "mode_B": "baseline_strict", "criteria": {},
                                  "overall": "A"}]})
    payloads.append({"study_id": STUDY_ID,
                     "instrument_version": INSTRUMENT_VERSION,
                     "rater_id": "malformed",
                     "completed_at": "2026-07-10T11:00:00Z",
                     "ratings": [{"pr_id": 999, "comparison": "bogus",
                                  "mode_A": "x", "mode_B": "y",
                                  "criteria": {}, "overall": "A",
                                  "difficulty": 2}]})
    nonfinite = dict(payloads[0]["ratings"][0])
    nonfinite["time_spent_ms"] = float("nan")
    payloads.append({"study_id": STUDY_ID,
                     "instrument_version": INSTRUMENT_VERSION,
                     "rater_id": "nonfinite",
                     "completed_at": "2026-07-10T11:01:00Z",
                     "ratings": [nonfinite]})
    fractional_clicks = dict(payloads[0]["ratings"][0])
    fractional_clicks["github_clicks"] = 1.5
    payloads.append({"study_id": STUDY_ID,
                     "instrument_version": INSTRUMENT_VERSION,
                     "rater_id": "fractional-clicks",
                     "completed_at": "2026-07-10T11:02:00Z",
                     "ratings": [fractional_clicks]})
    tmp = Path("/tmp/heval4_selftest")
    tmp.mkdir(exist_ok=True)
    wrapped = [{"queued_at": "2026-07-10T10:00:00Z", "payload": p}
               for p in payloads]
    (tmp / "backup.json").write_text(json.dumps({"payloads": wrapped}))
    ratings, fb, audit = load_ratings(tmp)
    assert len(ratings) == 16, f"expected 16 raters, got {len(ratings)}"
    assert all(len(t) == 6 for t in ratings.values())
    assert audit["rows_rejected"] == 3, audit
    _, r_pos, _ = wilcoxon_vs_half(np.array([0.7, 0.8, 0.9, 0.7, 0.8]))
    _, r_neg, _ = wilcoxon_vs_half(np.array([0.3, 0.2, 0.1, 0.3, 0.2]))
    assert r_pos > 0 and r_neg < 0, (r_pos, r_neg)
    analyze(ratings, fb, Path("/tmp/heval4_selftest/RESULTS.md"), audit)
    print("\nSELFTEST OK: wrapped backups, validation, exclusions, "
          "un-blinding, and signed effects correct.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        selftest()
    elif len(sys.argv) > 1:
        args = [a for a in sys.argv[1:] if a != "--real-ids"]
        src = Path(args[0])
        ratings, fb, audit = load_ratings(src)
        analyze(ratings, fb, Path(__file__).parent / "RESULTS_HUMAN_V4.md",
                audit, real_ids="--real-ids" in sys.argv)
    else:
        print(__doc__)
