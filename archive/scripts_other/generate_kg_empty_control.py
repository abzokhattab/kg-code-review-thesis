#!/usr/bin/env python3
"""Prompt-priming control: KG system prompt with empty KG context.

Generates a review using ``SYSTEM_PROMPT_KG`` (which nudges the LLM toward
"integration risks, missing test coverage, code ownership concerns") but
injects *no* structural context. The user prompt contains only the diff.

Purpose: isolate how much of the apparent "KG lift" on KG-relevant rubric
criteria is due to the system-prompt nudge versus the structural KG data.

If the kg_empty mode scores comparably to the regular kg mode on PRs where
KG has no data to inject (NON_APPL tier), the lift is primarily prompt-priming.

Usage:
    python3 scripts/generate_kg_empty_control.py --pr-ids 1,5,11,12,13 \
        --model openai:gpt-4o --out-dir outputs/kg_empty_priming
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from prnote.llm import generate_completion  # noqa: E402
from prnote.note import (  # noqa: E402
    SYSTEM_PROMPT_KG,
    get_diff_from_evidence,
)


def build_prompt(evidence_path: Path) -> tuple[str, str]:
    ev = json.loads(evidence_path.read_text())
    diff = get_diff_from_evidence(ev)
    pr_title = (ev.get("pr") or {}).get("title") or evidence_path.stem
    user = f"""## Pull Request: {pr_title}

## Diff
```
{diff}
```


Please generate an evidence-anchored review note following the specified format."""
    return SYSTEM_PROMPT_KG, user


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr-ids", required=True, help="comma-separated PR ids")
    ap.add_argument("--model", default="openai:gpt-4o")
    ap.add_argument("--evidence-dir", default="data/luca_prs_fixed_ast_scoped")
    ap.add_argument("--out-dir", default="outputs/kg_empty_priming")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    ev_dir = REPO_ROOT / args.evidence_dir
    out_dir = REPO_ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    pr_ids = [int(x) for x in args.pr_ids.split(",") if x.strip()]
    print(f"[kg_empty] model={args.model}  prs={pr_ids}  out={out_dir.relative_to(REPO_ROOT)}")
    for pr_id in pr_ids:
        out_path = out_dir / f"pr{pr_id}_kgempty.md"
        if out_path.exists() and not args.force:
            print(f"  pr{pr_id}: SKIP (exists)")
            continue
        ev_path = ev_dir / f"pr{pr_id}_evidence.json"
        if not ev_path.exists():
            print(f"  pr{pr_id}: missing evidence at {ev_path}")
            continue
        sys_prompt, user_prompt = build_prompt(ev_path)
        t0 = time.time()
        try:
            text = generate_completion(prompt=user_prompt, system=sys_prompt,
                                       model=args.model, temperature=0.3)
        except Exception as exc:  # noqa: BLE001
            print(f"  pr{pr_id}: ERROR {exc}")
            continue
        out_path.write_text(text)
        print(f"  pr{pr_id}: wrote {len(text)} chars in {time.time()-t0:.1f}s -> {out_path.name}")


if __name__ == "__main__":
    main()
