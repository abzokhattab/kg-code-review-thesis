#!/usr/bin/env python3
"""Stage E: per-band detection rates, bootstrap CIs, paired permutation tests.
$0 — reads out/judgments/, writes out/RESULTS.md + out/results.json.

Statistical machinery per pre-reg §11: percentile bootstrap B=10000,
paired sign-flip permutation B=20000, seed=2026. All numbers reported
per band; no aggregate hides the local control band (§14).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ARMS, JUDGES, OUT, SEED, load_manifest  # noqa: E402

JUDGMENTS = OUT / "judgments"
B_BOOT, B_PERM = 10_000, 20_000


def majority(inj_id: str, arm: str) -> bool | None:
    votes = []
    for jm in JUDGES:
        jm_safe = jm.replace(":", "_").replace("/", "_")
        p = JUDGMENTS / inj_id / f"{arm}__{jm_safe}.json"
        if p.exists():
            try:
                votes.append(json.loads(p.read_text()).get("detected"))
            except Exception:
                votes.append(None)
    if not votes:
        return None
    n_true = sum(1 for v in votes if v is True)
    return n_true >= 2  # ties/None -> not detected (strict)


def boot_ci(x: np.ndarray, rng) -> tuple[float, float]:
    idx = rng.integers(0, len(x), size=(B_BOOT, len(x)))
    means = x[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def perm_p(diff: np.ndarray, rng) -> float:
    obs = diff.mean()
    signs = rng.choice([-1, 1], size=(B_PERM, len(diff)))
    null = (signs * diff).mean(axis=1)
    return float((np.abs(null) >= abs(obs)).mean())


def main():
    inj_all = load_manifest()
    rng = np.random.default_rng(SEED)

    det = {}  # (inj_id, arm) -> bool
    missing = []
    for inj in inj_all:
        for arm in ARMS:
            m = majority(inj["id"], arm)
            if m is None:
                missing.append((inj["id"], arm))
            else:
                det[(inj["id"], arm)] = m
    if missing:
        print(f"WARNING: {len(missing)} cells missing judgments "
              f"(first: {missing[:4]})")

    bands = {"structural": [i for i in inj_all if i["band"].startswith("S")],
             "local_control": [i for i in inj_all if i["band"].startswith("L")]}
    per_band = {b: sorted({i["band"] for i in v}) for b, v in bands.items()}

    results = {"n_total": len(inj_all), "seed": SEED,
               "B_bootstrap": B_BOOT, "B_permutation": B_PERM,
               "detection": {}, "contrasts": {}}
    L = ["# Experiment 2 — injection detection results", "",
         f"n = {len(inj_all)} injections "
         f"({len(bands['structural'])} structural, "
         f"{len(bands['local_control'])} local control) · "
         f"majority of {len(JUDGES)} judges, ties→0 · "
         f"bootstrap B={B_BOOT}, permutation B={B_PERM}, seed={SEED}", ""]

    for group, members in bands.items():
        ids = [i["id"] for i in members if all((i["id"], a) in det for a in ARMS)]
        L += [f"## {group} bands ({', '.join(per_band[group])}) — n={len(ids)}",
              "", "| Arm | Detected | Rate [95% CI] |", "|---|---:|---:|"]
        for arm in ARMS:
            x = np.array([float(det[(i, arm)]) for i in ids])
            lo, hi = boot_ci(x, rng) if len(x) > 1 else (0.0, 0.0)
            results["detection"][f"{group}:{arm}"] = {
                "n": len(ids), "detected": int(x.sum()), "rate": float(x.mean()),
                "ci95": [lo, hi]}
            L.append(f"| {arm} | {int(x.sum())}/{len(ids)} | "
                     f"{x.mean():.2f} [{lo:.2f}, {hi:.2f}] |")
        L.append("")

        contrasts = [("kg", "baseline"), ("rag", "baseline"),
                     ("hybrid", "baseline"), ("kg_idealised", "baseline"),
                     ("kg_joern_inherit", "kg")]
        L += ["| Contrast | Δ rate [95% CI] | p (perm) |", "|---|---:|---:|"]
        for a, b in contrasts:
            d = np.array([float(det[(i, a)]) - float(det[(i, b)]) for i in ids])
            lo, hi = boot_ci(d, rng) if len(d) > 1 else (0.0, 0.0)
            p = perm_p(d, rng) if len(d) > 1 and d.any() else 1.0
            results["contrasts"][f"{group}:{a}-vs-{b}"] = {
                "delta": float(d.mean()), "ci95": [lo, hi], "p_perm": p}
            L.append(f"| {a} − {b} | {d.mean():+.2f} [{lo:+.2f}, {hi:+.2f}] | {p:.4f} |")
        L.append("")

    # S4 inheritance-band focus (pre-reg §10.3)
    s4 = [i["id"] for i in inj_all if i["band"] == "S4"
          and all((i["id"], a) in det for a in ("kg", "kg_joern_inherit"))]
    if s4:
        d = np.array([float(det[(i, "kg_joern_inherit")]) - float(det[(i, "kg")])
                      for i in s4])
        L += [f"## S4 (inheritance) band — augmentation check, n={len(s4)}", "",
              f"kg_joern_inherit − kg on S4: Δ = {d.mean():+.2f} "
              f"({int(sum(float(det[(i,'kg_joern_inherit')]) for i in s4))}/{len(s4)}"
              f" vs {int(sum(float(det[(i,'kg')]) for i in s4))}/{len(s4)})", ""]
        results["s4_augmentation"] = {
            "n": len(s4), "delta": float(d.mean()),
            "kg": int(sum(det[(i, "kg")] for i in s4)),
            "kg_joern_inherit": int(sum(det[(i, "kg_joern_inherit")] for i in s4))}

    # per-injection table
    L += ["## Per-injection detail", "",
          "| id | band | fanout | " + " | ".join(ARMS) + " |",
          "|---|---|---:|" + "---|" * len(ARMS)]
    for inj in inj_all:
        cells = ["DET" if det.get((inj["id"], a)) else
                 ("miss" if (inj["id"], a) in det else "—") for a in ARMS]
        L.append(f"| {inj['id']} | {inj['band']} | {inj['fanout']} | "
                 + " | ".join(cells) + " |")

    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    (OUT / "RESULTS.md").write_text("\n".join(L) + "\n")
    print(f"wrote {OUT/'RESULTS.md'}")


if __name__ == "__main__":
    main()
