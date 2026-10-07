```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package.

## Problem
1. The `MutableDataFrame` class is no longer exported from `index.ts`, which may break modules that depend on this export.
2. The removal of `MutableDataFrame` from exports is not accompanied by any changes in the dependent files, suggesting potential integration issues.

## Evidence
- `packages/grafana-data/src/index.ts:10`: The `MutableDataFrame` export has been removed.
- `packages/grafana-data/src/utils/csv.ts`: Contains a lambda function that calls `MutableDataFrame.addFieldFor`.
- `packages/grafana-data/src/transformations/transformers/merge.ts`: Contains a lambda function that calls `MutableDataFrame.addField`.
- `packages/grafana-data/src/transformations/transformers/seriesToRows.ts`: Contains a lambda function that calls `MutableDataFrame.addField`.

## Impact
The removal of `MutableDataFrame` from the exports can lead to runtime errors in any module that relies on importing `MutableDataFrame` from `index.ts`. This can cause functionality that depends on `MutableDataFrame` to fail, potentially affecting data processing and transformation features within the application.

## Recommendation (Fix / Tests / Risks)
1. Re-evaluate the necessity of removing `MutableDataFrame` from exports. If it is still needed, consider re-exporting it or providing an alternative.
2. Conduct a thorough search for all modules that import `MutableDataFrame` from `index.ts` and update their import paths if necessary.
3. Add integration tests to ensure that modules dependent on `MutableDataFrame` continue to function correctly after this change.

## Traceability
Not specified
```