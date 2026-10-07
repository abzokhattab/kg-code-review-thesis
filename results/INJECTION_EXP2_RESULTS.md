# Experiment 2 — controlled cross-file defect injection (headline results)

**Run:** 2026-07-13. **Design:** pre-registered 2026-07-05
(`experiments/2026-07-05_injection_exp2/docs/DESIGN_AND_PREREGISTRATION.md`;
§13 sign-off in `DECISIONS.md`). **Full output:**
`experiments/2026-07-05_injection_exp2/out/{RESULTS.md,results.json,JUDGE_VALIDATION.md}`.

## Setup (one line each)

- **40 auto-discovered injections** (28 structural S1–S5 + 12 local-control
  L1–L2) across scikit-learn (Python), kafka-streams (Java),
  grafana-data (TypeScript). Pre-registered target was 48; band supply
  shortfalls (S3 operator is Python-only; Java has no S5 barrels) are
  reported, not back-filled (manifest §shortfalls).
- Direction-blind selection: top structural fan-out first, no review consulted.
- 6 arms: baseline / kg (deployed Joern CPG) / rag (top_k=10) / hybrid /
  kg_idealised (static-resolver ceiling) / kg_joern_inherit (Joern +
  import/INHERITS_FROM edges — the pre-declared augmentation).
- Generator gpt-4o (T=0.3, hardcoded in `prnote/note.py::generate_review_direct`;
  corrected 2026-08-12 from an earlier "T=0.4"); judges gpt-4o-mini + gpt-4o + gemini-2.5-flash,
  majority of 3, ties→0 (identical to Experiment 1).
- Ground truth: static-structural (independently resolved dependents with
  evidence lines in the manifest).

## Structural bands (n=28) — detection rate [95% bootstrap CI]

| Arm | Detected | Rate |
|---|---:|---:|
| baseline | 0/28 | 0.00 [0.00, 0.00] |
| rag | 1/28 | 0.04 [0.00, 0.11] |
| hybrid | 12/28 | 0.43 [0.25, 0.61] |
| **kg (deployed Joern)** | **15/28** | **0.54 [0.36, 0.71]** |
| kg_joern_inherit | 21/28 | 0.75 [0.57, 0.89] |
| kg_idealised (ceiling) | 26/28 | 0.93 [0.82, 1.00] |

Contrasts (paired permutation, B=20 000, seed 2026):
**kg − baseline = +0.54 [+0.36, +0.71], p < 0.0001** → pre-registered
§10.1 threshold (≥ +0.30, p < .05) **met: supports RQ2b**.
rag − baseline = +0.04, p = 1.0. hybrid − baseline = +0.43, p = 0.0005.

## Local control bands (n=12) — the placebo check

kg − baseline = **−0.08 [−0.25, +0.00]**, inside the pre-registered parity
window [−0.15, +0.15] (§10.2) → **the KG advantage is structural, not a
context-volume artefact**. All arms detect local defects at 0.83–1.00
(the defect is visible in the diff, as designed).

## S4 inheritance band (n=6) — the engineering contribution

kg_joern_inherit 5/6 vs kg 2/6: **Δ = +0.50** → pre-registered §10.3
threshold (≥ +0.30) **met**: adding import/inheritance edges recovers the
Joern blind spot found in the prototype. Overall (all structural bands)
kg_joern_inherit − kg = +0.21 [+0.04, +0.39], p = 0.071 (n=28).

## Judge validation vs deterministic mention-oracle (§9)

gpt-4o-mini 72%, gpt-4o 80%, gemini-2.5-flash 93% agreement; **zero**
"detected-without-mention" flags for both OpenAI judges (no
hallucinated detections). Full lists: `out/JUDGE_VALIDATION.md`.

## Honest notes for the thesis

- n=40 not 48; shortfalls reported per band (pre-reg anti-goalpost rule §14).
- kafka (Java) is the deployed KG's weakest repo (2/8 structural) even
  with correct Joern edges present for some misses — edge presence is
  necessary but not sufficient (salience/rendering), consistent with the
  prototype's `LinearRegression` caveat.
- Local-band detection is high for all arms because a local defect is
  visible in the diff; the band's job is the *difference* (parity), not
  the level.
- One grafana TS scope substitution vs the pre-reg's "grafana Go/TS"
  (Joern Go frontend gap; documented in `DECISIONS.md` §2 before the run).
