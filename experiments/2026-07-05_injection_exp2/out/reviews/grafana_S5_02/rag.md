```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package.

## Problem
1. Incomplete Export Removal: The removal of `MutableDataFrame` from the exports list may lead to unintended consequences if it is still being used elsewhere.
2. Consistency with Internal Exports: The change does not address whether similar adjustments are needed in internal exports, potentially leading to inconsistencies.

## Evidence
- `packages/grafana-data/src/index.ts:12`: The line where `MutableDataFrame` was removed from exports.
- Semantically similar files (e.g., `packages/grafana-data/src/internal/index.ts`) show consistent export patterns that might need similar review.

## Impact
- Removing `MutableDataFrame` from exports could break modules or plugins that rely on it, leading to runtime errors.
- Inconsistencies between public and internal exports could lead to maintenance challenges and confusion about which components are available for use.

## Recommendation (Fix / Tests / Risks)
1. **Fix**: Verify if `MutableDataFrame` is used elsewhere in the codebase or by external modules. If so, consider retaining the export or providing an alternative.
2. **Tests**: Ensure comprehensive tests are in place to catch any issues arising from this change, particularly focusing on modules that might import `MutableDataFrame`.
3. **Risks**: Assess the risk of this change by reviewing the dependency graph for `MutableDataFrame` to understand its usage and impact.

## Traceability
Not specified
```