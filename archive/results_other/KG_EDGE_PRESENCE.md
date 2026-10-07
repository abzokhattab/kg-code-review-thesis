# Does the KG effect track edges, or just the block?

Contrast: kg minus baseline, per pull request. Grouping is by what the *rendered* graph block contained, after the cohort filter in `format_kg_context`, so it reflects what the model was shown.

**Observational, not an ablation.** See the confound note at the end.

## KG-relevant /9

| Group | n | Δ | 95 % CI | d_z | p |
|---|---|---|---|---|---|
| Graph block has edges | 32 | +0.812 | [+0.406, +1.219] | +0.68 | 0.0013 |
| Graph block is a file list only | 8 | -0.250 | [-1.000, +0.625] | -0.20 | 0.7882 |
| _all pull requests_ | 40 | +0.600 | | | |

Between-group difference: +1.062, label-permutation p = 0.0436.

## Total /25

| Group | n | Δ | 95 % CI | d_z | p |
|---|---|---|---|---|---|
| Graph block has edges | 32 | +0.781 | [+0.125, +1.406] | +0.42 | 0.0332 |
| Graph block is a file list only | 8 | +0.000 | [-1.375, +1.375] | +0.00 | 1.0000 |
| _all pull requests_ | 40 | +0.625 | | | |

Between-group difference: +0.781, label-permutation p = 0.3652.

## The confound

Median changed files: 6 in the group with edges against 2 in the group without. Edge presence is entangled with change size: a single-file change cannot have an inter-file edge. The group difference below is therefore not attributable to the edges alone.

