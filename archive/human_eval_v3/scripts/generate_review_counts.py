#!/usr/bin/env python3
"""generate_review_counts.py — add a neutral "concrete-substance count" layer.

Rationale (2026-06-21, supervisor meeting w/ C. Adriano): rather than ask the
rater to count concrete items themselves (which they will try to do implicitly
and inconsistently), the LLM counts them ONCE, offline, and we show the counts
next to each review. The rater then only has to judge whether the *difference*
in counts is relevant — exactly the A / B / equivalent judgment the 5-point
preference scale already captures.

The five categories map directly onto the study's existing rubric criteria so
the count layer and the LLM-judge scores measure the same dimensions:

  components_apis  -> F3*  concrete components / APIs / design patterns named
  files            -> (objective grounding) concrete file paths/names referenced
  test_targets     -> T3   concrete test files or test scenarios named
  edge_cases       -> F2*  concrete edge cases / boundary / error conditions
  reasoned_claims  -> Q5   suggestions with an explicit reason ("X could cause Y")

Blinding-safe & reproducible, same constraints as generate_review_summaries.py:
  * extracted from the REVIEW TEXT ALONE, never the mode label;
  * identical neutral prompt for every arm;
  * pre-computed and frozen into study_data.json (no live API call in-study);
  * idempotent + cached (re-run skips reviews already counted unless --force);
  * stores the actual extracted ITEMS (not just a number) so every count is
    auditable.

Writes pr["review_counts"][mode] = {
    "components_apis": {"items": [...], "n": int}, ... , "total": int }

Usage:
  source load_env.sh
  python3 human_eval_v3/scripts/generate_review_counts.py
  python3 human_eval_v3/scripts/generate_review_counts.py --force
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
ENV = REPO / ".env"
if ENV.exists():
    for line in ENV.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from prnote.llm import generate_completion  # noqa: E402

CATEGORIES = ["components_apis", "files", "test_targets", "edge_cases", "reasoned_claims"]

SYSTEM = """You extract the CONCRETE, specific items a code-review note contains, so a reader can see how grounded it is. You are NOT judging quality — only listing what is explicitly, concretely named.

Extract five lists. Be strict: include an item ONLY if it is concrete and specific to this review; never invent, never count vague/generic phrasing.

- "components_apis": distinct concrete components, classes, functions, methods, APIs, or named design patterns the review explicitly references (e.g. `ShareGroupDLQStateManager`, `validateDlqTopic()`). Not generic words like "the system".
- "files": distinct concrete file paths or file names the review references (e.g. `src/api_client.py`). Count each file once.
- "test_targets": distinct concrete test files OR specific test scenarios the review names (e.g. `test_api_client.py`, "the exhausted-retries case"). Not a generic "add tests".
- "edge_cases": distinct concrete edge cases, boundary conditions, or error/failure conditions the review explicitly names (e.g. "null node list", "older runtime versions").
- "reasoned_claims": distinct suggestions/concerns where the review gives an explicit cause->effect reason (an "X could cause/lead to Y" link). Count the reasoned claims, not bare assertions.

De-duplicate within each list. Output STRICT JSON only, no prose:
{"components_apis":[...],"files":[...],"test_targets":[...],"edge_cases":[...],"reasoned_claims":[...]}"""


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1] if "```" in raw[3:] else raw
        raw = raw.lstrip("json").strip().strip("`").strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start:end + 1]
    return json.loads(raw)


def count_review(review: str, model: str) -> dict:
    raw = generate_completion(
        prompt=f"Code-review note:\n\n{review}\n\nExtract the five lists.",
        system=SYSTEM, model=model, temperature=0.0,
    )
    try:
        data = _parse_json(raw)
    except Exception as e:  # noqa: BLE001
        print(f"  ! parse error ({e}); treating as empty", flush=True)
        data = {}
    out: dict = {}
    total = 0
    for cat in CATEGORIES:
        items = data.get(cat, []) or []
        items = [str(x).strip() for x in items if str(x).strip()]
        # de-dup, preserve order
        seen, uniq = set(), []
        for it in items:
            key = it.lower()
            if key not in seen:
                seen.add(key)
                uniq.append(it)
        out[cat] = {"items": uniq, "n": len(uniq)}
        total += len(uniq)
    out["total"] = total
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--study", default="human_eval_v3/study_data.json")
    ap.add_argument("--model", default="openai:gpt-4o-mini")
    ap.add_argument("--force", action="store_true", help="re-count even if present")
    args = ap.parse_args()

    path = REPO / args.study
    data = json.loads(path.read_text())

    n_done = n_skip = 0
    for pr in data["prs"]:
        counts = pr.setdefault("review_counts", {})
        for mode, review in pr["reviews"].items():
            if not args.force and counts.get(mode):
                n_skip += 1
                continue
            c = count_review(review, args.model)
            counts[mode] = c
            n_done += 1
            print(f"PR#{pr['pr_id']:<3} {mode:<16} total={c['total']:<3} "
                  f"(comp={c['components_apis']['n']} files={c['files']['n']} "
                  f"test={c['test_targets']['n']} edge={c['edge_cases']['n']} "
                  f"reason={c['reasoned_claims']['n']})", flush=True)

    data["count_meta"] = {
        "model": args.model,
        "categories": CATEGORIES,
        "criterion_map": {
            "components_apis": "F3*", "test_targets": "T3",
            "edge_cases": "F2*", "reasoned_claims": "Q5",
        },
        "note": "Neutral concrete-item counts extracted from review text only "
                "(blinding-safe). See generate_review_counts.py.",
    }
    path.write_text(json.dumps(data, indent=2))
    print(f"\nwrote {path.relative_to(REPO)}  (counted={n_done}, skipped={n_skip})")


if __name__ == "__main__":
    main()
