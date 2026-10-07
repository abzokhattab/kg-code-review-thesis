```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the function name from `createDataFrame` to `createDataFrameInternal` in `processDataFrame.ts`.

## Problem
1. The function `createDataFrame` is renamed to `createDataFrameInternal`, but the changes may not be reflected in all dependent files.
2. The renaming might affect external modules or scripts that rely on the original function name if it was part of the public API.

## Evidence
- `packages/grafana-data/src/dataframe/processDataFrame.ts:590`: Function name changed from `createDataFrame` to `createDataFrameInternal`.
- `packages/grafana-data/src/dataframe/utils.ts`: Potentially uses the renamed function but not updated in this PR.
- `packages/grafana-data/src/dataframe/MutableDataFrame.ts`: May call the renamed function, requiring updates.
- `packages/grafana-data/src/dataframe/processDataFrame.test.ts`: Tests might need to be updated to reflect the new function name.

## Impact
- The renaming could break functionality in any module or script that imports `createDataFrame` if they are not updated accordingly.
- Potential runtime errors or failures in tests that depend on the original function name.
- If the function is part of a public API, external users may experience breaking changes.

## Recommendation (Fix / Tests / Risks)
1. Ensure all internal references to `createDataFrame` are updated to `createDataFrameInternal` across all dependent files.
2. Verify if `createDataFrame` is part of a public API. If so, consider maintaining backward compatibility or providing a migration path.
3. Update and run all relevant tests to ensure they pass with the new function name.
4. Document the change in the changelog or relevant documentation to inform users of the modification.

## Traceability
- Code Owner: Not specified
```