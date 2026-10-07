# Review readability pass — draft, 2026-08-01

**Trigger:** pilot rater (2026-07-23) reported the study is too heavy:
couldn't finish, "the reviews ramble", questions feel repetitive.

**Diagnosis:** the heaviness is the *template*, not the content. All 12
reviews share a rigid 5-section scaffold that states each point up to
three times (Problem -> Impact -> Recommendation) behind bold jargon
labels ("Integration Risk:", "API Contract Violation:").

## What this draft does (rules R1-R4, `simplify_reviews_draft.py`)

Uniform, direction-blind, defined on the template surface — the same
class of operation as the 2026-07-13 surface normalization:

- R1 drop the boilerplate title line
- R2 drop the "**Scope:**" line (restates the PR description the UI
  already shows above the reviews)
- R3 strip bold jargon labels from Problem/Impact bullets (the sentence
  restates the label in every instance); keep the plain action labels
  in Recommendations (Fix/Tests/Risks)
- R4 plain-language section headers ("Impact" -> "What could go wrong")

No sentence reworded, added, or removed.

## Verification (all passed)

- File/line reference sets identical before/after in all 12 files (the
  single diff was a bare `sessions.py` inside a deleted Scope line; the
  full `src/requests/sessions.py:182` reference survives in Evidence).
- All 38 curated answer-key markers survive verbatim.
- Reduction symmetric across arms: baseline −12.7%, kg −12.8%.

## Status

**DRAFT ONLY** — output in `simplified_reviews/`, live study untouched.

## To deploy (if approved)

1. Copy simplified files over `experiments/2026-07-06_user_study_prs/reviews/*.md`
2. Re-run `assemble_study_draft.py`, sync `pilot/study_data.json`
3. Bump study `version`; note the amendment in ANALYSIS_PLAN.md
   (instrument changed before real data collection; supervisor + 1 pilot
   run used the old surface — both excluded as pilots)
4. Re-run the blinding audit on the rebuilt data

## Rejected alternative

Free LLM paraphrase of the reviews: would make stimuli no longer the
system's outputs, risks asymmetric changes to the treatment content,
and would invalidate the marker/highlight layers. Not worth it for the
~30% further compression it might buy. The bigger remaining burden cuts
are UI-level anyway: collapse the diff by default, compact criterion
labels, mark the "why" box optional, neutralize the file-reference
instruction (see 2026-08-01 chat).
