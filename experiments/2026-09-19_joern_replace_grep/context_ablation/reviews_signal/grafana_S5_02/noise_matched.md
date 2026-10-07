```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package.

## Problem
1. The removal of `MutableDataFrame` from the exports may break existing code that relies on this export.
2. Lack of test coverage for the impact of removing `MutableDataFrame` from the exports.

## Evidence
- `packages/grafana-data/src/index.ts:10`: The line where `MutableDataFrame` export is removed.
- `packages/grafana-data/src/dataframe/processDataFrame.ts`: This file calls functions from `index.ts`, indicating potential dependencies on the exports.
- `packages/grafana-data/src/transformations/transformers/sortBy.ts`: Calls functions from `index.ts`, which may rely on `MutableDataFrame`.

## Impact
- Removing `MutableDataFrame` from exports could lead to runtime errors in any module or file that imports it from `index.ts`. This could affect the stability of the application if not caught before deployment.
- The lack of test coverage means that any issues arising from this change might not be detected until runtime, increasing the risk of undetected bugs.

## Recommendation (Fix / Tests / Risks)
1. Re-evaluate the necessity of removing `MutableDataFrame` from the exports. If it is still needed, consider maintaining the export to avoid breaking changes.
2. Add test cases to ensure that the removal of `MutableDataFrame` does not affect existing functionality or introduce bugs.
3. Conduct a thorough search for any internal or external dependencies on `MutableDataFrame` to assess the full impact of its removal.

## Traceability
- Code Owner: Not specified
```