#!/usr/bin/env python3
"""Add a judge from outside the generator's family, and unify the study panels.

Why this exists
---------------
Experiment 1's headline effect is carried by ``openai:gpt-4o``
(``results/JUDGE_LEAVE_ONE_OUT.md``), which is also the model that generated
every review, so self-preference cannot be excluded. Dropping gpt-4o answers a
different question, because it removes the panel's strongest judge as well as its
conflicted one. The missing measurement is a *replacement*: a comparable judge
from a third provider.

Two stages:

1. ``external`` -- score all 160 canonical reviews with ``anthropic:claude-sonnet-4-5``.
   Combined offline with the three stored panels this yields a four-judge
   majority and, more usefully, a three-judge panel with the conflicted judge
   swapped out rather than deleted.
2. ``human`` -- score the human study's 12 reviews with the canonical three-judge
   panel. They were originally scored by a two-judge Gemini-only panel; after
   this all three studies share one panel. The study's own endpoint is its 20
   raters, so this only affects the supporting panel check.

The existing per-judge verdicts are read from
``results/checklist_evaluation_llm_multi__v2.json``, so every aggregate beyond
the new judge's own verdicts costs nothing.

Idempotence: one cache file per (review, panel), written only when all judges in
that panel succeeded. A completed run makes zero API calls; an interrupted one
resumes. Deleting a cache directory is the only way to force re-querying.

Usage::

    source load_env.sh
    python scripts/rejudge_with_external_judge.py --dry-run   # count calls only
    python scripts/rejudge_with_external_judge.py
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from evaluate_reviews import (  # noqa: E402
    EVALUATION_CRITERIA,
    judge_one,
    load_pr_context,
)

EXTERNAL = "anthropic:claude-sonnet-4-5"
CANONICAL = ["openai:gpt-4o-mini", "openai:gpt-4o", "gemini:gemini-2.5-flash"]
CONFLICTED = "openai:gpt-4o"

REVIEWS = REPO_ROOT / "outputs" / "luca_prs_v2"
STORED = REPO_ROOT / "results" / "checklist_evaluation_llm_multi__v2.json"
STUDY = REPO_ROOT / "experiments" / "2026-07-06_user_study_prs"
OUT_MD = REPO_ROOT / "results" / "JUDGE_EXTERNAL_PANEL.md"
OUT_JSON = REPO_ROOT / "results" / "JUDGE_EXTERNAL_PANEL.json"

ALL_IDS = [c.id for c in EVALUATION_CRITERIA]
KG_IDS = [c.id for c in EVALUATION_CRITERIA if getattr(c, "kg_relevant", False)]
WORKERS = 8


def cache_dir(base: Path, tag: str, judges: list[str]) -> Path:
    slug = "_".join(j.replace(":", "-").replace("/", "-") for j in judges)
    d = base / ".judge_cache" / tag / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def judge_cached(path: Path, key: str, judges: list[str], cache: Path,
                 ctx: dict) -> dict:
    """Score one review with every judge in `judges`; cache on full success."""
    cp = cache / f"{key}.json"
    if cp.exists():
        try:
            return json.loads(cp.read_text())
        except Exception:
            pass
    review = path.read_text(errors="ignore")
    out = {}
    for model in judges:
        v = judge_one(review, ctx, model)
        if v.error:
            print(f"  ! {key} {model}: {v.error}", flush=True)
            return {}
        out[model] = v.scores
    cp.write_text(json.dumps(out, indent=1))
    return out


def run_stage(base: Path, tag: str, judges: list[str], ctx_for,
              dry: bool) -> dict[str, dict]:
    files = sorted(base.glob("*.md"))
    cache = cache_dir(base, tag, judges)
    jobs = [(f, f.stem) for f in files]
    todo = [j for j in jobs if not (cache / f"{j[1]}.json").exists()]
    print(f"\n[{tag}] {len(jobs)} reviews x {len(judges)} judge(s): "
          f"{len(jobs) - len(todo)} cached, {len(todo)} to query "
          f"= {len(todo) * len(judges)} API calls")
    if dry:
        return {}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futs = {pool.submit(judge_cached, f, k, judges, cache, ctx_for(k)): k
                for f, k in jobs}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                fut.result()
            except Exception as exc:
                print(f"  ! {futs[fut]}: {exc}", flush=True)
            if i % 20 == 0 or i == len(futs):
                print(f"  {i}/{len(futs)}", flush=True)
    return {p.stem: json.loads(p.read_text()) for p in cache.glob("*.json")}


def majority(per_judge: dict[str, dict]) -> dict[str, int]:
    """Majority over judges, ties to 0; a -1 verdict abstains rather than votes."""
    out = {}
    for cid in ALL_IDS:
        valid = [v for v in (j.get(cid, -1) for j in per_judge.values())
                 if v in (0, 1)]
        out[cid] = 1 if valid and sum(valid) * 2 > len(valid) else 0
    return out


def score(per_judge: dict[str, dict]) -> tuple[int, int]:
    maj = majority(per_judge)
    return sum(maj.values()), sum(maj[c] for c in KG_IDS)


def paired(by_mode: dict, mode: str, idx: int) -> dict:
    prs = sorted(set(by_mode.get("baseline", {})) & set(by_mode.get(mode, {})))
    diffs = [by_mode[mode][p][idx] - by_mode["baseline"][p][idx] for p in prs]
    if not diffs:
        return {}
    obs, n = mean(diffs), len(diffs)
    if n <= 20:
        hits = sum(1 for s in itertools.product((1, -1), repeat=n)
                   if abs(mean(a * b for a, b in zip(s, diffs))) >= abs(obs) - 1e-12)
        p = hits / 2 ** n
    else:
        rng = random.Random(2026)
        B = 20000
        hits = sum(1 for _ in range(B)
                   if abs(mean(rng.choice((1, -1)) * d for d in diffs))
                   >= abs(obs) - 1e-12)
        p = (hits + 1) / (B + 1)
    return {"n": n, "delta": round(obs, 3), "p": round(p, 4)}


def load_stored() -> dict[tuple[int, str], dict[str, dict]]:
    d = json.loads(STORED.read_text())
    return {(e["pr_id"], e["mode"]): {pj["model"]: {k: int(v) for k, v in
                                                    pj["scores"].items()}
                                      for pj in e["per_judge"]}
            for e in d["evaluations"]}


def build_panels(stored: dict, external: dict) -> dict:
    panels = {
        "canonical_3": CANONICAL,
        "plus_external_4": CANONICAL + [EXTERNAL],
        "swap_conflicted_3": [j for j in CANONICAL if j != CONFLICTED] + [EXTERNAL],
        "external_only_1": [EXTERNAL],
    }
    report = {}
    for name, judges in panels.items():
        by_mode: dict[str, dict] = {}
        skipped = 0
        for (pr_id, mode), pj in stored.items():
            merged = dict(pj)
            if EXTERNAL in judges:
                ext = external.get(f"pr{pr_id}_{mode}")
                if not ext:
                    skipped += 1
                    continue
                merged[EXTERNAL] = {k: int(v) for k, v in ext[EXTERNAL].items()}
            sel = {j: merged[j] for j in judges if j in merged}
            if len(sel) != len(judges):
                skipped += 1
                continue
            by_mode.setdefault(mode, {})[pr_id] = score(sel)
        report[name] = {
            "judges": judges, "skipped": skipped,
            "total_of_25": {m: paired(by_mode, m, 0)
                            for m in ("kg", "rag", "hybrid") if m in by_mode},
            "kg_relevant_of_9": {m: paired(by_mode, m, 1)
                                 for m in ("kg", "rag", "hybrid") if m in by_mode},
        }
    return report


def write_report(report: dict, human: dict) -> None:
    def cell(panel, scale, mode):
        d = report[panel][scale].get(mode, {})
        return " n/a |" if not d else f" {d['delta']:+.2f} ({d['p']:.3f}) |"

    def panel_n(panel):
        for scale in ("total_of_25", "kg_relevant_of_9"):
            for d in report[panel][scale].values():
                if d:
                    return d["n"]
        return 0

    L = ["# Judge panel sensitivity with an external judge", "",
         f"**External judge:** `{EXTERNAL}`, a third provider outside the",
         "generator's family. **Generator:** `openai:gpt-4o` for all 160 reviews.",
         "",
         "This answers a narrower question than leave-one-out. Dropping",
         f"`{CONFLICTED}` removes the panel's strongest judge as well as its",
         "conflicted one, so a null there is ambiguous. `swap_conflicted_3` replaces",
         "it with a comparable judge from another provider, and is the row to read.",
         "",
         "## Paired effect against baseline (delta, permutation p)", "",
         "The `n` column is the number of pull requests with a complete set of",
         "verdicts for that panel. A panel with fewer than 40 has not finished and",
         "its row is not comparable with `canonical_3`.",
         "",
         "| Panel | n | kg /25 | kg /9 | rag /25 | rag /9 | hybrid /25 | hybrid /9 |",
         "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for panel in ("canonical_3", "plus_external_4", "swap_conflicted_3",
                  "external_only_1"):
        if panel not in report:
            continue
        row = f"| `{panel}` | {panel_n(panel)} |"
        for m in ("kg", "rag", "hybrid"):
            row += cell(panel, "total_of_25", m) + cell(panel, "kg_relevant_of_9", m)
        L.append(row)
    L += ["", "Panel composition:", ""]
    for panel, d in report.items():
        extra = (f" -- INCOMPLETE, {d['skipped']} of 160 reviews unscored"
                 if d["skipped"] else "")
        L.append(f"- `{panel}`: " + ", ".join(f"`{j}`" for j in d["judges"]) + extra)

    if human:
        L += ["", "## Human study reviews under the canonical panel", "",
              "Originally scored by a two-judge Gemini-only panel, re-scored here with",
              "the canonical three so all three studies share one panel. The study's",
              "own endpoint is its 20 raters; this affects only the supporting check.",
              "", "| Review | total /25 | KG-relevant /9 |", "|---|---:|---:|"]
        for k in sorted(human):
            t, g = human[k]
            L.append(f"| `{k}` | {t} | {g} |")

    L += ["", "---", "",
          "Generated by `scripts/rejudge_with_external_judge.py`. Aggregation is",
          "majority of the panel with ties to 0, matching every other reported",
          "number. Permutation is exact sign-flip for n <= 20, else 20 000 draws",
          "at seed 2026."]
    OUT_MD.write_text("\n".join(L) + "\n")
    OUT_JSON.write_text(json.dumps(
        {"external_judge": EXTERNAL, "panels": report,
         "human_study_canonical_panel": human}, indent=1))
    print(f"\nwrote {OUT_MD.relative_to(REPO_ROOT)}")
    print(f"wrote {OUT_JSON.relative_to(REPO_ROOT)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["external", "human", "both"], default="both")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not a.dry_run and a.stage in ("external", "both") \
            and not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY environment variable required "
              "(run: source load_env.sh)", file=sys.stderr)
        return 1

    external: dict = {}
    if a.stage in ("external", "both"):
        external = run_stage(REVIEWS, "extjudge", [EXTERNAL],
                             lambda k: load_pr_context(
                                 int(re.match(r"pr(\d+)_", k).group(1))),
                             a.dry_run)

    human: dict = {}
    if a.stage in ("human", "both") and (STUDY / "reviews").exists():
        os.environ["PR_CONTEXT_DIR"] = str(STUDY / "evidence")
        raw = run_stage(STUDY / "reviews", "canonical3", CANONICAL,
                        lambda k: {"title": k, "body": "", "pr_id": 0},
                        a.dry_run)
        human = {k: score(v) for k, v in raw.items() if v}

    if a.dry_run:
        print("\ndry run: no API calls made, no files written")
        return 0

    if a.stage in ("external", "both"):
        write_report(build_panels(load_stored(), external), human)
    elif human:
        print(json.dumps(human, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
