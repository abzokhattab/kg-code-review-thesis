#!/usr/bin/env python3
"""Assemble 5-judge panel for the Joern-unified Experiment 1 (n=35).

KG mode:  gpt-4o + gemini from old 3-judge Joern scores,
          claude-sonnet-4.5 + deepseek-v4-pro + grok-4.6 from new independent cache.
Baseline/RAG/Hybrid: subset from existing 5-judge panel data (already scored on 40 PRs).

No API calls — pure offline aggregation.
"""
from __future__ import annotations

import itertools
import json
import math
import random
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

# Old 3-judge Joern KG scores (gpt-4o-mini, gpt-4o, gemini)
JOERN_SCORES_DIR = ROOT / "experiments/2026-09-19_joern_replace_grep/scores"

# New independent judge cache (claude, deepseek, grok)
JOERN_CACHE_DIR = (
    ROOT / "experiments/2026-09-19_joern_replace_grep/reviews/.judge_cache"
    "/joern_kg_independent"
    "/anthropic-claude-sonnet-4-5_deepseek-deepseek-v4-pro_xai-grok-4.6"
)

# Existing 5-judge panel for baseline/rag/hybrid (n=40)
FIVE_JUDGE_PANEL = ROOT / "results/FIVE_JUDGE_PANEL.json"

# Criteria definitions from the existing panel
CRITERIA_SOURCE = FIVE_JUDGE_PANEL

# Output paths
OUT_DIR = ROOT / "experiments/2026-10-04_joern_unified_five_judge"
OUT_JSON = OUT_DIR / "RESULTS.json"
OUT_MD = OUT_DIR / "RESULTS.md"
RESULT_JSON = ROOT / "results/JOERN_UNIFIED_FIVE_JUDGE.json"
RESULT_MD = ROOT / "results/JOERN_UNIFIED_FIVE_JUDGE.md"

PANEL = [
    "openai:gpt-4o",
    "gemini:gemini-2.5-flash",
    "anthropic:claude-sonnet-4-5",
    "deepseek:deepseek-v4-pro",
    "xai:grok-4.6",
]
MAJORITY = 3
SEED = 2026
B_BOOT = 10_000
B_PERM = 20_000
B_CRITERIA = 200_000

JOERN_PR_IDS = {
    1, 2, 3, 6, 8, 10, 12, 13, 14, 15, 18, 19, 20, 21, 22, 23, 24,
    28, 29, 30, 31, 32, 33, 34, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48,
}
assert len(JOERN_PR_IDS) == 35


def majority(votes: list[int]) -> int:
    valid = [v for v in votes if v >= 0]
    if len(valid) < 4:
        return 0
    return 1 if sum(valid) >= MAJORITY else 0


def bootstrap_ci(
    values: list[float], seed: int, B: int = B_BOOT
) -> list[float]:
    rng = random.Random(seed)
    n = len(values)
    means = sorted(
        statistics.fmean(rng.choices(values, k=n)) for _ in range(B)
    )
    lo = means[int(B * 0.025)]
    hi = means[int(B * 0.975)]
    return [lo, hi]


def permutation_p(
    differences: list[float], seed: int, B: int = B_PERM
) -> float:
    observed = abs(statistics.fmean(differences))
    rng = random.Random(seed)
    n = len(differences)
    hits = 0
    for _ in range(B):
        flipped = [d * rng.choice((-1, 1)) for d in differences]
        if abs(statistics.fmean(flipped)) >= observed - 1e-12:
            hits += 1
    return (hits + 1) / (B + 1)


def cohens_dz(values: list[float]) -> float:
    sd = statistics.stdev(values)
    return statistics.fmean(values) / sd if sd else 0.0


def cohen_kappa(a: list[int], b: list[int]) -> dict[str, Any]:
    pairs = [(x, y) for x, y in zip(a, b) if x >= 0 and y >= 0]
    n_cells = len(pairs)
    if n_cells == 0:
        return {"n_cells": 0, "raw_agreement": 0, "kappa": 0}
    agree = sum(x == y for x, y in pairs)
    raw = agree / n_cells
    p_a1 = sum(x for x, _ in pairs) / n_cells
    p_b1 = sum(y for _, y in pairs) / n_cells
    pe = p_a1 * p_b1 + (1 - p_a1) * (1 - p_b1)
    kappa = (raw - pe) / (1 - pe) if pe < 1 else 0.0
    return {"n_cells": n_cells, "raw_agreement": raw, "kappa": kappa}


def load_joern_kg_per_judge() -> dict[int, dict[str, dict[str, int]]]:
    """Load per-judge per-criterion scores for Joern KG reviews.

    Returns {pr_id: {judge_model: {criterion_id: 0|1}}}.
    Merges gpt-4o + gemini from old scores, claude + deepseek + grok from new cache.
    """
    result = {}
    for pr_id in sorted(JOERN_PR_IDS):
        old_path = JOERN_SCORES_DIR / f"pr{pr_id}_kg.json"
        new_path = JOERN_CACHE_DIR / f"pr{pr_id}_kg.json"
        if not old_path.exists():
            raise FileNotFoundError(f"Missing old score: {old_path}")
        if not new_path.exists():
            raise FileNotFoundError(f"Missing new score: {new_path}")

        old = json.loads(old_path.read_text())
        new = json.loads(new_path.read_text())

        per_judge: dict[str, dict[str, int]] = {}

        # Extract gpt-4o and gemini from old 3-judge scores
        for pj in old["per_judge"]:
            model = pj["model"]
            if model in ("openai:gpt-4o", "gemini:gemini-2.5-flash"):
                per_judge[model] = {k: int(v) for k, v in pj["scores"].items()}

        # Extract claude, deepseek, grok from new independent cache
        for pj in new["per_judge"]:
            model = pj["model"]
            if model in (
                "anthropic:claude-sonnet-4-5",
                "deepseek:deepseek-v4-pro",
                "xai:grok-4.6",
            ):
                per_judge[model] = {k: int(v) for k, v in pj["scores"].items()}

        if len(per_judge) != 5:
            raise ValueError(
                f"PR {pr_id}: expected 5 judges, got {len(per_judge)}: "
                f"{list(per_judge.keys())}"
            )
        result[pr_id] = per_judge
    return result


def load_existing_panel_subset() -> (
    tuple[dict[str, Any], dict[tuple[int, str], dict[str, dict[str, int]]]]
):
    """Load baseline/rag/hybrid per-judge scores from existing 5-judge panel, subset to 35 PRs.

    Returns (criteria_definitions_dict, {(pr_id, mode): {judge: {criterion: score}}}).
    """
    panel = json.loads(FIVE_JUDGE_PANEL.read_text())
    definitions = {
        row["id"]: row for row in panel["experiment1"]["criteria_definitions"]
    }
    subset = {}
    for ev in panel["experiment1"]["evaluations"]:
        pr_id = ev["pr_id"]
        mode = ev["mode"]
        if pr_id not in JOERN_PR_IDS:
            continue
        if mode in ("baseline", "rag", "hybrid"):
            subset[(pr_id, mode)] = ev["per_judge"]
    return definitions, subset


def run() -> dict[str, Any]:
    print("Loading Joern KG per-judge scores...")
    kg_judges = load_joern_kg_per_judge()

    print("Loading existing 5-judge panel for baseline/rag/hybrid (n=35)...")
    definitions, other_modes = load_existing_panel_subset()
    ids = list(definitions)
    kg_ids = {key for key, row in definitions.items() if row["kg_relevant"]}

    evaluations = []

    # KG evaluations from Joern
    for pr_id in sorted(JOERN_PR_IDS):
        per_judge = kg_judges[pr_id]
        scores = {
            criterion: majority(
                [per_judge[judge][criterion] for judge in PANEL]
            )
            for criterion in ids
        }
        evaluations.append({
            "pr_id": pr_id,
            "mode": "kg",
            "total": sum(scores.values()),
            "kg_relevant": sum(scores[c] for c in kg_ids),
            "scores": scores,
            "per_judge": per_judge,
        })

    # Baseline/RAG/Hybrid from existing panel, subset
    for (pr_id, mode), per_judge in sorted(other_modes.items()):
        scores = {
            criterion: majority(
                [per_judge[judge][criterion] for judge in PANEL]
            )
            for criterion in ids
        }
        evaluations.append({
            "pr_id": pr_id,
            "mode": mode,
            "total": sum(scores.values()),
            "kg_relevant": sum(scores[c] for c in kg_ids),
            "scores": scores,
            "per_judge": per_judge,
        })

    by_mode = {
        mode: {row["pr_id"]: row for row in evaluations if row["mode"] == mode}
        for mode in ("baseline", "kg", "rag", "hybrid")
    }

    # Per-mode summary stats
    modes = {}
    for mode, rows in by_mode.items():
        total_values = [row["total"] for row in rows.values()]
        kg_values = [row["kg_relevant"] for row in rows.values()]
        modes[mode] = {
            "n": len(rows),
            "mean_total": statistics.fmean(total_values),
            "total_ci95": bootstrap_ci(total_values, SEED),
            "mean_kg_relevant": statistics.fmean(kg_values),
            "kg_relevant_ci95": bootstrap_ci(kg_values, SEED),
        }
        if mode == "baseline":
            continue
        shared = sorted(set(rows) & set(by_mode["baseline"]))
        for metric in ("total", "kg_relevant"):
            differences = [
                rows[pr_id][metric] - by_mode["baseline"][pr_id][metric]
                for pr_id in shared
            ]
            modes[mode][metric + "_contrast"] = {
                "delta": statistics.fmean(differences),
                "ci95": bootstrap_ci(differences, SEED),
                "p_permutation": permutation_p(differences, SEED),
                "cohens_dz": cohens_dz(differences),
            }

    # Criterion localisation
    baseline_rates = {
        criterion: statistics.fmean(
            row["scores"][criterion] for row in by_mode["baseline"].values()
        )
        for criterion in ids
    }
    localisation = {}
    for mode in ("kg", "rag", "hybrid"):
        mode_rates = {
            criterion: statistics.fmean(
                row["scores"][criterion] for row in by_mode[mode].values()
            )
            for criterion in ids
        }
        delta = {
            criterion: mode_rates[criterion] - baseline_rates[criterion]
            for criterion in ids
        }
        observed = sum(delta[item] for item in kg_ids)
        total = sum(delta.values())
        rng = random.Random(SEED)
        hits = sum(
            sum(delta[item] for item in rng.sample(ids, len(kg_ids)))
            >= observed - 1e-12
            for _ in range(B_CRITERIA)
        )
        localisation[mode] = {
            "gain_target": observed,
            "gain_other": total - observed,
            "gain_total": total,
            "share": observed / total if total else None,
            "p_criterion_permutation": hits / B_CRITERIA,
        }

    # Abstentions
    abstentions = {
        judge: sum(
            score == -1
            for evaluation in evaluations
            for score in evaluation["per_judge"][judge].values()
        )
        for judge in PANEL
    }

    # Pairwise agreement
    agreement = {}
    for first, second in itertools.combinations(PANEL, 2):
        left, right = [], []
        for evaluation in evaluations:
            for criterion in ids:
                left.append(evaluation["per_judge"][first][criterion])
                right.append(evaluation["per_judge"][second][criterion])
        agreement[f"{first}__{second}"] = cohen_kappa(left, right)

    # Individual judge sensitivity for KG contrast
    individual_judges = {}
    for judge in PANEL:
        differences = []
        for pr_id in sorted(by_mode["baseline"]):
            baseline_score = sum(
                by_mode["baseline"][pr_id]["per_judge"][judge][item]
                for item in kg_ids
            )
            kg_score = sum(
                by_mode["kg"][pr_id]["per_judge"][judge][item]
                for item in kg_ids
            )
            differences.append(kg_score - baseline_score)
        individual_judges[judge] = {
            "delta": statistics.fmean(differences),
            "ci95": bootstrap_ci(differences, SEED),
            "p_permutation": permutation_p(differences, SEED),
            "cohens_dz": cohens_dz(differences),
        }

    # Criterion-level win/loss counts
    criterion_wl = {}
    for mode in ("kg", "rag", "hybrid"):
        kg_wins, kg_losses = 0, 0
        other_wins, other_losses = 0, 0
        for pr_id in sorted(by_mode["baseline"]):
            for criterion in ids:
                b = by_mode["baseline"][pr_id]["scores"][criterion]
                m = by_mode[mode][pr_id]["scores"][criterion]
                if criterion in kg_ids:
                    if m > b:
                        kg_wins += 1
                    elif m < b:
                        kg_losses += 1
                else:
                    if m > b:
                        other_wins += 1
                    elif m < b:
                        other_losses += 1
        criterion_wl[mode] = {
            "kg_wins": kg_wins,
            "kg_losses": kg_losses,
            "kg_net": kg_wins - kg_losses,
            "other_wins": other_wins,
            "other_losses": other_losses,
            "other_net": other_wins - other_losses,
        }

    return {
        "criteria_definitions": list(definitions.values()),
        "evaluations": evaluations,
        "modes": modes,
        "localisation": localisation,
        "abstentions": abstentions,
        "agreement": agreement,
        "individual_judges": individual_judges,
        "criterion_wl": criterion_wl,
    }


def markdown(result: dict) -> str:
    lines = [
        "# Joern-unified five-judge aggregation — Experiment 1 (n=35)",
        "",
        "Panel: " + ", ".join(f"`{j}`" for j in PANEL),
        "",
        "Aggregation: strict majority of valid votes (3/5; 3/4 when one "
        "judge abstains). gpt-4o-mini excluded.",
        "",
        "KG mode: Joern CPG reviews (35 PRs, 5 Go-only PRs excluded).",
        "Baseline/RAG/Hybrid: subset from existing 5-judge panel.",
        "",
        "## Paired Comparisons",
        "",
        "| Mode | n | Mean total /25 [95% CI] | Delta [95% CI], p, d_z "
        "| Mean KG /9 [95% CI] | Delta [95% CI], p, d_z |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for mode in ("baseline", "kg", "rag", "hybrid"):
        row = result["modes"][mode]
        if mode == "baseline":
            tc = "—"
            kc = "—"
        else:
            t = row["total_contrast"]
            k = row["kg_relevant_contrast"]
            tc = (
                f"{t['delta']:+.2f} [{t['ci95'][0]:+.2f}, {t['ci95'][1]:+.2f}]"
                f", p={t['p_permutation']:.4f}, d_z={t['cohens_dz']:+.2f}"
            )
            kc = (
                f"{k['delta']:+.2f} [{k['ci95'][0]:+.2f}, {k['ci95'][1]:+.2f}]"
                f", p={k['p_permutation']:.4f}, d_z={k['cohens_dz']:+.2f}"
            )
        lines.append(
            f"| `{mode}` | {row['n']} | {row['mean_total']:.2f} "
            f"[{row['total_ci95'][0]:.2f}, {row['total_ci95'][1]:.2f}] | "
            f"{tc} | {row['mean_kg_relevant']:.2f} "
            f"[{row['kg_relevant_ci95'][0]:.2f}, "
            f"{row['kg_relevant_ci95'][1]:.2f}] | {kc} |"
        )

    lines.extend(["", "## Criterion-Level Win/Loss Counts", ""])
    lines.append(
        "| Mode | KG-relevant (9): W / L / net | Other (16): W / L / net |"
    )
    lines.append("|---|---:|---:|")
    for mode in ("kg", "rag", "hybrid"):
        wl = result["criterion_wl"][mode]
        lines.append(
            f"| `{mode}` | {wl['kg_wins']} / {wl['kg_losses']} / "
            f"{wl['kg_net']:+d} | {wl['other_wins']} / {wl['other_losses']}"
            f" / {wl['other_net']:+d} |"
        )

    lines.extend(["", "## Criterion Localisation", ""])
    for mode in ("kg", "rag", "hybrid"):
        loc = result["localisation"][mode]
        share = f"{loc['share'] * 100:.1f}%" if loc["share"] is not None else "N/A"
        lines.append(
            f"- `{mode}`: target gain {loc['gain_target']:+.3f}, "
            f"other {loc['gain_other']:+.3f}, share {share}, "
            f"p={loc['p_criterion_permutation']:.4f}"
        )

    lines.extend([
        "",
        "## Single-Judge Sensitivity (KG-relevant contrast)",
        "",
        "| Judge | Delta /9 | 95% CI | p | d_z |",
        "|---|---:|---:|---:|---:|",
    ])
    for judge in PANEL:
        row = result["individual_judges"][judge]
        lines.append(
            f"| `{judge}` | {row['delta']:+.3f} | "
            f"[{row['ci95'][0]:+.3f}, {row['ci95'][1]:+.3f}] | "
            f"{row['p_permutation']:.4f} | {row['cohens_dz']:+.2f} |"
        )

    lines.extend([
        "",
        "## Inter-Judge Agreement",
        "",
        "| Judge pair | Valid cells | Raw agreement | Cohen's kappa |",
        "|---|---:|---:|---:|",
    ])
    for pair, row in result["agreement"].items():
        first, second = pair.split("__", maxsplit=1)
        lines.append(
            f"| `{first}` / `{second}` | {row['n_cells']} | "
            f"{row['raw_agreement']:.1%} | {row['kappa']:.3f} |"
        )

    lines.extend([
        "",
        f"Gemini abstained on {result['abstentions']['gemini:gemini-2.5-flash']}"
        " criterion cells.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    result = run()
    payload = {
        "status": "joern-unified-five-judge-aggregation",
        "panel": PANEL,
        "majority_threshold": MAJORITY,
        "n": 35,
        "excluded_pr_ids": sorted(set(range(1, 49)) - JOERN_PR_IDS),
        "experiment1": result,
    }
    json_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    md_text = markdown(result)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json_text)
    OUT_MD.write_text(md_text)
    RESULT_JSON.write_text(json_text)
    RESULT_MD.write_text(md_text)
    print(f"Wrote {OUT_MD.relative_to(ROOT)}")
    print(f"Wrote {RESULT_MD.relative_to(ROOT)}")

    # Print headline
    modes = result["modes"]
    kg = modes["kg"]["kg_relevant_contrast"]
    print(f"\n=== HEADLINE (Joern-unified, n=35, 5-judge) ===")
    print(
        f"KG-relevant: {kg['delta']:+.2f} "
        f"[{kg['ci95'][0]:+.2f}, {kg['ci95'][1]:+.2f}], "
        f"p={kg['p_permutation']:.4f}, d_z={kg['cohens_dz']:+.2f}"
    )
    total = modes["kg"]["total_contrast"]
    print(
        f"Total:        {total['delta']:+.2f} "
        f"[{total['ci95'][0]:+.2f}, {total['ci95'][1]:+.2f}], "
        f"p={total['p_permutation']:.4f}, d_z={total['cohens_dz']:+.2f}"
    )
    loc = result["localisation"]["kg"]
    share = f"{loc['share'] * 100:.1f}%" if loc["share"] else "N/A"
    print(f"Localisation: {share}, p={loc['p_criterion_permutation']:.4f}")


if __name__ == "__main__":
    main()
