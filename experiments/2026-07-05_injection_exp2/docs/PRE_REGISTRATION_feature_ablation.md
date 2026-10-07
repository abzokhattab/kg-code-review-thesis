# Pre-registration — Experiment 2 feature ablation

**Written:** 2026-09-06, before any `kg_deps_only` or `kg_edges_only` review
or verdict exists. Amendments go in a dated addendum only.

## 1. Why this runs on Experiment 2 and not on the rubric

RQ2.1 asks which context features carry the effect. Five attempts to answer it
on the 25-criterion coverage rubric have failed, and the reason is instrument
sensitivity rather than sample size:

* the rubric moves 5.00 → 5.56 /9 between baseline and `kg`, while measured
  single-draw generation noise is 0.88 /9 (`results/GENERATION_VARIANCE.md`);
* deleting either the test or the dependency section costs nothing
  (−0.27 and −0.10 /9, p = 0.33 and 0.78);
* scrambling the contents of either section costs nothing
  (`results/SCRAMBLED_NEIGHBOURHOOD.md`);
* the model discusses tests and downstream impact whether or not the block
  names any, so coverage saturates independently of the graph.

Experiment 2 measures whether the review finds a **planted** cross-file defect.
Its dynamic range on the structural bands is 0/28 for `baseline` against 15/28
for `kg` and 26/28 for `kg_idealised` — roughly thirty times the rubric's, on a
binary outcome that cannot be satisfied by generic prose. A feature that
matters will be visible here.

An independent precedent for both the sensitivity argument and the noise floor:
arXiv 2607.09691 holds localisation fixed with an oracle, scores binary issue
resolution, and reports that temperature-0 inference flips ~9% of per-instance
outcomes between byte-identical runs, "a noise floor under every small effect."
arXiv 2606.01859 isolates individual context types for Go review with one arm
per type plus a budget-matched random-context control.

## 2. The manipulation

The deployed `kg` arm supplies **two kinds of dependency evidence at once**
(`run_modes.py::joern_kg_context`):

| Component | Evidence | Granularity | Measured precision |
|---|---|---|---|
| `dependent_files` | lexical `grep` on the changed file's basename | file | 10.2% (`results/BUILDER_VOLUME_PRECISION.md`) |
| `call_graph_edges` | Joern CPG resolved call edges | function | program analysis |

Two new arms hold everything else fixed — same generator, same prompt, same
diff, same `changed_files` and `functions_changed` — and supply exactly one:

* **`kg_deps_only`** — `call_graph_edges` emptied. Lexical file list only.
* **`kg_edges_only`** — `dependent_files` emptied. Joern call edges only.

Experiment 2's KG block contains no test section, so the tests-versus-
dependencies split does not apply here. The split that does apply is lexical
against parsed evidence, which is the distinction Chapters 2 and 4 are built on.

## 3. Endpoint and eligibility

**Primary.** Detection rate on the 28 **structural** injections (bands S1-S5),
majority of the three canonical judges, ties to 0 — identical to the
pre-registered Experiment 2 endpoint.

**Secondary.** Detection rate on the 12 **local control** injections (L1, L2),
where the defect is visible in the diff and no arm should need the graph.

No injection is added or dropped. Both arms run on all 40.

## 4. Predictions, fixed now

The whole ladder, with the two new arms slotted in:

```
baseline            0/28   nothing
kg_deps_only          ?    lexical file list only
kg_edges_only         ?    Joern call edges only
kg                  15/28  both
kg_joern_inherit    21/28  both + resolved import/inherit edges
kg_idealised        26/28  true dependents
```

**P1 — parsed edges carry it.** `kg_edges_only` ≈ `kg` and `kg_deps_only` ≈
`baseline`. The function-level call edges are doing the work; the 10%-precise
file list is decoration. This is the prediction the precision measurement
implies and the one I expect.

**P2 — the file list carries it.** The reverse. Would mean naming a plausible
neighbouring file is enough to make the reviewer check it, consistent with the
scramble result on the rubric, and would make the Joern edges redundant.

**P3 — both are needed.** Both arms drop well below `kg`. The two kinds of
evidence would be complementary rather than substitutable.

**P4 — either alone suffices.** Both arms ≈ `kg`. Redundant evidence, and the
deployed arm carries avoidable prompt weight.

On the local controls all arms should stay near `baseline`'s 11/12. Any arm that
drops there indicates the added context is displacing attention from a
diff-visible defect rather than adding anything.

## 5. Statistics

Paired over injections. Exact McNemar for each arm against `kg` and against
`baseline` on the structural bands; Wilson 95% intervals on each rate;
bootstrap B = 10 000 and permutation B = 20 000 on rate differences, seed 2026,
matching `harness/stats.py`. Four primary contrasts, Holm-corrected.

Generator `openai:gpt-4o`, judges `gpt-4o-mini` + `gpt-4o` +
`gemini-2.5-flash`, majority of three — all unchanged from Experiment 2.

## 6. Outputs

```
experiments/2026-07-05_injection_exp2/out/reviews/*/kg_deps_only.md    (40)
experiments/2026-07-05_injection_exp2/out/reviews/*/kg_edges_only.md   (40)
results/EXP2_FEATURE_ABLATION.{md,json}
```

`ARMS` in `common.py` is left untouched and the new arms live in a separate
`ABLATION_ARMS` list, so the pre-registered `stats.py` output for the original
six arms cannot change. Estimated cost ~$8. Idempotent: generation skips
existing review files, judging is cached per verdict.
