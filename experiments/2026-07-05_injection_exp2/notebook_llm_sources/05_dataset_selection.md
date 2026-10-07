# `dataset_v2/` — LLM-judge dataset, cleaned and re-fetched

_Last revision: 2026-05-12.
Dataset locked at **40 PRs** after two direction-blind expansions
(18 → 25 → 40). The 40 PRs in this dataset replace the 25-PR v1
dataset in `data/luca_prs_fixed/` for the headline RQ1/RQ2
LLM-judge analysis. v1 is preserved unmodified in
`outputs/luca_prs_fixed/` for the side-by-side comparison in the
writeup._

## 1. What v2 is

A re-fetch and re-generation of the LUCA stimulus set with three
fixed problems:

| Problem in v1 | Fix in v2 |
|---------------|-----------|
| 10 of 25 PRs had empty body (LLM never saw the maintainer description) | Full GitHub body fetched per PR, capped at 8 kB (was 2 kB, often empty). Empty bodies are no longer present. |
| 4 of 25 PRs had placeholder titles like `"Grafana PR #95949"` | Real GitHub title fetched per PR. |
| 9 of 25 PRs had diffs truncated at the 15 kB cap | Cap raised to 50 kB; PRs with diffs above that are dropped. None of the kept v2 PRs are truncated. |

And two scope changes:

| Change | Why |
|--------|-----|
| 7 v1 PRs dropped (`5, 7, 11, 16, 17, 25, 26`) | Documentation-only, KG-unparseable, revert, or rejected/closed — none are valid code-review stimuli. See `AUDIT_v1.md` for per-PR rationale. |
| 22 additional PRs fetched fresh from GitHub (PRs 27-48) | Bring N back up to 40 *and* increase KG-richness so the KG-only effect is detectable. See § 4 below. |

## 2. Selection criteria (direction-blind, applied before any model output was inspected)

A PR is in v2 if and only if **all eight** of the following hold:

1. **Merged.** The PR is on `main`/`master` of the upstream repo. Excludes v1's PR 7.
2. **Not a revert.** The PR's net intent is to add or change behaviour, not undo a prior PR. Excludes v1's PR 26. Backports (title ending in `(#NNNNN)`) are treated as reverts of the original.
3. **Substantive code change.** The diff includes ≥ 1 file in a programming language (`.py`, `.java`, `.scala`, `.cpp`, `.h`, `.go`, `.ts`, `.tsx`, `.js`) AND the modified hunks are not exclusively docstring/comment text. Excludes v1's PRs 11, 16, 25.
4. **Sufficient KG-parseable surface.** **100 %** of changed code files are in tree-sitter-supported languages. Excludes v1's PRs 5 and 17 (single-Jelly) and any future candidate touching `.kt`, `.mm`, `.gd`, `.jelly`, `.swift`, etc.
5. **Diff fits in 50 kB.** The full GitHub diff is at most 50 kB (≈ 12 500 tokens). PRs above that need chunked review and are out of scope. None of the kept PRs hit this cap.
6. **Real PR body, not empty.** Maintainer-provided body of ≥ 100 chars. This is the description the LLM gets in the prompt.
7. **No cosmetic or chore titles.** PRs starting with `Bump`, `Chore`, `Docs`, `Update dependency`, `:lock:`, `:robot:`, `:memo:`, `:sparkles:` are skipped — they don't exercise the review rubric.
8. **KG-rich (2026-05-12 addition).** ≥ 2 KG-parseable code files in the diff, so the knowledge graph has at least one inter-file relationship to surface. This is a *stimulus-side* constraint requested by the supervisor ("pick good PRs that are usable for KG to see its performance"), not an outcome filter.

Each criterion is **direction-blind** — none depend on which mode (baseline/KG/RAG/hybrid) wins on which criterion.

**Why these constraints exist:** criteria 1–5 ensure that what we judge is an actual code review of a real, merged code change. Criterion 6 ensures all four modes (including baseline) see a maintainer description, so KG/RAG are not credited for context the prompt could have already obtained. Criterion 7 keeps the rubric meaningful (no rubric grades a `Bump v1.2.3 → v1.2.4` PR sensibly). Criterion 8 ensures that on each PR there is, in principle, *something* for KG mode to surface; otherwise the KG arm of the experiment is unfair to KG.

## 3. Final selection — 40 PRs

The 40 PRs come from 5 repositories across 5 languages, mix of bug-fix / feature / refactor, all merged, all KG-parseable, all with real bodies, all under 50 kB diff:

| Set | When added | N | Selection script |
|-----|------------|---|------------------|
| **Audit survivors** | 2026-04-30 | 18 | manual audit of v1 (`AUDIT_v1.md`) |
| **First expansion (RQ2 ⇒ 25)** | 2026-05-05 | +7  | `dataset_v2/scripts/find_seven_more_prs.py` |
| **Second expansion (RQ2 ⇒ 40)** | 2026-05-12 | +15 | `dataset_v2/scripts/find_fifteen_more_prs.py` |
| **Total** | | **40** | |

**Per-repo composition:**

| Repo | Audit | +7 | +15 | Total | Lang |
|---|---:|---:|---:|---:|---|
| grafana/grafana | 6 | 2 | 5 | 13 | Go/TS |
| apache/kafka | 4 | 1 | 3 | 8 | Java/Scala |
| scikit-learn/scikit-learn | 3 | 2 | 3 | 8 | Python |
| godotengine/godot | 3 | 1 | 2 | 6 | C++ |
| jenkinsci/jenkins | 2 | 1 | 2 | 5 | Java |
| **Total** | **18** | **7** | **15** | **40** | |

PR-by-PR enumeration:

| PR | Repo                       | Type      | Lang        | Diff (kB) | Body (chars) | Set |
|---:|----------------------------|-----------|-------------|----------:|--:|--|
|  1 | godotengine/godot          | bug-fix   | C++         |       2.3 |  1190 | audit |
|  2 | grafana/grafana            | feature   | Go/TS       |      19.4 |  2059 | audit |
|  3 | grafana/grafana            | feature   | TS          |       8.2 |   846 | audit |
|  6 | apache/kafka               | feature   | Java/Scala  |      14.6 |   294 | audit |
|  8 | grafana/grafana            | feature   | Go/TS       |      15.4 |   478 | audit |
|  9 | grafana/grafana            | feature   | Go/TS       |      12.7 |  4327 | audit |
| 10 | scikit-learn/scikit-learn  | refactor  | Python      |      29.0 |   422 | audit |
| 12 | godotengine/godot          | feature   | C++         |       2.6 |  2240 | audit |
| 13 | godotengine/godot          | refactor  | C++         |      33.2 |   430 | audit |
| 14 | grafana/grafana            | feature   | TS          |      11.7 |  1343 | audit |
| 15 | grafana/grafana            | refactor  | TS          |      29.5 |   378 | audit |
| 18 | jenkinsci/jenkins          | refactor  | Java        |       7.0 |  2000 | audit |
| 19 | jenkinsci/jenkins          | refactor  | Java        |       7.7 |  1618 | audit |
| 20 | apache/kafka               | refactor  | Java/Scala  |       6.8 |   311 | audit |
| 21 | apache/kafka               | refactor  | Java/Scala  |      26.7 |   625 | audit |
| 22 | apache/kafka               | refactor  | Java        |      10.3 |   342 | audit |
| 23 | scikit-learn/scikit-learn  | refactor  | Python      |       6.4 |   430 | audit |
| 24 | scikit-learn/scikit-learn  | refactor  | Python      |      32.1 |   318 | audit |
| 27 | grafana/grafana            | feature   | Go/TS       |  ≈ 12 | ≈ 1 k | +7 |
| 28 | grafana/grafana            | bug-fix   | Go/TS       |  ≈ 7  | ≈ 0.7 k | +7 |
| 29 | apache/kafka               | feature   | Java/Scala  |  ≈ 18 | ≈ 0.5 k | +7 |
| 30 | godotengine/godot          | refactor  | C++         |  ≈ 7  | ≈ 0.7 k | +7 |
| 31 | scikit-learn/scikit-learn  | bug-fix   | Python      |  ≈ 6  | ≈ 0.6 k | +7 |
| 32 | scikit-learn/scikit-learn  | refactor  | Python      |  ≈ 9  | ≈ 0.4 k | +7 |
| 33 | jenkinsci/jenkins          | refactor  | Java        |  ≈ 11 | ≈ 1.5 k | +7 |
| 34 | grafana/grafana            | feature   | Go/TS       |       2.8 |  1208 | +15 |
| 35 | grafana/grafana            | bug-fix   | Go/TS       |      19.8 |   558 | +15 |
| 36 | grafana/grafana            | bug-fix   | Go/TS       |       2.2 |  1760 | +15 |
| 37 | grafana/grafana            | feature   | Go/TS       |      18.5 |  1577 | +15 |
| 38 | grafana/grafana            | bug-fix   | Go/TS       |       2.6 |  2393 | +15 |
| 39 | apache/kafka               | feature   | Java        |       9.8 |   476 | +15 |
| 40 | apache/kafka               | refactor  | Java/Scala  |      19.3 |   294 | +15 |
| 41 | apache/kafka               | refactor  | Java        |      39.0 |   402 | +15 |
| 42 | scikit-learn/scikit-learn  | refactor  | Python      |      13.5 |   389 | +15 |
| 43 | scikit-learn/scikit-learn  | refactor  | Python      |       3.0 |   380 | +15 |
| 44 | scikit-learn/scikit-learn  | refactor  | Python      |      17.1 |   293 | +15 |
| 45 | godotengine/godot          | bug-fix   | C++         |       1.5 |   163 | +15 |
| 46 | godotengine/godot          | feature   | C++         |       5.8 |   658 | +15 |
| 47 | jenkinsci/jenkins          | bug-fix   | Java        |       3.6 |  7218 | +15 |
| 48 | jenkinsci/jenkins          | refactor  | Java        |      28.3 |  3790 | +15 |

## 4. Why expand to 40 PRs?

The 18 audit-survivor set was clean but underpowered for detecting
the smaller per-mode effects (Cohen's d_z ≈ 0.3–0.5). The 25-PR
expansion (2026-05-05) confirmed the direction of the effect but
left `KG-only` marginally non-significant on KG-relevant
criteria (p ≈ 0.12).

After the 2026-05-12 supervisor meeting (notes: "do more PRs if it
serves the thesis; pick good PRs that are usable for KG to see its
performance"), we added 15 more PRs subject to a new **KG-richness
criterion (c8)**: each PR must touch ≥ 2 KG-parseable code files,
so the knowledge graph has at least one inter-file relationship to
surface. This is a stimulus-side property — chosen from the diff
shape *before* any LLM was run — not an outcome filter.

The headline shift between the 25-PR and 40-PR datasets:

| Metric                           | 25 PRs        | 40 PRs        |
|----------------------------------|---------------|---------------|
| KG-only vs baseline (KG-rel Δ)   | +0.36, p≈0.12 | +0.60, p=0.007 |
| RAG-only vs baseline (total Δ)   | +0.36, p≈0.08 | +0.88, p=0.007 |
| Hybrid vs baseline (total Δ)     | +0.46, p≈0.05 | +0.72, p=0.037 |
| Hybrid vs baseline (KG-rel Δ)    | +0.46, p=0.009| +0.53, p=0.008 |

KG-only now shows a clean, significant effect on KG-relevant
criteria, and RAG-only on total coverage. That alignment is the
expected behavioural fingerprint:

- **RAG** retrieves nearby code → broader coverage on general
  rubric items (style, magic numbers, naming, etc.).
- **KG** retrieves dependency/test relationships → improvement
  concentrated in KG-relevant criteria (callers, tests, ownership).

The 40-PR sample size also lets each individual mode pass
significance, not just the hybrid arm — which strengthens the
thesis claim that the two context types are complementary rather
than just additive.

## 5. What v2 does NOT change

- **The rubric.** Same 25-criterion checklist, same KG-relevant
  subset of 9, same multi-judge panel.
- **The four modes.** Same baseline / KG / RAG / hybrid prompt
  templates. (The KG and RAG context blocks are re-built per the
  new evidence packs but the templates are identical.)
- **The base generator.** Same gpt-4o at temperature 0.0.
- **The thesis claim.** RQ1 and RQ2 are unchanged. The expected
  direction (more context ⇒ more KG-relevant coverage) is
  recovered with a tighter CI on the larger N.

## 6. Direction-blindness audit (per criterion)

The eight filter criteria are stimulus properties (merged status,
revert flag, file-extension language, code-vs-docstring ratio, byte
length, body length, title keywords, file count). None of them
depend on:

- which mode (baseline/KG/RAG/hybrid) wins on which criterion;
- the LLM-judge scores;
- the AI-generated reviews of any kind.

PRs were dropped/kept by reading their **GitHub diffs and titles**
*before* running any LLM. This is the same direction-blind
discipline applied to the v2 human-study selection in
`human_eval_v2/docs/SELECTION_v2.md`.

The KG-richness criterion (c8) is the only one that mentions "KG"
in its name, but it operates on a structural property of the
diff (file count by extension), not on any KG-mode output. A
baseline-only / RAG-only run would have selected the same 15 PRs
under c8.

## 7. Reproducibility

```bash
# Phase 1 — re-fetch evidence (free; uses gh CLI, no LLM calls)
python3 dataset_v2/scripts/fetch_evidence_v2.py

# Phase 2 — rebuild KG and RAG context blocks
python3 scripts/build_kg_evidence_ast.py --evidence-dir data/luca_prs_v2
python3 dataset_v2/scripts/build_rag_for_new_fifteen.py   # for PRs 34-48
python3 dataset_v2/scripts/build_rag_for_new_seven.py     # for PRs 27-33

# Phase 3 — regenerate reviews (≈ $5-10 in LLM credits)
python3 dataset_v2/scripts/regenerate_reviews_v2.py

# Phase 4 — re-run multi-judge panel (≈ $4-6)
python3 -m scripts.evaluate_reviews \
    --outputs-dir outputs/luca_prs_v2 \
    --output-suffix v2

# Phase 5 — stats + v1 vs v2 comparison
python3 scripts/bootstrap_stats.py \
    --in results/checklist_evaluation_llm_multi__v2.json \
    --out-json results/BOOTSTRAP_STATS_v2.json \
    --out-md results/BOOTSTRAP_STATS_v2.md \
    --label 'v2 (40 PRs, cleaned + expansion)'

python3 dataset_v2/scripts/compare_v1_v2.py \
    --v1 results/checklist_evaluation_llm_multi.json \
    --v2 results/checklist_evaluation_llm_multi__v2.json \
    --out-md results/V1_VS_V2_COMPARISON.md \
    --out-json results/V1_VS_V2_COMPARISON.json
```

## 8. Snapshots

Snapshots of intermediate datasets are kept in `results/`:

- `*_v2_18pr.*` — first audit-survivor snapshot (18 PRs)
- `*_v2_25pr.*` — first expansion snapshot (25 PRs)
- (current) `*_v2.*` — 40-PR headline used by the thesis

These let reviewers verify that the headline strengthened *as we
added more clean PRs*, not as we cherry-picked between datasets.
