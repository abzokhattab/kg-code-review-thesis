#!/usr/bin/env python3
"""Assemble and analyse the body-parity Joern run as an Experiment 1 panel.

`experiments/2026-06-11_joern_normal_prompt` generated its kg arm without the PR
description in the user prompt, while the headline pipeline
(`dataset_v2/scripts/regenerate_reviews_v2.py`) includes it. Its +0.69 KG-relevant
delta is therefore a lower bound: the kg arm saw less than the baseline it is
compared against. `experiments/2026-06-11_joern_normal_prompt_parity` re-ran all
35 PRs with body parity restored and scored them with the headline panel, but no
analysis artefact was ever produced from it.

This script builds the panel file the same way
`results/checklist_evaluation_llm_multi__joern.json` was built -- parity kg arm,
baseline/rag/hybrid carried over from the grep headline panel on the same 35 PRs
-- and then defers to `scripts/bootstrap_stats.py` so the CIs and permutation
tests are computed by exactly the same code as every other headline number.

Only the baseline-vs-kg contrast is licensed: rag and hybrid are carried over and
were never rebuilt with the Joern builder.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PARITY_SCORES = REPO / "experiments" / "2026-06-11_joern_normal_prompt_parity" / "scores"
GREP_PANEL = REPO / "results" / "checklist_evaluation_llm_multi__v2.json"
OUT_PANEL = REPO / "results" / "checklist_evaluation_llm_multi__joern_parity.json"
OUT_STEM = REPO / "results" / "BOOTSTRAP_STATS_joern_parity"

CARRIED_MODES = ("baseline", "rag", "hybrid")


def load_parity_kg() -> list[dict]:
    records = []
    for path in sorted(PARITY_SCORES.glob("pr*_kg.json")):
        rec = json.loads(path.read_text())
        if rec.get("mode") != "kg":
            raise SystemExit(f"{path} is not a kg record")
        records.append(rec)
    if not records:
        raise SystemExit(f"no parity scores found under {PARITY_SCORES}")
    return records


def main() -> None:
    kg_records = load_parity_kg()
    pr_ids = sorted(r["pr_id"] for r in kg_records)

    grep = json.loads(GREP_PANEL.read_text())
    carried = [
        e
        for e in grep["evaluations"]
        if e["mode"] in CARRIED_MODES and e["pr_id"] in set(pr_ids)
    ]

    for mode in CARRIED_MODES:
        got = sorted(e["pr_id"] for e in carried if e["mode"] == mode)
        if got != pr_ids:
            missing = sorted(set(pr_ids) - set(got))
            raise SystemExit(f"carried mode {mode} missing PRs {missing}")

    panel = {
        "metadata": {
            "label": "Joern CPG KG, body-parity prompt (Experiment 1 candidate)",
            "n_prs": len(pr_ids),
            "pr_ids": pr_ids,
            "kg_source": (
                "Joern Code Property Graph call edges, normal SYSTEM_PROMPT_KG, PR body "
                "included (experiments/2026-06-11_joern_normal_prompt_parity)"
            ),
            "baseline_rag_hybrid_source": (
                "carried from grep headline results/checklist_evaluation_llm_multi__v2.json "
                "(rag/hybrid are NOT Joern-built; included only for 4-way omnibus completeness)"
            ),
            "generator": "openai:gpt-4o T=0.0",
            "judges": grep.get("panel", {}).get("judges"),
            "note": "Clean comparison is baseline vs kg.",
        },
        "criteria_definitions": grep.get("criteria_definitions"),
        "panel": {"judges": grep.get("panel", {}).get("judges")},
        "evaluations": carried + kg_records,
    }
    OUT_PANEL.write_text(json.dumps(panel, indent=1))
    print(f"wrote {OUT_PANEL.relative_to(REPO)} ({len(panel['evaluations'])} cells)")

    cmd = [
        sys.executable,
        str(REPO / "scripts" / "bootstrap_stats.py"),
        "--in",
        str(OUT_PANEL),
        "--out-json",
        f"{OUT_STEM}.json",
        "--out-md",
        f"{OUT_STEM}.md",
        "--label",
        f"Joern CPG KG, body-parity prompt ({len(pr_ids)} PRs)",
    ]
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=REPO)


if __name__ == "__main__":
    main()
