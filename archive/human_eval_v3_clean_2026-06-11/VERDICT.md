# Verdict — clean Joern + normal prompt pilot, 2026-06-11

**Asked:** "tell me the experiment is solid and the user study is at the best shape."

**Answered (TL;DR):**

| Question | Verdict | Confidence |
|---|---|---|
| Is the **experiment** solid? | **Yes.** Publishable. Replaces tree-sitter as the principled headline. | High |
| Is the **user study at the best shape**? | **No — but not for the reason you thought.** | High |

---

## Detailed verdicts

### 1. Experiment soundness: **PASSED**

Independent recompute against raw files matches `RESULTS.md` to 3
decimals. Prompt is genuinely clean (no MUSTs, no mention of the 9
KG-relevant criteria). Judge panel uniform across all 35 PRs. p-values
reproduce. Sensitivity (2-OpenAI judges only) holds. **See
`EXPERIMENT_AUDIT.md` for the 5-check audit trail.**

Headline (clean): **n=35, KG-rel d_z=+0.58, p=0.003, total d_z=+0.61,
p=0.001.** This is the principled number. It replaces the tree-sitter
+0.47 (n=40) as the thesis headline, and supersedes the strict-prompt
+1.34 (which is reported as an exploratory upper bound).

Nothing in the audit blocks publication. There's a small list of
hygiene items for the methodology chapter — disclosed in the audit
file, not blocking.

### 2. User study shape: **NOT YET OPTIMAL**

The user's instinct that the strict-prompt review pairs are "too
similar" and should be replaced by clean-prompt pairs **was half
right**:
- Right that the strict-prompt human study has a confound (it does).
- Wrong that the clean prompt makes the rater's job easier. **It
  makes it harder on most overlapping PRs.**

I quantified this directly. On the 4 PRs that overlap between the
existing study and the pilot:

| PR | Strict-prompt visible differentiators | Clean-prompt visible differentiators |
|---:|---:|---:|
| 22 | 17 | 5 |
| 31 | 13 | 12 |
| 38 | **17** | **2** |
| 47 | 22 | 8 |

The strict prompt produced reviews that **explicitly cited Joern's
caller files in the review text** (`GrafanaRoute.tsx`,
`interceptLinkClicks.ts`, `CreateNodeCommand.java::run`, etc.). The
clean prompt let the LLM ignore the KG context — so even when the KG
data was identical on disk, it disappeared from the review text. **See
`STRICT_VS_CLEAN_COMPARISON.md` for full numbers and PR38 example.**

This is the "two reviews are similar" problem the user reported.
Replacing the strict pairs with clean pairs would make 3 of 4
overlapping PRs *harder* to differentiate, not easier.

---

## What's actually optimal — recommendation

**Run BOTH human studies. Don't replace.**

### Why

Each answers a different question:

1. **Strict-prompt study** (existing `human_eval_v3/`): "do humans
   agree with the LLM-judge ranking when the KG signal is forced
   into the review text?" Tests whether the rubric and judges
   are interpretable to humans when the input is rich.

2. **Clean-prompt study** (this pilot): "do humans agree with the
   LLM-judge ranking under the same prompt as the headline?" Tests
   whether the **published** d_z=+0.58 effect is human-detectable.

The thesis is *stronger* if both return τ > 0.6 (the pre-registered
"validated" threshold) than if either does alone.

### Cost
- Reviews already exist for both arms.
- Pilot folder is built and self-contained at
  `human_eval_v3_clean_2026-06-11/`.
- Webhook is disabled (backup-only) so test runs don't pollute the
  live study.
- LocalStorage namespace is separate (`heval5c_*`).
- Only cost is rater time — and you can recruit the same raters or
  fresh ones; the analysis plan doesn't require independence.

### What to do when you're back

1. Open `human_eval_v3_clean_2026-06-11/index.html` locally
   (`python3 -m http.server 8000`) and rate one PR yourself. Compare
   the experience to the live study.
2. If the differentiators-per-PR feel adequate, run the pilot on
   2-3 raters as a "phase 2" of the human study (after the strict
   study completes), with separate rater IDs.
3. If the differentiators feel sparse, **read PR38 closely** — that's
   the worst case. If you can pick a side on PR38 with reasonable
   confidence based on the prose alone, the pilot will work for
   raters too. If not, swap PR38 for PR42 or PR48 and regenerate.

---

## Files in this folder

| File | What it tells you |
|---|---|
| `VERDICT.md` (this file) | Top-line yes/no |
| `EXPERIMENT_AUDIT.md` | 5-check soundness audit of the clean-Joern run |
| `PILOT_SELF_RATING.md` | I rated all 6 pairs myself; agreed with LLM judges 5/6 |
| `NAMED_ENTITY_AUDIT.md` | Per-PR visible-differentiator counts for the pilot |
| `STRICT_VS_CLEAN_COMPARISON.md` | The trade-off comparison — the key insight |
| `README.md` | Folder description, run instructions |
| `study_data.json` | The pilot study payload (6 PRs × 2 modes) |
| `index.html` | Pilot UI (webhook disabled, namespace bumped) |
| `README.md.original` | Copy of the original `human_eval_v3/README.md` |

---

## What I changed in the live study

**Nothing.** The live `human_eval_v3/` is untouched. The pilot lives
entirely in this dated folder. You can keep it, throw it away, or
swap it in — the choice is open.

---

## Residual risks I want to flag

### Risk 1: PR31 inversion

In my self-rating, PR31 is the one PR where I would prefer baseline
even though LLM judges scored Joern +3 KG-rel. Joern's review for
PR31 fabricates a code owner ("Danilo Silva") and gets a technical
claim wrong (`X_offset_` initialization). If real human raters also
prefer baseline on PR31, that's:
- ✓ a finding worth reporting in RQ3 ("LLM judges reward the *shape*
  of structural claims even when the content is wrong")
- ✗ but it pulls the Kendall's τ down a notch

This affects both the strict and clean studies (PR31 is in both).
Not a pilot-specific issue.

### Risk 2: PR15's length ratio (1.38)

The pilot's PR15 baseline:joern ratio is 1.38, over the
pre-registered length-disparity threshold of 1.2. Mitigation: the
ANALYSIS_PLAN.md already specifies a length-controlled sensitivity
analysis. PR15 will be flagged in that sensitivity. **Not a blocker;
do not swap it out.**

### Risk 3: Generator robustness re-test

The strict-prompt run had a Gemini-generator robustness check; the
clean-prompt run does not. Cost to add: ~$1.10. **Recommended for
the methodology chapter** but not blocking the human study.

---

## Bottom line, one sentence

The clean experiment is solid and ready for the thesis headline; the
existing human study is the right shape for *its* question (does
human preference track LLM-judge ranking under structured-output
constraints) and the pilot is the right shape for the *new* question
(does it track under the same prompt as the headline) — run both,
don't replace.
