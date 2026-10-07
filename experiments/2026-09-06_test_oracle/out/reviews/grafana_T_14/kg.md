```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the function name from `arrayToDataFrame` to `arrayToDataFrameInternal` in the ArrayDataFrame module.

## Problem
1. The function name change might break existing code that relies on `arrayToDataFrame`.
2. There is no indication of updates in dependent files or tests to accommodate the new function name.

## Evidence
- `packages/grafana-data/src/dataframe/ArrayDataFrame.ts:30`: The function `arrayToDataFrame` is renamed to `arrayToDataFrameInternal`.
- `packages/grafana-data/src/dataframe/processDataFrame.ts`: This file depends on `ArrayDataFrame.ts` but does not show any updates in the diff to reflect the function name change.

## Impact
- The change could lead to runtime errors or broken functionality in any code that imports or calls `arrayToDataFrame` without updating to the new name.
- If the dependent files are not updated, this could cause integration issues within the codebase.

## Recommendation (Fix / Tests / Risks)
1. Update all references to `arrayToDataFrame` in dependent files, such as `processDataFrame.ts`, to use the new function name `arrayToDataFrameInternal`.
2. Ensure that all relevant tests are updated to reflect the function name change and verify that they pass.
3. Consider maintaining backward compatibility by exporting both the old and new function names, if feasible, to prevent breaking changes.

## Traceability
- Code Owner: Not specified
```