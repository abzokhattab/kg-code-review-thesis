```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `getFieldDisplayName` function to include a new parameter `requiredCtx` for future feature work.

## Problem
1. The introduction of the `requiredCtx` parameter is not utilized within the function, which may lead to confusion and maintenance challenges.
2. The refactor does not include any updates to existing unit tests or new tests to cover the changes, risking potential regressions.

## Evidence
- `packages/grafana-data/src/field/fieldState.ts:109`: The `requiredCtx` parameter is added but not used within the function body.
- Lack of corresponding test updates or additions in the diff for `getFieldDisplayName`.

## Impact
- The unused `requiredCtx` parameter could lead to misunderstandings about its purpose and future use, increasing the cognitive load for developers maintaining this code.
- Absence of test updates or new tests could result in undetected bugs or regressions, especially if future changes rely on the new parameter.

## Recommendation (Fix / Tests / Risks)
1. Clarify the intended use of `requiredCtx` by either implementing its logic within the function or documenting its future purpose.
2. Add or update unit tests to ensure the function behaves correctly with the new parameter, preventing regressions.
3. Consider adding comments or documentation to explain the planned integration of `requiredCtx` to assist future development efforts.

## Traceability
Not specified
```