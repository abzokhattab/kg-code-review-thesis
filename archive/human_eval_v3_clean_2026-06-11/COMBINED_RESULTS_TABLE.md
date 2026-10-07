# Combined results table — all four LLM-judge runs, consistent statistics

All d_z values use Cohen's d_z = mean(Δ) / sd(Δ) on paired per-PR deltas.
All p-values are two-sided. Wilcoxon uses normal approximation. Sign test
is exact binomial on non-zero deltas. Permutation test uses 10,000 sign-flip
reps. Bootstrap CI is percentile, 10,000 resamples (BCa values for parity
are in `BCA_BOOTSTRAP.md`). Random seed = 42.

## KG-rel subscale (9 KG-relevant criteria: F3, F4, T1, T2, T3, M1, M3, C2, Q2)

| Run | n | mean Δ | sd Δ | d_z | Wilcoxon p | sign p | perm p | 95% CI on d_z |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| tree-sitter `kg` (pre-registered) | 40 | +0.600 | 1.277 | **+0.470** | 0.0058 | 0.0290 | 0.0082 | [+0.167, +0.832] |
| Joern strict prompt (forced 9-criterion coverage) | 35 | +2.200 | 1.641 | **+1.340** | 0.0000 | 0.0000 | 0.0000 | [+1.092, +1.781] |
| Joern clean prompt — body OMITTED (buggy, retracted) | 35 | +0.686 | 1.183 | **+0.580** | 0.0028 | 0.0059 | 0.0026 | [+0.250, +1.014] |
| Joern clean prompt — body PARITY (current Joern headline) | 35 | +0.343 | 1.136 | **+0.302** | 0.0573 | 0.3833 | 0.1154 | [-0.025, +0.649] |

## Total score (all 25 criteria)

| Run | n | mean Δ | sd Δ | d_z | Wilcoxon p | sign p | perm p | 95% CI on d_z |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| tree-sitter `kg` (pre-registered) | 40 | +0.625 | 1.917 | **+0.326** | 0.0464 | 0.1628 | 0.0559 | [+0.021, +0.675] |
| Joern strict prompt (forced 9-criterion coverage) | 35 | +4.200 | 2.361 | **+1.779** | 0.0000 | 0.0000 | 0.0000 | [+1.422, +2.383] |
| Joern clean prompt — body OMITTED (buggy, retracted) | 35 | +1.171 | 1.932 | **+0.606** | 0.0018 | 0.0037 | 0.0015 | [+0.271, +1.031] |
| Joern clean prompt — body PARITY (current Joern headline) | 35 | +0.629 | 1.942 | **+0.324** | 0.0652 | 0.0708 | 0.0771 | [+0.000, +0.735] |

## Reading guide

- **Pre-registered headline**: tree-sitter `kg` row. This is what the
  ANALYSIS_PLAN locked. n=40 because tree-sitter parses Go.
- **Joern strict**: exploratory upper bound under a prompt that *mandates*
  coverage of the 9 KG-relevant criteria. The d_z is large but the prompt
  is biased toward the rubric.
- **Joern clean buggy**: the joern arm was missing the PR body in its
  prompt while baseline had it. **Confound.** Reported only for traceability.
- **Joern clean parity**: same prompt for both arms. The principled Joern
  comparison. Effect direction is consistent with tree-sitter but does not
  reach p<0.05 in any of three tests, and the bootstrap CI straddles zero.

## Judge panel note

**The Joern strict run used a different judge panel from all other runs.**

| Run | Judge panel |
|---|---|
| Tree-sitter `kg` | gpt-4o-mini + gpt-4o + gemini-2.5-flash (3-judge) |
| Joern parity | gpt-4o-mini + gpt-4o + gemini-2.5-flash (3-judge) |
| Joern strict | gemini-2.5-flash + gemini-2.0-flash (2-judge Gemini-only) |

The strict d_z=+1.340 is therefore not directly comparable to the other
rows. Panel-controlled recompute (gemini-2.5-flash scores only, same
judge on both sides): **d_z=+1.071** (Wilcoxon p<0.0001, CI [+0.791,
+1.478]). The ~0.27 difference between raw (+1.34) and panel-controlled
(+1.07) is the judge-panel inflation component.

The Joern runs use n=35 (Go excluded — Joern frontend lacks call edges).
Tree-sitter uses n=40 (its parser supports Go via tree-sitter-go).
Joern strict and buggy share the same 35 PRs but use different prompts.
Joern buggy and parity share the same prompt structure except for the body block.

The **buggy → parity** drop on KG-rel (d_z +0.58 → +0.30) reflects the joern
arm's mean KG-rel score *decreasing* by 0.34 points (5.69 → 5.34) when the
body is added to its prompt; baseline scores are unchanged across the two
Joern runs because they come from the same headline file. See `HONEST_HEADLINE.md`
§6 for the post-falsification interpretation (no confirmed mechanism).
