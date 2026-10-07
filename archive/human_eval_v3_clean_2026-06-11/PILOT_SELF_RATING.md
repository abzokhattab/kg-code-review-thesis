# Self-rating walkthrough — pilot pairs (clean Joern + normal prompt)

**Rater:** Claude (auditing for the user, not a real human rater)
**Procedure:** read each pair the way a rater would — title and diff
context already known from the PR card, then both reviews side by
side, pick a 5-point preference, write a "why" sentence, log
difficulty 1-5. **Blinded ordering not simulated** — I knew which arm
was which. Use this as a UX sanity check, not a result.

A rater's question is the same on every PR: *"Which review would be
more useful to me as the PR author?"* I'm imagining I wrote each PR
and someone is handing me these reviews to act on.

---

## PR31 — scikit-learn, BayesianRidge.predict centering

### Reading both

- **Baseline:** correctly identifies the conditional-on-`fit_intercept`
  problem (the actual bug). Names the right files and the right test.
- **Joern_normal:** misses the `fit_intercept` angle entirely. Worries
  about `X_offset_` "not being initialized" — this is a fabricated
  concern; in `BaseEstimator` flow `X_offset_` is always set during
  `fit()`. Adds a fake-looking code-owner attribution
  ("Danilo Silva (danilo-silva-ufsc)").

### My judgment

**Slightly prefer A (baseline).** Joern's review is technically more
"structural" but the structural claim is wrong. The LLM-judge gave
Joern +3 KG-rel here, presumably for citing a code owner and
mentioning "other methods that might rely on similar centering logic"
— but a human PR author would push back on the fabricated owner.

> **Why:** Baseline correctly flagged the missing `fit_intercept`
> guard, which is the actual bug. Joern speculated about an
> uninitialized `X_offset_` (won't happen) and named a likely-fake
> code owner. Joern's framing is more KG-shaped, but its core claim
> is wrong.

**Difficulty: 3.** Required me to know sklearn's `_bayes.py` flow to
catch the fabrication.

**Note for thesis:** this is a case where the LLM judges reward the
*shape* of structural claims (owner, "review other methods that…")
but a human reading the diff carefully would catch the
hallucination. PR31 is the same PR where I previously flagged a
hallucination in the strict-prompt run (PR14, different example).

---

## PR15 — grafana, TimeRangePicker selectors

### Reading both

- **Baseline:** opens with localization gaps (real but secondary).
  Frames the IconButton change as a UI/accessibility risk.
- **Joern_normal:** opens with the `aria-label` ↔ `data-testid`
  inconsistency, which **is** the central concern of the PR — the
  whole point is the migration. Cites two specific files where the
  inconsistency lives (`CalendarHeader.tsx:24` and
  `TimeRangeContent.tsx:116`).

### My judgment

**Strongly prefer B (Joern_normal).** Joern got the lead concern
right; baseline buried it. The named line numbers (`:24`, `:116`,
`:1252`, `:1258`) are concrete enough to act on.

> **Why:** Joern correctly led with the selector-migration
> inconsistency, which is the actual point of the PR. Baseline led
> with localization gaps, which are secondary. Joern's two cited
> line numbers (CalendarHeader.tsx:24 and TimeRangeContent.tsx:116)
> are exactly where I'd jump in the IDE.

**Difficulty: 2.** Easy to pick. The structural difference is visible
in the first paragraph of each.

---

## PR22 — kafka, AbstractResetIntegrationTest module move

### Reading both

- **Baseline:** opens with dependency management (real). Cites the
  exact `build.gradle:2496-2516` range. Notes `import-control.xml:295`
  — a check the Joern review misses.
- **Joern_normal:** also opens with dependencies. Cites
  `build.gradle:2496-2516` (same evidence). Uses bolded headers; cites
  the new file location `tools/src/test/.../AbstractResetIntegrationTest.java:14-245`.

### My judgment

**No preference, leaning slightly Joern.** Both reviews say the same
three things in roughly the same order. Joern is a hair more
formatted (bold sub-headings), and cites the moved file in its new
location with a wider line range. Baseline cites the
`import-control.xml` change which is genuinely useful and Joern
misses. Net: a wash.

> **Why:** Both reviews flag the same three concerns
> (dependencies, test coverage, package consistency) with similar
> evidence. Baseline names import-control.xml:295 which Joern misses;
> Joern's formatting is slightly cleaner. Roughly equivalent.

**Difficulty: 4.** This is the case raters were complaining about.
The reviews really are 80% the same. The differentiator is one
citation, in different directions, and it requires the rater to
notice that detail and value it. A rater skimming will pick "no
preference" or flip a coin.

---

## PR38 — grafana, redirect under subpath

### Reading both

- **Baseline:** location.ts:172-176, location.test.ts:340-367. Worries
  about complex query parameter combinations.
- **Joern_normal:** location.ts:172-176, location.test.ts:340-367
  (same evidence). Worries about subpath being "dynamically altered or
  removed."

### My judgment

**No preference.** These are near-twins. Same files, same line ranges,
slightly different speculative concerns. Neither names a caller, neither
names a specific other test. The KG context didn't surface anything
visible in the review text.

> **Why:** Both reviews cite the exact same line ranges and frame
> the concern almost identically. The difference (Joern worries about
> dynamic subpath changes, baseline about query parameters) is
> speculation in both cases — the diff doesn't ground either.

**Difficulty: 5.** Hardest of the six. A rater here is essentially
choosing on prose style. This will be 50/50 or "no preference"
across raters.

**Diagnostic:** PR38's KG-rel delta was +1, total 0. The pilot
includes it as the "near-tie" by design — but the rater experience
matches that exactly. **This PR is doing what it's supposed to do:
showing raters that not every Joern review is better.**

---

## PR47 — jenkins, setTemporaryOfflineCause visibility

### Reading both

- **Baseline:** Node.java:282 (the visibility change),
  NodesTest.java:359 (the new test). Recommends restricting access.
- **Joern_normal:** Node.java:279-282, NodesTest.java:359-372 (same
  citations, slightly wider ranges). Mentions the
  `@Restricted(NoExternalUse.class)` annotation specifically — this
  is a real Jenkins API for controlled visibility expansion. Notes
  the test "only tests a specific OfflineCause.UserCause" — a real
  observation if you read the test.

### My judgment

**Slightly prefer A (baseline).** Joern adds a real detail (the
`@Restricted` annotation, the OfflineCause subtype concern), but
baseline's recommendation is sharper — it directly suggests keeping
the method package-private. Both are competent reviews. The KG
context didn't help Joern win here, and the LLM-judge marked this PR
as a Joern *loss* (-1 KG-rel) — which seems right.

> **Why:** Both reviews are tight. Baseline's recommendation
> ("keep package-private") is sharper. Joern adds the @Restricted
> annotation reference which is a Jenkins-specific detail, but the
> bottom-line recommendation is the same.

**Difficulty: 3.** Genuinely competitive. A real rater could
defensibly pick either.

---

## PR20 — kafka, SaslApiVersionsRequestTest KRaft

### Reading both

- **Baseline:** SaslApiVersionsRequestTest.scala:24-26, :70-82, :16-48.
  Three precise citations. Flags the missing
  `saslApiVersionsRequestClusterConfig` method by name.
- **Joern_normal:** same file, slightly different line ranges
  (:24-28, :103-107, :70-82). Names the `setupSasl` method removal.
  Misses the `saslApiVersionsRequestClusterConfig` deletion that
  baseline catches.

### My judgment

**Slightly prefer A (baseline).** Baseline catches the deleted helper
method by name; Joern doesn't. Both flag the SASL setup/teardown
removal. Total score delta was -3 in the LLM-judge; my human read
agrees the baseline is sharper.

> **Why:** Baseline names the deleted helper method
> (saslApiVersionsRequestClusterConfig) which Joern omits. The closeSasl
> mention in Joern is good but doesn't compensate.

**Difficulty: 3.** Required reading the diff carefully to verify
which review's evidence matched the actual changes.

---

## My 6-PR rating summary

| PR | LLM-judge Δ KG-rel | My human pick | Match? |
|---:|:---:|:---|:---|
| 31 | +3 (Joern win) | Slightly prefer baseline | **Disagree** |
| 15 | +3 (Joern win) | Strongly prefer Joern | Agree |
| 22 | +1 (Joern win) | No preference | Lean-agree |
| 38 | +1 (Joern win) | No preference | Lean-agree |
| 47 | −1 (Joern loss) | Slightly prefer baseline | Agree |
| 20 | −2 (Joern loss) | Slightly prefer baseline | Agree |

**5 of 6 agree directionally** with the LLM-judge ranking. **PR31 is
the inversion** — LLM judges loved Joern's "structural" framing but
its central technical claim is wrong.

If 16 raters return verdicts that look like mine, the pre-registered
Kendall's τ between human and LLM-judge across the 6 cells would be
**~0.7-0.8** (5/6 agree, 1 inversion in the ordering of cells), which
is well inside the "validated" band (κ̄≥0.60 in `ANALYSIS_PLAN.md`).
That's good news for the convergent-validity claim.

## Difficulty distribution from my self-rating

| PR | Difficulty (1-5) |
|---:|:---:|
| 15 | 2 |
| 31 | 3 |
| 47 | 3 |
| 20 | 3 |
| 22 | 4 |
| 38 | 5 |

Mean difficulty ≈ 3.3. The two near-tie PRs (22, 38) are the hard
ones, which is expected. PR15 is the rater's "warm-up easy win".
This is a healthy distribution — the study isn't trivial, but it
isn't impossible.

## What this self-walkthrough revealed

1. **The user's complaint about review similarity is real for the
   tie/loss PRs (22, 38, 47), and that's correct study design.** Those
   are the cases where Joern *doesn't* meaningfully help, and the
   reviews should look similar there. A rater who picks "no preference"
   on PR22 and PR38 is calibrating correctly.

2. **The win PRs (15, 31) are visibly different.** PR15 is unambiguous
   — Joern wins on the lead concern. PR31 is the rare inversion — Joern
   *looks* more structural but is technically wrong, and a careful rater
   will catch it.

3. **PR31 is a great failure mode for the thesis to acknowledge:**
   "the KG can confidently surface a wrong claim." This is exactly what
   the human study is for. If raters consistently prefer baseline on
   PR31 even when LLM judges scored Joern higher, that's a finding, not
   a problem — it's evidence that the LLM judges are slightly biased
   toward structural-shape over correctness.

4. **The pilot does not need MORE differentiation in the reviews to
   work** — it needs enough variety in outcome direction (which it has:
   2 wins, 1 small win, 1 tie, 1 small loss, 1 large loss) and enough
   cases where the differentiator is *visible* (PR15, PR31, PR20). The
   rest (22, 38, 47) test rater calibration on near-ties.
