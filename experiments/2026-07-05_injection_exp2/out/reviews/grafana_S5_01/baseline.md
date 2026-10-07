```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package.

## Problem
1. The removal of `getDisplayProcessor` from the exports may affect modules that rely on this function.
2. There is no indication of updated documentation or migration notes for this change.

## Evidence
- `packages/grafana-data/src/index.ts:180`: The line removing `getDisplayProcessor` from exports.

## Impact
- Removing `getDisplayProcessor` from exports could break any external modules or plugins that depend on this function. This could lead to runtime errors or missing functionality in parts of the application that use this function.
- Lack of documentation or migration notes could lead to confusion among developers who rely on this function, increasing the maintenance burden.

## Recommendation (Fix / Tests / Risks)
1. Verify if `getDisplayProcessor` is used in other parts of the codebase or by external modules. If it is, consider keeping it exported or providing an alternative.
2. Update documentation to reflect this change and provide guidance on how to handle the absence of `getDisplayProcessor`.
3. Consider adding a deprecation warning if the function is to be removed in the future, allowing developers time to adjust.

## Traceability
Not specified
```