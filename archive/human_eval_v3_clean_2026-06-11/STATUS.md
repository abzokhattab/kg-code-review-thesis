# Status — clean-Joern audit work, 2026-06-11

> 📌 **Latest synthesis: read `HONEST_HEADLINE.md` first.** It supersedes
> `FINAL_REPORT.md` and `VERDICT_v2.md` after the robustness battery and
> parity-version audits surfaced findings that contradict the earlier
> redundancy-mechanism framing. Subsequent audits (statistics
> validation, per-language CI, interference falsification, top-loss
> spot checks) further refine the headline:
>
> - **Wilcoxon p is 0.057 (tie-corrected, scipy-validated)**, not 0.066 as in earlier docs.
> - **Per-language bootstrap CI computed.** Java [+0.00, +1.31] is the only sub-sample with non-negative lower bound.
> - **Interference hypothesis falsified at the per-PR level.** Body-length × joern-arm drop Pearson r = +0.24 (p = 0.17) — wrong direction. Mechanism narrative softened to "no confirmed mechanism".
> - **Top-loss spot checks** (PR15, PR43) show heterogeneous content-specific failure modes, not a single mechanism.
> - **Per-repo demeaning** of body-length × KG-rel delta gives within-repo r = −0.007 (p = 0.97). The cross-PR r=+0.13 is not driven by repo clustering, AND the within-repo correlation is also not negative. Redundancy hypothesis stays unsupported under both views.

## ✅ Complete (no further action needed for the user's question)

| Audit | File | Result |
|---|---|---|
| Initial 5-check experiment soundness | `EXPERIMENT_AUDIT.md` | PASSED |
| Pilot self-rating walkthrough | `PILOT_SELF_RATING.md` | 5/6 directional agreement with LLM judges |
| Named-entity differentiator audit | `NAMED_ENTITY_AUDIT.md` | 2-19 differentiators per PR |
| Strict-vs-clean trade-off | `STRICT_VS_CLEAN_COMPARISON.md` | Strict has 2-9× more visible differentiators |
| **Per-criterion KG-rel decomposition** | `DEEP_AUDIT.md` §1 | 6/9 KG-rel criteria positive; T1, Q2 at ceiling; M3 negative |
| **Per-language stratification (buggy + parity)** | `DEEP_AUDIT.md` / `DEEP_AUDIT_PARITY.md` | Parity collapses Python to 0; Java +0.58 strongest |
| **Judge unanimity** | `DEEP_AUDIT.md` §3 | 75.4% — above 70% robustness threshold |
| **File-citation hallucination audit (buggy)** | `HALLUCINATION_AUDIT.md` | 10/35 with unverified citations; 1 fabricated owner (PR31) |
| **File-citation hallucination audit (parity)** | `HALLUCINATION_AUDIT_PARITY.md` | 10/35 unverified; 3 fabricated team-shaped owner claims (PR10, PR31, PR42) |
| **KG-signal leakage (buggy)** | `KG_LEAKAGE_AUDIT.md` | LLM uses ~5% of available caller signals |
| **KG-signal leakage (parity)** | `KG_LEAKAGE_AUDIT_PARITY.md` | Surfacing rate ≈ unchanged (Δ +1 symbol total) — body does NOT substitute for KG citation |
| **T=0.0 reproducibility spot-check** | `REPRO_AUDIT.md` | NOT bit-deterministic; Jaccard 0.57-0.72 across runs |
| **Pilot UI sanity check** | (verified inline) | Loads, namespace `heval5c_*`, webhook disabled |
| **Unknown-unknowns probes (5)** | `UNKNOWN_UNKNOWNS_AUDIT.md` | Zero rubric leakage, balanced repos, healthy score range, no issue-number leakage, Go-exclusion bias = −0.034 (negligible) |
| **Robustness battery (7 tests)** | `ROBUSTNESS_BATTERY.md` | Bootstrap CI [−0.03, +0.65] straddles zero; sign p=0.38; permutation p=0.11; per-judge all positive (+0.20 to +0.34); body-redundancy NOT supported (r=+0.13); direction stability 54% |
| **Statistics validation vs scipy** | `STATS_VALIDATION.md` | Wilcoxon, sign, Pearson, Spearman, percentile + BCa bootstrap all match scipy to 4 decimals after tie correction added. p=0.057 confirmed. |
| **Combined results table (all 4 runs)** | `COMBINED_RESULTS_TABLE.md` | tree-sitter +0.47 / strict +1.34 / buggy +0.58 / parity +0.30, consistent CI/p columns |
| **BCa bootstrap on parity d_z** | `BCA_BOOTSTRAP.md` | KG-rel BCa CI [−0.05, +0.64] — also straddles zero. Bias and acceleration small. |
| **Per-language bootstrap CI** | `PER_LANGUAGE_CI_AND_FALSIFICATION.md` §1 | Java [+0.00, +1.31], TS [-0.13, +1.62], others degenerate |
| **Interference falsification** | `PER_LANGUAGE_CI_AND_FALSIFICATION.md` §2 | Pearson r(body_len, joern drop) = +0.24, p=0.17 — interference hypothesis NOT supported |
| **Top-loss spot checks (PR15, PR43)** | `TOP_LOSS_SPOT_CHECKS.md` | Heterogeneous content-specific failure modes — no single mechanism |
| **Per-repo (body-length × KG-rel delta) regression** | `PER_REPO_REGRESSION.md` | Within-repo r = −0.007, p = 0.97 — repo clustering does NOT mask a redundancy effect; cross-PR +0.13 is not a repo confound |
| **T=0 d_z perturbation bound** | `REROLL_BOUND.md` | Under ±1 per-PR judge noise, simulated d_z 95% band [+0.057, +0.458] (Pr(d_z≤0)=0.008); under ±2 noise [−0.075, +0.467] — headline robust to plausible T=0 variance |
| **Per-judge × per-language disaggregation** | `PER_JUDGE_BY_LANGUAGE.md` | Java (+0.44, +0.79, +0.16) and TypeScript (+0.21, +0.11, +1.00) all positive across 3 judges — judge-robust. Python and C++ are panel-aggregate nulls masking judge sign disagreement at small n |
| **Strict-prompt per-criterion sensitivity** | `STRICT_SENSITIVITY.md` | Strict d_z=+1.34 stays >+1.03 under removal of any single criterion (max drop 23.3% when C2 removed) — broadly distributed, not 1-2-criterion-driven |
| **Power analysis (scipy-validated)** | `POWER_ANALYSIS.md` | Parity n=35 had 41% power for d_z=+0.30; MDE at n=35 is +0.49; n=88 needed for 80% power. Tree-sitter n=40 had 83% power for d_z=+0.47. All numbers match scipy to 3 decimals |
| **PR31 spot check** | `PR31_SPOT_CHECK.md` | Buggy Δ=+3 → parity Δ=+1; both arms miss the `fit_intercept=False` case the body explicitly raises; fabrication mutated from person to team |
| **Pre-registered ANALYSIS_PLAN cross-check** | `ANALYSIS_PLAN_CROSSCHECK.md` | Plan locks κ analysis; tree-sitter `kg` headline unaffected; Joern is post-hoc exploratory follow-on (allowed but flag deviation) |
| **Adversarial gap audit on HONEST_HEADLINE.md** | `ADVERSARIAL_GAP_AUDIT.md` | 18 claims × attack × receipt; 2 partial gaps remain (per-repo random effects, T=0.0 d_z re-roll); interference hypothesis explicitly retracted |
| **Anticipated reviewer Q&A** | `REVIEWER_QA.md` | 5 sections × 28 questions, each with one-line answer + receipt pointer |
| **Honest synthesis (post-battery)** | `HONEST_HEADLINE.md` | Tree-sitter `kg` (d_z=+0.47, p=0.006) remains pre-registered headline. Joern parity (d_z=+0.30, CI [−0.03,+0.65], p=0.057) is exploratory replication. **Mechanism: not confirmed** — interference hypothesis falsified at per-PR level. |
| **Top-line synthesis (earlier)** | `VERDICT_v2.md` | **Superseded** by HONEST_HEADLINE.md |
| **Earlier final-report** | `FINAL_REPORT.md` | **Superseded** by HONEST_HEADLINE.md |

## 🟡 In progress (background)

| Task | Status |
|---|---|
| ~~Parity-corrected re-run~~ | **✅ Complete.** 35/35 done. Cost: $1.14. See `PARITY_RESULTS.md`. |

## 🚫 Will NOT change in this session

- Live `human_eval_v3/` study — untouched
- Thesis chapters / `thesis-context/` — untouched (per "wait dont touch the thesis yet")
- API keys / `.env` — never committed, never echoed

## Key findings the user should see first

1. **The pre-registered tree-sitter `kg` result (d_z=+0.47, n=40,
   p=0.006) is unaffected by the parity bug.** It uses a different
   pipeline. **It remains the cleanest defensible RQ2 anchor.**

2. **Joern parity headline is d_z=+0.30, but with weak statistical
   support.** 95% bootstrap CI [−0.03, +0.65] straddles zero;
   Wilcoxon p=0.057 (tie-corrected, scipy-validated), sign p=0.383,
   permutation p=0.112. Three judges all return positive d_z (+0.20
   to +0.34) so direction is judge-robust, but the n=35 sample
   doesn't reach p<0.05 in any non-parametric test.

3. **No confirmed mechanism for the parity drop.** The "redundancy
   mechanism" was retracted earlier (body-length r=+0.13). The
   subsequent "interference" hypothesis is **also retracted** — the
   per-PR falsification (joern-arm drop on body length) gives
   Pearson r=+0.24, p=0.17, *wrong direction*. Top-loss spot
   checks show heterogeneous content-specific effects (PR15: body
   redirects framing; PR43: body reassures; PR31: body absent →
   fabrication). The thesis must report parity drop as observed
   without a single-line mechanism.

4. **Direction stability buggy↔parity is 54%.** The buggy ranking
   was *not* salvageable as "magnitude shifts but ranking holds".
   Per-PR direction is barely stable across the two runs.

5. **Per-language under parity:** Java +0.58 (CI [+0.00, +1.31])
   strongest, TS +0.54 (CI [−0.13, +1.62]), Python panel-aggregate
   0.00, C++ panel-aggregate 0.00. **Per-judge disaggregation
   (`PER_JUDGE_BY_LANGUAGE.md`)**: Java and TypeScript are positive
   across all 3 judges (judge-robust); Python and C++ panel nulls
   mask judge sign disagreement at small n (Python: gemini +0.56,
   gpt-4o −0.11, mini 0.00; C++: gemini −0.10, gpt-4o +0.41, mini
   −0.09). Honest reading: "judges disagree on Python/C++ at this
   n", not "KG fails on Python/C++".

6. **PR31 fabrication persists under parity** in mutated form
   ("sklearn/linear_model team" instead of "Danilo Silva"). Two
   more sklearn-shaped fabrications appear (PR10, PR42). All three
   miss the `fit_intercept=False` concern that the body literally
   describes.

7. **The clean prompt mostly ignores the KG.** ~5% of available
   caller signals end up in the review text. Adding the body to the
   prompt does NOT change this rate — the parity-vs-buggy delta is
   +1 symbol across 35 reviews. KG citation behaviour is stable;
   what changes between runs is the joern arm's framing quality.

8. **Run both human studies, not one.** The clean-prompt effect is
   small (d_z=+0.30 with CI touching zero); the strict-prompt arm
   (d_z=+1.34) carries the statistical power.

## When the user is back

Read order:
1. `HONEST_HEADLINE.md` — corrected synthesis (post-robustness battery, post-mechanism check)
2. `STATUS.md` (this file) — what's done / what's pending
3. `ADVERSARIAL_GAP_AUDIT.md` — claim-by-claim defence map
4. `REVIEWER_QA.md` — anticipated committee questions
5. `STATS_VALIDATION.md` — scipy cross-check
6. `PER_LANGUAGE_CI_AND_FALSIFICATION.md` — per-language CI + interference falsification
7. `TOP_LOSS_SPOT_CHECKS.md` — concrete failure-mode examples beyond PR31
8. `ROBUSTNESS_BATTERY.md` — the seven probes that drove the correction
9. Drill into specific audits as needed
