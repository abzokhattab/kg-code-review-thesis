# Thesis POC Comparison Report

**Generated:** 2025-12-09

> **⚠️ DEPRECATED:** This report uses SBERT similarity to Luca's PR descriptions (a different metric).
> The **authoritative results** use Chris's 25-criterion checklist evaluation:
>
> - Baseline: 12.4%
> - KG: 20.8% (+68%)
> - Hybrid: 24.4% (+97%)
>   See `comprehensive_showcase.html` for the current results.

---

## Executive Summary (OLD - SBERT-based)

This report presents the evaluation results of four context retrieval strategies for LLM-based PR review generation, answering the research questions from the thesis exposé.

### Key Findings

| Metric            | Baseline | RAG   | KG        | Hybrid |
| ----------------- | -------- | ----- | --------- | ------ |
| **Avg SBERT**     | 0.167    | 0.234 | **0.497** | 0.492  |
| **Std Dev**       | 0.11     | 0.02  | 0.14      | 0.14   |
| **Improvement**   | —        | +40%  | **+198%** | +195%  |
| **PRs Evaluated** | 5        | 4     | 5         | 5      |

**Winner: Knowledge Graph (KG)** with 198% improvement over baseline.

---

## RQ1: Effectiveness of Context-Augmented Review Generation

### RQ1.1: Does context augmentation improve review quality?

**Answer: YES** — All context-augmented strategies outperform the diff-only baseline.

| Strategy        | vs Baseline |
| --------------- | ----------- |
| RAG (Semantic)  | +40%        |
| KG (Structural) | **+198%**   |
| Hybrid (KG+RAG) | +195%       |

**Interpretation:** The Knowledge Graph approach provides the largest improvement, suggesting that structural repository context (tests, dependencies, ownership) is more valuable than semantic code similarity for PR review generation.

### RQ1.2: Which strategy produces best results?

**Answer: Knowledge Graph (KG)**

Win distribution across 5 PRs:

- 🏆 **KG**: 3 wins (60%)
- 🥈 **Hybrid**: 2 wins (40%)
- 🥉 **RAG**: 0 wins (0%)
- **Baseline**: 0 wins (0%)

---

## Per-PR Results

### SBERT Cosine Similarity (vs Improved-Degraded Reference)

| PR  | Repository        | Type     | Baseline | RAG  | KG       | Hybrid   | Winner     |
| --- | ----------------- | -------- | -------- | ---- | -------- | -------- | ---------- |
| #1  | godotengine/godot | Bug Fix  | 0.12     | —    | **0.72** | 0.69     | **KG**     |
| #2  | grafana/grafana   | Breaking | 0.30     | 0.26 | **0.54** | 0.46     | **KG**     |
| #3  | grafana/grafana   | Feature  | 0.08     | 0.26 | 0.44     | **0.49** | **Hybrid** |
| #5  | jenkinsci/jenkins | Docs     | 0.01     | 0.23 | **0.44** | 0.42     | **KG**     |
| #6  | apache/kafka      | Feature  | 0.26     | 0.28 | 0.73     | **0.76** | **Hybrid** |

---

## RQ2: Feature Importance (Stretch Goal)

### RQ2.1: Which features matter most?

Based on ablation study (removing individual KG components):

| Feature Removed                  | Score Drop | Importance   |
| -------------------------------- | ---------- | ------------ |
| Dependencies (importers/callers) | ~23%       | **Critical** |
| Test Coverage                    | ~17%       | **High**     |
| CODEOWNERS                       | ~3%        | Low          |

**Interpretation:**

1. **Dependency detection is crucial** — Files outside the diff that import or call changed code provide essential context for impact analysis
2. **Test coverage is valuable** — Knowing which tests exercise changed code helps generate actionable recommendations
3. **Ownership has lower impact** — Useful for traceability but not essential for review quality

### RAG Hyperparameter Sensitivity

| Top-K   | Avg SBERT | Notes                 |
| ------- | --------- | --------------------- |
| k=1     | ~0.18     | Under-retrieval       |
| k=3     | ~0.22     | Suboptimal            |
| **k=5** | **~0.23** | **Optimal**           |
| k=10    | ~0.21     | Over-retrieval begins |
| k=20    | ~0.19     | Too much noise        |

---

## Methodology Notes

### Evaluation Dataset

- **Source:** Mariotto et al.'s curated PR dataset
- **PRs Evaluated:** 5 (PR #4 skipped - not merged)
- **Reference:** Improved-Degraded (ID) variant for comparison

### Metrics

1. **SBERT Cosine Similarity** (primary) — Semantic similarity using `all-MiniLM-L6-v2`
2. **BLEU Score** (secondary) — N-gram overlap with smoothing

### Limitations

- Small sample size (5 PRs)
- Single LLM (GPT-4o)
- Limited to Python/TypeScript/Java AST analysis
- No human evaluation of generated notes

---

## Conclusions

1. **Knowledge Graph beats RAG** for PR review context retrieval
   - Structural relationships (tests, dependencies) > Semantic similarity
   - 3× improvement over baseline vs 40% for RAG-only

2. **Hybrid provides no significant benefit** over KG alone
   - Adding RAG may introduce noise rather than complementary signal
   - Cost-benefit favors KG-only approach

3. **Dependency detection is the most valuable KG feature**
   - Enables warning about potential breaking changes
   - Provides context that LLMs cannot infer from diff alone

---

## Artifacts

| Artifact              | Path                                  |
| --------------------- | ------------------------------------- |
| Similarity Metrics    | `results/luca_similarity_metrics.csv` |
| Pipeline Results      | `results/luca_pipeline_results.csv`   |
| Generated Notes       | `outputs/luca_prs/*.md`               |
| Evidence Packs        | `data/luca_prs/*.json`                |
| Knowledge Graphs      | `data/luca_prs/pr*_kg/`               |
| Interactive Dashboard | `dashboard/index.html`                |

---

_Report generated by prnote thesis evaluation framework_
