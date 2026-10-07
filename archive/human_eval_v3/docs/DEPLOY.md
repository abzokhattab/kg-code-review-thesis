# Deploying v2 alongside v1

The v2 study lives in `human_eval_v2/`. v1 lives in `human_eval/`. They
are completely independent: separate `index.html`, separate
`study_data.json`, separate localStorage namespace, separate `study_id`
on every webhook payload.

You can deploy v2 in any of three ways. Pick the one that matches your
infrastructure. Configs (`netlify.toml`, `vercel.json`) are already
checked in next to `index.html`, so the deploy command is one line.

---

## 0. Local smoke test (always do this first)

```bash
# from repo root
python3 human_eval_v2/scripts/build_study_data_v2.py --final
python3 human_eval_v2/scripts/smoke_test.py
# expected: ALL CHECKS PASSED — v2 is ready to deploy.
```

For a manual visual check:

```bash
python3 -m http.server 8765 --directory human_eval_v2
# then open http://localhost:8765/index.html
```

The welcome page should show a purple "v2 · clean stimuli" badge.

A passing smoke test was recorded on 2026-04-29 by an automated browser
walkthrough: page title, badge, consent flow, demographics, briefing,
first-trial diff & reviews, no truncation marker, no "Code Owners"
leak, no stray fences, `localStorage` key starts with `heval3_v2_`.

If you change `study_data.json` or `index.html`, re-run the smoke test
before re-deploying.

---

## 1. Netlify (matches the v1 deployment)

v1 was deployed at Netlify (see `human_eval/.netlify/state.json`,
site id `ff6f501f-…`). Deploy v2 as a **separate Netlify site** so v1
stays online during the transition.

### One-time setup

```bash
# install the CLI globally (one-time)
npm install -g netlify-cli

# log in (opens browser, one-time per machine)
netlify login
```

### Deploy v2

```bash
cd human_eval_v2
netlify init                      # pick "Create & configure a new site"
                                  # site name: luca-human-eval-v2 (or your choice)
                                  # build command: leave empty
                                  # publish directory: .
netlify deploy --prod             # publishes ./ as the site root
```

After deployment you'll have two URLs:

| Study | URL |
|-------|-----|
| v1 | (your existing v1 Netlify URL — site id `ff6f501f-5ea0-4453-bc80-ad1a7376ce47`) |
| v2 | (new v2 Netlify URL, e.g. `https://luca-human-eval-v2.netlify.app`) |

Both write to the same Google Apps Script webhook
(`SHEET_URL` is identical), but every v2 row carries
`study_id: "human_eval_v2"`, so the spreadsheet pivots cleanly by
study version.

### Re-deploy after a change

```bash
cd human_eval_v2
python3 ../human_eval_v2/scripts/build_study_data_v2.py --final
python3 ../human_eval_v2/scripts/smoke_test.py && netlify deploy --prod
```

The smoke test acts as a deploy gate — if it fails, the deploy is
skipped.

## 2. Vercel (alternative — also matches v1)

v1 was also deployed to Vercel (see `human_eval/.vercel/project.json`,
project `human_eval`). Same pattern: deploy v2 as a separate Vercel
project.

### One-time setup

```bash
npm install -g vercel
vercel login                      # opens browser, one-time
```

### Deploy v2

```bash
cd human_eval_v2
vercel --prod                     # accept defaults; project name e.g. luca-human-eval-v2
```

## 3. Plain static host (S3, GitHub Pages, etc.)

The deployable surface is just three files:

- `index.html` (rater UI)
- `study_data.json` (stimuli)
- the icon dependencies in your CDN (none — this UI is self-contained)

Upload `index.html` and `study_data.json` to any web root that serves
static files. The fetch path in the HTML is relative
(`fetch("study_data.json")`) so this works under any prefix.

For Cloudflare Pages, Render, or a plain S3 bucket, the same applies
— upload the two files together, no build step.

---

## 4. Backend (Google Apps Script) — required configuration

The Apps Script `apps_script_webhook.gs` currently writes every
incoming row into a single sheet, indexed by `rater_id`. To keep v1
and v2 ratings separate without losing v1 data, do **one** of the
following.

### 4a. Filter on `study_id` in your analysis (recommended, no code change)

Every v2 row arrives with `study_id: "human_eval_v2"`. v1 rows have no
`study_id` field (they predate it). Your analysis SQL/Pandas can
filter on this column trivially:

```python
df_v1 = df[df.study_id.isna() | (df.study_id == "")]
df_v2 = df[df.study_id == "human_eval_v2"]
```

This requires no backend change. It is the recommended approach.

### 4b. Route to a separate sheet tab (one-line code change)

If you prefer separate sheet tabs, add this near the top of the
`doPost` handler in `apps_script_webhook.gs`:

```javascript
var sheetName = (data.study_id === "human_eval_v2") ? "Ratings_v2" : "Ratings_v1";
var sheet = ss.getSheetByName(sheetName) || ss.insertSheet(sheetName);
```

Then re-deploy the Apps Script. The webhook URL stays the same.

---

## 5. Pool management

- **Do not pool v1 and v2 ratings** for the κ computation. They are
  different stimulus sets (different PR list, different review
  cleanup) — they constitute different studies.
- **You may compare them descriptively** in the writeup as a
  robustness check ("the v1 finding holds / changes under v2's
  cleaner stimuli").
- **You may reuse v1 raters for v2** (re-invitation is fine), but the
  v2-namespaced localStorage key means even the same browser will
  not auto-resume v1 progress.

---

## 6. Pre-deployment checklist

Before sending v2 to a real cohort, all of these must be true. Tick
them off:

- [x] `python3 human_eval_v2/scripts/build_study_data_v2.py --final`
      writes the final selection
- [x] `python3 human_eval_v2/scripts/smoke_test.py` exits with code 0
- [x] `python3 human_eval_v2/scripts/deep_audit.py` returns 0 PROBLEMS
      (warnings about KG hallucinations, length disparity, binary
      markers are expected and documented)
- [x] Browser smoke test passed (welcome badge, consent, demographics,
      first-trial diff & reviews render, no truncation marker, no
      Code Owners leak, no stray fences, no Traceability section)
- [x] `human_eval_v2/docs/SELECTION_v2.md` §5 (ground-truth issues)
      is filled in for all 6 PRs from real GitHub conversations
- [x] `human_eval_v2/docs/ANALYSIS_PLAN.md` is finalised and locked
- [x] `human_eval_v2/data/pr_body_overrides.json` exists (recovered
      bodies for PR 1, 3, 14, 17, 19; PR 12 is a 60-char backport)
- [ ] **Deploy:** `cd human_eval_v2 && netlify deploy --prod`
      (or vercel `--prod`, or upload to a static host)
- [ ] Apps Script webhook is either confirmed to keep `study_id` in
      its output (4a) or routed to a separate tab (4b)
- [ ] v1 site is still up (so the comparison data remains accessible)
- [ ] You have a backup of `human_eval/study_data.json` somewhere
      separate from the working tree
- [ ] Cohort recruited; do **not** pool ratings with v1
