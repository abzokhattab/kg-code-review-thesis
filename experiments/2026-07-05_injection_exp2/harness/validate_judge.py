#!/usr/bin/env python3
"""Stage F: objective judge validation (pre-reg §9).  $0.

For every judged cell, compares each judge's verdict against a deterministic
text oracle: does the review literally mention >= 1 true dependent file
(basename or module stem) for structural bands?  Reports per-judge
agreement with the oracle, plus per-judge false-positive candidates
(judge said detected, oracle found no dependent named) for manual audit.

The oracle is conservative for detection (string containment), so
judge-vs-oracle disagreement is a flag list, not an automatic error count —
that nuance is written into the report.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ARMS, JUDGES, OUT, load_manifest  # noqa: E402

REVIEWS = OUT / "reviews"
JUDGMENTS = OUT / "judgments"


def oracle_mentions_dependent(inj: dict, text: str) -> bool:
    tl = text.lower()
    for d in inj["true_dependents"]:
        base = Path(d).name.lower()
        stem = Path(d).stem.lower()
        if base in tl or (len(stem) > 4 and stem in tl):
            return True
    return False


def main():
    inj_all = [i for i in load_manifest() if i["band"].startswith("S")]
    per_judge = {jm: {"agree": 0, "total": 0, "fp": [], "fn": []} for jm in JUDGES}

    for inj in inj_all:
        for arm in ARMS:
            md = REVIEWS / inj["id"] / f"{arm}.md"
            if not md.exists():
                continue
            oracle = oracle_mentions_dependent(inj, md.read_text())
            for jm in JUDGES:
                jm_safe = jm.replace(":", "_").replace("/", "_")
                p = JUDGMENTS / inj["id"] / f"{arm}__{jm_safe}.json"
                if not p.exists():
                    continue
                v = json.loads(p.read_text()).get("detected")
                if v is None:
                    continue
                st = per_judge[jm]
                st["total"] += 1
                if v == oracle:
                    st["agree"] += 1
                elif v and not oracle:
                    st["fp"].append(f"{inj['id']}/{arm}")
                else:
                    st["fn"].append(f"{inj['id']}/{arm}")

    L = ["# Judge validation vs deterministic mention-oracle (structural bands)",
         "",
         "Oracle = review text literally names >= 1 true dependent file. "
         "The oracle is a conservative lexical check; disagreements are audit "
         "flags, not automatic judge errors (a judge may rightly reject a "
         "mention that names the file without identifying the breakage).", "",
         "| Judge | Agreement | Detected-without-mention (FP-flag) | Mention-without-detected (FN-flag) |",
         "|---|---:|---:|---:|"]
    for jm, st in per_judge.items():
        rate = st["agree"] / st["total"] if st["total"] else 0
        L.append(f"| {jm} | {st['agree']}/{st['total']} ({rate:.0%}) | "
                 f"{len(st['fp'])} | {len(st['fn'])} |")
    L += ["", "## FP flags (judge said detected; no dependent named)"]
    for jm, st in per_judge.items():
        if st["fp"]:
            L.append(f"- **{jm}**: {', '.join(st['fp'][:20])}")
    (OUT / "JUDGE_VALIDATION.md").write_text("\n".join(L) + "\n")
    print(f"wrote {OUT/'JUDGE_VALIDATION.md'}")


if __name__ == "__main__":
    main()
