#!/usr/bin/env python3
"""Discover and inject the test-oracle band.

Pre-registration: ../docs/PRE_REGISTRATION_test_oracle.md

Question: does naming a change's related tests help the reviewer say that a
specific test breaks?  This is the test analogue of Experiment 2's dependency
oracle, and it exists because no design on the coverage rubric can resolve the
test section: the rubric moves 0.6 points against a 0.88-point generation noise
floor, and the model discusses tests whether or not any are named.

Construction.  A symbol whose importers include at least one test file is
renamed (the S1 operator from Experiment 2, drawn from the mutation-testing
literature).  The rename provably breaks every importer, so the test files
among them are a ground-truth oracle: after this change, those tests fail.

Arms are built downstream; the split that matters is that the `kg` arm's
dependency list has the test files **removed**, so `kg_plus_tests` adds exactly
one thing — a labelled Related Tests section naming them.

Grafana only.  Sklearn and Kafka carry zero candidates because their
Experiment 2 scopes exclude test directories entirely; that limitation is
stated in the pre-registration and must be carried into any claim.

No model calls.  Deterministic given the seed.
"""

from __future__ import annotations

import difflib
import json
import random
import re
import sys
from pathlib import Path

EXP2 = Path("/Users/akhattab/ai/experiments/2026-07-05_injection_exp2/harness")
sys.path.insert(0, str(EXP2))

from analyzers import ANALYZERS          # noqa: E402
from common import SCOPES, scope_dir     # noqa: E402
from operators import OPERATORS          # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"
SEED = 2026
TARGET_N = 28
REPO = "grafana"
TEST_RE = re.compile(r"(^|[/_.-])(tests?|specs?)([/_.-]|$)", re.I)

PR_TITLE = "refactor: internal naming cleanup in {mod}"
PR_BODY = ("Small internal cleanup as part of ongoing maintenance. "
           "No behavior change intended.")


def build_diff(scope: Path, edit: dict) -> str | None:
    clean = (scope / edit["file"]).read_text(errors="ignore")
    if clean.count(edit["old"]) != 1:
        return None
    mutant = clean.replace(edit["old"], edit["new"], 1)
    return "".join(difflib.unified_diff(
        clean.splitlines(keepends=True), mutant.splitlines(keepends=True),
        fromfile=f"a/{edit['file']}", tofile=f"b/{edit['file']}", n=3))


def main() -> None:
    rng = random.Random(SEED)
    cfg = SCOPES[REPO]
    scope = scope_dir(REPO)
    if not scope.exists():
        raise SystemExit(f"scope missing: {scope} — run Experiment 2's inject.py first")

    analyzer = ANALYZERS[cfg["language"]](scope)
    syms = analyzer.symbols()
    print(f"[{REPO}] symbols={len(syms)}")

    cands = []
    for s in syms:
        try:
            deps = analyzer.importers(s)
        except Exception:
            continue
        if not deps:
            continue
        tests = sorted(f for f in deps
                       if TEST_RE.search(f) and f != s.get("file"))
        others = sorted(f for f in deps
                        if not TEST_RE.search(f) and f != s.get("file"))
        if tests:
            cands.append({"sym": s, "tests": tests, "others": others,
                          "deps": deps})
    print(f"candidates with >=1 test importer: {len(cands)}")

    # Prefer targets with a non-test dependency too, so the `kg` arm is not
    # empty and the contrast is "tests added" rather than "any context added".
    cands.sort(key=lambda c: (c["others"] == [], -len(c["tests"]),
                              c["sym"]["file"], c["sym"]["name"]))
    rng.shuffle_hint = None

    chosen, used_files, used_syms = [], set(), set()
    for c in cands:
        if len(chosen) >= TARGET_N:
            break
        s = c["sym"]
        if s["file"] in used_files or (s["file"], s["name"]) in used_syms:
            continue
        edit = OPERATORS["S1"](scope, s, cfg["language"])
        if edit is None:
            continue
        diff = build_diff(scope, edit)
        if diff is None or len(diff) > 6000:
            continue
        chosen.append({
            "id": f"{REPO}_T_{len(chosen)+1:02d}",
            "repo": REPO, "language": cfg["language"], "band": "T1",
            "operator": edit["detail"],
            "edit_file": edit["file"], "old": edit["old"], "new": edit["new"],
            "symbol": s.get("name"),
            "true_test_dependents": c["tests"],
            "true_other_dependents": c["others"],
            "n_tests": len(c["tests"]), "n_others": len(c["others"]),
            "resolver": analyzer.resolver,
            "oracle": "static-test-breakage",
            "edge_type": "IMPORTS",
            "pr_title": PR_TITLE.format(mod=Path(edit["file"]).stem),
            "pr_body": PR_BODY,
            "diff": diff,
            "ground_truth": (
                "The rename breaks every importer of this symbol. Among them "
                "these test files, which are not shown in the diff and will "
                f"fail: {', '.join(Path(t).name for t in c['tests'])}."),
        })
        used_files.add(s["file"])
        used_syms.add((s["file"], s["name"]))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps(
        {"seed": SEED, "repo": REPO, "target_n": TARGET_N,
         "operator": "S1 rename (breaks importers)",
         "injections": chosen}, indent=2) + "\n")

    n_with_other = sum(1 for c in chosen if c["n_others"])
    print(f"\nbuilt {len(chosen)} injections -> out/manifest.json")
    print(f"  with a non-test dependency too: {n_with_other}/{len(chosen)}")
    print(f"  median test dependents: "
          f"{sorted(c['n_tests'] for c in chosen)[len(chosen)//2]}")
    for c in chosen[:5]:
        print(f"    {c['id']:<16} {c['symbol']:<26} "
              f"tests={c['n_tests']} others={c['n_others']}")


if __name__ == "__main__":
    main()
