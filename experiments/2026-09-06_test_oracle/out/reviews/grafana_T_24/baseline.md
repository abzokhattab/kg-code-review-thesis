```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming within the string utility module.

## Problem
1. The function `escapeStringForRegexInternal` is renamed but lacks documentation updates or comments explaining the internal usage.
2. The refactor may affect external modules if this function was previously exposed or used outside the intended scope.

## Evidence
- `packages/grafana-data/src/text/string.ts:8`: The function name is changed from `escapeStringForRegex` to `escapeStringForRegexInternal`.

## Impact
- The renaming could lead to confusion or misuse if the function is used externally, as the name suggests it's for internal use only. Without proper documentation, developers might not understand the intended scope.
- If this function is part of a public API, this change could break existing integrations that rely on the original function name.

## Recommendation (Fix / Tests / Risks)
1. Add a comment above the `escapeStringForRegexInternal` function to clarify its intended internal use and any limitations.
2. Verify if this function is used outside the module. If so, consider maintaining the original name or providing a deprecation notice.
3. Ensure that any dependent modules or documentation are updated to reflect this change.

## Traceability
Not specified
```