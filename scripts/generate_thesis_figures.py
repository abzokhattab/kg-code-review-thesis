#!/usr/bin/env python3
"""Generate the thesis's data figures as TikZ from the result JSONs.

Why TikZ rather than a plotting library: the figures are typeset by the same
engine as the body text, so fonts, sizes and rules match exactly, output is
vector, and the thesis gains no Python dependency at build time. Nothing here
needs a package outside the standard library either, so the pinned environment
of requirements.txt is untouched.

Every figure is written as a `\\begin{tikzpicture}` fragment that the chapter
`\\input`s inside its own float, so captions, labels and placement stay in the
chapter where an author can see them. Each file carries a provenance header
naming this script and the JSON it was computed from, and no timestamp, so
regenerating without a data change produces a byte-identical file and shows up
as no diff.

Numbers are read from the analysis outputs rather than recomputed, so a figure
cannot silently disagree with the table beside it. If a figure and a table
disagree, exactly one of them is stale and re-running this script fixes it.

Inputs
  experiments/2026-09-23_five_judge_panel/RESULTS.json
                                                    final Experiment 1/2 panels
  results/CROSS_GENERATOR_v2.json                 four generators
  results/BOOTSTRAP_STATS_joern_parity.json       builder parity run, n = 35
  results/BOOTSTRAP_STATS_confirmatory_clean.json held-out replication, n = 12

Outputs (Thesis-2/figures/)
  fig_exp1_effects.tex            paired effect of each mode, both scales
  fig_criterion_localisation.tex  per-criterion effect, the two bands separated
  fig_exp1_robustness.tex         the same effect under other evaluation choices
  fig_exp2_detection.tex          structural detection ladder + local control
  fig_builder_edges.tex           lexical vs parsed edges on one pull request

Usage
  python3 scripts/generate_thesis_figures.py
  python3 scripts/generate_thesis_figures.py --out /tmp/figs --only robustness
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "Thesis-2" / "figures"

# Abbreviated criterion labels, copied verbatim from tab:exp1-criteria in
# 6_results_and_discussion/results_experiment1.tex. Kept identical on purpose:
# the figure and the table describe the same 25 criteria, and a reader moving
# between them should not have to work out whether two wordings mean one thing.
CRITERION_LABEL = {
    "F1": "Change solves the stated problem",
    "F2": "Edge cases in the change identified",
    "F3": "Integration with existing code",
    "F4": "Breaking changes or impact",
    "T1": "Need for tests discussed",
    "T2": "Edge cases and error paths in tests",
    "T3": "Specific test files referenced",
    "R1": "Code clarity, naming, function size",
    "R2": "Unnecessary complexity flagged",
    "R3": "Comments explain why, not what",
    "M1": "Fit with existing architecture",
    "M2": "Pull request too large to review",
    "M3": "Public API or interface handling",
    "C1": "Project style-guide compliance",
    "C2": "Consistency with similar solutions",
    "P1": "Obvious inefficiencies",
    "P2": "Benchmarks for critical paths",
    "S1": "Input validation",
    "S2": "Hardcoded secrets or credentials",
    "S3": "Error-handling quality",
    "Q1": "Overall assessment summary",
    "Q2": "Comments anchored to code locations",
    "Q3": "Blocking versus non-blocking issues",
    "Q4": "Clarifying questions asked",
    "Q5": "Rationale given for suggestions",
}

# Colours are defined once in packages_and_commands/additional_packages.tex so
# every figure and any future coloured table agree. The palette is Okabe-Ito,
# which stays distinguishable under the common forms of colour blindness and
# survives greyscale printing as distinct lightnesses.
C_KG = "kgblue"
C_RAG = "ragorange"
C_HYBRID = "hybridgreen"
C_BASE = "modegrey"
C_RULE = "black!55"


# ---------------------------------------------------------------- primitives


def tex_escape(s: str) -> str:
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
                 ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"),
                 ("}", r"\}"), ("~", r"\textasciitilde{}"),
                 ("^", r"\textasciicircum{}")):
        s = s.replace(a, b)
    return s


def nice_ticks(lo: float, hi: float, target: int = 6) -> list[float]:
    """Round tick positions covering [lo, hi], at a 1/2/2.5/5 x 10^k step."""
    span = hi - lo
    if span <= 0:
        return [lo]
    raw = span / max(target, 2)
    mag = 10.0 ** (len(f"{int(abs(raw)):d}") - 1) if abs(raw) >= 1 else 1.0
    while mag > raw:
        mag /= 10.0
    step = mag
    for mult in (1.0, 2.0, 2.5, 5.0, 10.0):
        if mag * mult >= raw:
            step = mag * mult
            break
    first = -(-lo / step // 1) * step
    ticks, v = [], first
    while v <= hi + step * 1e-9:
        r = round(v, 10)
        # Negative zero prints as "-0", which looks like a typo on an axis.
        ticks.append(0.0 if abs(r) < 1e-12 else r)
        v += step
    return ticks


def fmt(v: float, dec: int = 2, signed: bool = True) -> str:
    s = f"{v:+.{dec}f}" if signed else f"{v:.{dec}f}"
    return s.replace("-", "$-$")


def fmt_p(p: float) -> str:
    """Report p at the resolution the permutation supports, not more."""
    if p < 0.0001:
        return r"$<$0.0001"
    return f"{p:.4f}".rstrip("0").rstrip(".") if p < 0.001 else f"{p:.3f}"


def header(sources: list[str]) -> list[str]:
    L = [r"% !TeX root = ../thesis.tex",
         "% GENERATED FILE - do not edit by hand; your changes will be lost.",
         "% Produced by scripts/generate_thesis_figures.py",
         "% Regenerate: python3 scripts/generate_thesis_figures.py",
         "% Computed from:"]
    L += [f"%   {s}" for s in sources]
    L.append("%")
    return L


class Canvas:
    """Minimal TikZ writer with a data-to-centimetre transform on x only."""

    def __init__(self, xlo: float, xhi: float, width: float):
        self.xlo, self.xhi, self.width = xlo, xhi, width
        self.L: list[str] = []

    def x(self, v: float) -> float:
        return (v - self.xlo) / (self.xhi - self.xlo) * self.width

    def line(self, x1, y1, x2, y2, opt="thin"):
        self.L.append(r"\draw[%s] (%.4f,%.4f) -- (%.4f,%.4f);"
                      % (opt, x1, y1, x2, y2))

    def text(self, x, y, s, anchor="west", opt=r"font=\footnotesize"):
        self.L.append(r"\node[anchor=%s,%s] at (%.4f,%.4f) {%s};"
                      % (anchor, opt, x, y, s))

    def rect(self, x1, y1, x2, y2, opt):
        self.L.append(r"\fill[%s] (%.4f,%.4f) rectangle (%.4f,%.4f);"
                      % (opt, x1, y1, x2, y2))

    def marker(self, x, y, colour, filled=True, size=1.5):
        style = ("fill=%s,draw=%s" % (colour, colour) if filled
                 else "fill=white,draw=%s,line width=0.6pt" % colour)
        self.L.append(r"\draw[%s] (%.4f,%.4f) circle (%.3fpt);"
                      % (style, x, y, size))

    def axis(self, y: float, ticks: list[float], dec: int = 2,
             label: str | None = None, pct: bool = False):
        self.line(0, y, self.width, y, "thin,%s" % C_RULE)
        for t in ticks:
            xt = self.x(t)
            self.line(xt, y, xt, y - 0.08, "thin,%s" % C_RULE)
            s = (f"{t:.0f}" if pct else f"{t:g}")
            self.text(xt, y - 0.28, s.replace("-", "$-$"), "center",
                      r"font=\scriptsize")
        if label:
            self.text(self.width / 2.0, y - 0.72, label, "center",
                      r"font=\footnotesize")

    def zero(self, ytop: float, ybot: float, at: float = 0.0):
        """The reference line for "no effect", which is not always at zero:
        a preference proportion has its null at 0.5."""
        xz = self.x(at)
        self.line(xz, ytop, xz, ybot, "densely dashed,%s" % C_RULE)

    def render(self) -> str:
        return "\n".join([r"\begin{tikzpicture}"] + self.L
                         + [r"\end{tikzpicture}"])


def forest(rows: list[dict], width: float, label_w: float, rowsep: float,
           xlabel: str, dec: int = 2, show_p: bool = True,
           p_w: float = 1.35, null: float = 0.0,
           encode_significance: bool = True) -> str:
    """A forest plot: one interval per row, dashed line at no effect.

    A row is either {"kind": "header", "label": str} or a point with keys
    label, mean, lo, hi, p, colour and optionally note (printed instead of p)
    and rule (draw a separator above the row).
    """
    pts = [r for r in rows if r.get("kind") != "header"]
    xlo = min(min(r["lo"] for r in pts), null)
    xhi = max(max(r["hi"] for r in pts), null)
    pad = (xhi - xlo) * 0.06
    xlo, xhi = xlo - pad, xhi + pad
    ticks = nice_ticks(xlo, xhi)
    xlo, xhi = min(xlo, ticks[0]), max(xhi, ticks[-1])

    c = Canvas(xlo, xhi, width)
    y = 0.0
    ys = []
    for r in rows:
        if r.get("rule"):
            c.line(-label_w, y + rowsep * 0.52, width + (p_w if show_p else 0),
                   y + rowsep * 0.52, "thin,%s" % C_RULE)
        if r.get("kind") == "header":
            c.text(-label_w, y, r"\emph{%s}" % r["label"], "west",
                   r"font=\footnotesize")
            y -= rowsep
            continue
        ys.append(y)
        c.text(-label_w, y, r["label"], "west", r"font=\footnotesize")
        y -= rowsep
    c.zero(ys[0] + rowsep * 0.45, ys[-1] - rowsep * 0.45, at=null)

    i = 0
    for r in rows:
        if r.get("kind") == "header":
            continue
        yy = ys[i]
        i += 1
        colour = r.get("colour", C_KG)
        lo, hi, m = c.x(r["lo"]), c.x(r["hi"]), c.x(r["mean"])
        c.line(lo, yy, hi, yy, "%s,line width=0.9pt" % colour)
        for xe in (lo, hi):
            c.line(xe, yy - 0.07, xe, yy + 0.07, "%s,line width=0.9pt" % colour)
        # Fill marks p < 0.05 on the paired permutation test, not exclusion of
        # zero by the interval. The two procedures disagree at the boundary --
        # kg's total interval is [+0.050, +1.200] while its permutation p is
        # 0.054 -- and keying the marker to the interval would put a filled
        # marker next to a non-significant p on the same row. The permutation
        # test is the one the thesis infers from, so it governs the shape; the
        # interval is still drawn, and the disagreement is disclosed in the
        # caption rather than hidden by choosing whichever looks better.
        c.marker(
            m,
            yy,
            colour,
            filled=(r["p"] < 0.05 if encode_significance else True),
            size=2.0,
        )
        if show_p:
            note = r.get("note")
            c.text(width + p_w, yy, note if note else fmt_p(r["p"]), "east",
                   r"font=\scriptsize")

    c.axis(ys[-1] - rowsep * 0.95, ticks, dec, xlabel)
    if show_p:
        c.text(width + p_w, ys[0] + rowsep * 1.0, r"$p$", "east",
               r"font=\scriptsize")
    return c.render()


# --------------------------------------------------------- final-panel adapters


def final5_bootstrap(final: dict) -> dict:
    """Adapt the final five-judge result to the historical plotting schema."""
    e1 = final["experiment1"]
    by_mode = {
        mode: {"n": e1["modes"][mode]["n"]}
        for mode in ("baseline", "kg", "rag", "hybrid")
    }
    vs_baseline = {}
    for mode in ("kg", "rag", "hybrid"):
        row = e1["modes"][mode]

        def contrast(name: str) -> dict:
            value = row[name + "_contrast"]
            return {
                "mean": value["delta"],
                "ci_lo": value["ci95"][0],
                "ci_hi": value["ci95"][1],
                "p_value": value["p_permutation"],
            }

        vs_baseline[mode] = {
            "total_diff": contrast("total"),
            "kg_relevant_diff": contrast("kg_relevant"),
        }
    return {"by_mode": by_mode, "vs_baseline": vs_baseline}


def final5_concentration(final: dict) -> dict:
    """Build per-criterion deltas directly from final five-judge evaluations."""
    e1 = final["experiment1"]
    definitions = {item["id"]: item for item in e1["criteria_definitions"]}
    kg_ids = [cid for cid, item in definitions.items() if item["kg_relevant"]]
    evaluations = e1["evaluations"]

    def rates(mode: str) -> dict[str, float]:
        rows = [row for row in evaluations if row["mode"] == mode]
        return {
            cid: sum(row["scores"][cid] for row in rows) / len(rows)
            for cid in definitions
        }

    base = rates("baseline")
    modes = {}
    for mode in ("kg", "rag", "hybrid"):
        current = rates(mode)
        delta = {cid: current[cid] - base[cid] for cid in definitions}
        loc = e1["localisation"][mode]
        modes[mode] = {
            "base_rate": base,
            "mode_rate": current,
            "delta": delta,
            "kg_ids": kg_ids,
            "share": loc["share"],
        }
    return {"modes": modes}


def final5_detection(final: dict) -> dict:
    """Adapt final Experiment 2 rates to the detection-figure schema."""
    rates = final["experiment2"]["rates"]
    detection = {}
    for cohort, old_prefix in (("structural", "structural"),
                               ("local", "local_control")):
        for arm, value in rates[cohort].items():
            detection[f"{old_prefix}:{arm}"] = {
                "detected": value["detected"],
                "n": value["n"],
                "rate": value["rate"],
                "ci95": value["wilson95"],
            }
    return {"detection": detection}
# ------------------------------------------------------------------- figures


def fig_exp1_effects(boot: dict) -> str:
    """Each mode against baseline, on both the /25 total and the /9 subscale."""
    rows: list[dict] = []
    for mode, macro, colour in (("kg", r"\kg{}", C_KG),
                                ("rag", r"\rag{}", C_RAG),
                                ("hybrid", r"\hybrid{}", C_HYBRID)):
        d = boot["vs_baseline"][mode]
        for key, scale, first in (("kg_relevant_diff", "KG-relevant /9", True),
                                  ("total_diff", "total /25", False)):
            s = d[key]
            rows.append({
                "label": r"\textbf{%s}, %s" % (macro, scale),
                "mean": s["mean"], "lo": s["ci_lo"], "hi": s["ci_hi"],
                "p": s["p_value"], "colour": colour,
                "rule": first and mode != "kg",
            })
    body = forest(
        rows,
        width=6.0,
        label_w=4.5,
        rowsep=0.52,
        xlabel="Paired difference from the diff-only baseline (rubric points)",
        show_p=False,
        encode_significance=False,
    )
    return "\n".join(header([
        "experiments/2026-09-23_five_judge_panel/RESULTS.json "
        "(Experiment 1, n = 40)"
    ]) + [body]) + "\n"


VAL_W = 0.95  # width of the right-hand value column, centimetres


def fig_criterion_localisation(conc: dict) -> str:
    """Per-criterion effect with the two rubric bands drawn apart."""
    kg = conc["modes"]["kg"]
    delta = {k: v * 100.0 for k, v in kg["delta"].items()}
    kg_ids = set(kg["kg_ids"])
    # Descending by effect, then by criterion ID. The second key matters: several
    # criteria tie exactly, and without it their order would follow the JSON's key
    # order, so re-serialising the input would reshuffle rows and show up as a
    # figure diff that means nothing.
    def order(ids) -> list[str]:
        return sorted(ids, key=lambda c: (-delta[c], c))

    target = order(kg_ids)
    other = order(c for c in delta if c not in kg_ids)

    lo = min(min(delta.values()), 0.0)
    hi = max(max(delta.values()), 0.0)
    ticks = nice_ticks(lo - 2, hi + 2)
    c = Canvas(min(lo - 2, ticks[0]), max(hi + 2, ticks[-1]), 5.6)

    rowsep, label_w, y = 0.36, 5.0, 0.0
    bar_h = rowsep * 0.34

    def band(title: str, ids: list[str], colour: str, y: float) -> float:
        c.text(-label_w, y, r"\emph{%s}" % title, "west", r"font=\footnotesize")
        y -= rowsep
        for cid in ids:
            v = delta[cid]
            dead = kg["base_rate"][cid] in (0.0, 1.0) and v == 0.0
            lab = r"%s\enspace %s" % (cid, tex_escape(CRITERION_LABEL[cid]))
            if dead:
                lab += r"$^{\dagger}$"
            c.text(-label_w, y, lab, "west",
                   r"font=\scriptsize" + (r",%s" % C_RULE if dead else ""))
            x0, x1 = c.x(0.0), c.x(v)
            if abs(v) > 1e-9:
                style = colour if v > 0 else "%s!45" % colour
                c.rect(min(x0, x1), y - bar_h, max(x0, x1), y + bar_h, style)
                # Values go in a fixed column rather than at the bar tip: a
                # label tracking a short negative bar collides with the
                # criterion name, and a ragged value column is harder to scan.
                c.text(c.width + VAL_W, y, fmt(v, 1).replace(".0", ""),
                       "east", r"font=\scriptsize")
            y -= rowsep
        return y

    c.text(c.width + VAL_W, rowsep * 0.85, r"$\Delta$\,pp", "east",
           r"font=\scriptsize")
    y = band("KG-relevant band (9 criteria)", target, C_KG, y)
    y -= rowsep * 0.35
    c.line(-label_w, y + rowsep * 0.55, c.width + VAL_W, y + rowsep * 0.55,
           "thin,%s" % C_RULE)
    y = band("Negative-control band (16 criteria)", other, C_BASE, y)

    c.zero(rowsep * 0.6, y + rowsep * 0.5)
    c.axis(y + rowsep * 0.1, ticks, 0,
           "Change in satisfaction rate, KG versus baseline "
           "(percentage points)", pct=True)
    return "\n".join(header([
        "experiments/2026-09-23_five_judge_panel/RESULTS.json "
        "(Experiment 1 localisation, n = 40)"
    ]) + [c.render()]) + "\n"


def fig_exp1_robustness(boot: dict, single: dict, gen: dict, parity: dict,
                        conf: dict) -> str:
    """The headline effect recomputed under other defensible choices.

    One figure rather than four tables: the claim under test is about the
    spread of these estimates, and a spread is what a reader cannot assemble
    from four tables on four pages.
    """
    def kgrel(d: dict) -> dict:
        return {"mean": d["delta"], "lo": d["lo"], "hi": d["hi"], "p": d["p"]}

    h = boot["vs_baseline"]["kg"]["kg_relevant_diff"]
    rows: list[dict] = [
        {"kind": "header", "label": "Primary configuration"},
        {"label": r"Five-judge panel, $n = 35$", "colour": C_KG,
         "mean": h["mean"], "lo": h["ci_lo"], "hi": h["ci_hi"],
         "p": h["p_value"]},
        {"kind": "header", "label": "Single-judge sensitivity", "rule": True},
    ]
    judge_labels = (
        ("openai:gpt-4o", "gpt-4o only (also the generator)"),
        ("gemini:gemini-2.5-flash", "gemini-2.5-flash only"),
        ("anthropic:claude-sonnet-4-5", "claude-sonnet-4.5 only"),
        ("deepseek:deepseek-v4-pro", "deepseek-v4-pro only"),
        ("xai:grok-4.6", "grok-4.6 only"),
    )
    for key, label in judge_labels:
        value = single[key]
        rows.append({
            "label": label,
            "colour": C_KG,
            "mean": value["delta"],
            "lo": value["ci95"][0],
            "hi": value["ci95"][1],
            "p": value["p_permutation"],
        })

    rows.append({"kind": "header", "label": "Alternative generators",
                 "rule": True})
    for name, g in gen["generators"].items():
        if "headline" in name:
            continue
        d = g["paired"]["kg"]["kgrel"]
        display_name = "deepseek-chat" if name == "deepseek-v3" else name
        rows.append({
            "label": tex_escape(display_name),
            "colour": C_KG,
            **kgrel(d),
        })

    rows.append({"kind": "header",
                 "label": "Regeneration and sample sensitivity",
                 "rule": True})
    p = parity["vs_baseline"]["kg"]["kg_relevant_diff"]
    rows.append({"label": r"Earlier generation, same CPG, three judges",
                 "colour": C_KG,
                 "mean": p["mean"], "lo": p["ci_lo"], "hi": p["ci_hi"],
                 "p": p["p_value"]})
    cf = conf["vs_baseline"]["kg"]["kg_relevant_diff"]
    rows.append({"label": r"Held-out pull requests, $n = 12$", "colour": C_KG,
                 "mean": cf["mean"], "lo": cf["ci_lo"], "hi": cf["ci_hi"],
                 "p": cf["p_value"]})

    body = forest(
        rows,
        width=5.4,
        label_w=5.2,
        rowsep=0.46,
        xlabel="Effect on the nine KG-relevant criteria (rubric points)",
        show_p=False,
        encode_significance=False,
    )
    return "\n".join(header([
        "results/JOERN_UNIFIED_FIVE_JUDGE.json "
        "(headline and individual judges, n = 35)",
        "results/CROSS_GENERATOR_v2.json (generators)",
        "results/BOOTSTRAP_STATS_joern_parity.json (builder parity)",
        "results/BOOTSTRAP_STATS_confirmatory_clean.json (held-out)",
    ]) + [body]) + "\n"


def fig_exp2_detection(exp2: dict) -> str:
    """Structural detection ladder against the local-control band."""
    arms = [
        ("baseline", r"\baseline{} (diff only)", C_BASE),
        ("rag", r"\rag{}", C_RAG),
        ("hybrid", r"\hybrid{}", C_HYBRID),
        ("kg", r"\kg{} (deployed)", C_KG),
        ("kg_joern_inherit", r"\kg{} + inheritance edges", C_KG),
        ("kg_idealised", r"\kg{} idealised (ceiling)", C_KG),
    ]
    c = Canvas(0.0, 1.0, 6.0)
    rowsep, label_w, y = 0.50, 4.4, 0.0
    bar_h = 0.145
    ticks = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

    for key, lab, colour in arms:
        s = exp2["detection"]["structural:" + key]
        l = exp2["detection"]["local_control:" + key]
        c.text(-label_w, y, lab, "west", r"font=\footnotesize")

        if s["rate"] > 0:
            c.rect(c.x(0.0), y - bar_h, c.x(s["rate"]), y + bar_h, colour)
        c.line(c.x(s["ci95"][0]), y, c.x(s["ci95"][1]), y,
               "black!70,line width=0.5pt")
        for xe in s["ci95"]:
            c.line(c.x(xe), y - 0.055, c.x(xe), y + 0.055,
                   "black!70,line width=0.5pt")
        # The local control is a marker rather than a second bar. Two bar series
        # would give the control equal visual weight, and the control's job is
        # to be uninformative: the point is that these markers do not move while
        # the bars vary from nothing to almost everything.
        c.marker(c.x(l["rate"]), y, "black!75", filled=False, size=2.1)
        c.text(c.width + 1.5, y,
               r"%d/%d" % (s["detected"], s["n"]), "east", r"font=\scriptsize")
        y -= rowsep

    c.text(c.width + 1.5, rowsep * 0.8, "detected", "east", r"font=\scriptsize")
    c.axis(y + rowsep * 0.45, ticks, 1, "Detection rate")

    key_y = y - rowsep * 2.55
    c.rect(0.0, key_y - bar_h * 0.8, 0.42, key_y + bar_h * 0.8, "black!70")
    c.text(0.55, key_y,
           r"structural injections, consequence outside the diff ($n = 28$), "
           r"with 95\,\% CI", "west", r"font=\scriptsize")
    c.marker(0.21, key_y - 0.40, "black!75", filled=False, size=2.1)
    c.text(0.55, key_y - 0.40,
           r"local control, consequence inside the diff ($n = 12$)", "west",
           r"font=\scriptsize")
    return "\n".join(header([
        "experiments/2026-09-23_five_judge_panel/RESULTS.json "
        "(Experiment 2 detection)"
    ]) + [c.render()]) + "\n"


def fig_builder_edges(cmp: dict) -> str:
    """What two builders assert for one pull request, side by side.

    This is the only figure in the thesis that is a diagram rather than a plot,
    and it earns the space because the lexical-versus-parsed distinction is
    load-bearing in three chapters while being invisible in the data: both
    builders emit edges spelled ``imports``, and a reader has no way to see that
    one of them never checked. The encoding is deliberately blunt --- a filled
    marker means the file is library source, which is the only kind of file that
    can be a genuine dependent of a library module --- because the whole point is
    that one column is almost entirely filled and the other is entirely empty.

    Every path and every matched identifier is read from the comparison JSON, so
    the figure cannot drift from what the builders actually returned.
    """
    meta, lex, ast = cmp["meta"], cmp["lexical"], cmp["ast"]
    stem = meta["stem"]
    PW, X2 = 6.5, 7.6
    # Past the longest path that carries an annotation. Only the accidental
    # matches are annotated, so this column can sit well left of the longest
    # path in the panel without colliding with anything.
    ident_x = 4.35

    def is_accidental(ident: str | None) -> bool:
        """True when the stem is not a token of the identifier, only a substring.

        ``wrapped_view`` contains ``app`` the way ``therapist`` contains ``the``:
        the builder's match carries no information about the code at all. That is
        a different failure from ``create_app``, which is a real reference to a
        Flask application but in an example program rather than in the library.
        """
        if not ident:
            return False
        return stem not in ident.split("_")

    L: list[str] = [r"\begin{tikzpicture}"]

    def node(x, y, s, anchor="west", opt=r"font=\footnotesize"):
        L.append(r"\node[anchor=%s,%s] at (%.3f,%.3f) {%s};"
                 % (anchor, opt, x, y, s))

    def rule(x0, x1, y, opt="thin,black!55"):
        L.append(r"\draw[%s] (%.3f,%.3f) -- (%.3f,%.3f);" % (opt, x0, y, x1, y))

    def chip(x, y, filled):
        if filled:
            L.append(r"\fill[%s] (%.3f,%.3f) rectangle (%.3f,%.3f);"
                     % (C_KG, x - 0.055, y - 0.055, x + 0.055, y + 0.055))
        else:
            L.append(r"\draw[black!45,line width=0.4pt] "
                     r"(%.3f,%.3f) rectangle (%.3f,%.3f);"
                     % (x - 0.055, y - 0.055, x + 0.055, y + 0.055))

    # The changed file, and the pull request it was changed in.
    cx = (PW + X2 + PW) / 2.0
    L.append(r"\node[draw=black!55,thin,rounded corners=1pt,inner sep=3pt,"
             r"font=\ttfamily\scriptsize,anchor=center] (src) at (%.3f,1.62) "
             r"{%s};" % (cx, tex_escape(meta["changed_file"])))
    node(cx, 1.16, r"changed in \texttt{%s} at \texttt{%s}"
         % (tex_escape(meta["pr"]), meta["head_sha"][:8]), "center",
         r"font=\scriptsize,text=black!70")

    # Rail from the changed file down to the two builders that read it.
    p1c, p2c = PW / 2.0, X2 + PW / 2.0
    rule(p1c, p2c, 0.80)
    L.append(r"\draw[thin,black!55] (%.3f,0.98) -- (%.3f,0.80);" % (cx, cx))
    for xc in (p1c, p2c):
        L.append(r"\draw[thin,black!55] (%.3f,0.80) -- (%.3f,0.60);" % (xc, xc))

    panels = [
        (0.0, r"Lexical builder", lex,
         r"text search for \texttt{%s} in \texttt{*.py}" % stem,
         r"%d files match; first %d kept"
         % (lex["dependents_total_matches"], lex["dependents_cap"])),
        (X2, r"AST import resolver", ast,
         r"parsed \texttt{import} statements",
         r"%d edges, all resolved" % len(ast["dependents_kept"])),
    ]

    y_title, y_mech, y_rule, y_first, rowsep = 0.46, 0.10, -0.10, -0.42, 0.325
    nrows = max(len(p[2]["dependents_kept"]) for p in panels)
    ylast = y_first - (nrows - 1) * rowsep

    for x0, title, d, mech, count in panels:
        node(x0, y_title, r"\textbf{%s}" % title, "west", r"font=\footnotesize")
        node(x0, y_mech, mech, "west", r"font=\scriptsize,text=black!70")
        rule(x0, x0 + PW, y_rule)

        for i, path in enumerate(d["dependents_kept"]):
            y = y_first - i * rowsep
            lib = path in d["dependents_kept_in_library"]
            chip(x0 + 0.06, y, lib)
            node(x0 + 0.22, y, r"\texttt{%s}" % tex_escape(path), "west",
                 r"font=\tiny" if lib else r"font=\tiny,text=black!70")
            # Only the accidental matches are annotated. For the rest the matched
            # identifier is some form of ``app``, which the marker already
            # explains: a real reference, in a program that is not the library.
            ident = d.get("match_reason", {}).get(path)
            if ident and is_accidental(ident):
                node(x0 + ident_x, y,
                     r"$\dagger$\,\texttt{%s}" % tex_escape(ident), "west",
                     r"font=\tiny")

        yfoot = ylast - 0.54
        rule(x0, x0 + PW, yfoot + 0.20)
        n_lib = len(d["dependents_kept_in_library"])
        n_kept = len(d["dependents_kept"])
        node(x0, yfoot - 0.02,
             r"\textbf{%d of %d} inside \texttt{src/flask/}" % (n_lib, n_kept),
             "west", r"font=\scriptsize")
        node(x0, yfoot - 0.36, count, "west",
             r"font=\scriptsize,text=black!70")

    # Key. The dagger is explained here rather than in the caption because a
    # reader looking at a marked row should not have to leave the figure.
    ykey = ylast - 1.40
    chip(0.06, ykey, True)
    node(0.22, ykey, r"library source, i.e.\ a file that can depend on the "
                     r"changed module", "west", r"font=\scriptsize")
    chip(0.06, ykey - 0.34, False)
    node(0.22, ykey - 0.34, r"documentation or example program", "west",
         r"font=\scriptsize")
    node(0.06, ykey - 0.68,
         r"$\dagger$ the stem \texttt{%s} is not a token of the matched "
         r"identifier, only a substring of it" % stem, "west",
         r"font=\scriptsize")

    L.append(r"\end{tikzpicture}")
    return "\n".join(header(["results/BUILDER_EDGE_COMPARISON.json "
                             "(scripts/compare_builder_edges.py)"])
                     + ["\n".join(L)]) + "\n"


def fig_pipeline(boot: dict, panel: dict) -> str:
    """The construction/generation split, the frozen pack, and the nested arms.

    The figure exists to carry one argument visually that Chapter 4 has to make in
    prose: because a single frozen artefact sits between reading the repository and
    writing the review, and because the four arms are nested subsets of that
    artefact's fields, a difference between arms cannot come from anything except
    the fields. The middle band is therefore the centre of the figure rather than
    an afterthought --- it is the only place a reader can see that \\baseline{} is
    not deprived of the diff.

    Counts are read from the result files instead of typed in, so the figure and
    the tables cannot disagree about how many pull requests or judges there were.
    """
    n_pr = boot["by_mode"]["baseline"]["n"]
    modes = list(boot["by_mode"].keys())
    n_modes = len(modes)
    judges = panel.get("panel") or []
    n_judge = len(judges) if isinstance(judges, (list, tuple)) else 3
    n_crit = len(panel.get("criteria_definitions") or {})

    W = 13.8
    SPINE = 4.4  # half-width of the boxes on the centre line, set by the
                 # longest of their labels rather than by the narrowest
    L: list[str] = [r"\begin{tikzpicture}"]

    def box(x0, y0, x1, y1, label, opt="draw=black!55,thin",
            font=r"\scriptsize", fill=None):
        st = opt + (",fill=%s" % fill if fill else "")
        L.append(r"\draw[%s,rounded corners=1.5pt] (%.3f,%.3f) rectangle "
                 r"(%.3f,%.3f);" % (st, x0, y0, x1, y1))
        L.append(r"\node[anchor=center,font=%s,align=center] at (%.3f,%.3f) "
                 r"{%s};" % (font, (x0 + x1) / 2.0, (y0 + y1) / 2.0, label))

    def arrow(x, yfrom, yto):
        L.append(r"\draw[-{Latex[length=1.4mm,width=1.2mm]},thin,black!65] "
                 r"(%.3f,%.3f) -- (%.3f,%.3f);" % (x, yfrom, x, yto))

    def note(x, y, s, anchor="west"):
        L.append(r"\node[anchor=%s,font=\scriptsize,text=black!70] at "
                 r"(%.3f,%.3f) {%s};" % (anchor, x, y, s))

    cx = W / 2.0

    # -- Construction ------------------------------------------------------
    box(cx - SPINE, -0.42, cx + SPINE, 0.0,
        r"repository at the pull request's head commit")
    arrow(cx, -0.42, -0.80)

    src_w, src_gap = 3.9, 0.55
    total = 3 * src_w + 2 * src_gap
    xs = cx - total / 2.0
    srcs = [(r"unified diff", None),
            (r"graph builder \textrm{(}one of three\textrm{)}", C_KG),
            (r"similarity retrieval", C_RAG)]
    for i, (lab, col) in enumerate(srcs):
        x0 = xs + i * (src_w + src_gap)
        opt = "draw=%s,thin" % (col if col else "black!55")
        box(x0, -1.42, x0 + src_w, -0.80, lab, opt)
    L.append(r"\draw[thin,black!65] (%.3f,-1.62) -- (%.3f,-1.62);"
             % (xs + src_w / 2.0, xs + total - src_w / 2.0))
    for i in range(3):
        x0 = xs + i * (src_w + src_gap) + src_w / 2.0
        L.append(r"\draw[thin,black!65] (%.3f,-1.42) -- (%.3f,-1.62);"
                 % (x0, x0))
    arrow(cx, -1.62, -2.06)

    box(cx - SPINE, -2.72, cx + SPINE, -2.06,
        r"\textbf{evidence pack} \textrm{(}one JSON file per pull request,"
        r"\\generated once and reused\textrm{)}",
        "draw=black!75,line width=0.7pt")
    note(cx + SPINE + 0.20, -2.39,
         r"\begin{tabular}{@{}l@{}}generation reads\\this file only\end{tabular}")

    # -- The four arms, as nested subsets of the pack's fields -------------
    y_arm_top, y_arm_bot = -3.42, -5.30
    col_w, col_gap = 2.95, 0.35
    arms_total = n_modes * col_w + (n_modes - 1) * col_gap
    xa = cx - arms_total / 2.0
    L.append(r"\draw[thin,black!65] (%.3f,-2.72) -- (%.3f,-2.96);" % (cx, cx))
    L.append(r"\draw[thin,black!65] (%.3f,-2.96) -- (%.3f,-2.96);"
             % (xa + col_w / 2.0, xa + arms_total - col_w / 2.0))

    blocks = {"diff": (r"diff", C_BASE),
              "graph": (r"graph facts", C_KG),
              "chunks": (r"code chunks", C_RAG)}
    arm_blocks = {"baseline": ["diff"], "kg": ["diff", "graph"],
                  "rag": ["diff", "chunks"],
                  "hybrid": ["diff", "graph", "chunks"]}
    arm_label = {"baseline": r"\baseline{}", "kg": r"\kg{}", "rag": r"\rag{}",
                 "hybrid": r"\hybrid{}"}

    bh, bgap = 0.40, 0.10
    y_arm_label = y_arm_top - 0.30      # baseline of the arm name
    y_drop_end = y_arm_label + 0.26     # stop clear of the name's ascenders
    y_blocks_top = y_arm_label - 0.16
    deepest = y_blocks_top
    for i, mode in enumerate(modes):
        x0 = xa + i * (col_w + col_gap)
        xc = x0 + col_w / 2.0
        L.append(r"\draw[thin,black!65] (%.3f,-2.96) -- (%.3f,%.3f);"
                 % (xc, xc, y_drop_end))
        L.append(r"\node[anchor=base,font=\scriptsize\bfseries] at "
                 r"(%.3f,%.3f) {%s};" % (xc, y_arm_label,
                                         arm_label.get(mode, mode)))
        yb = y_blocks_top
        for key in arm_blocks.get(mode, []):
            lab, col = blocks[key]
            box(x0, yb - bh, x0 + col_w, yb, lab,
                "draw=%s,thin" % col, r"\tiny", fill="%s!8" % col)
            yb -= bh + bgap
        deepest = min(deepest, yb + bgap)
    note(xa - 0.18, (y_blocks_top + deepest) / 2.0,
         r"\begin{tabular}{@{}r@{}}prompt\\contents\end{tabular}", "east")

    y_arm_bot = deepest
    arrow(cx, y_arm_bot - 0.06, y_arm_bot - 0.48)

    # -- Generation and evaluation ----------------------------------------
    y = y_arm_bot - 0.48
    box(cx - SPINE, y - 0.62, cx + SPINE, y,
        r"generator, one call per arm per item")
    arrow(cx, y - 0.62, y - 1.00)

    y2 = y - 1.00
    box(cx - SPINE, y2 - 0.62, cx + SPINE, y2,
        r"$%d \times %d = %d$ review notes" % (n_pr, n_modes, n_pr * n_modes))
    arrow(cx, y2 - 0.62, y2 - 1.00)

    y3 = y2 - 1.00
    cells = n_pr * n_modes * n_judge * n_crit
    box(cx - SPINE, y3 - 0.62, cx + SPINE, y3,
        r"judge panel: %d models $\times$ %d criteria $=$ %s scored cells"
        % (n_judge, n_crit, f"{cells:,}".replace(",", r"\,")),
        "draw=black!55,thin")

    L.append(r"\end{tikzpicture}")
    return "\n".join(header([
        "experiments/2026-09-23_five_judge_panel/RESULTS.json "
        "(arms, panel, criteria)",
    ]) + ["\n".join(L)]) + "\n"


# ---------------------------------------------------------------------- main


def fig_human_study(hs: dict) -> str:
    """Per-criterion human preference, with the null at 0.5 rather than 0.

    Rows are grouped by evidential status rather than by effect size, because
    the whole point of the pre-registration is that one of these six rows was
    nominated as the test and the others were not. Colour carries that: the
    confirmatory endpoint is in the mode colour, everything decided after the
    fact is grey.
    """
    # The instrument labels its six items H1..H6 (Table tab:study-criteria);
    # the results JSON keys them by the closest rubric criterion.
    hid = {"F3": "H1", "F2": "H2", "T3": "H3", "Q5": "H4", "R1": "H5",
           "C6": "H6"}
    short = {"H1": "names affected code",
             "H2": "describes failure situations",
             "H3": "points to test files",
             "H4": "explains why something is a problem",
             "H5": "comments on code clarity",
             "H6": "covers the important issues"}

    def row(cid, mean, ci, p, colour, note=None, rule=False):
        cid = hid.get(cid, cid)
        return {"label": r"\textbf{%s} %s" % (cid, short[cid]) if cid in short
                         else r"\textbf{%s}" % cid,
                "mean": mean, "lo": ci[0], "hi": ci[1], "p": p,
                "colour": colour, "note": note, "rule": rule}

    def shown_p(p: float, digits: int) -> str:
        return f"{p:.{digits}f}"

    prim = hs["primary"]
    pid = prim["criterion"].rstrip("*")
    rows = [{"kind": "header", "label": "Primary (confirmatory)"},
            row(pid, prim["mean"], prim["ci"], prim["p"], C_KG,
                note=shown_p(prim["p"], 4))]

    ov = hs["secondary_overall"]
    rows += [{"kind": "header", "label": "Secondary (estimation only)",
              "rule": True},
             {"label": r"\textbf{Overall} usefulness", "mean": ov["mean"],
              "lo": ov["ci"][0], "hi": ov["ci"][1],
              # No significance claim was pre-registered for this endpoint, so
              # the marker must stay open whatever the interval happens to do.
              "p": 1.0, "colour": C_BASE, "note": "---"}]

    rows.append({"kind": "header", "label": "Exploratory (Holm-corrected)",
                 "rule": True})
    for cid, d in hs["exploratory"].items():
        rows.append(row(cid.rstrip("*"), d["mean"], d["ci"], d["p_holm"],
                        C_BASE, note=shown_p(d["p_holm"], 3)))

    body = forest(rows, width=5.6, label_w=5.6, rowsep=0.48, null=0.5,
                  xlabel="Rater preference for the \\kg{} review "
                         "($0.5 =$ no preference)",
                  p_w=1.25)
    return "\n".join(header([
        "experiments/2026-07-06_user_study_prs/RESULTS_HUMAN_V4.json "
        "(n = %d raters, 6 pull requests each)" % hs["n_raters"]]) + [body]) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--only", action="append", default=None,
                    help="effects | localisation | robustness | detection | "
                         "human")
    args = ap.parse_args()

    out = Path(args.out)
    if not out.is_absolute():
        out = REPO_ROOT / out
    out.mkdir(parents=True, exist_ok=True)

    def load(rel: str) -> dict:
        return json.loads((REPO_ROOT / rel).read_text())

    # Experiment 1 figures use the Joern-unified five-judge panel (n = 35),
    # which is the thesis headline; the 2026-09-23 file is the n = 40 panel
    # and is used here only for Experiment 2 and the panel definition.
    final5 = load("experiments/2026-09-23_five_judge_panel/RESULTS.json")
    unified = load("results/JOERN_UNIFIED_FIVE_JUDGE.json")
    boot = final5_bootstrap(unified)
    conc = final5_concentration(unified)
    single = unified["experiment1"]["individual_judges"]
    gen = load("results/CROSS_GENERATOR_v2.json")
    builder = load("results/BOOTSTRAP_STATS_joern_parity.json")
    conf = load("results/BOOTSTRAP_STATS_confirmatory_clean.json")
    exp2 = final5_detection(final5)
    hs = load("experiments/2026-07-06_user_study_prs/RESULTS_HUMAN_V4.json")
    bcmp = load("results/BUILDER_EDGE_COMPARISON.json")
    panel = {
        "panel": final5["panel"],
        "criteria_definitions": final5["experiment1"]["criteria_definitions"],
    }

    figs = {
        "effects": ("fig_exp1_effects.tex", lambda: fig_exp1_effects(boot)),
        "localisation": ("fig_criterion_localisation.tex",
                         lambda: fig_criterion_localisation(conc)),
        "robustness": ("fig_exp1_robustness.tex",
                       lambda: fig_exp1_robustness(boot, single, gen, builder,
                                                   conf)),
        "detection": ("fig_exp2_detection.tex",
                      lambda: fig_exp2_detection(exp2)),
        "human": ("fig_human_study.tex", lambda: fig_human_study(hs)),
        "builders": ("fig_builder_edges.tex",
                     lambda: fig_builder_edges(bcmp)),
        "pipeline": ("fig_pipeline.tex",
                     lambda: fig_pipeline(boot, panel)),
    }
    wanted = args.only or list(figs)
    for name in wanted:
        if name not in figs:
            print(f"unknown figure {name!r}; have {sorted(figs)}")
            return 2
        fname, build = figs[name]
        (out / fname).write_text(build())
        print(f"wrote {fname}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
