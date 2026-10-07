```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `getFieldDisplayName` function to include a new `RequiredContext` parameter, preparing for upcoming feature work.

## Problem
1. The introduction of the `RequiredContext` parameter may break existing function calls that do not provide this new argument.
2. There is a lack of test coverage for the new parameter, which could lead to undetected issues in its usage.
3. The change affects multiple files that call this function, increasing the risk of integration issues.

## Evidence
- `packages/grafana-data/src/field/fieldState.ts:106`: The function signature of `getFieldDisplayName` has changed, requiring a new `RequiredContext` parameter.
- `packages/grafana-data/src/dataframe/processDataFrame.ts`: Calls `getFieldDisplayName` but does not pass the new `RequiredContext` parameter.
- `packages/grafana-data/src/field/fieldDisplay.ts`: Multiple functions (`getSmartDisplayNameForRow`, `getFieldDisplayValues`) call `getFieldDisplayName` without the new parameter.
- `packages/grafana-data/src/transformations/matchers/nameMatcher.ts`: Lambda functions and `matcher` call `getFieldDisplayName` without the new parameter.
- `packages/grafana-data/src/transformations/transformers/calculateField.ts`: Functions like `findFieldValuesWithNameOrConstant` call `getFieldDisplayName` without the new parameter.

## Impact
- The change could lead to runtime errors or unexpected behavior in any module that calls `getFieldDisplayName` without the new `RequiredContext` parameter.
- Lack of test coverage for the new parameter increases the risk of bugs going unnoticed, potentially affecting data display features across the application.
- Integration issues may arise due to the widespread usage of this function across different modules, affecting data processing and transformation functionalities.

## Recommendation (Fix / Tests / Risks)
1. Ensure all calls to `getFieldDisplayName` are updated to include the new `RequiredContext` parameter.
2. Add unit tests specifically for the `getFieldDisplayName` function to cover scenarios involving the new `RequiredContext` parameter.
3. Conduct integration testing to verify that changes do not adversely affect modules that rely on `getFieldDisplayName`.

## Traceability
- Code owners for `packages/grafana-data` and related transformation modules should be consulted. If not specified, consider involving the data processing team.
```