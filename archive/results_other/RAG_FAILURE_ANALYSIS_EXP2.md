# Why RAG fails on cross-file defects — retrieval-stage analysis (Exp 2)

**Data:** per-injection retrieval diagnostics written during the RAG arm of
Experiment 2 (`experiments/2026-07-05_injection_exp2/out/reviews/*/rag_diagnostic.json`),
plus exact re-runs of the retrieval queries (2026-07-13). Config is the
thesis-faithful production RAG: `text-embedding-3-small`, prnote chunker,
top_k = 10, query = first 2 KB of the changed file, same-file chunks excluded.

## Headline

Across the 28 structural injections, retrieval surfaced **16 of 616 true
dependent files (2.6%)**. RAG's detection was 1/28. The failure locus is
retrieval, not generation: the reviewer cannot name a dependent it was
never shown, and the single detection is exactly the single case where a
dependent was retrieved saliently.

## Mechanisms (three cases)

### 1. Self-similarity collapse — `sklearn_S1_01`
(rename `TransformerMixin` in `sklearn/base.py`, 18 dependents)

All 10 top-ranked chunks are from `base.py` itself (sim 0.74–0.998);
after same-file exclusion RAG entered generation with **zero** other-file
context. The true dependents contain one `from sklearn.base import
TransformerMixin` line inside files that are topically about clustering /
preprocessing — embedded, they are dissimilar to the definition-site query
by construction. Modal outcome: **12/28 injections retrieved nothing from
any other file.**

### 2. Same collapse in Java — `kafka_S2_01`
(signature change in `WrappedStateStore.java`, 24 dependents)

Top-10 all same-file at sim 0.96–0.98 (Java boilerplate tightens
intra-file similarity). Zero surviving context.

### 3. The exception that proves the rule — `kafka_S1_01`
(rename `KeyValue`, 89 dependents; **RAG's only detection**)

Retrieval surfaced `KeyValueStore.java` (sim 0.696) — a consumer that is
lexically/conceptually saturated with the term "KeyValue". It was
retrieved for *topical name-sharing*, not because the system resolved a
dependency. Even here, 8 of 10 result slots were chunks of that one file
(no diversity), i.e. effective retrieval breadth was 1 of 89 dependents.
Detection tracked retrieval 1:1.

## Interpretation (for the Discussion chapter)

Dense retrieval ranks by topical similarity. The dependency relation
("file B imports/calls the symbol changed in file A") is not a topical
relation: the query is drawn from the definition site, the evidence lives
at usage sites, and the two are semantically dissimilar by construction.
Similarity correlates with dependency only for eponymous concept-defining
types (the `KeyValue`/`KeyValueStore` case) — 1 of 28 here.

Two pre-emptions of the "weak RAG strawman" objection:
1. The config is the production one that **wins on total coverage in
   Experiment 1** — it is good at what similarity search is for.
2. The prototype's purpose-built stronger RAG (AST chunks +
   query-by-symbol) raised dependent-retrieval 3/24 → 16/24 and detection
   1/8 → 5/8 (`exceptional test/prototype/FINDINGS_SCALE.md` §RAG
   sensitivity): the modifications that help are precisely lexical
   approximations of the structural edges the KG encodes exactly.

One-sentence claim:
> On defects whose evidence lives at usage sites, retrieval-by-similarity
> fails architecturally (2.6% dependent recall); graph edges encode the
> dependency relation directly, which is why the KG detects 15/28 where
> RAG detects 1/28 on the identical inputs.
