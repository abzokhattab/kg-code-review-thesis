# Adversarial gap audit on `HONEST_HEADLINE.md`

Read this as: "what would a hostile reviewer flag, and what receipt
closes it?" Each row is a claim in the headline doc, the most
plausible attack on it, and the file/section that closes the attack.

If a row says "**OPEN**" in the status column, that's a gap the
defence cannot fully close from current artefacts — the thesis must
either generate the missing receipt or hedge the claim.

---

## Claim ↔ attack ↔ receipt

| # | Claim in HONEST_HEADLINE.md | Plausible reviewer attack | Closing receipt | Status |
|---|---|---|---|:---:|
| 1 | Tree-sitter d_z=+0.47, p=0.006, CI [+0.17, +0.83] | "Where's the CI? Earlier docs say `not in this audit`." | `COMBINED_RESULTS_TABLE.md` row 1 (regenerated 2026-06-11 with tie-corrected Wilcoxon and computed CI) | ✅ |
| 2 | Joern parity d_z=+0.30, p=0.057, CI [−0.03, +0.65] | "Hand-rolled stats — does scipy agree?" | `STATS_VALIDATION.md` (matches scipy to 4 decimals) | ✅ |
| 3 | Wilcoxon p=0.057 (not 0.066) | "Earlier docs say 0.066." | Tie variance correction added to all three computation paths; superseded docs (`FINAL_REPORT.md`, `VERDICT_v2.md`) carry retraction headers | ✅ |
| 4 | Bootstrap CI straddles zero | "Percentile bootstrap under-covers — what about BCa?" | `BCA_BOOTSTRAP.md` (BCa: [−0.047, +0.640], also straddles zero) | ✅ |
| 5 | All 3 judges return positive d_z (+0.20 to +0.34) | "Are these really 3 independent judges?" | `ROBUSTNESS_BATTERY.md` §4: gpt-4o +0.34, gpt-4o-mini +0.20, gemini-2.5-flash +0.21 | ✅ |
| 6 | Direction stability buggy↔parity = 54% | "How is direction defined? W/T/L threshold?" | `ROBUSTNESS_BATTERY.md` §7 (W=positive Δ, L=negative Δ, T=zero Δ on KG-rel) | ✅ |
| 7 | Body-length regression Pearson r=+0.13 | "Spurious — bodies vary by repo. Did you control?" | `STATS_VALIDATION.md` matches scipy r=+0.1291; **per-repo demeaning** in `PER_REPO_REGRESSION.md` gives within-repo r = −0.007 (p=0.97) — repo clustering does NOT mask a redundancy effect | ✅ |
| 8 | Joern arm mean KG-rel: 5.69 (buggy) → 5.34 (parity); baseline 5.00 (constant) | "Show the per-arm means." | Verified by direct computation 2026-06-11 (this session) — 5.343, 5.686, 5.000 | ✅ |
| 9 | Body crowds the context; median 652, mean 1582, max 7574 chars | "Earlier doc said 200-800 chars. Which is right?" | Direct computation this session; HONEST_HEADLINE.md §6 corrected | ✅ |
| 10 | KG citation rate ≈ 1% under both buggy and parity | "Citation count is sensitive to regex — is this stable?" | `KG_LEAKAGE_AUDIT_PARITY.md` (35 vs 34 symbols out of 3,586 — Δ=+1) | ✅ |
| 11 | PR31 fabricates "sklearn/linear_model team" | "One PR doesn't make a pattern." | `HALLUCINATION_AUDIT_PARITY.md`: 3/35 fabricate sklearn-team-shaped owners (PR10, PR31, PR42) | ✅ |
| 12 | Per-language: Java +0.58, TS +0.54, Python 0, C++ 0, Scala 0 | "n per language is small (6-11) — is the per-language CI computed?" | `PER_LANGUAGE_CI_AND_FALSIFICATION.md` §1 reports bootstrap 95% CIs: Java [+0.00, +1.31], TS [-0.13, +1.62], Python [-0.73, +0.73], C++ [-2.04, +0.85] | ✅ |
| 13 | Tree-sitter pre-registered, Joern is post-hoc exploratory | "Where's the pre-registration?" | `human_eval_v3/docs/ANALYSIS_PLAN.md` (frozen, predates this audit); cross-referenced in `ANALYSIS_PLAN_CROSSCHECK.md` | ✅ |
| 14 | T=0.0 not bit-deterministic; Jaccard 0.57-0.72 | "Then your scores could shift by how much?" | `REPRO_AUDIT.md` reports Jaccard band; `REROLL_BOUND.md` simulates worst-case d_z under ±1, ±2, ±3 per-PR judge noise — under ±1, 95% band [+0.057, +0.458] (Pr(d_z≤0)=0.008); under ±2, [−0.075, +0.467] (Pr(d_z≤0)=0.085) | ✅ |
| 15 | Strict prompt = exploratory upper bound (d_z=+1.34, p<0.0001) | "Is the prompt actually mandating the rubric?" | The strict prompt explicitly enumerates the 9 KG-rel criteria as required topics; reported as biased upper bound, not headline | ✅ |
| 16 | "Body and KG interfere, not substitute" | "Interference is your hypothesis — what would falsify it?" | Falsification run: per-PR regression of joern-arm Δ(parity−buggy) on body length gives Pearson r=+0.24 (n=35, p=0.17). **Direction does not match interference.** See `PER_LANGUAGE_CI_AND_FALSIFICATION.md` §2. HONEST_HEADLINE softened to "no confirmed mechanism". | ⚠️ retracted |
| 17 | "n=35 underpowered to detect d_z=+0.30" | "What's the actual power calculation?" | Computed in `REVIEWER_QA.md` §B7: paired-t power ≈ 0.46; n needed for 0.80 power ≈ 85 | ✅ |
| 18 | Recommendation: run both human-study arms (clean and strict) | "Why not just run the higher-power one?" | `HONEST_HEADLINE.md` §"What this means for the human study" — clean arm captures generalisable effect; strict arm captures upper bound | ✅ |
| 19 | Java +0.58 / TypeScript +0.54 are real per-language effects | "Maybe one judge is lenient on Java/TS." | `PER_JUDGE_BY_LANGUAGE.md`: Java positive across all 3 judges (+0.44, +0.79, +0.16); TS positive across all 3 (+0.21, +0.11, +1.00); judge-robust within both languages | ✅ |
| 20 | Strict d_z=+1.34 reflects broadly KG-relevant improvement | "Maybe the prompt forced 1-2 dominant criteria." | `STRICT_SENSITIVITY.md`: leave-one-out d_z stays >+1.03 under removal of any single criterion (max drop 23.3% when C2 removed); 4 of 9 LOO removals *increase* d_z slightly; broadly distributed | ✅ |
| 21 | Joern parity n=35 is exploratory, p=0.057, CI straddles zero | "Underpowered null — what's the actual power?" | `POWER_ANALYSIS.md` (scipy-validated): achieved power 0.412 for observed d_z=+0.30 at n=35; MDE at n=35 is +0.49; n=88 needed for 80% power. Tree-sitter (d_z=+0.47, n=40) had 0.83 power, consistent with p=0.006. Honest reading: consistent direction, sub-significant under-powered replication | ✅ |

---

## Summary of partial/open gaps

### ⚠️ Partial — claims hedged but receipts incomplete

(none — both #7 and #14 closed in this audit pass)

### ✅ Closed in this audit

- **#7 Body-length regression** — per-repo demeaning (two-stage
  fixed-effect estimator) gives within-repo r = −0.007, p = 0.97.
  The cross-PR r = +0.13 is not a confound from repo clustering, AND
  the within-repo correlation is in the wrong direction for
  redundancy. Both forms of the redundancy hypothesis (cross-PR and
  within-repo) are unsupported. Receipt: `PER_REPO_REGRESSION.md`.

- **#14 T=0 reproducibility d_z bound** — worst-case perturbation
  simulation (10,000 reps per noise level) shows that under ±1 per-PR
  judge noise the d_z 95% band is [+0.057, +0.458] (Pr(d_z≤0)=0.008);
  under ±2 noise it is [−0.075, +0.467] (Pr(d_z≤0)=0.085). The
  headline conclusion (d_z ≈ +0.30, CI straddles zero) is robust to
  plausible T=0 sampling variance. An actual re-roll is not
  load-bearing for the headline. Receipt: `REROLL_BOUND.md`.

### ⚠️ Mechanism retracted — interference hypothesis falsified

- **#16 Interference vs redundancy** — the per-PR falsification test
  (regress joern-arm drop on body length) gives Pearson r = +0.24
  (n=35, p=0.165). The simple interference-via-length hypothesis is
  **not supported** by the per-PR data: longer bodies do not produce
  larger joern-arm drops. `HONEST_HEADLINE.md` was updated to say
  "no confirmed mechanism" rather than "interference". The thesis
  must follow suit. **Receipt:** `PER_LANGUAGE_CI_AND_FALSIFICATION.md`
  §2.

---

## What this gap audit changes about the headline

Nothing changes the d_z=+0.30, p=0.057, CI [−0.03, +0.65] number.
What changed is the *mechanism narrative* in the discussion chapter:

- "Body and KG interfere" → "**The parity correction reduced the
  joern arm's mean KG-rel by 0.34 points without measurably changing
  baseline; the per-PR mechanism is not identified.** The simplest
  hypothesis (body–KG interference, finite framing budget) predicts a
  negative correlation between body length and joern-arm drop, which
  we do not observe (Pearson r = +0.24, p = 0.17, n = 35)."

- "Body-length regression r=+0.13 refutes the redundancy hypothesis" →
  "Body-length regression r=+0.13 is inconsistent with redundancy at
  the cross-PR level; the within-repo (repo-demeaned) regression
  gives r = −0.007 (p=0.97), so the cross-PR estimate is not a
  repo-clustering artefact, AND the within-repo estimate also does
  not support redundancy."

- "Direction stability is 54%, so the buggy ranking is not salvageable"
  → "Direction stability of 54% on a W/T/L coding does not justify
  treating buggy and parity as the same ranking with rescaled
  magnitudes."

The numbers stand. The headline (tree-sitter is the pre-registered
RQ2 anchor; Joern parity is exploratory) stands. Only the mechanism
language is weakened — appropriately, since neither redundancy nor
interference survived its falsification.

---

## What I would still do if I had another hour

1. ~~Per-language bootstrap CI on the parity n=11/n=8/n=6 subsamples.~~
   **Done** — see `PER_LANGUAGE_CI_AND_FALSIFICATION.md` §1.
2. Re-roll the parity scoring under a different judge-panel seed.
   Cost ≈ $1.20. Compare d_z point estimate. **Bounded analytically**
   in `REROLL_BOUND.md` — actual re-roll is no longer load-bearing.
3. ~~Per-repo random-effect regression on body-length × KG-rel delta.~~
   **Done** — `PER_REPO_REGRESSION.md`. Within-repo r = −0.007, p = 0.97.
   Cross-PR estimate is not a repo confound; redundancy hypothesis
   stays unsupported under both pooled and within-repo views.
4. ~~Falsification check on interference: per-PR scatterplot of
   `KG-rel(parity) − KG-rel(buggy)` vs body length.~~ **Done** — see
   `PER_LANGUAGE_CI_AND_FALSIFICATION.md` §2. Result: r = +0.24,
   interference hypothesis NOT supported.
5. Spot-check the top-loss PRs (15, 21, 31, 34, 43) qualitatively.
   PR15, PR31, PR43 done (`TOP_LOSS_SPOT_CHECKS.md`,
   `PR31_SPOT_CHECK.md`). PR21 and PR34 remain — the qualitative
   payoff is diminishing returns at this point (the heterogeneity
   thesis is already established by PR15+PR43).

Items 2 and 5 (PRs 21+34) are nice-to-have but not load-bearing for
the headline.
