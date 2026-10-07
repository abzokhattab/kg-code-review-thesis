```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of the `createDataFrame` function to `createDataFrameInternal`.

## Problem
1. Inconsistent naming conventions may lead to confusion, as the function name `createDataFrameInternal` suggests internal use, but it is not clear if this is enforced or documented.
2. Potential breaking changes due to renaming, as the function is used across multiple files and tests.

## Evidence
- `packages/grafana-data/src/dataframe/processDataFrame.ts:593`: The function `createDataFrame` is renamed to `createDataFrameInternal`.
- `packages/grafana-data/src/dataframe/utils.test.ts`: This test file depends on the `createDataFrame` function.
- `packages/grafana-data/src/dataframe/frameComparisons.test.ts`: Another test file that relies on the `createDataFrame` function.
- `packages/grafana-data/src/dataframe/processDataFrame.test.ts:1-79`: Tests import and use the `createDataFrame` function.

## Impact
- The renaming could introduce breaking changes if external modules or projects rely on the original `createDataFrame` function name.
- Inconsistent naming might lead to confusion about the intended use of the function, especially if it is meant to be private but is not encapsulated or documented as such.

## Recommendation (Fix / Tests / Risks)
1. Ensure that all references to `createDataFrame` are updated to `createDataFrameInternal` across the codebase, including documentation and tests.
2. Consider adding documentation or comments to clarify the intended use and scope of `createDataFrameInternal`, specifying if it is meant for internal use only.
3. Verify that all dependent tests pass and consider adding a test to ensure that the function behaves as expected with the new name.

## Traceability
Not specified
```