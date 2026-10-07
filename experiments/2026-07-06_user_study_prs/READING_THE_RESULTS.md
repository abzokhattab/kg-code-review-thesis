# How to read this study's results — personal notes

**This file is not part of the study record.** It is a plain-language explainer
written to re-orient after time away from the project. It is deliberately not
referenced by `ANALYSIS_PLAN.md`, not listed in `thesis-context/CODE_INDEX.md`,
and no analysis decision depends on it. The binding documents are
`ANALYSIS_PLAN.md` (what will be done, fixed in advance) and
`POWER_ANALYSIS.md` (how many raters are needed). If this file ever disagrees
with those, they are right and this is stale.

---

## What the study is for

The thesis asks whether giving an AI code reviewer a map of the repository
makes its reviews better. The map records which file calls which function.

An earlier experiment answered this with AI judges, and the answer was a
qualified yes: the map helped on the criteria about naming affected code, but
did not make reviews better across the board. Retrieval (RAG) won on overall
coverage instead.

Using AI judges to score AI reviews is the weak point of that result. This
study shows the same reviews to humans, so the judges' verdict can be checked
against people.

## What a rater does

Six pull requests. For each one, two reviews side by side, labelled A and B,
with no indication of which is which.

- One review was written from the diff alone.
- One was written with the repository map as well.

The rater answers six questions per PR about which review is better, plus one
overall preference and a difficulty rating.

## The difference between the two reviews, concretely

From PR 1 in the study — a change to `prepare_body` in the `requests` library.

The diff-only review lists the files it was shown:

```
src/requests/models.py:596-600
tests/test_requests.py:2073-2088
```

The map-based review lists those plus the files that call the changed
function:

```
src/requests/models.py:596-600
tests/test_requests.py:2073-2087
src/requests/sessions.py     <- calls prepare_body
src/requests/api.py          <- uses prepare_body
tests/test_requests.py       <- existing body-preparation tests
```

The pull request never touched `sessions.py` or `api.py`. They are where the
change could cause breakage, and the diff-only reviewer had no way to know
they exist. That gap is the entire treatment.

## The number the study produces

Each pick is scored: map-based review = 1, diff-only = 0, "equal"/"both"/
"neither" = 0.5. Average over a rater's six PRs, then average over raters.

**0.5 (50%) is the no-difference line.** With two reviews, someone who cannot
tell them apart lands at 50% by chance. Above 50% means the map-based review
is being preferred.

Worked example for one rater on one question:

| PR | picked |
|----|--------|
| 1 | map-based |
| 2 | map-based |
| 3 | diff-only |
| 4 | map-based |
| 5 | equal |
| 6 | map-based |

Four clear picks for the map, one against, one tie: `(1+1+0+1+0.5+1)/6 = 0.75`.

## The six questions and what to expect

Only the first is the confirmatory result. The rest provide context, and three
of them act as controls.

The expected values below are not guesses. They come from measuring what the
twelve review texts actually contain, arm by arm, across all six PRs. Where the
two arms differ mechanically, the question should move; where they are matched,
it should not. The counts are crude lexical proxies — counting the word "test"
is not the same as judging how well a review addresses testing — so they
indicate direction, not magnitude.

| id | question | measured difference (kg − baseline) | expect |
|----|----------|---|---|
| **F3\*** | Which review better names the functions/files this change could affect? | **+2.5 files, kg higher in 6/6** | **0.60–0.70** |
| T3 | Which better points to tests? | +5.2 mentions of "test", kg higher in 6/6 | 0.55–0.65 |
| F2\* | Which better describes how the code could fail? | −1.5 failure words, kg higher in only 1/6 | 0.45–0.55 |
| Q5 | Which better explains *why* something is a problem? | ±0.0 causal connectives | ~0.50 |
| R1 | Which better comments on code clarity? | −0.5 readability words (both near zero) | ~0.50 |
| C6 | Which better covers the important issues? | −0.2 numbered points, tied in 5/6 | ~0.50 |
| — | Overall preference | — | ~0.50 |

### F3\* — names the affected code (the primary result)

Distinct files named per review, baseline → kg: `2→4, 3→5, 2→5, 2→4, 2→4, 3→7`.
The kg review names more in every single PR, averaging 4.8 against 2.3.

This is the treatment itself, so this is the one question with a strong
mechanical basis for moving. **0.60–0.70 is the target.** Below 0.55 means
raters did not perceive a difference that is unambiguously present in the text.
Above 0.80 is discussed under "reading the result" below.

### T3 — points to tests (a second, weaker treatment effect)

Mentions of "test", baseline → kg: `6→10, 8→13, 8→13, 8→13, 7→10, 6→15`. Higher
in 6 of 6. Distinct test files named: higher in 3 of 6, tied in the other 3,
with one PR going `1→4`.

**T3 is not a control.** The kg review's file list includes test files, so
naming more files spills into this question by the same mechanism as F3\*.
Expect a real but smaller lean, roughly **0.55–0.65**. A T3 result close to
F3\*'s is coherent; T3 exceeding F3\* would be odd, since the file-count gap is
larger and more direct on F3\*.

### F2\* — describes failure cases (expected flat, possibly negative)

Failure-related words, baseline → kg: `2→3, 8→8, 10→1, 1→1, 6→5, 1→1`. The
*baseline* is higher on average (4.7 vs 3.2) and the kg review leads in only one
of six PRs, with one PR dropping sharply from 10 to 1.

So there is no content basis for a kg preference here. Expect **0.45–0.55**, and
a mild lean toward the baseline would be unsurprising and honest. A strong kg
result on F2\* is a warning sign, because the text does not support it — that
would point to raters favouring one review generally rather than answering the
question asked.

### Q5 — explains why (control)

Causal connectives ("could cause", "because", "leading to", "resulting in"):
1.3 per review in both arms, identical to one decimal place. The two arms are
matched. Expect **~0.50**. Movement here has no available explanation.

### R1 — comments on code clarity (control)

Readability vocabulary, baseline → kg: `4→0, 0→1, 1→1, 1→2, 1→0, 0→0`. Both arms
average roughly one word per review, i.e. neither says much about clarity at
all. A repository map carries no information about naming or structure, so
there is no mechanism by which it could help. Expect **~0.50**. This is the
cleanest control of the six.

### C6 — covers the important issues (control)

Numbered points per review: 7.3 baseline against 7.2 kg, tied in 5 of 6 PRs
(`8→7, 8→8, 7→7, 7→7, 7→7, 7→7`). The reviews are matched in breadth by
construction. Expect **~0.50**.

### Overall preference

Expect **~0.50**. See "why a boring overall result is the good one" below.

### The pattern in one line

**F3\* clearly up, T3 mildly up, everything else flat.** Both movers share one
mechanism — the kg review names more files, and some of those files are tests.
The three questions with no mechanism available stay at 0.50. That is a result
with an explanation attached to every part of it.

## Per-PR expectations

The six stimuli are not equivalent. They differ both in how many extra files
the kg review names and — more importantly — in how well those extra files are
actually connected to the change, according to the frozen answer key
(`build_answer_key.py`). The relationship labels below are the key's own:
`changed` (the PR edits this file), `direct` / `indirect` (call paths to the
changed code), `related`, and `exists` / `type_only` / `module_only`, which
mean the file is real but no connection to this change was established.

**Read per-PR numbers with caution.** Each PR is judged by every rater, so a
per-PR rate rests on ~35 observations and carries a 95% interval of roughly
±0.16. These are directional expectations, not predictions to be tested.

| PR | repo | kg extra files | grounding of the extras | F3\* expectation |
|----|------|---|---|---|
| 101 | requests #7433 | +2 | both `indirect` — real call paths | 0.60–0.70 |
| 102 | flask #5637 | +2 | 3 refs with **no established link** | 0.50–0.60 |
| 103 | click #3493 | +3 | 2 `direct` callers, 1 module-only | **0.65–0.75** |
| 104 | requests #7328 | +2 | both `indirect` — real call paths | 0.60–0.70 |
| 105 | flask #5799 | +2 | 1 `direct`, 1 module-only | 0.55–0.70 |
| 106 | click #3578 | **+4** | 4 refs with **no established link** | see below |

### PR 101 — requests, `prepare_body` stream detection

kg names `sessions.py` and `api.py` on top of the two changed files; both are
`indirect` call paths to the modified function. A clean stimulus: the extra
references are genuinely where breakage would surface.

Watch R1: the baseline uses four readability words here against the kg's zero
(the only PR where either arm says much about clarity), so R1 may lean baseline
on this PR alone.

### PR 102 — flask, `request.trusted_hosts`

The weakest F3\* stimulus. kg names two more files, but the key marks three of
its references as having no established link (`logging.py`, `sessions.py`,
`test_instance_config.py`). A rater who checks will find extra names that are
not obviously relevant, so a muted result here is the honest one — and a strong
kg win would be worth examining.

Failure content is tied 8–8, so expect F2\* near 0.50.

### PR 103 — click, empty bytes in `echo`

The best-grounded stimulus: two of the kg's extras are `direct` callers, the
strongest relationship class in the key. This is where the treatment should
show most clearly, so F3\* here is the single most informative per-PR number.

**But expect F2\* to favour the baseline on this PR**, and possibly strongly.
The baseline carries 10 failure-related words against the kg's 1 — the largest
per-PR gap anywhere in the stimulus set, in the baseline's favour. If raters
prefer kg on F2\* here, they are not answering the question from the text.

### PR 104 — requests, redirect history self-reference

Structurally the twin of 101: +2 files, both `indirect`, nothing unestablished.
Everything else is near-tied (failure 1–1, causal 1–1, length 226 vs 217, the
kg review actually being shorter). A clean, unremarkable stimulus, and useful
precisely because nothing except the file list distinguishes the arms.

### PR 105 — flask, `stream_with_context` for async views

Mixed grounding: one `direct` reference, one module-only. Expect a middling
F3\* result. A separate review of diff complexity flagged this PR as the
heaviest of the six to read — it combines a docstring rewrite with non-obvious
async control flow — so its difficulty ratings are worth checking against the
other five, and a lower F3\* here may reflect reading burden rather than the
stimulus.

### PR 106 — click, double-bracketing of choices — **the diagnostic PR**

This one carries the most information about whether the study measured
perception or counting.

It has the **largest file-count gap** (3 → 7, the biggest surface cue in the
set) and simultaneously the **weakest grounding**: four of its references have
no established link (`parser.py`, `test_context.py`, `test_defaults.py`,
`test_shell_completion.py`). It also has the largest jump in test mentions
(6 → 15) and is the longest kg review (288 words vs 239).

So the two readings pull apart cleanly here:

- **If F3\* on 106 is the highest of the six** — the result tracks the number of
  filenames, not their relevance. That is the counting-heuristic reading, and
  106 is where it shows.
- **If F3\* on 106 is unremarkable while 103 and 101 are strong** — raters
  responded to *which* files were named rather than how many. That is the
  result the thesis wants, and it is much harder to attack.

This is also why the pre-registered C1 check (`ANALYSIS_PLAN.md`) matters more
than its own description suggests. C1 correlates per-PR preference against the
file-count delta and is dismissed there as having little leverage. But in this
stimulus set the file-count delta runs *opposite* to reference quality — 106
has the most extra files and the worst grounding, 103 has fewer and the best —
so a positive correlation is not a neutral finding. It would be evidence for
the counting reading.

## Reading the result when it arrives

The question to ask is not "is the number big" but "is there an explanation
for this pattern".

**F3\* around 0.65, T3 a little above 0.50, the rest flat.** The effect sits
where the mechanism predicts and nowhere else. This is the result that supports
the thesis, and it matches what the AI judges found — the map changes what a
review points at, not how good it is overall.

**F2\* strongly favouring kg.** Specifically worth watching, because the
baseline reviews contain *more* failure-case content than the kg reviews. A
clear kg win here cannot be explained by what is in the text, so it would
suggest raters are expressing a general preference for one review rather than
answering each question separately. Treat it as evidence of a halo effect and
check it against the free-text reasons.

**F3\* up and overall usefulness up too.** A larger apparent win, but it
contradicts the earlier experiment, where the map did not win on overall
quality. Humans and judges disagreeing needs an explanation that is not
currently available.

**Everything at 0.75–0.85.** Looks like the strongest outcome and is the most
worrying. Nothing explains why a map would improve perceived code clarity. The
likelier cause is that raters found a way to tell the arms apart: the map-based
review names more files in all six PRs (2v4, 3v5, 2v5, 2v4, 2v4, 3v7), which is
visible without reading. Review *length* is not a usable cue — the two arms are
within 6% on average and the map-based review is the shorter one on two of the
six PRs — but file count is.

**Everything near 0.50.** A clean null. The extra references are real but not
salient to a human reading six PRs in one sitting. `ANALYSIS_PLAN.md` already
commits to reporting this as a boundary result rather than re-running with new
stimuli.

## Why a boring "overall" result is the good one

It is the difference between two claims:

- *"Map-based reviews are better."* Broad, and contradicted by the earlier
  experiment.
- *"Map-based reviews ground themselves in the right code."* Narrow, specific,
  and consistent with everything else in the thesis.

The second is the defensible claim, and a flat overall-preference number is
what makes it precise rather than vague.

## Participants

Background collected: primary occupation (student / researcher / junior /
mid-level / senior developer / other), years of programming experience, and
how often the person reviews pull requests.

A developer-majority sample helps. The closest comparable study (Tufano et al.)
excluded students without industrial experience on the grounds that industrial
experience is essential in code-review research; a sample that is mostly
working developers sidesteps that objection.

Across seniority the result to hope for is **flatness** — juniors, mid-level
and seniors all landing in a similar range. Seniors are the ones who can judge
whether `sessions.py` is genuinely at risk, so if the preference holds among
them, it survived scrutiny. A pattern where juniors strongly prefer the
map-based review and seniors do not would suggest the longer file list is
impressing people who cannot check it.

With around 35 raters spread over six occupation categories there are only
about six people per category, which is enough for a headcount table and
nothing more. Any actual comparison uses a single split on years of
experience, and per `ANALYSIS_PLAN.md` that split has to be fixed in writing
before recruiting to count as anything more than exploratory.
