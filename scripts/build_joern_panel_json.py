#!/usr/bin/env python3
"""build_joern_panel_json.py — assemble a first-class Joern results file.

The clean Joern run (experiments/2026-06-11_joern_normal_prompt/) stored 3-judge
scores per review but never produced a merged
`results/checklist_evaluation_llm_multi__*.json`, so it couldn't be fed to
`bootstrap_stats.py` / `kruskal_bonferroni.py`. This builds that file.

Composition (35 PRs Joern can analyse):
  * kg       -> Joern CPG reviews (experiments/.../scores/pr*_kg.json)
  * baseline -> headline __v2 (diff-only; KG source is irrelevant to baseline)
  * rag, hybrid -> headline __v2 (grep evidence) for omnibus completeness

The baseline-vs-kg comparison is the clean apples-to-apples KG-construction test
(same generator/prompt/judges; only KG source differs). rag/hybrid are carried
over from the grep headline only so the 4-way omnibus tests can run; they are
NOT Joern-built and are labelled as such in metadata.

No API calls.

Usage:
  python3 scripts/build_joern_panel_json.py
"""

from __future__ import annotations

import glob
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
V2 = REPO / "results/checklist_evaluation_llm_multi__v2.json"
JOERN_DIR = REPO / "experiments/2026-06-11_joern_normal_prompt/scores"
OUT = REPO / "results/checklist_evaluation_llm_multi__joern.json"


def main() -> None:
    v2 = json.loads(V2.read_text())
    v2_by = {(e["pr_id"], e["mode"]): e for e in v2["evaluations"]}

    joern_kg = {}
    for f in glob.glob(str(JOERN_DIR / "pr*_kg.json")):
        m = re.match(r"pr(\d+)_kg\.json", Path(f).name)
        if m:
            joern_kg[int(m.group(1))] = json.loads(Path(f).read_text())
    prs = sorted(joern_kg)

    evals = []
    for pr in prs:
        # kg from Joern
        evals.append(joern_kg[pr])
        # baseline/rag/hybrid carried from headline (restricted to these PRs)
        for mode in ("baseline", "rag", "hybrid"):
            e = v2_by.get((pr, mode))
            if e:
                evals.append(e)

    out = {
        "metadata": {
            "label": "Joern CPG KG (headline candidate)",
            "n_prs": len(prs),
            "pr_ids": prs,
            "kg_source": "Joern Code Property Graph call edges "
                         "(experiments/2026-06-11_joern_normal_prompt)",
            "baseline_rag_hybrid_source": "carried from grep headline "
                                          "results/checklist_evaluation_llm_multi__v2.json "
                                          "(rag/hybrid are NOT Joern-built; included only "
                                          "for 4-way omnibus completeness)",
            "generator": "openai:gpt-4o T=0.0",
            "judges": ["openai:gpt-4o-mini", "openai:gpt-4o", "gemini:gemini-2.5-flash"],
            "note": "Clean comparison is baseline vs kg.",
        },
        "criteria_definitions": v2["criteria_definitions"],
        "panel": v2.get("panel", {}),
        "evaluations": evals,
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(f"wrote {OUT}  ({len(evals)} evaluations across {len(prs)} PRs)")


if __name__ == "__main__":
    main()
