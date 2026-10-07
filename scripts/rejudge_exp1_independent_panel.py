#!/usr/bin/env python3
"""Score frozen Experiment 1 reviews with an independent 3-provider panel.

Panel:
  - anthropic:claude-sonnet-4-5 (reuses the completed external-judge cache)
  - deepseek:deepseek-v4-pro
  - xai:grok-4.6

No review generation occurs. Original evaluation artefacts are read-only.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_reviews import (  # noqa: E402
    EVALUATION_CRITERIA,
    SYSTEM_PROMPT,
    build_user_prompt,
    judge_one,
    load_pr_context,
)
from prnote.llm import _USAGE_LOG  # noqa: E402


REVIEWS = ROOT / "outputs/luca_prs_v2"
CLAUDE_CACHE = (
    REVIEWS
    / ".judge_cache/extjudge/anthropic-claude-sonnet-4-5"
)
EXP = ROOT / "experiments/2026-09-19_independent_judges"
CACHE = EXP / "exp1_judgments"
PREFLIGHT = EXP / "PREFLIGHT_EXP1.md"
USAGE_LOG = EXP / "usage_exp1.jsonl"
RESULTS_JSON = EXP / "RESULTS_EXP1.json"
RESULTS_MD = EXP / "RESULTS_EXP1.md"

CLAUDE = "anthropic:claude-sonnet-4-5"
NEW_JUDGES = ["deepseek:deepseek-v4-pro", "xai:grok-4.6"]
PANEL = [CLAUDE] + NEW_JUDGES
KG_IDS = {c.id for c in EVALUATION_CRITERIA if c.kg_relevant}
ALL_IDS = [c.id for c in EVALUATION_CRITERIA]
RATES = {
    "deepseek:deepseek-v4-pro": {"input": 1.32, "output": 3.96},
    "xai:grok-4.6": {"input": 2.00, "output": 6.00},
}
ESTIMATED_OUTPUT_TOKENS = 1_200
PRINT_LOCK = threading.Lock()


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def safe_model(model: str) -> str:
    return model.replace(":", "_").replace("/", "_")


def parse_review_key(path: Path) -> tuple[int, str]:
    stem = path.stem
    left, mode = stem.rsplit("_", 1)
    return int(left.removeprefix("pr")), mode


def cache_path(review_key: str, model: str) -> Path:
    return CACHE / safe_model(model) / f"{review_key}.json"


def review_files() -> list[Path]:
    return sorted(
        REVIEWS.glob("pr*_*.md"),
        key=lambda path: (*parse_review_key(path), path.name),
    )


def claude_scores(review_key: str) -> dict[str, int]:
    path = CLAUDE_CACHE / f"{review_key}.json"
    payload = json.loads(path.read_text())
    scores = payload[CLAUDE]
    if set(scores) != set(ALL_IDS):
        raise AssertionError(f"incomplete Claude cache: {path}")
    return {key: int(value) for key, value in scores.items()}


def judge_and_cache(path: Path, model: str, force: bool) -> str:
    review_key = path.stem
    output = cache_path(review_key, model)
    if output.exists() and not force:
        try:
            payload = json.loads(output.read_text())
            if not payload.get("error") and len(payload.get("scores", {})) == 25:
                return "cached"
        except Exception:
            pass

    pr_id, _ = parse_review_key(path)
    verdict = judge_one(path.read_text(), load_pr_context(pr_id), model)
    payload = {
        "model": model,
        "review_key": review_key,
        "scores": verdict.scores,
        "evidence": verdict.evidence,
        "error": verdict.error,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(output)
    return "ERROR: " + verdict.error if verdict.error else "judged"


def majority(scores: list[int]) -> int:
    if any(score not in (0, 1) for score in scores):
        raise ValueError(f"invalid panel scores: {scores}")
    return 1 if sum(scores) >= 2 else 0


def permutation_p(differences: list[float], seed: int = 2026, B: int = 20_000) -> float:
    observed = abs(statistics.fmean(differences))
    if not differences or observed == 0:
        return 1.0
    rng = random.Random(seed)
    hits = 0
    for _ in range(B):
        trial = abs(
            statistics.fmean(rng.choice((-1, 1)) * value for value in differences)
        )
        hits += trial >= observed - 1e-12
    return (hits + 1) / (B + 1)


def bootstrap_ci(
    differences: list[float], seed: int = 2026, B: int = 10_000
) -> tuple[float, float]:
    rng = random.Random(seed)
    n = len(differences)
    means = sorted(
        statistics.fmean(differences[rng.randrange(n)] for _ in range(n))
        for _ in range(B)
    )
    return means[int(0.025 * B)], means[int(0.975 * B) - 1]


def cohens_dz(differences: list[float]) -> float:
    if len(differences) < 2:
        return 0.0
    sd = statistics.stdev(differences)
    return statistics.fmean(differences) / sd if sd else 0.0


def assemble() -> None:
    evaluations = []
    for path in review_files():
        pr_id, mode = parse_review_key(path)
        per_judge = {CLAUDE: claude_scores(path.stem)}
        for model in NEW_JUDGES:
            payload = json.loads(cache_path(path.stem, model).read_text())
            if payload.get("error"):
                raise RuntimeError(f"{path.stem}/{model}: {payload['error']}")
            scores = {key: int(value) for key, value in payload["scores"].items()}
            if set(scores) != set(ALL_IDS):
                raise RuntimeError(f"incomplete scores: {path.stem}/{model}")
            per_judge[model] = scores
        panel = {
            criterion: majority([per_judge[model][criterion] for model in PANEL])
            for criterion in ALL_IDS
        }
        evaluations.append(
            {
                "pr_id": pr_id,
                "mode": mode,
                "total": sum(panel.values()),
                "kg_relevant": sum(panel[key] for key in KG_IDS),
                "panel_scores": panel,
                "criteria_scores": [
                    {"criterion_id": key, "score": panel[key]}
                    for key in ALL_IDS
                ],
                "per_judge": per_judge,
            }
        )

    by_mode = {
        mode: {row["pr_id"]: row for row in evaluations if row["mode"] == mode}
        for mode in ("baseline", "kg", "rag", "hybrid")
    }
    means = {}
    contrasts = {}
    for mode, rows in by_mode.items():
        means[mode] = {
            "n": len(rows),
            "total": statistics.fmean(row["total"] for row in rows.values()),
            "kg_relevant": statistics.fmean(
                row["kg_relevant"] for row in rows.values()
            ),
        }
        if mode == "baseline":
            continue
        ids = sorted(set(rows) & set(by_mode["baseline"]))
        contrasts[mode] = {}
        for metric in ("total", "kg_relevant"):
            differences = [
                rows[pr_id][metric] - by_mode["baseline"][pr_id][metric]
                for pr_id in ids
            ]
            low, high = bootstrap_ci(differences)
            contrasts[mode][metric] = {
                "n": len(ids),
                "delta": statistics.fmean(differences),
                "ci95": [low, high],
                "p_permutation": permutation_p(differences),
                "cohens_dz": cohens_dz(differences),
            }

    payload = {
        "status": "post-hoc-independent-panel-sensitivity",
        "panel": PANEL,
        "generator": "openai:gpt-4o",
        "claude_source": str(CLAUDE_CACHE.relative_to(ROOT)),
        "criteria_definitions": [
            {
                "id": criterion.id,
                "category": criterion.category,
                "description": criterion.description,
                "kg_relevant": criterion.kg_relevant,
            }
            for criterion in EVALUATION_CRITERIA
        ],
        "means": means,
        "contrasts": contrasts,
        "evaluations": evaluations,
    }
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Experiment 1 — independent three-provider judge panel",
        "",
        "**Status:** post-hoc sensitivity; frozen reviews, no regeneration.",
        "",
        "Panel: " + ", ".join(f"`{model}`" for model in PANEL),
        "",
        "| Mode | Mean total /25 | Mean KG-relevant /9 |",
        "|---|---:|---:|",
    ]
    for mode in ("baseline", "kg", "rag", "hybrid"):
        row = means[mode]
        lines.append(
            f"| `{mode}` | {row['total']:.2f} | {row['kg_relevant']:.2f} |"
        )
    lines.extend(
        [
            "",
            "| Contrast vs baseline | Metric | Delta [95% CI] | p | d_z |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for mode in ("kg", "rag", "hybrid"):
        for metric in ("total", "kg_relevant"):
            row = contrasts[mode][metric]
            lines.append(
                f"| `{mode}` | {metric} | {row['delta']:+.2f} "
                f"[{row['ci95'][0]:+.2f}, {row['ci95'][1]:+.2f}] | "
                f"{row['p_permutation']:.4f} | {row['cohens_dz']:+.2f} |"
            )
    lines.extend(
        [
            "",
            "This panel contains no OpenAI judge. It is reported beside the original "
            "panel and does not alter the historical generator configuration.",
            "",
        ]
    )
    RESULTS_MD.write_text("\n".join(lines))


def write_usage() -> None:
    if not _USAGE_LOG:
        return
    USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with USAGE_LOG.open("a") as handle:
        for row in _USAGE_LOG:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    _USAGE_LOG.clear()


def preflight() -> dict[str, Any]:
    files = review_files()
    missing_claude = [
        path.stem for path in files if not (CLAUDE_CACHE / f"{path.stem}.json").exists()
    ]
    by_model = {}
    for model in NEW_JUDGES:
        pending = [
            path for path in files if not cache_path(path.stem, model).exists()
        ]
        input_tokens = 0
        for path in pending:
            pr_id, _ = parse_review_key(path)
            prompt = build_user_prompt(path.read_text(), load_pr_context(pr_id))
            input_tokens += estimate_tokens(SYSTEM_PROMPT + "\n" + prompt)
        output_tokens = len(pending) * ESTIMATED_OUTPUT_TOKENS
        rates = RATES[model]
        by_model[model] = {
            "calls": len(pending),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": (
                input_tokens / 1_000_000 * rates["input"]
                + output_tokens / 1_000_000 * rates["output"]
            ),
        }
    return {
        "reviews": len(files),
        "claude_cached": len(files) - len(missing_claude),
        "missing_claude": missing_claude,
        "by_model": by_model,
        "cost": sum(row["cost"] for row in by_model.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    EXP.mkdir(parents=True, exist_ok=True)
    estimate = preflight()
    if estimate["missing_claude"]:
        raise SystemExit(
            f"missing {len(estimate['missing_claude'])} Claude cache files"
        )
    if args.dry_run:
        print(json.dumps(estimate, indent=2))
        return

    tasks = []
    for path in review_files():
        for model in NEW_JUDGES:
            output = cache_path(path.stem, model)
            if output.exists() and not args.force:
                try:
                    payload = json.loads(output.read_text())
                    if not payload.get("error") and len(payload.get("scores", {})) == 25:
                        continue
                except Exception:
                    pass
            tasks.append((path, model))
    print(
        f"{len(tasks)} Experiment 1 independent judge calls "
        f"(Claude cached: {estimate['claude_cached']})"
    )
    failed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(judge_and_cache, path, model, args.force): (path.stem, model)
            for path, model in tasks
        }
        for index, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result.startswith("ERROR"):
                failed += 1
                with PRINT_LOCK:
                    print(f"{futures[future]} {result}", flush=True)
            elif index % 20 == 0 or index == len(tasks):
                with PRINT_LOCK:
                    print(f"[{index}/{len(tasks)}]", flush=True)
            write_usage()
    write_usage()
    if failed:
        raise SystemExit(f"{failed} judge calls failed; rerun to retry")
    assemble()
    print(f"DONE results={RESULTS_MD}")


if __name__ == "__main__":
    main()
