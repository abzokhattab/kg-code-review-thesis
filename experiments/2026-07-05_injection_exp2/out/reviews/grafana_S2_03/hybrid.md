```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `getFieldDisplayName` function to include a `RequiredContext` parameter for future feature enhancements.

## Problem
1. The refactoring introduces a new parameter `RequiredContext` without clear documentation or usage examples, which may lead to confusion about its purpose and integration.
2. The change impacts multiple dependent files and functions, but there is no indication of corresponding updates to test cases to ensure the refactor does not introduce regressions.
3. The refactor could potentially break existing functionality if the new parameter is not handled correctly in all call sites.

## Evidence
- `packages/grafana-data/src/field/fieldState.ts:107`: Introduction of `requiredCtx` parameter in `getFieldDisplayName`.
- Dependent files such as `packages/grafana-data/src/dataframe/processDataFrame.ts`, `packages/grafana-data/src/transformations/transformers/filterByValue.ts`, and others are affected but not shown to have corresponding updates or tests.
- Similar function `getSmartDisplayNameForRow` in `packages/grafana-data/src/field/fieldDisplay.ts:189-254` handles context and display logic, suggesting potential integration points or patterns.

## Impact
- The introduction of an undocumented parameter can lead to integration issues across multiple modules that depend on `getFieldDisplayName`.
- Without updated tests, there is a risk of regressions, especially in modules that heavily rely on display name logic for data visualization.
- Potential for runtime errors if the new parameter is not correctly initialized or used in all contexts.

## Recommendation (Fix / Tests / Risks)
1. Document the purpose and expected usage of the `RequiredContext` parameter, including examples if possible.
2. Review and update all dependent modules to ensure they handle the new parameter correctly.
3. Add or update test cases in files such as `StreamingDataFrame.test.ts` and `calculateField.test.ts` to cover scenarios involving the new parameter.
4. Conduct a thorough integration test to ensure no regressions occur in the data transformation and display logic.

## Traceability
Not specified
```