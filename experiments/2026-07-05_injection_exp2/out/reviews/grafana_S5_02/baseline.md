```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the package exports in the index file of the grafana-data package.

## Problem
1. The removal of `MutableDataFrame` from the exports may lead to issues if it is used elsewhere in the codebase.
2. Lack of context or documentation on why `MutableDataFrame` was removed from exports.

## Evidence
- `packages/grafana-data/src/index.ts:12`: The line where `MutableDataFrame` was removed from the exports.

## Impact
- Removing `MutableDataFrame` from the exports could break functionality in other parts of the application that rely on this export. This could lead to runtime errors or failures in modules that expect `MutableDataFrame` to be available.
- Without clear documentation or rationale, other developers may be confused about the change, leading to potential miscommunication or misalignment in future development efforts.

## Recommendation (Fix / Tests / Risks)
1. Verify if `MutableDataFrame` is used in other parts of the codebase. If it is, consider re-exporting it or refactoring those parts to not rely on it.
2. Provide documentation or comments in the code explaining the rationale behind removing `MutableDataFrame` from the exports to aid future maintainability.
3. Run a comprehensive test suite to ensure that removing this export does not introduce any regressions or break existing functionality.

## Traceability
Not specified
```