# Inter-annotator agreement on `kg_relevant` tag

**Annotator A (this thesis):** rubric author / in-code `kg_relevant` flag.  
**Annotator B (independent re-annotation):** `openai:gpt-4o`, blind to A's labels, prompted with a content-derived rule.

**Raw agreement:** 21/25 = 84.0%  
**Cohen's κ:** **0.615** (substantial; Landis & Koch 1977)

## Per-criterion comparison

| ID | Category | A (ours) | B (independent) | Agree |
|---|---|:---:|:---:|:---:|
| F1 | Functionality | 0 | 0 | ✓ |
| F2 | Functionality | 0 | 0 | ✓ |
| F3 | Functionality | 1 | 1 | ✓ |
| F4 | Functionality | 1 | 1 | ✓ |
| T1 | Tests | 1 | 0 | ✗ |
| T2 | Tests | 1 | 0 | ✗ |
| T3 | Tests | 1 | 1 | ✓ |
| R1 | Readability | 0 | 0 | ✓ |
| R2 | Readability | 0 | 0 | ✓ |
| R3 | Readability | 0 | 0 | ✓ |
| M1 | Maintainability | 1 | 1 | ✓ |
| M2 | Maintainability | 0 | 0 | ✓ |
| M3 | Maintainability | 1 | 0 | ✗ |
| C1 | Consistency | 0 | 0 | ✓ |
| C2 | Consistency | 1 | 1 | ✓ |
| P1 | Performance | 0 | 0 | ✓ |
| P2 | Performance | 0 | 0 | ✓ |
| S1 | Security | 0 | 0 | ✓ |
| S2 | Security | 0 | 0 | ✓ |
| S3 | Security | 0 | 0 | ✓ |
| Q1 | Quality | 0 | 0 | ✓ |
| Q2 | Quality | 1 | 0 | ✗ |
| Q3 | Quality | 0 | 0 | ✓ |
| Q4 | Quality | 0 | 0 | ✓ |
| Q5 | Quality | 0 | 0 | ✓ |

## Interpretation

- κ = 0.615 corresponds to **substantial** agreement (Landis & Koch 1977 thresholds: 0.0 poor → 0.2 slight → 0.4 fair → 0.6 moderate → 0.8 substantial → 1.0 almost perfect).
- Treating κ ≥ 0.6 as the conventional threshold for 'substantial' agreement, the `kg_relevant` flag is reproducible by an independent annotator following a content-derived rule.
- This counters the objection that `kg_relevant` is a subjective judgement of the rubric author.
