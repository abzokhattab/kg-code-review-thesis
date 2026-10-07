```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package.

## Problem
1. The `MutableDataFrame` class is no longer exported from `index.ts`, which could affect modules relying on this export.
2. There is a lack of clarity on whether all dependent modules have been updated to accommodate this change.

## Evidence
- `packages/grafana-data/src/index.ts:10`: The `MutableDataFrame` export has been removed.
- `packages/grafana-data/src/utils/csv.ts` and other files call `MutableDataFrame` methods, indicating reliance on this export.

## Impact
- Removing the `MutableDataFrame` export could lead to runtime errors in modules that depend on this class being available via the package's main entry point.
- This change might break existing integrations or cause failures in parts of the application that use `MutableDataFrame` if they are not updated accordingly.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Re-evaluate the necessity of removing the `MutableDataFrame` export. If removal is intended, ensure all dependent modules are updated to import `MutableDataFrame` directly from its file.
2. **Tests:** Add or update tests to verify that modules previously importing `MutableDataFrame` from `index.ts` are functioning correctly with the new import paths.
3. **Risks:** Conduct a thorough review of the codebase to identify any indirect dependencies on `MutableDataFrame` through `index.ts` and address them.

## Traceability
- Code Owners: Grafana Data Team (assumed based on package name)
```