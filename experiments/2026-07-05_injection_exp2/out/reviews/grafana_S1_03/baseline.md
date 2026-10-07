```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming within the `processDataFrame` function by renaming the `createDataFrame` function to `createDataFrameInternal`.

## Problem
1. The renaming of the function to `createDataFrameInternal` suggests it is intended for internal use, but there is no indication of access control or documentation to enforce or communicate this.
2. The change might affect other parts of the codebase that rely on the `createDataFrame` function, potentially leading to integration issues if not all usages are updated.

## Evidence
- `packages/grafana-data/src/dataframe/processDataFrame.ts:593`: The function `createDataFrame` is renamed to `createDataFrameInternal`.

## Impact
- Without proper documentation or access control, other developers might mistakenly use `createDataFrameInternal` as a public API, leading to potential misuse or reliance on an internal function.
- If the function is used elsewhere in the codebase, failing to update all references could result in runtime errors or broken functionality.

## Recommendation (Fix / Tests / Risks)
1. Add documentation to clarify the intended internal use of `createDataFrameInternal` and consider using TypeScript's `private` keyword or similar patterns if applicable.
2. Conduct a thorough search across the codebase to ensure all references to `createDataFrame` are updated to `createDataFrameInternal`.
3. Implement unit tests to verify that the refactored function behaves as expected and does not introduce regressions.

## Traceability
Not specified
```