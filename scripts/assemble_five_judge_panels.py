#!/usr/bin/env python3
"""Aggregate one final five-judge panel across Experiments 1 and 2."""
from __future__ import annotations

import itertools
import json
import math
import random
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/2026-09-23_five_judge_panel"
OUT_JSON = EXP / "RESULTS.json"
OUT_MD = EXP / "RESULTS.md"
RESULT_JSON = ROOT / "results/FIVE_JUDGE_PANEL.json"
RESULT_MD = ROOT / "results/FIVE_JUDGE_PANEL.md"
BUNDLE_JSON = ROOT / "thesis-context/results/FIVE_JUDGE_PANEL.json"
BUNDLE_MD = ROOT / "thesis-context/results/FIVE_JUDGE_PANEL.md"

OLD_EXP1 = ROOT / "results/checklist_evaluation_llm_multi__v2.json"
NEW_EXP1 = (
    ROOT / "experiments/2026-09-19_independent_judges/RESULTS_EXP1.json"
)
OLD_EXP2 = ROOT / "experiments/2026-09-19_exp2_rejudge_v2/RESULTS_V3.json"
NEW_EXP2 = (
    ROOT
    / "experiments/2026-09-19_exp2_rejudge_v2/RESULTS_INDEPENDENT.json"
)

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


def majority(votes: list[int | bool]) -> int:
    if len(votes) != 5 or any(
        vote not in (-1, 0, 1, False, True) for vote in votes
    ):
        raise ValueError(f"invalid five-judge votes: {votes}")
    valid = [int(vote) for vote in votes if vote in (0, 1, False, True)]
    if len(valid) < 4:
        raise ValueError(f"fewer than four valid judge votes: {votes}")
    return int(sum(valid) * 2 > len(valid))


def cohen_kappa(left: list[int], right: list[int]) -> dict[str, float | int]:
    pairs = [
        (first, second)
        for first, second in zip(left, right)
        if first in (0, 1) and second in (0, 1)
    ]
    if not pairs:
        raise ValueError("no shared valid votes for agreement calculation")
    n = len(pairs)
    observed = sum(first == second for first, second in pairs) / n
    p_left = sum(first for first, _ in pairs) / n
    p_right = sum(second for _, second in pairs) / n
    expected = p_left * p_right + (1 - p_left) * (1 - p_right)
    kappa = (observed - expected) / (1 - expected) if expected < 1 else 1.0
    return {
        "n_cells": n,
        "raw_agreement": observed,
        "kappa": kappa,
    }


def bootstrap_ci(values: list[float], seed: int) -> list[float]:
    rng = random.Random(seed)
    n = len(values)
    means = sorted(
        statistics.fmean(values[rng.randrange(n)] for _ in range(n))
        for _ in range(B_BOOT)
    )
    return [means[int(0.025 * B_BOOT)], means[int(0.975 * B_BOOT) - 1]]


def permutation_p(values: list[float], seed: int) -> float:
    observed = abs(statistics.fmean(values))
    if observed == 0:
        return 1.0
    rng = random.Random(seed)
    hits = 0
    for _ in range(B_PERM):
        trial = abs(
            statistics.fmean(rng.choice((-1, 1)) * value for value in values)
        )
        hits += trial >= observed - 1e-12
    return (hits + 1) / (B_PERM + 1)


def cohens_dz(values: list[float]) -> float:
    sd = statistics.stdev(values)
    return statistics.fmean(values) / sd if sd else 0.0


def wilson(successes: int, n: int) -> list[float]:
    z = 1.959963984540054
    p = successes / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = (
        z
        * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
        / denominator
    )
    return [max(0.0, center - half), min(1.0, center + half)]


def exact_mcnemar(treatment_wins: int, control_wins: int) -> float:
    discordant = treatment_wins + control_wins
    if discordant == 0:
        return 1.0
    smaller = min(treatment_wins, control_wins)
    tail = sum(math.comb(discordant, index) for index in range(smaller + 1))
    return min(1.0, 2 * tail / (2**discordant))


def exp1() -> dict[str, Any]:
    old = json.loads(OLD_EXP1.read_text())
    new = json.loads(NEW_EXP1.read_text())
    old_lookup = {
        (row["pr_id"], row["mode"]): {
            judge["model"]: {
                key: int(value) for key, value in judge["scores"].items()
            }
            for judge in row["per_judge"]
        }
        for row in old["evaluations"]
    }
    new_lookup = {
        (row["pr_id"], row["mode"]): row["per_judge"]
        for row in new["evaluations"]
    }
    definitions = {row["id"]: row for row in new["criteria_definitions"]}
    ids = list(definitions)
    kg_ids = {key for key, row in definitions.items() if row["kg_relevant"]}

    evaluations = []
    for key in sorted(old_lookup):
        per_judge = {
            PANEL[0]: old_lookup[key][PANEL[0]],
            PANEL[1]: old_lookup[key][PANEL[1]],
            PANEL[2]: new_lookup[key][PANEL[2]],
            PANEL[3]: new_lookup[key][PANEL[3]],
            PANEL[4]: new_lookup[key][PANEL[4]],
        }
        scores = {
            criterion: majority(
                [per_judge[judge][criterion] for judge in PANEL]
            )
            for criterion in ids
        }
        evaluations.append(
            {
                "pr_id": key[0],
                "mode": key[1],
                "total": sum(scores.values()),
                "kg_relevant": sum(scores[item] for item in kg_ids),
                "scores": scores,
                "per_judge": per_judge,
            }
        )

    by_mode = {
        mode: {row["pr_id"]: row for row in evaluations if row["mode"] == mode}
        for mode in ("baseline", "kg", "rag", "hybrid")
    }
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
    abstentions = {
        judge: sum(
            score == -1
            for evaluation in evaluations
            for score in evaluation["per_judge"][judge].values()
        )
        for judge in PANEL
    }
    agreement = {}
    for first, second in itertools.combinations(PANEL, 2):
        left, right = [], []
        for evaluation in evaluations:
            for criterion in ids:
                left.append(evaluation["per_judge"][first][criterion])
                right.append(evaluation["per_judge"][second][criterion])
        agreement[f"{first}__{second}"] = cohen_kappa(left, right)

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
    return {
        "criteria_definitions": list(definitions.values()),
        "evaluations": evaluations,
        "modes": modes,
        "localisation": localisation,
        "abstentions": abstentions,
        "agreement": agreement,
        "individual_judges": individual_judges,
    }


def exp2() -> dict[str, Any]:
    old = json.loads(OLD_EXP2.read_text())
    new = json.loads(NEW_EXP2.read_text())
    old_lookup = {
        (row["case_id"], row["arm"]): row for row in old["rows"]
    }
    new_lookup = {
        (row["case_id"], row["arm"]): row for row in new["rows"]
    }
    evaluations = []
    for key in sorted(old_lookup):
        old_row = old_lookup[key]
        new_row = new_lookup[key]
        votes = [
            old_row["judge_values"][1],
            old_row["judge_values"][2],
            new_row["judge_values"][0],
            new_row["judge_values"][1],
            new_row["judge_values"][2],
        ]
        evaluations.append(
            {
                "case_id": key[0],
                "arm": key[1],
                "band": old_row["band"],
                "cohort": old_row["cohort"],
                "votes": dict(zip(PANEL, votes)),
                "detected": bool(majority(votes)),
            }
        )
    rates = {}
    contrasts = {}
    arms = old["arms"]
    for cohort in ("structural", "local"):
        case_ids = sorted(
            {
                row["case_id"]
                for row in evaluations
                if row["cohort"] == cohort
            }
        )
        lookup = {
            (row["case_id"], row["arm"]): row["detected"]
            for row in evaluations
            if row["cohort"] == cohort
        }
        rates[cohort] = {}
        for arm in arms:
            detected = sum(lookup[(case_id, arm)] for case_id in case_ids)
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
                lookup[(case_id, treatment)]
                and not lookup[(case_id, control)]
                for case_id in case_ids
            )
            control_wins = sum(
                lookup[(case_id, control)]
                and not lookup[(case_id, treatment)]
                for case_id in case_ids
            )
            contrasts[cohort][f"{treatment}_vs_{control}"] = {
                "delta": (
                    rates[cohort][treatment]["rate"]
                    - rates[cohort][control]["rate"]
                ),
                "treatment_wins": treatment_wins,
                "control_wins": control_wins,
                "p_exact_mcnemar": exact_mcnemar(
                    treatment_wins, control_wins
                ),
            }
    return {
        "arms": arms,
        "evaluations": evaluations,
        "rates": rates,
        "contrasts": contrasts,
    }


def markdown(exp1_result: dict, exp2_result: dict) -> str:
    lines = [
        "# Final five-judge aggregation — both experiments",
        "",
        "Panel: " + ", ".join(f"`{judge}`" for judge in PANEL),
        "",
        "Aggregation: strict majority of valid votes (normally 3/5; 3/4 when "
        "one judge abstains). At least four valid votes are required; ties are "
        "false. `gpt-4o-mini` is excluded.",
        "",
        "## Experiment 1",
        "",
        "| Mode | Mean total /25 [95% CI] | Delta [95% CI], p | Mean KG /9 [95% CI] | Delta [95% CI], p |",
        "|---|---:|---:|---:|---:|",
    ]
    for mode in ("baseline", "kg", "rag", "hybrid"):
        row = exp1_result["modes"][mode]
        if mode == "baseline":
            total_contrast = "—"
            kg_contrast = "—"
        else:
            total = row["total_contrast"]
            kg = row["kg_relevant_contrast"]
            total_contrast = (
                f"{total['delta']:+.2f} "
                f"[{total['ci95'][0]:+.2f}, {total['ci95'][1]:+.2f}], "
                f"p={total['p_permutation']:.4f}"
            )
            kg_contrast = (
                f"{kg['delta']:+.2f} "
                f"[{kg['ci95'][0]:+.2f}, {kg['ci95'][1]:+.2f}], "
                f"p={kg['p_permutation']:.4f}"
            )
        lines.append(
            f"| `{mode}` | {row['mean_total']:.2f} "
            f"[{row['total_ci95'][0]:.2f}, {row['total_ci95'][1]:.2f}] | "
            f"{total_contrast} | {row['mean_kg_relevant']:.2f} "
            f"[{row['kg_relevant_ci95'][0]:.2f}, "
            f"{row['kg_relevant_ci95'][1]:.2f}] | {kg_contrast} |"
        )
    lines.extend(["", "Criterion localisation:", ""])
    for mode in ("kg", "rag", "hybrid"):
        loc = exp1_result["localisation"][mode]
        lines.append(
            f"- `{mode}`: target gain {loc['gain_target']:+.3f}, "
            f"other-criteria gain {loc['gain_other']:+.3f}, "
            f"share {loc['share'] * 100:.1f}%, "
            f"criterion-subset permutation p={loc['p_criterion_permutation']:.4f}."
        )
    lines.extend(
        [
            "",
            "Single-judge sensitivity for the KG-relevant contrast:",
            "",
            "| Judge | Delta /9 | 95% CI | p |",
            "|---|---:|---:|---:|",
        ]
    )
    for judge in PANEL:
        row = exp1_result["individual_judges"][judge]
        lines.append(
            f"| `{judge}` | {row['delta']:+.3f} | "
            f"[{row['ci95'][0]:+.3f}, {row['ci95'][1]:+.3f}] | "
            f"{row['p_permutation']:.4f} |"
        )
    lines.extend(
        [
            "",
            "Pairwise inter-judge agreement across all Experiment 1 rubric cells:",
            "",
            "| Judge pair | Valid cells | Raw agreement | Cohen's kappa |",
            "|---|---:|---:|---:|",
        ]
    )
    for pair, row in exp1_result["agreement"].items():
        first, second = pair.split("__", maxsplit=1)
        lines.append(
            f"| `{first}` / `{second}` | {row['n_cells']} | "
            f"{row['raw_agreement']:.1%} | {row['kappa']:.3f} |"
        )
    lines.extend(
        [
            "",
            f"Gemini abstained on {exp1_result['abstentions']['gemini:gemini-2.5-flash']}"
            " of 4,000 Experiment 1 criterion cells; every cell retained at least "
            "four valid judges.",
            "",
            "## Experiment 2",
            "",
            "| Arm | Structural detection [Wilson 95% CI] | Local control |",
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
        structural = exp2_result["rates"]["structural"][arm]
        local = exp2_result["rates"]["local"][arm]
        lines.append(
            f"| `{arm}` | {structural['detected']}/{structural['n']} "
            f"[{structural['wilson95'][0]:.2f}, "
            f"{structural['wilson95'][1]:.2f}] | "
            f"{local['detected']}/{local['n']} |"
        )
    lines.extend(["", "Paired structural contrasts:", ""])
    for key in (
        "kg_vs_baseline",
        "rag_vs_baseline",
        "hybrid_vs_baseline",
        "hybrid_vs_kg",
        "kg_joern_inherit_vs_kg",
    ):
        row = exp2_result["contrasts"]["structural"][key]
        lines.append(
            f"- `{key}`: delta={row['delta']:+.3f}, "
            f"wins/losses={row['treatment_wins']}/{row['control_wins']}, "
            f"exact McNemar p={row['p_exact_mcnemar']:.4g}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This file provides one aggregation rule and one result table per "
            "experiment. The six-model vote archive remains available, but the "
            "final panel excludes gpt-4o-mini to avoid an even-panel tie and reduce "
            "same-provider duplication.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    first = exp1()
    second = exp2()
    payload = {
        "status": "five-judge-offline-aggregation",
        "panel": PANEL,
        "majority_threshold": MAJORITY,
        "experiment1": first,
        "experiment2": second,
    }
    json_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    markdown_text = markdown(first, second)
    EXP.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json_text)
    OUT_MD.write_text(markdown_text)
    RESULT_JSON.write_text(json_text)
    RESULT_MD.write_text(markdown_text)
    BUNDLE_JSON.write_text(json_text)
    BUNDLE_MD.write_text(markdown_text)
    print(f"wrote {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
