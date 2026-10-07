# Named-entity audit — what each review names that the other doesn't

**Method:** for each PR pair, extract every concrete file path,
file:line citation, function name, and quoted code symbol from each
review. Take the asymmetric diff. The result is the rater's
differentiator budget — how many concrete things they could point to
when writing the "why" sentence.

A pair with 2 differentiators is asking the rater to pick on prose.
A pair with 19 differentiators is letting them pick on substance.

---

## Per-PR named-entity counts

| PR | Differentiators | LLM-judge Δ KG-rel | My read |
|---:|---:|:---:|:---|
| 15 | **19** | +3 | Substantively different — easy rater pick |
| 20 | 11 | −2 | Both sharp, baseline has the deleted helper |
| 31 | 10 | +3 | Joern fabricates; baseline more accurate |
| 47 | 8 | −1 | Joern adds @Restricted; baseline sharper rec |
| 22 | 6 | +1 | Mostly the same; baseline has `import-control.xml` |
| 38 | **2** | +1 | **Near-identical reviews** |

## What a rater actually sees

### High-substance pairs (PR15, PR20, PR31, PR47)

The rater can write a meaningful "why" sentence:

- "Joern named `CalendarHeader.tsx:24` and `TimeRangeContent.tsx:116`
  where the inconsistency lives." (PR15)
- "Baseline named the deleted `saslApiVersionsRequestClusterConfig`
  helper; Joern only mentioned `closeSasl`." (PR20)
- "Joern correctly framed structural concern but its
  `X_offset_` claim is wrong; baseline got `fit_intercept`." (PR31)
- "Joern cited the `@Restricted(NoExternalUse.class)` annotation that
  baseline missed." (PR47)

These four PRs **work** as study items.

### Borderline (PR22)

6 differentiators. The rater can write *something*, but it'll be
about which of two extra files got cited. Most raters will land on
"slightly prefer A" or "slightly prefer B" with low confidence,
which is consistent with the LLM-judge Δ=+1 outcome.

### Problem child (PR38)

**2 differentiators.** Both reviews cite the exact same file:line
ranges (`location.ts:172-176`, `location.test.ts:340-367`). The only
unique entities are `home_page` and `redirectUri`, both in the
baseline. Joern adds nothing identifiable.

The reviews also score Δ=+1 on KG-rel — a near-tie — so this is
data-faithful: the LLM judges agree the reviews are nearly equivalent.

But for a rater this PR is an instruction to **write prose-level
preferences**, which is what raters complain about. PR38 has the
**lowest signal-to-effort ratio** of the six.

## Implications for study design

### Option A: keep PR38 as the "near-tie" anchor
Pros: balanced design, the LLM-judge says it's a near-tie, the
human study should test whether raters agree on near-ties too.
Cons: raters report low-confidence ratings on this PR, time spent
disproportionate to information yielded.

### Option B: replace PR38 with a different near-tie PR
Candidates from the 35-PR pool with Δ_KG-rel ∈ {−1, 0, +1} and
larger named-entity differences would have to be re-audited. PR48
(Δ=+1, total=+1, 4 differentiators expected based on review length)
is a candidate. So is PR42 (Δ=+1, total=+3).

### My recommendation
**Keep PR38 in the pilot, but document that it is the near-tie test
case.** The whole point of including a near-tie is that it should
*feel* near-tie to raters. If 16/16 raters return "no preference" on
PR38, that's a positive validity signal for the LLM-judge ranking
(both agree it's a tie). If raters split 50/50, also a tie signal.
The only worrying outcome is if raters strongly prefer one side on
PR38 — and given the 2 named-entity differences, that's unlikely.

But: in the analysis, **expect lower confidence and longer time
on PR38**, and use that as a rater-effort signal not a design flaw.

## Connection to the user's complaint

The user said: *"the reviews are similar so it was kinda hard for me
to tell the difference."*

Cross-reference with this audit:
- If they were on PR38 (2 differentiators) — **expected, design-faithful**.
- If they were on PR22 (6 differentiators) — **expected for the
  small-win arm**.
- If they were on PR31, PR15, PR20, or PR47 — there's plenty of
  signal to find; the UI may have been the bottleneck, not the data.

The pilot UI already has unique-sentence highlighting via
`shadeUniqueBlocks()` — but the threshold is Jaccard 0.50 over
3-letter tokens, which is text-level, not entity-level. On PR38, the
two reviews share so much vocabulary that the Jaccard score is
high *across the whole review*, so highlighting may shade nothing.

**Actionable UI improvement (not done in this pilot, but recommended):**
add a "named entities only this side" strip above each review card.
This would surface the 2-19 differentiators directly without making
the rater hunt. Even on PR38, showing "this review names `home_page`
and `redirectUri`" would clarify the difference exists.
