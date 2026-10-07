#!/usr/bin/env python3
"""Consolidate the four 40-PR generator runs into one cross-generator comparison.

Experiment 1's headline uses gpt-4o as the generator. Three further full 40-PR
runs exist with the same evidence packs, the same lexical graph block, the same
three-judge panel and the same 25-criterion rubric, differing only in which model
wrote the reviews. They were never consolidated into a reportable artefact.

Two things are computed and they must not be conflated:

  Within-generator paired contrasts (kg/rag/hybrid vs baseline on the same PR).
  These are valid: arm-to-arm length differences inside a generator are small,
  and every arm shares the generator, prompt, panel and rubric.

  Between-generator score levels. These are CONFOUNDED with verbosity. The
  alternative generators write roughly twice as many words per review, and the
  rubric is a mention-check instrument on which length mechanically buys
  criteria. The script therefore reports mean review length beside every level
  so the confound cannot be read past, and computes the within-generator
  length/score coupling that bounds it.

Statistics are imported from scripts/bootstrap_stats.py so they match every other
number in the project.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts.bootstrap_stats import (  # noqa: E402
    bootstrap_mean_ci,
    paired_bootstrap_diff_ci,
    paired_permutation_p,
)

MODES = ("baseline", "kg", "rag", "hybrid")

# generator label -> (panel suffix, review output dir)
RUNS = {
    "gpt-4o (headline)": ("v2", "luca_prs_v2"),
    "claude-haiku-4.5": ("v2_claude", "luca_prs_v2_claude"),
    "gemini-2.5-flash": ("v2_gemini", "luca_prs_v2_gemini"),
    "deepseek-v3": ("v2_deepseek", "luca_prs_v2_deepseek"),
}


def load_scores(suffix: str) -> dict[str, dict[int, tuple[int, int]]]:
    path = REPO / "results" / f"checklist_evaluation_llm_multi__{suffix}.json"
    panel = json.loads(path.read_text())
    out: dict[str, dict[int, tuple[int, int]]] = {m: {} for m in MODES}
    for ev in panel["evaluations"]:
        if ev["mode"] in out:
            out[ev["mode"]][ev["pr_id"]] = (ev["total_score"], ev["kg_relevant_score"])
    return out


def load_lengths(outdir: str) -> dict[str, dict[int, int]]:
    base = REPO / "outputs" / outdir
    out: dict[str, dict[int, int]] = {m: {} for m in MODES}
    for mode in MODES:
        for f in base.glob(f"pr*_{mode}.md"):
            stem = f.name.split("_")[0]
            if not stem.startswith("pr"):
                continue
            try:
                pr_id = int(stem[2:])
            except ValueError:
                continue
            out[mode][pr_id] = len(f.read_text().split())
    return out


def spearman(xs: list[float], ys: list[float]) -> float:
    def ranks(vs: list[float]) -> list[float]:
        order = sorted(range(len(vs)), key=lambda i: vs[i])
        r = [0.0] * len(vs)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vs[order[j + 1]] == vs[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-md", default=str(REPO / "results" / "CROSS_GENERATOR_v2.md"))
    ap.add_argument("--out-json", default=str(REPO / "results" / "CROSS_GENERATOR_v2.json"))
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--n-perm", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    report: dict = {"seed": args.seed, "generators": {}}
    for label, (suffix, outdir) in RUNS.items():
        scores = load_scores(suffix)
        words = load_lengths(outdir)
        rng = random.Random(args.seed)
        entry: dict = {"levels": {}, "paired": {}, "words": {}, "length_coupling": {}}

        for mode in MODES:
            prs = sorted(scores[mode])
            for key, idx in (("total", 0), ("kgrel", 1)):
                xs = [scores[mode][p][idx] for p in prs]
                mean, lo, hi = bootstrap_mean_ci(xs, args.n_boot, rng)
                entry["levels"].setdefault(mode, {})[key] = {"mean": mean, "lo": lo, "hi": hi}
            if words[mode]:
                entry["words"][mode] = st.mean(words[mode].values())

        for mode in MODES:
            if mode == "baseline":
                continue
            prs = sorted(set(scores["baseline"]) & set(scores[mode]))
            for key, idx in (("total", 0), ("kgrel", 1)):
                pairs = [(scores["baseline"][p][idx], scores[mode][p][idx]) for p in prs]
                d, lo, hi, sd = paired_bootstrap_diff_ci(pairs, args.n_boot, rng)
                p = paired_permutation_p(pairs, args.n_perm, rng)
                entry["paired"].setdefault(mode, {})[key] = {
                    "n": len(pairs), "delta": d, "lo": lo, "hi": hi, "p": p,
                    "d_z": (d / sd) if sd else 0.0,
                }
            shared = sorted(set(words["baseline"]) & set(words[mode]) & set(prs))
            if len(shared) > 3:
                dlen = [words[mode][p] - words["baseline"][p] for p in shared]
                for key, idx in (("total", 0), ("kgrel", 1)):
                    dsc = [scores[mode][p][idx] - scores["baseline"][p][idx] for p in shared]
                    entry["length_coupling"].setdefault(mode, {})[key] = spearman(dlen, dsc)
                entry["length_coupling"][mode]["mean_delta_words"] = st.mean(dlen)
        report["generators"][label] = entry
        print(f"  computed {label}")

    L = [
        "# Cross-generator comparison — Experiment 1 arms under four generators",
        "",
        "**Held fixed:** evidence packs, lexical graph block, prompts, 25-criterion rubric, "
        "three-judge panel (gpt-4o-mini, gpt-4o, gemini-2.5-flash), majority vote with ties to 0, "
        "40 PRs, T = 0.0.  ",
        "**Varied:** the generator only.  ",
        f"**Method:** percentile bootstrap (B={args.n_boot}), paired sign-flip permutation "
        f"(B={args.n_perm}), seed={args.seed}, via `scripts/bootstrap_stats.py`.",
        "",
        "## 1. Within-generator paired effect (the valid comparison)",
        "",
        "| Generator | kg Δ /25 | p | kg Δ /9 | p | rag Δ /9 | p | hybrid Δ /9 | p |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label in RUNS:
        e = report["generators"][label]["paired"]
        L.append(
            f"| {label} | {e['kg']['total']['delta']:+.2f} | {e['kg']['total']['p']:.3f} "
            f"| {e['kg']['kgrel']['delta']:+.2f} | {e['kg']['kgrel']['p']:.3f} "
            f"| {e['rag']['kgrel']['delta']:+.2f} | {e['rag']['kgrel']['p']:.3f} "
            f"| {e['hybrid']['kgrel']['delta']:+.2f} | {e['hybrid']['kgrel']['p']:.3f} |"
        )

    L += [
        "",
        "## 2. Score levels beside review length (confounded — do not read as capability)",
        "",
        "| Generator | baseline /25 | baseline /9 | baseline words | kg words |",
        "|---|---:|---:|---:|---:|",
    ]
    for label in RUNS:
        g = report["generators"][label]
        L.append(
            f"| {label} | {g['levels']['baseline']['total']['mean']:.2f} "
            f"| {g['levels']['baseline']['kgrel']['mean']:.2f} "
            f"| {g['words'].get('baseline', float('nan')):.0f} "
            f"| {g['words'].get('kg', float('nan')):.0f} |"
        )

    L += [
        "",
        "## 3. Within-generator length/score coupling for the kg arm",
        "",
        "Spearman correlation between the per-PR change in review length and the per-PR "
        "change in score, kg vs baseline. A high value would mean the kg arm's score "
        "advantage is a verbosity effect.",
        "",
        "| Generator | mean Δwords | ρ(Δwords, Δ/25) | ρ(Δwords, Δ/9) |",
        "|---|---:|---:|---:|",
    ]
    for label in RUNS:
        c = report["generators"][label]["length_coupling"].get("kg", {})
        L.append(f"| {label} | {c.get('mean_delta_words', float('nan')):+.0f} "
                 f"| {c.get('total', float('nan')):+.2f} | {c.get('kgrel', float('nan')):+.2f} |")

    L += [
        "",
        "## Reading",
        "",
        "Section 1 is the reportable result. Section 2 exists to prevent a level comparison: "
        "the alternative generators write roughly twice as many words per review, and on a "
        "mention-check rubric length buys criteria, so the higher baselines are not evidence "
        "of higher capability. Section 3 bounds the verbosity account of the within-generator "
        "kg effect.",
        "",
    ]

    Path(args.out_md).write_text("\n".join(L) + "\n")
    Path(args.out_json).write_text(json.dumps(report, indent=1))
    print(f"wrote {Path(args.out_md).relative_to(REPO)}")
    print(f"wrote {Path(args.out_json).relative_to(REPO)}")


if __name__ == "__main__":
    main()
