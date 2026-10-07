#!/usr/bin/env python3
"""analyze_snr.py — analyze signal-to-noise caches and answer the real question.

Reads results/snr_cache/{verbose,concise}/<model>/pr*_*.json and reports, per
mode and per condition:
  signal (useful points), noise (generic+wrong), SNR (precision/actionability)

Then runs the two comparisons that matter:
  1. concise vs verbose, paired per (pr, mode): does concise raise precision?
  2. kg vs baseline, paired per pr (verbose): does KG add signal or just noise?

Wilcoxon signed-rank on paired deltas. Writes results/SNR_RESULTS.md.
"""

from __future__ import annotations

import argparse
import glob
import json
import statistics as st
from pathlib import Path

from scipy import stats

REPO = Path(__file__).resolve().parents[1]
MODEL = "openai-gpt-4o-mini"
MODES = ["baseline", "rag", "kg", "hybrid"]
VTAG, CTAG = "verbose", "concise"


def load(tag: str) -> dict[tuple[int, str], dict]:
    out = {}
    for f in glob.glob(f"{REPO}/results/snr_cache/{tag}/{MODEL}/pr*_*.json"):
        d = json.loads(Path(f).read_text())
        out[(d["pr_id"], d["mode"])] = d
    return out


def fmt(label, vals):
    return f"{label:<10} n={len(vals):<3} mean={st.mean(vals):.3f}  median={st.median(vals):.3f}"


def wilcoxon(a, b):
    """paired a vs b; returns (delta_mean, p)"""
    pairs = [(x, y) for x, y in zip(a, b)]
    diffs = [x - y for x, y in pairs]
    if not any(diffs):
        return st.mean(diffs), 1.0
    try:
        _, p = stats.wilcoxon([x for x, _ in pairs], [y for _, y in pairs])
    except Exception:
        p = float("nan")
    return st.mean(diffs), p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose-tag", default="verbose")
    ap.add_argument("--concise-tag", default="concise")
    ap.add_argument("--out", default="results/SNR_RESULTS.md")
    args = ap.parse_args()
    verbose = load(args.verbose_tag)
    concise = load(args.concise_tag)
    lines: list[str] = []

    def emit(s=""):
        print(s); lines.append(s)

    emit("# Signal-to-Noise (precision / actionability) results")
    emit(f"\nJudge: {MODEL} · labels each raised point useful / generic / wrong")
    emit("signal = #useful · noise = #generic+#wrong · SNR = signal/total\n")

    # ---- per mode, per condition table ----
    emit("## Per-mode means\n")
    emit("| mode | cond | n | signal | noise | total | SNR |")
    emit("|---|---|---|---|---|---|---|")
    for tag, data in (("verbose", verbose), ("concise", concise)):
        for mode in MODES:
            rows = [v for (p, m), v in data.items() if m == mode]
            if not rows:
                continue
            emit(f"| {mode} | {tag} | {len(rows)} | "
                 f"{st.mean(r['signal'] for r in rows):.2f} | "
                 f"{st.mean(r['noise'] for r in rows):.2f} | "
                 f"{st.mean(r['total'] for r in rows):.2f} | "
                 f"{st.mean(r['snr'] for r in rows):.3f} |")

    # ---- Q1: concise vs verbose (paired per pr,mode) ----
    emit("\n## Q1 — does CONCISE raise precision? (paired concise vs verbose)\n")
    common = sorted(set(verbose) & set(concise))
    for metric in ("snr", "signal", "noise", "total"):
        v = [verbose[k][metric] for k in common]
        c = [concise[k][metric] for k in common]
        dmean, p = wilcoxon(c, v)
        arrow = "concise↑" if dmean > 0 else "concise↓"
        emit(f"- **{metric}**: verbose={st.mean(v):.3f}  concise={st.mean(c):.3f}  "
             f"Δ={dmean:+.3f} ({arrow})  Wilcoxon p={p:.4g}  (n={len(common)})")

    # ---- Q2: kg vs baseline within verbose (paired per pr) ----
    emit("\n## Q2 — does KG add signal over baseline? (paired, verbose)\n")
    prs = sorted({p for (p, m) in verbose if m == "baseline"})
    for metric in ("signal", "noise", "snr", "total"):
        base = [verbose[(p, "baseline")][metric] for p in prs if (p, "kg") in verbose]
        kg = [verbose[(p, "kg")][metric] for p in prs if (p, "kg") in verbose]
        dmean, p = wilcoxon(kg, base)
        emit(f"- **{metric}**: baseline={st.mean(base):.3f}  kg={st.mean(kg):.3f}  "
             f"Δ={dmean:+.3f}  Wilcoxon p={p:.4g}  (n={len(kg)})")

    # ---- bottom line ----
    emit("\n## Bottom line\n")
    v_snr = st.mean(verbose[k]["snr"] for k in common)
    c_snr = st.mean(concise[k]["snr"] for k in common)
    v_sig = st.mean(verbose[k]["signal"] for k in common)
    c_sig = st.mean(concise[k]["signal"] for k in common)
    emit(f"- Concise SNR {c_snr:.3f} vs verbose {v_snr:.3f} "
         f"({'higher precision' if c_snr > v_snr else 'not higher'}).")
    emit(f"- Concise signal {c_sig:.2f} vs verbose {v_sig:.2f} useful points/review "
         f"({'keeps' if c_sig >= 0.9 * v_sig else 'loses'} real signal).")

    out = REPO / args.out
    out.write_text("\n".join(lines) + "\n")
    print(f"\nwrote {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
