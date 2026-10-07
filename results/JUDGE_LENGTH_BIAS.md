# Verbosity-bias check — is the KG effect a length artifact?

Inputs: `results/checklist_evaluation_llm_multi__v2_gpt4o_only.json` + `outputs/luca_prs_v2/pr*_*.md` (length in words). No API calls.

## Global length sensitivity (all reviews)

- Spearman(length, total /25) = **+0.14** (p=0.068)
- Spearman(length, KG-rel /9) = **+0.16** (p=0.049)

## Is KG's win mediated by length? (paired kg vs baseline)

- n = 40 PRs; KG longer than baseline in **29/40** (mean Δlen = +23 words)
- corr(Δlength, Δtotal) = **+0.22** (p=0.172)
- corr(Δlength, ΔKG-rel) = **+0.20** (p=0.207)

## Conclusion

Length correlates only weakly with score, and the KG score advantage is **not** significantly explained by the KG length advantage. The KG-vs-baseline effect is **robust to verbosity bias** — it is not an artifact of KG reviews being longer. (Consistent with Zheng et al. 2023 finding GPT-4 is the least length-biased judge.)