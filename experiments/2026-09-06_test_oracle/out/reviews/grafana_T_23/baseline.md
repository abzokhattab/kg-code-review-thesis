```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of the `sanitizeTextPanelContent` function to `sanitizeTextPanelContentInternal`.

## Problem
1. The renaming of the function may affect other parts of the codebase if this function is used externally.
2. Lack of test updates or additions to verify that the refactoring does not break existing functionality.

## Evidence
- `packages/grafana-data/src/text/sanitize.ts:98`: The function `sanitizeTextPanelContent` is renamed to `sanitizeTextPanelContentInternal`.

## Impact
- If `sanitizeTextPanelContent` is used in other parts of the codebase or by external modules, this change could lead to runtime errors or broken functionality due to the missing function reference.
- Without corresponding test updates, there's a risk that this change could introduce undetected issues, especially if the function is part of a public API or used in integration points.

## Recommendation (Fix / Tests / Risks)
1. Conduct a thorough search across the codebase to identify all usages of `sanitizeTextPanelContent` and update them to use the new name `sanitizeTextPanelContentInternal`.
2. Add or update existing unit tests to ensure that the function's behavior remains consistent after the renaming.
3. Consider adding a deprecation notice or alias for the old function name if it is part of a public API to prevent breaking changes for external users.

## Traceability
Not specified
```