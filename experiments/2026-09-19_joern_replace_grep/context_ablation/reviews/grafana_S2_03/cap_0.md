```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `getFieldDisplayName` function to include a new parameter `requiredCtx` for future feature work.

## Problem
1. The introduction of the `requiredCtx` parameter is not accompanied by any documentation or comments explaining its purpose or usage.
2. There are no corresponding updates to unit tests or new tests added to verify the behavior with the `requiredCtx` parameter.

## Evidence
- `packages/grafana-data/src/field/fieldState.ts:109`: The function signature of `getFieldDisplayName` is modified to include `requiredCtx`, but there is no explanation or usage context provided.
- Lack of changes in test files related to `fieldState.ts` indicates that the new parameter is not being tested.

## Impact
- Without documentation, future developers may not understand the purpose of the `requiredCtx` parameter, leading to misuse or incorrect assumptions.
- The absence of tests means that any issues introduced by this change may go unnoticed, potentially causing bugs in the application that depend on this function.

## Recommendation (Fix / Tests / Risks)
1. Add comments or documentation explaining the purpose and expected usage of the `requiredCtx` parameter.
2. Update existing unit tests or add new tests to cover scenarios involving the `requiredCtx` parameter to ensure its correct behavior.
3. Verify that the addition of `requiredCtx` does not break existing functionality by running a full test suite.

## Traceability
Not specified
```