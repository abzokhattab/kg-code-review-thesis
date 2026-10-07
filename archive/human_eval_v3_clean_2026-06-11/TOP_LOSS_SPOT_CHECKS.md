# Top-loss spot checks — PR15 and PR43

The four PRs that drove the parity drop in the joern arm:

| PR | Lang | body chars | base | buggy joern | parity joern | joern Δ | parity−base |
|---:|---|---:|---:|---:|---:|---:|---:|
| 15 | TypeScript | 378  | 3 | 6 | 3 | -3 | 0 |
| 21 | Java       | 625  | 6 | 7 | 5 | -2 | -1 |
| 31 | Python     | 743  | 2 | 5 | 3 | -2 | +1 |
| 34 | TypeScript | 1208 | 4 | 5 | 3 | -2 | -1 |
| 43 | Python     | 380  | 5 | 7 | 5 | -2 | 0 |

PR31 is already covered in `PR31_SPOT_CHECK.md`. This file walks
PR15 (largest single-PR drop, joern arm dropped to baseline) and
PR43 (parity ties baseline despite the buggy run scoring +2 above).

If the discussion chapter wants concrete failure-mode examples beyond
PR31, these are the next two.

---

## PR15 — grafana/grafana #78399, "Refactor TimeRangePicker for aria-label selectors"

### Setup

- Language: TypeScript
- Body: 378 chars, conversational ("Hopefully things should be a bit
  better now :)"), describes the refactor at a high level + one
  inline image link.
- The KG context (caller list, dependents) is identical between
  buggy and parity runs. The only delta is presence of the body in
  the parity prompt.

### Buggy joern review (KG-rel = 6)

Three specific Problems:
1. Inconsistent Selector Usage
2. Localization Gaps
3. Potential UI Regression

Evidence section lists **5 file:line citations**:
- `CalendarHeader.tsx:24`
- `TimeRangeContent.tsx:116`
- `de-DE/grafana.json:1252`
- `es-ES/grafana.json:1258`
- `CalendarFooter.tsx:1-44`

### Parity joern review (KG-rel = 3)

Three Problems with similar headings but more cautious wording:
1. **Accessibility Concerns** ("might impact accessibility if not handled correctly")
2. **Incomplete Localization**
3. **Potential UI/UX Regression** ("might affect... especially if not thoroughly tested")

Evidence section lists **3 file:line citations** — one of the
locale-files cites is dropped, the CalendarFooter cite is dropped.

### What the body did

The body mentions IconButton refactoring as a side-feature ("ended up
being a rats nest of adjusting the design"). The parity review
**reframed** Problem 3 from "removal of custom styles" (a code-grounded
observation) to "Change from Button to IconButton" (a body-grounded
observation), then hedged it with "might not be consistent across
different themes". The reviewer rubric punishes that kind of hedging
under T3 (specific anchoring) and Q2 (line-numbered citations).

**Per-judge breakdown** (gpt-4o-mini for the parity review): F3, F4,
T3, M1, C2 are all 0; the "might"-type framing in Impact and
Recommendation costs all the optional KG-rel points.

### Reading

The body content **redirected** the joern review toward generic
visual-regression framing rather than the structural issues the buggy
review nailed. This is consistent with neither pure "redundancy" nor
pure "interference-via-length" — the body length (378) is small.
What changed is that the body told the model "this is a refactor,
hopefully no regressions", and the model adopted that frame.

This is a **content-specific effect** — the body biased the model
toward a softer reading of the same code change. It is not predictable
from body length.

---

## PR43 — scikit-learn/scikit-learn #33964, "MNT move test on pandas sparse dataframe"

### Setup

- Language: Python (sklearn)
- Body: 380 chars, technical ("`check_array` is part of
  `sklearn.utils.validation`. Currently, the only test for the
  warning ... is in linear models. This PR moves the test where it
  belongs.")
- KG context identical between buggy and parity.

### Buggy joern review (KG-rel = 7)

Two Problems, both pointed at integration risk in the new test
location. Evidence section cites both files with line ranges.
Recommendations include "additional tests that cover edge cases" and
"review dependencies and ensure that any changes in sparse dataframe
handling are reflected in tests across all dependent modules".

### Parity joern review (KG-rel = 5)

Two Problems with near-identical headings. Evidence section is
similar. Recommendations are also similar but slightly more abstract
("Add integration tests that verify the behavior of `check_array`
with sparse DataFrames across different modules" vs the buggy version
which named the test functions involved).

### What the body did

The body explicitly says "this PR moves the test where it belongs".
The parity review picks up that framing and softens its concerns:
"may not be adequately covered" instead of "may not align with the
intended validation checks". The body reassured the reviewer.

This is a different mode of body interference than PR15:
- PR15: body redirected framing from structural to UX-visual.
- PR43: body reassured the reviewer, softening the concern register.

Both reduce KG-rel scores but neither is "the body content
substitutes for the KG context" in the redundancy sense.

---

## Implication for the thesis discussion chapter

The mechanism by which the body lowers the joern arm's score is **not
length-based** (Pearson r=+0.24 across 35 PRs in
`PER_LANGUAGE_CI_AND_FALSIFICATION.md` §2). It is **content-specific**
and varies by PR:

- Some bodies (PR15) introduce framing the model adopts, displacing
  structural review framing.
- Some bodies (PR43) reassure the reviewer, softening the concern
  register.
- Some bodies (PR31, see `PR31_SPOT_CHECK.md`) trigger fabrication
  in the Traceability section.

A clean single-line mechanism is **not available** at this n. What is
available: parity reduced the joern arm's mean KG-rel by 0.34, and
spot-checks of the largest drops show plausible per-PR mechanisms
that are heterogeneous, not uniform.

**Recommended language for the discussion chapter:**

> "The parity correction reduced the joern arm's mean KG-rel by 0.34
> points without measurably changing baseline scores. The simplest
> hypothesis (body length crowds out KG-driven framing) is not
> supported by a per-PR regression of joern-arm drop on body length
> (Pearson r = +0.24, n = 35, p = 0.165). Spot-checks of the
> top-loss PRs (15, 31, 34, 43) instead show heterogeneous
> content-specific failure modes: in some cases the body
> redirects the model toward a non-structural frame (PR15), in
> others it reassures the model and softens concern register
> (PR43), and in others it triggers fabrication when the body does
> not name a reviewer (PR31). The parity drop should therefore be
> reported as an observed effect without a confirmed mechanism."
