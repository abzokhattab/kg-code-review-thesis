#!/usr/bin/env python3
"""Consolidate the independent Experiment 1/2 judge-panel sensitivities."""
from __future__ import annotations

import itertools
import json
import math
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP1 = ROOT / "experiments/2026-09-19_independent_judges/RESULTS_EXP1.json"
LOCALISATION = (
    ROOT
    / "experiments/2026-09-19_independent_judges/CRITERION_CONCENTRATION.json"
)
EXP2 = ROOT / "experiments/2026-09-19_exp2_rejudge_v2/RESULTS_INDEPENDENT.json"
OUT_JSON = ROOT / "results/INDEPENDENT_JUDGE_PANELS.json"
OUT_MD = ROOT / "results/INDEPENDENT_JUDGE_PANELS.md"
BUNDLE_MD = ROOT / "thesis-context/results/INDEPENDENT_JUDGE_PANELS.md"


def cohen_kappa(left: list[int], right: list[int]) -> float:
    n = len(left)
    observed = sum(a == b for a, b in zip(left, right)) / n
    p_left = sum(left) / n
    p_right = sum(right) / n
    expected = p_left * p_right + (1 - p_left) * (1 - p_right)
    return (observed - expected) / (1 - expected) if expected < 1 else 1.0


def exact_mcnemar(a_wins: int, b_wins: int) -> float:
    discordant = a_wins + b_wins
    if discordant == 0:
        return 1.0
    smaller = min(a_wins, b_wins)
    tail = sum(math.comb(discordant, i) for i in range(smaller + 1))
    return min(1.0, 2 * tail / (2**discordant))


def wilson(successes: int, n: int, z: float = 1.959963984540054) -> list[float]:
    p = successes / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = (
        z
        * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
        / denominator
    )
    return [max(0.0, center - half), min(1.0, center + half)]


def exp1_agreement(data: dict) -> dict:
    output = {}
    for first, second in itertools.combinations(data["panel"], 2):
        left, right = [], []
        for evaluation in data["evaluations"]:
            for criterion in evaluation["panel_scores"]:
                left.append(evaluation["per_judge"][first][criterion])
                right.append(evaluation["per_judge"][second][criterion])
        output[f"{first}__{second}"] = {
            "kappa": cohen_kappa(left, right),
            "raw_agreement": sum(a == b for a, b in zip(left, right)) / len(left),
            "n_cells": len(left),
        }
    return output


def exp2_analysis(data: dict) -> dict:
    rows = {
        (row["case_id"], row["arm"]): bool(row["majority_detected"])
        for row in data["rows"]
    }
    case_cohort = {
        row["case_id"]: row["cohort"] for row in data["rows"]
    }
    arms = data["arms"]
    rates = {}
    contrasts = {}
    for cohort in ("structural", "local"):
        case_ids = sorted(
            case_id for case_id, value in case_cohort.items() if value == cohort
        )
        rates[cohort] = {}
        for arm in arms:
            detected = sum(rows[(case_id, arm)] for case_id in case_ids)
            rates[cohort][arm] = {
                "n": len(case_ids),
                "detected": detected,
                "rate": detected / len(case_ids),
                "wilson95": wilson(detected, len(case_ids)),
            }
        comparisons = [
            ("kg", "baseline"),
            ("rag", "baseline"),
            ("hybrid", "baseline"),
            ("hybrid", "kg"),
            ("kg_joern_inherit", "kg"),
            ("kg_idealised", "kg"),
            ("kg_deps_only", "baseline"),
            ("kg_edges_only", "baseline"),
        ]
        contrasts[cohort] = {}
        for treatment, control in comparisons:
            treatment_wins = sum(
                rows[(case_id, treatment)] and not rows[(case_id, control)]
                for case_id in case_ids
            )
            control_wins = sum(
                rows[(case_id, control)] and not rows[(case_id, treatment)]
                for case_id in case_ids
            )
            contrasts[cohort][f"{treatment}_vs_{control}"] = {
                "treatment_wins": treatment_wins,
                "control_wins": control_wins,
                "delta": (
                    rates[cohort][treatment]["rate"]
                    - rates[cohort][control]["rate"]
                ),
                "p_exact_mcnemar": exact_mcnemar(treatment_wins, control_wins),
            }
    return {"rates": rates, "contrasts": contrasts}


def main() -> None:
    exp1 = json.loads(EXP1.read_text())
    localisation = json.loads(LOCALISATION.read_text())
    exp2 = json.loads(EXP2.read_text())
    agreement = exp1_agreement(exp1)
    exp2_stats = exp2_analysis(exp2)

    payload = {
        "status": "post-hoc-provider-independence-sensitivity",
        "panel": exp1["panel"],
        "exp1": {
            "means": exp1["means"],
            "contrasts": exp1["contrasts"],
            "criterion_localisation": localisation["modes"],
            "agreement": agreement,
        },
        "exp2": exp2_stats,
        "source_files": [
            str(EXP1.relative_to(ROOT)),
            str(LOCALISATION.relative_to(ROOT)),
            str(EXP2.relative_to(ROOT)),
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    exp1_kg = exp1["contrasts"]["kg"]
    exp1_rag = exp1["contrasts"]["rag"]
    exp1_hybrid = exp1["contrasts"]["hybrid"]
    loc = localisation["modes"]["kg"]
    structural = exp2_stats["rates"]["structural"]
    exp2_contrasts = exp2_stats["contrasts"]["structural"]

    lines = [
        "# Independent judge panels — Experiments 1 and 2",
        "",
        "**Status:** post-hoc provider-independence sensitivity. Frozen reviews; "
        "no review regeneration.",
        "",
        "Panel: " + ", ".join(f"`{model}`" for model in exp1["panel"]),
        "",
        "## Experiment 1",
        "",
        "| Mode | Total delta [95% CI] | p | KG-relevant delta [95% CI] | p |",
        "|---|---:|---:|---:|---:|",
    ]
    for mode, result in (
        ("kg", exp1_kg),
        ("rag", exp1_rag),
        ("hybrid", exp1_hybrid),
    ):
        total = result["total"]
        kg = result["kg_relevant"]
        lines.append(
            f"| `{mode}` | {total['delta']:+.2f} "
            f"[{total['ci95'][0]:+.2f}, {total['ci95'][1]:+.2f}] | "
            f"{total['p_permutation']:.4f} | {kg['delta']:+.2f} "
            f"[{kg['ci95'][0]:+.2f}, {kg['ci95'][1]:+.2f}] | "
            f"{kg['p_permutation']:.4f} |"
        )
    lines.extend(
        [
            "",
            f"KG localisation: {loc['gain_in_target']:+.3f} points in the nine "
            f"pre-specified criteria against {loc['gain_elsewhere']:+.3f} in the "
            f"other sixteen (criterion-subset permutation "
            f"p={loc['p_concentration']:.4f}).",
            "",
            "Inter-judge agreement:",
            "",
        ]
    )
    for pair, row in agreement.items():
        lines.append(
            f"- `{pair.replace('__', ' ↔ ')}`: kappa={row['kappa']:.3f}, "
            f"raw agreement={row['raw_agreement']:.1%}"
        )

    lines.extend(
        [
            "",
            "## Experiment 2 — structural injections",
            "",
            "| Arm | Detected | Rate [Wilson 95% CI] |",
            "|---|---:|---:|",
        ]
    )
    for arm in (
        "baseline",
        "rag",
        "kg",
        "hybrid",
        "kg_joern_inherit",
        "kg_idealised",
        "kg_deps_only",
        "kg_edges_only",
    ):
        row = structural[arm]
        lines.append(
            f"| `{arm}` | {row['detected']}/{row['n']} | "
            f"{row['rate']:.2f} [{row['wilson95'][0]:.2f}, "
            f"{row['wilson95'][1]:.2f}] |"
        )
    lines.extend(
        [
            "",
            "Key paired contrasts (exact McNemar):",
            "",
        ]
    )
    for key in (
        "kg_vs_baseline",
        "rag_vs_baseline",
        "hybrid_vs_baseline",
        "hybrid_vs_kg",
        "kg_joern_inherit_vs_kg",
    ):
        row = exp2_contrasts[key]
        lines.append(
            f"- `{key}`: delta={row['delta']:+.3f}, "
            f"wins/losses={row['treatment_wins']}/{row['control_wins']}, "
            f"p={row['p_exact_mcnemar']:.4g}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The independent panel reproduces the targeted Experiment 1 KG effect "
            "without any OpenAI judge and preserves the mechanism separation: KG "
            "is significant on the KG-relevant subscale, while RAG leads total "
            "coverage. Experiment 2 independently reproduces the corrected ordering "
            "(hybrid 21/28, KG 18/28) and rejects the earlier claim that hybrid is "
            "lower because of context dilution.",
            "",
            "These analyses are post-hoc and must be reported beside the historical "
            "panels rather than described as pre-registered.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines))
    BUNDLE_MD.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(OUT_MD, BUNDLE_MD)
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(f"copied {BUNDLE_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
