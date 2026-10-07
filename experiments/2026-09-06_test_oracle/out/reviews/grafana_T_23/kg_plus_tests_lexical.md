```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming in the sanitize function within the Grafana data package.

## Problem
1. The renaming of the function `sanitizeTextPanelContent` to `sanitizeTextPanelContentInternal` may affect external dependencies if not properly encapsulated.
2. Lack of updates in related test files to reflect the new function name, which could lead to test failures or missed test coverage.

## Evidence
- `packages/grafana-data/src/text/sanitize.ts:95`: The function name is changed from `sanitizeTextPanelContent` to `sanitizeTextPanelContentInternal`.
- `packages/grafana-data/src/text/sanitize.test.ts`: No changes observed in test cases to accommodate the new function name.
- `packages/grafana-data/src/text/markdown.ts`: This file imports the `sanitizeTextPanelContent` function, which may be impacted by the name change.

## Impact
- The renaming could break any external code that relies on the original function name if it is not truly internal or if the change is not propagated correctly.
- Tests may fail or not execute the intended code if they are not updated to reflect the new function name, leading to potential undetected bugs.

## Recommendation (Fix / Tests / Risks)
1. Verify that `sanitizeTextPanelContent` is not used externally or update all references to the new name if it is indeed internal.
2. Update `packages/grafana-data/src/text/sanitize.test.ts` to use the new function name to ensure all tests are valid and cover the intended functionality.
3. Confirm that `packages/grafana-data/src/text/markdown.ts` and any other dependent files are updated to use the new function name, or ensure backward compatibility if necessary.

## Traceability
- Code Owner: Not specified
```