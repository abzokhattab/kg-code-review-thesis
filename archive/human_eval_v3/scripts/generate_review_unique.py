#!/usr/bin/env python3
"""generate_review_unique.py — semantic unique-content markers for highlighting.

Rationale (2026-06-21, supervisor meeting w/ C. Adriano): the study UI shades the
content of each review that is *genuinely unique* relative to the other review, so
a rater can see at a glance where the two reviews actually differ. The earlier
lexical (word-overlap) heuristic shaded ~70-80% of every review because it flagged
paraphrases of SHARED points as different. Chris's spec: highlight a point only if
it is absent from the other review; a point that is merely re-worded is SHARED and
must stay unshaded.

This script does that semantic diff once, offline, with an LLM, and freezes the
result into study_data.json as pr["review_unique"][mode] = [key, ...]. The UI
(index.html -> shadeByKeys) shades a paragraph/bullet iff its text contains one of
that mode's keys (case-insensitive substring).

Design constraints (same as generate_review_summaries.py / generate_review_counts.py):
  * Blinding-safe: reviews are compared as neutral "Review 1 / Review 2"; the mode
    label is NEVER shown to the model.
  * Keys are VERBATIM substrings copied from the review text, so UI substring
    matching is exact; we validate every key is actually present and drop any that
    is not (model paraphrase guard).
  * Pre-computed and frozen: identical for every rater, no live API call in-study.
  * Idempotent + cached: re-running skips PRs already done unless --force.

For PRs with exactly two arms this is a clean A-vs-B diff. For >2 arms, each arm is
diffed against the concatenation of the others (its keys = content unique to it).

Usage:
  source load_env.sh
  python3 human_eval_v3/scripts/generate_review_unique.py
  python3 human_eval_v3/scripts/generate_review_unique.py --force
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

SYSTEM = """You compare two independent code-review notes for the SAME pull request and extract the content that is GENUINELY UNIQUE to "THIS" review — points or specifics that the OTHER review does not make at all.

Critical rule (semantic, not lexical): if both reviews make the same point in different words, that point is SHARED — do NOT extract it. Extract a phrase ONLY when the underlying concern, recommendation, or concrete reference is absent from the other review.

What counts as genuinely unique (extract these):
- a concrete identifier (file path, function/method/class name, test file, API) that appears in THIS review but not the other;
- a concern/recommendation/edge-case THIS review raises that the other never raises in any form.

What does NOT count (never extract):
- generic shared advice both make ("add tests", "update documentation", "risk of regression", "could break functionality");
- the same point worded differently.

Output rules:
- Each phrase MUST be copied VERBATIM (an exact substring) from THIS review, so it can be found again by string match. Do not paraphrase, do not add words.
- Keep each phrase short and distinctive (an identifier, or 2-8 words). Prefer the most distinctive token (e.g. a function name) over a long sentence.
- Each phrase should occur in only the unique block(s) it marks, not in this review's shared/generic sentences.
- De-duplicate.

Output STRICT JSON only, no prose: {"unique": ["...", "..."]}"""


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1] if "```" in raw[3:] else raw
        raw = raw.lstrip("json").strip().strip("`").strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start:end + 1]
    return json.loads(raw)


def unique_keys(this_review: str, other_reviews: str, model: str) -> list[str]:
    prompt = (
        "THIS review:\n\n" + this_review.strip() +
        "\n\n----------\n\nThe OTHER review(s) for the same PR:\n\n" +
        other_reviews.strip() +
        "\n\nExtract the phrases unique to THIS review."
    )
    raw = generate_completion(prompt=prompt, system=SYSTEM, model=model, temperature=0.0)
    try:
        data = _parse_json(raw)
    except Exception as e:  # noqa: BLE001
        print(f"  ! parse error ({e}); treating as empty", flush=True)
        return []
    items = data.get("unique", []) or []
    low = this_review.lower()
    seen, keys = set(), []
    dropped = 0
    for it in items:
        s = str(it).strip()
        if not s:
            continue
        k = s.lower()
        if k not in low:          # model paraphrase guard: must be a real substring
            dropped += 1
            continue
        if k in seen:
            continue
        seen.add(k)
        keys.append(k)
    if dropped:
        print(f"  (dropped {dropped} non-verbatim phrase(s))", flush=True)
    return keys


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--study", default="human_eval_v3/study_data.json")
    ap.add_argument("--model", default="openai:gpt-4o-mini")
    ap.add_argument("--force", action="store_true", help="re-diff even if present")
    args = ap.parse_args()

    path = REPO / args.study
    data = json.loads(path.read_text())

    n_done = n_skip = 0
    for pr in data["prs"]:
        uniq = pr.setdefault("review_unique", {})
        modes = list(pr["reviews"].keys())
        for mode in modes:
            if not args.force and uniq.get(mode) is not None:
                n_skip += 1
                continue
            others = "\n\n====\n\n".join(
                pr["reviews"][m] for m in modes if m != mode
            )
            keys = unique_keys(pr["reviews"][mode], others, args.model)
            uniq[mode] = keys
            n_done += 1
            print(f"PR#{pr['pr_id']:<3} {mode:<16} {len(keys):>2} unique keys: "
                  f"{', '.join(keys[:3])}{' ...' if len(keys) > 3 else ''}", flush=True)

    if n_done:  # don't relabel existing hand-curated markers on a pure-skip run
        data["highlight_meta"] = {
            "method": "llm-semantic",
            "model": args.model,
            "note": "Genuinely-unique content per review, extracted by pairwise semantic "
                    "diff from review text only (blinding-safe, verbatim-validated). "
                    "Shared points (even if paraphrased) carry no key and stay unshaded. "
                    "See generate_review_unique.py.",
        }
    path.write_text(json.dumps(data, indent=2))
    print(f"\nwrote {path.relative_to(REPO)}  (diffed={n_done}, skipped={n_skip})")


if __name__ == "__main__":
    main()
