/**
 * Google Apps Script webhook for the human-evaluation studies.
 *
 * SOURCE OF TRUTH for the Apps Script the study UIs POST to. The deployed
 * /exec URL is embedded in each study's index.html as SHEET_URL.
 *
 * v2 (2026-07-13) — rewritten for the v4 Python-PR study
 * (experiments/2026-07-06_user_study_prs/pilot/; final study_id
 * "human_eval_v4_python_20260808"). Changes vs v1:
 *
 *   1. EVERY POST is appended verbatim to a 'raw_log' tab BEFORE any
 *      schema-specific parsing. Even a malformed or unknown payload is
 *      never lost.
 *   2. Every tab now records `study_id`, `instrument_version` (the analyzer
 *      filters on both), and `raw_payload` (the verbatim JSON —
 *      analyze_responses.py ingests Sheet CSV exports by parsing JSON cells).
 *   3. Header reconciliation: if a tab already exists with an older
 *      header, missing columns are appended to row 1 and rows are written
 *      aligned by column NAME, never by position. No silent misalignment.
 *   4. LockService serialises concurrent writes (multiple raters
 *      submitting at the same time).
 *
 * SCHEMAS handled (auto-detected per POST):
 *   • per-criterion + overall (v4 study and bl_strict-vs-joern): each
 *     rating has `criteria` {F3*,F2*,T3,Q5,R1,C6 → A|B|both|neither},
 *     `criteria_net`, `overall` (A|equal|B), `why`, `difficulty`,
 *     `time_spent_ms`, `github_clicks`  → tab 'responses_criteria', along
 *     with the session-level `started_at` / `completed_at`.
 *   • 5-point preference (older v4 pilot): `preference_score` → 'responses'.
 *   • legacy v3 per-criterion 0/1 `scores` → 'responses'.
 *   • demographics — travel on every ratings POST (role, role_other,
 *     exp_years, freq_review_pr; exact key names, do not rename)
 *     → 'demographics'.
 *   • `feedback` string → 'feedback'.
 *   • `quality_flags` array → 'quality_flags'.
 *
 * ─── Deployment checklist ────────────────────────────────────────────
 *   1. Open (or create) the study spreadsheet → Extensions → Apps Script.
 *   2. Paste this entire file as Code.gs and save.
 *   3. Deploy → New deployment → "Web app".
 *      • Execute as: Me
 *      • Who has access: Anyone   (NOT "Anyone with Google account")
 *   4. Copy the /exec URL; it goes into the study UI as SHEET_URL.
 *   5. Verify health without writing rows:
 *        curl -sS -L "<URL>?selftest=1"
 *      → {"ok":true,"version":"v3-2026-08-17","spreadsheet_name":...}
 *      Bump VERSION whenever this file changes, otherwise the selftest
 *      reports a match while the deployment is stale.
 *   6. Verify an end-to-end write:
 *        curl -sS -L -X POST -d '{"study_id":"smoke","rater_id":"smoke_1",
 *          "completed_at":"2026-01-01T00:00:00Z","demographics":{"role":
 *          "student","exp_years":"1-3","freq_review_pr":"weekly"},
 *          "ratings":[{"pr_id":101,"comparison":"bl_vs_kg","mode_A":"kg",
 *          "mode_B":"baseline_strict","criteria":{"F3*":"A","F2*":"both",
 *          "T3":"B","Q5":"neither","R1":"both","C6":"A"},"criteria_net":2,
 *          "overall":"A","why":"smoke","difficulty":3,"time_spent_ms":1,
 *          "github_clicks":0}]}' "<URL>"
 *      → {"ok":true,"wrote":{"raw_log":1,"responses_criteria":1,
 *          "demographics":1}}
 *      Then check tabs raw_log / responses_criteria / demographics.
 */

const VERSION = 'v6-2026-08-24';

const SHEETS = {
  rawLog:            'raw_log',
  responses:         'responses',            // legacy schemas
  responsesCriteria: 'responses_criteria',   // current per-criterion + overall
  demographics:      'demographics',
  feedback:          'feedback',
  qualityFlags:      'quality_flags',
};

// Rater-facing criteria ids, display order. MUST match the study data's
// criteria[].id and the analyzers. Cell values: "A"|"B"|"both"|"neither".
const CRITERIA_IDS = ['F3*', 'F2*', 'T3', 'Q5', 'R1', 'C6'];

function doGet(e) {
  if (e && e.parameter && e.parameter.selftest === '1') {
    try {
      const ss = SpreadsheetApp.getActive();
      const ok = !!ss && !!ss.getId();
      // The endpoint is public, so the health check reports only that a bound
      // Sheet is reachable. It used to return the spreadsheet's id and name,
      // which told any caller where the study's data lives.
      return _json({
        ok: ok,
        version: VERSION,
        spreadsheet_bound: ok,
        deployment_alive: true,
        timestamp: new Date().toISOString(),
        hint: 'POST JSON to this same endpoint.',
      });
    } catch (err) {
      return _json({
        ok: false,
        version: VERSION,
        deployment_alive: true,
        error: 'Could not access the bound Sheet: ' + String(err),
        hint: 'Open the script via Extensions → Apps Script FROM the Sheet so it is container-bound.',
      });
    }
  }
  return _json({ok: true, version: VERSION,
                hint: 'POST JSON here. Append ?selftest=1 for deployment health.'});
}

function doOptions() {
  return ContentService.createTextOutput('').setMimeType(ContentService.MimeType.TEXT);
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  let locked = false;
  try {
    lock.waitLock(20000);   // serialise concurrent rater submissions
    locked = true;
    const raw = _rawBody(e);
    let body = {};
    try { body = JSON.parse(raw); } catch (_) { body = {}; }

    const wrote = {};

    // 0) Catch-all FIRST: the verbatim POST always lands in raw_log,
    //    even if nothing below recognises it. This is the no-data-loss
    //    guarantee.
    wrote.raw_log = _writeRawLog(body, raw);

    // 1) Per-task ratings batch (the common payload).
    if (Array.isArray(body.ratings) && body.ratings.length) {
      const n = _writeResponses(body, raw);
      wrote[n.sheet] = n.count;
      // Demographics travel on every ratings POST; persist a copy
      // (analyzer dedupes last-write-wins per rater).
      if (body.demographics && Object.keys(body.demographics).length) {
        wrote.demographics = _writeDemographics(body);
      }
    }

    // 2) Final feedback POST.
    if (typeof body.feedback === 'string' && body.feedback.trim()) {
      wrote.feedback = _writeFeedback(body);
    }

    // 3) Quality-flags POST (not emitted by the v4 UI; kept for others).
    if (Array.isArray(body.quality_flags) && body.quality_flags.length) {
      wrote.quality_flags = _writeQualityFlags(body);
    }

    return _json({ok: true, version: VERSION, wrote: wrote});
  } catch (err) {
    // Last-ditch: even on error, try to preserve the raw body.
    try { _writeRawLog({}, _rawBody(e), 'ERROR: ' + String(err)); } catch (_) {}
    return _json({ok: false, version: VERSION, error: String(err)});
  } finally {
    if (locked) lock.releaseLock();
  }
}

/* ─── Writers (all append by column NAME via _appendByName) ─────────── */

function _writeRawLog(body, raw, note) {
  _appendByName(SHEETS.rawLog,
    ['received_at', 'study_id', 'instrument_version', 'rater_id', 'kind', 'note', 'raw_payload'], {
    received_at: new Date(),
    study_id: body.study_id || '',
    instrument_version: body.instrument_version || '',
    rater_id: body.rater_id || '',
    kind: _kindOf(body),
    note: note || '',
    raw_payload: raw || '',
  });
  return 1;
}

function _kindOf(body) {
  if (Array.isArray(body.ratings) && body.ratings.length) {
    const r0 = body.ratings[0] || {};
    if (r0.criteria) return 'ratings_criteria';
    if (r0.preference_score !== undefined) return 'ratings_pref5';
    if (r0.scores) return 'ratings_v3';
    return 'ratings_unknown';
  }
  if (typeof body.feedback === 'string') return 'feedback';
  if (Array.isArray(body.quality_flags)) return 'quality_flags';
  return 'unknown';
}

function _writeResponses(body, raw) {
  const r0 = (body.ratings && body.ratings[0]) || {};
  if (r0.criteria && typeof r0.criteria === 'object') {
    return {sheet: SHEETS.responsesCriteria,
            count: _writeResponsesCriteria(body, raw)};
  }
  return {sheet: SHEETS.responses, count: _writeResponsesLegacy(body, raw)};
}

function _writeResponsesCriteria(body, raw) {
  // Current schema: per-criterion A/B/both/neither + overall + why.
  // Column names are read by the analyzers — do not rename.
  const header = ['received_at', 'study_id', 'instrument_version', 'rater_id',
                  'device_token', 'started_at', 'completed_at',
                  'pr_id', 'comparison', 'mode_A', 'mode_B']
    .concat(CRITERIA_IDS)
    .concat(['criteria_net', 'overall', 'why',
             'difficulty', 'time_spent_ms', 'github_clicks',
             'highlight_used', 'raw_payload']);
  let count = 0;
  for (const r of body.ratings) {
    const c = r.criteria || {};
    const obj = {
      received_at: new Date(),
      study_id: body.study_id || '',
      instrument_version: body.instrument_version || '',
      rater_id: body.rater_id || '',
      device_token: body.device_token || '',
      started_at: body.started_at || '',
      completed_at: body.completed_at || '',
      pr_id: r.pr_id !== undefined ? r.pr_id : '',
      comparison: r.comparison || '',
      mode_A: r.mode_A || '',
      mode_B: r.mode_B || '',
      criteria_net: r.criteria_net !== undefined ? r.criteria_net : '',
      overall: r.overall || '',
      why: r.why || '',
      difficulty: r.difficulty !== undefined ? r.difficulty : '',
      time_spent_ms: r.time_spent_ms !== undefined ? r.time_spent_ms : '',
      github_clicks: r.github_clicks !== undefined ? r.github_clicks : 0,
      highlight_used: r.highlight_used === true,
      raw_payload: raw || '',
    };
    for (const cid of CRITERIA_IDS) obj[cid] = c[cid] || '';
    _appendByName(SHEETS.responsesCriteria, header, obj);
    count++;
  }
  return count;
}

function _writeResponsesLegacy(body, raw) {
  // Older 5-point-preference and v3 0/1-scores schemas, kept so the old
  // study URLs continue to work against the same deployment.
  const header = ['received_at', 'study_id', 'instrument_version', 'rater_id', 'completed_at',
                  'pr_id', 'comparison', 'blind_label', 'mode',
                  'mode_A', 'mode_B', 'preference_score']
    .concat(CRITERIA_IDS)
    .concat(['difficulty', 'preference', 'why', 'time_spent_ms',
             'notes', 'github_clicks', 'raw_payload']);
  let count = 0;
  for (const r of body.ratings) {
    const sc = r.scores || {};
    const obj = {
      received_at: new Date(),
      study_id: body.study_id || '',
      instrument_version: body.instrument_version || '',
      rater_id: body.rater_id || '',
      completed_at: body.completed_at || '',
      pr_id: r.pr_id !== undefined ? r.pr_id : '',
      comparison: r.comparison || '',
      blind_label: r.blind_label || '',
      mode: r.mode || '',
      mode_A: r.mode_A || '',
      mode_B: r.mode_B || '',
      preference_score: r.preference_score !== undefined ? r.preference_score : '',
      difficulty: r.difficulty !== undefined ? r.difficulty : '',
      preference: r.preference || '',
      why: r.why || '',
      time_spent_ms: r.time_spent_ms !== undefined ? r.time_spent_ms : '',
      notes: r.notes || '',
      github_clicks: r.github_clicks !== undefined ? r.github_clicks : 0,
      raw_payload: raw || '',
    };
    for (const cid of CRITERIA_IDS) obj[cid] = _zeroOne(sc[cid]);
    _appendByName(SHEETS.responses, header, obj);
    count++;
  }
  return count;
}

function _writeDemographics(body) {
  // Exact field names — the analyzers read them by name.
  const d = body.demographics || {};
  _appendByName(SHEETS.demographics,
    ['received_at', 'study_id', 'instrument_version', 'rater_id', 'device_token', 'role', 'role_other',
     'exp_years', 'freq_review_pr', 'completed_at'], {
    received_at: new Date(),
    study_id: body.study_id || '',
    instrument_version: body.instrument_version || '',
    rater_id: body.rater_id || '',
    device_token: body.device_token || '',
    role: d.role || '',
    role_other: d.role_other || '',   // free text when role === 'other'
    exp_years: d.exp_years || '',
    freq_review_pr: d.freq_review_pr || '',
    completed_at: body.completed_at || '',
  });
  return 1;
}

function _writeFeedback(body) {
  _appendByName(SHEETS.feedback,
    ['received_at', 'study_id', 'instrument_version', 'rater_id', 'feedback', 'completed_at'], {
    received_at: new Date(),
    study_id: body.study_id || '',
    instrument_version: body.instrument_version || '',
    rater_id: body.rater_id || '',
    feedback: body.feedback || '',
    completed_at: body.completed_at || '',
  });
  return 1;
}

function _writeQualityFlags(body) {
  _appendByName(SHEETS.qualityFlags,
    ['received_at', 'study_id', 'instrument_version', 'rater_id', 'quality_flags', 'completed_at'], {
    received_at: new Date(),
    study_id: body.study_id || '',
    instrument_version: body.instrument_version || '',
    rater_id: body.rater_id || '',
    quality_flags: JSON.stringify(body.quality_flags || []),
    completed_at: body.completed_at || '',
  });
  return 1;
}

/* ─── Helpers ─────────────────────────────────────────────────────── */

/**
 * Append one row to `name`, aligning values by column NAME.
 * - Creates the sheet with `header` if missing.
 * - If the sheet exists with an older header, appends any missing
 *   expected columns to row 1 (never reorders existing ones), so old
 *   rows keep their meaning and new rows are always aligned.
 */
function _appendByName(name, header, obj) {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    sh.appendRow(header);
    sh.setFrozenRows(1);
  }
  const lastCol = Math.max(sh.getLastColumn(), 1);
  let cols = sh.getRange(1, 1, 1, lastCol).getValues()[0]
               .map(function (v) { return String(v); });
  // Reconcile: add any expected column the sheet doesn't have yet.
  const missing = header.filter(function (h) { return cols.indexOf(h) === -1; });
  if (missing.length) {
    sh.getRange(1, cols.length + 1, 1, missing.length).setValues([missing]);
    cols = cols.concat(missing);
  }
  const row = cols.map(function (c) {
    return obj.hasOwnProperty(c) ? obj[c] : '';
  });
  // appendRow() runs every value through the same parser as typed input, which
  // silently rewrites data: the demographics answer "3-5" was stored as the
  // date 2026-03-05 (serial 46086), and "1-3" and "5-10" would go the same way.
  // Preformatting string cells as plain text ("@") stops that; numbers keep
  // General so they stay numeric.
  const r = sh.getLastRow() + 1;
  const range = sh.getRange(r, 1, 1, row.length);
  range.setNumberFormats([row.map(function (v) {
    return (typeof v === 'string' && v !== '') ? '@' : 'General';
  })]);

  // The number format does NOT stop formula parsing: setValues() treats any
  // string starting with "=" as a formula whatever the cell format, which
  // turned a probe `why` of "=1+1 ..." into #ERROR! under v4. Such cells are
  // therefore written as rich text, which sets characters and never parses
  // them. Leading "+", "-", "@" and "'" get the same treatment: "-" is
  // realistic in free text ("- Review A named the file"), and a leading
  // apostrophe would otherwise be eaten as a text marker.
  const RISKY = /^[=+\-@']/;
  const risky = function (v) { return typeof v === 'string' && v !== '' && RISKY.test(v); };

  range.setValues([row.map(function (v) { return risky(v) ? '' : v; })]);
  row.forEach(function (v, i) {
    if (risky(v)) {
      sh.getRange(r, i + 1).setRichTextValue(
        SpreadsheetApp.newRichTextValue().setText(v).build());
    }
  });
}

function _rawBody(e) {
  if (e && e.postData && e.postData.contents) return e.postData.contents;
  if (e && e.parameter && e.parameter.payload) return e.parameter.payload;
  return '';
}

function _json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function _zeroOne(v) {
  if (v === 0 || v === 1) return v;
  if (v === '0' || v === '1') return Number(v);
  if (v === true) return 1;
  if (v === false) return 0;
  return '';
}
