```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the function name from `createDataFrame` to `createDataFrameInternal` in the `processDataFrame.ts` file.

## Problem
1. The renaming of the function to `createDataFrameInternal` may break existing dependencies that rely on the original function name.
2. The change does not include updates to all dependent files and tests that call the `createDataFrame` function.

## Evidence
- `packages/grafana-data/src/dataframe/processDataFrame.ts:590`: The function `createDataFrame` is renamed to `createDataFrameInternal`.
- Dependencies not updated: 
  - `packages/grafana-data/src/dataframe/utils.test.ts` 
  - `packages/grafana-data/src/dataframe/frameComparisons.test.ts`
  - `packages/grafana-data/src/dataframe/DataFrameJSON.ts`
  - `packages/grafana-data/src/dataframe/FieldCache.test.ts`
  - `packages/grafana-data/src/dataframe/utils.ts`
  - `packages/grafana-data/src/dataframe/MutableDataFrame.ts`
  - `packages/grafana-data/src/dataframe/StreamingDataFrame.ts`
  - `packages/grafana-data/src/dataframe/FieldCache.ts`
  - `packages/grafana-data/src/dataframe/ArrayDataFrame.ts`
  - `packages/grafana-data/src/dataframe/processDataFrame.test.ts`
  - `packages/grafana-data/src/field/fieldOverrides.test.ts`
  - `packages/grafana-data/src/field/getFieldDisplayValuesProxy.test.tsx`
  - `packages/grafana-data/src/panel/PanelPlugin.test.tsx`
  - `packages/grafana-data/src/panel/suggestions/getPanelDataSummary.test.ts`

## Impact
The primary impact is the potential for runtime errors or test failures due to unresolved references to the old function name `createDataFrame`. This could lead to broken functionality in any module that depends on this function, affecting data processing and rendering in the application.

## Recommendation (Fix / Tests / Risks)
1. Update all dependent files and tests to use the new function name `createDataFrameInternal`.
2. Run the full test suite to ensure that all references have been correctly updated and that no tests fail due to this change.
3. Consider adding a deprecation warning or alias for `createDataFrame` to maintain backward compatibility temporarily.

## Traceability
Not specified
```