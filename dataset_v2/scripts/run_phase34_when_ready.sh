#!/usr/bin/env bash
# Wait for the v2 multi-judge panel JSON to appear, then auto-run:
#   1. bootstrap CIs + paired permutation tests on v2
#   2. v1 vs v2 side-by-side comparison
#
# Tailored for the May 5 2026 v2 rebuild. Idempotent: re-running this
# script after success simply re-computes the comparison docs.
#
# Usage:
#   bash dataset_v2/scripts/run_phase34_when_ready.sh
#
set -euo pipefail
cd "$(dirname "$0")/../.."

V2_PANEL_JSON=results/checklist_evaluation_llm_multi__v2.json
V2_PANEL_RAW=results/checklist_evaluation_llm_multi__v2.raw.json
V1_PANEL_JSON=results/checklist_evaluation_llm_multi.json

echo "==> Waiting for v2 panel JSON to appear: ${V2_PANEL_JSON}"
WAITED=0
TIMEOUT=$((90 * 60))   # 90 min hard cap
while [ ! -f "${V2_PANEL_JSON}" ]; do
    sleep 30
    WAITED=$((WAITED + 30))
    if [ ${WAITED} -ge ${TIMEOUT} ]; then
        echo "ERROR: timeout (${TIMEOUT}s) waiting for ${V2_PANEL_JSON}." >&2
        if [ -f "${V2_PANEL_RAW}" ]; then
            echo "  Raw verdicts present at ${V2_PANEL_RAW} — investigate manually." >&2
        fi
        exit 1
    fi
done
echo "==> Panel JSON found after ${WAITED}s."

echo "==> Running bootstrap CIs + paired permutation tests on v2..."
python3 scripts/bootstrap_stats.py \
    --in  "${V2_PANEL_JSON}" \
    --out-json results/BOOTSTRAP_STATS_v2.json \
    --out-md   results/BOOTSTRAP_STATS_v2.md \
    --label    "v2 (18 PRs, cleaned dataset)"

echo "==> Running v1 vs v2 side-by-side comparison..."
python3 dataset_v2/scripts/compare_v1_v2.py \
    --v1 "${V1_PANEL_JSON}" \
    --v2 "${V2_PANEL_JSON}" \
    --out-md   results/V1_VS_V2_COMPARISON.md \
    --out-json results/V1_VS_V2_COMPARISON.json

echo "==> All phase 3+4 outputs written:"
ls -la results/V1_VS_V2_COMPARISON.* results/BOOTSTRAP_STATS_v2.* "${V2_PANEL_JSON}"
echo "==> Done."
