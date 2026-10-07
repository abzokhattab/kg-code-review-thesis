```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `toDataFrame` function to include a `RequiredContext` parameter for future feature work.

## Problem
1. The addition of the `RequiredContext` parameter to `toDataFrame` may break existing function calls that do not provide this new argument.
2. There is a lack of updated test coverage to ensure that the refactored `toDataFrame` function behaves correctly with the new parameter.

## Evidence
- `packages/grafana-data/src/dataframe/processDataFrame.ts:305`: The `toDataFrame` function signature has changed, requiring a new `RequiredContext` parameter.
- `packages/grafana-data/src/utils/dataLinks.test.ts`, `packages/grafana-data/src/types/live.test.ts`, `packages/grafana-data/src/text/sanitize.test.ts`, `packages/grafana-data/src/utils/Registry.test.ts`: These test files do not appear to have been updated to account for the new `RequiredContext` parameter in `toDataFrame`.

## Impact
- The change to the function signature could lead to runtime errors in any existing code that calls `toDataFrame` without the new `RequiredContext` parameter, potentially causing application crashes or incorrect data processing.
- Without updated tests, there is a risk that the new functionality introduced by the `RequiredContext` parameter is not properly validated, leading to undetected bugs.

## Recommendation (Fix / Tests / Risks)
1. Review all call sites of `toDataFrame` to ensure they are updated to pass the `RequiredContext` parameter.
2. Update existing test cases or add new ones to cover scenarios involving the `RequiredContext` parameter, ensuring that the function behaves as expected.
3. Consider implementing backward compatibility or default values for the `RequiredContext` parameter to minimize integration risks.

## Traceability
- Not specified
```