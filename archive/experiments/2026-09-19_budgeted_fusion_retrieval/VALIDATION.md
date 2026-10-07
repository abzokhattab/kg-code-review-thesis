# Validation record

Date: 2026-09-19

## Final decision artefact

`RESULTS_FINAL.{md,json}` is the governing output. Earlier `RESULTS`,
`RESULTS_COMPACT`, and `RESULTS_VALIDITY` files preserve the transparent
development/validity-review history but do not govern the paid-run decision.

## Checks

- API/model calls: none
- Final records: 1,512 (56 cases × 9 arms × 3 budgets)
- Missing RAG/index inputs: 0
- Budget violations: 0
- Empty oracle sets: 0
- Noncanonical selected paths: 0
- Budget nesting: asserted for every case and arm (`2k ⊆ 4k ⊆ 8k`)
- Linter diagnostics on driver: 0
- Idempotence: existing result stems are not overwritten without `--force`
- Determinism: a fresh `RESULTS_FINAL_RERUN` produced byte-equivalent
  `records`, `summary`, `gate`, `unavailable`, and `input_fingerprints` data
  after excluding the intentionally different result-stem metadata

## Outcome

**NO-GO** for paid generation.

At the 4,000-token budget, deployed RRF:

- lost zero cases hit by deployed graph retrieval;
- improved dependency hit-any to 27/28 from 25/28 for deployed graph and
  25/28 for deployed naive fusion;
- admitted a semantic-only file in 75.0% of dependency cases, below the fixed
  90% requirement;
- Pareto-dominated deployed naive fusion in both cohorts after overlapping
  graph/RAG paths were rendered once using compact graph evidence.

No generation or judging spend is licensed by this gate.
