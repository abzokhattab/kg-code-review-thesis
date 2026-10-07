#!/usr/bin/env python3
"""Analyse the Experiment 2 feature ablation.

Pre-registration:
experiments/2026-07-05_injection_exp2/docs/PRE_REGISTRATION_feature_ablation.md

The deployed `kg` arm supplies two kinds of dependency evidence at once: a
lexical grep file list (10.2% precise, file-level) and Joern-resolved call
edges (function-level).  Two arms hold everything else fixed and supply one
each, so the detection rate attributes the cross-file finding to a kind of edge:

    kg_deps_only    lexical file list only  (call_graph_edges emptied)
    kg_edges_only   Joern call edges only   (dependent_files emptied)

Runs on Experiment 2 rather than the coverage rubric because the rubric moves
0.6 points against a measured 0.88-point generation noise floor, while
Experiment 2's structural bands run 0/28 to 26/28 on a binary outcome.

Outputs
-------
results/EXP2_FEATURE_ABLATION.{md,json}
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

BASE = Path("/Users/akhattab/ai")
EXP = BASE / "experiments/2026-07-05_injection_exp2"
JUDG = EXP / "out/judgments"
SEED = 2026
B_BOOT = 10_000
B_PERM = 20_000

JUDGES = ["openai:gpt-4o-mini", "openai:gpt-4o", "gemini:gemini-2.5-flash"]
ARMS = ["baseline", "rag", "kg_deps_only", "kg_edges_only", "kg",
        "kg_joern_inherit", "kg_idealised", "hybrid"]
STRUCTURAL = ["S1", "S2", "S3", "S4", "S5"]
LOCAL = ["L1", "L2"]


def slug(model: str) -> str:
    return model.replace(":", "_").replace("/", "_")


def detected(inj_id: str, arm: str) -> bool | None:
    """Majority of the three judges, ties to 0 (the Experiment 2 rule)."""
    votes = []
    for j in JUDGES:
        p = JUDG / inj_id / f"{arm}__{slug(j)}.json"
        if p.exists():
            votes.append(bool(json.loads(p.read_text()).get("detected")))
    if len(votes) < len(JUDGES):
        return None
    return sum(votes) > len(votes) / 2


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    z = 1.959963985
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def mcnemar_exact(a: list[bool], b: list[bool]) -> tuple[int, int, float]:
    """Two-sided exact McNemar on paired binary outcomes."""
    n01 = sum(1 for x, y in zip(a, b) if x and not y)
    n10 = sum(1 for x, y in zip(a, b) if y and not x)
    n = n01 + n10
    if n == 0:
        return n01, n10, 1.0
    k = min(n01, n10)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return n01, n10, min(1.0, 2 * tail)


def perm_p(a: list[bool], b: list[bool], rng: np.random.Generator) -> float:
    """Paired permutation on the rate difference: swap within pairs."""
    x = np.array(a, float)
    y = np.array(b, float)
    obs = abs(x.mean() - y.mean())
    d = x - y
    signs = rng.choice((-1.0, 1.0), size=(B_PERM, d.size))
    return float((np.sum(np.abs((signs * d).mean(axis=1)) >= obs - 1e-12) + 1)
                 / (B_PERM + 1))


def boot_ci(a: list[bool], b: list[bool],
            rng: np.random.Generator) -> tuple[float, float]:
    d = np.array(a, float) - np.array(b, float)
    idx = rng.integers(0, d.size, size=(B_BOOT, d.size))
    means = d[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def holm(p: dict[str, float]) -> dict[str, float]:
    order = sorted(p, key=lambda k: p[k])
    m, adj, run = len(order), {}, 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (m - i) * p[k]))
        adj[k] = run
    return adj


def main() -> None:
    manifest = json.loads((EXP / "out/manifest.json").read_text())["injections"]
    rng = np.random.default_rng(SEED)

    bands = {i["id"]: i["band"] for i in manifest}
    groups = {
        "structural": [i for i, b in bands.items() if b in STRUCTURAL],
        "local_control": [i for i, b in bands.items() if b in LOCAL],
    }

    out: dict[str, Any] = {
        "meta": {"seed": SEED, "B_boot": B_BOOT, "B_perm": B_PERM,
                 "judges": JUDGES, "rule": "majority of 3, ties to 0",
                 "pre_registration":
                     "experiments/2026-07-05_injection_exp2/docs/"
                     "PRE_REGISTRATION_feature_ablation.md"},
        "groups": {},
    }

    for gname, ids in groups.items():
        ids = sorted(i for i in ids
                     if all(detected(i, a) is not None for a in ARMS))
        det = {a: [detected(i, a) for i in ids] for a in ARMS}

        rates = {}
        for a in ARMS:
            k = sum(det[a])
            lo, hi = wilson(k, len(ids))
            rates[a] = {"k": k, "n": len(ids), "rate": k / len(ids) if ids else 0,
                        "wilson95": [lo, hi]}

        contrasts = {}
        for a, ref in (("kg_deps_only", "baseline"), ("kg_edges_only", "baseline"),
                       ("kg_deps_only", "kg"), ("kg_edges_only", "kg")):
            n01, n10, pm = mcnemar_exact(det[ref], det[a])
            lo, hi = boot_ci(det[a], det[ref], rng)
            contrasts[f"{a} - {ref}"] = {
                "delta": rates[a]["rate"] - rates[ref]["rate"],
                "ci95": [lo, hi],
                "discordant_ref_only": n01, "discordant_arm_only": n10,
                "p_mcnemar_exact": pm,
                "p_perm": perm_p(det[a], det[ref], rng),
            }
        adj = holm({k: v["p_mcnemar_exact"] for k, v in contrasts.items()})
        for k, v in contrasts.items():
            v["p_holm"] = adj[k]
            v["significant"] = adj[k] < 0.05

        out["groups"][gname] = {"ids": ids, "rates": rates,
                                "contrasts": contrasts}

    (BASE / "results/EXP2_FEATURE_ABLATION.json").write_text(
        json.dumps(out, indent=2))
    write_md(out)

    for gname, g in out["groups"].items():
        print(f"\n=== {gname} (n={len(g['ids'])}) ===")
        for a in ARMS:
            r = g["rates"][a]
            print(f"  {a:<18} {r['k']:>2}/{r['n']:<3} {r['rate']:>6.1%}  "
                  f"[{r['wilson95'][0]:.2f}, {r['wilson95'][1]:.2f}]")
        print(f"  {'contrast':<28} {'Δ':>7} {'McNemar':>9} {'Holm':>7}")
        for k, v in g["contrasts"].items():
            print(f"  {k:<28} {v['delta']:>+7.1%} "
                  f"{v['p_mcnemar_exact']:>9.4f} {v['p_holm']:>7.4f}"
                  f"{'  **' if v['significant'] else ''}")
    print("\nwrote results/EXP2_FEATURE_ABLATION.{md,json}")


def write_md(out: dict[str, Any]) -> None:
    L = ["# Experiment 2 feature ablation — which kind of edge finds the defect",
         "",
         "Pre-registered in "
         "`experiments/2026-07-05_injection_exp2/docs/PRE_REGISTRATION_feature_ablation.md` "
         "before any review existed.", "",
         "The deployed `kg` arm supplies two kinds of dependency evidence at "
         "once. These arms hold everything else fixed — generator, prompt, "
         "diff, changed-file list, changed-symbol list — and supply one each:",
         "",
         "| Arm | Evidence supplied | Granularity | Precision |",
         "|---|---|---|---|",
         "| `kg_deps_only` | lexical `grep` file list | file | 10.2% |",
         "| `kg_edges_only` | Joern CPG call edges | function | program analysis |",
         "",
         "Run on Experiment 2 rather than the coverage rubric because the "
         "rubric moves 0.6 points against a measured 0.88-point generation "
         "noise floor, while these bands run 0/28 to 26/28 on a binary "
         "outcome.", ""]
    for gname, g in out["groups"].items():
        n = len(g["ids"])
        L += [f"## {gname.replace('_', ' ')} bands (n = {n})", "",
              "| Arm | Detected | Rate | 95% Wilson |", "|---|---:|---:|---|"]
        for a in ARMS:
            r = g["rates"][a]
            L.append(f"| `{a}` | {r['k']}/{r['n']} | {r['rate']:.0%} | "
                     f"[{r['wilson95'][0]:.2f}, {r['wilson95'][1]:.2f}] |")
        L += ["", "| Contrast | Δ rate | 95% CI | discordant | McNemar (exact) | p (Holm) |",
              "|---|---:|---|---:|---:|---:|"]
        for k, v in g["contrasts"].items():
            L.append(f"| {k} | {v['delta']:+.0%} | "
                     f"[{v['ci95'][0]:+.2f}, {v['ci95'][1]:+.2f}] | "
                     f"{v['discordant_arm_only']}/{v['discordant_ref_only']} | "
                     f"{v['p_mcnemar_exact']:.4f} | {v['p_holm']:.4f}"
                     f"{' **' if v['significant'] else ''} |")
        L.append("")
    (BASE / "results/EXP2_FEATURE_ABLATION.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
