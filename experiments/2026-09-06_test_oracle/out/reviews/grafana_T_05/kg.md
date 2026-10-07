```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of the `getFieldDisplayName` function to `getFieldDisplayNameInternal` in `fieldState.ts`.

## Problem
1. The renaming of the function may break dependencies in other files that rely on the original function name.
2. There is no evidence of updated tests or documentation reflecting the name change, which could lead to confusion or errors in future maintenance.

## Evidence
- `packages/grafana-data/src/field/fieldState.ts:106`: The function `getFieldDisplayName` is renamed to `getFieldDisplayNameInternal`.
- Multiple files depend on this function, such as:
  - `packages/grafana-data/src/dataframe/processDataFrame.ts`
  - `packages/grafana-data/src/field/fieldDisplay.ts`
  - `packages/grafana-data/src/transformations/matchers/nameMatcher.ts`
  - `packages/grafana-data/src/transformations/transformers/calculateField.ts`
  - `packages/grafana-data/src/transformations/transformers/filterByValue.ts`
  - `packages/grafana-data/src/transformations/transformers/groupBy.ts`
  - `packages/grafana-data/src/transformations/transformers/groupToNestedTable.ts`
  - `packages/grafana-data/src/transformations/transformers/labelsToFields.ts`
  - `packages/grafana-data/src/transformations/transformers/order.ts`
  - `packages/grafana-data/src/transformations/transformers/reduce.ts`
  - `packages/grafana-data/src/transformations/transformers/rename.ts`
  - `packages/grafana-data/src/transformations/transformers/renameByRegex.ts`
  - `packages/grafana-data/src/transformations/transformers/sortBy.ts`
  - `packages/grafana-data/src/utils/csv.ts`

## Impact
- The renaming could lead to runtime errors if the function is called by its old name in any of the dependent files. This can cause failures in data processing or transformations that rely on this function.
- Lack of updated tests or documentation increases the risk of misunderstandings and bugs in future development efforts.

## Recommendation (Fix / Tests / Risks)
1. Ensure all dependent files are updated to use the new function name `getFieldDisplayNameInternal`.
2. Update any relevant test cases to reflect the function name change and verify that all tests pass.
3. Update documentation to reflect the new function name to prevent confusion for future developers.

## Traceability
Not specified
```