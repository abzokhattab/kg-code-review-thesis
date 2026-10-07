```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `getFieldDisplayName` function to accept a `RequiredContext` parameter, preparing it for upcoming feature work.

## Problem
1. The introduction of the `RequiredContext` parameter in `getFieldDisplayName` may break existing functionality where this function is called without the new parameter.
2. There is insufficient test coverage for the changes, particularly concerning the new `RequiredContext` parameter's impact on existing functionality.

## Evidence
- `packages/grafana-data/src/field/fieldState.ts:109`: The function signature of `getFieldDisplayName` is modified to include `requiredCtx: RequiredContext`.
- `packages/grafana-data/src/field/fieldState.test.ts`: No new tests are added to verify the behavior of `getFieldDisplayName` with the `RequiredContext` parameter.
- `packages/grafana-data/src/dataframe/processDataFrame.ts:line` and `packages/grafana-data/src/transformations/matchers/nameMatcher.ts:line`: These files call `getFieldDisplayName` but are not updated to pass the new `RequiredContext` parameter.

## Impact
- The change could lead to runtime errors or unexpected behavior in parts of the application that rely on `getFieldDisplayName` without updating the function calls to include the new `RequiredContext` parameter.
- Lack of test coverage increases the risk of undetected bugs, especially in scenarios where the new parameter affects the function's logic.

## Recommendation (Fix / Tests / Risks)
1. Update all call sites of `getFieldDisplayName` to include the `RequiredContext` parameter to prevent runtime errors.
2. Add unit tests in `packages/grafana-data/src/field/fieldState.test.ts` to cover scenarios involving the `RequiredContext` parameter, ensuring the function behaves as expected.
3. Conduct integration testing to ensure that changes do not negatively impact dependent modules, particularly those listed in the call-graph.

## Traceability
- Code owners for `packages/grafana-data/src/field/fieldState.ts` and related test files are not specified.
```