#!/usr/bin/env python3
"""check_judge_length_bias.py — test the verbosity-bias threat to validity.

LLM-as-judge is known to favour longer responses (Zheng et al. 2023, MT-Bench;
Dubois et al. 2024, length-controlled AlpacaEval; Findings-EMNLP 2025). This
script quantifies how much review length drives the checklist score, and —
critically — whether the KG-vs-baseline effect is mediated by length.

Method:
  * Spearman(length, score) across all reviews (global length sensitivity).
  * Paired per-PR: corr(Δlength, Δscore) for kg-vs-baseline. If the KG score
    advantage does NOT track the KG length advantage, the effect is not a
    verbosity artifact.

No API calls. Reads the gpt-4o-only verbose panel + the review .md files.

Usage:
  python3 scripts/check_judge_length_bias.py \
    --judged results/checklist_evaluation_llm_multi__v2_gpt4o_only.json \
    --reviews outputs/luca_prs_v2
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import statistics as st
from pathlib import Path

from scipy import stats

MODES = ["baseline", "kg", "rag", "hybrid"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--judged", required=True)
    ap.add_argument("--reviews", required=True)
    ap.add_argument("--out-md", default="results/JUDGE_LENGTH_BIAS.md")
    args = ap.parse_args()

    length: dict[tuple[int, str], int] = {}
    for f in glob.glob(f"{args.reviews}/pr*_*.md"):
        m = re.match(r"pr(\d+)_(\w+)\.md", Path(f).name)
        if m:
            length[(int(m.group(1)), m.group(2))] = len(Path(f).read_text().split())

    evs = json.loads(Path(args.judged).read_text())["evaluations"]
    rows = []
    for e in evs:
        k = (e["pr_id"], e["mode"])
        if k in length:
            rows.append((length[k], e["total_score"], e["kg_relevant_score"],
                         e["mode"], e["pr_id"]))

    lens = [r[0] for r in rows]
    tot = [r[1] for r in rows]
    kgr = [r[2] for r in rows]
    g_tot = stats.spearmanr(lens, tot)
    g_kg = stats.spearmanr(lens, kgr)

    by_pr: dict[int, dict] = {}
    for ln, t, kg, mode, pr in rows:
        by_pr.setdefault(pr, {})[mode] = (ln, t, kg)
    dlen, dtot, dkg = [], [], []
    for pr, mm in by_pr.items():
        if "kg" in mm and "baseline" in mm:
            dlen.append(mm["kg"][0] - mm["baseline"][0])
            dtot.append(mm["kg"][1] - mm["baseline"][1])
            dkg.append(mm["kg"][2] - mm["baseline"][2])
    p_tot = stats.spearmanr(dlen, dtot)
    p_kg = stats.spearmanr(dlen, dkg)
    n_longer = sum(1 for d in dlen if d > 0)

    L = []
    L.append("# Verbosity-bias check — is the KG effect a length artifact?\n")
    L.append(f"Inputs: `{args.judged}` + `{args.reviews}/pr*_*.md` (length in words). "
             "No API calls.\n")
    L.append("## Global length sensitivity (all reviews)\n")
    L.append(f"- Spearman(length, total /25) = **{g_tot.correlation:+.2f}** (p={g_tot.pvalue:.3f})")
    L.append(f"- Spearman(length, KG-rel /9) = **{g_kg.correlation:+.2f}** (p={g_kg.pvalue:.3f})\n")
    L.append("## Is KG's win mediated by length? (paired kg vs baseline)\n")
    L.append(f"- n = {len(dlen)} PRs; KG longer than baseline in **{n_longer}/{len(dlen)}** "
             f"(mean Δlen = {st.mean(dlen):+.0f} words)")
    L.append(f"- corr(Δlength, Δtotal) = **{p_tot.correlation:+.2f}** (p={p_tot.pvalue:.3f})")
    L.append(f"- corr(Δlength, ΔKG-rel) = **{p_kg.correlation:+.2f}** (p={p_kg.pvalue:.3f})\n")
    robust = p_kg.pvalue > 0.05 and abs(g_kg.correlation) < 0.3
    L.append("## Conclusion\n")
    if robust:
        L.append("Length correlates only weakly with score, and the KG score advantage "
                 "is **not** significantly explained by the KG length advantage. The "
                 "KG-vs-baseline effect is **robust to verbosity bias** — it is not an "
                 "artifact of KG reviews being longer. (Consistent with Zheng et al. 2023 "
                 "finding GPT-4 is the least length-biased judge.)")
    else:
        L.append("Length shows a non-trivial association with score; report a "
                 "length-controlled estimate before claiming the KG effect.")
    Path(args.out_md).write_text("\n".join(L))
    print("\n".join(L))
    print(f"\nwrote {args.out_md}")


if __name__ == "__main__":
    main()
