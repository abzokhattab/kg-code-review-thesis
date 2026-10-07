# Graph-constrained semantic fusion — zero-cost development gate

Date: 2026-09-20  
Status: exploratory development gate; not a confirmatory thesis result

## Question

Can semantic similarity improve the ordering and usefulness of structural
context without adding unrelated repository files?

The historical hybrid concatenates an independent KG block and five dense-RAG
snippets. This trial instead restricts semantic retrieval to files already
connected to the change by the graph.

## Inputs

Read-only reuse of existing artefacts:

- 28 Experiment 2 structural injections and true dependent paths;
- 28 test-oracle injections and true broken test paths;
- clean source scopes;
- deployed Joern/lexical graph candidates;
- manifest-resolver candidates as a circular development ceiling only;
- saved `text-embedding-3-small` chunk vectors and code chunks.

No API or model call is made.

## Candidate policies

### `deployed_graph`

The existing deployed candidate pool and deterministic source/path ordering.

### `deployed_graph_semantic`

1. Build exactly the deployed graph pool.
2. Collapse candidates to one exact repository-relative path.
3. Split candidates by evidence confidence:
   - Joern-resolved call edge;
   - lexical/test-convention candidate.
4. Within each confidence tier, rank by the best saved semantic similarity for
   that same file.
5. Render compact graph evidence plus at most 300 characters from that file's
   highest-scoring code chunk.
6. Pack the longest ranked prefix under the fixed context budget.

Semantic search may rank or enrich a graph file; it may not introduce a file
outside the graph candidate pool.

### `manifest_resolver_graph_semantic`

Apply the same policy to the import/call/inheritance resolver union. Because
that resolver family generated the oracle labels, this is a packing ceiling,
not independent evidence of retrieval quality.

## Budgets

Context-only sensitivity at 2,000, 4,000 and 8,000 approximate tokens using
`ceil(serialized_characters / 4)`. The 4,000-token result governs the gate.

## Outcomes

Primary:

- hit at least one exact oracle file after budget packing.

Secondary:

- macro oracle-path recall;
- oracle-path fraction among selected files;
- first relevant rank / MRR;
- fraction of selected oracle files carrying a semantic source-code excerpt;
- tokens and candidate count.

Dependency and test cohorts govern separately. Pooled output is descriptive.

## Go/no-go rule

At 4,000 tokens, `deployed_graph_semantic` must, in both cohorts:

1. lose zero per-case hits relative to `deployed_graph`;
2. have no lower macro oracle recall;
3. have no lower oracle-path fraction;
4. attach semantic code evidence to at least 75% of selected oracle paths;
5. remain within budget for every case; and
6. produce byte-equivalent records on a deterministic rerun.

Passing licenses only a pre-registration and new held-out generation study.
Failure stops the fused-hybrid proposal before paid calls.

## Validity restrictions

- The semantic query is the first indexed chunk of the changed file, a
  zero-cost proxy for the deployed full-prefix embedding.
- The same 56 stimuli informed earlier analyses; this is development data.
- Oracle relevance is not exhaustive for semantic files, but this policy does
  not add semantic-only files.
- A retrieval pass does not show that an LLM will use the evidence correctly.

## Reproduction

```bash
python scripts/evaluate_graph_constrained_fusion.py
```

Outputs: `RESULTS.{md,json}` and `VALIDATION.md` in this folder.
