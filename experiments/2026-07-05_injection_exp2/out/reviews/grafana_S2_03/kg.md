```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `getFieldDisplayName` function to include a new parameter `requiredCtx` for future feature work.

## Problem
1. The addition of the `requiredCtx` parameter to `getFieldDisplayName` may break existing functionality where this function is called without the new parameter.
2. There is a lack of test coverage to verify the behavior of `getFieldDisplayName` with the new `requiredCtx` parameter.

## Evidence
- `packages/grafana-data/src/field/fieldState.ts:108`: The function signature of `getFieldDisplayName` is changed to include `requiredCtx`.
- `packages/grafana-data/src/dataframe/processDataFrame.ts`: This file calls `getFieldDisplayName` but is not updated to pass the new `requiredCtx` parameter.
- `packages/grafana-data/src/transformations/transformers/calculateField.test.ts`: No new tests are added to cover the changes in `getFieldDisplayName`.

## Impact
- **Technical Impact:** The change in the function signature can lead to runtime errors in parts of the codebase that call `getFieldDisplayName` without the `requiredCtx` parameter. This could cause unexpected behavior or crashes in data processing and transformation operations.
- **Risk:** Without adequate test coverage, there is a risk that the new parameter does not integrate well with existing functionality, leading to potential data display issues.

## Recommendation (Fix / Tests / Risks)
1. Update all call sites of `getFieldDisplayName` to include the `requiredCtx` parameter, ensuring compatibility with the new function signature.
2. Add unit tests specifically for `getFieldDisplayName` to verify its behavior with different values of `requiredCtx`.
3. Conduct integration tests to ensure that the changes do not negatively impact the dependent modules, particularly in data transformation and display logic.

## Traceability
- Code owners of `packages/grafana-data/src/field/fieldState.ts` and related transformation modules should be consulted to ensure alignment with the intended feature work.
```