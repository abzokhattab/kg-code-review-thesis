#!/usr/bin/env python3
"""Analyse the section-deletion ablation using its three-judge verdicts.

Background
----------
The ablation was generated on 2026-03-05 (`scripts/run_ablation_study.py`,
51 reviews over the v1 25-PR set) and written up in `results/ablation_report.md`
against a single `gpt-4o-mini` judge, with no significance testing.  That
write-up is unusable: it reported removing tests *and* dependencies together
(6.6%) hurting less than removing tests alone (10.6%), which cannot happen if
the effects are real.

On 2026-05-31 all 51 reviews were re-judged with the **canonical three-judge
panel** (`gpt-4o-mini`, `gpt-4o`, `gemini-2.5-flash`) against the current
25-criterion rubric and the current 9-criterion KG-relevant subscale, into
`results/ablation_3judge/`.  Nothing in the repository ever read those files.
This script does.

It runs the paired contrasts the March write-up lacked, and checks whether the
non-monotonicity that discredited it survives the better instrument.

Scope caveat, carried into every output: these reviews sit on the **v1**
25-PR dataset and the v1 prompt, not the v2 40-PR headline configuration.  The
contrast is internally consistent — full_kg and the ablated arms share a
generator, prompt, dataset and judge panel — but its magnitudes are not
directly comparable to the v2 headline.

Outputs
-------
results/SECTION_ABLATION_3JUDGE.{md,json}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

BASE = Path(__file__).resolve().parent.parent
ABL_DIR = BASE / "results/ablation_3judge"
FULL_PANEL = BASE / "results/checklist_evaluation_llm_multi.json"
B = 200_000
SEED = 2026
ALPHA = 0.05

SCALES = {"kg_relevant": "kg_relevant_score", "total": "total_score"}
ARMS = {
    "kg_no_tests": "tests section deleted",
    "kg_no_deps": "dependency section deleted",
    "kg_minimal": "both sections deleted",
}


def load_full() -> dict[int, dict[str, int]]:
    out = {}
    for e in json.loads(FULL_PANEL.read_text())["evaluations"]:
        if e["mode"] == "kg":
            out[e["pr_id"]] = {k: e[v] for k, v in SCALES.items()}
    return out


def load_arm(arm: str) -> dict[int, dict[str, int]]:
    out = {}
    for f in ABL_DIR.glob(f"pr*_{arm}_3judge.json"):
        d = json.loads(f.read_text())
        if d["mode"] != arm:
            continue
        out[d["pr_id"]] = {k: d[v] for k, v in SCALES.items()}
    return out


def perm_p(d: np.ndarray, rng: np.random.Generator) -> float:
    obs, hits, done = abs(d.mean()), 0, 0
    while done < B:
        n = min(20_000, B - done)
        s = rng.choice((-1.0, 1.0), size=(n, d.size))
        hits += int(np.sum(np.abs((s * d).mean(axis=1)) >= obs - 1e-12))
        done += n
    return (hits + 1) / (B + 1)


def boot_ci(d: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    means, done = np.empty(B), 0
    while done < B:
        n = min(20_000, B - done)
        idx = rng.integers(0, d.size, size=(n, d.size))
        means[done:done + n] = d[idx].mean(axis=1)
        done += n
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def holm(p: dict[str, float]) -> dict[str, float]:
    order = sorted(p, key=lambda k: p[k])
    m, adj, run = len(order), {}, 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (m - i) * p[k]))
        adj[k] = run
    return adj


def main() -> None:
    full = load_full()
    rng = np.random.default_rng(SEED)
    results: dict[str, dict[str, Any]] = {}

    for arm in ARMS:
        abl = load_arm(arm)
        for scale in SCALES:
            ids = sorted(set(full) & set(abl))
            d = np.array([full[p][scale] - abl[p][scale] for p in ids], float)
            lo, hi = boot_ci(d, rng)
            sd = float(d.std(ddof=1))
            results[f"{arm}|{scale}"] = {
                "arm": arm, "label": ARMS[arm], "scale": scale, "n": len(ids),
                "pr_ids": ids,
                "full_mean": float(np.mean([full[p][scale] for p in ids])),
                "ablated_mean": float(np.mean([abl[p][scale] for p in ids])),
                "mean_drop": float(d.mean()), "sd": sd, "ci95": [lo, hi],
                "d_z": float(d.mean() / sd) if sd else None,
                "p_raw": perm_p(d, rng),
                "n_worse": int((d > 0).sum()), "n_tie": int((d == 0).sum()),
                "n_better": int((d < 0).sum()),
            }

    for scale in SCALES:
        keys = [k for k in results if k.endswith(f"|{scale}")]
        adj = holm({k: results[k]["p_raw"] for k in keys})
        for k in keys:
            results[k]["p_holm"] = adj[k]
            results[k]["significant"] = adj[k] < ALPHA

    # The coherence check the March write-up failed: on the 16 pull requests
    # where all three arms exist, removing both sections cannot hurt less than
    # removing either one alone.
    coherence = {}
    common = sorted(set(load_arm("kg_minimal")) & set(load_arm("kg_no_tests"))
                    & set(load_arm("kg_no_deps")) & set(full))
    for scale in SCALES:
        arms = {a: load_arm(a) for a in ARMS}
        drops = {a: float(np.mean([full[p][scale] - arms[a][p][scale]
                                   for p in common])) for a in ARMS}
        coherence[scale] = {
            "n": len(common), "drops": drops,
            "monotonic": bool(drops["kg_minimal"] >= drops["kg_no_tests"] - 1e-9
                              and drops["kg_minimal"] >= drops["kg_no_deps"] - 1e-9),
        }

    out = {"meta": {"B": B, "seed": SEED, "alpha": ALPHA,
                    "judges": ["openai:gpt-4o-mini", "openai:gpt-4o",
                               "gemini:gemini-2.5-flash"],
                    "dataset": "v1 25-PR (data/luca_prs_fixed), v1 prompt",
                    "supersedes": "results/ablation_report.md"},
           "contrasts": results, "coherence": coherence}
    (BASE / "results/SECTION_ABLATION_3JUDGE.json").write_text(json.dumps(out, indent=2))
    write_md(out)

    print(f"{'arm':<14} {'scale':<12} {'n':>3} {'full':>6} {'abl':>6} "
          f"{'drop':>7} {'95% CI':>18} {'d_z':>6} {'p':>6} {'holm':>6}")
    for k, v in results.items():
        print(f"{v['arm']:<14} {v['scale']:<12} {v['n']:>3} "
              f"{v['full_mean']:>6.2f} {v['ablated_mean']:>6.2f} "
              f"{v['mean_drop']:>+7.3f} "
              f"[{v['ci95'][0]:+.2f}, {v['ci95'][1]:+.2f}]".ljust(19)
              + f"{v['d_z'] if v['d_z'] is not None else 0:>6.2f} "
                f"{v['p_raw']:>6.3f} {v['p_holm']:>6.3f}")
    print("\ncoherence (removing both must not hurt less than removing one):")
    for s, c in coherence.items():
        dd = ", ".join(f"{a}={x:+.2f}" for a, x in c["drops"].items())
        print(f"  {s:<12} n={c['n']}  {dd}  -> "
              f"{'coherent' if c['monotonic'] else 'NON-MONOTONIC'}")
    print("\nwrote results/SECTION_ABLATION_3JUDGE.{md,json}")


def write_md(out: dict[str, Any]) -> None:
    r, c = out["contrasts"], out["coherence"]
    L = ["# Section-deletion ablation — three-judge re-analysis", "",
         "The 51 ablated reviews generated on 2026-03-05 were re-judged on "
         "2026-05-31 with the canonical three-judge panel "
         "(`gpt-4o-mini`, `gpt-4o`, `gemini-2.5-flash`) into "
         "`results/ablation_3judge/`. Those verdicts had never been analysed. "
         "This file supersedes `results/ablation_report.md`, which used a "
         "single `gpt-4o-mini` judge and reported no significance test.", "",
         "**Scope.** These reviews sit on the v1 25-PR dataset and the v1 "
         "prompt, not the v2 40-PR headline configuration. Generator, prompt, "
         "dataset and judge panel are shared across `full_kg` and the ablated "
         "arms, so the contrast is internally valid, but the magnitudes are "
         "not directly comparable to the v2 headline.", "",
         f"Paired sign-flip permutation and paired bootstrap, B = {B:,}, "
         f"seed {SEED}, Holm-corrected within each scale.", "",
         "## Contrasts (positive drop = the deleted section was helping)", "",
         "| Section deleted | Scale | n | full_kg | ablated | drop | 95% CI | d_z | p | p (Holm) |",
         "|---|---|---:|---:|---:|---:|---|---:|---:|---:|"]
    for v in r.values():
        L.append(f"| {v['label']} | "
                 f"{'KG-rel /9' if v['scale']=='kg_relevant' else 'total /25'} | "
                 f"{v['n']} | {v['full_mean']:.2f} | {v['ablated_mean']:.2f} | "
                 f"{v['mean_drop']:+.3f} | "
                 f"[{v['ci95'][0]:+.2f}, {v['ci95'][1]:+.2f}] | "
                 f"{v['d_z']:+.2f} | {v['p_raw']:.3f} | {v['p_holm']:.3f} |")
    L += ["", "## Coherence check", "",
          "The March write-up was discredited by a non-monotonicity: removing "
          "both sections scored a smaller drop than removing tests alone, "
          "which is impossible if the effects are real. On the pull requests "
          "where all three arms exist:", ""]
    for s, cc in c.items():
        dd = ", ".join(f"`{a}` {x:+.2f}" for a, x in cc["drops"].items())
        L.append(f"* **{'KG-relevant /9' if s=='kg_relevant' else 'total /25'}** "
                 f"(n = {cc['n']}): {dd} — "
                 f"**{'coherent' if cc['monotonic'] else 'still non-monotonic'}**")
    L += ["",
          "## Power", "",
          "At n = 16-19 these contrasts detect only large effects. A drop of "
          "the full KG effect would be visible; a drop of half of it would "
          "not reliably be. Read non-significant rows as uninformative about "
          "small effects rather than as evidence of no effect.", ""]
    (BASE / "results/SECTION_ABLATION_3JUDGE.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
