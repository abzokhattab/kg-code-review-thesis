# Human-Study Analysis Runbook

_How to go from Christian's pilot-v2 Google Sheet to a thesis-ready
human↔LLM agreement analysis. Everything you need lives in
`scripts/analyze_human_llm_agreement.py`._

---

## 1. Export the human data from the Google Sheet

The Apps Script writes to **four** tabs. You only *need* the main one,
but the optional tabs unlock demographic slicing and rater-quality
filtering — export them too if they exist.

| Sheet tab          | Purpose                          | Filename to save as                       | Required? |
|--------------------|----------------------------------|-------------------------------------------|-----------|
| `responses`        | one row per (rater, PR, label)   | `human_eval/pilot_v2_responses.csv`       | **yes**   |
| `demographics`     | one row per task submit per rater (so role/exp_years/freq_review_pr appear once per rater after dedup) | `human_eval/pilot_v2_demographics.csv` | optional  |
| `quality_flags`    | auto-flagged anomalies per rater | `human_eval/pilot_v2_quality_flags.csv`   | optional  |
| `feedback`         | free-text feedback per rater     | `human_eval/pilot_v2_feedback.csv`        | optional  |

For each tab: `File → Download → Comma Separated Values (.csv)` (Sheets
exports the *active* tab only — switch tabs and re-download for the
others).

Expected `responses` columns (any order, case-insensitive; missing
columns are ignored):

```
rater_id, pr_id, comparison, blind_label, mode,
F3*, F2*, T3, Q5, R1, C6,          ← per-criterion columns
difficulty, preference,            ← A / B / Both/both (case-insensitive)
time_spent_ms, notes, github_clicks
```

A `scores` column containing a JSON blob (`{"F3*": 1, ...}`) is also
accepted in place of the per-criterion columns — useful if the Apps
Script writes in that shape.

Expected `demographics` columns: `rater_id, role, exp_years,
freq_review_pr, completed_at` (the UI emits these exact field names —
do not rename them). Per-rater rows can be duplicated (the UI re-emits
on every task submit); the analyzer keeps the last value per rater.

Expected `quality_flags` columns: `rater_id, quality_flags,
completed_at`. The `quality_flags` cell may be a comma-separated list
or a JSON array.

Expected `feedback` columns: `rater_id, feedback, completed_at`.

## 2. Run the analysis

```bash
# 1. Minimal — only the main responses CSV
python3 scripts/analyze_human_llm_agreement.py \
    --human human_eval/pilot_v2_responses.csv \
    --out results/pilot_v2_agreement.json

# 2. Full — all 4 tabs, with auto-exclusion of low-quality raters
python3 scripts/analyze_human_llm_agreement.py \
    --human         human_eval/pilot_v2_responses.csv \
    --demographics  human_eval/pilot_v2_demographics.csv \
    --quality-flags human_eval/pilot_v2_quality_flags.csv \
    --feedback      human_eval/pilot_v2_feedback.csv \
    --exclude-flagged \
    --out results/pilot_v2_agreement.json

# 3. Drop a specific rater by hand (repeatable)
python3 scripts/analyze_human_llm_agreement.py \
    --human human_eval/pilot_v2_responses.csv \
    --exclude-rater test_rater_42

# 4. Dry-run with synthetic data (no real CSV needed)
python3 scripts/analyze_human_llm_agreement.py --sample
```

The script writes a full JSON report to the `--out` path and prints a
human-readable summary to stdout.

## 3. What the output contains

- **Overall human↔LLM agreement** — raw % and Cohen's κ across all
  criteria, all raters, all modes. Landis & Koch interpretation
  included (slight / fair / moderate / substantial / almost perfect).
- **Per-criterion table** — for each of the 6 human criteria
  (`F3*, F2*, T3, Q5, R1, C6`): `n`, raw agreement %, κ, and whether
  the human rubric is *stricter* than the LLM rubric it is compared
  against (applies to `F3*` and `F2*`, which add a "concrete" requirement
  that the 25-criterion LLM prompt does not).
- **Per-rater and per-mode slices** for every criterion — lets you
  check if agreement is uniform across raters or concentrated on one
  mode (e.g. is Christian systematically stricter on KG-mode reviews?).
- **Largest flips** — a list of (rater, PR, mode, criterion) cells
  where human and LLM disagreed, with the rater's note field preserved.
  These are the qualitative-analysis seeds for the thesis.
- **Inter-rater κ** — when ≥ 2 raters are present, pairwise Cohen's κ
  for each criterion. This is the human-side reliability signal that
  reviewers will ask about.
- **Preference distribution** — A/B/Both tallies by comparison
  (bl_vs_kg, kg_vs_rag). Maps directly to the headline "do humans
  prefer KG over baseline?" claim. (`Both`/`both` are normalised; old
  exports won't lose data.)
- **Descriptive task stats** — overall and per-comparison difficulty
  mean/median, per-rater median time-on-task (ms), GitHub-click rate.
  Use these for the "study took ~25 min, median difficulty 3/5" methods
  paragraph.
- **Per-rater audit** — n, κ vs LLM, demographics, attached quality
  flags, free-text feedback, all in one block. Use this to decide who
  (if anyone) to exclude from the headline numbers.
- **Demographic slices** — agreement broken down by `role`,
  `exp_years`, `freq_review_pr` whenever the demographics CSV is
  passed. Lets you say things like "experienced reviewers agreed with
  the LLM more often (κ=0.62) than students (κ=0.31)" if the data
  supports it.

## 4. How to read the numbers

### Agreement baselines

Using Landis & Koch (1977) anchors:

| Cohen's κ | Interpretation | What to say in the thesis |
|-----------|----------------|----------------------------|
| < 0.20 | slight | "LLM judge unreliable on this criterion — treat as qualitative only." |
| 0.21 – 0.40 | fair | "Consistent enough for directional claims, not for magnitudes." |
| 0.41 – 0.60 | moderate | "LLM judgement aligns with humans; report LLM means alongside human." |
| 0.61 – 0.80 | substantial | "Strong alignment; LLM and human can be used interchangeably for this criterion." |
| > 0.80 | almost perfect | "Near-ceiling agreement; LLM is a valid proxy." |

### Where to look for trouble

1. **κ < 0.20 on any criterion** → candidate criterion to drop from the
   headline comparison and report only qualitatively. Also worth asking
   whether the rubric wording was ambiguous.
2. **`human_yes_rate_pct` and `llm_yes_rate_pct` in the per-mode slice**
   far apart with high agreement (> 75 %) → the criterion is saturated.
   You saw this on R1 (readability) in the LLM-only run. It's a
   *finding* more than a problem, but needs a sentence in the thesis.
3. **Inter-rater κ very different from human↔LLM κ** → tells you whether
   the limit of the protocol is the LLM side or the human side. If
   raters disagree with each other more than they disagree with the LLM,
   the rubric itself is the weak link.

## 5. Mapping from human criteria to LLM sources

This is in-code in `HUMAN_TO_LLM_CRITERION`:

| Human criterion | LLM source | Notes |
|-----------------|------------|-------|
| `F3*` | LLM `F3` | Human rubric is stricter ("name concrete components") — expect LLM to be slightly more lenient; this asymmetry is flagged in the output. |
| `F2*` | LLM `F2` | Same caveat. |
| `T3`  | LLM `T3` | Semantically aligned. |
| `Q5`  | LLM `Q5` | Semantically aligned. |
| `R1`  | LLM `R1` | Semantically aligned. |
| `C6`  | `results/c6_completeness_llm.json` | C6 is served from the dedicated multi-judge completeness run. |

## 6. Suggested thesis sentences (once you have real κ values)

Fill in the placeholders from `results/pilot_v2_agreement.json`:

> We validate the LLM judge panel against \<N\> human raters across
> \<M\> PR × mode pairs and \<K\> criteria. Across 6 criteria we observe
> Cohen's κ in the \<low\>–\<high\> range (mean \<μ\>), which maps to
> \<interpretation\> agreement per Landis & Koch (1977). Agreement is
> weakest on \<criterion\>, likely because \<reason from flip list\>,
> and strongest on \<criterion\>. We retain only criteria with κ ≥ 0.40
> for the primary comparison, relegating \<criterion\> to a qualitative
> companion analysis (Table \<ref\>).

## 7. If things go wrong

- **"Missing `results/checklist_evaluation_llm.json`"** → run
  `python3 scripts/evaluate_reviews.py` first (the multi-judge LLM eval).
- **"Unmatched cells (no LLM source)"** in the report banner → means
  the human CSV has a (PR, mode) combination that isn't in the LLM eval
  (e.g. a hybrid-mode row, which the human study doesn't use). Harmless,
  but investigate if > 0 for expected modes.
- **κ NaN / negative** on a criterion → usually one side scored all-0
  or all-1 (saturation). The `by_mode` slice will tell you which side.
  Report this as a limitation for that specific criterion and fall back
  on raw agreement.
- **Single rater (pilot v1 shape)** → inter-rater section is empty by
  design. Everything else works.
