```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package.

## Problem
1. The removal of `MutableDataFrame` from the exports may break dependencies that rely on it.
2. Insufficient test coverage to ensure that the removal of `MutableDataFrame` does not affect existing functionality.

## Evidence
- `packages/grafana-data/src/index.ts:12`: `MutableDataFrame` export has been removed.
- `packages/grafana-data/src/dataframe/CircularDataFrame.ts`: This file depends on `MutableDataFrame`.
- `packages/grafana-data/src/transformations/transformers/merge.ts`: This file depends on `MutableDataFrame`.
- `packages/grafana-data/src/transformations/transformers/seriesToRows.ts`: This file depends on `MutableDataFrame`.

## Impact
- Removing `MutableDataFrame` from exports could lead to runtime errors in modules that import it, potentially causing application failures.
- The lack of explicit test coverage for the removal of this export increases the risk of undetected issues in dependent modules.

## Recommendation (Fix / Tests / Risks)
1. Re-evaluate the necessity of removing `MutableDataFrame` from exports and consider keeping it if dependencies are not updated.
2. Add or update test cases in `MutableDataFrame.test.ts` to ensure that all dependent modules function correctly without direct access to `MutableDataFrame`.
3. Communicate with teams or code owners of dependent modules to ensure they are aware of this change and can make necessary adjustments.

## Traceability
- Code Owners: Not specified
```