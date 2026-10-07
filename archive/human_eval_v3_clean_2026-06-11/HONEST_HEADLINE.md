# Honest headline — clean Joern audit, **post-robustness battery, 2026-06-11**

**Read this before `FINAL_REPORT.md` or `VERDICT_v2.md`.** The
robustness battery surfaced findings that contradict parts of those
earlier docs. This file is the corrected synthesis.

---

## Three numbers, three caveats

| Configuration | n | KG-rel d_z | 95% CI | Wilcoxon p | Status |
|---|---:|:---:|:---:|:---:|---|
| Tree-sitter `kg` (pre-registered headline) | 40 | +0.47 | [+0.17, +0.83] | 0.006 | **Pre-registered. Unchanged.** |
| Joern strict prompt (forced 9-criterion coverage) | 35 | +1.34 raw / **+1.07 panel-controlled** | [+1.09, +1.78] | <0.0001 | Exploratory upper bound ⚠️ panel mismatch |
| Buggy Joern clean prompt (body omitted) | 35 | +0.58 | [+0.25, +1.01] | 0.003 | **Confound — discard** |
| **Joern clean prompt, body parity** | **35** | **+0.30** | **[−0.03, +0.65]** | **0.057** | **Most principled Joern run, but...** |

> ⚠️ **Panel mismatch on Joern strict:** the strict arm was judged by
> gemini-2.5-flash + gemini-2.0-flash (2-judge Gemini-only panel),
> while the baseline arm used gpt-4o-mini + gpt-4o + gemini-2.5-flash
> (3-judge mixed panel). Three things change simultaneously between the
> arms: KG addition, prompt change, and judge panel. The d_z=+1.340
> cannot be cleanly attributed to the KG alone. Panel-controlled
> recompute (gemini-2.5-flash scores only, same judge both sides):
> **d_z=+1.071** (Wilcoxon p<0.0001, CI [+0.791, +1.478]). The ~0.27
> difference is the judge-panel inflation component. The panel-controlled
> +1.07 is the defensible number for this run.

> *Statistics validated against `scipy.stats` to four decimals — Wilcoxon
> uses normal approximation with tie variance correction; bootstrap and
> BCa intervals match scipy's `bootstrap` to within Monte-Carlo noise;
> Pearson, Spearman, and exact sign test are bit-identical. Cross-check
> table in `STATS_VALIDATION.md`.*

The Joern parity number is **the most principled clean-prompt
comparison we have for Joern**, but:

1. **The 95% bootstrap CI straddles zero** ([−0.03, +0.65]).
2. **All three independent p-tests are above 0.05** (Wilcoxon 0.057,
   sign 0.383, permutation 0.112).
3. **Direction stability buggy↔parity is 54%** — not the "magnitude
   shifts but ranking holds" picture I claimed earlier.

**The pre-registered tree-sitter result (d_z=+0.47, n=40, p=0.006) is
the cleanest defensible RQ2 anchor.** The Joern parity number is a
post-hoc exploratory follow-on with weaker statistical support.

---

## What the robustness battery showed

### 1. Bootstrap CI straddles zero

`[−0.03, +0.65]` on KG-rel; `[+0.00, +0.74]` on total. Bootstrap is the
non-parametric companion to Wilcoxon and it agrees: at n=35, the parity
effect is *consistent in direction* but the data don't rule out a null.

### 2. Three p-values converge — and they all sit above 0.05

| Test | KG-rel p |
|---|:---:|
| Wilcoxon signed-rank | 0.057 |
| Sign test (exact binomial) | 0.383 |
| Permutation (10000 sign-flips) | 0.112 |

The sign test is the most conservative and shows the effect is *not*
detectable when you only ask "do positive deltas outnumber negative
deltas". The Wilcoxon and permutation tests use rank/magnitude
information and get closer to significance, but neither crosses
p<0.05.

### 3. Per-judge: no single judge driving the effect

| Judge | KG-rel d_z |
|---|:---:|
| gpt-4o | +0.34 |
| gpt-4o-mini | +0.20 |
| gemini-2.5-flash | +0.21 |

All three positive, range +0.20 to +0.34. **Headline is judge-robust
in direction.** That's the one place the post-audit story holds up.

### 4. Body-redundancy mechanism: NOT supported

I had claimed in `FINAL_REPORT.md` that PR-body and KG-context were
substitutable signals — that's why parity dropped d_z (baseline arm
got the body it had been missing).

The body-length regression refutes this:

- **Pearson r(body_length, KG-rel delta) = +0.13**
- **Spearman ρ = +0.09**

If the body were substituting for KG, we'd expect a *negative*
correlation (KG helps less when body is rich). The correlation is
weakly *positive* — not zero, not what redundancy predicts.

**The strict-prompt cross-check** is similar (Pearson r = +0.17 on
strict deltas), so the body-length signal is not picking up
redundancy under either prompt regime.

**Per-repo control:** demeaning body-length and KG-rel delta within
each repo (two-stage fixed-effect estimator) gives within-repo
r = −0.007 (p=0.97, n=35). See `PER_REPO_REGRESSION.md`. The cross-PR
+0.13 is not a confound from repo clustering, AND the within-repo
correlation is essentially zero — both views fail to support
redundancy.

**Conclusion:** the parity drop is real but the redundancy
explanation isn't. The actual mechanism (per §6 below) is more
deflating.

### 5. Direction stability: 54%, not 80-90%

| Buggy → Parity | Count |
|---|---:|
| W → W | 12 |
| L → L | 3 |
| T → T | 4 |
| **Total preserved** | **19/35 = 54%** |
| Total flipped (W→L, L→W, ±→T) | 16/35 |

54% is barely above what you'd see if the runs were uncorrelated and
roughly half-and-half W/L. The buggy ranking *was* unreliable per-PR;
parity is not just rescaling the same per-PR signal.

This conflicts with `VERDICT_v2.md` which framed parity as "softer than
feared". It's harder than that.

---

## 6. The real mechanism — joern arm scores went DOWN, not baseline UP

Mean KG-rel score, joern arm:

- Under buggy: **5.69**
- Under parity: **5.34** (Δ = −0.34)

Mean KG-rel score, baseline arm: **5.00** (constant — same headline data
both times).

So the parity correction did not "give the baseline what it was
missing". It **degraded the joern arm** by 0.34 KG-rel points on
average. Adding the PR body to the joern prompt made the joern
review *less effective* per the panel.

The KG-leakage audit confirms this with a different metric: across 35
parity reviews vs 35 buggy reviews, the total caller-signal citation
count is essentially flat (35 vs 34 symbols cited out of 3,586
available — Δ = +1). The LLM does not surface less of the KG under
parity. **What changes is review quality, not KG visibility.**

**Plausible read of why the body hurt the joern arm:**
- Body length is non-trivial: median 652 chars, mean 1,582, max 7,574;
  15/35 PRs have bodies ≥800 chars and 3 have ≥5,000.
- The model splits attention between body content and the KG pack,
  producing more diffuse reviews.
- The structural framing — which the panel rewards as KG-rel — gets
  diluted when the model also tries to engage with the body.

This is not a redundancy story. Whether to call it **interference** is
itself an open question — see the **per-PR falsification check** in
`PER_LANGUAGE_CI_AND_FALSIFICATION.md` §2. That regression of joern-arm
score change on body length finds Pearson r = +0.24 (p=0.165), i.e. the
joern arm did *not* drop more on PRs with longer bodies — the simple
interference hypothesis is not supported. The biggest single drop
(PR15, joern arm −3) had a 376-char body; PR2 with 5,828 chars only
dropped 1 point.

**The most defensible reading:** the parity correction reduced the
joern arm's mean KG-rel by 0.34 points; the mechanism is not yet
identified at the per-PR level. Body-and-KG interference is the
*simplest* hypothesis but the per-PR data do not support it cleanly. A
plausible alternative is that the body content occasionally redirects
the model's attention toward task-specific concerns the panel doesn't
reward as KG-rel — a content-specific effect, not a length effect.

---

## What this means for the thesis

### Claim language to use

✅ **Tree-sitter result remains the headline RQ2 finding.**
> "Tree-sitter-AST KG augmentation produces a moderate positive shift
> on the LLM-judged rubric (d_z=+0.47, n=40, p=0.006) under the
> v2 multi-judge panel."

✅ **Joern parity reported as exploratory replication.**
> "A follow-on Joern CPG-based KG implementation, evaluated under prompt
> body-parity (n=35), produced d_z=+0.30 (Wilcoxon p=0.057,
> bootstrap 95% CI [−0.03, +0.65]). The effect is consistent in
> direction with tree-sitter but does not reach conventional
> significance, with the lower CI bound below zero."

✅ **Per-judge robustness.**
> "All three judges return positive d_z on KG-rel for the parity
> Joern run (range +0.20 to +0.34), so the direction is not driven
> by a single panel member."

✅ **Honest mechanism discussion.**
> "Adding the PR body to the Joern arm's prompt reduced the joern
> arm's mean KG-rel score by 0.34 points and did not measurably
> change baseline scores. We do not have a confirmed mechanism: the
> simplest hypothesis (body–KG interference, i.e. the model's framing
> budget is finite) is *not* supported by a per-PR regression of joern
> arm drop on body length (Pearson r = +0.24, n=35, p=0.165). A
> content-specific account — the body redirects the model toward
> task-specific concerns the panel does not reward as KG-rel — is
> consistent with the data but is not formally tested at this n."

❌ **Do not claim**: "KG context and body are partially substitutable"
   — the body-length regression does not support this; nor is the
   simpler interference account confirmed (per-PR falsification
   r = +0.24, p = 0.17). Frame the parity drop as observed without
   a confirmed mechanism.

❌ **Do not claim**: "Joern significantly improves code review quality"
   — at n=35, Wilcoxon p=0.057, bootstrap CI straddles zero.

❌ **Do not claim**: "Parity preserves the buggy ranking with smaller
   magnitudes" — direction stability is only 54%.

### Threats-to-validity to disclose

- GPT-4o T=0.0 is not bit-deterministic (Jaccard 0.57–0.72).
- 5 Go PRs excluded from Joern (frontend lacks call edges).
- 3-judge panel is 3 commercial LLMs; no human-validated criterion-level
  ground truth for the Joern n=35.
- PR31 fabricates "sklearn/linear_model team" as code owner under
  parity (mutated form of buggy "Danilo Silva"). PR10 and PR42 also
  fabricate sklearn team-shaped attributions.
- Direction stability buggy↔parity is 54%; the buggy ranking did
  not isolate "true" KG benefit.

### Pre-registration check

The pre-registered ANALYSIS_PLAN locks the **human-study κ analysis**,
not the choice of LLM-judge instrument. Pivoting from tree-sitter to
Joern as primary RQ2 instrument is *allowed* but a deviation worth
flagging. See `ANALYSIS_PLAN_CROSSCHECK.md` for the full mapping. The
plan's anti-goalpost-moving rules are about not dropping PRs/criteria
inside the κ analysis; they don't constrain which upstream LLM-judge
run feeds the secondary directional-consistency outcome.

**Recommended position:** keep tree-sitter `kg` as the headline RQ2
result, report Joern parity as an exploratory replication with the
above caveats, and use the gap between Joern strict (+1.34), Joern
parity (+0.30), and tree-sitter (+0.47) as a finding about how
*prompt design and KG implementation jointly determine* measurable
KG augmentation value.

---

## What this means for the human study

The clean-prompt human study now needs to detect a d_z somewhere
between +0.30 (Joern parity) and +0.47 (tree-sitter). With 16 raters ×
6 PRs and Kendall's τ threshold 0.6, this is **possible but tight**.

The strict-prompt arm (d_z=+1.34) remains the higher-power comparison.

**Recommendation, unchanged:** run both arms.

---

## Files that need updating to reflect this synthesis

| File | What to change |
|---|---|
| `FINAL_REPORT.md` | Replace "redundancy mechanism" framing with "interference" interpretation; add "CI straddles zero" caveat to lead. |
| `VERDICT_v2.md` | Replace "softer than feared" framing with "direction stability 54%" finding. |
| `PARITY_RESULTS.md` | Add §"What actually changed: joern arm got worse" with the per-arm score breakdown. |
| `STATUS.md` | Update "key findings" §1 to reflect CI/p-value detail and to retract the redundancy claim. |
| `MEMORY.md` (auto-memory) | Skip — the stable claim is "tree-sitter +0.47 remains headline; Joern parity +0.30 is a weaker exploratory replication." |

---

## What I'd recommend if you have another half-hour with the lab

1. **Add bias-corrected (BCa) bootstrap CI**, not just percentile.
   Percentile bootstrap is known to under-cover with small samples;
   BCa gives a slightly tighter and more honest interval.

2. **Permutation test using a paired structure** (resampling pairs,
   not just sign-flipping deltas). The current permutation test
   matches Wilcoxon's null but a paired-permutation framework gives
   a confidence interval on d_z directly.

3. **Run the Joern parity scoring with a different judge panel**
   (e.g., Claude Sonnet + GPT-4 + Gemini Pro) to test whether the
   d_z=+0.30 is a panel-of-three artefact. Cost: ~$3.

4. **Write a single combined results table** for tree-sitter +
   Joern strict + Joern parity + Joern buggy with consistent CI/p
   columns. Right now they live in separate files with different
   conventions.

5. **Spot-check 3 more PRs** (one W→L flip, one L→W flip, one
   stable W→W) to triangulate why direction stability is only 54%.
   Right now PR31 is the only one we've manually inspected.

None of these are blockers. The honest headline above is defensible
as-is.
