# `human_eval_v3/` — locked human study, rebuilt on `dataset_v2` stimuli

The v3 human-evaluation study folder. **Selection is locked**
(unchanged from v2 — Decision 13 still binds). v1 and v2 are preserved
unmodified for the side-by-side audit trail.

## What's different in v3

v3 is a structural fork of `human_eval_v2/` with **one substantive
change**: the LLM-generated reviews shown to raters now come from
`outputs/luca_prs_v2/` (the cleaned `dataset_v2` rebuild), not
`outputs/luca_prs_fixed/` (the contaminated v1 dataset).

This makes RQ3 honest: the LLM judge ran the multi-judge panel against
these same v2 reviews (see `results/V1_VS_V2_COMPARISON.md`), so the
human↔LLM kappa is now computed on identical stimuli on both sides.

| Aspect | v2 | v3 |
|--------|----|----|
| Evidence packs | `data/luca_prs_fixed/` (truncated diffs, empty bodies) | **`data/luca_prs_v2/`** (50 kB diffs, full bodies) |
| LLM reviews | `outputs/luca_prs_fixed/` (10/18 PRs had empty PR-body context at generation) | **`outputs/luca_prs_v2/`** (full PR-body context, RAG re-built for 4 contaminated PRs) |
| `STUDY_ID` | `human_eval_v2` | `human_eval_v3` |
| localStorage prefix | `heval3_v2_` | `heval3_v3_` |
| Diff cap (defensive) | 15 kB | 50 kB |
| Comparisons per PR | 2 (`bl_vs_kg`, `kg_vs_rag`) | **1 (`bl_vs_kg` only)** — Decision 15 |
| PR set | `{12, 1, 3, 14}` (4 PRs) | **`{1, 14, 22, 24, 30, 42}` (6 PRs)** — Decision 17 (was `{12, 1, 3, 14, 21, 24}` per Decision 16; 3 swapped for higher rater discriminability) |
| Trials per rater | 8 (~25 min) | **6 (~15–18 min)** — Decisions 15 + 16 |
| A/B difference highlighting | none | **sentence-level Jaccard shading** — Decision 15 |
| "What differs?" prompt | bottom, optional, generic | **promoted, with attention flag** — Decision 15 |
| Criteria, modes, UI flow | identical | identical |

See `docs/DECISION_LOG.md` Decisions 14–17 for the full justification.

## Final selection (locked, 6 PRs after Decision 17)

| Order | PR | Repo                       | Type        | Diff    | Lang     | bl↔kg overlap |
|------:|---:|----------------------------|-------------|--------:|----------|--------------:|
| 1     |  1 | godotengine/godot          | bug-fix     |  3 051  | C++      | 50 %          |
| 2     | 14 | grafana/grafana            | feature     | 12 025  | TS       | 33 %          |
| 3     | 22 | apache/kafka               | refactor    | 10 555  | Java     |  0 %          |
| 4     | 24 | scikit-learn/scikit-learn  | refactor    | 16 483  | Python   | 50 %          |
| 5     | 30 | godotengine/godot          | test-add    |  9 011  | C++      |  0 %          |
| 6     | 42 | scikit-learn/scikit-learn  | refactor    | 13 416  | Python   |  0 %          |

- 2 godot (C++) + 1 grafana (TypeScript) + 1 kafka (Java) + 2 sklearn (Python)
- All 100 % KG-parseable by tree-sitter (no Jelly templates, no binary-only diffs)
- 2 features + 3 refactors + 1 test-addition
- Mean baseline↔kg problem-overlap: **27 %** (vs 58 % under the previous Decision-16 set — Decision 17 was triggered by supervisor feedback that "the two reviews look mostly the same"; 3 PRs were swapped for the most-differentiable candidates in the 40-PR LLM-judge dataset, holding direction-blind criteria constant)
- All under 17 kB diff (well below the 50 kB cap)
- All single-purpose, all merged, all spot-checked

## Documents that make this defensible

| Document | What it answers |
|----------|-----------------|
| `docs/SELECTION_v2.md` | Why these 4 PRs (and why PRs 17, 19 are *not* in the locked set) — carries over from v2 unchanged |
| `docs/DECISION_LOG.md` | Chronological audit trail of all 14 decisions, including the v2→v3 stimuli swap (Decision 14) |
| `docs/ANALYSIS_PLAN.md` | **Pre-registered** success/failure/null criteria for the κ computation, locked before any rater data exists — same plan as v2 |
| `docs/DEPLOY.md` | How to deploy v3 alongside v1/v2 (Netlify / Vercel / static / Apps Script) |

## Layout

```
human_eval_v3/
├── README.md                      ← this file
├── index.html                     ← v3 fork of the rater UI; loads ./study_data.json
├── study_data.json                ← built from data/luca_prs_v2/ + outputs/luca_prs_v2/
├── docs/
│   ├── SELECTION_v2.md            ← rationale, final 4 PRs (carried over from v2)
│   ├── DECISION_LOG.md            ← 14 decisions, including v2→v3 stimuli swap
│   ├── ANALYSIS_PLAN.md           ← pre-registered κ thresholds and reporting commitments
│   └── DEPLOY.md                  ← how to deploy v3 alongside v1/v2
├── analysis/
│   ├── pr_candidates.json         ← all 25 LUCA PRs scored on 9 filters
│   └── pr_candidates.md           ← human-readable ranked table
└── scripts/
    ├── analyze_pr_candidates.py   ← reproduces the candidate table
    ├── build_study_data_v2.py     ← builds study_data.json from dataset_v2 sources
    ├── deep_audit.py              ← content-quality audit on study_data.json
    ├── fetch_pr_bodies.py         ← (legacy v2 helper; v2 evidence already has bodies)
    ├── fetch_pr_ground_truth.py   ← fetches reviewer comments + filenames
    └── smoke_test.py              ← deploy gate: validates study_data.json + index.html
```

## Reproducibility

```bash
# 1. (One-time) build the cleaned dataset_v2 evidence + reviews.
#    See dataset_v2/docs/STATUS.md for the rebuild trail.
#    For v3 we assume data/luca_prs_v2/ and outputs/luca_prs_v2/ already exist.

# 2. Re-build study_data.json (idempotent)
python3 human_eval_v3/scripts/build_study_data_v2.py

# 3. Smoke-test (must exit 0 before any deployment)
python3 human_eval_v3/scripts/smoke_test.py

# 4. Deep audit (must exit with 0 problems)
python3 human_eval_v3/scripts/deep_audit.py

# 5. Local visual check
python3 -m http.server 8765 --directory human_eval_v3
# then open http://localhost:8765/index.html
```

All scripts run from the repo root and produce byte-stable outputs
from byte-stable inputs (`data/luca_prs_v2/` and `outputs/luca_prs_v2/`).

## Cleanups applied to every review in `study_data.json`

- Stripped leading/trailing ` ``` ` fences.
- Removed the `- Code Owners: …` line from KG Traceability sections
  (mode-leak fix carried over from v2).
- Removed empty `Traceability` sections entirely.
- (Optional) full PR bodies from `data/pr_body_overrides.json` —
  redundant in v3 since v2 evidence already has full bodies, but kept
  for parity with v2 cleanup pipeline.
- Defensive truncation marker if any diff hits the 50 kB v2 cap (none
  in the current selection; max is PR 14 at 12 kB).

These are surface-form normalisations. They do not change which issues
the review flags or which recommendations it makes.

## Direction-blind disclosure

None of the v3 selection or stimuli choices depend on which mode wins.
The PR set is identical to v2 (Decision 13 stands). The stimuli swap
(Decision 14) replaces v1-grounded reviews with v2-grounded reviews
**uniformly across all three modes**. A KG review and a baseline review
for the same PR were both regenerated against the same recovered PR
body — the fix improves grounding for all modes, not preferentially
for any one of them.

## Outstanding work before v3 runs

| # | Step | Status |
|--:|------|--------|
| 1 | Lock PR list | **DONE** — `{1, 14, 22, 24, 30, 42}` (Decisions 13 → 16 → 17) |
| 2 | Build clean `study_data.json` from v2 stimuli | **DONE** (Decision 14) |
| 3 | Trim to 1 comparison per PR + add diff highlighting + "what differs?" attention flag | **DONE** (Decision 15) |
| 3b | Recover 6-PR scope (add PRs 21 + 24 from the audited dataset_v2 pool) | **DONE** (Decision 16) |
| 4 | Fork rater UI (`index.html`) for v3 namespacing | **DONE** — `STUDY_ID="human_eval_v3"`, `heval3_v3_` localStorage |
| 5 | Smoke-test (script + browser) | **DONE** (`scripts/smoke_test.py` exits 0) |
| 6 | Deep audit (0 problems required) | **DONE** (1 minor warning carried over from v2) |
| 7 | Pre-registered analysis plan | **DONE** — `docs/ANALYSIS_PLAN.md` (carried over from v2) |
| 8 | Decision log up to Decision 15 | **DONE** — `docs/DECISION_LOG.md` |
| 9 | Apps Script webhook (currently HTTP 405 — must be fixed before any human study can collect data) | **TODO — only remaining blocker** |
| 10 | Deploy v3 (Netlify / Vercel / static) | **TODO** — see `docs/DEPLOY.md` after step 9 |
| 11 | Pilot — 2 raters before full recruit | **TODO** — recommended; pre-registered analysis allows it |
| 12 | Recruit + run ≥ 10-rater cohort (preferably paid $10–15/session) | **TODO** — do **not** pool with v1 or v2 |
