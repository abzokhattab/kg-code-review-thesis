#!/usr/bin/env python3
"""Zero-cost graph-constrained semantic-reranking development gate."""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import evaluate_budgeted_fusion_retrieval as base  # noqa: E402


EXP = ROOT / "experiments/2026-09-20_graph_constrained_fusion"
RESULTS_JSON = EXP / "RESULTS.json"
RESULTS_MD = EXP / "RESULTS.md"
BUDGETS = (2_000, 4_000, 8_000)
SEMANTIC_PREVIEW_CHARS = 300


def graph_confidence(item: dict[str, Any]) -> int:
    sources = set(item["sources"])
    if sources & {"joern", "manifest_resolver"}:
        return 0
    return 1


def graph_semantic_rerank(
    graph_items: list[dict[str, Any]],
    rag_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Re-rank only graph-connected files; never add a semantic-only file."""
    rag_by_file = {item["file"]: item for item in rag_items}
    output = []
    for graph_item in graph_items:
        item = dict(graph_item)
        item["sources"] = list(graph_item["sources"])
        item["evidence"] = list(graph_item["evidence"])
        rag_item = rag_by_file.get(item["file"])
        similarity = float(rag_item["score"]) if rag_item is not None else -1.0
        item["semantic_similarity"] = similarity
        if rag_item is not None:
            item["sources"] = list(
                dict.fromkeys(item["sources"] + ["semantic_context"])
            )
            evidence = list(rag_item.get("evidence", []))
            if evidence:
                item["evidence"].append(evidence[0])
            if len(evidence) > 1 and evidence[1]:
                item["evidence"].append(
                    "CODE PREVIEW:\n" + evidence[1][:SEMANTIC_PREVIEW_CHARS]
                )
        output.append(item)
    return sorted(
        output,
        key=lambda item: (
            graph_confidence(item),
            -float(item["semantic_similarity"]),
            item["file"],
        ),
    )


def evaluate(
    case: dict[str, Any],
    arm: str,
    ranking: list[dict[str, Any]],
    budget: int,
) -> dict[str, Any]:
    selected, used = base.pack(ranking, budget)
    gold = set(case["gold"])
    selected_paths = {item["file"] for item in selected}
    hits = selected_paths & gold
    semantic_hits = {
        item["file"]
        for item in selected
        if item["file"] in gold and "semantic_context" in item["sources"]
    }
    first_rank = next(
        (
            rank
            for rank, item in enumerate(ranking, 1)
            if item["file"] in gold
        ),
        None,
    )
    return {
        "case_id": case["id"],
        "repo": case["repo"],
        "band": case["band"],
        "cohort": case["cohort"],
        "arm": arm,
        "budget": budget,
        "gold_count": len(gold),
        "candidate_count": len(ranking),
        "selected_count": len(selected),
        "tokens_used": used,
        "within_budget": used <= budget,
        "hit_any": bool(hits),
        "hit_count": len(hits),
        "target_recall": len(hits) / len(gold),
        "oracle_path_fraction": (
            len(hits) / len(selected_paths) if selected_paths else 0.0
        ),
        "semantic_hit_count": len(semantic_hits),
        "semantic_oracle_coverage": (
            len(semantic_hits) / len(hits) if hits else 0.0
        ),
        "first_relevant_rank": first_rank,
        "reciprocal_rank": 0.0 if first_rank is None else 1.0 / first_rank,
        "selected": [
            {
                "file": item["file"],
                "sources": item["sources"],
                "estimated_tokens": item["estimated_tokens"],
                "semantic_similarity": item.get("semantic_similarity"),
            }
            for item in selected
        ],
    }


def aggregate(
    records: list[dict[str, Any]],
    cohort: str,
    arm: str,
    budget: int,
) -> dict[str, Any]:
    rows = [
        row
        for row in records
        if row["cohort"] == cohort
        and row["arm"] == arm
        and row["budget"] == budget
    ]
    total_hits = sum(row["hit_count"] for row in rows)
    total_semantic_hits = sum(row["semantic_hit_count"] for row in rows)
    return {
        "cohort": cohort,
        "arm": arm,
        "budget": budget,
        "n": len(rows),
        "hit_any_n": sum(int(row["hit_any"]) for row in rows),
        "hit_any_rate": statistics.fmean(row["hit_any"] for row in rows),
        "mean_target_recall": statistics.fmean(
            row["target_recall"] for row in rows
        ),
        "mean_oracle_path_fraction": statistics.fmean(
            row["oracle_path_fraction"] for row in rows
        ),
        "mrr": statistics.fmean(row["reciprocal_rank"] for row in rows),
        "semantic_oracle_coverage": (
            total_semantic_hits / total_hits if total_hits else 0.0
        ),
        "mean_tokens": statistics.fmean(row["tokens_used"] for row in rows),
        "within_budget": all(row["within_budget"] for row in rows),
    }


def gate(
    records: list[dict[str, Any]],
    summary: list[dict[str, Any]],
) -> dict[str, Any]:
    lookup = {
        (row["cohort"], row["arm"], row["budget"]): row for row in summary
    }
    checks = []
    for cohort in ("dependency", "test"):
        plain = lookup[(cohort, "deployed_graph", 4_000)]
        fused = lookup[(cohort, "deployed_graph_semantic", 4_000)]
        plain_cases = {
            row["case_id"]: row
            for row in records
            if row["cohort"] == cohort
            and row["arm"] == "deployed_graph"
            and row["budget"] == 4_000
        }
        fused_cases = {
            row["case_id"]: row
            for row in records
            if row["cohort"] == cohort
            and row["arm"] == "deployed_graph_semantic"
            and row["budget"] == 4_000
        }
        lost = sorted(
            case_id
            for case_id, row in plain_cases.items()
            if row["hit_any"] and not fused_cases[case_id]["hit_any"]
        )
        checks.extend(
            [
                {
                    "name": f"{cohort}: lose zero graph hits",
                    "passed": not lost,
                    "observed": "none" if not lost else ", ".join(lost),
                },
                {
                    "name": f"{cohort}: macro recall non-decreasing",
                    "passed": (
                        fused["mean_target_recall"]
                        >= plain["mean_target_recall"] - 1e-12
                    ),
                    "observed": (
                        f"{fused['mean_target_recall']:.1%} vs "
                        f"{plain['mean_target_recall']:.1%}"
                    ),
                },
                {
                    "name": f"{cohort}: oracle-path fraction non-decreasing",
                    "passed": (
                        fused["mean_oracle_path_fraction"]
                        >= plain["mean_oracle_path_fraction"] - 1e-12
                    ),
                    "observed": (
                        f"{fused['mean_oracle_path_fraction']:.1%} vs "
                        f"{plain['mean_oracle_path_fraction']:.1%}"
                    ),
                },
                {
                    "name": f"{cohort}: >=75% oracle paths have code snippets",
                    "passed": fused["semantic_oracle_coverage"] >= 0.75,
                    "observed": f"{fused['semantic_oracle_coverage']:.1%}",
                },
                {
                    "name": f"{cohort}: all contexts within budget",
                    "passed": fused["within_budget"],
                    "observed": str(fused["within_budget"]).lower(),
                },
            ]
        )
    return {"passed": all(item["passed"] for item in checks), "checks": checks}


def validate_nested(
    cases: list[dict[str, Any]],
    arms: list[str],
    records: list[dict[str, Any]],
) -> None:
    mapping = {
        (row["case_id"], row["arm"], row["budget"]): [
            item["file"] for item in row["selected"]
        ]
        for row in records
    }
    for case in cases:
        for arm in arms:
            two = mapping[(case["id"], arm, 2_000)]
            four = mapping[(case["id"], arm, 4_000)]
            eight = mapping[(case["id"], arm, 8_000)]
            if not (two == four[: len(two)] and four == eight[: len(four)]):
                raise AssertionError(
                    f"non-prefix budget packing: {case['id']}/{arm}"
                )


def markdown(
    summary: list[dict[str, Any]],
    decision: dict[str, Any],
    arms: list[str],
) -> str:
    lines = [
        "# Graph-constrained semantic fusion — offline gate",
        "",
        "**Status:** exploratory development result; no API/model calls.",
        "",
        f"**Decision: {'PASS' if decision['passed'] else 'NO-GO'}**",
        "",
        "| Check | Result | Observed |",
        "|---|:---:|---:|",
    ]
    for item in decision["checks"]:
        lines.append(
            f"| {item['name']} | {'pass' if item['passed'] else 'fail'} | "
            f"{item['observed']} |"
        )
    for cohort in ("dependency", "test"):
        lines.extend(
            [
                "",
                f"## {cohort.capitalize()} cohort",
                "",
                "| Arm | Budget | Hit-any | Macro recall | Oracle-path fraction | "
                "MRR | Oracle paths with semantic code | Mean tokens |",
                "|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        rows = {
            (row["arm"], row["budget"]): row
            for row in summary
            if row["cohort"] == cohort
        }
        for arm in arms:
            for budget in BUDGETS:
                row = rows[(arm, budget)]
                lines.append(
                    f"| `{arm}` | {budget:,} | "
                    f"{row['hit_any_n']}/{row['n']} "
                    f"({row['hit_any_rate']:.1%}) | "
                    f"{row['mean_target_recall']:.1%} | "
                    f"{row['mean_oracle_path_fraction']:.1%} | "
                    f"{row['mrr']:.3f} | "
                    f"{row['semantic_oracle_coverage']:.1%} | "
                    f"{row['mean_tokens']:.0f} |"
                )
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "- The changed-file embedding is a saved first-chunk proxy.",
            "- The manifest-resolver arms are circular packing ceilings.",
            "- These reused stimuli are development data.",
            "- A retrieval pass does not imply an LLM review-quality gain.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if (RESULTS_JSON.exists() or RESULTS_MD.exists()) and not args.force:
        print(f"results already exist under {EXP}; use --force to recompute")
        return

    cases = base.load_cases()
    graphs = base.GraphSources()
    arms = [
        "deployed_graph",
        "deployed_graph_semantic",
        "manifest_resolver_graph",
        "manifest_resolver_graph_semantic",
    ]
    records = []
    done = 0
    for repo in sorted({case["repo"] for case in cases}):
        rag_proxy = base.SavedRagProxy(repo)
        for case in [case for case in cases if case["repo"] == repo]:
            retrieval_case = {
                key: case[key]
                for key in ("id", "repo", "language", "edit_file", "symbol")
            }
            deployed = graphs.deployed(retrieval_case, case["cohort"])
            resolved = graphs.resolved(retrieval_case, case["cohort"])
            rag = rag_proxy.rank(case["edit_file"])
            rankings = {
                "deployed_graph": deployed,
                "deployed_graph_semantic": graph_semantic_rerank(deployed, rag),
                "manifest_resolver_graph": resolved,
                "manifest_resolver_graph_semantic": graph_semantic_rerank(
                    resolved, rag
                ),
            }
            for arm in arms:
                for budget in BUDGETS:
                    records.append(evaluate(case, arm, rankings[arm], budget))
            done += 1
            if done % 10 == 0 or done == len(cases):
                print(f"evaluated {done}/{len(cases)}")
        del rag_proxy

    validate_nested(cases, arms, records)
    summary = [
        aggregate(records, cohort, arm, budget)
        for cohort in ("dependency", "test")
        for arm in arms
        for budget in BUDGETS
    ]
    decision = gate(records, summary)
    payload = {
        "status": "exploratory-development-only",
        "cost_usd": 0,
        "policy": {
            "semantic_preview_chars": SEMANTIC_PREVIEW_CHARS,
            "confidence_order": ["joern_or_manifest_resolver", "lexical"],
            "budgets": list(BUDGETS),
        },
        "decision": decision,
        "summary": summary,
        "records": records,
    }
    EXP.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    RESULTS_MD.write_text(markdown(summary, decision, arms))
    print(f"{'PASS' if decision['passed'] else 'NO-GO'}: wrote {RESULTS_MD}")


if __name__ == "__main__":
    main()
