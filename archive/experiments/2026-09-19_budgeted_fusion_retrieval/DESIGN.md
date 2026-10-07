# Zero-cost gate: budgeted graph + semantic retrieval

Date: 2026-09-19  
Status: exploratory development gate; not a confirmatory thesis result

## Question

Before purchasing another generation run, can a deterministic fusion policy
preserve at least one known cross-file dependent or broken test under a fixed
context budget while also admitting semantic repository context?

This is an **information-availability** check. It does not test whether an LLM
uses the evidence correctly.

## Inputs

All inputs already exist; this experiment makes no API or model calls.

1. `experiments/2026-07-05_injection_exp2/out/manifest.json`
   - 28 structural injections (`S1`--`S5`)
   - exact-path oracle: `true_dependents`
2. `experiments/2026-09-06_test_oracle/out/manifest.json`
   - 28 Grafana test injections
   - exact-path oracle: `true_test_dependents`
3. Clean source scopes, Joern edges, and saved RAG indices under
   `experiments/2026-07-05_injection_exp2/out/`
4. Existing language resolvers in
   `experiments/2026-07-05_injection_exp2/harness/analyzers.py`

## Retrieval arms

| Arm | Candidate source and order |
|---|---|
| `deployed_graph` | Existing Joern callers plus lexical dependent-file search; for the test cohort, the deployed filename-convention test finder |
| `resolved_graph` | **Manifest-resolver ceiling:** union of existing import/call/inheritance resolvers, reconstructed from clean source; not an independent arm |
| `rag_proxy` | Cosine ranking over saved `text-embedding-3-small` chunk vectors, using the changed file's first indexed chunk vector as the zero-cost query |
| `deployed_naive` | `deployed_graph` followed by `rag_proxy`, de-duplicated by exact path |
| `deployed_rrf` | Reciprocal-rank fusion of `deployed_graph` and `rag_proxy` |
| `resolved_naive` | `resolved_graph` followed by `rag_proxy`, de-duplicated by exact path |
| `resolved_rrf` | Reciprocal-rank fusion of `resolved_graph` and `rag_proxy` |
| `deployed_compact` | Compact deployed graph evidence followed only by semantic files absent from that graph |
| `resolved_compact` | Compact resolved graph evidence followed only by semantic files absent from that graph |

RRF uses the fixed, untuned constant \(k=60\). Ties prefer a graph-supported
candidate and then exact path order.

## Context budgets

Evaluate each arm at 2,000, 4,000, and 8,000 approximate context tokens.
Token count is the repository's existing deterministic approximation:
`ceil(characters / 4)`. This budget applies only to retrieved context, not to
the PR title, description, diff, or system prompt.

Evidence units match the current prompting asymmetry:

- graph evidence is a compact path plus relation/evidence lines;
- semantic evidence includes path, line range, similarity, and at most 800
  characters of source.

## Outcomes

Primary:

- **hit-any**: at least one exact oracle path is present in the packed context.

Secondary:

- exact-path oracle recall;
- exact-path precision among selected files;
- first relevant rank before packing;
- approximate tokens used and files selected;
- whether packed context contains both graph and semantic evidence;
- count of semantic-only files admitted.

Results are reported separately for dependency and test cohorts and pooled.

## Go/no-go rule for a later paid generation experiment

At the 4,000-token budget, the independently usable `deployed_rrf` must:

1. lose zero per-case hits relative to `deployed_graph` in each cohort;
2. satisfy the context budget for every case;
3. include at least one semantic-only file in at least 90% of cases; and
4. achieve no lower hit-any than `deployed_naive`; and
5. Pareto-dominate `deployed_naive` on cohort hit-any, macro target recall,
   and semantic-only-case rate, with at least one strict improvement.

Failure means the fusion policy is revised or abandoned before model calls.
Passing only licenses a pre-registration and held-out generation study; it is
not evidence that review quality improved.

## Transparent development amendment after the first gate

The first run (`RESULTS.{md,json}`) evaluated `resolved_rrf` and returned
**NO-GO**. At 4,000 tokens it preserved hit-any but reduced dependency-target
recall from 93.5% for compact resolved graph evidence to 72.1%, performed the
same as naive concatenation, and admitted a semantic-only file in 64.3% of
dependency cases.

Inspection showed the mechanism: when graph and semantic retrieval selected the
same file, v1 merged the full semantic preview into the compact graph item,
spending the shared budget twice on one path. After observing that result, the
`*_compact` policies were added as an explicitly post-hoc development revision.
They keep graph-supported paths compact and use remaining budget only for
non-overlapping semantic files. Their results are written separately to
`RESULTS_COMPACT.{md,json}` and must not be described as pre-registered.

The compact result remains a post-hoc packing diagnostic. It cannot license a
paid run because it depends on the manifest-resolver ceiling.

## Validity-review amendment

An independent methods review identified that a go/no-go rule based on the
manifest resolver is circular. The script was therefore hardened before making
any paid decision:

- retrieval receives only `id`, `repo`, `language`, `edit_file`, and `symbol`;
  oracle paths, evidence, fanout, band, edge type, and ground-truth prose remain
  evaluation-only;
- the manifest-resolver ceiling unions all relation families instead of using
  the oracle band to choose the correct one;
- deployed graph candidates are sorted by a frozen source/path key before
  budget packing;
- paths are exact canonical repository-relative paths;
- packing uses the longest fitting prefix and asserts nested 2k ⊆ 4k ⊆ 8k
  selections;
- the reported “precision” label is corrected to **oracle-path fraction**,
  because the oracle is not an exhaustive relevance set;
- dependency and test cohorts govern separately; pooled output is descriptive;
- the final gate uses `deployed_rrf` versus `deployed_graph` and
  `deployed_naive`, including the Pareto rule above.

The initial validity-review decision was written to
`RESULTS_VALIDITY.{md,json}`. A final conformance pass then suppressed duplicate
semantic previews when graph and RAG selected the same path, counted the exact
whole serialized context, validated index dimensions/IDs, processed one index
at a time, and failed on partial output state. The governing decision is
`RESULTS_FINAL.{md,json}`.

The saved first-chunk embedding is retained as a deployment-prefix proxy. It
misses the edit location in many files, so any future policy that otherwise
passes must also survive an edit-containing-chunk sensitivity on the covered
subset before paid generation.

## Validity restrictions

1. **Resolver circularity.** The manifests' oracle paths were originally
   produced by the same language resolvers reconstructed here. Therefore
   `resolved_graph` and `resolved_rrf` measure packing/fusion feasibility, not
   independent resolver accuracy. They are development-only upper bounds.
2. **RAG proxy.** The saved index contains chunk embeddings but not the
   original full-prefix query embeddings. The first changed-file chunk vector
   is a no-cost proxy and is not byte-equivalent to the deployed RAG query.
3. **Reused stimuli.** Both corpora have already informed earlier analyses.
   No result from this folder is confirmatory. A later paid test must use
   frozen logic and new held-out defects.
4. **Static oracle scope.** Exact-path matching evaluates whether evidence is
   available, not whether the path is behaviorally affected under all runtime
   conditions.

## Reproduction

```bash
python scripts/evaluate_budgeted_fusion_retrieval.py
python scripts/evaluate_budgeted_fusion_retrieval.py \
  --result-stem RESULTS_COMPACT
python scripts/evaluate_budgeted_fusion_retrieval.py \
  --result-stem RESULTS_VALIDITY
python scripts/evaluate_budgeted_fusion_retrieval.py \
  --result-stem RESULTS_FINAL
```

The script is idempotent per result stem. It refuses to overwrite an existing
JSON/Markdown pair unless `--force` is supplied.
