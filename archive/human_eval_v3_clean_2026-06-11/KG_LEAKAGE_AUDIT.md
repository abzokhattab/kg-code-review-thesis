# KG-signal leakage audit — clean Joern reviews

**Question:** when Joern's evidence pack supplies caller/dependent symbols,
how often does the clean-prompt review actually cite them in the text?

This is the quantitative companion to `STRICT_VS_CLEAN_COMPARISON.md`.
If the clean prompt routinely *omits* the caller signal, the d_z=+0.58
effect is being driven by something other than visible structural
citations — and the human study under the clean prompt will struggle.

## Summary

- Reviews audited: **35**
- PRs whose Joern pack supplied ≥1 caller/dependent signal: **33**
- Of those, reviews that **cited** ≥1 such signal: **22 / 33** = **67%**

## Per-PR detail

| PR | Joern signals available | Cited in review | Citation rate | Cited symbols |
|---:|---:|---:|---:|:---|
| 10 | 15 | 2 | 13% | __init__.py, test_min_dependencies_readme.py |
| 12 | 38 | 1 | 3% | array.cpp |
| 13 | 42 | 2 | 5% | delaunay_3d.h, dynamic_bvh.h |
| 14 | 19 | 0 | 0% |  |
| 15 | 2490 | 1 | 0% | layout |
| 18 | 57 | 0 | 0% |  |
| 19 | 45 | 3 | 7% | DirectoryBrowserSupport.java, DirectoryBrowserSupportTest.java, IconSet.java |
| 1 | 5 | 0 | 0% |  |
| 20 | 0 | 0 | 0% |  |
| 21 | 37 | 1 | 3% | Crc32C.java |
| 22 | 11 | 0 | 0% |  |
| 23 | 19 | 0 | 0% |  |
| 24 | 32 | 1 | 3% | _logistic.py |
| 28 | 12 | 1 | 8% | SearchStateManager.ts |
| 29 | 10 | 0 | 0% |  |
| 2 | 81 | 1 | 1% | reducer.ts |
| 30 | 0 | 0 | 0% |  |
| 31 | 22 | 2 | 9% | _bayes.py, test_bayes.py |
| 32 | 37 | 1 | 3% | test_common.py |
| 33 | 49 | 2 | 4% | OldDataMonitor.java, saveAndRemoveEntries |
| 34 | 4 | 2 | 50% | DashboardSceneRenderer, DashboardSceneRenderer.tsx |
| 38 | 19 | 1 | 5% | location.ts |
| 39 | 10 | 0 | 0% |  |
| 3 | 19 | 2 | 11% | Reduce, Reduce.tsx |
| 40 | 6 | 0 | 0% |  |
| 41 | 15 | 0 | 0% |  |
| 42 | 36 | 1 | 3% | test_tree.py |
| 43 | 9 | 2 | 22% | test_base.py, test_validation.py |
| 44 | 27 | 1 | 4% | test_bitset.py |
| 45 | 37 | 0 | 0% |  |
| 46 | 32 | 0 | 0% |  |
| 47 | 212 | 2 | 1% | Node.java, setTemporaryOfflineCause |
| 48 | 54 | 2 | 4% | AbstractLazyLoadRunMapTest.java, update |
| 6 | 18 | 1 | 6% | ConsumerConfig.java |
| 8 | 67 | 2 | 3% | sceneVariablesSetToVariables, sceneVariablesSetToVariables.ts |

## Reading

The "67% citation rate" sounds reassuring but is misleading — **it's
binary** (does the review cite *any* caller?). The per-PR rates are
overwhelmingly 0-10%: most reviews cite 0-2 out of 30+ available
signals. The LLM is using ~5% of the KG context the evidence pack
supplied.

**This corroborates** the strict-vs-clean comparison finding: the
clean prompt mostly ignores Joern's caller list and uses only the
changed-file context. The d_z=+0.58 effect is **not** driven by the
LLM weaving callers into the review text — it must be driven by:

1. The function-list / dependent-file context shifting how the LLM
   *frames* the changed code (without explicit citation).
2. The 1-2 strategically cited callers per review (PR19 names 3,
   PR34 names 2 — which happen to be where the model felt them
   most relevant).

**Implication for the human study:** with citation rates this low,
raters cannot point to "Joern named X" as a differentiator on most
PRs. The signal is in the framing, not the entities — exactly the
"reviews look similar" complaint surfacing.
