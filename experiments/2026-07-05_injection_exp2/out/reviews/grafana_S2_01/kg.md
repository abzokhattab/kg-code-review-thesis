```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `toDataFrame` function to include an additional `requiredCtx` parameter for future feature work.

## Problem
1. The addition of the `requiredCtx` parameter to `toDataFrame` is not backward compatible, potentially breaking existing code that calls this function.
2. The updated function signature is not reflected in the dependent test files, which may lead to inadequate test coverage and undetected issues.

## Evidence
- `packages/grafana-data/src/dataframe/processDataFrame.ts:305`: The function signature of `toDataFrame` is changed to include `requiredCtx`.
- `packages/grafana-data/src/dataframe/utils.test.ts`, `packages/grafana-data/src/dataframe/frameComparisons.test.ts`, `packages/grafana-data/src/dataframe/processDataFrame.test.ts`: These test files depend on `toDataFrame` but do not show any changes to accommodate the new parameter.

## Impact
- The change in the function signature without updating all call sites can lead to runtime errors where `toDataFrame` is used without the new `requiredCtx` parameter.
- Lack of updated tests could result in insufficient coverage, allowing bugs related to the new parameter to go unnoticed until they cause failures in production.

## Recommendation (Fix / Tests / Risks)
1. Update all call sites of `toDataFrame` to include the `requiredCtx` parameter to ensure compatibility and prevent runtime errors.
2. Modify existing tests and add new ones to cover scenarios involving the `requiredCtx` parameter to ensure comprehensive test coverage.
3. Consider implementing a default value or an overload for `toDataFrame` to maintain backward compatibility if immediate updates to all call sites are not feasible.

## Traceability
Not specified
```