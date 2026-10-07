```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `getFieldDisplayName` function to include a `requiredCtx` parameter for future feature work.

## Problem
1. The introduction of the `requiredCtx` parameter is not accompanied by any documentation or explanation of its intended use.
2. The change impacts multiple files and functions that call `getFieldDisplayName`, but there is no evidence of updated test coverage to ensure these integrations function correctly.
3. The refactor may introduce backward compatibility issues with existing code that relies on the previous function signature.

## Evidence
- `packages/grafana-data/src/field/fieldState.ts:106`: The function signature of `getFieldDisplayName` is changed to include a `requiredCtx` parameter.
- `packages/grafana-data/src/dataframe/processDataFrame.ts`: Calls to `getFieldDisplayName` are not updated to accommodate the new parameter.
- `packages/grafana-data/src/transformations/matchers/nameMatcher.ts`: Multiple lambda functions call `getFieldDisplayName` without changes to handle the new parameter.
- `packages/grafana-data/src/transformations/transformers/calculateField.ts`: Calls to `getFieldDisplayName` are unchanged, potentially leading to runtime errors.

## Impact
- The lack of documentation for `requiredCtx` can lead to misuse or misunderstanding of its purpose, affecting future development and maintenance.
- Without updated test coverage, there is a risk of introducing bugs or regressions in areas of the code that depend on `getFieldDisplayName`.
- Existing code that calls `getFieldDisplayName` may break due to the new required parameter, unless all call sites are updated accordingly.

## Recommendation (Fix / Tests / Risks)
1. Provide documentation or comments explaining the purpose and expected use of the `requiredCtx` parameter.
2. Update all call sites of `getFieldDisplayName` to handle the new parameter, ensuring backward compatibility or providing a migration path.
3. Expand test coverage to include scenarios with the `requiredCtx` parameter, verifying that all integrations behave as expected.
4. Consider adding deprecation warnings or a transitional strategy if backward compatibility cannot be maintained.

## Traceability
- Code Owners: The Grafana Data team is likely responsible for this area, but specific owners are not specified.
```