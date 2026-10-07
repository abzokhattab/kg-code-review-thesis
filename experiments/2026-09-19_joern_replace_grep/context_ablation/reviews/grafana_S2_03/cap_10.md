```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `getFieldDisplayName` function to include a new parameter `requiredCtx` for future feature expansions.

## Problem
1. **Backward Compatibility Risk:** The addition of a new required parameter `requiredCtx` to `getFieldDisplayName` may break existing calls that do not provide this argument.
2. **Insufficient Test Coverage:** There is no evidence of updated tests to cover the new parameter `requiredCtx`, which could lead to undetected bugs.
3. **Integration Complexity:** The function `getFieldDisplayName` is widely used across multiple files, increasing the risk of integration issues if all call sites are not updated accordingly.

## Evidence
- **Backward Compatibility Risk:**
  - `packages/grafana-data/src/field/fieldState.ts:106`: The function signature change from `getFieldDisplayName(field, frame, allFrames)` to `getFieldDisplayName(requiredCtx, field, frame, allFrames)`.

- **Insufficient Test Coverage:**
  - No changes in test files related to `getFieldDisplayName` were observed in the diff, indicating a lack of test updates for the new parameter.

- **Integration Complexity:**
  - Multiple call sites affected, such as:
    - `packages/grafana-data/src/dataframe/processDataFrame.ts::toLegacyResponseData`
    - `packages/grafana-data/src/field/fieldDisplay.ts::getSmartDisplayNameForRow`
    - `packages/grafana-data/src/transformations/matchers/nameMatcher.ts::matcher`

## Impact
- **Technical Impact:** Existing code that calls `getFieldDisplayName` without the new `requiredCtx` parameter will break, potentially causing runtime errors. The lack of updated tests increases the risk of introducing bugs that could affect data display functionalities.
- **Risk of Integration Failures:** Given the function's integration into various parts of the codebase, any oversight in updating call sites could lead to widespread issues.

## Recommendation (Fix / Tests / Risks)
1. **Backward Compatibility:** Consider providing a default value for `requiredCtx` or overloading the function to maintain backward compatibility.
2. **Update Tests:** Add or update tests to cover the new parameter `requiredCtx`, ensuring that all code paths are validated.
3. **Comprehensive Refactoring:** Ensure all call sites are updated to pass the new parameter, and conduct a thorough integration test to verify that the changes do not introduce new issues.

## Traceability
- **Code Owners:** Not specified
```