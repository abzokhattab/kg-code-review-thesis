```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the index file of the grafana-data package.

## Problem
1. The `MutableDataFrame` class is no longer exported from `index.ts`, which might affect modules that depend on this export.
2. There is a lack of test coverage to ensure that removing `MutableDataFrame` from the exports does not break existing functionality.

## Evidence
- `packages/grafana-data/src/index.ts:12`: `MutableDataFrame` export has been removed.
- `packages/grafana-data/src/dataframe/MutableDataFrame.test.ts`: No tests appear to directly verify the impact of removing `MutableDataFrame` from exports.
- `packages/grafana-data/src/transformations/transformers/merge.ts`: This file depends on `MutableDataFrame`, which could be impacted by its removal from exports.

## Impact
- Removing `MutableDataFrame` from the exports could lead to runtime errors in modules that rely on it being available through the package's main entry point.
- This change might break backward compatibility, affecting any external code that imports `MutableDataFrame` directly from the package.

## Recommendation (Fix / Tests / Risks)
1. Re-evaluate the necessity of removing `MutableDataFrame` from the exports. If it is required, ensure that all dependent modules are updated accordingly.
2. Add tests to verify that the removal of `MutableDataFrame` from exports does not break existing functionality or dependent modules.
3. Consider providing a migration guide or deprecation notice if this change is intended to be permanent.

## Traceability
- Code Owners: Not specified
```