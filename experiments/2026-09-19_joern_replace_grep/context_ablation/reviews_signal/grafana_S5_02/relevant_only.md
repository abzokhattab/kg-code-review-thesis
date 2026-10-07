```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package.

## Problem
1. The `MutableDataFrame` class is no longer exported from `index.ts`, which may break dependencies relying on this export.
2. There is a lack of clarity on whether all dependent modules have been updated to accommodate this change.

## Evidence
- `packages/grafana-data/src/index.ts:9`: The export of `MutableDataFrame` has been removed.
- Call-graph indicates dependencies on `MutableDataFrame` in several files:
  - `packages/grafana-data/src/utils/csv.ts`
  - `packages/grafana-data/src/transformations/transformers/merge.ts`
  - `packages/grafana-data/src/transformations/transformers/seriesToRows.ts`

## Impact
Removing the export of `MutableDataFrame` could lead to runtime errors in modules that expect this export to be available. This could result in broken functionality in parts of the application that rely on `MutableDataFrame` for data manipulation.

## Recommendation (Fix / Tests / Risks)
1. Verify and update all dependent modules to ensure they do not rely on `MutableDataFrame` being exported from `index.ts`.
2. Consider re-exporting `MutableDataFrame` if it is still needed by other parts of the codebase.
3. Add or update tests to ensure that the removal of this export does not cause any unintended side effects.

## Traceability
Not specified
```