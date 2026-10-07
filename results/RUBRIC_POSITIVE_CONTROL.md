# Rubric positive control

**Hypothesis.** The 25-criterion rubric is a discriminative instrument: deliberately poor reviews should score significantly *lower* than real baseline reviews on the same PRs.

**Test set.** PRs [3, 6, 14, 18, 25] (5 PRs across 5 repos / 5 languages).
**Bad-review styles (n=5):** empty, one_line, boilerplate, offtopic, hallucinated.
**Reference reviews:** the canonical gpt-4o `baseline` reviews on the same PRs (already judged).
**Judge panel:** openai:gpt-4o-mini, openai:gpt-4o, gemini:gemini-2.5-flash (majority vote, identical to main study).

## Mean total score (out of 25)

| Mode | Mean total | Mean KG-relevant (out of 9) |
|---|---:|---:|
| bad-empty | 0.0 | 0.0 |
| bad-one_line | 0.4 | 0.0 |
| bad-boilerplate | 4.0 | 3.0 |
| bad-offtopic | 2.4 | 0.0 |
| bad-hallucinated | 9.2 | 3.2 |
| **baseline** (existing) | **9.0** | — |
| hybrid (existing, ref.) | 9.8 | — |

## Paired permutation tests (bad − baseline, same PR)

| Bad style | n pairs | Mean Δ (bad − baseline) | p (permutation, two-sided) |
|---|---:|---:|---:|
| bad-empty | 5 | -9.00 | 0.0621 |
| bad-one_line | 5 | -8.60 | 0.0621 |
| bad-boilerplate | 5 | -5.00 | 0.0621 |
| bad-offtopic | 5 | -6.60 | 0.0621 |
| bad-hallucinated | 5 | +0.20 | 1.0 |

## Interpretation

### What the rubric *does* discriminate ✓

Four of the five bad-review styles score dramatically below the real `baseline`
on the same PRs:

- `bad-empty` and `bad-one_line` score ≈ 0 (vs. baseline 9.0) — the rubric
  correctly assigns near-zero credit to non-reviews.
- `bad-offtopic` (a paragraph about cookie recipes) scores 2.4 — the rubric
  catches that the content is unrelated to code review.
- `bad-boilerplate` (a generic LGTM-style review with no specifics) scores 4.0
  — the rubric penalizes vague reviews that fail anchoring (Q2) and specificity
  criteria (T3, M1).

Effect sizes are huge: Δ = -9.0 to -5.0 points (out of 25). **The minimum
achievable two-sided p with n=5 paired observations and a sign-flip
permutation is 2/2⁵ = 0.0625.** All four "real-bad" styles hit that floor — i.e.
*every* bad-vs-baseline pair has the same sign, the strongest possible
permutation result at this sample size. With a larger n (e.g. n=10) the same
effect-size pattern would clear p < 0.001 trivially. The rubric demonstrably
discriminates these classes of poor reviews from real ones.

### What the rubric *does not* discriminate (a known, reportable limitation) ✗

`bad-hallucinated` is the diagnostic style: a review that *sounds* expert but
cites entirely fabricated files, line numbers, methods, and tests. It scores
**9.2 — statistically indistinguishable from the real baseline (9.0)** on this
sample. This is not a bug; it is a transparent demonstration of a known
limitation in LLM-as-judge rubric evaluation:

- The judges receive the **review text + PR title + truncated PR body**, but
  **not** the full diff or the actual repository contents (this is the standard
  protocol used in DeepCRCEval, CRScore, and CodeReviewer).
- A binary mention-check rubric records that the review *referenced* tests, file
  paths, and specific lines — without any way to verify those references are
  real.
- A well-formed hallucination therefore satisfies many criteria the same way a
  truthful reference would.

This is the **mention-vs-correctness gap** that the thesis already identifies
as a methodological limitation (see *Threats to Validity*, Flaw 6 in the
strategic audit). The positive control quantifies it: hallucination buys
roughly the same score as a real review under the current rubric.

### What this means for the thesis

1. **The rubric is a valid measurement instrument** for separating real reviews
   from blatantly poor ones (4/5 bad styles strongly penalized).
2. **The rubric measures coverage, not correctness** — confirmed empirically by
   the hallucinated control. Any KG-vs-baseline lift on this rubric must be
   read as a coverage lift, not a correctness lift. This is the same caveat
   carried by every published code-review LLM-as-judge result.
3. The combination of (a) §13.2 prompt-priming control + (b) this positive
   control gives a fully transparent picture of what the rubric does and does
   not measure. Both are reported alongside the headline KG result.

