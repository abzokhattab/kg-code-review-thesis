#!/usr/bin/env python3
"""Build the scrambled-neighbourhood control arms for the KG block.

Pre-registration: dataset_v2/docs/PRE_REGISTRATION_scrambled.md (seed 2026).

Each arm replaces exactly one rendered list in the v2 evidence pack with the
same number of randomly drawn files from the same repository, so that
relatedness is removed while prompt volume, section set and section order stay
fixed.  Deleting the list instead would shorten the prompt and confound
information loss with prompt shortening.

    scrambled_deps    dependent_files replaced, nearest_tests intact
    scrambled_tests   nearest_tests   replaced, dependent_files intact

What is held constant, per pull request:

  * the number of paths the formatter *displays* in the replaced section,
    which is not the same as the number stored in the pack because
    `format_kg_context` applies a language-cohort filter and a per-section cap;
  * the file-extension multiset of that displayed list, so the drawn paths
    survive the same cohort filter and land at the same rendered count;
  * every other section of the rendered block, byte for byte.

The last two are asserted at build time, not assumed.  A pack that fails
either check is not written.

No model calls.  Deterministic given the seed.

Usage
-----
    python3 scripts/build_scrambled_kg_evidence.py --arm deps
    python3 scripts/build_scrambled_kg_evidence.py --arm tests
    python3 scripts/build_scrambled_kg_evidence.py --arm both
"""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from prnote.note import format_kg_context  # noqa: E402

SEED = 2026
GREP_DIR = BASE / "data/luca_prs_v2"
REPO_ROOT = BASE / "luca_repos"

# Frozen in the pre-registration before any data existed.
ELIGIBLE = {
    "deps": [2, 3, 6, 8, 10, 14, 15, 18, 19, 21, 22, 23, 24, 27, 28, 29, 31,
             32, 33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 44, 47, 48],
    "tests": [2, 3, 6, 8, 9, 10, 14, 15, 18, 19, 21, 22, 23, 24, 27, 28, 31,
              33, 36, 37, 38, 40, 41, 44, 47, 48],
}
ARM = {
    "deps": {"field": "dependent_files", "header": "Files that depend on changes",
             "relationship": "imports", "out": "data/luca_prs_v2_scrambled_deps"},
    "tests": {"field": "nearest_tests", "header": "Related Tests",
              "relationship": "tests", "out": "data/luca_prs_v2_scrambled_tests"},
}

TESTISH = re.compile(r"(^|[/_.-])(tests?|specs?)([/_.-]|$)", re.I)


def displayed(block: str, header: str) -> list[str]:
    m = re.search(rf"\*\*{re.escape(header)}:\*\* (.+)", block)
    return [p.strip() for p in m.group(1).split(",") if p.strip()] if m else []


def sections_of(block: str) -> dict[str, str]:
    """Map section header -> its rendered payload."""
    return {m.group(1): m.group(2)
            for m in re.finditer(r"\*\*([^*]+):\*\* (.+)", block)}


def locate_repo(pack: dict[str, Any], repos: list[Path]) -> Path | None:
    changed = [c["path"] for c in pack.get("changed_files", [])]
    if not changed:
        return None
    best, score = None, 0
    for r in repos:
        s = sum(1 for f in changed if (r / f).exists())
        if s > score:
            best, score = r, s
    return best


_tracked: dict[Path, list[str]] = {}


def tracked_files(repo: Path) -> list[str]:
    if repo not in _tracked:
        out = subprocess.run(["git", "ls-files"], cwd=repo,
                             capture_output=True, text=True, timeout=180)
        _tracked[repo] = [ln for ln in out.stdout.splitlines() if ln]
    return _tracked[repo]


def draw(pool: list[str], want_exts: Counter, exclude: set[str],
         rng: random.Random, testish: bool) -> list[str] | None:
    """Draw one path per requested extension, honouring the exclusions."""
    by_ext: dict[str, list[str]] = {}
    for p in pool:
        if p in exclude:
            continue
        if testish and not TESTISH.search(p):
            continue
        by_ext.setdefault(Path(p).suffix.lower(), []).append(p)
    for v in by_ext.values():
        v.sort()                      # stable order before seeded shuffle

    picked: list[str] = []
    used: set[str] = set()
    for ext, n in sorted(want_exts.items()):
        cand = [p for p in by_ext.get(ext, []) if p not in used]
        if len(cand) < n:
            return None               # cannot match this extension mix fairly
        for p in rng.sample(cand, n):
            picked.append(p)
            used.add(p)
    rng.shuffle(picked)
    return picked


def build_arm(arm: str) -> dict[str, Any]:
    spec = ARM[arm]
    out_dir = BASE / spec["out"]
    out_dir.mkdir(parents=True, exist_ok=True)
    repos = [d for d in REPO_ROOT.iterdir()
             if d.is_dir() and not d.name.startswith(".")]

    written, skipped = [], []
    for pr in ELIGIBLE[arm]:
        rng = random.Random(f"{SEED}:{arm}:{pr}")   # per-PR, so order-independent
        pack = json.loads((GREP_DIR / f"pr{pr}_evidence.json").read_text())
        real_block = format_kg_context(pack) or ""
        target = displayed(real_block, spec["header"])
        if not target:
            skipped.append((pr, "section renders empty"))
            continue

        repo = locate_repo(pack, repos)
        if repo is None:
            skipped.append((pr, "no local checkout"))
            continue

        exclude = {c["path"] for c in pack.get("changed_files", [])}
        for f in ("dependent_files", "nearest_tests"):
            exclude |= {d.get("path", "") for d in pack.get(f, [])}

        picked = draw(tracked_files(repo), Counter(Path(p).suffix.lower()
                                                  for p in target),
                      exclude, rng, testish=(arm == "tests"))
        if picked is None:
            skipped.append((pr, "repo cannot supply the extension mix"))
            continue

        scrambled = json.loads(json.dumps(pack))
        scrambled[spec["field"]] = [
            {"path": p, "relationship": spec["relationship"],
             "source_file": "", "_scrambled": True} for p in picked]
        scrambled.setdefault("metadata", {})["scramble"] = {
            "arm": arm, "seed": SEED, "replaced_field": spec["field"],
            "n_replaced": len(picked),
            "pre_registration": "dataset_v2/docs/PRE_REGISTRATION_scrambled.md",
        }

        # Verify rather than assume: same rendered count in the replaced
        # section, and every other section byte-identical.
        new_block = format_kg_context(scrambled) or ""
        new_target = displayed(new_block, spec["header"])
        a, b = sections_of(real_block), sections_of(new_block)
        if len(new_target) != len(target):
            skipped.append((pr, f"rendered count moved "
                                f"{len(target)} -> {len(new_target)}"))
            continue
        if set(a) != set(b):
            skipped.append((pr, "section set changed"))
            continue
        drifted = [h for h in a if h != spec["header"] and a[h] != b[h]]
        if drifted:
            skipped.append((pr, f"other sections drifted: {drifted}"))
            continue
        if set(new_target) & set(target):
            skipped.append((pr, "a true path leaked into the scramble"))
            continue

        (out_dir / f"pr{pr}_evidence.json").write_text(
            json.dumps(scrambled, indent=2))
        written.append({"pr_id": pr, "repo": repo.name, "n": len(picked),
                        "real_chars": len(real_block),
                        "scrambled_chars": len(new_block),
                        "char_delta": len(new_block) - len(real_block)})

    return {"arm": arm, "written": written, "skipped": skipped}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["deps", "tests", "both"], default="both")
    args = ap.parse_args()
    arms = ["deps", "tests"] if args.arm == "both" else [args.arm]

    report: dict[str, Any] = {"seed": SEED, "arms": {}}
    for arm in arms:
        r = build_arm(arm)
        report["arms"][arm] = r
        deltas = [w["char_delta"] for w in r["written"]]
        print(f"\n=== arm {arm} ===")
        print(f"  written : {len(r['written'])}/{len(ELIGIBLE[arm])} "
              f"-> {ARM[arm]['out']}")
        if deltas:
            print(f"  rendered-length change: median "
                  f"{sorted(deltas)[len(deltas)//2]:+d} chars, "
                  f"range [{min(deltas):+d}, {max(deltas):+d}]")
        for pr, why in r["skipped"]:
            print(f"  SKIP PR{pr}: {why}")

    (BASE / "results").mkdir(exist_ok=True)
    (BASE / "results/SCRAMBLE_BUILD_LOG.json").write_text(
        json.dumps(report, indent=2))
    print("\nwrote results/SCRAMBLE_BUILD_LOG.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
