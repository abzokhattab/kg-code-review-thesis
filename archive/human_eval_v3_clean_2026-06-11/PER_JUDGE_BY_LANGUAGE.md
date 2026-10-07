# Per-judge × per-language KG-rel d_z (parity n=35)

Closes the reviewer attack: "the Java effect (d_z=+0.58) might be one
judge being lenient." If the Java cell is positive across all three
judges, the language effect is judge-robust within Java. Same logic
applies to every (judge, language) cell.

**KG-rel = sum of 9 binary criteria (F3, F4, T1, T2, T3, M1, M3, C2, Q2).**
Each judge scores each PR; per-judge KG-rel is reconstructed from each
judge's individual criterion scores. Δ = parity − baseline, paired by PR.

## d_z by (judge, language)

| Judge | C++ | Java | Python | Scala | TypeScript | overall |
|---|---:|---:|---:|---:|---:|---:|
| gemini:gemini-2.5-flash | **-0.10** (n=6) | **+0.44** (n=11) | **+0.56** (n=8) | _+0.00_ (n=2) | **+0.21** (n=8) | **+0.28** (n=35) |
| openai:gpt-4o | **+0.41** (n=6) | **+0.79** (n=11) | **-0.11** (n=8) | _+2.12_ (n=2) | **+0.11** (n=8) | **+0.34** (n=35) |
| openai:gpt-4o-mini | **-0.09** (n=6) | **+0.16** (n=11) | **+0.00** (n=8) | _+0.00_ (n=2) | **+1.00** (n=8) | **+0.20** (n=35) |
| **panel** (majority-vote) | **+0.00** (n=6) | **+0.58** (n=11) | **+0.00** (n=8) | **+0.00** (n=2) | **+0.54** (n=8) | **+0.30** (n=35) |

Cells in **bold** have n ≥ 4 PRs; cells in _italics_ have n < 4 and are
shown for transparency only — d_z is not reliable on n < 4.

**Note on metrics.** The per-judge rows compute KG-rel as the sum of each
judge's binary scores on the 9 KG-rel criteria, then take per-PR Δ. The
**panel** row uses the majority-vote-per-criterion KG-rel (the headline
metric reported elsewhere) — that gives the panel parity d_z = +0.30
(matches the value reported in `HONEST_HEADLINE.md` and `COMBINED_RESULTS_TABLE.md`).
Per-judge and panel d_z differ because majority-vote loses the per-criterion
variance that the per-judge sums retain; the two are related but not identical.

## Reading

- **Java is positive across all three judges.** The d_z=+0.58 reported
  in the per-language CI table is not driven by one lenient judge.
  Per-judge Java d_z: gemini-2.5-flash: +0.44, gpt-4o: +0.79, gpt-4o-mini: +0.16.

- **TypeScript is positive across all three judges** (gemini-2.5-flash: +0.21, gpt-4o: +0.11, gpt-4o-mini: +1.00). The
  +0.54 figure is judge-robust at this n.

- **Python (n=8):** the panel aggregate is +0.00 but per-judge cells
  disagree on sign: gemini-2.5-flash: +0.56, gpt-4o: -0.11, gpt-4o-mini: +0.00. The null is the average of judge
  disagreement, not three-way agreement on no-effect.

- **C++ (n=6):** also judge-mixed: gemini-2.5-flash: -0.10, gpt-4o: +0.41, gpt-4o-mini: -0.09. The null is similarly
  an average of disagreement.

- **Per-judge overall d_z** ranges from +0.20 to +0.34; all positive,
  consistent with the headline panel-aggregated d_z = +0.30.

## What this changes about the audit

The per-language results in `PER_LANGUAGE_CI_AND_FALSIFICATION.md` §1
are now also dis-aggregated by judge. **Java (+0.58) and TypeScript (+0.54)**
are positive across all three judges — not single-judge artefacts.
**Python (+0.00) and C++ (+0.00)** are panel-aggregate nulls that mask
per-judge sign disagreement at small n (8 and 6), so the discussion
chapter should not over-interpret these as 'KG fails on Python/C++';
the right reading is 'judges disagree at this n, panel averages to zero'.

The thesis can describe Java and TypeScript parity effects as judge-robust
within each language. Python and C++ should be reported as panel nulls
with judge-disagreement noted.