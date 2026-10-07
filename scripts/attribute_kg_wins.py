#!/usr/bin/env python3
"""Attribute the KG-vs-baseline lift to specific criteria and verify grounding.

Answers two thesis questions:
  1. "When KG wins, is it because of the context provided?" — we split every
     paired win/loss by whether the criterion is KG-relevant (the 9 criteria a
     structural graph can answer) vs not (the 16 it cannot). If the lift is real
     context, wins must concentrate on the 9 and the 16 act as a placebo band.
  2. "Does the rubric reflect context richness?" — for each KG win on a
     KG-relevant criterion we dump the judge's stated reason so it can be
     read against the KG evidence pack (callers / tests / dependents).

Usage:
    python3 scripts/attribute_kg_wins.py \
        --eval results/checklist_evaluation_llm_multi__v2.json \
        --treatment kg --out results/KG_WIN_ATTRIBUTION.md
"""
from __future__ import annotations
import argparse, json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KG_REL = {"F3", "F4", "T1", "T2", "T3", "M1", "M3", "C2", "Q2"}


def load(path: Path):
    d = json.loads(path.read_text())
    # (pr, mode) -> {crit_id: {"score":int,"evidence":str}}
    table: dict = {}
    for e in d["evaluations"]:
        cell = {c["criterion_id"]: {"score": c["score"], "evidence": c.get("evidence", "")}
                for c in e["criteria_scores"]}
        table[(e["pr_id"], e["mode"])] = cell
    return d, table


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--eval", default="results/checklist_evaluation_llm_multi__v2.json")
    ap.add_argument("--treatment", default="kg")
    ap.add_argument("--baseline", default="baseline")
    ap.add_argument("--out", default="results/KG_WIN_ATTRIBUTION.md")
    args = ap.parse_args()

    d, table = load(REPO / args.eval)
    prs = sorted({pr for (pr, m) in table})

    # per-criterion win/loss tallies
    crit_win = defaultdict(int)   # treatment scored 1, baseline 0
    crit_loss = defaultdict(int)  # baseline 1, treatment 0
    crit_tie = defaultdict(int)
    kgwin_evidence = []           # (pr, crit, treatment-judge-evidence)

    for pr in prs:
        b = table.get((pr, args.baseline))
        t = table.get((pr, args.treatment))
        if not b or not t:
            continue
        for crit in t:
            bs = b.get(crit, {}).get("score", 0)
            ts = t.get(crit, {}).get("score", 0)
            if ts > bs:
                crit_win[crit] += 1
                if crit in KG_REL:
                    kgwin_evidence.append((pr, crit, t[crit].get("evidence", "")))
            elif bs > ts:
                crit_loss[crit] += 1
            else:
                crit_tie[crit] += 1

    def band(crits):
        w = sum(crit_win[c] for c in crits)
        l = sum(crit_loss[c] for c in crits)
        return w, l, w - l

    rel_w, rel_l, rel_net = band([c for c in crit_win | crit_loss if c in KG_REL] or KG_REL)
    # ensure all KG_REL counted even if zero
    rel_w = sum(crit_win[c] for c in KG_REL)
    rel_l = sum(crit_loss[c] for c in KG_REL)
    all_crit = set(crit_win) | set(crit_loss) | set(crit_tie)
    non = all_crit - KG_REL
    non_w = sum(crit_win[c] for c in non)
    non_l = sum(crit_loss[c] for c in non)

    lines = []
    lines.append(f"# KG-win attribution — `{args.treatment}` vs `{args.baseline}` (n={len(prs)} PRs)\n")
    lines.append(f"Source: `{args.eval}` (3-judge majority). A *win* = treatment scored the "
                 f"criterion 1 and baseline 0 on the same PR.\n")

    lines.append("## 1. Where do the wins land? (the placebo-band test)\n")
    lines.append("| Criterion band | wins | losses | **net** | wins/PR |")
    lines.append("|---|---:|---:|---:|---:|")
    lines.append(f"| KG-relevant (9 criteria) | {rel_w} | {rel_l} | **{rel_w-rel_l:+d}** | {rel_w/len(prs):.2f} |")
    lines.append(f"| Non-KG-relevant (16 criteria) | {non_w} | {non_l} | **{non_w-non_l:+d}** | {non_w/len(prs):.2f} |")
    lines.append("")
    lines.append("> If the KG lift were generic (longer/nicer reviews), wins would spread evenly. "
                 "Concentration on the KG-relevant band is the signature of *context-caused* wins; "
                 "the 16 non-KG criteria are a built-in negative control.\n")

    lines.append("## 2. Per-criterion breakdown\n")
    lines.append("| crit | KG-rel | wins | losses | net |")
    lines.append("|---|:---:|---:|---:|---:|")
    for c in sorted(all_crit):
        net = crit_win[c] - crit_loss[c]
        lines.append(f"| {c} | {'✅' if c in KG_REL else '—'} | {crit_win[c]} | {crit_loss[c]} | {net:+d} |")
    lines.append("")

    lines.append("## 3. Judge reasons for KG wins on KG-relevant criteria\n")
    lines.append("Read each reason against the KG evidence pack "
                 "(`data/luca_prs_v2/pr<ID>_evidence.json`: `callers`/`dependent_files`/`nearest_tests`). "
                 "A grounded win cites a structural fact the baseline could not see.\n")
    by_crit = defaultdict(list)
    for pr, crit, ev in kgwin_evidence:
        by_crit[crit].append((pr, ev))
    for crit in sorted(by_crit):
        lines.append(f"### {crit}  ({len(by_crit[crit])} wins)")
        for pr, ev in by_crit[crit]:
            lines.append(f"- **PR{pr}** — {ev.strip()}")
        lines.append("")

    out = REPO / args.out
    out.write_text("\n".join(lines))

    # console summary
    print(f"KG-relevant band: wins={rel_w} losses={rel_l} net={rel_w-rel_l:+d}")
    print(f"Non-KG band:      wins={non_w} losses={non_l} net={non_w-non_l:+d}")
    print(f"wrote {out.relative_to(REPO)}  ({len(kgwin_evidence)} KG-relevant wins with reasons)")


if __name__ == "__main__":
    main()
