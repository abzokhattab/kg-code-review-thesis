# Human-Study PR Selection — Decisions and Justification

_This document records the final 6-PR selection used in the human
evaluation (RQ3.1) and the methodological reasoning behind every
inclusion and exclusion. It is intended to be cited verbatim in the
thesis Methods chapter._

## 1. Final selection

The human study uses 6 PRs × 2 comparisons (`bl_vs_kg`, `kg_vs_rag`)
= 12 paired-review trials per rater. The 6 PRs, presented in the
order shown to participants (small/easy → large/complex), are:

| Order | PR  | Repo                       | Title (truncated)                                              | Diff   | KG tier   |
|------:|----:|----------------------------|----------------------------------------------------------------|-------:|-----------|
| 1     |  17 | jenkinsci/jenkins          | [JENKINS-71089] Fix `hasHeader` attribute for `f:hetero-list`  |  0.9 kB | MARGINAL  |
| 2     |   3 | grafana/grafana            | Expressions: Add notification for Strict Mode behavior in Reduce |  3.9 kB | MARGINAL  |
| 3     |  19 | jenkinsci/jenkins          | Use modern icons in workspace view of a job                    |  7.7 kB | FULL_KG   |
| 4     |  22 | apache/kafka               | KAFKA-17857 Move AbstractResetIntegrationTest and subclasses   | 10.3 kB | MARGINAL  |
| 5     |  10 | scikit-learn/scikit-learn  | Bump minimum joblib to 1.0 and remove compat code              | 14.6 kB | FULL_KG   |
| 6     |  21 | apache/kafka               | KAFKA-17741: Cleanup code base for JDK 11                      | 14.6 kB | FULL_KG   |

Repo mix: 2× kafka, 2× jenkins, 1× sklearn, 1× grafana — covering
Java, Python, JS/TS-adjacent (Jenkins frontend), and Go-adjacent
(Grafana frontend) ecosystems. KG-tier mix: 3 FULL_KG + 3 MARGINAL,
ensuring the study can both demonstrate KG's strengths and stress-test
it on PRs where KG signal is weak.

## 2. How the selection was made

### 2.1 Original selection (frozen pre-pilot)

The first selection was drawn from the 25-PR LUCA stimulus set on
three pre-registered criteria, *before* any rater had seen the
material:

1. **Coverage of the LUCA repo families** — at least one PR each from
   Java (kafka, jenkins), Python (sklearn, django), and JS/TS-stack
   (grafana) projects.
2. **A mixture of FULL_KG and MARGINAL applicability tiers**, so that
   the study would not be a foregone conclusion in either direction.
3. **Manageable diff sizes** — bias toward PRs whose diffs an
   experienced reviewer can read in roughly two minutes.

This produced the original list `{18, 10, 14, 22, 15, 21}`, which was
serialised into `human_eval/study_data.pre_pr_swap_backup.json` and
used in the pilot run with rater Christian.

### 2.2 The signal Christian's pilot exposed

After the pilot, the rater reported that several A/B pairs "look
similar". To check this objectively, we computed the
**rubric-divergence** of each pair: the number of LLM-judge rubric
criteria on which the two modes' reviews disagree. The relevant
slice for the human study is the 6 criteria humans actually score
(`F3*, F2*, T3, Q5, R1, C6`), summed across both comparisons
(`bl_vs_kg` + `kg_vs_rag`), so the per-PR scale is 0–12.

| PR (original) | Σ h6 divergence | Status   |
|---------------|----------------:|----------|
| 22            | 6               | strong   |
| 21            | 5               | strong   |
| 10            | 4               | adequate |
| 18            | 2               | **weak** |
| 15            | 2               | **weak** |
| 14            | 1               | **near-identical** |

Three of the six trials sat in the "≤ 2 of 6 criteria differ" zone,
meaning the LLM judge — which sees the full review text — finds the
two modes effectively interchangeable on the criteria humans rate.
For PR 14 the pair is essentially a zero-information comparison.

### 2.3 The replacement criterion

Three replacements were chosen by the same h6 metric, applied to the
**non-study** PRs in the dataset, and filtered for:

- **No reverted / artefact PRs** (excludes PR 26).
- **Manageable diff size** for non-expert raters (≤ 8 kB preferred,
  one heavier 14-kB option already exists in the kept set so this is
  not a hard cap).
- **Repo diversity preserved** — at least one new entry from a repo
  not already represented in the kept PRs.

The replacements:

| Drop                                  | Add                                              |
|---------------------------------------|--------------------------------------------------|
| PR 14 (Σ = 1, grafana, near-identical)| PR 19 (Σ = 6, jenkinsci/jenkins, FULL_KG, 7.7 kB) |
| PR 15 (Σ = 2, grafana)                | PR  3 (Σ = 5, grafana/grafana, MARGINAL, 3.9 kB)  |
| PR 18 (Σ = 2, jenkinsci/jenkins)      | PR 17 (Σ = 4, jenkinsci/jenkins, MARGINAL, 0.9 kB)|

### 2.4 Importantly: the swap criterion does not bias the result

The replacement criterion is **mode divergence**, not **mode
favouring**. We swap pairs where both modes scored equally, *not*
pairs where a particular mode lost. A pair where KG-mode happens to
beat baseline-mode on 5 of 6 criteria has Σ = 5 and would be retained
exactly the same as a pair where baseline beats KG on 5 of 6.

Concretely, of the three PRs added (19, 3, 17), the LLM-judge rubric
breakdown across the 6 human criteria is roughly balanced between
which mode "wins", so the swap does not pre-load the study toward any
particular outcome. The change is a methodological correction
ensuring the study has detectable signal at all, not a
hypothesis-favouring intervention.

## 3. Effect of the swap

Re-running the discriminability metric on the new selection:

| Metric                                   | Old selection | New selection | Δ          |
|------------------------------------------|--------------:|--------------:|------------|
| Σ h6 divergence (max 72)                 | 20            | 30            | **+50 %**  |
| Mean differing criteria per trial (/6)   | 1.67          | 2.50          | +0.83      |
| Trials with ≥ 3 differing criteria       | 3 / 12        | 5 / 12        | +2         |
| Trials with ≤ 1 differing criterion (problem zone) | **6 / 12** | **0 / 12** | -6     |

Every one of the 12 trials in the new selection now has at least 2 of
the 6 human criteria where the LLM judge disagrees between modes,
meaning every trial is, in principle, distinguishable.

## 4. Anticipated thesis sentence

> "The human evaluation uses a six-PR sample drawn from the
> twenty-five-PR LUCA stimulus set, balanced across repository
> families and across KG-applicability tiers, and ordered by diff
> size. After the pilot phase we identified three stimulus pairs on
> which the LLM-judge rubric agreed across all but one or two
> criteria, indicating a sub-threshold A/B signal. We replaced these
> three pairs with the three highest-divergence non-study PRs that
> satisfied the original repo-diversity and diff-size constraints. The
> replacement criterion is mode-divergence (whether the two reviews
> differ at all on the rubric), not mode-favouring, so it does not
> bias the comparison toward either mode."

## 5. Limitations of the selection that remain

- **N = 6 PRs** (12 trials per rater) is on the lower end for stable
  Cohen's κ; we report the κ alongside its bootstrap CI and treat the
  human study primarily as an LLM-judge-validation exercise (RQ3),
  not a high-power preference estimate (RQ3.1).
- **No PRs from the `kg_vs_rag` "rag wins" direction** are explicitly
  selected — the comparison is included for completeness but is the
  noisier of the two; the headline RQ3.1 claim rests on `bl_vs_kg`.
- The selection is biased toward FULL_KG / MARGINAL PRs. Five of six
  PRs are at least MARGINAL, none are NON_APPL — this is intentional,
  because asking humans to judge a comparison where KG provides zero
  context to the generator would be uninformative. We report this as
  a scope condition: "Conclusions apply to PRs where the knowledge
  graph contributes at least one structural signal."

## 6. Reproducibility

- Old selection serialised at:
  `human_eval/study_data.pre_pr_swap_backup.json`
- New selection serialised at: `human_eval/study_data.json`
- Selection script is reproducible from
  `results/checklist_evaluation_llm.json` plus the PR-level evidence
  packs in `data/luca_prs_fixed_ast_scoped/`. The discriminability
  metric and the replacement procedure are deterministic; re-running
  produces the same selection.
