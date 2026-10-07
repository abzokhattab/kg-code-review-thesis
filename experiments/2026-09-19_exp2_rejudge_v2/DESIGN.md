# Experiment 2 judge correction — design and audit trail

Date: 2026-09-19  
Status: post-hoc measurement correction; review generation is frozen

## Why this exists

The original Experiment 2 judge prompt asks a three-LLM panel whether a
generated review detects a known injected defect. A deterministic audit found
obvious false negatives. For example, the `sklearn_S2_01` hybrid review
explicitly names `_least_angle.py`, a true broken dependent, but both OpenAI
judges state that the review does not identify `_least_angle.py`.

Across 168 structural review/arm cells:

- gpt-4o-mini agrees with the deterministic mention oracle on 72%;
- gpt-4o agrees on 80%;
- gemini-2.5-flash agrees on 93%.

The correction does **not** regenerate any review. It changes only how the
frozen reviews are adjudicated.

## Preservation

Original judgments remain untouched under:

`experiments/2026-07-05_injection_exp2/out/judgments/`

Corrected judgments and all derived outputs go under this dated folder.

## Scope

Rejudge all existing reviews for all eight available arms:

- headline: `baseline`, `kg`, `rag`, `hybrid`, `kg_idealised`,
  `kg_joern_inherit`;
- feature ablations: `kg_deps_only`, `kg_edges_only`.

The same three models are retained for comparability:

- `openai:gpt-4o-mini`
- `openai:gpt-4o`
- `gemini:gemini-2.5-flash`

Majority of three remains the cell verdict.

## Two-stage structural adjudication

### Stage 1 — deterministic candidate matching

For each structural injection, case-sensitive exact repository-relative path
or exact basename matching identifies which **true broken dependents are
actually mentioned in the review**. Stems, substrings, symbols, and inferred
paths are rejected. Match offsets, matched text, and a surrounding excerpt are
stored. Basename collisions are flagged for sensitivity analysis.

If none is mentioned, the verdict is deterministically `false`; no model call
is needed because the pre-registered criterion requires at least one specific
dependent.

### Stage 2 — concise causal-link adjudication

When one or more true broken dependents are mentioned, the judge receives:

1. the injected change;
2. only the true broken files already found in the review;
3. the frozen review text.

It decides only whether the review links at least one matched file/usage to
the injected change as broken or requiring an update. One file is enough.
Hedging words such as “may” or “potential” do not invalidate an otherwise
specific causal warning.

The initial v2 implementation requested verbatim quotes. Models often copied
the correct text with trivial punctuation/Markdown changes, causing transport
failures rather than scientific disagreements. Those partial files are
preserved under `judgments/`.

The governing v3 protocol assigns IDs to every non-empty review line and asks
judges to select existing passages instead of reproducing text. Corrected v3
files are written separately under `judgments_v3/`.

Strict v3 output schema:

```json
{
  "schema_version": "exp2-adjudication-v3",
  "detected": true,
  "evidence_id": "M001",
  "finding_passage_id": "P004",
  "causal_passage_id": "P007",
  "reason_code": "specific_cross_file_link"
}
```

For `detected=true`, the harness verifies that:

- `evidence_id` resolves to one deterministic candidate;
- `finding_passage_id` is the deterministic passage containing that exact
  mention; and
- `causal_passage_id` is another supplied review passage (or the same one).

The harness accepts bare JSON or one exact `````json ... ````` transport
wrapper, recording which form was used. It rejects prose wrapping, arbitrary
JSON salvage, extra/missing keys, non-boolean verdicts, unknown passage or
evidence IDs, and wrong reason codes. Unsupported outputs are retried and are
never silently accepted.

`evidence_id` is redundant with `finding_passage_id`. If a model selects a
valid candidate ID but a different supplied finding passage, the harness
deterministically normalizes the ID to the candidate actually present in that
passage and records both the model ID and the normalization flag. It never
changes the selected passage or the semantic verdict.

## Local-defect adjudication

Local controls have no dependent file. The judge receives the exact mutation
and frozen review and decides whether the review explains why the new logic is
wrong—not merely that it changed or should be tested. A positive verdict must
include an exact supporting quote.

One source-manifest defect is corrected only in this adjudication layer:
`grafana_L2_02` changes `===` to the invalid sequence `=!=`. Its original
description says “null-guard inverted,” but the actual injected defect is a
syntax error. Results retain the original manifest and record the corrected
target; local-control sensitivity must also report the panel with that cell
excluded.

## Interpretation

This is a transparent post-hoc correction prompted by a documented
measurement failure. Both original and corrected panels must be reported.
The corrected panel cannot be called pre-registered.

The deterministic mention count remains a sensitivity analysis, not the sole
primary score: mentioning a true filename without connecting it to the defect
does not automatically count as detection.

Every corrected cell records the model alias, execution timestamp, prompt and
system hashes, schema hash, manifest hash, review hash, and deterministic
candidate list. The providers' exact model snapshot remains unavailable because
the original wrapper records aliases only; this limitation is reported.

## Reproduction

```bash
# No API calls; validates prompts and estimates cost.
python scripts/rejudge_exp2_detection.py --selftest
python scripts/rejudge_exp2_detection.py --dry-run

# Paid run only after the pre-flight summary is approved.
source load_env.sh
python scripts/rejudge_exp2_detection.py --workers 8
```

The harness is parallel and idempotent. Each
`(injection, arm, judge)` verdict has its own JSON file.
