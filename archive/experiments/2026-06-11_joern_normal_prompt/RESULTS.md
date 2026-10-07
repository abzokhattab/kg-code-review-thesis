# Clean Joern Run — Joern KG + Normal Prompt

**Date:** 2026-06-11
**Question:** Does Joern's precise call-graph context improve LLM review quality
*under the same prompt as the headline experiment* (no mandatory-coverage checklist)?

This fills the missing cell in the headline matrix. The previous Joern run
(`experiments/2026-05-15_joern_kg_main/`) used a strict prompt that mandated
coverage of the 9 KG-relevant criteria — circular and confounded. This run
uses the production `SYSTEM_PROMPT_KG` from `prnote/note.py` (no MUSTs).

---

## Configuration

| Parameter | Value |
|---|---|
| Generator | GPT-4o, T=0.0 |
| KG | Joern CPG (reused from `experiments/2026-05-15_joern_kg_main/evidence/`) |
| Prompt | `SYSTEM_PROMPT_KG` from `prnote/note.py` (matches tree-sitter headline) |
| Judges | GPT-4o-mini + GPT-4o + Gemini 2.5 Flash, majority vote |
| n | 35 (5 Go PRs excluded — Joern Go frontend has no call edges) |
| Cost | $1.11 |

---

## Headline result

**Joern + normal prompt vs baseline (paired, n=35):**

| Metric | Δ mean | 95% CI | p (perm, B=20k) | Cohen's d_z |
|---|---:|---:|---:|---:|
| Total /25 | **+1.17** | [+0.54, +1.80] | **0.0014** | +0.61 |
| KG-relevant /9 | **+0.69** | [+0.31, +1.09] | **0.0029** | +0.58 |

**KG-rel W/T/L vs baseline: 21W / 8T / 6L**

Mean scores:
- baseline (n=35): total = 8.94, KG-rel = 5.00
- joern_normal:    total = 10.11, KG-rel = 5.69

---

## Comparison to other experiments

| Setup | KG | Prompt | n | KG-rel d_z | KG-rel p | Status |
|---|---|---|---|---:|---:|---|
| Headline (tree-sitter) | tree-sitter AST | normal | 40 | +0.47 | 0.007 | clean, current headline |
| Joern strict (existing) | Joern CPG | strict (mandates 9 criteria) | 35 | +1.34 | <0.0001 | confounded |
| **Joern clean (this run)** | **Joern CPG** | **normal** | **35** | **+0.58** | **0.0029** | **clean, replaces tree-sitter as the principled headline** |

### What this tells us

1. **Joern under a fair prompt produces a clean, significant effect.** d_z=+0.58 on
   KG-relevant criteria, p=0.003. Slightly *larger* than the tree-sitter headline
   (+0.47) — Joern does add real signal.
2. **The +1.34 in the strict-prompt experiment was inflated by the prompt confound.**
   Going from strict to normal prompt with the same KG drops the effect from
   d_z=+1.34 to d_z=+0.58 — most of that delta was the prompt mandating coverage,
   not the KG.
3. **Joern's signal beats tree-sitter's.** d_z +0.58 > +0.47, on a smaller sample
   (35 vs 40), with the same prompt and same generator. The improvement is modest
   but consistent with the qualitative story (Joern finds real callers; tree-sitter
   finds almost none).
4. **Total score is now also significant** (p=0.0014, d_z=+0.61). The tree-sitter
   headline missed total significance (p=0.054). With Joern, KG context improves
   *general* review coverage too, not only the structural-knowledge criteria.

---

## Sensitivity: 2-OpenAI judges only (Gemini removed)

Re-aggregated using only GPT-4o-mini + GPT-4o (2-of-2 majority, ties → 0):

| Metric | Δ mean | p | d_z |
|---|---:|---:|---:|
| Total /25 | +0.69 | 0.061 | +0.35 |
| KG-relevant /9 | **+0.69** | **0.006** | **+0.54** |

The KG-relevant effect survives Gemini removal (d_z drops from +0.58 to +0.54,
remains p<0.01). Gemini is not driving the headline; the cross-family panel is
behaving as a noise reducer rather than a tip-the-scale judge. Total score
loses significance, which mirrors the tree-sitter headline pattern.

---

## What this means for the thesis

The headline can move from tree-sitter (n=40, d_z=+0.47) to Joern + normal
prompt (n=35, d_z=+0.58). This is the principled choice:

- Joern is the actual KG implementation in production (`experiments/2026-05-15_joern_kg_main/`).
- The +1.34 strict-prompt number can stay in the doc as an *exploratory upper bound*.
- The tree-sitter result becomes a development-history artefact, not the headline.

The Joern Go frontend limitation (5 Go PRs excluded) is the price of the change:
n=35 instead of n=40. Worth it.

---

## Files

| Path | Description |
|---|---|
| `reviews/pr*_kg.md` | 35 generated reviews |
| `scores/pr*_kg.json` | 3-judge panel scores per review |
| `scores_2openai_only.json` | 2-OpenAI-only sensitivity aggregate |
| `usage_log.jsonl` | Token usage per API call |
| `run.py` | Reproducible run script (idempotent) |
| `run.log` | Run output |
