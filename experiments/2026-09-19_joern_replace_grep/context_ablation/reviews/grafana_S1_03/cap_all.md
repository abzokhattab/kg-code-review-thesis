```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the function name `createDataFrame` to `createDataFrameInternal` in the `processDataFrame.ts` file.

## Problem
1. The function `createDataFrameInternal` is still being used externally, which contradicts the implication of it being an internal function.
2. The renaming may break existing code that relies on the original function name `createDataFrame`.

## Evidence
- **packages/grafana-data/src/dataframe/processDataFrame.ts:591**: The function `createDataFrame` is renamed to `createDataFrameInternal`.
- **packages/grafana-data/src/field/fieldOverrides.ts**: The lambda function still calls `createDataFrame`, which may lead to runtime errors if not updated.
- **packages/grafana-data/src/dataframe/utils.test.ts**: Tests are likely to fail if they rely on the old function name.

## Impact
- **Technical Impact:** The renaming can lead to runtime errors in any code that imports `createDataFrame` by its old name. This could break functionality in dependent modules and tests.
- **Risk:** The change introduces a risk of breaking changes in any module that uses this function. It may also cause confusion about the function's intended scope and usage.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Update all references to `createDataFrame` in dependent files to use the new name `createDataFrameInternal`.
2. **Tests:** Ensure all test cases in files like `utils.test.ts` and `processDataFrame.test.ts` are updated to reflect the name change and pass successfully.
3. **Risks:** Consider whether the function should indeed be internal. If it is meant to be used externally, reconsider the naming to avoid confusion.

## Traceability
- **Code Owners:** Not specified
```