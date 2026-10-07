```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the function name from `createDataFrame` to `createDataFrameInternal` in the `processDataFrame.ts` file.

## Problem
1. Inconsistent function naming may lead to confusion if not updated across all dependent files.
2. Potential breakage in dependent modules or tests that rely on the original function name.

## Evidence
- `packages/grafana-data/src/dataframe/processDataFrame.ts:593`: Function name changed from `createDataFrame` to `createDataFrameInternal`.
- Dependent files such as `packages/grafana-data/src/dataframe/utils.ts` and `packages/grafana-data/src/dataframe/MutableDataFrame.ts` may still reference the old function name.

## Impact
- Technical impact includes potential runtime errors or failed imports in modules that have not been updated to reflect the new function name.
- Tests that rely on the `createDataFrame` function may fail, leading to decreased test coverage and potential undetected bugs.

## Recommendation (Fix / Tests / Risks)
1. Ensure all references to `createDataFrame` in dependent files are updated to `createDataFrameInternal`.
2. Run all existing tests, especially in `processDataFrame.test.ts`, `utils.test.ts`, and other related test files to verify no functionality is broken.
3. Consider adding a deprecation warning or alias for `createDataFrame` to maintain backward compatibility if necessary.

## Traceability
- Code ownership is likely under the Grafana data processing team or a specific module owner, but it is not specified in the provided context.
```