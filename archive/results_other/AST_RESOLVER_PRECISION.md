# AST import resolver precision (human-study packs)

Builder: `experiments/2026-07-06_user_study_prs/build_evidence.py` (Python `ast.Import` / `ast.ImportFrom` at each PR head SHA).
Census, not a sample: every displayed `dependent_files` edge in the six committed packs, n = 47.  Cost: $0.

## Headline (same classifier as lexical 10.2%)

A Python edge is confirmed if any import's final component matches the builder's `source_file` stem.  That is `scripts/compare_kg_builder_volume_precision.py::classify_grep_edge`, the test behind the lexical 10.2% figure.

| Builder | edges checked | confirmed | refuted | unverifiable | precision |
|---|---:|---:|---:|---:|---:|
| AST import resolver (human study) | 47 | 47 | 0 | 0 | 100.0% |
| lexical grep (40-PR set, for scale) | 177 | 18 | 56 | 232 | 10.2% |

The lexical row is quoted from `results/BUILDER_VOLUME_PRECISION.md` and is not recomputed here.  Its unverifiable count is high because most 40-PR edges are not Python-to-Python; every human-study edge is.

## Module-reach (stricter; not the comparable number)

Confirmed only if the flagged file imports the changed module's dotted name (`flask.app`, not a coincidental identifier `app`) or an `ImportFrom` of a function the diff added or modified.  This is the check that answers 'does the import plausibly reach the changed function?' at module granularity.

| Check | n | confirmed | refuted | precision |
|---|---:|---:|---:|---:|
| generous stem match (headline) | 47 | 47 | 0 | 100.0% |
| module-reach | 47 | 47 | 0 | 100.0% |
| ImportFrom of a changed function | 47 | 9 | 38 | 19.1% |
| generous stem match, test edges | 16 | 16 | 0 | 100.0% |

## Per-pack dependent edges

| Pack | n | stem confirmed | module-reach confirmed |
|---|---:|---:|---:|
| requests_7433 | 10 | 10/10 | 10/10 |
| flask_5637 | 12 | 12/12 | 12/12 |
| click_3493 | 8 | 8/8 | 8/8 |
| requests_7328 | 2 | 2/2 | 2/2 |
| flask_5799 | 8 | 8/8 | 8/8 |
| click_3578 | 7 | 7/7 | 7/7 |

## What this does not establish

Module-level import precision is not function-level relevance.  A file that imports `flask.app` can still be unaffected by a seven-line change to `Flask.create_url_adapter`, which is the distinction the human study raters drew on flask#5637.
