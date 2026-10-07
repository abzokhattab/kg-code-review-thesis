```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the function name `createDataFrame` to `createDataFrameInternal` in the `processDataFrame.ts` file.

## Problem
1. The function `createDataFrame` is renamed to `createDataFrameInternal`, but the change is not reflected in the test files or other parts of the codebase where this function might be used.
2. The renaming might affect external modules or scripts relying on the public API if `createDataFrame` was intended to be a public function.

## Evidence
- `packages/grafana-data/src/dataframe/processDataFrame.ts:593`: The function `createDataFrame` is renamed to `createDataFrameInternal`.
- `packages/grafana-data/src/dataframe/processDataFrame.test.ts:1-79`: The test file imports `createDataFrame`, but there is no update to reflect the new function name.

## Impact
- If `createDataFrame` is used elsewhere in the codebase or by external consumers, this change could break functionality or cause runtime errors due to unresolved references.
- Tests may fail or not cover the intended functionality if they are not updated to use the new function name.

## Recommendation (Fix / Tests / Risks)
1. Search for all occurrences of `createDataFrame` across the codebase and update them to `createDataFrameInternal` if they are meant to use the internal function.
2. Update the test files to reflect the new function name and ensure all tests pass.
3. If `createDataFrame` is part of the public API, consider maintaining the original name for external use and using a different strategy to indicate internal usage.

## Traceability
Not specified
```