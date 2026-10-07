```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming within the `processDataFrame` function to improve clarity.

## Problem
1. The renaming of `createDataFrame` to `createDataFrameInternal` may affect external modules or scripts if this function is used outside its intended scope.
2. Lack of comments or documentation updates to reflect the change in function name, which could lead to confusion for future maintainers.

## Evidence
- `packages/grafana-data/src/dataframe/processDataFrame.ts:593`: The function `createDataFrame` is renamed to `createDataFrameInternal`.

## Impact
- If `createDataFrame` is used by other parts of the codebase or by external consumers, this change could break functionality or lead to runtime errors.
- Without updated documentation or comments, developers may not understand the purpose of the renaming, potentially leading to incorrect usage or further refactoring.

## Recommendation (Fix / Tests / Risks)
1. Conduct a search across the codebase to ensure that `createDataFrame` is not used externally or update all references to the new name.
2. Update any relevant documentation or inline comments to reflect the change in the function name.
3. Consider adding a deprecation warning if `createDataFrame` was previously part of the public API, guiding users to the new function name.

## Traceability
Not specified
```