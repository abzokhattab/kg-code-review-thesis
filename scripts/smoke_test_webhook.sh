#!/usr/bin/env bash
# Smoke-test an Apps Script /exec webhook for the human-evaluation study.
#
# Confirms three things:
#   1. The deployment is live (selftest GET returns ok=true)
#   2. The bound Sheet is reachable from the script
#   3. A real POST writes a row and returns wrote.responses >= 1
#
# Usage:
#   bash scripts/smoke_test_webhook.sh "REDACTED_WEBHOOK_URL"
#
# Exits 0 on success, non-zero on first failure.

set -euo pipefail

URL="${1:-}"
if [ -z "${URL}" ]; then
    echo "usage: $0 <web-app-/exec-URL>" >&2
    exit 64
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 required (for JSON validation)" >&2
    exit 65
fi

red()    { printf '\033[31m%s\033[0m\n' "$*"; }
green()  { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }

echo "==> Webhook URL: ${URL}"
echo

# ─── 1. selftest GET ────────────────────────────────────────────────────
echo "==> 1/3 GET ?selftest=1 (deployment + Sheet reachability)"
SELFTEST_RAW="$(curl -sS -L "${URL}?selftest=1" || true)"
SELFTEST_PRETTY="$(printf '%s' "${SELFTEST_RAW}" | python3 -m json.tool 2>/dev/null || true)"

if [ -z "${SELFTEST_PRETTY}" ]; then
    red "FAIL: selftest did not return parseable JSON."
    echo "Raw response (first 400 chars):"
    printf '%s' "${SELFTEST_RAW}" | head -c 400
    echo
    yellow "Common causes: deployment revoked (HTTP 405), 'Who has access' is 'Only myself', or Sheet was deleted."
    yellow "See human_eval_v3/docs/REDEPLOY_WEBHOOK.md."
    exit 1
fi

OK_VAL="$(printf '%s' "${SELFTEST_PRETTY}" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("yes" if d.get("ok") else "no")')"
if [ "${OK_VAL}" != "yes" ]; then
    red "FAIL: selftest returned ok=false."
    echo "${SELFTEST_PRETTY}"
    exit 2
fi
green "OK  selftest passed:"
echo "${SELFTEST_PRETTY}" | sed 's/^/    /'
echo

# ─── 2. POST a real ratings row ─────────────────────────────────────────
TS="$(date -u +%FT%TZ)"
RATER="selftest_$(date +%s)"
echo "==> 2/3 POST a test ratings row (rater_id=${RATER})"
POST_RAW="$(curl -sS -L -X POST -H "Content-Type: application/json" \
    -d "{\"study_id\":\"selftest\",\"rater_id\":\"${RATER}\",\"completed_at\":\"${TS}\",\"ratings\":[{\"pr_id\":1,\"comparison\":\"bl_vs_kg\",\"blind_label\":\"A\",\"mode\":\"baseline\",\"scores\":{\"F3*\":1,\"F2*\":0,\"T3\":1,\"Q5\":1,\"R1\":1,\"C6\":0},\"difficulty\":3,\"preference\":\"both\",\"time_spent_ms\":12345,\"notes\":\"smoke\",\"github_clicks\":0}],\"demographics\":{\"role\":\"student\",\"exp_years\":\"1-3\",\"freq_review_pr\":\"weekly\"}}" \
    "${URL}" || true)"
POST_PRETTY="$(printf '%s' "${POST_RAW}" | python3 -m json.tool 2>/dev/null || true)"

if [ -z "${POST_PRETTY}" ]; then
    red "FAIL: POST did not return parseable JSON."
    echo "Raw response (first 400 chars):"
    printf '%s' "${POST_RAW}" | head -c 400
    echo
    exit 3
fi

WROTE_OK="$(printf '%s' "${POST_PRETTY}" | python3 -c '
import json, sys
d = json.load(sys.stdin)
ok = d.get("ok") and (d.get("wrote") or {}).get("responses", 0) >= 1
print("yes" if ok else "no")
')"
if [ "${WROTE_OK}" != "yes" ]; then
    red "FAIL: POST did not report wrote.responses >= 1."
    echo "${POST_PRETTY}"
    exit 4
fi
green "OK  POST written:"
echo "${POST_PRETTY}" | sed 's/^/    /'
echo

# ─── 3. Reminder ────────────────────────────────────────────────────────
echo "==> 3/3 Manual verification step:"
yellow "    Open the bound spreadsheet and confirm:"
yellow "      • a 'responses' row exists for rater_id='${RATER}'"
yellow "      • a 'demographics' row exists for the same rater_id"
echo

green "ALL CHECKS PASSED — webhook is healthy. Update SHEET_URL in:"
echo "    human_eval/index.html"
echo "    human_eval_v2/index.html"
echo "    human_eval_v3/index.html"
echo "and redeploy the static site."
