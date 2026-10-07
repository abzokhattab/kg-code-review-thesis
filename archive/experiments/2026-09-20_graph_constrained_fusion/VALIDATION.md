# Validation record

Date: 2026-09-20

- Cost: $0
- Cases: 56 (28 dependency, 28 test)
- Budgets: 2k, 4k, 8k approximate context tokens
- Missing inputs: 0
- Budget violations: 0
- Nested-prefix packing: asserted for every case/arm
- Deterministic rerun: byte-identical `RESULTS.json`
- SHA-256:
  `3045d8b3f29499e1ef52bd4d944ab1a8a9ad95aab0ccf669bf3d510b7848b869`

## Decision

**NO-GO** for paid generation.

At 4k tokens the graph-constrained semantic policy:

- improves dependency hit-any from 25/28 to 27/28;
- improves MRR from 0.700 to 0.836;
- improves oracle-path fraction from 53.8% to 62.3%;
- attaches code snippets to every selected oracle path;
- but lowers macro oracle recall from 52.6% to 48.9% because source snippets
  consume budget that previously carried additional compact graph paths.

The predeclared gate requires no recall loss. No paid review-generation run is
licensed for this policy.
