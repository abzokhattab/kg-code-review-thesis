#!/usr/bin/env python3
"""Integrity audit for the paper's headline numbers.

Recomputes every number the paper intends to cite directly from the raw
artefacts (judge panel JSON, injection harness output, evidence packs) and
compares against the summary markdown files. Read-only.

Run from the repository root:  python3 paper/2026-08-12/verify_paper_numbers.py
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict
from itertools import combinations

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Documented values the paper will cite, with their source file.
ERA2_MEANS = {  # results/BOOTSTRAP_STATS_v2.md + thesis-context/CLAUDE.md
    "baseline": (9.20, 4.97),
    "kg": (9.82, 5.58),
    "rag": (10.07, 5.40),
    "hybrid": (9.93, 5.50),
}
ERA2_DELTAS = {  # (total delta, kg-relevant delta)
    "kg": (0.62, 0.60),
    "rag": (0.88, 0.42),
    "hybrid": (0.72, 0.53),
}
ERA2_KAPPA = {  # thesis-context/CLAUDE.md §Inter-judge Cohen's kappa
    ("openai:gpt-4o-mini", "openai:gpt-4o"): 0.717,
    ("openai:gpt-4o-mini", "gemini:gemini-2.5-flash"): 0.590,
    ("openai:gpt-4o", "gemini:gemini-2.5-flash"): 0.713,
}
KG_RELEVANT_EXPECTED = {"F3", "F4", "T1", "T2", "T3", "M1", "M3", "C2", "Q2"}

JOERN_DELTAS = {  # results/BOOTSTRAP_STATS_joern.md, original 25-criterion rubric
    "kg": (1.17, 0.69),
    "rag": (0.97, 0.43),
    "hybrid": (0.94, 0.60),
}

EXP2_STRUCTURAL = {  # results/INJECTION_EXP2_RESULTS.md
    "baseline": 0, "rag": 1, "hybrid": 12,
    "kg": 15, "kg_joern_inherit": 21, "kg_idealised": 26,
}
EXP2_REPO_MIX = {  # results/ERA_GUIDE.md era 2
    "grafana": 13, "kafka": 8, "scikit-learn": 8, "godot": 6, "jenkins": 5,
}

results: list[tuple[str, bool, str]] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    results.append((label, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))


def close(a: float, b: float, tol: float = 0.005) -> bool:
    return abs(a - b) <= tol


def load(rel: str):
    with open(os.path.join(ROOT, rel)) as fh:
        return json.load(fh)


def spearman(xs: list[float], ys: list[float]) -> float:
    """Spearman rank correlation with average ranks for ties."""
    def ranks(vals: list[float]) -> list[float]:
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        out = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                out[order[k]] = avg
            i = j + 1
        return out

    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


def cohens_kappa(pairs: list[tuple[int, int]]) -> float:
    """Cohen's kappa for two raters on binary labels."""
    n = len(pairs)
    if n == 0:
        return float("nan")
    agree = sum(1 for a, b in pairs if a == b) / n
    a1 = sum(a for a, _ in pairs) / n
    b1 = sum(b for _, b in pairs) / n
    chance = a1 * b1 + (1 - a1) * (1 - b1)
    return (agree - chance) / (1 - chance) if chance != 1 else float("nan")


def mode_scores(evaluations, kg_criteria: set[str] | None = None):
    """Return {mode: {pr_id: (total, kg_relevant)}} recomputed from criteria."""
    out: dict[str, dict[int, tuple[int, int]]] = defaultdict(dict)
    for ev in evaluations:
        crits = ev["criteria_scores"]
        total = sum(c["score"] for c in crits)
        if kg_criteria is None:
            kg = ev["kg_relevant_score"]
        else:
            kg = sum(c["score"] for c in crits if c["criterion_id"] in kg_criteria)
        out[ev["mode"]][ev["pr_id"]] = (total, kg)
    return out


# ---------------------------------------------------------------- Experiment 1
def audit_era2() -> None:
    print("\n=== Experiment 1 (era 2, v2) — results/checklist_evaluation_llm_multi__v2.json ===")
    d = load("results/checklist_evaluation_llm_multi__v2.json")
    ev = d["evaluations"]
    meta = d["metadata"]

    check("panel metadata: 25 criteria, 9 KG-relevant",
          meta["criteria_count"] == 25 and meta["kg_relevant_criteria_count"] == 9,
          f"{meta['criteria_count']} / {meta['kg_relevant_criteria_count']}")
    check("judges are the era-2 panel",
          meta["judges"] == ["openai:gpt-4o-mini", "openai:gpt-4o", "gemini:gemini-2.5-flash"],
          ", ".join(meta["judges"]))

    prs = {e["pr_id"] for e in ev}
    modes = {e["mode"] for e in ev}
    check("160 evaluations = 40 PRs x 4 modes",
          len(ev) == 160 and len(prs) == 40 and modes == {"baseline", "kg", "rag", "hybrid"},
          f"{len(ev)} evals, {len(prs)} PRs, modes={sorted(modes)}")

    # KG-relevant criterion set, read off the by_criterion flags.
    flagged = {k for k, v in d["summary"]["by_criterion"].items() if v["kg_relevant"]}
    check("KG-relevant subset is the pre-registered 9",
          flagged == KG_RELEVANT_EXPECTED,
          f"{sorted(flagged)}" if flagged != KG_RELEVANT_EXPECTED else "F3 F4 T1 T2 T3 M1 M3 C2 Q2")

    # Internal consistency: stored aggregates must equal the criterion sums.
    bad_total = bad_kg = bad_vote = 0
    for e in ev:
        crits = e["criteria_scores"]
        if len(crits) != 25:
            bad_total += 1
        if sum(c["score"] for c in crits) != e["total_score"]:
            bad_total += 1
        if sum(c["score"] for c in crits if c["criterion_id"] in flagged) != e["kg_relevant_score"]:
            bad_kg += 1
        for c in crits:
            expected = 1 if c["n_yes"] * 2 > c["n_valid"] else 0
            if c["score"] != expected:
                bad_vote += 1
    check("stored total_score equals sum of criterion scores", bad_total == 0, f"{bad_total} mismatches")
    check("stored kg_relevant_score equals sum over the 9 criteria", bad_kg == 0, f"{bad_kg} mismatches")
    check("majority vote (ties -> 0) applied correctly in all 4000 cells",
          bad_vote == 0, f"{bad_vote} mismatched cells")

    # Per-mode means.
    scores = mode_scores(ev, flagged)
    for mode, (doc_total, doc_kg) in ERA2_MEANS.items():
        vals = scores[mode]
        mt = sum(v[0] for v in vals.values()) / len(vals)
        mk = sum(v[1] for v in vals.values()) / len(vals)
        check(f"mean {mode}: total {doc_total} / kg-rel {doc_kg}",
              close(mt, doc_total, 0.006) and close(mk, doc_kg, 0.006),
              f"recomputed {mt:.3f} / {mk:.3f}")

    # Paired deltas vs baseline.
    base = scores["baseline"]
    for mode, (doc_t, doc_k) in ERA2_DELTAS.items():
        common = sorted(set(base) & set(scores[mode]))
        dt = sum(scores[mode][p][0] - base[p][0] for p in common) / len(common)
        dk = sum(scores[mode][p][1] - base[p][1] for p in common) / len(common)
        check(f"paired delta {mode} vs baseline: total {doc_t:+} / kg-rel {doc_k:+}",
              close(dt, doc_t, 0.006) and close(dk, doc_k, 0.006),
              f"recomputed {dt:+.3f} / {dk:+.3f} on n={len(common)}")

    # Win attribution (results/KG_WIN_ATTRIBUTION.md §1) — the placebo-band test.
    cells = {(e["pr_id"], e["mode"]): {c["criterion_id"]: c["score"]
                                       for c in e["criteria_scores"]} for e in ev}
    for mode, doc in (("kg", (42, 18, 24, 34, 33, 1)),):
        kw = kl = nw = nl = 0
        for pr in prs:
            b, t = cells[(pr, "baseline")], cells[(pr, mode)]
            for crit in b:
                if t[crit] == 1 and b[crit] == 0:
                    if crit in flagged:
                        kw += 1
                    else:
                        nw += 1
                elif t[crit] == 0 and b[crit] == 1:
                    if crit in flagged:
                        kl += 1
                    else:
                        nl += 1
        got = (kw, kl, kw - kl, nw, nl, nw - nl)
        check(f"win attribution {mode}: KG-relevant {doc[0]}W/{doc[1]}L net {doc[2]:+}, "
              f"non-KG {doc[3]}W/{doc[4]}L net {doc[5]:+}",
              got == doc,
              f"recomputed KG-rel {kw}W/{kl}L net {kw - kl:+}, "
              f"non-KG {nw}W/{nl}L net {nw - nl:+}")

    # RAG floor effect (results/FINAL_RESULTS_REPORT.md §Finding 1): baseline score
    # vs RAG delta, Spearman r = -0.577.
    base_tot = {pr: cells[(pr, "baseline")] for pr in prs}
    xs = [sum(base_tot[pr].values()) for pr in sorted(prs)]
    ys = [sum(cells[(pr, "rag")].values()) - sum(base_tot[pr].values())
          for pr in sorted(prs)]
    check("RAG floor effect: Spearman r = -0.577 between baseline score and RAG delta",
          close(spearman(xs, ys), -0.577, 0.02),
          f"recomputed r = {spearman(xs, ys):+.3f} on n={len(xs)} (era-2 totals /25)")

    # Inter-judge kappa from the raw per-judge votes.
    raw = load("results/checklist_evaluation_llm_multi__v2.raw.json")
    votes: dict[str, dict[tuple, int]] = defaultdict(dict)
    for e in raw["evaluations"]:
        for pj in e["per_judge"]:
            for crit, val in pj["scores"].items():
                if val in (0, 1):
                    votes[pj["model"]][(e["pr_id"], e["mode"], crit)] = val
    for (j1, j2), doc_k in ERA2_KAPPA.items():
        keys = sorted(set(votes[j1]) & set(votes[j2]))
        k = cohens_kappa([(votes[j1][x], votes[j2][x]) for x in keys])
        check(f"Cohen's kappa {j1.split(':')[1]} vs {j2.split(':')[1]} = {doc_k}",
              close(k, doc_k, 0.006), f"recomputed {k:.3f} on {len(keys)} cells")


# ------------------------------------------------- Experiment 1 builder sensitivity
def audit_joern() -> None:
    print("\n=== Experiment 1 builder sensitivity (Joern) — results/checklist_evaluation_llm_multi__joern.json ===")
    d = load("results/checklist_evaluation_llm_multi__joern.json")
    ev = d["evaluations"]
    meta = d.get("metadata", {})
    prs = {e["pr_id"] for e in ev}
    check("Joern run is n=35 PRs (5 Go excluded)", len(prs) == 35, f"{len(prs)} PRs")
    check("Joern run scored on the same 25-criterion rubric (/25 and /9)",
          all(e["max_score"] == 25 and e["kg_relevant_max"] == 9 for e in ev),
          f"{len(ev[0]['criteria_scores'])} criteria per evaluation")

    # The era guide claims era 3 changed the judge panel. This file says otherwise.
    judges = meta.get("judges", [])
    era2_panel = ["openai:gpt-4o-mini", "openai:gpt-4o", "gemini:gemini-2.5-flash"]
    check("judge panel behind BOOTSTRAP_STATS_joern.md is the SAME as era 2 "
          "(so builder comparison holds the panel constant)",
          judges == era2_panel, ", ".join(judges))

    # Only the kg arm is Joern-built; the others are carried over from era 2.
    carried = str(meta.get("baseline_rag_hybrid_source", ""))
    check("metadata discloses that only the kg arm is Joern-built",
          "carried" in carried.lower() and "NOT Joern" in carried,
          carried[:110] + ("..." if len(carried) > 110 else ""))

    gen = str(meta.get("generator", ""))
    check("generator temperature matches Experiment 1 (T=0.0), so the builder "
          "comparison is temperature-matched",
          "0.0" in gen, f"joern run generator = {gen!r}")

    scores = mode_scores(ev, KG_RELEVANT_EXPECTED)
    base = scores.get("baseline", {})
    for mode, (doc_t, doc_k) in JOERN_DELTAS.items():
        if mode not in scores:
            check(f"Joern paired delta {mode}", False, "mode absent from run")
            continue
        common = sorted(set(base) & set(scores[mode]))
        dt = sum(scores[mode][p][0] - base[p][0] for p in common) / len(common)
        dk = sum(scores[mode][p][1] - base[p][1] for p in common) / len(common)
        label = "kg (Joern-built)" if mode == "kg" else f"{mode} (CARRIED from era 2, not Joern)"
        check(f"BOOTSTRAP_STATS_joern.md delta {label}: total {doc_t:+} / kg-rel {doc_k:+}",
              close(dt, doc_t, 0.006) and close(dk, doc_k, 0.006),
              f"recomputed {dt:+.3f} / {dk:+.3f} on n={len(common)}")


# ---------------------------------------------------------------- Experiment 2
def audit_exp2() -> None:
    print("\n=== Experiment 2 (injection) — experiments/2026-07-05_injection_exp2/out/results.json ===")
    d = load("experiments/2026-07-05_injection_exp2/out/results.json")
    det = d["detection"]

    check("n_total = 40 injections", d["n_total"] == 40, str(d["n_total"]))
    struct_n = {v["n"] for k, v in det.items() if k.startswith("structural:")}
    local_n = {v["n"] for k, v in det.items() if k.startswith("local_control:")}
    check("bands split 28 structural + 12 local control",
          struct_n == {28} and local_n == {12} and 28 + 12 == d["n_total"],
          f"structural n={struct_n}, local n={local_n}")

    for arm, doc in EXP2_STRUCTURAL.items():
        got = det[f"structural:{arm}"]["detected"]
        check(f"structural detection {arm} = {doc}/28", got == doc, f"harness says {got}/28")

    local_rates = {k.split(":")[1]: v["rate"] for k, v in det.items() if k.startswith("local_control:")}
    check("local-control rates all within 0.83-1.00 (defect visible in diff)",
          all(0.83 <= r <= 1.0 for r in local_rates.values()),
          ", ".join(f"{k} {v:.2f}" for k, v in sorted(local_rates.items())))

    parity = d["contrasts"]["local_control:kg-vs-baseline"]["delta"]
    check("placebo parity: kg-baseline on local bands inside [-0.15, +0.15]",
          -0.15 <= parity <= 0.15, f"delta={parity:+.4f}")

    inherit = d["contrasts"]["structural:kg_joern_inherit-vs-kg"]
    check("inheritance-edge gain over deployed KG = +0.21, p=0.071",
          close(inherit["delta"], 0.2143, 0.001) and close(inherit["p_perm"], 0.07145, 0.001),
          f"delta={inherit['delta']:+.4f}, p={inherit['p_perm']}")

    kg_base = d["contrasts"]["structural:kg-vs-baseline"]
    check("headline contrast kg-baseline = +0.54, p<0.0001",
          close(kg_base["delta"], 0.5357, 0.001) and kg_base["p_perm"] < 0.0001,
          f"delta={kg_base['delta']:+.4f}, p={kg_base['p_perm']}")

    # Band composition from the manifest.
    man = load("experiments/2026-07-05_injection_exp2/out/manifest.json")
    items = man["injections"]
    bands = Counter(it["band"] for it in items)
    structural = sum(v for k, v in bands.items() if k.startswith("S"))
    local = sum(v for k, v in bands.items() if k.startswith("L"))
    check("manifest band mix: 28 structural (S) + 12 local (L)",
          structural == 28 and local == 12,
          f"{dict(sorted(bands.items()))}")
    check("manifest S4 inheritance band has 6 injections", bands.get("S4") == 6,
          f"S4={bands.get('S4')}")

    repos = Counter(it["repo"] for it in items)
    check("injections span the three pre-registered repos",
          set(repos) == {"sklearn", "kafka", "grafana"}, f"{dict(sorted(repos.items()))}")

    # Recompute detection from the raw per-judge verdicts (majority of 3, ties -> 0).
    jroot = os.path.join(ROOT, "experiments/2026-07-05_injection_exp2/out/judgments")
    recomputed: dict[str, dict[str, bool]] = defaultdict(dict)
    for inj in sorted(os.listdir(jroot)):
        d_inj = os.path.join(jroot, inj)
        if not os.path.isdir(d_inj):
            continue
        votes: dict[str, list[bool]] = defaultdict(list)
        for fn in os.listdir(d_inj):
            if not fn.endswith(".json"):
                continue
            arm = fn.split("__")[0]
            with open(os.path.join(d_inj, fn)) as fh:
                votes[arm].append(bool(json.load(fh).get("detected")))
        for arm, vs in votes.items():
            recomputed[arm][inj] = sum(vs) * 2 > len(vs)

    band_of = {it["id"]: it["band"] for it in items}
    for arm, doc in EXP2_STRUCTURAL.items():
        got = sum(1 for inj, det in recomputed[arm].items()
                  if det and band_of.get(inj, "").startswith("S"))
        check(f"structural {arm} = {doc}/28 recomputed from individual judge votes",
              got == doc, f"majority-of-3 over judgment files gives {got}/28")

    s4_kg = sum(1 for inj, det in recomputed["kg"].items()
                if det and band_of.get(inj) == "S4")
    s4_inh = sum(1 for inj, det in recomputed["kg_joern_inherit"].items()
                 if det and band_of.get(inj) == "S4")
    check("S4 band: deployed kg 2/6 vs kg+inheritance 5/6 (delta +0.50)",
          s4_kg == 2 and s4_inh == 5, f"kg {s4_kg}/6, kg_joern_inherit {s4_inh}/6")


# --------------------------------------------------------------------- dataset
def audit_dataset() -> None:
    print("\n=== Dataset integrity ===")
    pack_dir = os.path.join(ROOT, "data/luca_prs_v2")
    packs = sorted(f for f in os.listdir(pack_dir)
                   if re.fullmatch(r"pr\d+_evidence\.json", f))
    pack_ids = {int(re.search(r"\d+", f).group()) for f in packs}

    panel_ids = {e["pr_id"] for e in load(
        "results/checklist_evaluation_llm_multi__v2.json")["evaluations"]}
    check("the scored sample is exactly 40 PRs", len(panel_ids) == 40, f"{len(panel_ids)} PRs")
    check("every scored PR has an evidence pack", panel_ids <= pack_ids,
          f"missing packs for {sorted(panel_ids - pack_ids)}")
    # PR50 was built on 2026-07-13 by the Joern "Option B" out-of-dataset probe
    # (experiments/2026-05-15_joern_kg_main/progress.json records evidence_pr50).
    # It is deliberately outside the scored 40; the guard is that it stays outside.
    orphans = pack_ids - panel_ids
    check("extra packs on disk are the known out-of-dataset ones only",
          orphans <= {50},
          f"unexpected extra pack(s): {sorted(orphans - {50})}" if orphans - {50}
          else "PR50 only (Option B probe, correctly excluded from the scored 40)")

    repos = Counter()
    for f in packs:
        pid = int(re.search(r"\d+", f).group())
        if pid not in panel_ids:
            continue
        p = json.load(open(os.path.join(pack_dir, f)))
        slug = str((p.get("pr") or {}).get("repo", "?")).split("/")[-1].lower()
        repos[slug] += 1
    norm = Counter()
    for k, v in repos.items():
        for want in EXP2_REPO_MIX:
            if want.replace("-", "") in k.replace("_", "").replace("-", ""):
                norm[want] += v
                break
        else:
            norm[k] += v
    check("repo mix matches grafana 13 / kafka 8 / sklearn 8 / godot 6 / jenkins 5",
          dict(norm) == EXP2_REPO_MIX, f"found {dict(sorted(norm.items()))}")

    out_dir = os.path.join(ROOT, "outputs/luca_prs_v2")
    reviews = [f for f in os.listdir(out_dir) if f.endswith(".md")]
    by_mode = Counter(f.rsplit("_", 1)[-1].removesuffix(".md") for f in reviews)
    check("160 generated reviews (40 PRs x 4 modes)", len(reviews) == 160,
          f"{len(reviews)} files; by mode {dict(sorted(by_mode.items()))}")

    # The generation configuration the paper will state in Methods. Corrected
    # 2026-08-12; these checks are the regression guard for that correction.
    print("\n--- generator configuration provenance ---")

    def txt(rel: str) -> str:
        return open(os.path.join(ROOT, rel), errors="ignore").read()

    exp1_docs = ["thesis-context/CLAUDE.md",
                 "reports/2026-07-13/EXPERIMENT_1_SUMMARY.md",
                 "thesis-context/CODE_INDEX.md",
                 "thesis-context/README.md",
                 "dataset_v2/docs/STATUS.md"]

    # A correction note necessarily quotes the wrong value, so only count lines
    # that assert it rather than lines that retract it.
    RETRACTION = re.compile(
        r"originally|corrected|wrong|not to either|sensitivity|earlier", re.I)

    def asserts(rel: str, pat: str) -> bool:
        return any(re.search(pat, line) and not RETRACTION.search(line)
                   for line in txt(rel).splitlines())

    stale = [rel for rel in exp1_docs if asserts(rel, r"T\s*=\s*0\.4|T=0\.4")]
    check("no Experiment 1 doc still asserts T=0.4", not stale, "; ".join(stale))

    seeded = [rel for rel in exp1_docs if asserts(rel, r"seed\s*=\s*42")]
    check("no doc still asserts a generation seed of 42", not seeded, "; ".join(seeded))

    check("Experiment 1 pipeline default temperature is 0.0",
          bool(re.search(r"default=0\.0",
                         txt("dataset_v2/scripts/regenerate_reviews_v2.py"))),
          "regenerate_reviews_v2.py --temperature default")
    check("Experiment 2 generator temperature is 0.3, hardcoded and documented",
          bool(re.search(r"temperature=0\.3", txt("prnote/note.py"))) and
          not asserts("results/INJECTION_EXP2_RESULTS.md", r"T=0\.4"),
          "prnote/note.py::generate_review_direct hardcodes 0.3; results doc corrected")
    check("no generation seed is sent on any model call (documented as such)",
          not re.search(r"\bseed\s*=", txt("prnote/llm.py")),
          "confirmed absent in prnote/llm.py; seed 2026 remains the stats seed")
    check("the Django-in-dataset error is gone from thesis-context/README.md",
          "Django" not in txt("thesis-context/README.md").split("### Dataset")[1][:400]
          or "not** in the dataset" in txt("thesis-context/README.md"),
          "dataset repo list")


# ------------------------------------------------------------- cross-doc sweep
def audit_crossdoc() -> None:
    print("\n=== Cross-document consistency ===")
    banned = {
        "25-PR dataset": r"25[- ]PR dataset",
        "14-criterion rubric": r"14[- ]criterion",
        "re-based +1.743/6 in a paper-facing doc": r"\+?1\.743",
    }
    # CLAUDE.md is excluded: it is the file that *prohibits* these phrases, so it
    # necessarily quotes them.
    paper_facing = [
        "reports/2026-07-13/EXPERIMENT_1_SUMMARY.md",
        "reports/2026-07-13/EXPERIMENT_2_INJECTION_SUMMARY.md",
        "results/INJECTION_EXP2_RESULTS.md",
        "results/BOOTSTRAP_STATS_v2.md",
    ]
    for label, pat in banned.items():
        hits = []
        for rel in paper_facing:
            path = os.path.join(ROOT, rel)
            if not os.path.exists(path):
                continue
            txt = open(path, errors="ignore").read()
            for m in re.finditer(pat, txt):
                line = txt[:m.start()].count("\n") + 1
                hits.append(f"{rel}:{line}")
        check(f"no '{label}' in paper-facing summaries", not hits, "; ".join(hits))

    # The 5/28 claim. `paper/` is excluded: this audit itself discusses the claim.
    found_528 = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in {
            ".git", "venv", "luca_repos", "repos", "node_modules", "__pycache__",
            "paper"}]
        for fn in filenames:
            if not fn.endswith((".md", ".json", ".tex", ".py")):
                continue
            path = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(path) > 2_000_000:
                    continue
                txt = open(path, errors="ignore").read()
            except Exception:
                continue
            if re.search(r"\brag\b[^\n]{0,40}\b5\s*/\s*28\b", txt, re.I):
                found_528.append(os.path.relpath(path, ROOT))
    check("no unsourced 'RAG 5/28' claim anywhere in the repo", not found_528,
          "; ".join(found_528))


def audit_paper_prose() -> None:
    """Verify the numbers written by hand in the paper's prose.

    The tables and the figure are generated, so they cannot drift. The prose
    is typed, so it can. This checks every quantitative claim in main.tex
    against the same artefacts the tables come from.
    """
    print("\n=== Paper prose (hand-written numbers in main.tex) ===")
    tex_path = os.path.join(ROOT, "paper/2026-08-12/draft/main.tex")
    if not os.path.exists(tex_path):
        check("paper draft exists", False, tex_path)
        return
    tex = open(tex_path, errors="ignore").read()
    # LaTeX wraps prose across lines, so match against whitespace-collapsed text.
    flat = re.sub(r"\s+", " ", tex)

    def claims(pattern: str) -> bool:
        return bool(re.search(pattern, flat, re.I))

    # --- Experiment 2 detection counts (the headline) ---
    det = load("experiments/2026-07-05_injection_exp2/out/results.json")["detection"]
    for arm, phrase in (("baseline", r"baseline detects (?:none|\$0\$|0\b)"),
                        ("rag", r"retrieval detects (?:one|1\b)"),
                        ("kg", r"graph context detects (?:fifteen|15\b)"),
                        ("hybrid", r"hybrid condition detects twelve"),
                        ("kg_idealised", r"idealised graph detects \$?26/28")):
        n = det[f"structural:{arm}"]["detected"]
        expect = {"baseline": 0, "rag": 1, "kg": 15, "hybrid": 12,
                  "kg_idealised": 26}[arm]
        check(f"prose states {arm} = {expect}/28 and artefact agrees",
              n == expect and claims(phrase), f"artefact={n}, prose match={claims(phrase)}")

    check("prose states the inheritance-augmented arm at 21/28",
          det["structural:kg_joern_inherit"]["detected"] == 21 and claims(r"21/28"),
          f"artefact={det['structural:kg_joern_inherit']['detected']}")

    # --- Experiment 2 contrasts quoted in prose ---
    kg_c = load("experiments/2026-07-05_injection_exp2/out/results.json"
                )["contrasts"]["structural:kg-vs-baseline"]
    check("prose quotes kg structural delta +0.54 [+0.36, +0.71]",
          abs(kg_c["delta"] - 0.54) < 0.005
          and claims(r"\+0\.54.{0,40}\+0\.36.{0,10}\+0\.71"),
          f"artefact delta={kg_c['delta']:.4f} ci={kg_c['ci95']}")
    loc = load("experiments/2026-07-05_injection_exp2/out/results.json"
               )["contrasts"]["local_control:kg-vs-baseline"]
    check("prose quotes the placebo delta -0.08",
          abs(loc["delta"] + 0.08) < 0.005 and claims(r"-0\.08"),
          f"artefact delta={loc['delta']:.4f}")

    # --- Experiment 1 win attribution (+24 / +1 / +17 / +18) ---
    ev = load("results/checklist_evaluation_llm_multi__v2.json")["evaluations"]
    cells = {(e["pr_id"], e["mode"]): {c["criterion_id"]: c["score"]
                                      for c in e["criteria_scores"]} for e in ev}
    prs = sorted({e["pr_id"] for e in ev})
    nets = {}
    for mode in ("kg", "rag"):
        w = {True: [0, 0], False: [0, 0]}
        for pr in prs:
            base, treat = cells[(pr, "baseline")], cells[(pr, mode)]
            for crit, b in base.items():
                dep = crit in KG_RELEVANT_EXPECTED
                if treat[crit] == 1 and b == 0:
                    w[dep][0] += 1
                elif treat[crit] == 0 and b == 1:
                    w[dep][1] += 1
        nets[mode] = (w[True][0] - w[True][1], w[False][0] - w[False][1])
    check("prose states kg nets +24 dependency and +1 elsewhere",
          nets["kg"] == (24, 1) and claims(r"nets \$\+24\$ on the nine dependency")
          and claims(r"\$\+1\$ on the sixteen others"),
          f"recomputed kg net = {nets['kg']}")
    check("prose states rag nets +17 and +18",
          nets["rag"] == (17, 18) and claims(r"nets \$\+17\$ and \$\+18\$"),
          f"recomputed rag net = {nets['rag']}")
    check("prose states the selectivity ratio consistently (24 vs 1)",
          claims(r"factor of twenty-four"), "'factor of twenty-four' phrasing")

    # --- Experiment 1 deltas and builder sensitivity quoted in prose ---
    v2 = load("results/BOOTSTRAP_STATS_v2.json")["vs_baseline"]
    jo = load("results/BOOTSTRAP_STATS_joern.json")["vs_baseline"]
    lo = min(v2[m]["total_diff"]["mean"] for m in ("kg", "rag", "hybrid"))
    hi = max(v2[m]["total_diff"]["mean"] for m in ("kg", "rag", "hybrid"))
    check("prose states the aggregate range +0.63 to +0.88",
          abs(lo - 0.625) < 0.005 and abs(hi - 0.875) < 0.005
          and claims(r"\$\+0\.63\$ and \$\+0\.88\$"),
          f"recomputed range = {lo:.3f}..{hi:.3f}")
    check("prose states kg total p = 0.054 (not significant)",
          abs(v2["kg"]["total_diff"]["p_value"] - 0.0537) < 0.001
          and claims(r"p = 0\.054"),
          f"artefact p={v2['kg']['total_diff']['p_value']}")
    check("prose states kg dependency p = 0.0066",
          abs(v2["kg"]["kg_relevant_diff"]["p_value"] - 0.0066) < 0.0005
          and claims(r"p = 0\.0066"),
          f"artefact p={v2['kg']['kg_relevant_diff']['p_value']}")
    check("prose states the builder effect moving +0.63 to +1.17",
          abs(jo["kg"]["total_diff"]["mean"] - 1.171) < 0.005
          and claims(r"\$\+0\.63\$ to \$\+1\.17\$"),
          f"joern total delta={jo['kg']['total_diff']['mean']}")
    check("prose states the dependency effect moving +0.60 to +0.69",
          abs(jo["kg"]["kg_relevant_diff"]["mean"] - 0.686) < 0.005
          and claims(r"\$\+0\.60\$ to \$\+0\.69\$"),
          f"joern dependency delta={jo['kg']['kg_relevant_diff']['mean']}")

    # --- Reliability figures ---
    raw = load("results/checklist_evaluation_llm_multi__v2.raw.json")
    votes: dict[str, dict[tuple, int]] = defaultdict(dict)
    for e in raw["evaluations"]:
        for pj in e["per_judge"]:
            for crit, val in pj["scores"].items():
                if val in (0, 1):
                    votes[pj["model"]][(e["pr_id"], e["mode"], crit)] = val
    judges = sorted(votes)
    check("raw per-judge votes are readable for the reliability check",
          len(judges) == 3, f"judges found: {judges}")
    kap = {}
    for a, b in combinations(judges, 2):
        shared = sorted(set(votes[a]) & set(votes[b]))
        kap[(a, b)] = (cohens_kappa([(votes[a][k], votes[b][k]) for k in shared]),
                       len(shared))
    vals = sorted(round(v[0], 2) for v in kap.values())
    check("prose quotes the three kappas (0.59, 0.71, 0.72)",
          vals == [0.59, 0.71, 0.72] and claims(r"0\.72") and claims(r"0\.71")
          and claims(r"0\.59"), f"recomputed = {vals}")
    smallest = min(v[1] for v in kap.values())
    check("prose footnote states the Gemini judge's usable cell count",
          smallest == 3836 and claims(r"3\\,836") and claims(r"4\\,000"),
          f"smallest shared cell count = {smallest}")

    # --- Judge validation percentages ---
    jv = open(os.path.join(
        ROOT, "experiments/2026-07-05_injection_exp2/out/JUDGE_VALIDATION.md"),
        errors="ignore").read()
    for pct in ("72", "80", "93"):
        check(f"prose judge-agreement {pct}\\% matches JUDGE_VALIDATION.md",
              re.search(rf"\b{pct}(\.0)?\s*%", jv) is not None
              and claims(rf"{pct}\\%"), f"{pct}% present in both sources")

    # --- Dataset composition sentence ---
    repos = Counter()
    for path in sorted(glob.glob(os.path.join(ROOT, "data/luca_prs_v2/pr*_evidence.json"))):
        pid = int(re.search(r"pr(\d+)_evidence", path).group(1))
        if pid == 50:
            continue
        with open(path) as fh:
            repos[(json.load(fh).get("pr", {}).get("repo") or "?").split("/")[-1]] += 1
    stated = re.search(r"\(Grafana (\d+), Apache Kafka (\d+), scikit-learn (\d+), "
                       r"Godot (\d+), Jenkins (\d+)\)", tex)
    check("prose repository counts match the evidence packs",
          stated is not None and [int(g) for g in stated.groups()] ==
          [repos.get("grafana", 0), repos.get("kafka", 0),
           repos.get("scikit-learn", 0), repos.get("godot", 0),
           repos.get("jenkins", 0)],
          f"artefact = {dict(repos)}, prose = "
          f"{stated.groups() if stated else 'not found'}")

    # --- Guard the bans in the paper itself ---
    check("paper contains no banned era-1 or re-based numbers",
          not re.search(r"25 PRs|14-criterion|1\.743", tex), "banned numbers")
    check("paper does not claim a generation seed",
          not re.search(r"seed\s*=?\s*42", tex), "seed 42 in paper")
    check("paper states both experiments' temperatures",
          "0.0" in tex and "0.3" in tex, "temperature disclosure")
    check("paper has no unresolved citation placeholder in body text",
          "\\cite{TODO" not in tex and "[TODO: citation]" not in tex,
          "TODO citations must be LaTeX comments, not body text")


def main() -> int:
    audit_era2()
    audit_joern()
    audit_exp2()
    audit_dataset()
    audit_crossdoc()
    audit_paper_prose()

    failed = [r for r in results if not r[1]]
    print("\n" + "=" * 72)
    print(f"{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("\nFAILURES:")
        for label, _, detail in failed:
            print(f"  - {label}" + (f" — {detail}" if detail else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
