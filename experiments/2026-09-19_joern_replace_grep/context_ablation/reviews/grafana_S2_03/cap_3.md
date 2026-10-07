```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `getFieldDisplayName` function to include a new parameter `requiredCtx` for upcoming feature work.

## Problem
1. The introduction of the `requiredCtx` parameter lacks backward compatibility, potentially breaking existing calls to `getFieldDisplayName`.
2. The change in function signature is not accompanied by corresponding updates in all calling functions, which may lead to runtime errors.
3. There is no evidence of updated or additional test coverage to ensure the new parameter's integration does not introduce regressions.

## Evidence
- `packages/grafana-data/src/field/fieldState.ts:108`: The function signature of `getFieldDisplayName` has been modified to include a new `requiredCtx` parameter.
- `packages/grafana-data/src/dataframe/processDataFrame.ts`: The function `toLegacyResponseData` calls `getFieldDisplayName` but has not been updated to pass the new `requiredCtx` parameter.
- `packages/grafana-data/src/field/fieldDisplay.ts`: Functions `getSmartDisplayNameForRow` and `getFieldDisplayValues` call `getFieldDisplayName` but have not been updated to accommodate the new parameter.

## Impact
The technical impact includes potential runtime errors due to missing arguments in existing function calls. This could lead to application crashes or incorrect display names being generated, affecting user experience. Additionally, without proper test coverage, there is a risk of undetected regressions.

## Recommendation (Fix / Tests / Risks)
1. Update all calling functions (`toLegacyResponseData`, `getSmartDisplayNameForRow`, `getFieldDisplayValues`) to include the `requiredCtx` parameter.
2. Ensure backward compatibility by providing a default value for `requiredCtx` or overloading the function to handle calls without this parameter.
3. Add or update tests to cover the new function signature and ensure no regressions occur due to this change.

## Traceability
- Code Owner: Data Processing Team (assumed based on file path and function usage)
```