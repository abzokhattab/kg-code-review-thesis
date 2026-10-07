#!/usr/bin/env python3
"""Build a combined results table across all four LLM-judge runs.

For each of:
  - tree-sitter `kg` (n=40, headline) — from results/checklist_evaluation_llm_multi__v2.json
  - Joern strict prompt (n=35) — from experiments/2026-05-15_joern_kg_main/exp_b_full35
  - Joern buggy clean prompt (n=35) — from experiments/2026-06-11_joern_normal_prompt
  - Joern parity clean prompt (n=35) — from experiments/2026-06-11_joern_normal_prompt_parity

compute consistent statistics:
  - n
  - mean Δ KG-rel, sd, d_z
  - mean Δ total, sd, d_z
  - Wilcoxon signed-rank p (two-sided, normal approx)
  - Sign test p (exact)
  - Permutation test p (10000 reps)
  - Percentile bootstrap 95% CI on d_z

Output: COMBINED_RESULTS_TABLE.md
"""
from __future__ import annotations
import json
import math
import random
import statistics
from math import comb
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HEADLINE = REPO / "results" / "checklist_evaluation_llm_multi__v2.json"
JOERN_STRICT = REPO / "experiments" / "2026-05-15_joern_kg_main" / "exp_b_full35"
JOERN_BUGGY = REPO / "experiments" / "2026-06-11_joern_normal_prompt" / "scores"
JOERN_PARITY = REPO / "experiments" / "2026-06-11_joern_normal_prompt_parity" / "scores"
OUT = REPO / "human_eval_v3_clean_2026-06-11" / "COMBINED_RESULTS_TABLE.md"

KG_IDS = {"F3", "F4", "T1", "T2", "T3", "M1", "M3", "C2", "Q2"}
random.seed(42)


def load_dir_kg_scores(d: Path, fname_glob: str = "pr*_kg.json"):
    out = {}
    for f in sorted(d.glob(fname_glob)):
        data = json.loads(f.read_text())
        out[data["pr_id"]] = data
    return out


def load_strict():
    out = {}
    for f in sorted(JOERN_STRICT.glob("pr*_eval.json")):
        data = json.loads(f.read_text())
        out[data["pr_id"]] = data
    return out


def load_headline_modes():
    d = json.loads(HEADLINE.read_text())
    out = {"baseline": {}, "kg": {}}
    for e in d["evaluations"]:
        if e["mode"] in out:
            out[e["mode"]][e["pr_id"]] = e
    return out


def normal_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def wilcoxon_p(deltas):
    """Two-sided Wilcoxon p, normal approximation with tie variance correction.

    Matches scipy.stats.wilcoxon(method='approx', correction=False) to four
    decimals. Without the tie correction (sum(t**3 - t)/48 subtracted from
    sigma**2), p-values on tied integer deltas are biased upward."""
    nz = [d for d in deltas if d != 0]
    n = len(nz)
    if n == 0:
        return 1.0
    mags = sorted(abs(d) for d in nz)
    rank = {}
    tie_groups = []
    i = 0
    while i < n:
        j = i
        while j < n and mags[j] == mags[i]:
            j += 1
        avg = (i + 1 + j) / 2
        for k in range(i, j):
            rank[(mags[k], k)] = avg
        if j - i > 1:
            tie_groups.append(j - i)
        i = j
    used = [False] * n
    sorted_mags = mags
    w_pos = 0
    w_neg = 0
    for d in nz:
        m = abs(d)
        for k, mm in enumerate(sorted_mags):
            if mm == m and not used[k]:
                used[k] = True
                r = rank[(mm, k)]
                if d > 0:
                    w_pos += r
                else:
                    w_neg += r
                break
    W = min(w_pos, w_neg)
    mu = n * (n + 1) / 4
    sigma2 = n * (n + 1) * (2 * n + 1) / 24
    sigma2 -= sum(t ** 3 - t for t in tie_groups) / 48.0
    if sigma2 <= 0:
        return 1.0
    sigma = math.sqrt(sigma2)
    z = (W - mu) / sigma
    p_one = normal_cdf(z)
    return 2 * min(p_one, 1 - p_one)


def sign_p(deltas):
    pos = sum(1 for d in deltas if d > 0)
    neg = sum(1 for d in deltas if d < 0)
    n = pos + neg
    if n == 0:
        return 1.0
    k = max(pos, neg)
    p_one = sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n
    return min(1.0, 2 * p_one)


def perm_p(deltas, n_perm=10000):
    obs = abs(sum(deltas))
    count = 0
    for _ in range(n_perm):
        s = sum(d if random.random() < 0.5 else -d for d in deltas)
        if abs(s) >= obs:
            count += 1
    return count / n_perm


def boot_ci(deltas, n_boot=10000, alpha=0.05):
    dzs = []
    n = len(deltas)
    for _ in range(n_boot):
        sample = [random.choice(deltas) for _ in range(n)]
        sd = statistics.stdev(sample) if n > 1 else 0.0
        if sd > 0:
            dzs.append(statistics.mean(sample) / sd)
    dzs.sort()
    lo = dzs[int(alpha / 2 * len(dzs))]
    hi = dzs[int((1 - alpha / 2) * len(dzs))]
    return lo, hi


def stats_block(deltas, label):
    n = len(deltas)
    m = sum(deltas) / n
    sd = statistics.stdev(deltas) if n > 1 else 0.0
    dz = m / sd if sd > 0 else 0.0
    p_w = wilcoxon_p(deltas)
    p_s = sign_p(deltas)
    p_p = perm_p(deltas)
    lo, hi = boot_ci(deltas)
    return {
        "label": label, "n": n, "mean": m, "sd": sd, "dz": dz,
        "p_wilcox": p_w, "p_sign": p_s, "p_perm": p_p,
        "ci_lo": lo, "ci_hi": hi,
    }


def kg_rel_score_from_criteria(scores_obj):
    """Some payloads use criteria_scores (list of dicts), others use criterion_id->score map."""
    if "kg_relevant_score" in scores_obj:
        return scores_obj["kg_relevant_score"]
    crit = scores_obj.get("criteria_scores", [])
    return sum(c["score"] for c in crit if c["criterion_id"] in KG_IDS)


def total_score_from_criteria(scores_obj):
    if "total_score" in scores_obj:
        return scores_obj["total_score"]
    crit = scores_obj.get("criteria_scores", [])
    return sum(c["score"] for c in crit)


def main():
    headline = load_headline_modes()
    bl_headline = headline["baseline"]
    kg_headline = headline["kg"]
    strict = load_strict()
    buggy = load_dir_kg_scores(JOERN_BUGGY)
    parity = load_dir_kg_scores(JOERN_PARITY)

    # Tree-sitter `kg` vs baseline (n=40)
    common_ts = sorted(set(bl_headline) & set(kg_headline))
    ts_kg_deltas = [kg_rel_score_from_criteria(kg_headline[p]) - kg_rel_score_from_criteria(bl_headline[p]) for p in common_ts]
    ts_tot_deltas = [total_score_from_criteria(kg_headline[p]) - total_score_from_criteria(bl_headline[p]) for p in common_ts]

    # Joern strict
    common_strict = sorted(set(strict) & set(bl_headline))
    js_kg_deltas = [strict[p]["kg_relevant_score"] - bl_headline[p]["kg_relevant_score"] for p in common_strict]
    js_tot_deltas = [strict[p]["total_score"] - bl_headline[p]["total_score"] for p in common_strict]

    # Joern buggy
    common_buggy = sorted(set(buggy) & set(bl_headline))
    jb_kg_deltas = [buggy[p]["kg_relevant_score"] - bl_headline[p]["kg_relevant_score"] for p in common_buggy]
    jb_tot_deltas = [buggy[p]["total_score"] - bl_headline[p]["total_score"] for p in common_buggy]

    # Joern parity
    common_parity = sorted(set(parity) & set(bl_headline))
    jp_kg_deltas = [parity[p]["kg_relevant_score"] - bl_headline[p]["kg_relevant_score"] for p in common_parity]
    jp_tot_deltas = [parity[p]["total_score"] - bl_headline[p]["total_score"] for p in common_parity]

    runs = [
        ("tree-sitter `kg` (pre-registered)", ts_kg_deltas, ts_tot_deltas),
        ("Joern strict prompt (forced 9-criterion coverage)", js_kg_deltas, js_tot_deltas),
        ("Joern clean prompt — body OMITTED (buggy, retracted)", jb_kg_deltas, jb_tot_deltas),
        ("Joern clean prompt — body PARITY (current Joern headline)", jp_kg_deltas, jp_tot_deltas),
    ]

    rows_kg = [stats_block(deltas, label) for (label, deltas, _) in runs]
    rows_tot = [stats_block(deltas, label) for (label, _, deltas) in runs]

    lines = []
    P = lines.append
    P("# Combined results table — all four LLM-judge runs, consistent statistics")
    P("")
    P("All d_z values use Cohen's d_z = mean(Δ) / sd(Δ) on paired per-PR deltas.")
    P("All p-values are two-sided. Wilcoxon uses normal approximation. Sign test")
    P("is exact binomial on non-zero deltas. Permutation test uses 10,000 sign-flip")
    P("reps. Bootstrap CI is percentile, 10,000 resamples (BCa values for parity")
    P("are in `BCA_BOOTSTRAP.md`). Random seed = 42.")
    P("")
    P("## KG-rel subscale (9 KG-relevant criteria: F3, F4, T1, T2, T3, M1, M3, C2, Q2)")
    P("")
    P("| Run | n | mean Δ | sd Δ | d_z | Wilcoxon p | sign p | perm p | 95% CI on d_z |")
    P("|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for r in rows_kg:
        P(f"| {r['label']} | {r['n']} | {r['mean']:+.3f} | {r['sd']:.3f} | "
          f"**{r['dz']:+.3f}** | {r['p_wilcox']:.4f} | {r['p_sign']:.4f} | {r['p_perm']:.4f} | "
          f"[{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}] |")
    P("")
    P("## Total score (all 25 criteria)")
    P("")
    P("| Run | n | mean Δ | sd Δ | d_z | Wilcoxon p | sign p | perm p | 95% CI on d_z |")
    P("|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for r in rows_tot:
        P(f"| {r['label']} | {r['n']} | {r['mean']:+.3f} | {r['sd']:.3f} | "
          f"**{r['dz']:+.3f}** | {r['p_wilcox']:.4f} | {r['p_sign']:.4f} | {r['p_perm']:.4f} | "
          f"[{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}] |")
    P("")
    P("## Reading guide")
    P("")
    P("- **Pre-registered headline**: tree-sitter `kg` row. This is what the")
    P("  ANALYSIS_PLAN locked. n=40 because tree-sitter parses Go.")
    P("- **Joern strict**: exploratory upper bound under a prompt that *mandates*")
    P("  coverage of the 9 KG-relevant criteria. The d_z is large but the prompt")
    P("  is biased toward the rubric.")
    P("- **Joern clean buggy**: the joern arm was missing the PR body in its")
    P("  prompt while baseline had it. **Confound.** Reported only for traceability.")
    P("- **Joern clean parity**: same prompt for both arms. The principled Joern")
    P("  comparison. Effect direction is consistent with tree-sitter but does not")
    P("  reach p<0.05 in any of three tests, and the bootstrap CI straddles zero.")
    P("")
    P("## Why d_z differs across runs even when n is the same")
    P("")
    P("The Joern runs use n=35 (Go excluded — Joern frontend lacks call edges).")
    P("Tree-sitter uses n=40 (its parser supports Go via tree-sitter-go).")
    P("Joern strict and buggy share the same 35 PRs but use different prompts.")
    P("Joern buggy and parity share the same prompt structure except for the body block.")
    P("")
    P("The **buggy → parity** drop on KG-rel (d_z +0.58 → +0.30) reflects the joern")
    P("arm's mean KG-rel score *decreasing* by 0.34 points (5.69 → 5.34) when the")
    P("body is added to its prompt; baseline scores are unchanged across the two")
    P("Joern runs because they come from the same headline file. See `HONEST_HEADLINE.md`")
    P("§6 for the post-falsification interpretation (no confirmed mechanism).")
    P("")
    OUT.write_text("\n".join(lines))
    print(f"Wrote {OUT}")
    print()
    print(f"{'Run':<55} | {'n':>3} | {'d_z':>7} | {'p_wilcox':>9} | {'CI':>20}")
    for r in rows_kg:
        print(f"{r['label'][:55]:<55} | {r['n']:>3} | {r['dz']:>+7.3f} | {r['p_wilcox']:>9.4f} | "
              f"[{r['ci_lo']:>+5.2f}, {r['ci_hi']:>+5.2f}]")


if __name__ == "__main__":
    main()
