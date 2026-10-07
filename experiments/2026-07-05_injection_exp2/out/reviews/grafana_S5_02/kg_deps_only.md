```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package.

## Problem
1. Removal of `MutableDataFrame` export may break dependencies that rely on this export.
2. Lack of test updates or additions to verify the impact of the export change.

## Evidence
- `packages/grafana-data/src/index.ts:12`: The export of `MutableDataFrame` has been removed.

## Impact
- The removal of the `MutableDataFrame` export can lead to runtime errors in any module that imports this class from `grafana-data`. This could break functionality in parts of the application that depend on `MutableDataFrame`.
- Without corresponding test updates, it is unclear if the existing test suite covers the potential impact of this change, increasing the risk of undetected issues.

## Recommendation (Fix / Tests / Risks)
1. Review all modules that import `MutableDataFrame` to ensure they are not affected by this change. Re-export `MutableDataFrame` if necessary.
2. Add or update tests to specifically cover the use cases of `MutableDataFrame` to ensure that its removal as an export does not introduce any regressions.
3. Consider adding a deprecation notice or migration guide if the removal is intentional and necessary, to inform developers of the change.

## Traceability
- Code Owner: Not specified
```