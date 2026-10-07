# KG builder comparison — volume and precision (no model calls)

Builders: `data/luca_prs_v2` (lexical) vs `data/luca_prs_v2_ast` (unscoped AST, tree-sitter).
PRs compared: 40.  Cost: $0.

## Volume

| Measure | grep | unscoped AST |
|---|---:|---:|
| Dependent edges, median per PR | 14 | 14 |
| Dependent edges, total | 409 | 2730 |
| PRs with no dependent edges | 8 | 9 |
| Rendered block, median chars | 1300 | 2796 |
| Dependents actually shown, median | 10 | 10 |
| Sections in the block, median | 4 | 6 |

AST asserts more dependent edges than grep in 19 of 40 PRs.
Median Jaccard overlap of the two dependent-edge sets: 0.000.

## Precision

| Builder | edges checked | confirmed | refuted | impossible | precision | unverifiable |
|---|---:|---:|---:|---:|---:|---:|
| lexical (grep) | 177 | 18 | 56 | 103 | 10.2% | 232 |
| unscoped AST | 2730 | 2363 | 0 | 367 | 86.6% | 0 |

Grep precision is an upper bound: a Python edge counts as confirmed if any import's final component matches the changed file's stem, which also admits same-named modules in unrelated packages.  AST edges are checked against the builder's own claimed import statement and line.

## Can a precision-only experiment be run?

A clean single-factor contrast requires holding the section set and the displayed dependent count at grep's values and changing only which paths are named.  That needs AST to have resolved at least as many dependents as grep displayed.

* Feasible in **16 of 40** pull requests.
* AST resolves **zero** dependents in 9.
* AST resolves fewer than grep displays in 15.
* Median rendered-length change of the swap: -157 chars.

The precise builder therefore cannot supply comparable coverage across the set.  A clean precision contrast is confined to the feasible subset, which is the same underpowered regime that rules out the feature ablation (see `results/CONFIRMATORY_POWER.md`).  The trade-off itself, not a further generation run, is the reportable result.

## Per-PR detail

| PR | repo | grep deps | AST deps | grep rendered chars | AST rendered chars | Jaccard |
|---|---|---:|---:|---:|---:|---:|
| 1 | godotengine_godot | 0 | 200 | 131 | 2572 | 0.000 |
| 2 | grafana_grafana | 15 | 191 | 2500 | 4758 | 0.005 |
| 3 | grafana_grafana | 15 | 15 | 1411 | 1572 | 0.000 |
| 6 | apache_kafka | 15 | 70 | 2612 | 6532 | 0.000 |
| 8 | grafana_grafana | 15 | 39 | 2987 | 4554 | 0.000 |
| 9 | grafana_grafana | 15 | 260 | 1299 | 2476 | 0.004 |
| 10 | scikit-learn_scikit-learn | 15 | 235 | 1535 | 2919 | 0.000 |
| 12 | godotengine_godot | 0 | 25 | 124 | 839 | 0.000 |
| 13 | godotengine_godot | 0 | 232 | 421 | 2795 | 0.000 |
| 14 | grafana_grafana | 15 | 29 | 2117 | 2796 | 0.048 |
| 15 | grafana_grafana | 15 | 476 | 2274 | 4868 | 0.000 |
| 18 | jenkinsci_jenkins | 15 | 158 | 1884 | 4344 | 0.024 |
| 19 | jenkinsci_jenkins | 15 | 31 | 2051 | 4811 | 0.179 |
| 20 | apache_kafka | 0 | 0 | 120 | 763 | — |
| 21 | apache_kafka | 15 | 14 | 2471 | 7035 | 0.074 |
| 22 | apache_kafka | 11 | 0 | 1861 | 3858 | 0.000 |
| 23 | scikit-learn_scikit-learn | 15 | 144 | 1397 | 2785 | 0.006 |
| 24 | scikit-learn_scikit-learn | 15 | 115 | 1160 | 3017 | 0.008 |
| 27 | grafana_grafana | 15 | 309 | 1787 | 3466 | 0.000 |
| 28 | grafana_grafana | 7 | 1 | 772 | 1412 | 0.143 |
| 29 | apache_kafka | 10 | 1 | 1038 | 3241 | 0.100 |
| 30 | — | 0 | 0 | 83 | 83 | — |
| 31 | scikit-learn_scikit-learn | 10 | 1 | 692 | 1779 | 0.100 |
| 32 | scikit-learn_scikit-learn | 10 | 0 | 524 | 1897 | 0.000 |
| 33 | jenkinsci_jenkins | 15 | 13 | 1300 | 3583 | 0.556 |
| 34 | grafana_grafana | 2 | 0 | 336 | 382 | 0.000 |
| 35 | — | 0 | 0 | 251 | 251 | — |
| 36 | grafana_grafana | 13 | 0 | 600 | 1139 | 0.000 |
| 37 | grafana_grafana | 15 | 3 | 1588 | 2499 | 0.000 |
| 38 | grafana_grafana | 10 | 10 | 853 | 2265 | 0.000 |
| 39 | apache_kafka | 10 | 0 | 1047 | 4028 | 0.000 |
| 40 | apache_kafka | 6 | 2 | 1400 | 4862 | 0.333 |
| 41 | apache_kafka | 15 | 7 | 2003 | 5124 | 0.100 |
| 42 | scikit-learn_scikit-learn | 10 | 2 | 714 | 1881 | 0.200 |
| 43 | scikit-learn_scikit-learn | 10 | 0 | 606 | 2185 | 0.000 |
| 44 | scikit-learn_scikit-learn | 15 | 26 | 2142 | 3778 | 0.051 |
| 45 | godotengine_godot | 0 | 42 | 99 | 2545 | 0.000 |
| 46 | godotengine_godot | 0 | 6 | 132 | 2771 | 0.000 |
| 47 | jenkinsci_jenkins | 15 | 63 | 1488 | 3931 | 0.026 |
| 48 | jenkinsci_jenkins | 15 | 10 | 1425 | 3445 | 0.191 |
