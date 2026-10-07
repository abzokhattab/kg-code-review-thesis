#!/usr/bin/env python3
"""Positive control: does the rubric discriminate known-bad reviews from real ones?

We generate a small set of *deliberately bad* reviews — empty, generic boilerplate,
off-topic, hallucinated — for several PRs, then score them with the same multi-judge
panel used in the main study and compare to the existing baseline reviews on the
same PRs. If the rubric is a meaningful instrument, bad << baseline at p < 0.001.

If this fails, no claim about KG vs baseline can be drawn from the rubric, because
the rubric isn't discriminating quality. If it succeeds (which we expect), it
provides the methods-section sanity check that the rubric measures *something*.

Usage:
    python3 scripts/positive_control_rubric.py
"""

from __future__ import annotations

import json
import sys
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.evaluate_reviews import (  # noqa: E402
    EVALUATION_CRITERIA,
    evaluate_single_review,
)


# Five PRs spanning repos / languages / sizes
TEST_PRS = [3, 6, 14, 18, 25]

JUDGES = ["openai:gpt-4o-mini", "openai:gpt-4o", "gemini:gemini-2.5-flash"]
OUT_DIR = REPO_ROOT / "outputs" / "positive_control_bad"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ── Bad-review templates ──────────────────────────────────────────────────────

BAD_EMPTY = ""

BAD_ONE_LINE = "Looks good to me."

BAD_BOILERPLATE = """## Summary

This pull request introduces some changes that should be reviewed carefully before merging.

## Comments

- Please ensure all changes are well-tested.
- Consider the maintainability of the code.
- Check that the change is consistent with the rest of the codebase.
- Make sure documentation is up to date.

## Conclusion

Overall the change looks reasonable. Please address any concerns before merging."""

BAD_OFFTOPIC = """## Summary

The recipe for chocolate chip cookies has been updated to include more sugar and an
additional egg. The mixing instructions remain the same: cream butter and sugar, then
add eggs one at a time, then dry ingredients.

## Comments

- The new sugar ratio improves browning during baking.
- Adding the second egg gives a chewier texture.
- Bake at 175°C for 12 minutes, not 10, given the increased moisture.

## Conclusion

The updated recipe should produce better cookies. Please test before publishing."""

BAD_HALLUCINATED = """## Summary

This change modifies `src/main/handler/AuthHandler.java` line 142 to fix a null
pointer exception in the `validateToken()` method, and updates the corresponding
test in `src/test/AuthHandlerTest.java`.

## Comments

- The fix at `AuthHandler.java:142` correctly checks `token != null` before dereferencing.
- The new branch in `validateToken()` should also handle empty strings.
- Test coverage for `AuthHandlerTest.testInvalidToken()` looks adequate.
- The `JwtService.parseClaims()` call on line 167 should be wrapped in try/catch.

## Conclusion

LGTM after the empty-string handling is addressed."""

BAD_TEMPLATES = {
    "empty":         BAD_EMPTY,
    "one_line":      BAD_ONE_LINE,
    "boilerplate":   BAD_BOILERPLATE,
    "offtopic":      BAD_OFFTOPIC,
    "hallucinated":  BAD_HALLUCINATED,
}


def write_bad_reviews() -> list[Path]:
    written = []
    for pr_id in TEST_PRS:
        for tag, content in BAD_TEMPLATES.items():
            p = OUT_DIR / f"pr{pr_id}_bad-{tag}.md"
            p.write_text(content)
            written.append(p)
    return written


def evaluate_bad_review(pr_id: int, tag: str):
    """Reuse the canonical single-review evaluator; review file already written."""
    review_path = OUT_DIR / f"pr{pr_id}_bad-{tag}.md"
    return evaluate_single_review(
        review_path=review_path, pr_id=pr_id,
        mode=f"bad-{tag}", judges=JUDGES,
    )


def load_existing_baseline_scores() -> dict[int, dict[str, float]]:
    """Pull baseline + hybrid scores from canonical and scoped runs."""
    out: dict[int, dict[str, float]] = {}
    canonical = REPO_ROOT / "results" / "checklist_evaluation_llm_multi.json"
    if canonical.exists():
        ev = json.loads(canonical.read_text())
        for e in ev["evaluations"]:
            if e["pr_id"] in TEST_PRS and e["mode"] == "baseline":
                out.setdefault(e["pr_id"], {})["baseline"] = e["total_score"]
                out[e["pr_id"]]["baseline_kg"] = e["kg_relevant_score"]
    scoped = REPO_ROOT / "results" / "checklist_evaluation_llm_multi__gpt4o_scoped_fullkg16.json"
    if scoped.exists():
        ev = json.loads(scoped.read_text())
        for e in ev["evaluations"]:
            if e["pr_id"] in TEST_PRS and e["mode"] == "hybrid":
                out.setdefault(e["pr_id"], {})["hybrid"] = e["total_score"]
                out[e["pr_id"]]["hybrid_kg"] = e["kg_relevant_score"]
    return out


def paired_permutation_p(diffs: list[float], n_perm: int = 20000, seed: int = 2026) -> float:
    """Two-sided sign-flip permutation p-value on paired differences."""
    rng = random.Random(seed)
    n = len(diffs)
    if n == 0 or all(d == 0 for d in diffs):
        return 1.0
    obs = sum(diffs) / n
    bigger = 0
    for _ in range(n_perm):
        s = sum(rng.choice([-1, 1]) * d for d in diffs) / n
        if abs(s) >= abs(obs) - 1e-12:
            bigger += 1
    return bigger / n_perm


def main() -> None:
    print(f"PRs under test: {TEST_PRS}")
    print(f"Bad-review styles: {list(BAD_TEMPLATES.keys())}")
    print(f"Judges: {JUDGES}")

    write_bad_reviews()
    bad_evals: list[dict] = []
    n_total = len(TEST_PRS) * len(BAD_TEMPLATES)
    i = 0
    for pr_id in TEST_PRS:
        for tag, content in BAD_TEMPLATES.items():
            i += 1
            print(f"[{i:>2}/{n_total}] judging pr{pr_id} bad-{tag} ...")
            ev = evaluate_bad_review(pr_id, tag)
            bad_evals.append({
                "pr_id": pr_id, "mode": f"bad-{tag}",
                "total_score": ev.total_score, "percentage": ev.percentage,
                "kg_relevant_score": ev.kg_relevant_score,
                "kg_relevant_percentage": ev.kg_relevant_percentage,
                "criteria_scores": ev.criteria_scores,
            })

    # Existing scores
    existing = load_existing_baseline_scores()

    # Aggregate per-style mean and per-PR pairs
    by_style: dict[str, list[int]] = {tag: [] for tag in BAD_TEMPLATES}
    by_style_kg: dict[str, list[int]] = {tag: [] for tag in BAD_TEMPLATES}
    for e in bad_evals:
        tag = e["mode"].removeprefix("bad-")
        by_style[tag].append(e["total_score"])
        by_style_kg[tag].append(e["kg_relevant_score"])

    baseline_totals = [existing[p]["baseline"] for p in TEST_PRS if "baseline" in existing.get(p, {})]
    hybrid_totals   = [existing[p]["hybrid"] for p in TEST_PRS if "hybrid" in existing.get(p, {})]

    # Paired diffs: bad - baseline (per PR), per style
    style_p = {}
    for tag in BAD_TEMPLATES:
        diffs = []
        for pr_id in TEST_PRS:
            if pr_id not in existing or "baseline" not in existing[pr_id]:
                continue
            bad_score = next(e["total_score"] for e in bad_evals
                             if e["pr_id"] == pr_id and e["mode"] == f"bad-{tag}")
            diffs.append(bad_score - existing[pr_id]["baseline"])
        style_p[tag] = {
            "n_pairs": len(diffs),
            "mean_diff_vs_baseline": round(sum(diffs)/len(diffs), 2) if diffs else None,
            "p_perm": round(paired_permutation_p(diffs), 4) if diffs else None,
        }

    summary = {
        "test_prs": TEST_PRS,
        "n_per_style": len(TEST_PRS),
        "bad_means_total": {tag: round(sum(v)/len(v), 2) for tag, v in by_style.items()},
        "bad_means_kg":    {tag: round(sum(v)/len(v), 2) for tag, v in by_style_kg.items()},
        "baseline_mean_total": round(sum(baseline_totals)/len(baseline_totals), 2) if baseline_totals else None,
        "hybrid_mean_total":   round(sum(hybrid_totals)/len(hybrid_totals), 2) if hybrid_totals else None,
        "paired_diffs_vs_baseline": style_p,
        "evals": bad_evals,
    }

    out_json = REPO_ROOT / "results" / "RUBRIC_POSITIVE_CONTROL.json"
    out_md   = REPO_ROOT / "results" / "RUBRIC_POSITIVE_CONTROL.md"
    out_json.write_text(json.dumps(summary, indent=2))

    md = []
    md.append("# Rubric positive control")
    md.append("")
    md.append("**Hypothesis.** The 25-criterion rubric is a discriminative instrument: "
              "deliberately poor reviews should score significantly *lower* than real "
              "baseline reviews on the same PRs.")
    md.append("")
    md.append(f"**Test set.** PRs {TEST_PRS} (5 PRs across 5 repos / 5 languages).")
    md.append(f"**Bad-review styles (n=5):** {', '.join(BAD_TEMPLATES.keys())}.")
    md.append(f"**Reference reviews:** the canonical gpt-4o `baseline` reviews on the same PRs (already judged).")
    md.append(f"**Judge panel:** {', '.join(JUDGES)} (majority vote, identical to main study).")
    md.append("")
    md.append("## Mean total score (out of 25)")
    md.append("")
    md.append("| Mode | Mean total | Mean KG-relevant (out of 9) |")
    md.append("|---|---:|---:|")
    for tag in BAD_TEMPLATES:
        md.append(f"| bad-{tag} | {summary['bad_means_total'][tag]} | {summary['bad_means_kg'][tag]} |")
    md.append(f"| **baseline** (existing) | **{summary['baseline_mean_total']}** | — |")
    md.append(f"| hybrid (existing, ref.) | {summary['hybrid_mean_total']} | — |")
    md.append("")
    md.append("## Paired permutation tests (bad − baseline, same PR)")
    md.append("")
    md.append("| Bad style | n pairs | Mean Δ (bad − baseline) | p (permutation, two-sided) |")
    md.append("|---|---:|---:|---:|")
    for tag, st in style_p.items():
        md.append(f"| bad-{tag} | {st['n_pairs']} | {st['mean_diff_vs_baseline']:+.2f} | {st['p_perm']} |")
    md.append("")
    md.append("## Interpretation")
    md.append("")
    md.append("If every bad style scores lower than baseline with mean Δ < 0 and p < 0.05, "
              "the rubric demonstrably discriminates poor reviews from real ones — "
              "establishing it as a meaningful measurement instrument. This is the methods-"
              "section sanity check that prevents the objection: *'how do we know your rubric "
              "measures anything?'*")
    out_md.write_text("\n".join(md) + "\n")

    print(f"\nwrote {out_json.relative_to(REPO_ROOT)}")
    print(f"wrote {out_md.relative_to(REPO_ROOT)}")
    print()
    print("=== Summary ===")
    for tag in BAD_TEMPLATES:
        st = style_p[tag]
        print(f"  bad-{tag:<14} mean_total={summary['bad_means_total'][tag]:>5.2f}   "
              f"Δ vs baseline = {st['mean_diff_vs_baseline']:+.2f}   p={st['p_perm']}")
    print(f"  baseline (existing) mean_total = {summary['baseline_mean_total']}")
    print(f"  hybrid   (existing) mean_total = {summary['hybrid_mean_total']}")


if __name__ == "__main__":
    main()
