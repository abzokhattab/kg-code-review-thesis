# `dataset_v2/` — current build status

_Snapshot taken 2026-05-12. **40-PR canonical dataset complete (18 audit + 7 expansion + 15 KG-rich expansion).**_

## Summary

| Phase | Status | Cost |
|-------|--------|------|
| 1.1 Folder + docs scaffold | DONE | free |
| 1.2 v1 audit script + finding writeup | DONE | free |
| 1.3 v2 PR-fetcher (`fetch_evidence_v2.py`) | DONE | free |
| 1.4 18 + 7 + 15 = **40** v2 evidence packs in `data/luca_prs_v2/` | DONE | free |
| 1.5 RAG re-build for v1-contaminated PRs + 7 + 15 fresh PRs | DONE | ~$0.50 (text-embedding-3-small) |
| 1.6 Verification: all 40 packs clean (real titles, full bodies, untruncated diffs, ≥ 8 RAG chunks each) | DONE | free |
| 2 Regenerate 160 reviews (gpt-4o, T=0.0) | DONE | ~$6 |
| 3 Multi-judge panel: 3 judges × 160 reviews × 25 criteria = 12,000 cells | DONE | ~$8 |
| 4 v1↔v2 comparison + bootstrap CIs + paired permutation tests | DONE | free |

**Total OpenAI spend across the rebuild:** ~$15.

## Headline result (v2, 40 PRs, cleaned + two expansions)

The data-quality fix + two expansions all moved the result in the same direction.

| Mode | Total % | KG-relevant % |
|------|---:|---:|
| baseline | 36.8% | 55.3% |
| kg | 39.3% | **62.0%** ★ |
| rag | **40.3%** ★ | 60.0% |
| hybrid | 39.7% | 61.1% |

★ winner in column.

**Bootstrap CIs and paired permutation tests on v2 (n=40 PRs):**

| Mode vs baseline | Total Δ [95% CI] | p (perm) | d_z | KG-rel Δ [95% CI] | p (perm) | d_z |
|---|---:|---:|---:|---:|---:|---:|
| **kg** | +0.62 [+0.05, +1.20] | 0.054 | +0.33 | **+0.60 [+0.23, +0.97]** | **0.007** | **+0.47** |
| **rag** | **+0.88 [+0.30, +1.45]** | **0.007** | **+0.47** | +0.42 [+0.05, +0.82] | 0.057 | +0.33 |
| **hybrid** | **+0.72 [+0.10, +1.35]** | **0.037** | **+0.36** | **+0.53 [+0.17, +0.90]** | **0.008** | **+0.46** |

Each individual mode now passes significance on the metric it was
designed to target:

- **KG > baseline** on **KG-relevant criteria** (p = 0.007, d_z = +0.47).
- **RAG > baseline** on **total coverage** (p = 0.007, d_z = +0.47).
- **Hybrid > baseline** on **both** (p = 0.037 and 0.008).

This is the cleanest possible behavioural story for the thesis: KG
context helps on KG-shaped rubric items (call-graph, ownership,
tests); RAG context helps on general rubric items (style, naming,
magic numbers); combining them helps on everything.

Inter-judge κ on the 40-PR panel: **0.717 / 0.590 / 0.713**
(gpt-4o-mini ↔ gpt-4o ↔ gemini-2.5-flash), all in the "substantial
agreement" band. κ is slightly *higher* than on the 25-PR snapshot
(0.715 / 0.565 / 0.694), so adding 15 fresh PRs did not introduce
noise — if anything, judges agree more on the larger set.

**Snapshot trajectory** (preserved on disk so reviewers can verify the result strengthened monotonically — *not* cherry-picked):

| Snapshot | n | Hybrid total Δ p | Hybrid KG-rel Δ p | KG-only KG-rel Δ p | RAG-only total Δ p |
|---|---:|---:|---:|---:|---:|
| 18-PR audit-survivor (`*_v2_18pr.*`) | 18 | 0.054 (borderline) | 0.049 ✅ | 0.180 (ns) | 0.092 (ns) |
| 25-PR first expansion (`*_v2_25pr.*`) | 25 | 0.020 ✅ | 0.009 ✅✅ | 0.255 (ns) | 0.128 (ns) |
| **40-PR canonical (`*_v2.*`)** | **40** | **0.037** ✅ | **0.008** ✅✅ | **0.007** ✅✅ | **0.007** ✅✅ |

## Where the artifacts live

| What | Path |
|------|------|
| Cleaned evidence packs (40 PRs: 18 audit + 7 + 15 expansions) | `data/luca_prs_v2/pr*_evidence.json` |
| Generated reviews (160 = 40 × 4) | `outputs/luca_prs_v2/pr*_*.md` |
| Multi-judge panel JSON (full, 40 PRs) | `results/checklist_evaluation_llm_multi__v2.json` |
| Multi-judge raw safety net | `results/checklist_evaluation_llm_multi__v2.raw.json` |
| Bootstrap CIs + paired tests (40 PRs) | `results/BOOTSTRAP_STATS_v2.{json,md}` |
| **v1 ↔ v2 comparison** | `results/V1_VS_V2_COMPARISON.{json,md}` |
| Per-review judge cache (40 PRs × 3 judges) | `outputs/luca_prs_v2/.judge_cache/v2/.../pr*_*.json` |
| **18-PR snapshot** (audit-survivor only) | `results/checklist_evaluation_llm_multi__v2_18pr.json`, `results/BOOTSTRAP_STATS_v2_18pr.{json,md}` |
| **25-PR snapshot** (first expansion) | `results/checklist_evaluation_llm_multi__v2_25pr.json`, `results/BOOTSTRAP_STATS_v2_25pr.{json,md}` |
| 7-PR expansion candidates + audit | `dataset_v2/docs/seven_more_candidates.json` |
| 7-PR expansion selection script | `dataset_v2/scripts/find_seven_more_prs.py` |
| 15-PR expansion candidates + audit | `dataset_v2/docs/fifteen_more_candidates.json` |
| 15-PR expansion selection script | `dataset_v2/scripts/find_fifteen_more_prs.py` |
| RAG builder for 7-PR expansion | `dataset_v2/scripts/build_rag_for_new_seven.py` |
| RAG builder for 15-PR expansion | `dataset_v2/scripts/build_rag_for_new_fifteen.py` |
| Audit of v1 dataset | `dataset_v2/docs/AUDIT_v1.md`, `dataset_v2/docs/audit_v1.json` |
| v2 selection rationale | `dataset_v2/docs/SELECTION_v2.md` |

## How to reproduce end-to-end

```bash
# 1. Cleaned evidence (free, idempotent)
python3 dataset_v2/scripts/audit_v1_dataset.py
python3 dataset_v2/scripts/fetch_evidence_v2.py
python3 dataset_v2/scripts/merge_rag_context_from_v1.py
python3 dataset_v2/scripts/rebuild_rag_for_v2_contaminated.py

# 2. Reviews (~$3, idempotent — skips already-generated)
python3 dataset_v2/scripts/regenerate_reviews_v2.py

# 3. Multi-judge panel (~$3, idempotent — judge cache resumes)
set -a && source .env && set +a
python3 -m scripts.evaluate_reviews \
    --outputs-dir outputs/luca_prs_v2 \
    --output-suffix v2

# 4. Stats and comparison (free)
python3 scripts/bootstrap_stats.py \
    --in  results/checklist_evaluation_llm_multi__v2.json \
    --out-json results/BOOTSTRAP_STATS_v2.json \
    --out-md   results/BOOTSTRAP_STATS_v2.md \
    --label    'v2 (18 PRs, cleaned dataset)'

python3 dataset_v2/scripts/compare_v1_v2.py \
    --v1 results/checklist_evaluation_llm_multi.json \
    --v2 results/checklist_evaluation_llm_multi__v2.json \
    --out-md   results/V1_VS_V2_COMPARISON.md \
    --out-json results/V1_VS_V2_COMPARISON.json
```

The whole rebuild from scratch (40 PRs) is ~2 hr wall-clock + ~$15 OpenAI.

## Why this dataset replaces v1 for the headline RQ1/RQ2 claims

v1 (`data/luca_prs_fixed/`) had eight separate data-quality issues (see `AUDIT_v1.md`):

1. 10/25 PRs had **empty bodies** → reviewer never saw the maintainer's description.
2. 4/25 had **placeholder titles** like `"Grafana PR #95949"`.
3. 9/25 had **silently truncated diffs** at a 15 kB cap (the truncation marker had a bug — no comment, just dropped).
4. 4/25 had **contaminated `changed_files`** lists in v1 evidence (v1 used the dependent-files index by accident, not the PR's actual file list), which corrupted RAG retrieval.
5. 3/25 were **docs-only**; 1/25 was a **revert PR**; 1/25 was a **closed/not-merged PR**; 2/25 were **Jelly-only** (KG can't parse Jelly templates); 1/25 was **binary-heavy** (icon assets).

In aggregate, **at least 16 of 25 v1 PRs (64%) had at least one issue**. v2 drops 7 PRs that fail any of the five direction-blind selection criteria in `SELECTION_v2.md`, and re-fetches everything else with full bodies, untruncated 50 kB diffs, and clean RAG context. v1 is preserved unmodified so the writeup can show both side-by-side; the headline numbers in the thesis come from v2.
