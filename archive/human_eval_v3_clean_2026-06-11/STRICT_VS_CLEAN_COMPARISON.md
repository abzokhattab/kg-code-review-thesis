# Strict-prompt vs clean-prompt — the trade-off, in numbers

**Question:** the user reported "the reviews are similar." Does the
clean-prompt run actually fix that, or does it make it *worse* by
dropping the visible structural-context citations the strict prompt
forced into the review text?

**Source:** the 4 PRs that overlap between `human_eval_v3/` (strict
prompt) and this pilot (clean prompt) — PR22, PR31, PR38, PR47.

---

## Punchline

**The strict prompt produces reviews that are visibly more
*differentiated* than the clean prompt** — by 2-9× on named-entity
count for the same PR. The clean prompt produces a real statistical
effect (d_z=+0.58 KG-rel) but **surrenders the visible-to-rater
structural-context citations** that make the difference legible.

This is exactly the user's complaint, and **the pilot does not fix
it. It makes it worse on 3 of the 4 overlapping PRs.**

## The numbers

Named entities (file paths, file:line, backticked symbols) that
appear in only one of the two reviews per pair — i.e. visible
differentiators a rater can point to:

| PR | STRICT differentiators | CLEAN differentiators | Direction |
|---:|---:|---:|:---|
| 22 | 17 | 5 | Strict 3.4× more |
| 31 | 13 | 12 | About even |
| 38 | **17** | **2** | **Strict 8.5× more** |
| 47 | 22 | 8 | Strict 2.75× more |

Length ratios (Joern / baseline) — both are within reasonable bounds:

| PR | STRICT ratio | CLEAN ratio |
|---:|:---:|:---:|
| 22 | 1.23 | 1.15 |
| 31 | 1.28 | 1.09 |
| 38 | 1.45 | 1.18 |
| 47 | 1.05 | 1.11 |

## What this looks like in practice — PR38 example

**Strict-prompt Joern review** explicitly cites:
- `GrafanaRoute.tsx` (caller, from KG)
- `interceptLinkClicks.ts` (caller, from KG)
- `processRedirectUri` (the changed function, by name)
- `stripBaseFromUrl` (a related function it depends on)
- `location.test.ts` in two distinct paths (KG-supplied test list)
- 4 numbered concerns including "Integration Risk" naming the callers

**Clean-prompt Joern review** cites:
- `location.ts:172-176` (same as baseline)
- `location.test.ts:340-367` (same as baseline)
- 3 generic concerns indistinguishable from baseline

The KG data was **the same in both runs** — it's the same Joern
evidence pack on disk. The strict prompt forced the LLM to weave it
into the review; the normal prompt let the LLM ignore it.

## What this means

### For the thesis headline (RQ2)
The clean Joern + normal-prompt run is still the **right** number to
report (d_z=+0.58, p=0.003). It's the principled, no-confound effect
size. Nothing about this audit invalidates that. The LLM-judge picks
up on subtle phrasing differences even when explicit caller names
aren't in the text.

### For the human study (RQ3)
This is where the trade-off bites. The human study is asking
*humans* to detect the difference. Humans need visible
differentiators. The clean prompt strips them out.

### The honest framing

There are two distinct experiments hiding inside RQ3:

1. **"Is the clean Joern d_z=+0.58 detectable by humans?"** —
   pilot answers this. Probably "yes on the win PRs, ambiguous on
   the ties." Expected Kendall's τ ≈ 0.7 from my self-rating.

2. **"Is the strict-prompt d_z=+1.34 detectable by humans?"** —
   the existing `human_eval_v3/` answers this. Probably "yes more
   strongly" — strict reviews have more visible differentiators.

These are *different questions*. The user assumed the clean version
strictly dominates the strict one. **It doesn't, for the rater
experience.** The clean version dominates for **statistical
honesty**; the strict version dominates for **visible KG signal**.

## What I'm now recommending

Three options, ranked:

### Option 1 (recommended) — Run both
- Keep `human_eval_v3/` (strict) live.
- Run this pilot (clean) on a small set of raters as a **second
  arm**, not a replacement.
- Report both in the thesis: "humans agree with the LLM-judge
  ranking under the clean prompt with τ=X, under the strict prompt
  with τ=Y." If both are >0.6, the convergent-validity claim is
  *stronger* than either alone.
- Cost: ~$0 (reviews already exist), just need raters' time.

### Option 2 — Replace and accept the cost
- Swap to clean. Some PRs (especially PR38) will be hard for raters,
  with low signal-to-effort ratio.
- Get a clean alignment with the headline.
- Risk: lower power; raters give "no preference" more often.

### Option 3 — Keep strict, document the prompt confound louder
- Don't change the human study.
- In the thesis, frame RQ3 as: "validates the LLM-judge ranking
  under the strict-prompt setup, which is a stress test of whether
  the rubric is interpretable across model families."
- This is what the existing `THESIS_OVERVIEW_FOR_JUDGE.md` already
  half-says.

## My honest verdict on the user's two questions

**Q: Is the experiment solid?**
**A: Yes.** The clean-Joern run reproduces, the prompt is genuinely
clean, judge panel is uniform, the d_z=+0.58 effect is real and
sensitivity-robust. See `EXPERIMENT_AUDIT.md`.

**Q: Is the user study at its best shape?**
**A: It depends what "best" means.**
- If "best" = aligned with the headline → clean prompt wins.
- If "best" = maximum chance of raters detecting the effect → **strict
  prompt wins**, by 2-9× more visible differentiators per pair.
- If "best" = both axes → run both arms (Option 1). The reviews
  already exist; you only need rater time.

The pilot folder I built is a **valid, principled second arm** to
the existing human study. **It is not a strict upgrade**, and I
don't recommend swapping it in as the only study.
