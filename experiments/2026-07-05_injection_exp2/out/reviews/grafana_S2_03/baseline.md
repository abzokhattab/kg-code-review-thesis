```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `getFieldDisplayName` function to include a new parameter `requiredCtx` for future feature work.

## Problem
1. The introduction of the `requiredCtx` parameter is not accompanied by any usage or documentation, making its purpose unclear.
2. There is no evidence of updated test cases to cover the changes made to the function signature.

## Evidence
- `packages/grafana-data/src/field/fieldState.ts:109`: The function signature of `getFieldDisplayName` has been changed to include `requiredCtx`, but there are no comments or documentation explaining its intended use.
- No changes in test files or new test cases are visible in the diff to verify the behavior of the refactored function.

## Impact
- The lack of documentation and test coverage for the new parameter could lead to confusion among developers and potential misuse of the function.
- Without tests, there is a risk that the function may not behave as expected in all scenarios, especially with the new parameter, leading to potential bugs in the application.

## Recommendation (Fix / Tests / Risks)
1. Add documentation or comments explaining the purpose and expected values of the `requiredCtx` parameter.
2. Update existing test cases or add new ones to cover the changes in the function signature, ensuring that the function behaves correctly with the new parameter.
3. Ensure that any dependent code or modules that use `getFieldDisplayName` are reviewed for compatibility with the new parameter.

## Traceability
Not specified
```