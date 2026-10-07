#!/usr/bin/env bash
#
# reproduce.sh — One-command reproduction of the thesis evaluation.
#
# Runs, in order:
#   1. Multi-judge 25-criterion checklist evaluation
#      (scripts/evaluate_reviews.py)
#   2. Recovery pass for malformed Gemini JSON, if any
#      (scripts/retry_failed_judges.py)
#   3. Completeness (C6) multi-judge evaluation
#      (scripts/evaluate_completeness.py)
#   4. Human ↔ LLM agreement dry-run on the synthetic sample
#      (scripts/analyze_human_llm_agreement.py --sample)
#
# Prerequisites (see README.md for detail):
#   - Python >= 3.10, virtual env activated
#   - `pip install -r requirements-eval.txt`
#   - .env with OPENAI_API_KEY and GEMINI_API_KEY
#
# Expected wall-clock: ~20–25 minutes.
# Expected cost:       ~$6 OpenAI credit + free-tier Gemini.
#
# Usage:
#   ./reproduce.sh                    # run the full pipeline
#   ./reproduce.sh --skip-checklist   # skip step 1 (useful if results/
#                                       checklist_evaluation_llm_multi.json
#                                       already exists and you only
#                                       want to (re)run C6 + agreement)
#   ./reproduce.sh --real-human path/to/chris_pilot_v2.csv
#                                     # use the real exported CSV in
#                                       step 4 instead of the synthetic
#                                       sample.

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ----- flags -----------------------------------------------------------------
SKIP_CHECKLIST=0
REAL_HUMAN=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-checklist) SKIP_CHECKLIST=1; shift ;;
    --real-human)     REAL_HUMAN="$2"; shift 2 ;;
    -h|--help)
      grep '^#' "$0" | sed -e 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown flag: $1" >&2; exit 2 ;;
  esac
done

# ----- env -------------------------------------------------------------------
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
  echo "[env] Loaded .env"
else
  echo "[env] WARNING: no .env found; relying on shell environment"
fi

missing=0
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "[env] ERROR: OPENAI_API_KEY is not set" >&2
  missing=1
fi
if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo "[env] ERROR: GEMINI_API_KEY is not set" >&2
  missing=1
fi
if [[ "$missing" -eq 1 ]]; then
  echo "[env] Copy .env.example to .env and fill in both keys, then re-run." >&2
  exit 1
fi

# ----- deps ------------------------------------------------------------------
python3 -c "import openai" 2>/dev/null || {
  echo "[deps] 'openai' not installed. Run:" >&2
  echo "       pip install -r requirements-eval.txt" >&2
  exit 1
}

mkdir -p results

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
step() { printf "\n========== [%s] %s ==========\n" "$(ts)" "$1"; }

# ----- 1. multi-judge 25-criterion evaluation -------------------------------
if [[ "$SKIP_CHECKLIST" -eq 0 ]]; then
  step "Step 1/4: Multi-judge 25-criterion evaluation"
  python3 -m scripts.evaluate_reviews \
      --models "openai:gpt-4o-mini,openai:gpt-4o,gemini:gemini-2.5-flash" \
      2>&1 | tee results/checklist_evaluation_llm_multi_run.log

  # ----- 2. recovery pass for malformed Gemini JSON, if needed --------------
  step "Step 2/4: Recovery pass for malformed judge output (if any)"
  if python3 -c "
import json, sys
from pathlib import Path
p = Path('results/checklist_evaluation_llm_multi.json')
if not p.exists():
    sys.exit(0)
d = json.loads(p.read_text())
fails = sum(
    1
    for e in d.get('evaluations', [])
    for j in e.get('per_judge', [])
    if j.get('error')
)
print(f'[retry] {fails} failed judges detected', file=sys.stderr)
sys.exit(0 if fails == 0 else 2)
"; then
    echo "[retry] No failed verdicts; skipping retry pass."
  else
    python3 -m scripts.retry_failed_judges \
        2>&1 | tee results/checklist_evaluation_llm_retry.log
  fi
else
  step "Step 1-2/4: SKIPPED (--skip-checklist)"
fi

# ----- 3. completeness (C6) evaluation --------------------------------------
step "Step 3/4: Completeness (C6) multi-judge evaluation"
python3 -m scripts.evaluate_completeness \
    --models "openai:gpt-4o-mini,openai:gpt-4o,gemini:gemini-2.5-flash" \
    2>&1 | tee results/c6_completeness_llm_run.log

# ----- 4. human ↔ LLM agreement ---------------------------------------------
step "Step 4/4: Human ↔ LLM agreement"
if [[ -n "$REAL_HUMAN" ]]; then
  echo "[human] Using real human CSV: $REAL_HUMAN"
  python3 -m scripts.analyze_human_llm_agreement \
      --human "$REAL_HUMAN" \
      --out   results/human_llm_agreement.json
else
  echo "[human] No --real-human flag; running with synthetic sample."
  echo "[human] See results/HUMAN_STUDY_ANALYSIS_RUNBOOK.md to swap in"
  echo "[human] the real Google Sheet export when it is available."
  python3 -m scripts.analyze_human_llm_agreement \
      --sample \
      --out results/human_llm_agreement.json
fi

step "Done."
cat <<EOF

Primary outputs:
  results/checklist_evaluation_llm_multi.json      (raw per-judge verdicts)
  results/checklist_evaluation_llm.json            (majority-vote aggregate)
  results/CHECKLIST_EVALUATION_REPORT.md           (human-readable report)
  results/c6_completeness_llm.json                 (C6 scores)
  results/human_llm_agreement.json                 (human ↔ LLM Cohen's κ)

Narrative documents (paste-ready):
  results/METHODOLOGY_AND_FINDINGS.md
  results/DISCUSSION.md
  results/THREATS_TO_VALIDITY.md

Manifest:
  results/DATA_MANIFEST.md
EOF
