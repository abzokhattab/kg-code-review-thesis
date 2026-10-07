```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of a function in the StreamingDataFrame module.

## Problem
1. The function `closestIdxInternal` is still exported, which may lead to misuse if intended for internal use only.
2. There is no update to the related test cases to reflect the name change, which could lead to test failures or inadequate test coverage.

## Evidence
- `packages/grafana-data/src/dataframe/StreamingDataFrame.ts:509`: The function `closestIdxInternal` is exported, suggesting it is available for external use.
- No changes in `packages/grafana-data/src/dataframe/StreamingDataFrame.test.ts` to reflect the function name change, indicating potential gaps in test coverage.

## Impact
- Exporting a function intended for internal use could lead to unintended dependencies and misuse by other modules or external code.
- Lack of updated test cases may result in undetected issues if the function's behavior changes in the future, as the tests may not accurately reflect the current implementation.

## Recommendation (Fix / Tests / Risks)
1. If `closestIdxInternal` is intended for internal use only, remove the `export` keyword to restrict its visibility.
2. Update the test cases in `StreamingDataFrame.test.ts` to use the new function name `closestIdxInternal` to ensure test coverage is maintained.
3. Verify that no external modules rely on the `closestIdx` function due to its previous export status, and update any dependencies accordingly.

## Traceability
- Code Owner: Not specified
```