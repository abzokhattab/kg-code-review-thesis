```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the index file of the grafana-data package.

## Problem
1. The `MutableDataFrame` export has been removed, which may affect modules that depend on it.
2. There is no evidence of updated test coverage to ensure the removal doesn't break functionality.

## Evidence
- `packages/grafana-data/src/index.ts:12`: The line removing `MutableDataFrame` from the exports.

## Impact
- Removing `MutableDataFrame` from the exports can lead to runtime errors in any module that imports it from this index file. This can cause failures in parts of the application relying on this functionality.
- Lack of test updates suggests that the impact of this change on existing functionality has not been verified, increasing the risk of undetected issues.

## Recommendation (Fix / Tests / Risks)
1. Review all modules that import `MutableDataFrame` to ensure they are updated to import it directly from `./dataframe/MutableDataFrame`.
2. Add or update tests to verify that the removal of `MutableDataFrame` from the exports does not break existing functionality.
3. Consider adding a deprecation notice or migration guide if this change is intended to be permanent.

## Traceability
- Code ownership: Grafana Data Team (assumed based on package name)
```