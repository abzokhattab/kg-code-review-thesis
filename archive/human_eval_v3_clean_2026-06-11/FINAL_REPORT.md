# Final report — clean Joern audit, post-parity, 2026-06-11

> ⚠️ **SUPERSEDED 2026-06-11 (later same day) by `HONEST_HEADLINE.md`.**
> The robustness battery (`ROBUSTNESS_BATTERY.md`) found that:
> - 95% bootstrap CI on the parity d_z **straddles zero** ([−0.03, +0.65]).
> - Sign-test p=0.383 and permutation p=0.112 — only Wilcoxon (0.066)
>   came close to significance.
> - The "body-redundancy mechanism" claim below is **not supported** by
>   the body-length regression (Pearson r=+0.13, the wrong sign).
> - Direction stability buggy↔parity is **54%**, not the "softer than
>   feared" picture this doc paints.
> - The real mechanism: parity *reduced the joern arm's mean KG-rel
>   score by 0.34*; baseline was unchanged. Body and KG **interfere**,
>   they don't substitute.
>
> Read `HONEST_HEADLINE.md` for the corrected synthesis. The
> bullets below remain useful as a snapshot of mid-audit thinking but
> the framing has been retracted.

---


**Read this first when you're back.** Everything else is supporting evidence.

---

## The bottom line in three numbers

| Configuration | n | KG-rel d_z | p-value | Status |
|---|---:|:---:|:---:|---|
| Buggy clean prompt (body omitted from joern) | 35 | +0.580 | 0.003 | **Confound — discard** |
| **Parity-corrected clean prompt (body included)** | **35** | **+0.302** | **0.066** | **Principled headline** |
| Strict prompt (forced 9-criterion coverage) | 35 | +1.34 | <0.0001 | **Exploratory upper bound** |

The principled clean-prompt comparison shows a small positive effect of
KG augmentation that **does not reach conventional p<0.05 significance**
at n=35.

The strict-prompt comparison shows a large effect with high power, but
under a prompt that *mandates* coverage of the KG-relevant rubric items.

**Both are honest results. Neither is a slam-dunk.**

---

## What the deep audit changed in my understanding

1. **The body-parity bug had inflated the headline.**
   Mechanistic explanation: PR descriptions in this dataset already
   contain a lot of KG-relevant information (function names, callsite
   summaries, test rationale). When the baseline arm received the body
   but the joern arm did not, the joern arm was using KG to *rebuild*
   what the body would have given for free. With both arms equal, KG's
   *marginal* contribution drops from +0.58 to +0.30.

2. **Per-language: parity changes the picture.**
   Buggy run had Python d_z=+1.14 and TypeScript d_z=+1.41. Parity
   collapses these to **Python d_z=0.00** and **TypeScript d_z=+0.54**.
   The Python collapse is the most striking — Python PR descriptions
   in this dataset must be unusually rich. C++ moves from −0.22 to 0.00
   (still null). Java is the only stratum where parity raises the
   number (+0.45 → +0.58).
   See `DEEP_AUDIT_PARITY.md` vs `DEEP_AUDIT.md`.

3. **The "Danilo Silva" fabrication on PR31 persists** even with the
   body included. The parity review for PR31 now claims a "sklearn/
   linear_model team" code owner — neither in the body nor anywhere
   else in the evidence. **This is still a fabrication.** The model
   is *categorically* prone to inventing authorial metadata when the
   review template has a "Code Owner" slot.

4. **However, most of the *new* owner claims under parity are real.**
   23/35 parity reviews name an owner. Spot-checked PR40 ("Sean Quah"),
   PR29 ("Ken Huang"), PR41 ("Apoorv Mittal"), PR39, PR24 ("@OmarManzoor")
   all appear verbatim in the PR body's "Reviewers:" line (Apache Kafka
   convention) or `cc @user` line. This is correct extraction, not
   hallucination — the LLM is doing its job here.

5. **The earlier hallucination audit was on the buggy reviews.** The
   parity-run hallucination rate is plausibly *lower* (because the
   model has the body to ground claims in). I did not re-run the
   full hallucination audit on parity in the time available.

---

## What this means for the thesis

### Claim language to use

✅ "Joern KG augmentation produces a small positive shift on the
LLM-judged rubric (d_z=+0.30, p=0.07, n=35) under a prompt that does
not mandate structural-context coverage. Under a strict-coverage
prompt, the effect grows to d_z=+1.34 (p<0.0001), but this number
should be interpreted with the caveat that the prompt biases the
model toward the rubric."

❌ "Joern KG augmentation significantly improves code review quality"
— not supported at p<0.05 under the principled comparison.

✅ "Per-language stratification reveals Java as the strongest
beneficiary (d_z=+0.58) and Python as null (d_z=0.00). The Python
result is consistent with the hypothesis that PR descriptions and
KG context provide redundant signals for code review LLMs."

✅ "PR descriptions and KG context are partially substitutable as
sources of structural review-relevant information. KG augmentation
appears most valuable when PR descriptions are sparse." — this is
a thesis contribution arising from the parity finding.

### Threats-to-validity to disclose

- **GPT-4o T=0.0 is not bit-deterministic** (Jaccard 5-gram 0.57-0.72
  across runs). Single-point d_z estimates have non-zero noise.
- **5 Go PRs excluded** (Joern's Go frontend lacks call edges).
  Excluding them shifts tree-sitter d_z by only −0.034, so this is
  a low-impact exclusion.
- **The judge panel is 3 commercial LLMs.** No human-validated
  ground truth at the criterion level for n=35.
- **PR31 demonstrates a fabrication failure mode** even when the
  body is provided.

---

## What about the human study

The clean-prompt human study now needs to detect a d_z=+0.30 effect.
With 16 raters × 6 PRs and a Kendall's τ threshold of 0.6, this is
**possible but tight**. The strict-prompt arm (d_z=+1.34) has much
higher power.

**Recommendation, unchanged:** run both arms. The clean-prompt arm
tests the principled-but-small effect; the strict-prompt arm tests
whether human raters track LLM judges under forced-coverage. Reporting
both — and reporting the gap between them — is the honest move.

---

## What I would do next (if you have another half-hour)

1. **Re-run hallucination audit on parity reviews** (`hallucination_audit.py`
   pointed at the parity scores dir). Report whether the unverified-citation
   rate drops from 29% with the body included.

2. **Re-run KG-leakage audit on parity reviews.** Hypothesis: with
   the body present, the LLM cites *fewer* KG signals because the
   body is a substitute. If true, this confirms the redundancy
   mechanism.

3. **Bootstrap CI on the parity d_z.** Resample the 35 PRs with
   replacement 1000× to get a 95% CI on +0.30. Tells you whether
   the lower bound is above zero.

4. **Decide whether to swap the human study to parity reviews.** The
   parity reviews are cleaner methodologically, but the user pilot
   was built on the buggy ones. A swap means regenerating
   `study_data.json` and re-validating the 6 PRs feel rateable.
   Probably not worth doing if the buggy reviews already have the
   structural framing.

---

## Files

| File | Purpose |
|---|---|
| **THIS FILE (`FINAL_REPORT.md`)** | What you're reading |
| `STATUS.md` | Audit-task status board |
| `VERDICT_v2.md` | Top-line synthesis (now updated for parity) |
| `PARITY_RESULTS.md` | Buggy vs parity numbers + per-PR shifts |
| `DEEP_AUDIT_PARITY.md` | Per-criterion + per-language on parity scores |
| `DEEP_AUDIT.md` | Same on the buggy scores (kept for traceability) |
| `HALLUCINATION_AUDIT.md` | File-citation + owner audit (buggy run) |
| `KG_LEAKAGE_AUDIT.md` | How much of KG ends up in review text (buggy) |
| `REPRO_AUDIT.md` | T=0.0 reproducibility spot-check |
| `UNKNOWN_UNKNOWNS_AUDIT.md` | 5 sanity probes (clean) |
| `EXPERIMENT_AUDIT.md` | Original 5-check soundness audit |
| `STRICT_VS_CLEAN_COMPARISON.md` | Named-entity trade-off |
| `NAMED_ENTITY_AUDIT.md` | Pilot-PR differentiator counts |
| `PILOT_SELF_RATING.md` | I rated 6 pairs; agreed with judges 5/6 |
| `VERDICT.md` | Original surface verdict (before deep audit) |

| Script | Purpose |
|---|---|
| `parity_compare.py` | Computes parity-vs-buggy d_z and Wilcoxon |
| `deep_audit.py [parity\|buggy]` | Per-criterion + per-language analysis |
| `hallucination_audit.py` | File-citation verification |
| `kg_leakage_audit.py` | KG-signal-in-review-text count |
| `repro_check.py` | T=0.0 spot-check on PR1 + PR31 |
