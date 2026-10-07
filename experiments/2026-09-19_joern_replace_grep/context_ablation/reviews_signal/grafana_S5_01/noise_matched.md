```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the index file of the grafana-data package.

## Problem
1. The removal of `getDisplayProcessor` from exports may break existing functionality that depends on this function.
2. Lack of clarity on whether the removal of `getDisplayProcessor` is intentional and if it has been deprecated or replaced.

## Evidence
- `packages/grafana-data/src/index.ts:180`: The line removing `getDisplayProcessor` from exports.
- Call-graph context indicates that `getDisplayProcessor` might be used in other parts of the codebase, but specific references are not provided in the current context.

## Impact
- Removing `getDisplayProcessor` from exports could lead to runtime errors in parts of the application that rely on this function, potentially causing failures in data processing or display functionalities.
- If the function is still being used internally or by external modules, this change could lead to broken dependencies and hinder the functionality of the application.

## Recommendation (Fix / Tests / Risks)
1. Verify if `getDisplayProcessor` is still used elsewhere in the codebase or by external modules. If so, reconsider its removal or provide an alternative solution.
2. If `getDisplayProcessor` is deprecated, ensure that all dependencies are updated to use the new method and communicate this change clearly in the documentation.
3. Add tests to verify that the removal of `getDisplayProcessor` does not affect existing functionalities, especially in modules that might use this function indirectly.

## Traceability
Not specified
```