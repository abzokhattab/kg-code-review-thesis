```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package.

## Problem
1. The export of `MutableDataFrame` has been removed, which might affect modules relying on it.
2. Lack of clarity on whether the removal of `MutableDataFrame` is intentional and if dependent modules have been updated accordingly.

## Evidence
- `packages/grafana-data/src/index.ts:12`: The line where `MutableDataFrame` export was removed.

## Impact
- The removal of `MutableDataFrame` from exports could break functionality in other parts of the application or in external projects that depend on this package. If other modules or external users rely on this export, they will encounter runtime errors or broken imports, leading to potential application failures.

## Recommendation (Fix / Tests / Risks)
1. Verify if `MutableDataFrame` is used in other parts of the codebase or by external consumers. If it is, consider re-exporting it or providing an alternative solution.
2. Update documentation and notify relevant teams or users about this change if it is intentional.
3. Add tests or update existing ones to ensure that the removal of `MutableDataFrame` does not cause any regressions.

## Traceability
Not specified
```