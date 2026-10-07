```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `getFieldDisplayName` function to include an additional parameter `requiredCtx` for future feature work.

## Problem
1. The addition of the `requiredCtx` parameter to `getFieldDisplayName` may break existing functionality or integrations that rely on the previous function signature.
2. There is a lack of updated test coverage to ensure that the new parameter does not introduce regressions or unexpected behavior.

## Evidence
- `packages/grafana-data/src/field/fieldState.ts:108`: The function signature of `getFieldDisplayName` has been changed to include `requiredCtx`.
- `packages/grafana-data/src/dataframe/StreamingDataFrame.test.ts`: No updates to tests to cover the new parameter.
- `packages/grafana-data/src/transformations/transformers/calculateField.test.ts`: Existing tests do not account for the `requiredCtx` parameter.

## Impact
- The change in function signature could lead to runtime errors or unexpected behavior in modules that call `getFieldDisplayName` without the new `requiredCtx` parameter.
- Without adequate test coverage, there is a risk of introducing regressions that could affect data processing and transformation features that depend on this function.

## Recommendation (Fix / Tests / Risks)
1. Update all call sites of `getFieldDisplayName` to include the `requiredCtx` parameter to prevent runtime errors.
2. Add or modify existing tests in `StreamingDataFrame.test.ts` and `calculateField.test.ts` to cover scenarios involving the new parameter.
3. Ensure that any dependent modules or functions are reviewed for compatibility with the new function signature.

## Traceability
- Code owners of `packages/grafana-data/src/field/fieldState.ts` and related test files should be consulted for integration and testing strategies.
```