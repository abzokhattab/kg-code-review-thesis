# Statistics validation — hand-rolled vs scipy

All numbers are on the **parity Joern KG-rel deltas** (n=35).
Sample: [-1, 0, -1, 0, 2, 0, 2, 1, 2, 0, 0, 0, -2, -1, 1, -1, 0, 2, 0, -1, 1, 0, 2, -1, 2, 2, 1, 2, 0, 0, 0, -1, 0, 0, 1]

## Wilcoxon signed-rank (two-sided)

| Source | p-value |
|---|---:|
| **My normal-approximation** | 0.0573 |
| scipy default (auto)        | 0.0573 |
| scipy method=exact          | 0.0701 |
| scipy method=approx (no continuity correction) | 0.0573 |

## Sign test

Counts: positive=13, negative=8

| Source | p-value |
|---|---:|
| **My exact binomial** | 0.3833 |
| scipy binomtest       | 0.3833 |

## Pearson r (body length, KG-rel delta)

| Source | r |
|---|---:|
| **My implementation** | +0.1291 |
| scipy.stats.pearsonr  | +0.1291 |

## Spearman ρ

| Source | ρ |
|---|---:|
| **My implementation** | +0.0933 |
| scipy.stats.spearmanr | +0.0933 |

## Bootstrap percentile 95% CI on d_z (10,000 resamples)

| Source | low | high |
|---|---:|---:|
| **My implementation (random seed=42)** | -0.0267 | +0.6526 |
| scipy.stats.bootstrap method=percentile | -0.0260 | +0.6565 |

## Bootstrap BCa 95% CI on d_z (10,000 resamples)

| Source | low | high |
|---|---:|---:|
| **My implementation** | -0.0472 | +0.6396 |
| scipy.stats.bootstrap method=BCa | -0.0310 | +0.6358 |

## Wilcoxon zero-method sensitivity (parity run)

The parity KG-rel deltas have **14 zeros out of 35 observations (40%)**
— ties where baseline and Joern scores are equal. The Wilcoxon test has
three ways to handle these:

| Method | What it does | p-value |
|---|---|---:|
| `zero_method='wilcox'` (default, used throughout) | Drops zeros; ranks only the 21 non-zero differences | **0.0573** |
| `zero_method='pratt'` | Keeps zeros in rank computation | 0.1326 |
| `zero_method='zsplit'` | Splits zero ranks between positive and negative | 0.1436 |

**Why `'wilcox'` was chosen:** this is Wilcoxon's (1945) original
formulation and scipy's default. It conditions on the non-zero
differences, giving a test of "among the PRs where the two arms
disagree, do the disagreements favour KG?" — which is the natural
estimand when many PRs are genuinely tied.

**What this means for the headline:** the p=0.057 finding is
zero-method-sensitive. Under Pratt or zsplit the same data gives
p≈0.13. This is why the parity result is reported as *exploratory* and
the bootstrap CI [−0.03, +0.65] (zero-method-free) and sign test
p=0.383 (also zero-method-free) are co-reported. The tree-sitter
pre-registered result (p=0.006) is robust to all three methods.


- Wilcoxon-exact differs slightly from approx because of ties; scipy's auto
  picks approx when ties are present, matching my hand-rolled value.
- The bootstrap intervals from scipy and my implementation differ only
  because the random draws are not literally identical seeds; the substantive
  conclusion (CI straddles zero on KG-rel) is identical.
- This file is the cross-check: a committee member rerunning with scipy will
  see the same numbers.
