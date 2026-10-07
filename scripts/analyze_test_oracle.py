#!/usr/bin/env python3
"""Analyse the test-oracle band.

Pre-registration:
experiments/2026-09-06_test_oracle/docs/PRE_REGISTRATION_test_oracle.md

Question: does naming a change's related tests help the reviewer say that a
specific test breaks?  Runs on a ground-truthed binary outcome because five
attempts on the 25-criterion coverage rubric could not resolve the test
section — the rubric's T3 criterion is satisfied by generic test talk, which
this analysis measures separately and finds saturated in every arm.

Arms.  A symbol whose importers include test files is renamed, so those tests
provably fail.  `kg` carries the dependency list with the test files removed;
the two `kg_plus_tests*` arms add exactly one thing, a Related Tests section,
sourced either from ground truth or from the deployed filename-convention
finder that the real pipeline would have used.

Outputs
-------
results/TEST_ORACLE.{md,json}
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

BASE = Path("/Users/akhattab/ai")
EXP = BASE / "experiments/2026-09-06_test_oracle"
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "scripts"))
sys.path.insert(0, str(BASE / "experiments/2026-07-05_injection_exp2/harness"))

SEED = 2026
B_BOOT = 10_000
B_PERM = 20_000
JUDGES = ["openai:gpt-4o-mini", "openai:gpt-4o", "gemini:gemini-2.5-flash"]
ARMS = ["baseline", "kg", "kg_plus_tests_lexical", "kg_plus_tests"]
LABEL = {
    "baseline": "diff only",
    "kg": "dependencies, test files removed",
    "kg_plus_tests_lexical": "+ tests from the deployed filename finder",
    "kg_plus_tests": "+ tests from ground truth (ceiling)",
}
CONTRASTS = [
    ("kg", "baseline"),
    ("kg_plus_tests_lexical", "kg"),
    ("kg_plus_tests", "kg"),
    ("kg_plus_tests", "kg_plus_tests_lexical"),
]


def verdict(inj_id: str, arm: str, key: str) -> bool | None:
    votes = []
    for j in JUDGES:
        p = EXP / "out/judgments" / inj_id / f"{arm}__{j.replace(':', '_')}.json"
        if p.exists():
            votes.append(bool(json.loads(p.read_text())[key]))
    return None if len(votes) < len(JUDGES) else sum(votes) > len(votes) / 2


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    z = 1.959963985
    p, d = k / n, 1 + 1.959963985 ** 2 / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def mcnemar_exact(ref: list[bool], arm: list[bool]) -> tuple[int, int, float]:
    n_ref = sum(1 for x, y in zip(ref, arm) if x and not y)
    n_arm = sum(1 for x, y in zip(ref, arm) if y and not x)
    n = n_ref + n_arm
    if n == 0:
        return n_ref, n_arm, 1.0
    k = min(n_ref, n_arm)
    return n_ref, n_arm, min(
        1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def boot_ci(arm: list[bool], ref: list[bool],
            rng: np.random.Generator) -> tuple[float, float]:
    d = np.array(arm, float) - np.array(ref, float)
    idx = rng.integers(0, d.size, size=(B_BOOT, d.size))
    m = d[idx].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def perm_p(arm: list[bool], ref: list[bool],
           rng: np.random.Generator) -> float:
    d = np.array(arm, float) - np.array(ref, float)
    obs = abs(d.mean())
    s = rng.choice((-1.0, 1.0), size=(B_PERM, d.size))
    return float((np.sum(np.abs((s * d).mean(axis=1)) >= obs - 1e-12) + 1)
                 / (B_PERM + 1))


def holm(p: dict[str, float]) -> dict[str, float]:
    order = sorted(p, key=lambda k: p[k])
    m, adj, run = len(order), {}, 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (m - i) * p[k]))
        adj[k] = run
    return adj


def analyse(ids: list[str], key: str,
            rng: np.random.Generator) -> dict[str, Any]:
    det = {a: [verdict(i, a, key) for i in ids] for a in ARMS}
    rates = {}
    for a in ARMS:
        k = sum(det[a])
        lo, hi = wilson(k, len(ids))
        rates[a] = {"k": k, "n": len(ids), "rate": k / len(ids),
                    "wilson95": [lo, hi], "label": LABEL[a]}
    contrasts = {}
    for a, ref in CONTRASTS:
        n_ref, n_arm, pm = mcnemar_exact(det[ref], det[a])
        lo, hi = boot_ci(det[a], det[ref], rng)
        contrasts[f"{a} - {ref}"] = {
            "delta": rates[a]["rate"] - rates[ref]["rate"],
            "ci95": [lo, hi], "discordant_arm_only": n_arm,
            "discordant_ref_only": n_ref, "p_mcnemar_exact": pm,
            "p_perm": perm_p(det[a], det[ref], rng)}
    adj = holm({k: v["p_mcnemar_exact"] for k, v in contrasts.items()})
    for k, v in contrasts.items():
        v["p_holm"] = adj[k]
        v["significant"] = adj[k] < 0.05
    return {"rates": rates, "contrasts": contrasts}


def main() -> None:
    from expand_dataset import find_tests
    from common import scope_dir

    inj = json.loads((EXP / "out/manifest.json").read_text())["injections"]
    ids = [i["id"] for i in inj
           if all(verdict(i["id"], a, "named_test") is not None for a in ARMS)]
    rng = np.random.default_rng(SEED)

    # How good is the deployed finder on these targets?  Reported so the
    # lexical arm's rate can be read against its input quality.
    fq = {"n": 0, "empty": 0, "hits_a_true_test": 0}
    for i in inj:
        if i["id"] not in ids:
            continue
        found = {t["path"] for t in find_tests(i["edit_file"], scope_dir(i["repo"]))}
        fq["n"] += 1
        fq["empty"] += int(not found)
        fq["hits_a_true_test"] += int(bool(found & set(i["true_test_dependents"])))

    out = {
        "meta": {"seed": SEED, "n": len(ids), "judges": JUDGES,
                 "rule": "majority of 3, ties to 0",
                 "repo": "grafana (TypeScript) only — see pre-registration §7",
                 "pre_registration":
                     "experiments/2026-09-06_test_oracle/docs/"
                     "PRE_REGISTRATION_test_oracle.md"},
        "deployed_finder_quality": fq,
        "primary_named_test": analyse(ids, "named_test", rng),
        "secondary_generic_test_talk": analyse(ids, "generic_test_talk", rng),
    }
    (BASE / "results/TEST_ORACLE.json").write_text(json.dumps(out, indent=2))
    write_md(out)

    for sect in ("primary_named_test", "secondary_generic_test_talk"):
        print(f"\n=== {sect} ===")
        for a in ARMS:
            r = out[sect]["rates"][a]
            print(f"  {a:<24} {r['k']:>2}/{r['n']}  {r['rate']:>6.1%}  "
                  f"[{r['wilson95'][0]:.2f}, {r['wilson95'][1]:.2f}]")
        for k, v in out[sect]["contrasts"].items():
            print(f"  {k:<44} {v['delta']:>+7.1%}  "
                  f"McNemar {v['p_mcnemar_exact']:.4f}  Holm {v['p_holm']:.4f}"
                  f"{'  **' if v['significant'] else ''}")
    print(f"\ndeployed finder: {fq['hits_a_true_test']}/{fq['n']} targets where it "
          f"returned a genuinely broken test, {fq['empty']} where it returned nothing")
    print("wrote results/TEST_ORACLE.{md,json}")


def write_md(out: dict[str, Any]) -> None:
    fq = out["deployed_finder_quality"]
    L = ["# Test-oracle band — does naming the tests help?", "",
         "Pre-registered in "
         "`experiments/2026-09-06_test_oracle/docs/PRE_REGISTRATION_test_oracle.md` "
         "before any review existed.", "",
         f"n = {out['meta']['n']} injections. A symbol whose importers include "
         "test files is renamed, so those tests provably fail. The reviewer is "
         "scored on whether it names one of them.", "",
         "**Grafana/TypeScript only** — the Experiment 2 scopes for sklearn and "
         "Kafka contain no test directories, so this result is one "
         "repository's and cannot be reported with the three-repo generality "
         "of Experiment 2.", ""]
    for sect, title, note in (
        ("primary_named_test", "Primary — names a genuinely breaking test file",
         "This is the actionable outcome: a review that says *which* test "
         "breaks."),
        ("secondary_generic_test_talk",
         "Secondary — talks about tests without naming one",
         "Pre-declared fairness check. This is what the coverage rubric's T3 "
         "criterion actually rewards."),
    ):
        s = out[sect]
        L += [f"## {title}", "", note, "",
              "| Arm | Context | Rate | 95% Wilson |", "|---|---|---:|---|"]
        for a in ARMS:
            r = s["rates"][a]
            L.append(f"| `{a}` | {r['label']} | {r['k']}/{r['n']} "
                     f"({r['rate']:.0%}) | "
                     f"[{r['wilson95'][0]:.2f}, {r['wilson95'][1]:.2f}] |")
        L += ["", "| Contrast | Δ | 95% CI | discordant | McNemar | p (Holm) |",
              "|---|---:|---|---:|---:|---:|"]
        for k, v in s["contrasts"].items():
            L.append(f"| {k} | {v['delta']:+.0%} | "
                     f"[{v['ci95'][0]:+.2f}, {v['ci95'][1]:+.2f}] | "
                     f"{v['discordant_arm_only']}/{v['discordant_ref_only']} | "
                     f"{v['p_mcnemar_exact']:.4f} | {v['p_holm']:.4f}"
                     f"{' **' if v['significant'] else ''} |")
        L.append("")
    L += ["## Why five rubric attempts found nothing", "",
          "Generic test talk is near ceiling in every arm, including the "
          "diff-only baseline. The model says tests are affected whether or "
          "not any are named, and the rubric criterion that would move — T3, "
          "*references specific test files or suggests which tests* — is "
          "satisfied by exactly that boilerplate. So the coverage instrument "
          "has no headroom on the test section, which is why deletion, "
          "scrambling and the three-judge re-analysis all returned null. The "
          "signal is real; the ruler could not see it.", "",
          "## Quality of the deployed finder on these targets", "",
          f"The filename-convention finder returned a genuinely broken test "
          f"for **{fq['hits_a_true_test']}/{fq['n']}** targets and nothing at "
          f"all for {fq['empty']}. TypeScript's `Foo.test.ts` beside `Foo.ts` "
          "convention is unusually favourable, so this recall should not be "
          "assumed for other languages.", ""]
    (BASE / "results/TEST_ORACLE.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
