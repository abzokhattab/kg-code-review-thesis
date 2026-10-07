# Redeploy the Apps Script webhook (5-minute runbook)

_The current `SHEET_URL` returns HTTP 405 — the deployed Web App has been
revoked, unbound from its Sheet, or had its access setting flipped to
"Only myself". The script source (`human_eval/apps_script_webhook.gs`) is
correct. You only need to redeploy._

> Until this is fixed, raters' submissions are NOT making it to the
> spreadsheet. They ARE being saved to the rater's browser localStorage
> via the new client-side outbox, and recoverable via the "Download my
> responses" button on the completion screen. So existing in-flight data
> is not lost, but a fix is still required before recruiting raters.

---

## Step 1 — Open the bound spreadsheet

The Sheet that owned the prior deployment is the one whose `id`
appears in the previous Apps Script project's `appsscript.json`. Open
that Sheet in Google Drive.

If you no longer have it:

1. Create a new spreadsheet in Google Drive named e.g.
   `LUCA Thesis · Human Evaluation · v3`.
2. Use that one going forward.

---

## Step 2 — Open the bound Apps Script project

In the Sheet:

1. **Extensions → Apps Script.**
2. A new tab opens with `Code.gs` (possibly empty or with sample code).
3. Select all in `Code.gs` and replace it with the contents of
   `human_eval/apps_script_webhook.gs` (this repo).
4. **Save** (Ctrl/⌘ S).

If a previous (broken) project is still bound, you can either edit it
in place or create a new one — either works as long as the URL ends up
in the static site.

---

## Step 3 — Deploy as Web App

1. Top-right: **Deploy → New deployment**.
2. The gear icon (⚙) next to "Select type": pick **Web app**.
3. Fill in:
   - **Description**: `human_eval webhook · 2026-05-05`
   - **Execute as**: **Me** (your Google account).
   - **Who has access**: **Anyone** (NOT "Anyone with Google account").
4. Click **Deploy**.
5. The first deploy of a new project asks for OAuth consent.
   - Click **Authorize access** → choose your account
     → Google will warn "Google hasn't verified this app" → click
     **Advanced** → **Go to (project name) (unsafe)** → **Allow**.
   - This is normal for personal-account Apps Scripts. The script
     only writes to the bound Sheet.
6. After deploy: copy the **Web app URL**. It looks like
   `REDACTED_WEBHOOK_URL

> Tip: every redeploy creates a new URL. After this run, reuse the same
> deployment with **Manage deployments → ✏ → Deploy** instead of
> **New deployment**, so the URL is stable.

---

## Step 4 — Update `SHEET_URL` in the static site

Three index.html files all share the same constant:

```bash
# From repo root, single command updates all three studies:
NEW_URL='REDACTED_WEBHOOK_URL'
for f in human_eval/index.html human_eval_v2/index.html human_eval_v3/index.html; do
  sed -i.bak "s|const SHEET_URL=\"https://script.google.com/macros/s/[^\"]*\";|const SHEET_URL=\"${NEW_URL}\";|" "$f"
done
```

(The `.bak` files are scratch; delete or `git checkout` after.)

---

## Step 5 — Smoke-test BEFORE redeploying the static site

Use the bundled smoke-test script:

```bash
bash scripts/smoke_test_webhook.sh "$NEW_URL"
```

Or call it manually:

```bash
# (a) deployment alive + sheet reachable, no test rows written
curl -sS -L "$NEW_URL?selftest=1" | python3 -m json.tool

# Expected response:
# { "ok": true,
#   "spreadsheet_id": "1AbC…",
#   "spreadsheet_name": "LUCA Thesis · Human Evaluation · v3",
#   "deployment_alive": true,
#   "timestamp": "2026-…" }

# (b) end-to-end POST writes a test row
curl -sS -L -X POST -H "Content-Type: application/json" \
  -d '{"study_id":"selftest","rater_id":"selftest_'$(date +%s)'","completed_at":"'$(date -u +%FT%TZ)'","ratings":[{"pr_id":1,"comparison":"bl_vs_kg","blind_label":"A","mode":"baseline","scores":{"F3*":1,"F2*":0,"T3":1,"Q5":1,"R1":1,"C6":0},"difficulty":3,"preference":"both","time_spent_ms":12345,"notes":"smoke","github_clicks":0}],"demographics":{"role":"student","exp_years":"1-3","freq_review_pr":"weekly"}}' \
  "$NEW_URL" | python3 -m json.tool

# Expected response:
# { "ok": true, "wrote": { "responses": 1, "demographics": 1 } }
```

If you don't get those two responses, do NOT redeploy the static site
yet — fix the deployment first (most common causes below).

### Common failure modes

| Symptom on `?selftest=1` | Likely cause | Fix |
|---|---|---|
| HTTP 405 + `allow: HEAD, GET` from `script.googleusercontent.com` | The deployment has been revoked or "Who has access" is **Only myself**. | Redeploy with **Anyone**. |
| `{"ok":false,"error":"Could not access the bound Sheet…"}` | The script project has lost its container Sheet binding. | In the Apps Script editor, ensure the project was opened via **Extensions → Apps Script** *from the Sheet*, not as a standalone script. |
| HTTP 200 but body is HTML asking you to sign in | Access is set to "Anyone with Google account" or "Only myself". | Change to **Anyone**. |
| HTTP 401 / `Authorization required` | Deployment access is internal-org-only on a Workspace account. | Use a personal account, or set **Who has access → Anyone within your organization** AND have raters sign in. |

---

## Step 6 — Redeploy the static site

Once the smoke-test returns `{"ok":true,"wrote":{...}}`, redeploy
whichever hosting you use (Netlify / Vercel / static):

```bash
# Netlify
netlify deploy --prod --dir=human_eval_v3

# Vercel
vercel --prod human_eval_v3

# Or just git push if you have a CI-driven deploy.
```

Then open the live URL → finish a 1-task self-test as a real rater →
verify a row appears in the spreadsheet's `responses` tab → and a
`demographics` row in the `demographics` tab.

---

## Step 7 — Backfill from the rater outbox (only if relevant)

If any participant ran the study while the webhook was broken between
2026-04-28 and now, their data is **not** in the spreadsheet. They DO
have it in their browser localStorage, recoverable via the
"Download my responses (.json)" button on the completion screen.

To collect:

1. Email affected participants (you should know who; they're not in the
   sheet but they emailed you a confirmation or you can check with them).
2. Ask them to: re-open the study URL → click "Resume" if available →
   navigate to the completion screen → click **Download my responses
   (.json)** → reply with the file attached.
3. Drop the files into `human_eval_v3/data/exported_payloads/`.
4. Run:

   ```bash
   python3 scripts/ingest_exported_payloads.py \
       --in  human_eval_v3/data/exported_payloads \
       --out human_eval_v3/data/ingested_csv
   ```

5. Then feed the resulting CSVs straight into the analyzer:

   ```bash
   python3 scripts/analyze_human_llm_agreement.py \
       --human         human_eval_v3/data/ingested_csv/responses.csv \
       --demographics  human_eval_v3/data/ingested_csv/demographics.csv \
       --feedback      human_eval_v3/data/ingested_csv/feedback.csv \
       --quality-flags human_eval_v3/data/ingested_csv/quality_flags.csv
   ```

---

## How to keep this from breaking again

- **One-time:** do not delete or rename the bound Sheet without
  redeploying the script.
- **One-time:** prefer **Manage deployments → ✏ → Deploy** for future
  changes so the URL is stable across redeploys.
- **Already done:** the rater UI now mirrors every submission to
  localStorage, so even a future webhook outage doesn't lose data.
- **Already done:** the Apps Script now has a `?selftest=1` GET that
  reports deployment health without writing test rows. Use it as a
  CI/cron healthcheck if you like.
