```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package.

## Problem
1. The `MutableDataFrame` export has been removed, which might affect other parts of the codebase that rely on this export.
2. There is no indication that the removal of `MutableDataFrame` is accompanied by corresponding updates in the dependent modules or test cases.

## Evidence
- `packages/grafana-data/src/index.ts:10`: The `MutableDataFrame` export is removed without any replacement or deprecation notice.

## Impact
- Removing `MutableDataFrame` from exports could break any module or component that imports it from `index.ts`. This can lead to runtime errors or failures in dependent systems that expect this export to be available.
- There is a risk of reduced functionality or broken features if `MutableDataFrame` is used in other parts of the application or by external consumers.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Ensure that all modules or components that rely on `MutableDataFrame` are updated to import it directly from its source file, or provide an alternative export path.
2. **Tests:** Verify that all existing test cases that involve `MutableDataFrame` are updated to reflect the changes in import paths. Add new tests if necessary to cover any changes in functionality.
3. **Risks:** Conduct a thorough search for all instances where `MutableDataFrame` is used across the codebase and document any necessary changes to maintain backward compatibility.

## Traceability
- Code Owners: Not specified
```