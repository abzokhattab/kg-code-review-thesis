```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of a function in the sanitize module.

## Problem
1. The renaming of the function `sanitizeTextPanelContent` to `sanitizeTextPanelContentInternal` is not reflected in all dependent files.
2. The related test file `sanitize.test.ts` does not appear to have been updated to reflect the function name change.

## Evidence
- `packages/grafana-data/src/text/sanitize.ts:95`: Function renamed to `sanitizeTextPanelContentInternal`.
- `packages/grafana-data/src/text/markdown.ts`: This file imports `sanitizeTextPanelContent`, which may now be broken due to the renaming.
- `packages/grafana-data/src/text/sanitize.test.ts`: No changes in the test file to accommodate the new function name.

## Impact
- The renaming could lead to runtime errors in any module that imports `sanitizeTextPanelContent` if they are not updated to the new name.
- Tests may fail or not cover the intended function due to the unchanged references, leading to potential undetected issues in the sanitization logic.

## Recommendation (Fix / Tests / Risks)
1. Update all dependent files, such as `markdown.ts`, to use the new function name `sanitizeTextPanelContentInternal`.
2. Modify the test file `sanitize.test.ts` to reflect the function name change and ensure all tests are passing.
3. Consider adding a deprecation warning or alias for `sanitizeTextPanelContent` if it is widely used, to prevent breaking changes.

## Traceability
- Code Owner: Not specified
```