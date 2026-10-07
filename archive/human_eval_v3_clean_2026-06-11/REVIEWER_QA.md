# Anticipated reviewer Q&A — clean-Joern audit, 2026-06-11

This document is a hostile-reviewer pre-mortem on `HONEST_HEADLINE.md`.
Each entry is a question I expect a committee member to ask, a one-line
answer, and a pointer to the file that contains the receipts.

The questions are grouped by the chapter where they're most likely to
land: **methodology**, **statistics**, **mechanism**, **threats to
validity**, **scope of claims**.

---

## A. Methodology

### A1. "Why is the headline n=40 (tree-sitter) when the Joern run is n=35?"

Tree-sitter `kg` has parsers for Go; Joern's frontend produces no call
edges for Go. Excluding the 5 Go PRs from the Joern arm gives n=35. The
exclusion is justified by inspection (caller lists empty for all 5 Go
PRs in the Joern CPG), not by score-snooping. **Receipt:**
`UNKNOWN_UNKNOWNS_AUDIT.md` §"Go-exclusion bias = −0.034".

### A2. "Why two RQ2 instruments at all? Pick one."

The pre-registered instrument is tree-sitter `kg`
(`human_eval_v3/docs/ANALYSIS_PLAN.md`). Joern was added post-hoc to
test whether a more principled call-graph KG would change the
conclusion. The plan does not lock the instrument; it locks the human-κ
analysis. **Receipt:** `ANALYSIS_PLAN_CROSSCHECK.md` §"What is and is
not pre-registered".

### A3. "Did you score-snoop when picking parity vs strict?"

No. Both strict and parity were generated *before* the score files
were inspected. Buggy was generated first (body omitted from the joern
arm by mistake), parity was generated as the bug fix, strict pre-dates
both. **Receipt:** file mtimes in `experiments/2026-06-11_joern_normal_prompt_parity/scores/`
post-date the buggy mtimes by hours, all generated-then-scored.

### A4. "Why three commercial-LLM judges and not human raters?"

The commercial-LLM panel is RQ2's *secondary* outcome. The κ analysis
in `human_eval_v3/` (16 raters, Kendall's τ ≥ 0.6 threshold) is the
primary RQ2 design. The LLM panel is a high-throughput pre-screen.
**Receipt:** `ANALYSIS_PLAN_CROSSCHECK.md` §"Pre-registered design".

### A5. "Why 9 KG-relevant criteria? Did you cherry-pick the subscale?"

The 9 criteria (F3, F4, T1, T2, T3, M1, M3, C2, Q2) were picked from
the 25-criterion rubric on theoretical grounds *before* any LLM-judge
run, by mapping each criterion to whether a structural-context KG could
plausibly help (call-graph, type info, test linkage). The mapping is
documented in `human_eval_v3/docs/ANALYSIS_PLAN.md` and frozen.
**Receipt:** the same 9 IDs appear in every results file.

### A6. "Did you tune anything against the LLM judges?"

No. Prompts (clean-Joern parity and strict) and the rubric were frozen
before scoring. Only the parity prompt was modified — to match
baseline's prompt structure (include PR body) — and that was a bug fix
disclosed in `HONEST_HEADLINE.md` §6. **Receipt:** the four runs use
the prompts in `experiments/.../prompts/` which are version-controlled.

---

## B. Statistics

### B1. "Your Wilcoxon p of 0.057 — is that scipy-validated?"

Yes. `STATS_VALIDATION.md` cross-checks every reported statistic
(Wilcoxon, sign test, Pearson, Spearman, percentile bootstrap, BCa
bootstrap) against `scipy.stats`. Wilcoxon matches to four decimals
(my 0.0573, scipy default 0.0573, scipy method='approx' 0.0573).
**Receipt:** `STATS_VALIDATION.md`.

### B2. "Do you correct for ties in the Wilcoxon variance?"

Yes. Earlier scripts used the un-corrected sigma² = n(n+1)(2n+1)/24 and
got p=0.066. The corrected formula subtracts `sum(t³ − t)/48` over
tie-group sizes, giving sigma² = 777 instead of 827.75 and p=0.057.
**Receipt:** `STATS_VALIDATION.md`; the earlier 0.066 only persists in
the explicitly retracted `FINAL_REPORT.md` and `VERDICT_v2.md`.

### B3. "Why three different p-tests? Are you cherry-picking the lowest?"

No — the *highest* of the three (sign p=0.383) is also reported; that
is the conservative bound. The three tests use different signal
(Wilcoxon: signed ranks, sign: count direction only, permutation:
sign-flip). **All three are reported, in `HONEST_HEADLINE.md` table 2.**

### B4. "Your bootstrap CI is percentile, which under-covers. Did you check BCa?"

Yes. `BCA_BOOTSTRAP.md` runs the bias-corrected accelerated bootstrap.
KG-rel BCa CI is [−0.047, +0.640]; percentile is [−0.027, +0.653].
**Both straddle zero**, so the conclusion does not change. The BCa
bias correction z₀=−0.013 and acceleration a=−0.013 are both small,
which is why the two intervals are nearly identical.

### B5. "Is the 10,000-resample bootstrap stable? Did you re-run?"

Yes. `validate_stats.py` re-runs my percentile bootstrap and scipy's
side-by-side from independent seeds. Both intervals match to ±0.005
on each end. **Receipt:** `STATS_VALIDATION.md` table 5.

### B6. "Multiple comparisons — you ran four configurations. Bonferroni?"

The four configurations are not four hypothesis tests of the same
null. Tree-sitter is the pre-registered RQ2 instrument; Joern strict,
buggy, and parity are exploratory replications under different
prompts. Only tree-sitter (p=0.006) survives a Bonferroni-of-four
correction, which is exactly the position taken in `HONEST_HEADLINE.md`:
**tree-sitter is the headline; Joern parity is exploratory.**

### B7. "What's the power of n=35 to detect d_z=+0.30?"

Scipy-validated paired-t power at d_z=+0.30, n=35, α=0.05 (two-sided)
is ≈ 0.41. **The Joern parity n=35 is underpowered to detect a d_z of
this size at conventional thresholds.** This is precisely why the
result is reported as exploratory — the direction is consistent
(per-judge all positive), the magnitude is plausible, but the data do
not statistically rule out a null. **Receipt:** `POWER_ANALYSIS.md` —
the n required for 0.80 power at d_z=+0.30 is n ≈ 88; the MDE at
n=35 is d_z ≈ +0.49. (Wilcoxon is slightly *more* powerful than
paired-t on this specific data because the per-PR deltas are bounded
integers — paired-t p=0.083 vs Wilcoxon p=0.057 — so these paired-t
power numbers are conservative.)

### B8. "Effect-size choice — why d_z and not r or g?"

d_z is paired Cohen's d (mean Δ ÷ sd Δ). It is the natural effect size
for matched-pairs designs and the one the pre-registered analysis
plan uses. `BOOTSTRAP_STATS_v2.{md,json}` reports d_z for the
tree-sitter run; the Joern runs follow the same convention.

### B9. "Is the buggy run still in the catalog? Why?"

It is reported as "discard — confound" in every table, alongside the
parity number. Hiding it would be selective reporting. The reason it's
still listed: a reader who finds the d_z=+0.58 quoted in earlier
documents (e.g., `FINAL_REPORT.md`) should be able to verify it was
the buggy-arm number and that the correction is parity = +0.30.
**Receipt:** every results table lists buggy with explicit
"retracted/confound" annotation.

---

## C. Mechanism (parity drop)

### C1. "You retracted the redundancy story — what's the new mechanism?"

We do not have a confirmed mechanism. The simplest hypothesis (body
and KG **interfere** in the joern prompt) predicts a negative slope
when joern-arm score drop is regressed on body length; the per-PR
falsification test gives Pearson r = +0.24 (n=35, p=0.165), so
interference-via-length is **not** supported either. What is robust:
parity *reduced the joern arm's mean KG-rel by 0.34* (5.69 → 5.34);
baseline is unchanged. **Receipt:** `HONEST_HEADLINE.md` §6 and
`PER_LANGUAGE_CI_AND_FALSIFICATION.md` §2.

### C2. "Show me the body-length regression that killed the redundancy story."

If body substituted for KG, we'd expect a *negative* Pearson r between
body length and the per-PR KG-rel delta (more body → less KG benefit).
We see **r = +0.13** (Spearman ρ = +0.09). That is the wrong sign.
**Receipt:** `STATS_VALIDATION.md` §4 (scipy match: my r=+0.1291,
scipy r=+0.1291).

### C2a. "Could that +0.13 be a repo-clustering artefact? Bodies and deltas may both vary by repo."

Tested. Repo-demeaning each observation (subtract repo mean from both
body length and KG-rel delta — the fixed-effect estimator under a
random-intercept-by-repo model) gives **within-repo r = −0.007**
(p = 0.97, n = 35). The cross-PR +0.13 is not driven by repo
clustering, and the within-repo correlation is also essentially zero —
neither view supports redundancy. **Receipt:** `PER_REPO_REGRESSION.md`.

### C3. "Could the parity drop be due to a non-stationarity / API drift / model rev?"

Possible but unlikely. Both runs (buggy and parity) use the same Gemini
2.5 Flash and the same temp/top_p settings, generated within a 24-hour
window on 2026-06-11. The strict run pre-dates both. We have no
evidence the model changed between buggy and parity.
**Receipt:** `experiments/2026-06-11_joern_normal_prompt_parity/run.py`
shares config with `experiments/2026-06-11_joern_normal_prompt/run.py`.

### C4. "Could the parity drop be a 1-in-3 statistical fluke (per-judge)?"

The drop is consistent across all three judges (parity arm scores all
fall, baseline arm scores all flat). It is not a single-judge
artefact. **Receipt:** `ROBUSTNESS_BATTERY.md` §4 per-judge d_z table.

### C5. "Direction stability is 54%. What does that say about the buggy ranking?"

It says the buggy ranking is *not* a salvageable shadow of the parity
ranking. 54% is barely above the W/T/L base rate. **The thesis cannot
claim "buggy preserves direction with smaller magnitudes".** It must
say: the parity correction changed not just magnitude but per-PR
direction in nearly half the cases. **Receipt:** `ROBUSTNESS_BATTERY.md`
§7 transition table.

---

## D. Threats to validity

### D1. "PR31 fabrication — does this happen often?"

Three out of 35 parity reviews fabricate sklearn-team-shaped owner
attributions (PR10, PR31, PR42). Ten of 35 contain unverified
file-path citations. **The thesis discussion chapter must include a
fabrication disclosure.** PR31 is the worked example.
**Receipt:** `HALLUCINATION_AUDIT_PARITY.md` and `PR31_SPOT_CHECK.md`.

### D2. "T=0.0 reproducibility — you say the run is non-deterministic?"

Yes. GPT-4o at T=0.0 is not bit-deterministic (Jaccard 0.57–0.72
across re-runs of the same prompt). The reported scores are from a
single run. We bounded the d_z impact by simulating worst-case
per-PR judge noise: under ±1 noise the simulated 95% d_z band is
[+0.057, +0.458] (Pr(d_z≤0)=0.008); under generous ±2 noise it is
[−0.075, +0.467] (Pr(d_z≤0)=0.085). The headline conclusion
(d_z ≈ +0.30, CI straddles zero) is robust to plausible T=0
variance. **Receipt:** `REPRO_AUDIT.md`, `REROLL_BOUND.md`.

### D3. "What about the per-language picture under parity?"

Java +0.58 (n=11) is the strongest language; TypeScript +0.54 (n=8)
second; **Python panel-aggregate 0.00 (n=8); C++ panel-aggregate 0.00
(n=6)**. The Python and C++ panel nulls mask per-judge sign disagreement
at small n (see E6 below), so the right reading is "judges disagree at
this n, panel averages to zero", not "KG fails on Python/C++". The
thesis cannot claim "KG works for code review in general"; it must
qualify the claim to the (judge-robust) languages where Joern's
call-graph extraction produces useful edges (Java, TypeScript at this n).
**Receipt:** `DEEP_AUDIT_PARITY.md`, `PER_JUDGE_BY_LANGUAGE.md`.

### D4. "What does the LLM cite from the KG?"

Across 35 parity reviews, the 3,586 caller symbols available from the
Joern CPG are surfaced 35 times (1.0%). Buggy was 34 / 3,586 (0.9%).
**The body-parity correction did not change KG citation behaviour.**
Whatever changed between buggy and parity was *framing quality*, not
KG visibility. **Receipt:** `KG_LEAKAGE_AUDIT_PARITY.md`.

### D5. "Are there rubric-leakage artefacts?"

`UNKNOWN_UNKNOWNS_AUDIT.md` checked five sources of leakage: rubric
appearing in prompts, balanced repos, healthy score range, GitHub
issue numbers leaking labels, and Go-exclusion bias. Largest signal:
Go exclusion is −0.034 d_z (i.e. excluding Go *understates* d_z by a
hair). Everything else is null.

### D6. "Does the human study match this LLM result?"

The human study (`human_eval_v3/`) is in progress and untouched by this
audit. Its κ analysis is the pre-registered RQ2 outcome. The LLM-panel
results in this folder are a fast secondary outcome. The agreement
between them is the eventual validation step.

---

## E. Scope of claims

### E1. "What can the thesis claim about Joern, exactly?"

> "A follow-on Joern CPG-based KG, evaluated under prompt body-parity
> on n=35 PRs, produces a directionally consistent positive shift on
> the LLM-judged rubric (d_z=+0.30, three-judge mean). The 95%
> bootstrap CI is [−0.03, +0.65] and the Wilcoxon two-sided p is
> 0.057 (tie-corrected, scipy-validated). The effect does not reach
> conventional significance at n=35; we report it as an exploratory
> replication of the pre-registered tree-sitter result."

### E2. "What can it claim about tree-sitter?"

> "Tree-sitter-AST KG augmentation produces a moderate positive shift
> (d_z=+0.47, n=40, Wilcoxon p=0.006) under the v2 multi-judge LLM
> panel."

### E3. "What can it NOT claim?"

- "Joern significantly improves code review quality" — n=35 doesn't
  reach p<0.05 in any of three tests.
- "Body and KG context are partially substitutable" — body-length
  regression refutes this (r=+0.13).
- "Buggy preserves direction with smaller magnitudes" — direction
  stability is 54%.
- "KG augmentation works across languages" — Python/C++ panel
  aggregates are 0.00 under parity (with per-judge sign disagreement
  at n=8 and n=6); judge-robust positive effects only on Java and
  TypeScript at this n.
- "The model uses the KG citations heavily" — 1% surfacing rate
  on caller symbols.

### E4. "What's the strict-prompt result actually showing?"

Strict d_z = +1.34 (n=35, Wilcoxon p<0.0001) is the *upper bound* of
what KG augmentation can achieve **when the prompt mandates coverage
of the 9 KG-relevant criteria.** This is a prompt-engineering ceiling,
not a clean comparison; it is reported as such.

### E5. "Is the strict d_z driven by 1-2 dominant criteria the prompt forced?"

No. Leave-one-out analysis: removing any single criterion from the
9-criterion KG-rel subscale leaves d_z ≥ +1.03. The largest single
drop is 23.3% (when C2 is removed); four of the nine removals
actually *increase* d_z slightly. The strict-prompt effect is
broadly distributed across the criteria, not carried by one or two.
**Receipt:** `STRICT_SENSITIVITY.md`.

### E6. "Java +0.58 / TS +0.54 — is that just one lenient judge?"

No. Per-judge Java d_z: gemini-2.5-flash +0.44, gpt-4o +0.79,
gpt-4o-mini +0.16 — all positive. Per-judge TypeScript d_z: +0.21,
+0.11, +1.00 — all positive. Both per-language effects are
judge-robust. The Python (+0.00) and C++ (+0.00) panel nulls do mask
per-judge sign disagreement at small n, so those should be reported
as 'panel-aggregate null with judge disagreement', not as 'KG fails
on Python/C++'. **Receipt:** `PER_JUDGE_BY_LANGUAGE.md`.

### E7. "n=35, p=0.057, CI straddles zero — isn't this just an underpowered null?"

Yes — n=35 has 41% power for d_z=+0.30 (scipy-validated). The MDE
at n=35 is d_z ≈ +0.49; to detect d_z=+0.30 at 80% power would
require n ≈ 88. We do not claim p<0.05 on the parity arm; we report
the CI [−0.03, +0.65] honestly and flag the Joern parity result as
exploratory. The pre-registered RQ2 anchor (tree-sitter, d_z=+0.47,
n=40) had 83% power and is comfortably significant (p=0.006). Joern
is not the headline. **Receipt:** `POWER_ANALYSIS.md`.

---

## F. The questions I expect the user can't fully answer

These are the gaps that remain *after* this audit. None are fatal but
all should be acknowledged in the thesis's threats-to-validity:

1. **No human-validated criterion ground truth at n=35.** The κ analysis
   is on a different (sub)sample.
2. **Single LLM-judge panel run.** No re-roll under different judge
   permutations.
3. **No paired-permutation CI on d_z.** The current permutation test
   matches Wilcoxon's null but does not give a CI directly.
4. **Three judges all from the commercial frontier-LLM family.** A
   judge panel using a Claude or Mistral model would be a different
   data point.
5. **Joern strict prompt is a prompt-engineering ceiling, not a
   methodologically clean result.** It can illustrate the upper bound
   but should not anchor the headline.

---

## How to use this document

When the committee asks a question, find it here and quote the
one-line answer plus the receipt. If they ask a question not on this
list, that's a real new question — flag it, don't extemporise.
