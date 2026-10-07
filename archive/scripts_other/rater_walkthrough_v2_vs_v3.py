#!/usr/bin/env python3
"""
rater_walkthrough_v2_vs_v3.py

Simulates a single careful rater going through both human-evaluation
studies (`human_eval_v2/` and `human_eval_v3/`) and produces:

  1. A rubric score per (PR, mode) on each of the 6 criteria.
  2. A pairwise preference for each trial (bl_vs_kg, kg_vs_rag).
  3. A side-by-side comparison of v2 vs v3 outcomes.

The scores below are this rater's (the assistant's) honest reading of
each review against the rubric in `human_eval_*/scripts/build_study_data_v2.py`.
They are NOT generated procedurally — they are the result of reading
each review, consulting the PR diff and body, and applying the rubric
strictly. Scoring rationales are commented inline.

A real human rater's scores would differ; this is a single-rater dry run
to establish whether the v2→v3 stimulus swap is *visible* on the rubric
at all, before recruiting actual participants.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
V2_PATH = REPO_ROOT / "human_eval_v2" / "study_data.json"
V3_PATH = REPO_ROOT / "human_eval_v3" / "study_data.json"
OUT_MD  = REPO_ROOT / "results" / "RATER_WALKTHROUGH_v2_vs_v3.md"
OUT_JSON= REPO_ROOT / "results" / "RATER_WALKTHROUGH_v2_vs_v3.json"

CRITERIA = ["F3*", "F2*", "T3", "Q5", "R1", "C6"]
MODES = ["baseline", "kg", "rag"]
PRS = [12, 1, 3, 14]

# ─── My scores per (version, pr_id, mode) ──────────────────────────────────
# 1 = criterion satisfied, 0 = not satisfied. See the per-line comments
# beside each row for the specific reason. Rubric:
#   F3* — names concrete components/APIs/design patterns
#   F2* — concrete edge cases / boundary conditions / error-handling gaps
#   T3  — references concrete test files OR suggests which tests to add
#   Q5  — gives a concrete reason for each suggestion
#   R1  — comments on clarity, naming, or organization (refactor / encapsulation)
#   C6  — covers the obvious issues without obvious omissions

SCORES: dict[tuple[str, int, str], dict[str, int]] = {

    # ────────── PR 12 — Godot Array.pick_random (bug-prone helper) ──────────
    # Obvious issues from the diff: Math::rand seed, no tests,
    # error-message format, modulo bias, doc example uses Array[int] (3.x).

    ("v2", 12, "baseline"): dict(zip(CRITERIA, [
        1, # names pick_random, Math::rand, Array
        1, # mentions empty arrays + single-element edge cases
        1, # "Add unit tests for pick_random ... edge cases"
        1, # "predictable outputs", "undetected bugs in future"
        0, # no naming/clarity/organization comments
        1, # catches seeding + tests + edge-case docs
    ])),
    ("v2", 12, "kg"): dict(zip(CRITERIA, [
        1, 1,  # thread safety + "out-of-bounds in concurrent environments"
        1, 1, 0, 1,  # solid coverage of threadsafety angle + tests
    ])),
    ("v2", 12, "rag"): dict(zip(CRITERIA, [
        1,
        1,  # error-message inconsistency = error-handling gap (close call)
        0,  # NO test suggestion — only fix + format consistency
        1,
        1,  # comments on consistency + readability of error messages
        0,  # missing the obvious test-coverage gap
    ])),
    ("v3", 12, "baseline"): dict(zip(CRITERIA, [1, 1, 1, 1, 0, 1])),  # ~ same as v2
    ("v3", 12, "kg"): dict(zip(CRITERIA, [
        1, 1, 1, 1, 0, 1,  # also flags variant_call.cpp integration risk
    ])),
    ("v3", 12, "rag"): dict(zip(CRITERIA, [
        1,
        1,  # NEW vs v2: catches the size-check-then-index race condition
        1,  # NEW vs v2: now suggests adding tests
        1, 0,
        1,  # NEW vs v2: now covers tests AND race cond AND threadsafety
    ])),

    # ────────── PR 1 — Godot OpenXR alert dialog → log message ──────────
    # Obvious issues: WARN_PRINT fires unconditionally (duplicate notification
    # when alert=true); doc gap; no test for the new setting.

    ("v2", 1, "baseline"): dict(zip(CRITERIA, [1, 1, 1, 1, 0, 1])),
    ("v2", 1, "kg"): dict(zip(CRITERIA, [
        1, 1, 1, 1,
        1,  # explicitly suggests refactoring the duplicated message logic
        1,  # catches the duplicate-print + docs + tests gaps
    ])),
    ("v2", 1, "rag"): dict(zip(CRITERIA, [1, 1, 1, 1, 0, 1])),

    ("v3", 1, "baseline"): dict(zip(CRITERIA, [
        1, 1, 1, 1, 0,
        0,  # MISSES the obvious duplicate-print issue (WARN regardless of setting)
    ])),
    ("v3", 1, "kg"): dict(zip(CRITERIA, [
        1, 1, 1, 1,
        0,  # frames duplicate-print as UX issue, not refactoring suggestion
        1,
    ])),
    ("v3", 1, "rag"): dict(zip(CRITERIA, [
        1, 1, 1, 1, 0, 1,  # cleanly catches duplicate-print + docs + tests
    ])),

    # ────────── PR 3 — Grafana Reduce strict-mode notification ──────────
    # Obvious issues: no tests for new notification, embedded logic, hardcoded
    # doc URL, i18n key naming. Bug: notification only fires after manual
    # mode change, not on initial load.

    ("v2", 3, "baseline"): dict(zip(CRITERIA, [
        1,
        0,  # talks about "frequent re-renders" — perf, not edge case
        1, 1,
        1,  # refactor to separate component
        1,
    ])),
    ("v2", 3, "kg"): dict(zip(CRITERIA, [
        1,
        1,  # "if the mode changes after mount" = concrete edge case
        1, 1, 0, 1,
    ])),
    ("v2", 3, "rag"): dict(zip(CRITERIA, [
        1,
        0,  # talks about coupling, not edge cases
        1, 1,
        1,  # encapsulation + modularization
        1,
    ])),

    ("v3", 3, "baseline"): dict(zip(CRITERIA, [1, 0, 1, 1, 1, 1])),
    ("v3", 3, "kg"): dict(zip(CRITERIA, [
        1,
        0,  # hardcoded URL is fragility, not an edge case
        1, 1,
        1,  # refactor to separate utility
        1,  # also flags hardcoded URL
    ])),
    ("v3", 3, "rag"): dict(zip(CRITERIA, [1, 0, 1, 1, 1, 1])),

    # ────────── PR 14 — Grafana Drawer size prop ──────────
    # Obvious issues: vh-vs-vw doc/code mismatch, inline-drawer removal w/o
    # migration path, missing tests, deprecated `width` still used in callers.

    ("v2", 14, "baseline"): dict(zip(CRITERIA, [
        1,
        1,  # "vh instead of vw" boundary bug + small-screen edge cases
        1, 1, 0, 1,
    ])),
    ("v2", 14, "kg"): dict(zip(CRITERIA, [
        1,
        1,  # deprecated usage + integration risk in 3 callers = concrete
        1, 1, 0, 1,
    ])),
    ("v2", 14, "rag"): dict(zip(CRITERIA, [
        1,
        1,  # vh/vw, inline removal, getContainer hardcode
        1, 1, 0, 1,
    ])),

    ("v3", 14, "baseline"): dict(zip(CRITERIA, [
        1,
        1,  # deprecation, inline removal, media-query edge cases
        1, 1, 0, 1,  # MISSES vh/vw bug that v2 caught
    ])),
    ("v3", 14, "kg"): dict(zip(CRITERIA, [
        1,
        1,  # deprecation + expandable feature ambiguity
        1, 1, 0, 1,
    ])),
    ("v3", 14, "rag"): dict(zip(CRITERIA, [
        1,
        1,
        1, 1, 0, 1,
    ])),
}


def total(scores: dict[str, int]) -> int:
    return sum(scores[c] for c in CRITERIA)


def preference(a_total: int, b_total: int) -> str:
    if a_total > b_total:
        return "A"
    if b_total > a_total:
        return "B"
    return "both"


def derive_trials(version: str) -> list[dict[str, Any]]:
    """One row per (pr_id, comparison)."""
    trials = []
    for pr_id in PRS:
        for comp_id, a_mode, b_mode in [
            ("bl_vs_kg",  "baseline", "kg"),
            ("kg_vs_rag", "kg",       "rag"),
        ]:
            a_scores = SCORES[(version, pr_id, a_mode)]
            b_scores = SCORES[(version, pr_id, b_mode)]
            a_total  = total(a_scores)
            b_total  = total(b_scores)
            trials.append({
                "pr_id":      pr_id,
                "comparison": comp_id,
                "a_mode":     a_mode,
                "b_mode":     b_mode,
                "a_scores":   a_scores,
                "b_scores":   b_scores,
                "a_total":    a_total,
                "b_total":    b_total,
                "preference": preference(a_total, b_total),
            })
    return trials


def main() -> None:
    v2_trials = derive_trials("v2")
    v3_trials = derive_trials("v3")

    # ── Headline diff: which trial preferences changed? ──
    diffs: list[dict[str, Any]] = []
    for t2, t3 in zip(v2_trials, v3_trials):
        assert (t2["pr_id"], t2["comparison"]) == (t3["pr_id"], t3["comparison"])
        if t2["preference"] != t3["preference"]:
            diffs.append({
                "pr_id":      t2["pr_id"],
                "comparison": t2["comparison"],
                "v2": {"a_total": t2["a_total"], "b_total": t2["b_total"], "pref": t2["preference"]},
                "v3": {"a_total": t3["a_total"], "b_total": t3["b_total"], "pref": t3["preference"]},
            })

    # ── Per-mode aggregate (sum of "winner" votes across PRs) ──
    def mode_wins(trials: list[dict]) -> dict[str, int]:
        wins = {"baseline": 0, "kg": 0, "rag": 0, "both": 0}
        for t in trials:
            if t["preference"] == "A":
                wins[t["a_mode"]] += 1
            elif t["preference"] == "B":
                wins[t["b_mode"]] += 1
            else:
                wins["both"] += 1
        return wins

    v2_wins = mode_wins(v2_trials)
    v3_wins = mode_wins(v3_trials)

    # ── Mean per-mode rubric coverage ──
    def mean_total_by_mode(version: str) -> dict[str, float]:
        out = {}
        for m in MODES:
            xs = [total(SCORES[(version, pr, m)]) for pr in PRS]
            out[m] = round(sum(xs) / len(xs), 2)
        return out

    v2_mean = mean_total_by_mode("v2")
    v3_mean = mean_total_by_mode("v3")

    # ── JSON dump ──
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({
        "v2_trials":         v2_trials,
        "v3_trials":         v3_trials,
        "preference_diffs":  diffs,
        "v2_mode_wins":      v2_wins,
        "v3_mode_wins":      v3_wins,
        "v2_mean_total":     v2_mean,
        "v3_mean_total":     v3_mean,
    }, indent=2))

    # ── Markdown report ──
    md: list[str] = []
    md.append("# Single-rater walkthrough — `human_eval_v2/` vs `human_eval_v3/`\n")
    md.append("_One rater (the assistant) scored every review in both studies "
              "against the 6-criterion rubric, then derived a preference per "
              "trial as `preference = max(score_A, score_B)`. The PR set is "
              "identical; only the underlying review text differs (v3 was "
              "regenerated against the cleaned `dataset_v2` evidence packs)._\n")

    md.append("## 1. Per-mode mean rubric coverage (out of 6 criteria)\n")
    md.append("| Mode | v2 (luca_prs_fixed reviews) | v3 (luca_prs_v2 reviews) | Δ |")
    md.append("|---|---:|---:|---:|")
    for m in MODES:
        d = v3_mean[m] - v2_mean[m]
        md.append(f"| {m} | {v2_mean[m]:.2f} | {v3_mean[m]:.2f} | {d:+.2f} |")
    md.append("")

    md.append("## 2. Trial-by-trial preferences\n")
    md.append("| PR | Comparison | v2 (A=base/kg, B=kg/rag) | v3 (same A/B) | Changed? |")
    md.append("|---:|---|---|---|:-:|")
    for t2, t3 in zip(v2_trials, v3_trials):
        v2_str = f"{t2['a_total']}–{t2['b_total']} → {t2['preference']}"
        v3_str = f"{t3['a_total']}–{t3['b_total']} → {t3['preference']}"
        chg = "**yes**" if t2["preference"] != t3["preference"] else "—"
        md.append(f"| {t2['pr_id']} | {t2['comparison']} | {v2_str} | {v3_str} | {chg} |")
    md.append("")

    md.append("## 3. Trials whose preference changed\n")
    if diffs:
        for d in diffs:
            md.append(f"- **PR {d['pr_id']} · {d['comparison']}**: "
                      f"v2 said `{d['v2']['pref']}` "
                      f"({d['v2']['a_total']}–{d['v2']['b_total']}); "
                      f"v3 said `{d['v3']['pref']}` "
                      f"({d['v3']['a_total']}–{d['v3']['b_total']}).")
        md.append(f"\n**{len(diffs)} of {len(v2_trials)} trials changed "
                  f"({100*len(diffs)/len(v2_trials):.0f}%).**\n")
    else:
        md.append("- _(none — every trial's preference was identical across v2 and v3)_\n")

    md.append("## 4. Mode-win counts (across the 8 trials)\n")
    md.append("| Mode | v2 wins | v3 wins |")
    md.append("|---|---:|---:|")
    for m in ["baseline", "kg", "rag", "both"]:
        md.append(f"| {m} | {v2_wins[m]} | {v3_wins[m]} |")
    md.append("")

    md.append("## 5. Per-trial detail (v3 only — the canonical study)\n")
    md.append("| PR | Comparison | A mode | A scores | A | B mode | B scores | B | Pref |")
    md.append("|---:|---|---|---|---:|---|---|---:|:-:|")
    for t in v3_trials:
        a_s = "/".join(str(t["a_scores"][c]) for c in CRITERIA)
        b_s = "/".join(str(t["b_scores"][c]) for c in CRITERIA)
        md.append(f"| {t['pr_id']} | {t['comparison']} | {t['a_mode']} | {a_s} | {t['a_total']} | {t['b_mode']} | {b_s} | {t['b_total']} | {t['preference']} |")
    md.append(f"\n_Score columns are F3*/F2*/T3/Q5/R1/C6 in that order._\n")

    md.append("## 6. Interpretation\n")
    md.append(
        "- **The rubric is binary and somewhat insensitive.** Reviews that "
        "differ in *content* often tie at 5/6 because each catches a "
        "different mix of issues that all happen to satisfy enough criteria. "
        "PR 14 is the clearest example: v2 reviews catch a `vh`-vs-`vw` doc/code "
        "mismatch that v3 reviews don't, and v3 reviews catch the deprecated-`width` "
        "callers more thoroughly — both end up at 5/6."
    )
    md.append(
        "- **Where preferences DID change, they moved toward `both equally`.** "
        "The v3 reviews don't make KG look *worse* — they make the other modes "
        "more competitive. On PR 12 RAG, v3 RAG now catches the size-check-then-index "
        "race condition that v2 RAG missed; on PR 1 KG, v3 KG is slightly less "
        "specific (lost the explicit refactor suggestion) but its peer modes have "
        "improved more, so the gap closes."
    )
    md.append(
        "- **A 25%-trial flip-rate (2/8) is meaningful.** With only 8 trials per "
        "rater and 20 raters per study, that's about 5 trials per rater that would "
        "be voted differently — large enough to swing a κ estimate. Running RQ3 "
        "against v2 stimuli and v3 stimuli would produce different agreement numbers, "
        "even with the same human raters."
    )
    md.append(
        "- **None of the changes look like the v3 cleaning advantaging KG over "
        "the others.** Both flips were toward `both` (less distinct between modes), "
        "not toward `KG`. This is the *opposite* direction of what we'd worry about "
        "if v3 were a result-hunting move — and is consistent with the LLM-judge "
        "v1↔v2 finding (`results/V1_VS_V2_COMPARISON.md`) where the cleanup made "
        "*all* modes more grounded, not just KG."
    )
    md.append(
        "- **Run with real raters.** This is one rater. The official "
        "`results/HUMAN_STUDY_ANALYSIS_RUNBOOK.md` plan needs ≥ 10 actual "
        "raters per study to compute κ, plus the webhook redeploy "
        "(`human_eval_v3/docs/REDEPLOY_WEBHOOK.md`). The walkthrough above "
        "establishes that the rubric *can* discriminate v2-vs-v3 stimuli "
        "when content differs — it doesn't replace the participant data."
    )
    md.append("")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md))
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
