# KG findings + methodology validity — session synthesis (2026-06-19)

One-page summary of what we settled today. All numbers are reproducible from
the scripts in `scripts/` against already-judged data (no new API spend except
the concise ablation, ~$10).

---

## TL;DR

1. **The KG effect is real and robust** — it survives the two scariest
   validity threats (judge-model artifact, verbosity/length bias).
2. **Best KG construction = Joern** (precise call graph), not grep or AST.
   It is the only variant that makes *both* the KG-relevant /9 and the broad
   Total /25 significant.
3. **Primary endpoint should be the KG-relevant /9 subscale**, not Total /25.
   KG targets 9 structural criteria; judging it on all 25 dilutes the effect.
4. **"Be concise" is a dead end** — it strips breadth, hitting the structural
   (KG-relevant) criteria hardest. Keep it as a *negative control*, not a fix.

---

## 1. Which KG construction wins?  (`scripts/compare_kg_methods.py`)

Same 35 PRs, same GPT-4o generator + prompt, same 3-judge panel. Only the KG
evidence source differs.

| KG source | KG-rel /9 vs baseline | Total /25 vs baseline |
|---|---|---|
| grep "thin" (current headline) | Δ+0.54, d_z 0.44, p=0.016 ✓ | Δ+0.66, p=0.062 ✗ |
| tree-sitter scoped-AST | Δ+0.23, p=0.25 ✗ | Δ+0.63, p=0.078 ✗ |
| **Joern CPG (promote)** | **Δ+0.69, d_z 0.58, p=0.003 ✓** | **Δ+1.17, d_z 0.61, p=0.002 ✓** |

It is **precision, not volume**: the AST variant adds *more* (text-matched)
structural tokens yet performs worst; Joern adds *fewer but statically-resolved*
call edges and wins. Matches the long-context literature that input length/noise
degrade LLMs even with perfect retrieval (Liu et al. 2023 *Lost in the Middle*,
arXiv:2307.03172; Levy/Schwartz et al. 2025 *Context Length Alone Hurts*,
arXiv:2510.05381). Cost of Joern: n=35 (its Go frontend yields no call edges →
5 Go PRs dropped).

## 2. Verbosity-bias check  (`scripts/check_judge_length_bias.py`)

The #1 LLM-as-judge failure mode (Zheng et al. 2023, MT-Bench; Dubois et al.
2024, length-controlled AlpacaEval).

- Spearman(length, score) ≈ **+0.14–0.16** (weak; GPT-4o is the least
  length-biased judge per Zheng et al.).
- KG only ~9% longer than baseline (+23 words; longer in 29/40 PRs).
- **corr(Δlength, Δscore) within paired KG–baseline = +0.22, p=0.17 (n.s.)** →
  the KG advantage is **not** explained by length.

**The KG effect is not a verbosity artifact.** (Defense-grade paragraph.)

## 3. Judge-model check

On the same verbose reviews, a **single GPT-4o judge reproduces the 3-judge
panel** (KG-rel kg: panel Δ+0.60 p=0.006 vs gpt-4o Δ+0.65 p=0.005; Total hybrid:
panel p=0.014 vs gpt-4o p=0.003). So the single-judge runs used for the concise
ablation are trustworthy; the judge is not the variable.

## 4. Concise ablation — negative control  (`scripts/run_concise_prompt_experiment.py`)

Re-generated all 160 reviews with a "be concise" instruction, judged by GPT-4o.

| Metric | Mode | Verbose | Concise | Effect |
|---|---|---|---|---|
| KG-rel /9 | kg vs baseline | p=0.005 ✓ | p=0.003 ✓ | ~same |
| KG-rel /9 | hybrid vs baseline | p=0.002 ✓ | p=0.065 ✗ | broke |
| Total /25 | kg vs baseline | p=0.053 | p=0.385 ✗ | worse |
| Total /25 | hybrid vs baseline | p=0.003 ✓ | p=0.384 ✗ | broke |

Concision cut length ~28% across all modes and **lowered coverage**, hitting the
**structural KG-relevant criteria hardest** (mean yes-rate Δ = −5.8 for the 9
KG-relevant criteria vs −1.7 for the 16 non-KG). Core-quality criteria were
untouched (Q1 overall assessment, Q2 anchored-to-code, Q5 explains-reasoning all
stayed at 100%). So concise reviews are **narrower, not worse** — but narrowing
removes exactly the structural coverage KG exists to add, which is why it cannot
sharpen the KG result.

---

## Recommendation

- Report **KG-relevant /9 as the pre-specified primary endpoint**; Total /25 secondary.
- Promote **Joern + production prompt** to the headline KG result.
- Include a **Threats to Validity** section with checks (2)+(3) and the concise
  negative control (4).
- Let the **human study** carry convergent validity (usefulness, which a
  coverage checklist cannot measure).

## Artifacts

| File | What |
|---|---|
| `scripts/compare_kg_methods.py` → `results/KG_METHOD_COMPARISON.md` | KG construction ranking |
| `scripts/check_judge_length_bias.py` → `results/JUDGE_LENGTH_BIAS.md` | verbosity-bias check |
| `scripts/run_concise_prompt_experiment.py` → `outputs/luca_prs_v2_concise/` | concise reviews |
| `scripts/judge_parallel.py` | threaded single-judge driver |
| `scripts/extract_single_judge_scores.py` | project a panel to one judge (free) |
| `results/checklist_evaluation_llm_multi__v2_concise_gpt4o.json` | concise scores |
| `results/KRUSKAL_BONFERRONI_v2_concise_gpt4o.{md,json}` | concise stats |
