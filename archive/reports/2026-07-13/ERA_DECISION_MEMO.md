# Memo — which experiment is the canonical RQ2 headline?

> ## ⛔ SUPERSEDED — DO NOT CITE
>
> The KG effect reported below (+1.743/6, d_z=+1.24, p<.0001, W/T/L 28/6/1) is
> an artefact of a **prompt asymmetry**: the KG arm received a prompt the
> baseline did not, so the contrast measured builder *plus* prompt. Re-running
> the same Joern builder with the prompt held at parity
> (`results/BOOTSTRAP_STATS_joern_parity.md`, n=35) yields kg +0.63 on the
> total (p=0.077) and +0.34 KG-relevant (p=0.111) — **not significant on
> either metric**.
>
> Canonical RQ2 headline: `results/BOOTSTRAP_STATS_v2.md` (era 2).
> Causal claim for structural context: `results/INJECTION_EXP2_RESULTS.md`.
> Context: `results/ERA_GUIDE.md`.


**For:** supervisor meeting. **Date:** 2026-07-13.
**Decision requested:** the thesis has two complete, significant
versions of the context-augmentation experiment. They are different
experiments (builder, judge panel, rubric, n), not two estimates of the
same quantity (`results/ERA_GUIDE.md`). Which one is the RQ2 headline,
and how is the other reported?

---

## The two candidates

| | **Option A — "v2" (May 2026)** | **Option B — "Joern" (June 2026)** |
|---|---|---|
| n | 40 PRs, 5 repos | 35 PRs (5 Grafana Go PRs excluded — Joern has no Go frontend) |
| Modes | baseline / kg / rag / hybrid | baseline / joern-kg / rag (hybrid exists in `BOOTSTRAP_STATS_joern.md` but not in the headline report) |
| KG builder | grep-based | Joern code property graph (callers + tests) |
| Judges | gpt-4o-mini, gpt-4o, gemini-2.5-flash | gpt-4o, gemini-2.5-flash, gemini-2.0-flash |
| Rubric | 25 criteria, 9 KG-relevant (pre-registered) | re-based post hoc: 10 zero-variance criteria dropped → 15 active, 6 KG-active |
| KG headline | +0.60/9 KG-relevant, p=.007, d_z=.47 (`BOOTSTRAP_STATS_v2.md`) | +1.743/6 KG-active, p<.0001, d_z=1.24, W/T/L 28/6/1 (`FINAL_RESULTS_REPORT.md`) |
| RAG in same run | +0.88/25 total, p=.007 (RAG wins total; KG wins KG-relevant) | +0.429/6, p=.045, d_z=.31 (KG effect ≈ 4× RAG) |
| Story | **complementarity** — each mode wins the metric it targets | **KG ≫ RAG** when the builder resolves real call edges |
| Robustness on file | trajectory 18→25→40 monotone; cross-generator caveat (Claude saturates) | generator-robust: Gemini generator d_z=+1.34 ≈ GPT-4o +1.33 (`FINAL_RESULTS_REPORT.md` §Exp 2) |

## Internal caveat on Option B (must be stated wherever B is cited)

The same Joern data scored on the *original* 25-criterion rubric gives
KG-relevant Δ **+0.69/9, p=.003, d_z=.58** and Total Δ +1.17/25, p=.002
(`BOOTSTRAP_STATS_joern.md`). The +1.743/6 figure comes from the
re-based 15-active-criterion rubric. The two are consistent (dead,
zero-variance criteria dilute the /9 denominator) but the re-basing was
done *after* seeing the data — the committee will ask. If B becomes the
headline, the honest presentation is: primary on the original rubric
(+0.69/9), with the re-based +1.743/6 as a pre-explained instrument
refinement.

## Considerations

- **A is more defensible; B is more impressive.** A has full n=40, a
  pre-registered rubric, and no post-hoc instrument change. B has a
  large, generator-robust effect but carries the rubric re-basing, the
  judge-panel change (two Gemini models — family correlation), and the
  n=35 exclusion.
- **B connects directly to Experiment 2.** The injection pre-registration
  (`experiments/2026-07-05_injection_exp2/docs/DESIGN_AND_PREREGISTRATION.md`
  §7) deploys the Joern builder and its inheritance-edge augmentation.
  The prototype already showed detection tracks builder edge coverage
  (deployed Joern 4/8 vs idealised 8/8).
- **The operating instructions currently pin A as canonical**
  (`thesis-context/CLAUDE.md` §Headline numbers, verified 2026-05-12)
  and mandate the complementarity framing. Choosing B requires updating
  that file and re-deriving the framing.

## Recommendation (student position, for discussion)

Keep **A as the canonical RQ2 headline** and report **B as a clearly
labeled follow-up study**: "does a stronger KG builder increase the
effect?" — answer: yes, substantially (+0.69/9 → on the same rubric,
vs A's +0.60/9 with a weaker builder; d_z .47 → .58, and 1.24 on the
re-based instrument). This ordering (1) preserves the pre-registered
instrument for the headline, (2) turns B's builder change from a
confound into a *finding*, and (3) sets up Experiment 2, which tests the
builder-edge-coverage mechanism causally. One era per table, always
labeled, per `results/ERA_GUIDE.md`.

## What the decision unblocks

Abstract framing, results-chapter structure, `thesis-context/CLAUDE.md`
update (if B), and the Experiment 2 §13 sign-off (same meeting:
N=48 split, repo trio, oracle scope, ablation arms, human-study
downgrade confirmation).
