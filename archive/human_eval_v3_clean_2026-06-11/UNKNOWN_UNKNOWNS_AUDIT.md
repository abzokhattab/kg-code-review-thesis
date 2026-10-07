# Unknown-unknowns probes — clean Joern run

## 1. Rubric leakage in review text

**Probe:** does any of the 35 reviews accidentally cite criterion IDs
(F1, T2, M3, etc.) — which would mean the prompt leaked the rubric
into the LLM's output, inflating scores artificially?

**Result:** **0 / 35 reviews mention any criterion ID.** Clean.

## 2. Repository concentration

**Probe:** are the 35 PRs concentrated in 1-2 repos? If so, the
result might generalise less.

**Result:** balanced across 5 repos:
- 8× scikit-learn
- 8× grafana
- 8× kafka
- 6× godot
- 5× jenkins

This is the design's intended distribution. **No concentration risk.**

## 3. Score range and ceiling/floor effects

**Probe:** are clean-Joern total scores hitting 25/25 (ceiling) or
1-2 (floor)? Either pattern would compress the d_z.

**Result:** total scores range **7-14 / 25**, mean 10.1. Healthy
distribution, no ceiling, no floor. **No score-compression risk.**

## 4. Issue-number leakage (training data contamination signal)

**Probe:** does any review cite a specific GitHub issue/PR number
(e.g., `#1234`)? This would suggest the LLM is recalling training
data about the actual PR rather than reasoning from the diff +
context.

**Result:** **0 / 35 reviews cite an issue number.** Clean.

## 5. Sample-selection bias from the 5 Go-PR exclusion

**Probe:** the clean-Joern set is 35 PRs (5 Go PRs excluded because
Joern's Go frontend has no call edges). Could excluding those 5
shift the comparison artificially?

**Method:** restrict the **tree-sitter** baseline-vs-KG comparison
(which has all 40 PRs) to the same 35-PR subset and see whether the
tree-sitter d_z changes.

**Result:**
- Tree-sitter KG d_z, all 40 PRs: **+0.47** (n=40)
- Tree-sitter KG d_z, restricted to clean-Joern 35-PR subset: **+0.44** (n=35)
- Shift from sample restriction: **−0.034**

**The 35-PR subset is representative of the 40-PR set.** The Go
exclusion is not biasing the headline d_z.

## 6. Excluded-PRs list (for transparency)

5 Go PRs are excluded from the clean-Joern run: PR9, PR27, PR35,
PR36, PR37. The exclusion is **declared upfront** in the run script
docstring with the technical reason (Joern's Go frontend lacks call
edges). This should be disclosed in the methodology chapter as a
boundary condition.

## Summary

No unknown-unknown found in the 5 probes that bear on the headline
soundness. The sample is balanced, the score distribution is healthy,
the rubric is not leaking into the LLM, and the Go-PR exclusion does
not bias the result.
