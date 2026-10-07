# Clean confirmatory test — 12 held-out PRs, headline configuration

**Date:** 2026-08-31
**Script:** `scripts/rerun_confirmatory_heldout.py`
**Supersedes:** `experiments/2026-05-14_confirmatory_kg/RESULTS.md` and
`results/checklist_evaluation_llm_multi__confirmatory.json` (2026-05-14), which
are not interpretable — see "Why the May run was discarded" below.

**Design:** 12 held-out PRs (never used in any exploratory analysis), paired
baseline vs KG, same 25-criterion checklist and same 9-item KG-relevant subscale
as the 40-PR headline.
**Generator:** `openai:gpt-4o` @ T=0.0, v2 prompt, v2 (grep-based) KG builder.
**Judges:** headline 3-judge panel — `gpt-4o-mini`, `gpt-4o`, `gemini-2.5-flash`.

Only the dataset differs from the headline run. Generator, prompt, KG builder,
temperature, judge panel, rubric and scoring denominator are all held fixed,
which is what a confirmatory test requires.

---

## Headline result

| Mode vs baseline | n pairs | Total Δ [95% CI] | p | d_z | KG-rel Δ [95% CI] | p | d_z |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg | 12 | +0.42 [−0.25, +1.17] | 0.426 | +0.30 | +0.42 [−0.17, +1.00] | 0.312 | +0.39 |

Per-mode means:

| Mode | n | Total [95% CI] | KG-relevant [95% CI] |
|---|---:|---:|---:|
| baseline | 12 | 10.00 [9.00, 11.08] | 5.17 [4.58, 5.75] |
| kg | 12 | 10.42 [9.75, 11.08] | 5.58 [5.00, 6.08] |

**The pre-registered significance criterion (KG-rel Δ > 0, p < 0.05) is not met.**
The point estimate is positive and of the same magnitude as the exploratory
estimate, but the confidence interval includes zero.

---

## Comparison to the exploratory run

| | Exploratory (n=40) | Clean confirmatory (n=12) |
|---|---:|---:|
| Total Δ | +0.62 | +0.42 |
| Total p | 0.054 | 0.426 |
| Total d_z | +0.33 | +0.30 |
| KG-rel Δ | +0.60 | +0.42 |
| KG-rel p | 0.007 | 0.312 |
| KG-rel d_z | +0.47 | +0.39 |

Direction is preserved on both endpoints and the standardised effect sizes are
close (0.33 → 0.30 and 0.47 → 0.39). The mild attenuation is expected: an
effect first estimated on the data used to find it is biased upward.

## The confirmatory test was underpowered by construction

Resampling 12 PRs at a time from the 40 observed per-PR paired differences and
running the same exact sign-flip permutation test gives the probability that
this design would reach p < 0.05 *if the exploratory effect is exactly real*:

| Endpoint | Power at n = 12 |
|---|---:|
| Total | 8% |
| KG-relevant | 16% |

So a null was the overwhelmingly likely outcome (84–92%) whether or not the
effect exists. **This test cannot falsify the effect, and its p-value carries
almost no evidential weight.** Its point estimate is the informative part, and
that replicates.

The honest reading: the held-out data is consistent with a small positive KG
effect of roughly d_z ≈ 0.3–0.4, and is not powerful enough to confirm or
refute it. Any claim of "failed replication" from n = 12 is a
power failure, not evidence of absence.

## Judge-level detail

Per-judge yes rates (baseline → kg):

| Judge | baseline | kg |
|---|---:|---:|
| `gpt-4o-mini` | 39.0% | 41.3% |
| `gpt-4o` | 38.7% | 38.7% |
| `gemini-2.5-flash` | 42.7% | 45.3% |

Note that on this held-out set the KG gain comes from `gpt-4o-mini` and
`gemini-2.5-flash`, while `gpt-4o` — the judge sharing a family with the
generator — records exactly no difference. That is the opposite of the pattern
in `results/JUDGE_LEAVE_ONE_OUT.md`, where `gpt-4o` carried most of the
headline effect. Self-preference therefore does not explain the effect seen
here, though the small n makes this observation suggestive rather than solid.

Inter-judge agreement: κ = 0.710 (`gpt-4o-mini`/`gpt-4o`), 0.692
(`gpt-4o`/`gemini`), 0.539 (`gpt-4o-mini`/`gemini`); n = 600 cells per pair.

---

## Why the May 2026 run was discarded

`experiments/2026-05-14_confirmatory_kg/RESULTS.md` reported KG-rel Δ = −0.750
and Total Δ = −2.250 (p = 0.046, significantly *negative*) and concluded the
effect did not replicate. That run differs from the headline in five ways, four
of which were undisclosed:

1. **Wrong PR context fed to the judges (fatal).** It judged through
   `scripts/evaluate_reviews.py`, whose `load_pr_context` resolved
   `pr<N>_evidence.json` against `data/luca_prs_v2`. The held-out set numbers
   its PRs 1..12 and therefore collides with the canonical dataset, so every
   review was scored against a *different pull request's* title and body — e.g.
   the review of grafana#124912 "apply security patches" was graded against
   godot#73144 "Replaced OpenXR operating system alert dialog…". This penalises
   the KG arm asymmetrically: KG reviews name concrete files and symbols from
   the PR they actually read, which look irrelevant against an unrelated PR
   description, whereas a generic baseline review looks less wrong. This is a
   plausible mechanism for the spurious significant negative on total score.
2. **Judge panel excluded `gpt-4o`.** It used
   `gemini-2.5-flash` + `claude-sonnet-4`. Per
   `results/JUDGE_LEAVE_ONE_OUT.md`, dropping `gpt-4o` from the panel is by
   itself enough to remove most of the headline effect.
3. **Different generator.** Gemini 2.5 Flash, not gpt-4o (OpenAI quota was
   exhausted at the time). This was disclosed.
4. **Different prompt and KG context format.** It used the bespoke templates in
   that experiment's own `generate_reviews.py`, not the v2 prompt or
   `prnote.note.format_kg_context`.
5. **Different scoring denominator.** It scored a 5-item refined subscale
   {F3, F4, T3, M1, C2}, then compared the resulting Δ = −0.750 directly against
   the exploratory +0.60, which is computed on the 9-item KG-relevant subscale.
   Those two numbers are not on the same scale.

Defect 1 is a code defect, now fixed: `load_pr_context` accepts a
`PR_CONTEXT_DIR` override, and the re-run sets it. Verified — without the
override PR#1 resolves to "Replaced OpenXR operating system alert dialog…";
with it, to "apply security patches".

---

## Reproduction

```bash
source load_env.sh
python3 scripts/rerun_confirmatory_heldout.py --dry-run   # plan + cost
python3 scripts/rerun_confirmatory_heldout.py --workers 6 # ~$3, ~4 min
python3 scripts/bootstrap_stats.py \
  --in  results/checklist_evaluation_llm_multi__confirmatory_clean.json \
  --out-json results/BOOTSTRAP_STATS_confirmatory_clean.json \
  --out-md   results/BOOTSTRAP_STATS_confirmatory_clean.md \
  --label "Clean confirmatory re-run — 12 held-out PRs, headline config"
```

Both stages are idempotent: generation skips reviews that exist, judging skips
per-review cache entries that exist, so a re-run costs nothing. Actual wall
clock was 195 s at 6 workers; actual reviews 24, judge calls 72.

## Artefacts

| File | Contents |
|---|---|
| `experiments/2026-05-14_confirmatory_kg/reviews_clean/pr{1..12}_{baseline,kg}.md` | 24 generated reviews |
| `results/checklist_evaluation_llm_multi__confirmatory_clean.json` | full per-judge panel detail |
| `results/CHECKLIST_EVALUATION_REPORT__confirmatory_clean.md` | panel summary |
| `results/BOOTSTRAP_STATS_confirmatory_clean.{md,json}` | CIs + permutation tests |
