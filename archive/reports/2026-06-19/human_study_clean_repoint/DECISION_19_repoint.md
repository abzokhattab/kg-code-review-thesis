# Decision 19 — Re-point the human study to the clean normal-prompt comparison (2026-06-19)

**Status:** built and validated (study instrument), pending one open
selection decision (see §5). No LLM calls; cost $0; idempotent.

**Supersedes for RQ3:** Decision 18 (2026-06-13), which pointed the live
study at `baseline_strict` vs `joern` under the strict prompt.

---

## 1. What changed

| | Decision 18 (live `human_eval_v3`) | Decision 19 (this folder) |
|---|---|---|
| Comparison id | `bl_vs_joern` | `bl_vs_joern_normal` |
| Arm A | `baseline_strict` (strict prompt) | `baseline` (normal production prompt) |
| Arm B | `joern` (strict prompt + Joern KG) | `joern` (normal production prompt + Joern KG) |
| Review source A | `experiments/human_study_reviews/` | `outputs/luca_prs_v2/pr<N>_baseline.md` |
| Review source B | `experiments/2026-05-15_joern_kg_main/exp_gpt4o_joern/` | `experiments/2026-06-11_joern_normal_prompt/reviews/pr<N>_kg.md` |
| 6 rating criteria | {F3\*, F2\*, T3, Q5, R1, C6} | **unchanged** |
| PRs | {22, 24, 31, 38, 44, 47} | {22, 24, 31, 38, 44, 47} *(unchanged for now — see §5)* |
| Rater UI / flow / analysis metric | unchanged | unchanged |

**Nothing about the rubric or the rating criteria was added or removed.**
Only the *prompt regime* of the two review arms changed (strict → normal),
and with it the review files that are loaded.

## 2. Why

The thesis headline is the **normal-prompt** result:
- tree-sitter KG: KG-relevant d_z = +0.47, p = 0.007 (n = 40), pre-registered.
- clean Joern KG: KG-relevant d_z = +0.58, p = 0.003; total d_z = +0.61,
  p = 0.001 (n = 35) — `experiments/2026-06-11_joern_normal_prompt/RESULTS.md`.

Decision 18 validated the **strict-prompt** Joern arm, whose larger effect
(d_z = +1.07 / +1.34) is the documented *confound*: the strict prompt
mandates coverage of the very 9 criteria being scored
(`THESIS_OVERVIEW_FOR_JUDGE.md` lines 154-181). Validating the judge
against humans on the confounded arm does **not** validate the headline.

The clean Joern run was completed on **2026-06-11 — two days before
Decision 18** — and gives a sizeable, significant effect *without* the
prompt confound. It is therefore the correct target for RQ3 convergent
validity. This decision re-points the study at it.

## 3. Direction-blindness statement

Re-pointing from the strict to the normal prompt changes the prompt regime
**symmetrically** for both arms (baseline and Joern both move from strict
to normal). The 6 PRs, the 6 rating criteria, the comparison structure,
and the analysis metric (Kendall's τ between human preference rank and
LLM-judge KG-relevant delta rank) are unchanged. No selection in this
decision depends on which mode wins on any PR.

## 4. Balance caveat (important — read before recruiting raters)

Decision 18 chose its PR set to be **outcome-balanced** under the strict
scoring (2 wins / 2 ties / 2 losses) so the study can fail — a
requirement for meaningful convergent validity. Under the **clean**
normal-prompt scoring, the *same* 6 PRs are **not** balanced:

| PR | Repo | Baseline KG-rel /9 | Clean Joern KG-rel /9 | Δ | Outcome |
|---:|---|---:|---:|---:|---|
| 22 | apache/kafka | 5 | 6 | +1 | WIN |
| 24 | scikit-learn | 6 | 7 | +1 | WIN |
| 31 | scikit-learn | 5 | 8 | +3 | WIN |
| 38 | grafana | 4 | 5 | +1 | WIN |
| 44 | scikit-learn | 7 | 8 | +1 | WIN |
| 47 | jenkinsci/jenkins | 6 | 5 | −1 | LOSS |

**This faithful arm-swap set is 5W / 0T / 1L.** Baseline KG-rel from the
canonical v2 panel (`results/checklist_evaluation_llm_multi__v2.json`);
Joern KG-rel from the clean run's per-PR scores
(`experiments/2026-06-11_joern_normal_prompt/scores/pr<N>_kg.json`).

A study that is almost all wins is weak for convergent validity: it asks
raters about PRs the judge already says KG wins, leaving little room to
detect *disagreement*. **The built `study_data.json` in this folder uses
this set so the instrument is runnable today, but the set should be
rebalanced before recruiting.**

## 5. Recommended rebalanced selection (the open decision)

Across all 35 clean-Joern PRs the outcome distribution is **21W / 8T /
6L**, so a balanced 2W / 2T / 2L design is selectable. Proposed set,
prioritising PRs already vetted in Decisions 13-18 and keeping repo /
language diversity:

| Slot | PR | Repo | Lang | Δ (clean) | Prior vetting |
|---|---:|---|---|---:|---|
| Win (strong) | 31 | scikit-learn | Python | +3 | Decision 18 |
| Win (weak) | 38 | grafana | TypeScript | +1 | Decision 18 |
| Tie | *TBD* | — | — | 0 | needs re-vetting |
| Tie | *TBD* | — | — | 0 | needs re-vetting |
| Loss | 47 | jenkinsci/jenkins | Java | −1 | Decision 18 |
| Loss | 30 | godotengine/godot | C++ | −1 | Decision 17 |

**Why the ties are marked TBD.** The 8 clean-scoring tie PRs are
{3, 10, 13, 19, 23, 29, 45, 46}. Most were previously rejected for good
reasons: PR 3 was swapped out in Decision 17 for low discriminability
(50 % problem-overlap); PR 13 was dropped in Decision 16 for an oversized
47 kB diff; PR 23 was dropped for paraphrasing-only reviews; PRs 19 / 46
are Jenkins/Jelly (KG-unparseable risk). Picking 2 clean tie PRs that
*also* satisfy the direction-blind stimulus criteria (≤ 50 kB diff,
non-empty body, 100 % KG-parseable, visible baseline↔Joern difference)
needs the same discriminability + parseability re-vetting that Decisions
16-17 ran. That is a small, well-defined follow-up — but it is a
selection choice that should be made deliberately (and ideally noted to
the supervisor), not silently.

## 6. What stays the same

- 25-criterion rubric, 3-judge panel, 40-PR LLM-judge dataset — untouched.
- 6-criterion human-rating subscale {F3\*, F2\*, T3, Q5, R1, C6} — unchanged.
- Session structure and rater UI — unchanged.
- Primary metric: Kendall's τ (human preference rank ↔ LLM-judge KG-rel
  delta rank) — unchanged.
- Anti-goalpost-moving rules from `ANALYSIS_PLAN.md` §2.3 — still bind:
  no dropping criteria or PRs after seeing rater data.

## 7. Files in this folder

| File | Purpose |
|---|---|
| `build_study_data_clean.py` | Reproducible builder (normal baseline vs clean Joern). |
| `study_data.json` | Built stimulus file (6 PRs, 1 comparison, clean arms). |
| `DECISION_19_repoint.md` | This document. |

## 8. Verification (2026-06-19)

- Builder ran clean: 6 PRs × 1 comparison = 6 trials; both arms loaded for
  every PR.
- Schema: `version = clean-bl-vs-joern-normal-v1`, modes `[baseline,
  joern]`, comparison `bl_vs_joern_normal`, criteria {F3\*, F2\*, T3, Q5,
  R1, C6}.
- Mode-leak check: 0 residual Evidence-section banner labels; baseline and
  Joern reviews differ on all 6 PRs (not byte-identical).

## 9. Next steps

1. Decide the rebalanced 2W/2T/2L PR set (§5) — pick the two tie PRs.
2. Rebuild `study_data.json` with `--pr-ids` once the set is locked.
3. Port into a deployable study folder (clone of `human_eval_v3/`) and run
   the smoke test / deep audit.
4. Resolve the webhook (HTTP 405) before any rater data can be collected
   (`human_eval_v3/docs/REDEPLOY_WEBHOOK.md`).
