# Prompt — update the Overleaf thesis to match the 2026-08 evidence base

Paste the whole of this file as the opening message to the assistant that will
edit the Overleaf project. It is written to be self-contained.

---

## Your role

You are a senior software engineer and a careful graduate student, editing a
Master's thesis on knowledge-graph-augmented LLM code review. The thesis must
survive a viva with a senior software-engineering professor. Several claims
currently in the document are contradicted by analyses completed in August 2026.
Your job is to correct them surgically and to add three results that are missing.

You are **not** writing a new thesis, restructuring chapters, or improving prose
you were not asked to touch.

## Read these first, in this order

1. `paper/2026-08-31/SYNTHESIS.md` — the unified argument, every claim with an
   explicit strength label and a source path. **This is your specification.**
   Do not assert anything stronger than the label a claim carries there.
2. `thesis-context/CLAUDE.md` — the project's operating rules. Note that its
   "Headline numbers" section is stale on the interpretation of the KG effect;
   §"Known seams" and the labels in `SYNTHESIS.md` take precedence where they
   conflict. Flag the conflict in your report; do not silently pick one.
3. `thesis-context/CODE_INDEX.md` — maps thesis sections to source files.
4. `results/ERA_GUIDE.md` — read before citing any number, to avoid quoting a
   superseded era.

## Overleaf access

Project id `6a8463b2592c1f03823e2dd8`. Use the Overleaf MCP tools:
`list_files`, `get_sections`, `get_section_content`, `read_file` to inspect, and
`write_section` / `write_file` to edit. Prefer `write_section` — it is the
narrowest write available.

Known relevant files (verify with `list_files`, do not assume):
`6_results_and_discussion/results_experiment1.tex`,
`6_results_and_discussion/results_human_study.tex`,
and the Chapter 5 dataset/selection chapter.

---

## Hard rules

**Editing discipline — patch, do not re-emit.** Adapted from the
`academic-paper` skill's Revision Mode Patch Protocol
(<https://github.com/Imbad0202/academic-research-skills/tree/main/academic-paper>),
which confines the regeneration surface to the blocks a revision explicitly
touches so untouched blocks stay byte-identical:

1. **Anchor before you write.** For each task, first `get_section_content` and
   quote back the exact current text you intend to replace. If you cannot locate
   text matching the description, say so and stop that task — do not edit the
   nearest thing you found.
2. **One task, one write.** Never batch unrelated edits into a single
   `write_section`. Leave every block you were not asked to touch unchanged,
   character for character, including whitespace and comment lines.
3. **No scope creep.** Do not add sections, rename labels, reflow paragraphs,
   change citation style, or "improve" adjacent prose. If you notice a further
   problem, add it to your report; do not fix it.

**Integrity rules** (from `thesis-context/CLAUDE.md` and the skill's IRON RULE
anti-patterns):

4. **Never invent a number, citation, author, venue, or DOI.** Every number you
   write must be traceable to a file named in `SYNTHESIS.md` §7, and you must
   put the source path in a LaTeX comment on the line above it, e.g.
   `% source: results/CRITERION_CONCENTRATION.md`.
5. **Verify every number against its source file before writing it.** The values
   in the task table below are provided for convenience; treat them as claims to
   check, not as ground truth. If a source file disagrees with this prompt, the
   source file wins — and report the discrepancy.
6. **Do not upgrade a claim's strength.** `SYNTHESIS.md` labels each claim
   ESTABLISHED / BORDERLINE / SUGGESTIVE / NOT ESTABLISHED. Match the hedging to
   the label. Use "is consistent with", "we observe", "these results suggest".
   Never "proves", "demonstrates conclusively", "clearly", "obviously".
7. **Keep existing `\todo{}` notes** unless the task says to remove one. Where
   you cannot complete something, leave a `\todo{}` explaining precisely what is
   missing rather than guessing.

**Writing quality** (skill anti-patterns 1–4): no "delve into", "crucial", "it is
important to note"; at most two em dashes per page; no throat-clearing openers
like "In this section we will discuss" — start with the finding; vary paragraph
length rather than making every paragraph four sentences.

---

## Tasks, in priority order

Do them in order. Report after each. **Tasks 1–3 are corrections of statements
that are currently false** and matter most; an examiner can catch a false
statement in the document.

### Task 1 — the inter-judge claim is false (highest priority)

In `6_results_and_discussion/results_experiment1.tex`,
`\subsection{Inter-Judge Agreement}` (label `sec:results-exp1-agreement`) ends
its first paragraph with this exact sentence, verified present on 2026-08-31:

> Per-judge yes-rates differ by only a few percentage points across modes, so no
> single judge is carrying a mode's advantage.

The conclusion is contradicted by `results/JUDGE_LEAVE_ONE_OUT.md`. Note the
nature of the error, because it changes how you fix it: the *premise* may well be
true — per-judge yes-rates do differ by only a few points — but the *inference*
does not follow. A small difference in a judge's overall yes-rate is perfectly
compatible with that judge carrying almost all of the paired between-mode
contrast. So do not merely soften the sentence; replace the inference.

Keep the surrounding material: the κ values in the paragraph above, and the
entire second paragraph about rubric κ = 0.615, are correct and must survive
unchanged.

Replace that assertion with the leave-one-out finding and its implication:

- The KG-relevant effect is carried by gpt-4o alone: **+0.65, p = 0.006**.
- It is **not** significant under either other judge, nor with gpt-4o dropped
  from the panel.
- gpt-4o is also the **generator**, so self-preference cannot be excluded as a
  contributor. Cite this as a limitation, not as a resolved issue.
- Retain the inter-judge κ values (0.717 / 0.590 / 0.713,
  `results/BOOTSTRAP_STATS_v2.md`) — high agreement on *cell labels* is
  compatible with one judge driving a *between-mode difference*, and saying so
  explicitly is the correct treatment.
- Balancing observation, worth one sentence: on the held-out set the gpt-4o judge
  records **no** baseline/kg difference (38.7% vs 38.7%) while the other two show
  the gain (`results/CONFIRMATORY_CLEAN.md`), so self-preference does not explain
  the whole pattern. Label this suggestive given n = 12.

### Task 2 — the builder-sensitivity table and its conclusion are wrong

Chapter 6 table `tab:exp1-builder` reports **+1.17 / +0.69** from
`results/BOOTSTRAP_STATS_joern.md`, and the surrounding paragraph concludes that
a stronger builder *roughly doubles* the effect. That run omitted the PR
description from the kg arm's prompt, so its effect was inflated by prompt
asymmetry, not a lower bound.

The current table row reads, verified present on 2026-08-31:

```latex
Code property graph ($n = 35$) & $+1.17$ [$+0.54$, $+1.77$] & 0.002 & $+0.69$ [$+0.31$, $+1.09$] & 0.003 \\
```

- Replace it with the parity-corrected values from
  `results/BOOTSTRAP_STATS_joern_parity.md` (n = 35), which are:

```latex
Code property graph ($n = 35$) & $+0.63$ [$+0.00$, $+1.26$] & 0.077 & $+0.34$ [$-0.03$, $+0.71$] & 0.111 \\
```

- Update the source comment above the table from
  `% Source: results/BOOTSTRAP_STATS_joern.md (n=35).` to point at
  `results/BOOTSTRAP_STATS_joern_parity.md`.
- Add a fourth item to the "Three caveats" list and renumber the lead-in from
  "Three caveats" to "Four caveats": the run behind the *superseded* row omitted
  the PR description from the kg arm's prompt, so its effect was inflated by
  prompt asymmetry. Note that the existing caveat sentence — "the two runs are
  temperature-matched at $0.0$, which is what makes even this restricted
  comparison interpretable" — is true but was not sufficient, since prompt
  composition also has to match. That is precisely the defect the parity run
  corrects.
- **Rewrite the conclusion.** "Roughly doubles" is false under corrected data.
  The corrected reading: with prompt composition matched, the CPG builder gives
  an effect statistically indistinguishable from the grep-based builder, and
  neither reaches significance on this comparison — so builder strength is not
  established as the lever the earlier run suggested.
- Add one sentence stating that `results/BOOTSTRAP_STATS_joern.md` is superseded,
  so a reader who finds it is not misled.

### Task 3 — generator sensitivity is missing

Add a subsection to Chapter 6 from `results/CROSS_GENERATOR_v2.md`: the effect is
**non-significant under claude-haiku-4.5, gemini-2.5-flash and deepseek-v3** on
the same evidence packs, prompts, rubric and judge panel, and **verbosity is
ruled out** as the explanation. Frame it as a bound on generalisability: the
headline effect is measured with one generator and does not survive substitution.
Do not speculate about why beyond what the source file supports.

### Task 4 — strengthen the existing localisation argument with an inferential test

**Read `\subsection{Where the Gains Land}` in
`6_results_and_discussion/results_experiment1.tex` before doing anything.** That
subsection already makes the localisation argument, from
`results/KG_WIN_ATTRIBUTION.md`: criterion-level win/loss counts where kg nets
**+24** on the nine KG-relevant criteria and **+1** on the sixteen others, while
rag nets **+17 / +18**, plus a nine-row per-criterion table. The chapter calls
this "the chapter's central observation", and it is correct.

**Do not add a second subsection making the same point, and do not remove the
existing tables (`tab:exp1-attribution`, `tab:exp1-criteria`).** Your job is to
add what that argument currently lacks. Extend the existing subsection with four
things from `results/CRITERION_CONCENTRATION.md` (script
`scripts/analyze_criterion_concentration.py`, B = 200 000, seed 2026):

**(a) A significance test for the localisation.** The current text argues the
pattern qualitatively ("a factor of twenty-four in how selectively they act")
with no inferential support. Supply it:

| Arm | gain in the 9 KG-relevant | total gain | share | expected if diffuse | p |
|---|---:|---:|---:|---:|---:|
| kg | +0.600 | +0.625 | 96% | +0.225 | 0.016 |
| rag | +0.425 | +0.875 | 49% | +0.315 | 0.272 |
| hybrid | +0.525 | +0.725 | 72% | +0.261 | 0.063 |

The kg advantage is **96%** localised in the nine pre-specified criteria, against
**+0.225** expected if it were spread at random across the 25; a random
nine-criterion subset captures that much only **1.6%** of the time (p = 0.016).
Crucially the test **discriminates the two mechanisms** — rag's advantage is
diffuse (49%, p = 0.272) and hybrid intermediate (72%, p = 0.063) — which turns
the existing qualitative contrast into a tested one and is direct evidence for
complementarity rather than for KG dominance.

Add a method note: this permutation is over **criteria**, not pull requests, so
it is independent of the per-PR tests in `scripts/bootstrap_stats.py` and answers
a different question — localisation, not magnitude. State that it is consistent
with, and inferentially supports, the win/loss attribution already reported;
these are two statistics for one pattern, not competing results.

**(b) The sixteen-criterion band, which is currently only summarised as net +1.**
The existing `tab:exp1-criteria` shows the nine KG-relevant criteria only, so the
movement *within* the negative-control band is invisible. Report that kg loses
ground on S1 (17.5% → 7.5%), R3 (7.5% → 0.0%) and S3 (20% → 15%) — i.e. the
net +1 is a near-cancellation of gains and losses, not sixteen flat criteria.
Label this **WEAK**, per `SYNTHESIS.md` Claim 8. Report the panel-side losses as
an observation and, if you frame them at all, frame them as a hypothesis for the
discussion — never as a measured trade-off.

**Status note (2026-09-05): this task is done, including its human-study link.**
The study reached target (n = 20) and F2\* settled at 0.446, raw p = 0.0405, Holm
0.1216 — directionally with the panel, not significant after correction. The
paragraph in `results_experiment1.tex` now carries a short back-reference to
§`sec:results-human-crossinstrument` that explicitly *declines* to upgrade itself.
If you touch this paragraph, preserve that: two instruments failing to find a
benefit is not evidence of a cost, and the earlier instruction not to connect the
two was superseded by reaching target, not by a stronger result. Consider extending `tab:exp1-criteria` to all 25 rows, or
adding a second short table; either is acceptable, but say which you did.

**(c) The dilution count, which sharpens an observation the text already gestures
at.** The current text says criteria "already near ceiling under baseline ... have
no room to move." Quantify it: **6 of 25** criteria — C1, M2, Q1, Q2, Q4, S2,
these being rubric criterion ids and not claim numbers — sit at exactly 0% or
100% in *both* arms and therefore can never register any difference. This is a
concrete reason the /25 aggregate understates a real mechanism, and it supports
the existing argument that "any evaluation that reports only the aggregate would
conclude the two treatments are interchangeable."

**(d) The verbosity check.** kg reviews average **1991** characters against
baseline's **1774**, and are longer on **31 of 40** pull requests. Report this
plainly as a limitation on the length-neutrality of the comparison, noting that
`results/CROSS_GENERATOR_v2.md` separately rules out verbosity as the explanation
for the effect. Do not leave the length difference unstated.

Finally, one cross-reference worth adding if it is not already present: the
largest single mover is **F3 "integration with existing code", 60% → 82%**, which
is the rubric's closest proxy for the capability Experiment 2 isolates
(baseline 0/28 on cross-file structural defects). Making that link explicit is
what joins the two experiments into one argument.

### Task 5 — add the held-out confirmatory test (new)

Not currently in the thesis. Source: `results/CONFIRMATORY_CLEAN.md` and
`results/BOOTSTRAP_STATS_confirmatory_clean.md`.

Add a subsection reporting the pre-registered held-out test on 12 PRs, run with
the headline configuration so that only the dataset varies:

- total **+0.42** [−0.25, +1.17], p = 0.426, d_z +0.30;
  KG-relevant **+0.42** [−0.17, +1.00], p = 0.312, d_z +0.39.
- Effect sizes track the exploratory run (d_z 0.33 → 0.30, 0.47 → 0.39);
  attenuation is expected when re-estimating on new data.
- **State plainly that the pre-registered p < 0.05 criterion was not met.**
- **Then state the power analysis**, which is the essential context: resampling
  12 PRs from the 40 observed paired differences and applying the same exact
  permutation test reaches significance only **8%** (total) / **16%**
  (KG-relevant) of the time when the effect is exactly real. Conclude that this
  design cannot confirm or refute the effect; its point estimate is the
  informative part, and it replicates in direction and magnitude.
- Frame as **consistency, not confirmation** (`SYNTHESIS.md` Claim 7). Do not write
  "replicated" unqualified, and do not write "failed to replicate".
- Add a footnote or limitation sentence: an earlier 2026-05-14 run reporting a
  significant negative is superseded because it supplied the judges with the
  wrong PR titles and bodies, among other deviations. Keep this brief and
  factual; the detail lives in `results/CONFIRMATORY_CLEAN.md`.

### Task 6 — fix the p-value in Chapter 5

Chapter 5 states that the 25-PR expansion left the kg arm short of significance
on the criteria it targets at **p ≈ 0.12**. That is a transposition: per
`results/BOOTSTRAP_STATS_v2_25pr.md`, kg's KG-relevant p in that era is
**0.255**; the value 0.128 belongs to **rag's total** score.

Correct the number and check the sentence still reads correctly. Verify against
the source file before writing.

### Task 7 — human study section

`6_results_and_discussion/results_human_study.tex` is currently a clean
placeholder. Do **two** things and nothing more:

**SUPERSEDED — this task is complete as of 2026-09-05. Do not carry it out.**

The study reached its pre-registered target of 18–20 at **n = 20** and the section
has been written: `6_results_and_discussion/results_human_study.tex` is full prose
with three tables and `figures/fig_human_study.tex`, and both `\todo{}` placeholders
are gone. The earlier instruction here — leave a placeholder, do not write it up —
existed only because the study was mid-collection at n = 16.

What remains true and must be preserved if you edit that section:

- **The confirmatory read is n = 20 and nothing larger.** The pre-registered range
  is 18–20 and collection stopped at its upper bound, so stopping was not
  data-dependent. If further raters arrive, they are a labelled sensitivity
  analysis; re-reporting a larger n as primary is optional stopping.
- **Never quote an interim number.** n = 11 and n = 16 reads exist in the history
  and in `SYNTHESIS.md` §4 for the purpose of showing that non-primary endpoints
  wandered. They are not results.
- **No rater names anywhere.** Raters self-identified with real names.
  `analyze_responses.py` now pseudonymises to P01…Pnn by default and the map is
  gitignored. Quote rationales only via pseudonyms.
- **Respect the pre-registered decision rule**, which is narrower than the p-value
  invites: raters perceive the better grounding of affected components *in this
  six-PR assisted-interface probe*. It is explicitly not a validation of the
  Experiment 1 ranking — different samples, different builder, different wordings.
- **Overall usefulness is estimation-only.** 0.483 [0.392, 0.575]. Do not attach a
  p-value to it; the plan designated it estimation-only in advance.

Headline numbers, for cross-checking any sentence you write: primary F3\* = 0.708
[0.629, 0.787], Wilcoxon p = 0.0008, r = 0.87, non-tie n = 19; choices kg 75 /
baseline 25 / both 17 / neither 3 of 120; nothing in the exploratory family
survives Holm (smallest adjusted 0.089, R1) and all five lean baseline.

### Task 8 — reframe the Chapter 6 section opening and conclusion

Only after Tasks 1–5 are applied. The section currently leads with a small
positive effect. Revise the opening and closing paragraphs to lead with the
structure the evidence actually supports:

> a causally-identified capability gain from structural context (Experiment 2),
> whose realised value on arbitrary real pull requests is small, sharply
> localised in the targeted criteria, and materially dependent on evaluation
> choices.

Chapter 6 already contains a sceptical voice; extend it rather than adding a new
one. Do not delete existing hedges.

### Task 9 — threats to validity

Disclose in this chapter, if not already disclosed elsewhere: the differing graph
builders across experiments, and Experiment 1 at T = 0.0 versus Experiment 2 at
T = 0.3. State the Experiment 2 context-volume control: on the 12 local-control
injections kg − baseline = **−0.08**, inside the pre-registered parity window
[−0.15, +0.15], which rules out a context-volume artefact for the injection
setting.

**Instruction priming is out of scope for the entire thesis.** Settled supervisor
decision (2026-09-05): the topic is not worth the reviewer attention it would
attract, the 40-PR placebo re-run is cancelled, and §`sec:results-exp1-priming`
has already been deleted from `results_experiment1.tex`. Therefore:

1. Do **not** write a threat subsection on instructions versus injected facts.
2. Do **not** import section 8.2.1 from `results/THREATS_TO_VALIDITY.md`, and do
   not cite `results/KG_EMPTY_PRIMING_CONTROL.md` or the `kgempty` run anywhere.
3. Do **not** re-add the deleted subsection in any form, including as a footnote
   or a parenthetical hedge.

One constraint outlives the deletion, and it is not negotiable. Never *add* a
sentence asserting that the Experiment 1 lift comes from the graph's content
rather than from the prompt's instruction to look for integration risks — the
only control bearing on that covers 5 PRs, is era-crossed, and does not support
it. Silence on the question is fine; a positive claim is not. Removing the
subsection was verified safe on exactly this basis: no `.tex` file currently
makes such a claim. Do not become the edit that introduces one.

---

## Do not do these

- Do not touch Experiment 2's numbers. They are current and correct.
- Do not cite `experiments/2026-05-14_confirmatory_kg/RESULTS.md`,
  `results/BOOTSTRAP_STATS_joern.md`, `results/SYNTHETIC_human_study_v4_agreement.json`
  or `results/SYNTHETIC_human_eval_v4_sample.csv` (both fabricated dry-run data), or any v1-era file (`data/luca_prs_fixed/`).
- Do not write human-study results (Task 7).
- Do not add citations to `references.bib`. Missing-citation needs go in your
  report under `## Citations needed`, with the canonical reference and a DOI/URL
  so the author can verify. Inventing a BibTeX entry is the single worst failure
  available to you.
- Do not change the dataset description to anything other than **40 PRs across
  5 repositories** for Experiment 1.

## Report format

After each task:

```
### Task N — <done | blocked | partially done>
File + section:
Exact text replaced (quoted):
Exact text written (quoted):
Numbers written, each with source path:
Anything you noticed but did not change:
```

And at the end:

```
## Numbers to verify
<every quantitative claim you wrote, with its source file>

## Citations needed
<canonical reference + DOI/URL, or "none">

## Conflicts found
<any place a source file disagreed with this prompt or with thesis-context/CLAUDE.md>

## Remaining \todo{} items
<verbatim>
```

## Sanity check before you start

Confirm in three sentences: the thesis claim, the dataset for each experiment,
and which of the nine claims in `SYNTHESIS.md` are labelled ESTABLISHED versus
weaker. Wait for the author to confirm before your first write.
