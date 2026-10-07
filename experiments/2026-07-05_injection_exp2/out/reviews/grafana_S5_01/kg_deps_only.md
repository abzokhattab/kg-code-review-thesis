```
# Review Note — Evidence-Anchored

**Scope:** This PR modifies the export statements in the `index.ts` file of the `grafana-data` package, specifically removing the export of `getDisplayProcessor`.

## Problem
1. The removal of `getDisplayProcessor` from the exports may break dependent modules or packages that rely on this function.
2. There is no evidence of updated tests or documentation to reflect this change, which might lead to confusion or errors in usage.

## Evidence
- `packages/grafana-data/src/index.ts:180`: The line where `getDisplayProcessor` export is removed.

## Impact
- Removing the export of `getDisplayProcessor` could lead to runtime errors in any module that imports this function from `grafana-data`. This could affect the stability of the application if not all dependencies are updated accordingly.
- Lack of test updates increases the risk of this change going unnoticed until runtime, potentially causing failures in production environments.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Ensure that all internal and external dependencies are updated to no longer rely on `getDisplayProcessor` being exported from `grafana-data`.
2. **Tests:** Add or update tests to verify that the removal of `getDisplayProcessor` does not break existing functionality.
3. **Documentation:** Update any relevant documentation to reflect this change in exports, ensuring that developers are aware of the new usage patterns.

## Traceability
- Code Owner: Grafana Data Team (assumed based on package name)
```