# v1 Dataset Audit — what we found in `data/luca_prs_fixed/`

_Audit performed 2026-04-30 on the 25-PR LLM-judge dataset that
underpins the headline RQ1/RQ2 results in
`results/checklist_evaluation_llm_multi.json`. Findings below
motivated the v2 rebuild in `dataset_v2/`._

## Provenance of the 25 PRs (three layers, decreasing rigour)

| Layer | PRs | Source |
|-------|-----|--------|
| 1 | 1, 2, 3, 5, 6, 7 | LUCA paper catalog (`LUCA_PRS_CATALOG.md`). Selected by Loseto et al. for **PR-description generation**, not code review. |
| 2 | 8, 9, 10, 11 | Hand-stub'd "filler" entries with **placeholder titles** and **empty bodies**. No script in repo produced them; no selection rationale recorded. |
| 3 | 12 – 26 | `scripts/expand_dataset.py` `NEW_PRS` dict — 15 PRs hard-coded with no commentary on selection. The thesis Methods chapter says only "the 25-PR dataset spans four repositories in three language families." |

There is **no documented direction-blind selection criterion** for the
25 PRs. `results/DATA_MANIFEST.md` describes the stimuli as
"hand-curated", which is honest but not defensible at a viva.

## Specific data-quality issues per PR

Numbers from `dataset_v2/scripts/audit_v1_dataset.py` (committed in
this folder).

### Issue 1 — Empty body (LLM had no PR description)

10 of 25 PRs (40 %): **PRs 1, 2, 3, 5, 6, 7, 8, 9, 10, 11.**

The reviewer LLM was given only `title + diff`, never the
maintainer-written description. **This biases against baseline mode**
(which has nothing else to draw on) and **inflates the apparent
KG-vs-baseline lift** because KG/RAG retrieve repo context that
partially compensates for the missing description.

### Issue 2 — Placeholder title (LLM had no real title either)

4 of 25 PRs (16 %): **PRs 8, 9, 10, 11.**

| PR | Placeholder title shown to LLM | Real title on GitHub |
|----|--------------------------------|----------------------|
| 8  | `"Grafana PR #95949"` | actual title from grafana#95949 |
| 9  | `"Grafana PR #98123"` | actual title from grafana#98123 |
| 10 | `"scikit-learn PR #22365"` | actual title from sklearn#22365 |
| 11 | `"Django PR #18523"` | actual title from django#18523 |

For these 4 PRs, the only signal the model had was the diff itself.
This is a more severe version of Issue 1.

### Issue 3 — Diffs truncated at the 15 kB cap

9 of 25 PRs (36 %): **PRs 6, 7, 8, 9, 10, 13, 15, 21, 24.**

The cap is hard-coded in `scripts/expand_dataset.py`
(`max_chars = 15000`) and silently elides any diff content past it.
Both generation and evaluation operate on the truncated diff, so
this does not break per-PR comparisons, but:

- C6 ("missing information") is meaningless on a stimulus that is
  itself missing information.
- The judge cannot verify file:line citations that fall in the
  truncated tail.

### Issue 4 — Documentation-only PRs (no real code review surface)

3 of 25 PRs (12 %): **PR 11** (`.txt` only), **PR 16** (`.md` only),
**PR 25** (Python files but the diff is exclusively docstring text).

A code-review benchmark cannot validate review quality on PRs that
have no code to review.

### Issue 5 — Reverted PR (no ground-truth to compare against)

1 of 25 PRs: **PR 26** (django/django#18322 — explicitly titled
`Reverted "Fixed #35564 ..."`).

A revert PR is a special case that the rubric was not designed for.
The prior selection (`results/HUMAN_STUDY_PR_SELECTION.md` §2.3)
already excluded PR 26 from the human study for this reason; it
remained in the LLM-judge dataset.

### Issue 6 — Closed / not-merged PR

1 of 25 PRs: **PR 7** (microsoft/TypeScript#57375). LUCA's own
catalog flagged this:

> "Skip PR #4 for now, document why (rejected PR = no ground truth)."

It was retained anyway and is the only non-merged stimulus in the
set.

### Issue 7 — KG-unparseable single-Jelly stimuli (tiny + degraded grounding)

2 of 25 PRs: **PR 5** (0.8 kB, single `.jelly`) and **PR 17** (0.9 kB,
single `.jelly`). LUCA's tree-sitter parsers do not cover Jelly, so
KG mode operates with degraded grounding on these PRs (see
`human_eval_v2/docs/DECISION_LOG.md` §13 for the same issue in the
human study).

### Issue 8 — Binary-asset-heavy diff

1 of 25 PRs: **PR 19** (3 of 11 changed files are deleted PNG/GIF
icons). The diff includes "Binary files differ" markers that
neither the generator nor the judge can score on. Kept in v2 with
disclosure because the substantive Java changes are real.

## Summary table — issues per PR

| PR | Issues | Decision in v2 |
|---:|--------|----------------|
|  1 | empty body | **keep**, recover body |
|  2 | empty body | **keep**, recover body |
|  3 | empty body | **keep**, recover body |
|  5 | empty body, jelly-only, tiny | **drop** (Issue 7) |
|  6 | empty body, truncated | **keep**, recover body + full diff |
|  7 | empty body, truncated, **rejected/not merged** | **drop** (Issue 6) |
|  8 | placeholder title, empty body, truncated | **keep**, recover title + body + full diff |
|  9 | placeholder title, empty body, truncated | **keep**, recover title + body + full diff |
| 10 | placeholder title, empty body, truncated | **keep**, recover title + body + full diff |
| 11 | placeholder title, empty body, **docs-only** (`.txt`) | **drop** (Issue 4) |
| 12 | (clean — backport with 60-char body) | **keep** as-is |
| 13 | truncated | **keep**, full diff |
| 14 | (clean) | **keep** as-is |
| 15 | truncated | **keep**, full diff |
| 16 | **docs-only** (`.md`) | **drop** (Issue 4) |
| 17 | jelly-only, tiny | **drop** (Issue 7) |
| 18 | (clean) | **keep** as-is |
| 19 | binary-heavy | **keep**, disclose |
| 20 | (clean) | **keep** as-is |
| 21 | truncated | **keep**, full diff |
| 22 | (clean) | **keep** as-is |
| 23 | (clean) | **keep** as-is |
| 24 | truncated | **keep**, full diff |
| 25 | **docs-only** (docstrings) | **drop** (Issue 4) |
| 26 | **revert PR** | **drop** (Issue 5) |

## Net change

- **Dropped:** 7 PRs — `{5, 7, 11, 16, 17, 25, 26}` (issues 4–7).
- **Kept with fixes:** 11 PRs — `{1, 2, 3, 6, 8, 9, 10, 13, 15, 21, 24}` (recovery via GitHub).
- **Kept as-is:** 7 PRs — `{12, 14, 18, 19, 20, 22, 23}`.
- **Final v2 set: 18 PRs.**

## Why this matters for the thesis

The headline RQ1/RQ2 claim — "KG context improves reviews on
KG-relevant criteria over baseline" — was computed on a dataset
where 40 % of stimuli had no PR description. Empty bodies
**asymmetrically disadvantage baseline mode** (which has nothing else
to draw on) and **may inflate the KG-vs-baseline delta**. This is a
generation-time confound that the LLM-judge step cannot detect or
correct.

The v2 rebuild eliminates this confound at the source: every kept PR
has its full GitHub body and full untruncated diff. The headline
result will be re-computed on the cleaned 18-PR dataset and reported
side-by-side with the v1 result.
