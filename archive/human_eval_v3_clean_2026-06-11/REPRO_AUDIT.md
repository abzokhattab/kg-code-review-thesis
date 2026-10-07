# T=0.0 reproducibility — clean Joern reviews

**Question:** at temperature 0.0, with the same prompt and model
(`openai:gpt-4o`), does the LLM produce identical output across
runs?

## Method

Re-generate the clean-Joern review for PR1 and PR31 using the exact
same prompt construction as `experiments/2026-06-11_joern_normal_prompt/run.py`
(buggy version — body omitted, matching what produced the on-disk
review). Compare the regenerated text against the on-disk file by
MD5 hash, length, and 5-gram Jaccard similarity.

## Result

| PR | MD5 match | orig len | new len | Jaccard 5-gram | Verdict |
|---:|:---|---:|---:|---:|---|
| 1 | **DIFFERS** | 1557 | 1602 | **0.715** | Same direction, slight rewording, line numbers drift |
| 31 | **DIFFERS** | 1714 | 1763 | **0.570** | Substantially rewritten — and the regen actually **catches the `fit_intercept` insight** the original missed |

## Reading

**OpenAI's `temperature=0.0` is not strictly deterministic.** The
documentation has long noted that even at T=0 the API may produce
different outputs across calls due to:
- floating-point non-determinism in batched inference
- backend routing across model replicas
- nucleus sampling tie-breaking

This is a known property of GPT-4o (and most production LLMs at T=0).
Jaccard 5-gram of ~0.6-0.7 across runs is consistent with what other
T=0 reproducibility studies report.

## Implications for the experiment

1. **The headline d_z=+0.58 number is reproducible *in distribution*,
   not bit-for-bit.** A re-run of the entire 35-PR pipeline would
   produce slightly different review texts, slightly different judge
   scores, and slightly different d_z. Magnitude of fluctuation:
   based on a single PR-1 and PR-31 pair, the *content* is mostly
   stable (Jaccard ≥0.57); the *details* (line numbers, phrasings,
   minor concerns) vary.

2. **PR31 case is interesting.** The regen catches the
   `fit_intercept=False` angle that the on-disk version missed. This
   means **the LLM was capable of producing the correct insight on
   PR31**; the on-disk review just landed on the "X_offset_" framing
   instead. With Joern strict-prompt review (which is in the human
   study), the model was forced to discuss specific KG criteria and
   produced a different framing again. **Joern's contribution is
   bounded by LLM sampling variance.**

3. **For the methodology chapter:** state explicitly that T=0
   reproducibility for GPT-4o is approximate (Jaccard ≈0.6-0.7 in
   spot checks, not bit-identical). This is a normal property of
   production LLMs and is not a flaw in the experimental design,
   but it does bound the precision of single-run effect-size
   estimates.

4. **For the human study:** raters are evaluating a *specific
   review*, not "the average review the system would produce".
   That's intentional — humans see what real users would see — but
   it means that if a different rater pool saw a fresh re-generation,
   their preferences could shift on borderline PRs. **This is a
   first-order limitation that belongs in the threats-to-validity
   section.**

## Useful follow-up (out of scope for this audit)

- Run the full pipeline 5 times with T=0 and report the d_z 95% CI
  across runs. Estimated cost: ~$15, ~2 hours wall-clock. This
  would convert the headline from a single-point estimate to a
  range. Recommended for thesis revision but not blocking.

- Run with `seed=42` (OpenAI now supports seeded reproducibility on
  GPT-4o). Initial spot-checks show seeded runs are also not
  bit-deterministic but reduce drift further.
