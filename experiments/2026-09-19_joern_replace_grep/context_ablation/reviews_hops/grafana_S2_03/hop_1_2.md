```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `getFieldDisplayName` function to include a new parameter `requiredCtx` for upcoming feature work.

## Problem
1. The addition of the `requiredCtx` parameter to `getFieldDisplayName` may break existing function calls that do not provide this new parameter.
2. There is a lack of test coverage for the new parameter `requiredCtx` in the existing test files.

## Evidence
- `packages/grafana-data/src/field/fieldState.ts:106`: The function signature of `getFieldDisplayName` has been changed to include `requiredCtx`.
- `packages/grafana-data/src/dataframe/StreamingDataFrame.test.ts`: No updates to test cases to include the new `requiredCtx` parameter.
- `packages/grafana-data/src/transformations/transformers/calculateField.test.ts`: No test cases added or modified to test the new parameter.

## Impact
- The change in the function signature could lead to runtime errors if the function is called without the new `requiredCtx` parameter, impacting any dependent code that has not been updated.
- Lack of test coverage for the new parameter increases the risk of undetected bugs or incorrect behavior related to the `requiredCtx` functionality.

## Recommendation (Fix / Tests / Risks)
1. Update all existing calls to `getFieldDisplayName` to include the `requiredCtx` parameter to prevent runtime errors.
2. Add or modify test cases in `StreamingDataFrame.test.ts` and `calculateField.test.ts` to ensure the new parameter is covered and behaves as expected.
3. Conduct a thorough review of all dependent files and ensure they are updated to handle the new parameter correctly.

## Traceability
- Code owners of `packages/grafana-data/src/field/fieldState.ts` and related test files should be consulted. If not specified, coordinate with the team responsible for the `grafana-data` package.
```