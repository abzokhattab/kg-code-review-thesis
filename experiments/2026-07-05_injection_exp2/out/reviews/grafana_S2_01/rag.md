```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `toDataFrame` function to accept an additional `RequiredContext` parameter.

## Problem
1. The function signature change lacks corresponding updates in the test suite, potentially leading to untested paths.
2. The addition of the `requiredCtx` parameter is not backward compatible with existing calls to `toDataFrame`.

## Evidence
- `packages/grafana-data/src/dataframe/processDataFrame.ts:305`: The function `toDataFrame` now requires a `RequiredContext` parameter.
- `packages/grafana-data/src/dataframe/processDataFrame.test.ts:1-79`: Existing tests for `toDataFrame` do not account for the new `requiredCtx` parameter.

## Impact
- The change could break existing code that calls `toDataFrame` without the new parameter, leading to runtime errors.
- Lack of updated tests means potential bugs introduced by this change may go undetected, affecting data processing reliability.

## Recommendation (Fix / Tests / Risks)
1. Update all existing calls to `toDataFrame` to include the `requiredCtx` parameter to maintain compatibility.
2. Modify the test suite to include tests for the new parameter, ensuring all code paths are covered.
3. Consider providing a default value for `requiredCtx` to maintain backward compatibility, if feasible.

## Traceability
Not specified
```