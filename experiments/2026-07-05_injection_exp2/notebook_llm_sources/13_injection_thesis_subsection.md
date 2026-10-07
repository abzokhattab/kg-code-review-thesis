# Drop-in thesis subsection (sensitivity probe)

> Placement: a sensitivity/ablation subsection in the Discussion or an Appendix,
> referenced from (i) the KG-construction comparison, (ii) Threats to Validity,
> and (iii) Future Work. It is framed as a controlled probe that *complements*
> the RQ2 rubric result; it does not restate or override the headline numbers.
> Voices are tagged per the operating rules: **[data]** empirical, **[lit]**
> secondary, **[arg]** my interpretation. Citations used here already appear in
> the bundle (`reports/2026-06-19/kg_findings_and_validity.md`); none are new.
> `[TODO: confirm path]` flags a source path I have not re-verified.

---

## X.Y  A controlled probe: KG construction and the locus of the cross-file effect

The 40-PR evaluation measures review quality on a 25-criterion rubric and reports
a *complementarity* result rather than universal KG dominance
(`results/BOOTSTRAP_STATS_v2.md`). That design answers *whether* structural context
helps, but it cannot isolate *which* structural dependencies a given KG builder
resolves, because the rubric score aggregates many criteria over real, multi-faceted
diffs. To probe that mechanism directly I ran a small, deliberately KG-favourable
experiment with a known ground truth (`exceptional test/prototype/`,
`out_scale/RESULT_JOERN_KG.md`).

**Setup.** I auto-discovered, via AST analysis, eight top-level symbols in two
scikit-learn subpackages (`preprocessing`, `linear_model`) that sibling modules
depend on, and injected a single-symbol *rename* into each — a defect whose entire
blast radius is cross-file and absent from the diff. I then generated reviews with
the production `prnote` prompts for all four modes and scored *detection* — whether
the review names a genuinely broken dependent file — with the same three-judge
majority panel used in the main study. The independent variable is the **KG builder**;
generator, prompt, and judges are held fixed.

**[data]** Detection (majority of three judges, n = 8; `out_scale/RESULT_JOERN_KG.md`):

| Mode / KG builder | Detected |
|---|---:|
| baseline (diff only) | 0/8 |
| rag (semantic, top-k = 10) | 1/8 |
| KG — grep-stem dependents (file-level, cap 10) | 2/8 |
| KG — Joern CPG call-graph (the promoted builder) | 4/8 |
| KG — symbol-level import edges (idealised) | 8/8 |

**[data]** Detection tracked exactly whether the builder supplied a true dependent.
Joern's CPG resolved cross-file **call** dependencies precisely — the function
renames `_preprocess_data` (4/4 true callers), `make_dataset` (2/2) and
`LinearRegression` (2/2 constructor call-sites). All four Joern misses were
**base-class or mixin** renames (`LinearModel`, `_BaseEncoder`,
`LinearClassifierMixin`, `SparseCoefMixin`), where the dependency is an
inheritance relation (`class Sub(Base)`) rather than a call, and is therefore
invisible to a call-graph traversal.

**[arg]** I read this as the mechanistic counterpart of the rubric-level
construction comparison (`reports/2026-06-19/kg_findings_and_validity.md` §1;
`results/KG_METHOD_COMPARISON.md`), which ranks Joern
(KG-relevant Δ +0.69, p = 0.003) above grep (Δ +0.54, p = 0.016) above a
tree-sitter AST variant (Δ +0.23, p = 0.25) and attributes Joern's advantage to
*precision, not volume*. The probe reproduces the ordering on an independent,
ground-truth task (Joern 4/8 > grep 2/8) and identifies the residual limitation
the rubric cannot localise: the promoted KG is **call-graph-centric and does not
encode inheritance or import edges**.

**[arg]** The two experiments are easily mis-read as contradictory because both
mention an "AST" builder. They are not. The rubric comparison's AST is a
*tree-sitter token extractor* that adds more, noisily text-matched structural
tokens and performs worst — consistent with evidence that input length and noise
degrade long-context models even under perfect retrieval (**[lit]** Liu et al.,
2023, *Lost in the Middle*, arXiv:2307.03172; Levy and Schwartz et al., 2025,
*Context Length Alone Hurts*, arXiv:2510.05381). The probe's idealised builder is a
*statically-resolved symbol-level import resolver* that adds few but exact edges.
**[arg]** Both results therefore point the same way — precise, statically-resolved
edges help; volume hurts — and together they sharpen the conclusion: the route from
Joern's call graph toward the idealised ceiling is not *more tokens* but *more
precise edge types*, specifically import and `INHERITS_FROM` edges, which the CPG
substrate can already express.

### A symmetric check: is the RAG baseline merely under-tuned?

**[arg]** A natural objection is that RAG's 1/8 reflects a weak RAG, not a limit of
semantic retrieval. To test this I re-ran the eight injections with a deliberately
stronger RAG that targets exactly this defect: **AST/function-aware chunking** (each
top-level def/class, and the module-header import block, becomes its own chunk, so an
importer's `from … import X` line is no longer buried mid-window) and
**query-by-symbol** (retrieval is keyed on the renamed symbol and its signature, not
the first 2 KB of the changed file). Generator, prompt, and judges were held fixed.

**[data]** Detection rose from **1/8 to 5/8**, and true-dependent retrieval rose from
**3/24 to 16/24** (`out_scale/RESULT_RAG_IMPROVED.md`). The four-of-eight gain came
entirely from cases where isolating the import block let the query-symbol match it
lexically *and* semantically. **[data]** The three residual misses are informative:
`LinearModel` (8 dependents, only 4 retrieved within top-k), `make_dataset` and
`SparseCoefMixin` — high-fanout or low-salience symbols where similarity ranking
either truncated the dependent set below top-k or never surfaced it
(`SparseCoefMixin`: 0/2 retrieved).

**[arg]** Two conclusions follow. First, the headline RAG number is *not* an artefact
of a toy retriever — a strong, purpose-built RAG still misses defects that the
idealised import-KG catches deterministically (8/8), because ranked similarity gives
no completeness guarantee on the full dependent set and degrades as fan-out grows.
Second, and more interesting, **the chunking change that helped is precisely the one
that makes RAG more structure-aware**: function-level chunks plus a dedicated import
chunk are a coarse, lexical approximation of the import edges the KG resolves
exactly. **[arg]** This is the same conclusion the KG ladder reaches from the other
direction — the improvements that close the gap, on either method, are those that
inject *precise structural boundaries*, not those that add more semantic text. It
also motivates the **hybrid** configuration directly: a tuned RAG recovers most
call/import dependents cheaply, while the KG supplies the deterministic completeness
(especially on inheritance and high-fanout symbols) that ranking cannot.

### Threats to validity (KG-construction completeness)

**[arg]** The promoted Joern KG resolves call dependencies but omits inheritance
and import edges; in the probe, every undetected cross-file rename was an
inheritance dependency. This is a completeness limitation of the *deployed* KG, and
it plausibly bounds the magnitude of the KG-relevant effect reported for the main
study (KG-relevant Δ +0.60, p = 0.007; `results/BOOTSTRAP_STATS_v2.md`): structural
signal that the builder never extracts cannot reach the reviewer. **[arg]** It also
offers one concrete reason the KG does not universally outscore RAG — beyond the
fact that many rubric criteria are not cross-file-structural at all.

### Caveats on this probe

**[arg]** This is a mechanism probe, not a second rubric result, and should be read
as such. The endpoint is binary cross-file-dependent *detection*, not the
25-criterion quality score; the defects are eight synthetic single-symbol renames,
not real merged PRs; and the symbol set was chosen to be maximally cross-file, i.e.
favourable to the KG. The probe therefore characterises an upper bound and a
failure mode; it does not estimate effect sizes and does not alter the headline
numbers.

### Future work (one concrete step)

**[arg]** Augment the Joern KG with statically-resolved **import** and
**`INHERITS_FROM`** edges (available from `typeDecl.inheritsFromTypeFullName` in the
CPG) and re-evaluate. The probe predicts this recovers the inheritance-rename cases
that the current call-graph KG misses; whether it widens the KG-relevant effect on
the 40-PR rubric is the open empirical question.
