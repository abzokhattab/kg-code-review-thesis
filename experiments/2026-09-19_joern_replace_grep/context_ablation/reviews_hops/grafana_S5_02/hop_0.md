```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the `index.ts` file of the `grafana-data` package.

## Problem
1. The export of `MutableDataFrame` has been removed, which may impact modules relying on this export.
2. Lack of context or comments explaining the removal of `MutableDataFrame`, which could lead to confusion or misalignment with intended refactoring goals.

## Evidence
- `packages/grafana-data/src/index.ts:12`: The line exporting `MutableDataFrame` has been removed.

## Impact
- Removing the export of `MutableDataFrame` could break any module or component that imports this class from the `index.ts` file. This could lead to runtime errors or failures in dependent modules that expect this export to be available.
- Without documentation or comments, other developers might not understand the rationale behind this change, leading to potential miscommunication within the team.

## Recommendation (Fix / Tests / Risks)
1. Re-evaluate the necessity of removing `MutableDataFrame` from exports. If it is no longer needed, ensure all dependent modules are updated accordingly.
2. Add a comment or documentation explaining why `MutableDataFrame` was removed from exports to provide context for future developers.
3. Conduct a thorough search for any internal or external dependencies on `MutableDataFrame` to mitigate the risk of breaking changes.

## Traceability
Not specified
```