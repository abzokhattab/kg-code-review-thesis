```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `getFieldDisplayName` function to accept a `RequiredContext` parameter for future feature work.

## Problem
1. The introduction of the `RequiredContext` parameter lacks backward compatibility, potentially breaking existing calls to `getFieldDisplayName`.
2. There is no evidence of updated test cases to cover the new parameter, risking untested code paths.
3. The refactoring may impact multiple modules due to the function's extensive usage across different files.

## Evidence
- `packages/grafana-data/src/field/fieldState.ts:106`: The function signature of `getFieldDisplayName` is changed, adding a new `requiredCtx` parameter.
- `packages/grafana-data/src/dataframe/processDataFrame.ts`: Calls `getFieldDisplayName` without the new parameter, indicating potential breakage.
- `packages/grafana-data/src/field/fieldDisplay.ts`: Multiple functions (`getSmartDisplayNameForRow`, `getFieldDisplayValues`) call `getFieldDisplayName` without the new parameter.
- `packages/grafana-data/src/transformations/matchers/nameMatcher.ts`: Calls to `getFieldDisplayName` do not include the new parameter.

## Impact
The technical impact includes potential runtime errors or incorrect behavior due to missing the new `requiredCtx` parameter in existing function calls. This could lead to failures in data display logic and transformations, affecting user interfaces relying on these functions. Additionally, without updated test coverage, there's a risk of undetected bugs.

## Recommendation (Fix / Tests / Risks)
1. Ensure backward compatibility by providing a default value for `requiredCtx` or overloading the function to handle calls without the new parameter.
2. Update existing tests to include scenarios with the `requiredCtx` parameter and add new tests if necessary to cover all code paths.
3. Review all call sites of `getFieldDisplayName` to ensure they are updated to pass the new parameter, or refactor them to handle the parameter appropriately.

## Traceability
- Code Owners: Not specified
```