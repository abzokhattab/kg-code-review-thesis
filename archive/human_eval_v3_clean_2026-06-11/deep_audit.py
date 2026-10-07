#!/usr/bin/env python3
"""Deep audits of the clean-Joern (normal prompt) run.

Computes:
  1. Per-criterion contribution to the KG-rel delta (which of the 9
     criteria carry the +0.58 effect).
  2. Per-language stratification (Python/JS/TS/Java/C++).
  3. Judge unanimity rate per mode and Cohen's kappa pairs.

Inputs:
  - experiments/2026-06-11_joern_normal_prompt/scores/pr*_kg.json  (clean Joern, n=35)
  - results/checklist_evaluation_llm_multi__v2.json                (40-PR headline, baseline rows used)
  - data/luca_prs_v2/pr*_evidence.json                              (for language tags)

Output: this script writes a combined report to
  human_eval_v3_clean_2026-06-11/DEEP_AUDIT.md
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
import sys
SRC = sys.argv[1] if len(sys.argv) > 1 else "buggy"
if SRC == "parity":
    CLEAN_SCORES = REPO / "experiments" / "2026-06-11_joern_normal_prompt_parity" / "scores"
    OUT = REPO / "human_eval_v3_clean_2026-06-11" / "DEEP_AUDIT_PARITY.md"
else:
    CLEAN_SCORES = REPO / "experiments" / "2026-06-11_joern_normal_prompt" / "scores"
    OUT = REPO / "human_eval_v3_clean_2026-06-11" / "DEEP_AUDIT.md"
HEADLINE = REPO / "results" / "checklist_evaluation_llm_multi__v2.json"
EVIDENCE_DIR = REPO / "data" / "luca_prs_v2"

KG_IDS = {"F3", "F4", "T1", "T2", "T3", "M1", "M3", "C2", "Q2"}


def load_clean_kg() -> dict[int, dict]:
    out = {}
    for f in sorted(CLEAN_SCORES.glob("pr*_kg.json")):
        d = json.loads(f.read_text())
        out[d["pr_id"]] = d
    return out


def load_headline_baseline() -> dict[int, dict]:
    d = json.loads(HEADLINE.read_text())
    out = {}
    for ev in d["evaluations"]:
        if ev["mode"] == "baseline":
            out[ev["pr_id"]] = ev
    return out


def detect_language(pr_id: int) -> str:
    ev_path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    if not ev_path.exists():
        return "unknown"
    ev = json.loads(ev_path.read_text())
    files = ev.get("changed_files", []) or ev.get("files", [])
    if not files:
        return "unknown"
    exts = []
    for f in files:
        path = f.get("path") if isinstance(f, dict) else f
        if not path:
            continue
        if path.endswith(".py"):
            exts.append("Python")
        elif path.endswith((".ts", ".tsx")):
            exts.append("TypeScript")
        elif path.endswith((".js", ".jsx")):
            exts.append("JavaScript")
        elif path.endswith(".java"):
            exts.append("Java")
        elif path.endswith((".cpp", ".cc", ".h", ".hpp")):
            exts.append("C++")
        elif path.endswith(".scala"):
            exts.append("Scala")
        elif path.endswith(".go"):
            exts.append("Go")
    if not exts:
        return "unknown"
    # majority
    from collections import Counter
    c = Counter(exts)
    return c.most_common(1)[0][0]


def per_criterion_deltas(clean_kg, baseline) -> tuple[list[dict], dict]:
    """For each criterion, compute mean kg_score - baseline_score across PRs."""
    rows = []
    pr_ids = sorted(set(clean_kg) & set(baseline))
    crit_seen: dict[str, dict] = defaultdict(lambda: {"baseline_yes": 0, "kg_yes": 0, "n": 0, "deltas": []})
    for pr in pr_ids:
        kg = {c["criterion_id"]: c["score"] for c in clean_kg[pr]["criteria_scores"]}
        bl = {c["criterion_id"]: c["score"] for c in baseline[pr]["criteria_scores"]}
        for cid in set(kg) & set(bl):
            d = kg[cid] - bl[cid]
            crit_seen[cid]["deltas"].append(d)
            crit_seen[cid]["baseline_yes"] += bl[cid]
            crit_seen[cid]["kg_yes"] += kg[cid]
            crit_seen[cid]["n"] += 1
    for cid, s in crit_seen.items():
        deltas = s["deltas"]
        mean = sum(deltas) / len(deltas)
        sd = math.sqrt(sum((x - mean) ** 2 for x in deltas) / max(1, len(deltas) - 1))
        rows.append({
            "criterion": cid,
            "is_kg_rel": cid in KG_IDS,
            "n": s["n"],
            "baseline_yes": s["baseline_yes"],
            "kg_yes": s["kg_yes"],
            "delta_yes": s["kg_yes"] - s["baseline_yes"],
            "mean_delta": mean,
            "sd_delta": sd,
        })
    rows.sort(key=lambda r: -r["mean_delta"])
    return rows, {"n_pairs": len(pr_ids)}


def per_language(clean_kg, baseline) -> list[dict]:
    by_lang: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for pr in sorted(set(clean_kg) & set(baseline)):
        lang = detect_language(pr)
        kg_rel = sum(c["score"] for c in clean_kg[pr]["criteria_scores"] if c["criterion_id"] in KG_IDS)
        bl_rel = sum(c["score"] for c in baseline[pr]["criteria_scores"] if c["criterion_id"] in KG_IDS)
        total_kg = clean_kg[pr]["total_score"]
        total_bl = baseline[pr]["total_score"]
        by_lang[lang].append((pr, kg_rel - bl_rel, total_kg - total_bl))
    rows = []
    for lang, items in sorted(by_lang.items()):
        n = len(items)
        deltas_kg = [x[1] for x in items]
        deltas_total = [x[2] for x in items]
        m_kg = sum(deltas_kg) / n
        m_tot = sum(deltas_total) / n
        sd_kg = math.sqrt(sum((x - m_kg) ** 2 for x in deltas_kg) / max(1, n - 1))
        sd_tot = math.sqrt(sum((x - m_tot) ** 2 for x in deltas_total) / max(1, n - 1))
        dz_kg = m_kg / sd_kg if sd_kg > 0 else float("nan")
        dz_tot = m_tot / sd_tot if sd_tot > 0 else float("nan")
        rows.append({
            "language": lang, "n": n,
            "mean_kg_rel_delta": m_kg, "dz_kg_rel": dz_kg,
            "mean_total_delta": m_tot, "dz_total": dz_tot,
            "prs": [x[0] for x in items],
        })
    rows.sort(key=lambda r: -r["n"])
    return rows


def judge_unanimity(clean_kg) -> dict:
    """Per-PR fraction of criteria where all 3 judges agreed."""
    out = {"per_pr": [], "overall": {}}
    total_unan = 0
    total_cells = 0
    for pr in sorted(clean_kg):
        d = clean_kg[pr]
        unan = sum(1 for c in d["criteria_scores"] if c.get("unanimous"))
        n = len(d["criteria_scores"])
        out["per_pr"].append({"pr": pr, "unanimous": unan, "n": n, "frac": unan / n})
        total_unan += unan
        total_cells += n
    out["overall"]["unanimous"] = total_unan
    out["overall"]["n_cells"] = total_cells
    out["overall"]["frac"] = total_unan / total_cells if total_cells else 0
    return out


def main():
    clean_kg = load_clean_kg()
    baseline = load_headline_baseline()
    print(f"Clean Joern PRs: {sorted(clean_kg)}")
    print(f"Baseline PRs: {sorted(baseline)}")
    common = sorted(set(clean_kg) & set(baseline))
    print(f"Common: {len(common)}")

    crit_rows, crit_meta = per_criterion_deltas(clean_kg, baseline)
    lang_rows = per_language(clean_kg, baseline)
    unan = judge_unanimity(clean_kg)

    # ----- write report -----
    lines = []
    P = lines.append
    P("# Deep audit — clean Joern (normal prompt) run")
    P("")
    P(f"**Pairs analyzed:** n={crit_meta['n_pairs']} (clean-Joern KG vs headline baseline)")
    P("")
    P("## 1. Per-criterion contribution to the KG-rel delta")
    P("")
    P("Sorted by mean delta (kg_score − baseline_score). KG-rel criteria (the 9 the rubric calls KG-relevant) flagged.")
    P("")
    P("| Criterion | KG-rel? | n | Baseline yes | KG yes | Δ yes | Mean Δ | SD Δ |")
    P("|---|:---:|---:|---:|---:|---:|---:|---:|")
    for r in crit_rows:
        flag = "✓" if r["is_kg_rel"] else ""
        P(f"| {r['criterion']} | {flag} | {r['n']} | {r['baseline_yes']} | {r['kg_yes']} | {r['delta_yes']:+d} | {r['mean_delta']:+.3f} | {r['sd_delta']:.3f} |")
    P("")
    kg_rel_pos = [r for r in crit_rows if r["is_kg_rel"] and r["mean_delta"] > 0]
    kg_rel_neg = [r for r in crit_rows if r["is_kg_rel"] and r["mean_delta"] < 0]
    P(f"**KG-rel criteria contributing positively (n={len(kg_rel_pos)}):** "
      + ", ".join(f"{r['criterion']} ({r['mean_delta']:+.2f})" for r in kg_rel_pos))
    P("")
    P(f"**KG-rel criteria contributing negatively (n={len(kg_rel_neg)}):** "
      + (", ".join(f"{r['criterion']} ({r['mean_delta']:+.2f})" for r in kg_rel_neg) if kg_rel_neg else "none"))
    P("")
    P("## 2. Per-language stratification")
    P("")
    P("| Language | n | Mean Δ KG-rel | d_z KG-rel | Mean Δ total | d_z total | PRs |")
    P("|---|---:|---:|---:|---:|---:|:---|")
    for r in lang_rows:
        prs = ",".join(str(p) for p in r["prs"][:8]) + ("…" if len(r["prs"]) > 8 else "")
        P(f"| {r['language']} | {r['n']} | {r['mean_kg_rel_delta']:+.3f} | {r['dz_kg_rel']:+.3f} | {r['mean_total_delta']:+.3f} | {r['dz_total']:+.3f} | {prs} |")
    P("")
    big_langs = [r for r in lang_rows if r["n"] >= 5]
    if big_langs:
        P("**Reading:** stratify only on languages with n≥5. Strata with n<5 are noise.")
        P("")
        for r in big_langs:
            verdict = "positive" if r["dz_kg_rel"] > 0.3 else ("negative" if r["dz_kg_rel"] < -0.3 else "near-null")
            P(f"- **{r['language']}** (n={r['n']}): KG-rel d_z={r['dz_kg_rel']:+.2f} → **{verdict}**.")
    P("")
    P("## 3. Judge unanimity")
    P("")
    P(f"**Overall:** {unan['overall']['unanimous']}/{unan['overall']['n_cells']} cells "
      f"unanimous = **{unan['overall']['frac']*100:.1f}%**")
    P("")
    P("Per-PR unanimity rate (sorted by PR):")
    P("")
    P("| PR | Unanimous / 25 | Frac |")
    P("|---:|---:|---:|")
    for r in unan["per_pr"]:
        P(f"| {r['pr']} | {r['unanimous']} | {r['frac']*100:.0f}% |")
    P("")
    P("Reading: lower unanimity = judges split = closer-to-tie scores.")
    P("If overall unanimity is well below 70%, the headline d_z is being driven")
    P("by judges leaning the same direction without consensus — a softer signal.")
    P("If above 70%, the effect is judge-robust.")
    P("")
    OUT.write_text("\n".join(lines))
    print(f"Wrote {OUT}")
    print(f"\n=== Quick summary ===")
    print(f"KG-rel criteria positive contributors: {len(kg_rel_pos)} of 9")
    top3 = [(r["criterion"], round(r["mean_delta"], 2)) for r in kg_rel_pos[:3]]
    print(f"Top KG-rel positive: {top3}")
    print(f"Languages with n>=5: {[(r['language'], r['n'], round(r['dz_kg_rel'],2)) for r in big_langs]}")
    print(f"Judge unanimity overall: {unan['overall']['frac']*100:.1f}%")


if __name__ == "__main__":
    main()
