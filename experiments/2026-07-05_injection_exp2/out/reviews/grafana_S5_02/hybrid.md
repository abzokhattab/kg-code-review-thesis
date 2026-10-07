```
# Review Note — Evidence-Anchored

**Scope:** This PR modifies the package exports in `index.ts` by removing `MutableDataFrame` from the exports.

## Problem
1. The removal of `MutableDataFrame` from exports may break existing dependencies that rely on this export.
2. Lack of clarity on whether all usages of `MutableDataFrame` have been refactored or replaced elsewhere.

## Evidence
- `packages/grafana-data/src/index.ts:12`: `MutableDataFrame` is removed from the export list.
- Call-graph indicates multiple dependencies on `MutableDataFrame`:
  - `packages/grafana-data/src/utils/csv.ts::<lambda>2`
  - `packages/grafana-data/src/dataframe/MutableDataFrame.ts::addFieldFor`
  - `packages/grafana-data/src/transformations/transformers/merge.ts::<lambda>4`

## Impact
- Removing `MutableDataFrame` from exports can lead to runtime errors in parts of the codebase that still depend on it.
- Potentially breaks backward compatibility if external modules or plugins rely on this export.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Ensure that all dependencies on `MutableDataFrame` are updated to use an alternative or are refactored before removing the export.
2. **Tests:** Add tests to verify that the removal of `MutableDataFrame` does not affect existing functionalities. Consider integration tests that cover modules previously using `MutableDataFrame`.
3. **Risks:** Conduct a thorough impact analysis to identify all areas affected by this change, especially in external plugins or modules that might use this export.

## Traceability
Not specified
```