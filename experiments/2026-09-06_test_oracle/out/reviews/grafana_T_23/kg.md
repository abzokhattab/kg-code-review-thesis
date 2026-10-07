```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors an internal function name in the sanitize module.

## Problem
1. The function `sanitizeTextPanelContentInternal` is still being used externally, which contradicts the intent of marking it as internal.
2. Lack of updates to dependent files that import or call this function, potentially breaking existing functionality.

## Evidence
- `packages/grafana-data/src/text/sanitize.ts:95`: The function `sanitizeTextPanelContent` is renamed to `sanitizeTextPanelContentInternal`.
- `packages/grafana-data/src/text/markdown.ts`: This file depends on the changed function but is not updated in this PR.

## Impact
- Renaming the function to indicate it is internal without updating dependent files can lead to runtime errors where the function is used externally.
- This could break functionality in modules that rely on this function, leading to potential failures in text sanitization processes.

## Recommendation (Fix / Tests / Risks)
1. Review and update all files that import or call `sanitizeTextPanelContent` to use the new function name `sanitizeTextPanelContentInternal`.
2. Ensure that the function is truly intended for internal use only; if it is used externally, consider reverting the name change or providing a public-facing alias.
3. Add or update tests in `packages/grafana-data/src/text/markdown.ts` to ensure that the function name change does not affect its functionality.

## Traceability
- Code Owner: Not specified
```