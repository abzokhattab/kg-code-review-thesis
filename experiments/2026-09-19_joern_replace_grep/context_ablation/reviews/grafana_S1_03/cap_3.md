```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of the `createDataFrame` function to `createDataFrameInternal`.

## Problem
1. The renaming of `createDataFrame` to `createDataFrameInternal` may break existing dependencies that rely on the original function name.
2. There is no evidence of updated test cases or documentation reflecting the change in function name.
3. Potential lack of backward compatibility considerations for external modules or scripts that might use this function.

## Evidence
- `packages/grafana-data/src/dataframe/processDataFrame.ts:590`: The function `createDataFrame` is renamed to `createDataFrameInternal`.
- `packages/grafana-data/src/field/fieldOverrides.ts::<lambda>3`: This file references the original `createDataFrame` function, which may now be broken due to the rename.

## Impact
- The renaming could lead to runtime errors in any module or script that imports `createDataFrame` by its old name, potentially causing failures in data processing workflows.
- Tests that rely on the original function name may fail, leading to a false sense of security if not updated.
- Documentation or user guides referencing `createDataFrame` will become outdated, confusing users and developers.

## Recommendation (Fix / Tests / Risks)
1. Conduct a thorough search for all instances where `createDataFrame` is used and update them to `createDataFrameInternal`.
2. Update test cases in `packages/grafana-data/src/dataframe/utils.test.ts` and `packages/grafana-data/src/dataframe/frameComparisons.test.ts` to reflect the new function name.
3. Consider adding a deprecation warning for the old function name if backward compatibility is a concern.
4. Update any relevant documentation to ensure consistency with the code changes.

## Traceability
- Code Owner: Not specified
- Affected Teams: Not specified
```