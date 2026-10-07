```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming within the `processDataFrame` function in the Grafana data package.

## Problem
1. The function name change from `createDataFrame` to `createDataFrameInternal` may affect external modules if this function is used outside its intended internal scope.
2. Lack of test updates or additions to verify that the refactor does not break existing functionality.

## Evidence
- `packages/grafana-data/src/dataframe/processDataFrame.ts:593`: The function name is changed from `createDataFrame` to `createDataFrameInternal`.

## Impact
- If `createDataFrame` is used externally, renaming it to `createDataFrameInternal` without proper deprecation or aliasing could lead to runtime errors in modules that depend on the original function name.
- Without corresponding test updates, there is a risk that this change could introduce regressions or break existing functionality that relies on this function.

## Recommendation (Fix / Tests / Risks)
1. Verify if `createDataFrame` is used outside of its intended internal scope. If so, consider providing an alias or deprecation notice.
2. Add or update unit tests to ensure that the refactor does not affect existing functionality.
3. Review documentation to ensure that any references to `createDataFrame` are updated to reflect the new function name, if applicable.

## Traceability
Not specified
```