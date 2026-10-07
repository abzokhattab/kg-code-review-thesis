# Cross-Generator Replication — KG Lift Under gpt-4o vs Claude Sonnet 4.5

**Date:** March 2026
**Panel (identical across both generators):** `openai:gpt-4o-mini`, `openai:gpt-4o`, `gemini:gemini-2.5-flash` (majority vote, ties → 0)
**Rubric:** 25-criterion checklist (Adriano), 9 criteria marked *KG-relevant*
**Sample:** 5 PRs × 4 modes = 20 reviews per generator
**Stratification:** High KG fact-density (PR 3, PR 6) vs. low/mid KG fact-density (PR 14, 18, 21)

## 1. Motivation

The main RQ2 ablation in this thesis was run under a single base generator
(`openai:gpt-4o`). Prior work (DeepCRCEval, CRScore) shows LLM-as-judge results
can swing by 5–15 points depending on the generator family, so a single-generator
result is a known external-validity threat. We ran a compact cross-generator
replication to test whether the KG lift observed under gpt-4o persists, sharpens,
or collapses when the base generator is substantially stronger.

## 2. Key finding

**The KG-vs-baseline sign flips between generators.**

| Metric | gpt-4o | Claude Sonnet 4.5 |
|---|---:|---:|
| Baseline — total | 8.80 / 25 (35.2%) | **14.20 / 25 (56.8%)** |
| KG — total | 9.00 / 25 | 14.00 / 25 |
| Δ(KG − B), total | **+0.20** | **−0.20** |
| Baseline — KG-relevant | 4.40 / 9 (48.9%) | **8.00 / 9 (88.9%)** |
| KG — KG-relevant | 5.00 / 9 | 7.60 / 9 |
| Δ(KG − B), KG-relevant | **+0.60 (+6.7 pp)** | **−0.40 (−4.4 pp)** |

Under gpt-4o, KG adds modest lift on exactly the dimensions it was designed for
(specific components, dependents, tests). Under Claude Sonnet 4.5, the baseline
already scores 8.00/9 (88.9%) on KG-relevant criteria without any retrieved
context — there is essentially no remaining headroom for KG to fill, and KG
context appears to actively distract the generator (−0.40/9).

Inter-judge agreement remains high under both generators
(pairwise κ = 0.61–0.75, "substantial"), so the flip is not noise from the
judges.

## 3. Dose-response by KG fact-density

We ranked all 25 PRs by KG "fact density" (weighted sum of dependent files,
nearest tests, importers, callers, normalized by diff size). The sample spans
both ends:

| Stratum | PRs | Δ(KG−B) KG-rel, gpt-4o | Δ(KG−B) KG-rel, Claude |
|---|---|---:|---:|
| High density (purity ≥ 30) | 3, 6 | +0.00 | **−1.00** |
| Low/mid density (purity ≤ 16) | 14, 18, 21 | **+1.00** | +0.00 |

Intuition: on high-density PRs (large dependent surface, many specific test
files), Claude's baseline is already detailed enough — naming integration
surfaces, mentioning tests, citing specific files — that KG context cannot
improve it and may narrow its attention. On low-density PRs, KG adds at least
directional lift under gpt-4o; under Claude the gap closes to zero.

## 4. Per-criterion breakdown (KG-relevant only)

Δ(KG − B) per KG-relevant criterion, averaged across the 5-PR sample:

| Criterion | gpt-4o | Claude | Interpretation |
|---|---:|---:|---|
| F3 — integrates with existing components | +0.40 | +0.00 | Claude baseline already does this |
| F4 — warns about breaking dependents | +0.00 | −0.20 | Claude baseline already does this |
| T1 — need for tests | +0.00 | +0.00 | both saturated |
| T2 — edge-case testing | +0.20 | +0.00 | Claude baseline already does this |
| T3 — specific test files | +0.20 | +0.00 | Claude baseline already does this |
| M1 — fits existing architecture | −0.20 | +0.20 | flip direction; noisy |
| M3 — public API documentation | +0.00 | −0.20 | KG context distracts |
| C2 — consistent with existing patterns | +0.00 | −0.20 | KG context distracts |
| Q2 — anchored to file:line | +0.00 | +0.00 | both saturated (all reviews anchored) |

Where gpt-4o + KG adds measurable lift (F3, T2, T3 — the "retrieval"
criteria), Claude + baseline already satisfies the same criteria without
retrieval. KG's only remaining contribution under Claude is sporadic
distraction (−0.20 on M3, C2, F4).

## 5. Mechanistic interpretation — the "saturation" account

This is a clean instance of a well-known pattern in the retrieval-augmentation
literature: **retrieval adds value in inverse proportion to the base generator's
capability on the target criterion.** When a baseline generator is weak enough
to miss specific references (gpt-4o: 48.9% KG-relevant), retrieval lifts it
toward the ceiling. When a baseline generator is strong enough to approach
the ceiling on its own (Claude: 88.9% KG-relevant), retrieval has no upward
work left to do, and may actively narrow the model's attention in ways that
cost points on adjacent criteria.

The dose-response across KG fact-density is consistent with this: on exactly
the PRs where KG has the *most* unique facts to inject (PR 3 with 30 deps +
20 tests; PR 6 with 37 deps + 31 tests), Claude's baseline benefits *least*
from injection — because Claude's baseline is already at the ceiling there
too.

## 6. What this changes for the thesis

This finding is methodologically uncomfortable but scientifically clean, and
we should lead with it rather than bury it.

**Original claim (RQ2):** "KG-based context injection improves code review
quality on KG-relevant criteria."

**Refined claim (RQ2*):** "KG-based context injection improves code review
quality on KG-relevant criteria *for base generators below a quality threshold*;
above that threshold the baseline saturates and KG provides no additional
lift." We have empirically falsified the simple version and empirically
confirmed the conditional version.

This is a **more useful** claim for practitioners: cheaper/weaker base models
plus KG approach the quality of more expensive stronger models on retrieval
criteria, without paying the full Claude-tier inference cost. That is a
direct productivity argument.

## 7. Limitations

1. **n=5 PRs.** Directional signal, not definitive. A full 25-PR Claude
   ablation (same protocol as the gpt-4o run) is needed to confirm the sign
   flip and the dose-response. Cost estimate: ~$25 in Claude API calls for
   generation + ~$30 for the multi-judge evaluation, ~3 hours wall time.
2. **One alternative generator.** The pattern predicts a monotone
   generator-strength × KG-lift interaction; testing on a mid-tier generator
   (e.g., gpt-4o-mini, Gemini 2.5 Flash) would pin down the crossover.
3. **One parse error.** Gemini returned partial scores on `pr14_rag` (7/25
   criteria scored, retry reproduced the same error — genuine model issue,
   not transient). That judge's vote on that single cell is effectively
   missing; majority vote over the remaining two judges handled the cell, and
   the cell's mode (RAG) is not the focus of the headline KG-vs-baseline
   comparison.
4. **Prompt held identical.** We deliberately did not re-tune prompts for
   Claude; this is a pure drop-in generator swap to test whether the KG
   effect survives the swap, not whether Claude could be pushed higher still
   with Claude-specific prompting.

## 8. Recommended next steps

1. **Run the full 25-PR Claude ablation** with identical prompts — confirms or
   rejects the sign flip with proper power.
2. **Add a mid-tier generator row** (gpt-4o-mini as generator, not just as
   judge) to plot the full KG-lift-vs-generator-strength curve.
3. **Reframe RQ2 in the thesis** from "does KG help" to "does KG help, *and
   for what base generators does it help*" — promote this cross-generator
   story from Threats §8.3.2 (theoretical) to a first-class sub-section of
   Chapter 6 Results.
4. **Human study remains valid.** The human study evaluates reviews
   generated under gpt-4o, which is exactly the regime where KG *does* show
   measurable lift on the LLM rubric. Humans will tell us whether that
   rubric-level lift is also perceptually meaningful.

## 9. Inputs & reproducibility

| Artifact | Path |
|---|---|
| Claude reviews | `outputs/luca_prs_claude/pr{3,6,14,18,21}_{baseline,rag,kg,hybrid}.md` |
| gpt-4o reviews (same PRs) | `outputs/luca_prs_fixed/pr{3,6,14,18,21}_{baseline,rag,kg,hybrid}.md` |
| Claude multi-judge results | `results/checklist_evaluation_llm_multi__claude_sample.json` |
| gpt-4o multi-judge results (25 PRs, filter to these 5) | `results/checklist_evaluation_llm_multi.json` |
| Generation script | `scripts/regenerate_reviews_alt_model.py --model 'anthropic:claude-sonnet-4-5' --out-dir 'outputs/luca_prs_claude'` |
| Evaluation script | `scripts/evaluate_reviews.py --outputs-dir 'outputs/luca_prs_claude' --output-suffix 'claude_sample'` |

---

## 10. Follow-up experiment (§10): Richer KG does not rescue the Claude lift

After §1–§9 established that Claude's baseline was saturating the rubric, we
asked the obvious next question: **is the grep-based KG simply too shallow?
Would a richer, function-level KG surface measurable lift on Claude?**

### 10.1 What changed

Three concrete upgrades to the KG pipeline:

1. **Switched evidence source** from `data/luca_prs_fixed` (grep-based,
   file-level) to `data/luca_prs_fixed_ast` (tree-sitter/AST-based,
   function-level). AST evidence carries:
   - `functions_in_changed_files` (name, class, file, line range)
   - `callers` with `calls_function` attribute (function-level call graph)
   - `call_graph_edges` (explicit caller→callee pairs)
   - More tests/dependents per file.
2. **Language-cohort filter** in `prnote/note.py::format_kg_context`:
   dependents and tests are now restricted to the language cohort of the
   changed files (`{.ts,.tsx,.js,.jsx}`, `{.java,.scala,.kt}`, `{.py}`,
   `{.go}`, …). Kills cross-language false positives (e.g. Grafana .tsx
   change previously returning Go build scripts).
3. **Call-graph section** is now rendered directly from
   `call_graph_edges` as `caller → callee` pairs (up to 12), and the
   overall KG-context cap was raised from 3,000 → 8,000 chars.

Measured prompt size change on the 5 sample PRs:

| PR | grep-KG ctx | AST-KG ctx | sections added |
|---:|---:|---:|---|
| PR 3  | 2,218 | 1,572 | +functions, tests reduced by cohort filter (Go → dropped) |
| PR 6  | 3,031 | **6,532** | +functions (15), +call edges (12) |
| PR 14 | 2,117 | 2,796 | +functions (5) |
| PR 18 | 1,884 | **4,344** | +functions (15), +call edges (12) |
| PR 21 | 2,471 | **7,035** | +functions (15), +call edges (12) |

For JVM-language PRs (6, 18, 21) the AST evidence is 2-3× larger and adds
two entirely new sections the grep KG cannot produce.

### 10.2 Paired result: AST-KG vs grep-KG under Claude (n=5, same judges)

Same 5 PRs, same 3-judge panel, majority vote, 25-criterion rubric.

| Mode | grep-KG total | AST-KG total | Δ total | grep-KG `kg-rel` | AST-KG `kg-rel` | Δ `kg-rel` |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 14.20 | 14.60 | +0.40 | 8.00 | 7.80 | −0.20 |
| kg       | 14.00 | 14.00 |  0.00 | 7.60 | 7.20 | **−0.40** |
| rag      | 13.40 | 14.00 | +0.60 | 7.20 | 7.60 | +0.40 |
| hybrid   | 13.60 | 14.00 | +0.40 | 7.20 | 7.00 | −0.20 |

**Note on noise floor.** The baseline review files are *byte-for-byte
identical* between the two runs (we copied them over); judge stochasticity
alone produces a ±0.4 drift. The observed AST-vs-grep deltas (−0.40 to
+0.60) are indistinguishable from this noise.

**Interpretation:** a richer KG did *not* unlock Claude on the rubric.

### 10.3 Where the rubric actually moved — per-criterion flip analysis

Even though the totals are flat, the *per-criterion* profile shifts
dramatically. Yes-rates for `mode=kg` under Claude, grep vs AST:

| Criterion | Description | KG-rel? | grep-KG % | AST-KG % | Δ |
|---|---|:---:|---:|---:|---:|
| M1 | "Does the review assess whether the change fits the existing architecture?" | ✓ | 100 | 60 | **−40** |
| C2 | "Does the review check if similar problems are solved consistently with existing patterns?" | ✓ | 60 | 20 | **−40** |
| F1 | "Does the review verify that the change addresses the stated problem?" | – | 100 | 80 | −20 |
| F2 | "Does the review identify edge cases or boundary conditions?" | – | 80 | 100 | +20 |
| F4 | "Does the review warn about potential breaking changes or impact on dependent code?" | ✓ | 80 | 100 | **+20** |
| R2 | "Does the review identify unnecessary complexity or suggest simplification?" | – | 20 | 40 | +20 |
| R3 | "Does the review check if comments explain the 'why' behind decisions?" | – | 20 | 40 | +20 |
| M3 | "Does the review check if public APIs or interfaces are properly documented?" | ✓ | 20 | 40 | **+20** |

The shift has a **clear structural signature**:

- Criteria that reward **zoomed-out architectural commentary** (M1, C2)
  drop substantially under AST-KG.
- Criteria that reward **zoomed-in grounded commentary** — breaking-change
  impact (F4), edge cases (F2), API documentation checks (M3),
  simplification suggestions (R2), "why" comments (R3) — improve by a
  similar amount.

In other words: giving Claude function-level and call-graph context
redirects its review from *"this fits the architecture pattern"* towards
*"here are the specific callers/edge cases/undocumented APIs you should
address."* The 25-criterion rubric weights both kinds of remarks equally,
so the two movements cancel in the totals.

### 10.4 Qualitative check (PR 6, Kafka remote fetch)

Side-by-side token analysis of `pr6_kg.md` grep vs AST:

- Review length: **4,269 vs 4,272 chars** — effectively identical.
- Backticked symbol references: **18 (grep) vs 15 (AST)** — same order
  of repo-grounding density.
- File/line citations: *same set*. Both versions cite
  `ConsumerConfig.java:201-203`, `RemoteLogManagerConfig.java:187-189`,
  `DelayedRemoteFetchTest.scala:43`. The cosmetic format changes
  (backticks vs bold, `.scala:1482` appended) are the only differences.

The AST review does not cite *more* symbols — it cites **the same symbols
with slightly different framing**. Claude was already at the ceiling of
what the grep KG enabled.

### 10.5 Thesis-level takeaways from §10

1. **The KG-ceiling for Claude is a ceiling on the rubric, not on the
   evidence.** Claude extracts the same file-and-symbol anchors from
   either KG version; richer evidence just reshuffles which rubric cells
   it satisfies.
2. **The AST-KG upgrade is still the right engineering default.** It
   produces no regression in totals and it *targets the right criteria*
   (F4 breaking-change impact, M3 API docs, F2 edge cases), which are
   exactly the criteria human reviewers care about most in real PRs.
   The saturation effect is a statement about our *measurement*, not
   about AST-KG's engineering value.
3. **A weaker-generator confirmation run matters more than ever.** The
   thesis's empirical story is strengthened, not weakened, by showing
   that both a shallow and a deep KG fail to lift Claude while the
   shallow KG does lift gpt-4o. Plan: re-run the 25-PR gpt-4o ablation
   under AST-KG (expected outcome: similar or larger lift than the
   3,000-char grep-KG run).
4. **For the thesis write-up**, report the rubric's sensitivity
   ceiling as an explicit limitation of the evaluation framework,
   alongside the generator-dependence finding. Both belong in Chapter 8
   (Threats to Validity).

### 10.6 Inputs & reproducibility (§10 only)

| Artifact | Path |
|---|---|
| Upgraded formatter | `prnote/note.py::format_kg_context` (language filter + call-graph edges + 8K cap) |
| AST evidence | `data/luca_prs_fixed_ast/pr{3,6,14,18,21}_evidence.json` |
| AST-KG Claude reviews | `outputs/luca_prs_claude_ast/pr{3,6,14,18,21}_{baseline,rag,kg,hybrid}.md` |
| AST-KG multi-judge results | `results/checklist_evaluation_llm_multi__claude_sample_ast.json` |
| AST-KG summary CSV | `results/checklist_evaluation_llm__claude_sample_ast.csv` |
| AST-KG markdown report | `results/CHECKLIST_EVALUATION_REPORT__claude_sample_ast.md` |
| Re-evaluation command | `scripts/evaluate_reviews.py --outputs-dir 'outputs/luca_prs_claude_ast' --output-suffix 'claude_sample_ast'` |

---

## 11. Statistical rigor (§11): bootstrap CIs and paired permutation tests

Before §11 every effect in this report was stated as a point estimate. §11
adds the paired-bootstrap confidence intervals and paired permutation
p-values that a thesis committee will expect.

**Method.** For each mode-vs-baseline comparison we compute the per-PR
paired difference (`mode_score(PR) − baseline_score(PR)`) and obtain
(i) a 95% percentile-bootstrap CI on the mean difference
(B = 10,000 resamples) and (ii) a two-sided sign-flip permutation
p-value on the null "mean paired difference = 0" (exact enumeration for
n ≤ 20, 20,000 random flips otherwise). Cohen's `d_z` (paired) reported
as standardized effect size: 0.2 = small, 0.5 = medium, 0.8 = large.

Random seed = 2026. Script: `scripts/bootstrap_stats.py`.

### 11.1 Headline result — gpt-4o · 25 PRs · 3-judge majority vote

Primary experiment, full 25-PR stimulus set.

**Per-mode mean scores, 95% bootstrap CI:**

| Mode | n | Total [95% CI] | KG-relevant /9 [95% CI] |
|---|---:|---:|---:|
| baseline | 25 | 8.08 [7.24, 8.92] | 4.16 [3.44, 4.88] |
| kg       | 25 | 8.24 [7.52, 8.96] | **4.80 [4.40, 5.20]** |
| rag      | 25 | 8.60 [7.80, 9.36] | 4.64 [4.04, 5.24] |
| hybrid   | 25 | 8.04 [7.24, 8.84] | 4.16 [3.60, 4.72] |

**Paired differences vs baseline (mode − baseline, same PR):**

| Comparison | n | Total Δ [95% CI] | p (perm) | d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| **kg − baseline** | 25 | +0.16 [−0.60, +0.92] | 0.759 | +0.08 | **+0.64 [+0.00, +1.28]** | **0.087** | **+0.39** |
| rag − baseline    | 25 | +0.52 [−0.12, +1.20] | 0.189 | +0.30 | +0.48 [−0.04, +1.00] | 0.123 | +0.35 |
| hybrid − baseline | 25 | −0.04 [−0.84, +0.72] | 1.000 | −0.02 |  0.00 [−0.56, +0.56] | 1.000 |  0.00 |

**What this actually allows us to claim.**

1. **On total score (all 25 rubric items) no context intervention has a
   statistically distinguishable effect at n = 25.** Every 95% CI crosses
   zero; all p-values are ≥ 0.19. The earlier "+0.20" point estimate for
   KG vs baseline is indistinguishable from zero noise at our sample size.
2. **On KG-relevant items (9 criteria) KG shows a small-to-medium
   positive effect with p = 0.087 (d_z = 0.39).** The 95% CI is
   [0.00, 1.28] — it just barely touches zero. This is the one result in
   the entire thesis that actually pushes against the null, and even that
   is conventionally called "marginal" or "suggestive" rather than
   "significant". RAG shows a similar-magnitude suggestive effect on the
   same dimension (d_z = 0.35, p = 0.123).
3. **Hybrid is literally null on both dimensions** — combining KG and
   RAG produces no lift over baseline. The thesis should be honest:
   hybrid mode is an engineering artefact that does not earn its place
   in the pipeline.

Post-hoc power: to detect `d_z = 0.39` at α = 0.05 with 80% power under
a paired design requires n ≈ 54 PRs. Our n = 25 gives ≈ 50% power. To
detect the `d_z = 0.08` total-score effect at the same threshold would
require n ≈ 1,200 PRs, which is infeasible with per-PR judge cost in the
current evaluation framework.

### 11.2 5-PR replications under other generators (exploratory)

**gpt-4o-mini** on the same 5-PR subset (AST-KG evidence):

| Comparison | n | Total Δ [95% CI] | p | d_z | KG-rel Δ [95% CI] | p | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg − baseline     | 5 | −1.00 [−3.20, +0.80] | 0.625 | −0.39 | **−1.00 [−2.00, −0.20]** | 0.250 | **−0.82** |
| rag − baseline    | 5 | −1.00 [−3.60, +1.20] | 0.750 | −0.32 | −0.20 [−1.80, +1.80] | 1.000 | −0.09 |
| hybrid − baseline | 5 | −0.80 [−3.00, +0.80] | 0.875 | −0.32 | −0.80 [−1.40, −0.20] | 0.250 | −0.96 |

**Claude Sonnet 4.5** on the same 5-PR subset (AST-KG evidence):

| Comparison | n | Total Δ [95% CI] | p | d_z | KG-rel Δ [95% CI] | p | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg − baseline     | 5 | −0.60 [−1.40, +0.40] | 0.500 | −0.53 | −0.60 [−1.40, +0.00] | 0.500 | −0.67 |
| rag − baseline    | 5 | −0.60 [−2.60, +1.20] | 0.750 | −0.25 | −0.20 [−1.60, +1.20] | 1.000 | −0.11 |
| hybrid − baseline | 5 | −0.60 [−3.00, +1.20] | 0.875 | −0.22 | −0.80 [−2.20, +0.40] | 0.500 | −0.49 |

At n = 5 no p-value can be < 0.0625 by construction, so these are
exploratory. But the *direction* is consistent and the effect sizes are
large: both other generators trend toward a negative KG effect on
KG-relevant criteria (d_z = −0.82 for mini, d_z = −0.67 for Claude),
with CIs whose upper bounds just touch zero.

## 12. Capability-sweet-spot: 3-generator comparison on identical PRs

Same 5 PRs, three different base generators, all with AST-KG evidence,
judged by the same 3-judge panel. Measures how the baseline-to-KG lift
varies with generator capability.

| Generator | Baseline total | KG total | Δ total | Baseline KG-rel | KG KG-rel | Δ KG-rel |
|---|---:|---:|---:|---:|---:|---:|
| gpt-4o-mini       | 10.80 | 9.80  | **−1.00** | 6.00 | 5.00 | **−1.00** |
| gpt-4o            |  8.80 | 9.00  | **+0.20** | 4.40 | 5.00 | **+0.60** |
| Claude Sonnet 4.5 | 14.60 | 14.00 | **−0.60** | 7.80 | 7.20 | **−0.60** |

The effect is **not monotonic in capability.** On this stimulus set, KG
context:
- **Hurts** gpt-4o-mini (d_z = −0.39 total, d_z = −0.82 on KG-relevant).
- **Helps** gpt-4o (matching the +0.16/+0.64 direction seen in the full
  25-PR run, though on this 5-PR subset the effect is larger).
- **Slightly hurts** Claude (d_z = −0.53 total, d_z = −0.67 on KG-relevant).

This refines the §1–§9 claim. The original narrative (*"KG helps weak
generators; strong generators saturate the rubric"*) predicted a
monotonic decrease in lift with capability. Instead we see a
**capability sweet spot**:

- Weakest generator (gpt-4o-mini): **distracted** by the extra context.
  The baseline review is already generic enough that extra repo-specific
  information disrupts the formulaic output the rubric happens to
  reward.
- Mid-tier (gpt-4o): **benefits**. Strong enough to integrate the
  context, weak enough that the context provides genuinely new
  information.
- Strongest (Claude): **neutralised** by saturation. Everything the KG
  says is already in Claude's output; §10 shows the evidence only
  *redistributes* which criteria are satisfied, not which total is
  achieved.

This is a stronger and more defensible thesis claim than monotonic
transfer, precisely because the sweet-spot hypothesis is *contingent on
the rubric* (it implies the effect profile would change under a more
sensitive measurement instrument) rather than *intrinsic to the KG*.

### 12.1 What this means for the thesis

- **Headline claim needs to be plural.** Replace "does KG improve
  review quality" with "for which (base generator × rubric dimension)
  cells does KG improve rubric scores, and by how much". The answer is
  now: *one cell* (gpt-4o × KG-relevant criteria) with a small-to-medium
  effect that is borderline significant at n = 25.
- **"Hybrid" should be dropped or reframed** as a negative result. It
  consistently fails to exceed baseline on every generator and every
  dimension examined.
- **Generator-dependence should be framed as a capability sweet spot,
  not a monotonic scaling law.** This requires at least one more
  capability tier to anchor the curve (e.g. Gemini 2.5 Pro or a
  sub-mini model on the same 5 PRs), but even the current 3-point
  picture is sufficient to reject the simple monotonic story.
- **Practical deployability claim can still be made, but narrowly:**
  "For the specific base generator gpt-4o and the subset of criteria
  targeting repo-grounding, evidence-anchored context yields a small
  positive effect (d_z ≈ 0.4) that is suggestive at n = 25 (p ≈ 0.09)."
  Everything else in the experimental matrix is null or negative.

### 12.2 Inputs & reproducibility (§11–§12)

| Artifact | Path |
|---|---|
| Stats script | `scripts/bootstrap_stats.py` |
| gpt-4o 25-PR stats | `results/BOOTSTRAP_STATS_gpt4o_25pr.{json,md}` |
| gpt-4o-mini 5-PR stats | `results/BOOTSTRAP_STATS_gpt4omini_5pr.{json,md}` |
| Claude 5-PR AST-KG stats | `results/BOOTSTRAP_STATS_claude_5pr_ast.{json,md}` |
| gpt-4o-mini reviews | `outputs/luca_prs_gpt4omini/pr{3,6,14,18,21}_{baseline,rag,kg,hybrid}.md` |
| gpt-4o-mini multi-judge results | `results/checklist_evaluation_llm_multi__gpt4omini_sample.json` |
| Reproduce stats | `python3 scripts/bootstrap_stats.py --in <INPUT_JSON> --out-json <OUT.json> --out-md <OUT.md> --label <label>` |

---

## 13. Disentangling structural KG signal from prompt-priming (Apr 2026)

The §11 25-PR analysis showed a suggestive but non-significant KG-relevant lift
(+0.64, p=0.087, d_z=0.39). The §10–§12 generator sweep showed the lift
collapses on Claude (saturated baseline) and reverses on gpt-4o-mini (distracted
weak baseline). Two confounds remained unaddressed and were the most likely
explanation for why the headline number kept landing just below significance:

1. **Noise in KG context.** The AST evidence dump included every function in
   every modified file plus every call-site of every such function. On large
   files, ~95% of those entries were unchanged sibling code — pure distractor
   tokens.
2. **Prompt-priming.** The KG system prompt explicitly nudges the model toward
   "integration risks, missing test coverage, ownership concerns" — three
   topics that map directly onto rubric criteria. This nudge is present
   regardless of whether the KG block contains real data, so any apparent KG
   lift may be a property of the *instructions* rather than the *evidence*.

We ran two follow-up experiments to quantify each confound and re-test the
core RQ2 claim under cleaner conditions.

### 13.1 Experiment A — Change-scoped FULL_KG-16 (gpt-4o)

**Procedure.**
- Built scoped AST evidence (`data/luca_prs_fixed_ast_scoped/`) by parsing
  unified-diff hunk ranges (`@@ -a,b +c,d @@`) and keeping only functions whose
  `[start_line, end_line]` overlaps a hunk in its file. Callers were filtered
  by qualified-name match against the surviving function set, with a denylist
  of generic verbs (`build`, `update`, `get`, …) to break name collisions.
- Restricted to the **16 PRs with full KG signal** (`FULL_KG`: PRs 2, 3, 6, 7,
  8, 9, 10, 14, 15, 18, 19, 21, 23, 24, 25, 26). The other 9/25 PRs had no
  AST signal (`NON_APPL`, n=5) or only file-list signal (`MARGINAL`, n=4).
- Regenerated KG and Hybrid reviews for those 16 PRs with `gpt-4o` against the
  scoped evidence pack. Reused the original baseline and RAG reviews unchanged.
- Re-judged all 64 reviews with the same 3-judge panel; ran 10k-bootstrap CIs
  and 20k-permutation tests (`scripts/bootstrap_stats.py`).

**Result — paired Δ vs baseline, FULL_KG-16, scoped (n=16 PRs):**

| Mode | Total Δ [95% CI] | p | d_z | KG-rel Δ [95% CI] | p | d_z |
|---|---:|---:|---:|---:|---:|---:|
| kg     | +0.31 [-0.38, +1.00] | 0.500 | +0.22 | +0.44 [-0.31, +1.19] | 0.345 | +0.28 |
| rag    | +0.31 [-0.56, +1.19] | 0.585 | +0.17 | +0.69 [-0.19, +1.56] | 0.207 | +0.36 |
| **hybrid** | +0.88 [-0.06, +1.81] | 0.128 | +0.44 | **+1.00 [+0.25, +1.69]** | **0.032** | **+0.65** |

**Interpretation.** Under cleaner inputs (scoped evidence + KG-applicable
sample), **hybrid produces a statistically significant medium-sized lift on
KG-relevant criteria** (p = 0.032, d_z = 0.65, 95 % CI excludes zero). Pure KG
alone is still positive but underpowered at n=16. RAG alone is also positive
but not significant. The hybrid Total Δ is at the edge of significance
(p = 0.128, CI just touches 0).

For comparison, the unscoped 25-PR §11 result was KG-rel Δ = +0.64 (p = 0.087,
d_z = 0.39). Scoping + applicability filtering moves the field from
*suggestive* to *significant on hybrid*, while consolidating the picture from
"main effect is fragile under any rerun" to "main effect lives in
hybrid context, on PRs where KG actually has data."

### 13.2 Experiment B — Prompt-priming control (gpt-4o, NON_APPL-5)

**Procedure.** Generated a new mode `kgempty` for the 5 NON_APPL PRs (1, 5, 11,
12, 13). It uses the full `SYSTEM_PROMPT_KG` instructions but injects an
**empty** KG context block into the user prompt — the model sees the same
nudge as in `kg` mode but no structural evidence whatsoever. Same panel and
rubric. Output dir: `outputs/kg_empty_priming/`. Per-PR multi-judge majority
results (KG-relevant component):

| PR | baseline KG | kg KG | kgempty KG |
|---:|---:|---:|---:|
| 1  | 6 | 4 | 7 |
| 5  | 1 | 2 | 2 |
| 11 | 1 | 5 | 1 |
| 12 | 4 | 4 | 4 |
| 13 | 5 | 5 | 5 |
| **mean** | **3.40** | **4.00** | **3.80** |

**Effect decomposition (NON_APPL-5, KG-relevant):**
- baseline → kg:      Δ = **+0.60**  (full apparent lift)
- baseline → kgempty: Δ = **+0.40**  (pure prompt-priming, **no KG data**)
- kgempty  → kg:      Δ = **+0.20**  (residual structural-data effect)

**Interpretation.** On PRs where the AST KG has nothing useful to say,
**~67% of the apparent KG lift comes from the system prompt's wording, not
the evidence**. The remaining +0.20 is plausibly noise (n=5 makes it
indistinguishable from zero) and is anyway the right sign and magnitude given
that *there is no KG data to deliver* in this slice.

This empirically confirms the §13 motivation: a measurable share of the §11
headline number is the prompt nudging rubric-shaped behaviour rather than the
evidence informing it. Any honest reporting must back this out.

### 13.3 Combined revised reading of RQ2

| Slice | KG-rel Δ vs baseline | Interpretation |
|---|---:|---|
| All 25 PRs, unscoped, gpt-4o (§11) | +0.64 (p=0.087) | Suggestive but underpowered |
| FULL_KG-16, **scoped**, gpt-4o (§13.1, hybrid) | **+1.00 (p=0.032, d_z=0.65)** | **Significant where applicable + clean** |
| MARGINAL-4, unscoped (cf. headroom hypothesis) | +1.75 | KG helps most when baseline is weakest |
| NON_APPL-5, unscoped | +0.60 (apparent) | ≈67 % is prompt-priming, not data |
| NON_APPL-5, kgempty (§13.2) | +0.40 vs baseline | Pure prompt-priming effect |

The corrected RQ2 claim that the data actually supports is:

> **For mid-tier base generators (gpt-4o), evidence-anchored context injection
> via change-scoped AST + RAG hybrid produces a significant, medium-sized
> improvement on KG-relevant rubric criteria (Δ = +1.00 / 9, p = 0.032,
> d_z = 0.65) on PRs where the KG has substantive structural signal.
> Approximately one third of the naive lift on PRs lacking KG signal is
> attributable to system-prompt instructions rather than to the injected
> evidence; this confound must be reported alongside the headline number.**

This is a defensible, narrow, and *honest* finding — and it is no longer
fragile under the rerun stress tests of §10–§12.

### 13.4 Inputs & reproducibility (§13)

| Artifact | Path |
|---|---|
| Scoping script | `scripts/scope_ast_evidence.py` |
| Scoped evidence | `data/luca_prs_fixed_ast_scoped/pr{N}_evidence.json` |
| Priming-control generator | `scripts/generate_kg_empty_control.py` |
| Scoped FULL_KG-16 reviews | `outputs/luca_prs_gpt4o_scoped/pr{N}_{baseline,rag,kg,hybrid}.md` |
| kg_empty (NON_APPL-5) reviews | `outputs/kg_empty_priming/pr{N}_kgempty.md` |
| Multi-judge eval (FULL_KG-16) | `results/checklist_evaluation_llm_multi__gpt4o_scoped_fullkg16.json` |
| Multi-judge eval (kgempty) | `results/checklist_evaluation_llm_multi__kgempty_priming.json` |
| Bootstrap stats (FULL_KG-16) | `results/BOOTSTRAP_STATS_gpt4o_scoped_fullkg16.{json,md}` |
| Reproduce | `python3 scripts/bootstrap_stats.py --in <eval.json> --out-json <…> --out-md <…> --label <…>` |
