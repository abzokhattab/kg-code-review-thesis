# Deep-audit synthesis — clean Joern run (2026-06-11)

> ⚠️ **SUPERSEDED 2026-06-11 (later same day) by `HONEST_HEADLINE.md`.**
> Robustness battery results (`ROBUSTNESS_BATTERY.md`) and the
> per-arm score breakdown showed:
> - The 95% CI on parity d_z straddles zero.
> - The redundancy mechanism narrative below is **not supported** by
>   the body-length regression — read `HONEST_HEADLINE.md` §6 for the
>   corrected "interference" interpretation.
> - Direction stability buggy↔parity is 54%, conflicting with the
>   "softer-than-feared" framing in the bottom-line section.
>
> The bulk of this doc — per-criterion teardown, per-language
> stratification, hallucination audit, KG-leakage findings, judge
> unanimity — remains accurate as descriptive analysis on the buggy
> data. **The synthesis-level claims about parity should be read
> against `HONEST_HEADLINE.md`.**

---


**This file integrates all the deep-audit results into a single read.
For evidence, see the audit files listed at the bottom.**

> ⚠️ **Update 2026-06-11 evening:** the parity re-run completed and
> changed the headline. **New principled headline: d_z=+0.30 KG-rel,
> p=0.066, n=35** (was +0.58, p=0.003 under the buggy script). See
> §3 below and `PARITY_RESULTS.md` for full detail. The buggy +0.58
> overstated the effect by giving the baseline arm a piece of
> context (the PR body) the joern arm had to rebuild from KG. With
> both arms equal, KG's marginal contribution is +0.30 — small,
> consistent in direction, but **not significant at p<0.05** for
> n=35.

---

## TL;DR — what the deep audit changed

| Question | Surface verdict (initial VERDICT.md) | Deep-audit verdict |
|---|---|---|
| Is the experiment solid? | Yes | **Yes, but with caveats** ↓ |
| What drives the d_z=+0.58? | Implied: the 9 KG-rel criteria broadly | **6 of 9 KG-rel criteria contribute; 3 don't (T1/Q2/M3)** |
| Is the effect uniform across languages? | Implied: yes | **No. C++ is null (d_z=−0.22).** Python +1.14, TS +1.41, Java +0.45 |
| Is the experiment fair to the joern arm? | Implied: yes | **No.** Body was omitted from joern_normal user_prompt — parity re-run in progress |
| Are reviews factually grounded? | Not checked | **10/35 cite ≥1 unverified file. PR31 fabricates a code owner.** |
| Does the clean prompt surface KG signal? | Implied: weakly | **Quantified: ~5% of available caller signals get cited** |
| Are judges robust? | Not checked | **Yes** — 75.4% unanimity overall (above the 70% threshold) |

The thesis headline is still publishable as a result, but the
**methodology section** needs to disclose:
- Per-language stratification (Python/TS strong; C++ null)
- Per-criterion contribution (T1, Q2 are floor; M3 negative; Q5 — non-KG-rel — is the single biggest contributor at +0.20)
- The clean-prompt-vs-strict-prompt trade-off and why the headline is the clean number
- The 1 fabricated-owner case (PR31) as an honest failure-mode example
- The body-parity correction (once the re-run completes)

---

## 1. Per-criterion teardown of the +0.58 effect

The headline is "KG-rel d_z=+0.58 (n=35, p=0.003)". Decomposing it:

**Top 5 contributors to the criterion-level Δ-yes count (any criterion):**

| # | Criterion | KG-rel? | Δ yes (kg − bl) | Mean Δ |
|---|---|:---:|---:|---:|
| 1 | **Q5** | (no) | +7 | +0.20 |
| 2 | **M1** | ✓ | +7 | +0.20 |
| 3 | P1 | (no) | +5 | +0.14 |
| 4 | C2 | ✓ | +5 | +0.14 |
| 5 | F3 | ✓ | +5 | +0.14 |

**Within the 9 KG-rel criteria:**
- Positive contributors (6): M1 (+0.20), C2 (+0.14), F3 (+0.14), F4 (+0.11), T3 (+0.09), T2 (+0.03)
- Floor (no movement): T1 (already 34/35 yes for baseline), Q2 (already 35/35)
- Negative contributor (1): M3 (−0.03)

**Honest framing for thesis:** "the KG augmentation primarily improves
six structural-context criteria (M1, C2, F3, F4, T3, T2). Two of the
nine KG-relevant criteria (T1, Q2) are at ceiling under both
conditions, and M3 shows a small negative drift."

This is more defensible than "the KG improves the 9 criteria". The
rubric design assumed all 9 would move; in practice 2 are at ceiling
and 1 moves the wrong direction. **Discuss in the methodology
chapter.**

See: `DEEP_AUDIT.md` §1.

---

## 2. Per-language stratification

| Language | n | Mean Δ KG-rel | d_z KG-rel | Verdict |
|---|---:|---:|---:|---|
| **TypeScript** | 8 | +1.25 | +1.41 | **Strong positive** |
| **Python** | 8 | +1.13 | +1.14 | **Strong positive** |
| **Java** | 11 | +0.55 | +0.45 | **Modest positive** |
| **C++** | 6 | −0.17 | **−0.22** | **Null / slightly negative** |
| Scala | 2 | 0 | 0 | n too small |

**This is a real finding, not noise.** The C++ stratum has 6 PRs and
a nonzero SD (the d_z is computed). Joern's C++ frontend is a known
sore point — semantic resolution on header-heavy C++ is approximate.
The C++ PRs in the dataset (1, 12, 13, 30, 45, 46) don't gain
KG-relevant insight from the structural context.

**Implication:** the headline d_z=+0.58 is being **dragged down** by
C++ and pulled up mostly by TS and Python. A language-stratified
re-analysis would likely show the typed-script + Python d_z closer
to +1.0 and C++ near zero.

**Thesis recommendation:** add a per-language breakdown to the
results chapter. The "KG augmentation works" claim is honest for
Python/TS and modest for Java; for C++ it's not supported by this
sample.

See: `DEEP_AUDIT.md` §2.

---

## 3. Body-parity confound (the bug I caught)

The headline pipeline (`dataset_v2/scripts/regenerate_reviews_v2.py`)
includes the PR description body in the user_prompt:

```python
body_block = f"\n## PR Description\n{body}\n" if body else ""
user_prompt = f"## Pull Request: {title}\n{body_block}## Diff\n```...```\n{context}\n..."
```

The clean-Joern run script
(`experiments/2026-06-11_joern_normal_prompt/run.py`) **omits the body**:

```python
user_prompt = (
    f"## Pull Request: {pr_title}\n\n"   # ← no body_block
    f"## Diff\n```\n{diff}\n```\n"
    f"{context}\n\n"
    "Please generate an evidence-anchored review note ..."
)
```

**Impact:** all 35 PRs have non-empty bodies; 19/35 are >500 chars.
The largest are PR33 (7,574 chars), PR47 (7,216), PR2 (5,828) —
non-trivial review-relevant content (stack traces, motivations, edge
cases the author already flagged). The **baseline** scores in
`results/checklist_evaluation_llm_multi__v2.json` were generated
*with* the body via the headline pipeline. So the joern arm in the
clean-Joern comparison was given **less** information than the
baseline arm, which means **the d_z=+0.58 number is a lower bound**.

**Mitigation in progress:** a parity re-run is underway in
`experiments/2026-06-11_joern_normal_prompt_parity/`. Cost ≈ $2.60,
~25 min. When it completes I'll update this file with the corrected
d_z. Expectation: parity number ≥ +0.58 because the bug penalised
the joern arm.

> **Update — parity run complete:** the expectation was wrong. Parity
> correction lowered the d_z to **+0.30 (p=0.066)**, not raised it.
> Mechanistic explanation: PR bodies and KG context overlap in the
> review-relevant information they supply. Giving the baseline the
> body unlocks much of what the joern arm had been using KG to
> surface. The KG's *marginal* contribution above a body-equipped
> baseline is smaller than the +0.58 suggested. **This is the
> publishable headline.** See `PARITY_RESULTS.md`.

See: parity script at
`experiments/2026-06-11_joern_normal_prompt_parity/run.py`.

---

## 4. Hallucination audit

Method: extract every `file:line` citation and `Code Owner / Author`
field from the 35 reviews; cross-check against the Joern evidence
pack.

| Failure | Count |
|---|---:|
| Reviews with ≥1 unverified file citation | **10 / 35 (29%)** |
| Reviews fabricating a code owner | **1 / 35** (PR31, "Danilo Silva") |
| Reviews with `@handle` mentions | 0 |
| Reviews fabricating a team | 2 |

**Unverified file citations** include both real hallucinations (file
doesn't exist) and **soft hallucinations** (extension drift —
`CalendarHeader.ts` instead of `CalendarHeader.tsx`). PR15 has 5
soft hallucinations of this type. PR42 fabricates `utils/_sorting.py`
(real path is `sklearn/utils/_sorting.py` — but `utils/_sorting.py`
also appears separately, suggesting confusion).

**The Danilo Silva fabrication on PR31** is the most concerning:
it's an unambiguous hallucination of a person's name + GitHub
handle, dressed up as a code-owner attribution. This is the same PR
where my pilot self-rating preferred baseline despite LLM-judges
scoring Joern +3 KG-rel. The fabrication is a textbook example of
"the LLM rewards the *shape* of structural claims".

**Thesis recommendation:** include PR31 as a named
failure-mode example in §discussion. Frame as: "the KG-augmented
generation can produce fabricated authorial metadata; LLM judges
score this as evidence of context-awareness; humans correctly
identify it as wrong. This is part of why the human study matters."

See: `HALLUCINATION_AUDIT.md`.

---

## 5. KG-signal leakage — does the prose carry the structural context?

Method: for each PR, count Joern caller/dependent symbols that the
review actually cites in the text.

- 33 / 35 PRs had ≥1 caller signal available in the evidence pack.
- 22 / 33 reviews cited at least one of those signals (67%
  binary citation rate).
- **But the per-PR proportional rate is 0-22%, mostly 0-10%.** The
  LLM uses ~5% of the available caller list.

**This corroborates the strict-vs-clean trade-off.** Strict-prompt
reviews force ~17 named entities per pair (PR38 case) by mandate;
clean-prompt reviews settle for 1-2 — less than half of which come
from the KG. The d_z=+0.58 effect is driven mostly by the LLM's
*implicit framing* (which functions to discuss, what concerns to
raise) rather than by visible citations.

**Implication for the human study (the user's original concern):**
on most PRs, raters will find the differentiation in *prose framing*,
not in *named entities*. The pilot UI's per-side highlighter was
calibrated for entity-level differences; for clean-prompt pairs it
will under-highlight. The user's report of "reviews are similar" was
the rater catching this empirically.

**This does not invalidate the clean-prompt headline** — the LLM
judges pick up on framing — but it explains why human raters
struggle. The right framing in the thesis is:

> "The clean-prompt setting is the methodologically pure
> comparison: same prompt for all four arms, no MUST coverage
> mandates. It establishes that the KG augmentation produces
> measurable improvements in the LLM-judge ranking (d_z=+0.58,
> p=0.003). The strict-prompt setting (d_z=+1.34) is reported
> as an exploratory upper bound, with the methodological caveat
> that the prompt biases coverage toward the rubric. Both arms of
> the human study test the same convergent-validity claim under
> different signal-to-prose ratios."

See: `KG_LEAKAGE_AUDIT.md`.

---

## 6. Judge unanimity

- Overall: **660 / 875 cells unanimous = 75.4%** (3-judge panel).
- Per-PR: range 56% (PR12) to 88% (PR13, PR22, PR40).
- 7 PRs below 70%: PR12, PR20, PR23, PR45, PR46, PR47, PR15.

This is **well above the 70% robustness threshold** typically
quoted for multi-judge LLM evaluation. The d_z=+0.58 effect is not
driven by judges leaning the same direction without consensus — it
survives a unanimity-only re-aggregation. **The headline is judge-robust.**

See: `DEEP_AUDIT.md` §3.

---

## 7. Things I checked and did not find

- **No bias toward longer reviews.** Length ratios across the 6
  pilot PRs are 0.91–1.38 (median 1.11). The Joern arm is not
  systematically longer in a way that would mechanically inflate
  the score.
- **No silent generator drift.** Both runs use GPT-4o, T=0.0,
  same SDK version, same `prnote/llm.py` codepath.
- **No silent prompt difference beyond the body.** The system
  prompts are byte-identical (`SYSTEM_PROMPT_KG`); the user_prompt
  diff is the missing `body_block` and nothing else.
- **No judge-set leakage.** All 35 clean-Joern scores use the
  full 3-judge `DEFAULT_PANEL`. Re-aggregating with 2 OpenAI
  judges only (`scores_2openai_only.json`) gives the same
  direction.

---

## 8. What I would still want to do (out of scope for this hour)

1. **Re-run the per-criterion analysis after the body-parity fix
   completes.** The 6 KG-rel positive contributors might shrink or
   shift; expecting the *direction* to hold but the magnitudes to
   change.
2. **Per-language re-run after parity.** C++ might still be null;
   if it stays null across both, that's a thesis claim.
3. **Cohen's κ pairs between judges** (not just unanimity rate).
   I have unanimity at 75.4% but not the all-pairs κ. Would
   require re-extracting per-judge per-criterion verdicts from
   the score JSONs.
4. **A LLM-judge-vs-human bootstrap with 1000 raters' worth of
   resampling.** The pilot self-rating is 5/6 directional
   agreement on n=6; a real Kendall's τ confidence interval
   needs the live human study.
5. **A formal C++-frontend-quality probe.** Joern's C++ analyser
   may be silently producing thinner KG packs for C++ PRs; if so
   that explains the null d_z. Would require sizing
   `callers`/`functions_in_changed_files` per language.

---

## Pointer files

| File | What |
|---|---|
| `VERDICT.md` | Original surface verdict (yes/no on solidity + study) |
| `EXPERIMENT_AUDIT.md` | 5-check soundness audit |
| `DEEP_AUDIT.md` | Per-criterion + per-language + judge-unanimity |
| `HALLUCINATION_AUDIT.md` | File-citation + owner-name verification |
| `KG_LEAKAGE_AUDIT.md` | How much of Joern's KG ends up in the review text |
| `STRICT_VS_CLEAN_COMPARISON.md` | The named-entity trade-off across prompts |
| `NAMED_ENTITY_AUDIT.md` | Pilot-PR differentiator counts |
| `PILOT_SELF_RATING.md` | I rated 6 pairs; agreed with judges 5/6 |
| **THIS FILE (`VERDICT_v2.md`)** | Synthesis of all of the above |

---

## Bottom line, after deep audit

The clean-Joern experiment is **publishable but more nuanced than the
surface audit suggested**.

- The d_z=+0.30 effect (parity-corrected) is real in *direction* but
  **does not reach conventional significance** at p<0.05 (n=35,
  Wilcoxon p=0.066 KG-rel, p=0.070 total).
- It is **not uniform across languages** (TS/Python strong; C++ null
  in the buggy data — re-stratification needed for parity).
- It is **not driven by 9-of-9 KG-rel criteria** (6 positive, 2
  ceiling, 1 negative, in the buggy data — re-decomposition needed).
- The **body-parity correction lowered the effect**, indicating
  KG context and author-written PR bodies are partially redundant
  signals.
- It comes with a **29% unverified-file citation rate** and **1
  fabricated code owner** that the thesis discussion needs to name.

**The honest framing for the thesis:**

> The principled comparison (clean prompt, body parity) shows a
> small positive effect of KG augmentation (d_z=+0.30, p=0.066,
> n=35) that does not reach conventional significance. The
> exploratory strict-prompt comparison (d_z=+1.34, p<0.0001) shows
> a large effect under forced rubric coverage. The gap between
> these numbers is itself a finding: KG augmentation's *measurable*
> value depends on whether the prompt forces structural-context
> citation. The tree-sitter result (d_z=+0.47, n=40) sits between
> the two and is not directly comparable due to the language
> coverage difference.

**None of this changes the recommendation to run both human studies.**
With the clean-prompt effect now known to be small, the strict-prompt
arm is even more important for power.
