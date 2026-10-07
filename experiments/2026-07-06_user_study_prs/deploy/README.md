# Deployment of the v4 human study

What ran in production between 26 August and 6 October 2026, and how a
response travelled from a rater's browser to the thesis table.

| Stage | File | Notes |
|---|---|---|
| Study UI | `../pilot/index.html` + `../pilot/study_data.json` | Static page, instrument version `python-prs-study-v4-diff-default-r14`, build `2026-08-24-data-epoch`. Served from GitHub Pages at `khattab-thesis/pr-review-study` (the live file was verified byte-identical to `pilot/index.html` on 2026-08-24). The six PR tasks, both reviews per PR, plain-language context and file-existence badges are all read from `study_data.json`. |
| Submission endpoint | `apps_script_webhook.gs` | Google Apps Script (v5, 2026-08-19) bound to the results spreadsheet. Receives one JSON payload per completed task, validates `study_id` / `instrument_version`, appends rows to the `raw_log`, `responses_criteria` and `demographics` sheets. The deployed `/exec` URL is redacted from `index.html` (`SHEET_URL`); redeploying mints a new one. |
| Export | spreadsheet → `Human Eval (N).xlsx` | Downloaded manually; contains rater identifiers and is **not** in this repository. |
| Analysis | `../../../scripts/convert_xlsx_to_csv.py` → `../analyze_responses.py` | `analyze_responses.py responses.csv` applies `../ANALYSIS_PLAN.md`: filters on study id and instrument version, drops pilot/test ids, keeps raters who completed all six tasks, un-blinds from the row's own `mode_A`/`mode_B`, pseudonymises to `P01…`, and writes `../RESULTS_HUMAN_V4.{md,json}`. `--selftest` checks the logic on synthetic data at no cost. |

To re-run the analysis you need the spreadsheet export; to re-host the study
you need to deploy `apps_script_webhook.gs` to a Google account that owns a
results sheet and paste its `/exec` URL into `SHEET_URL` in `index.html`.
