# Context-Size Ablation Results

**Date:** 2026-09-19
**Design:** Vary the number of KG context items (call edges + dependent files) given to the reviewer on Experiment 2's 28 structural injections.
**Generator:** gpt-4o (T=0.0)
**Judges:** gpt-4o-mini + gpt-4o + gemini-2.5-flash (3-judge majority)
**n:** 28 structural injections (3 repos)

## Headline

Detection is non-monotonic in context size — an inverted-U peaking at 5 items:

| Cap | Items | Detected | Rate |
|-----|-------|----------|------|
| cap_0 | 0 | 0/28 | 0.0% |
| cap_3 | 3 | 13/28 | 46.4% |
| **cap_5** | **5** | **16/28** | **57.1%** |
| cap_10 | 10 | 11/28 | 39.3% |
| cap_20 | 20 | 9/28 | 32.1% |
| cap_all | ~40 | 14/28 | 50.0% |

Peak detection (57.1% at cap_5) exceeds the deployed arm (50.0% at cap_all).
The drop from cap_5 to cap_20 (57.1% → 32.1%) is the context bloating effect.

## Per-repo breakdown

| Cap | sklearn (10) | kafka (8) | grafana (10) |
|-----|-------------|-----------|-------------|
| cap_0 | 0/10 (0%) | 0/8 (0%) | 0/10 (0%) |
| cap_3 | 7/10 (70%) | 2/8 (25%) | 4/10 (40%) |
| cap_5 | 8/10 (80%) | 4/8 (50%) | 4/10 (40%) |
| cap_10 | 6/10 (60%) | 2/8 (25%) | 3/10 (30%) |
| cap_20 | 6/10 (60%) | 0/8 (0%) | 3/10 (30%) |
| cap_all | 8/10 (80%) | 1/8 (12%) | 5/10 (50%) |

Kafka shows the strongest bloating effect: 50% at cap_5 → 0% at cap_20.
This matches the edge count data — Kafka injections have 30–618 Joern edges,
so cap_20 is still dominated by cross-file noise. sklearn has fewer edges
and is more robust to context size.

## Interpretation

1. **Even 3 edges suffice to activate detection** (0% → 46.4%). The LLM
   does not need a complete call graph; a few relevant pointers are enough.
2. **More context is not monotonically better.** Beyond ~5 items, the
   signal-to-noise ratio degrades and the LLM loses the relevant edge
   among noise edges.
3. **The deployed arm (cap_all, ~40 edges) partially recovers** from the
   mid-range dip, possibly because the LLM can pattern-match on the sheer
   volume of evidence pointing to the same target file. But it doesn't
   reach the cap_5 peak.
4. **Context pruning/ranking is a practical improvement path.** Ranking
   edges by relevance before injection would likely outperform both the
   capped and uncapped strategies.

## Stability note

6 injections detected at cap_3 were lost at cap_20 (listed in the analysis
script output). This is direct evidence of context dilution — the model had
the right information at cap_3 but lost it when buried in 17 additional items.
