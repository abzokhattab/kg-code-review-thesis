#!/usr/bin/env python3
"""Regenerate PR reviews under an alternative base LLM generator.

Used for the cross-generator robustness ablation (see
``results/CROSS_GENERATOR_REPLICATION.md`` once produced). Preserves the
original prompts from ``prnote/note.py`` so every difference in the output
is attributable to the base model rather than to prompt drift.

Usage:
    # Full replication: all 25 PRs x 4 modes under Claude Sonnet 4.5
    python3 scripts/regenerate_reviews_alt_model.py \
        --model anthropic:claude-sonnet-4-5 \
        --out-dir outputs/luca_prs_claude

    # Diagnostic: one PR, all 4 modes
    python3 scripts/regenerate_reviews_alt_model.py \
        --model anthropic:claude-sonnet-4-5 \
        --out-dir outputs/luca_prs_claude \
        --pr-ids 18

Resumable: skips any (pr, mode) pair whose output file already exists
unless --force is passed.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from prnote.llm import generate_completion  # noqa: E402
from prnote.note import (  # noqa: E402
    SYSTEM_PROMPT_BASELINE,
    SYSTEM_PROMPT_HYBRID,
    SYSTEM_PROMPT_KG,
    SYSTEM_PROMPT_RAG,
    format_hybrid_context,
    format_kg_context,
    format_rag_context,
    get_diff_from_evidence,
)

EVIDENCE_DIR = REPO_ROOT / "data" / "luca_prs_fixed"  # default; can be overridden via --evidence-dir

ALL_PR_IDS = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
MODES = ["baseline", "rag", "kg", "hybrid"]

SYSTEM_PROMPTS = {
    "baseline": SYSTEM_PROMPT_BASELINE,
    "rag": SYSTEM_PROMPT_RAG,
    "kg": SYSTEM_PROMPT_KG,
    "hybrid": SYSTEM_PROMPT_HYBRID,
}


@dataclass
class GenResult:
    pr_id: int
    mode: str
    out_path: Path
    status: str  # "wrote" | "skipped" | "error"
    chars: int = 0
    elapsed_s: float = 0.0
    error: str = ""


def build_user_prompt(pr_id: int, mode: str) -> str:
    evidence_path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    with evidence_path.open() as f:
        evidence = json.load(f)

    diff = get_diff_from_evidence(evidence)
    pr_title = (evidence.get("pr") or {}).get("title") or f"PR #{pr_id}"

    if mode == "baseline":
        context = ""
    elif mode == "rag":
        context = format_rag_context(evidence)
    elif mode == "kg":
        context = format_kg_context(evidence)
    elif mode == "hybrid":
        context = format_hybrid_context(evidence)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return f"""## Pull Request: {pr_title}

## Diff
```
{diff}
```
{context}

Please generate an evidence-anchored review note following the specified format."""


def generate_one(pr_id: int, mode: str, model: str, out_dir: Path, force: bool) -> GenResult:
    out_path = out_dir / f"pr{pr_id}_{mode}.md"
    if out_path.exists() and not force:
        return GenResult(pr_id, mode, out_path, "skipped", chars=out_path.stat().st_size)

    system_prompt = SYSTEM_PROMPTS[mode]
    user_prompt = build_user_prompt(pr_id, mode)

    t0 = time.time()
    try:
        text = generate_completion(
            prompt=user_prompt,
            system=system_prompt,
            model=model,
            temperature=0.3,
        )
    except Exception as exc:  # noqa: BLE001
        return GenResult(
            pr_id, mode, out_path,
            status="error", elapsed_s=time.time() - t0, error=str(exc)[:300],
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text)
    return GenResult(pr_id, mode, out_path, "wrote", chars=len(text), elapsed_s=time.time() - t0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Model slug, e.g. 'anthropic:claude-sonnet-4-5'")
    parser.add_argument("--out-dir", required=True, help="Output directory for generated reviews")
    parser.add_argument(
        "--pr-ids",
        type=str,
        default="",
        help="Comma-separated PR ids (default: full set 1..26 skipping 4)",
    )
    parser.add_argument(
        "--modes",
        type=str,
        default=",".join(MODES),
        help=f"Comma-separated modes (default: {','.join(MODES)})",
    )
    parser.add_argument("--force", action="store_true", help="Re-generate even if output already exists")
    parser.add_argument(
        "--evidence-dir",
        type=str,
        default="",
        help="Override evidence directory (default: data/luca_prs_fixed)",
    )
    args = parser.parse_args()
    if args.evidence_dir:
        global EVIDENCE_DIR
        ed = Path(args.evidence_dir)
        EVIDENCE_DIR = ed if ed.is_absolute() else REPO_ROOT / ed

    if args.pr_ids.strip():
        pr_ids = [int(x) for x in args.pr_ids.split(",") if x.strip()]
    else:
        pr_ids = ALL_PR_IDS

    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    for m in modes:
        if m not in SYSTEM_PROMPTS:
            parser.error(f"Unknown mode: {m}")

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[GenResult] = []
    total = len(pr_ids) * len(modes)
    try:
        out_rel = out_dir.relative_to(REPO_ROOT)
    except ValueError:
        out_rel = out_dir
    print(f"[regen] model={args.model}  prs={len(pr_ids)}  modes={modes}  total={total}  out={out_rel}")
    print(f"[regen] resumable: skipping pairs whose output already exists (use --force to override)\n")

    t_start = time.time()
    for pr_id in pr_ids:
        for mode in modes:
            r = generate_one(pr_id, mode, args.model, out_dir, args.force)
            results.append(r)
            n = len(results)
            if r.status == "wrote":
                print(f"  [{n:3d}/{total}]  pr{pr_id:<2} {mode:<8}  OK    {r.chars:>5} chars  {r.elapsed_s:>5.1f}s  -> {r.out_path.name}")
            elif r.status == "skipped":
                print(f"  [{n:3d}/{total}]  pr{pr_id:<2} {mode:<8}  SKIP  {r.chars:>5} chars (exists)")
            else:
                print(f"  [{n:3d}/{total}]  pr{pr_id:<2} {mode:<8}  ERR   {r.error}")

    wrote = sum(1 for r in results if r.status == "wrote")
    skipped = sum(1 for r in results if r.status == "skipped")
    errors = sum(1 for r in results if r.status == "error")
    elapsed = time.time() - t_start
    print(f"\n[regen] done in {elapsed:.1f}s — wrote {wrote}, skipped {skipped}, errors {errors}")
    if errors:
        for r in results:
            if r.status == "error":
                print(f"  ERROR pr{r.pr_id} {r.mode}: {r.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
