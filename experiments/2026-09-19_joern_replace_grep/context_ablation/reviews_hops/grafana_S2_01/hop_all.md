```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `toDataFrame` function to include a `RequiredContext` parameter for future feature enhancements.

## Problem
1. The addition of the `RequiredContext` parameter to `toDataFrame` may break existing calls that do not provide this new parameter.
2. There is a lack of updated test coverage to validate the changes in `toDataFrame` with the new parameter.
3. The introduction of `RequiredContext` could cause integration issues with dependent files that have not been updated to accommodate this change.

## Evidence
- **processDataFrame.ts:305** - The function signature of `toDataFrame` has been modified to include `requiredCtx: RequiredContext`.
- **processDataFrame.test.ts** - No new tests have been added to cover the changes made to `toDataFrame`.
- **utils.ts, MutableDataFrame.ts, StreamingDataFrame.ts, ArrayDataFrame.ts** - These files depend on `toDataFrame` but have not been updated to reflect the new parameter.

## Impact
- **Technical Impact:** Existing code that calls `toDataFrame` without the `RequiredContext` parameter will fail, potentially leading to runtime errors.
- **Risk:** Without updated tests, there is a risk that the new functionality could introduce bugs or regressions in the system.

## Recommendation (Fix / Tests / Risks)
1. Update all calls to `toDataFrame` across the codebase to include the `RequiredContext` parameter.
2. Add new test cases in `processDataFrame.test.ts` to ensure the `toDataFrame` function behaves correctly with the `RequiredContext` parameter.
3. Review and update any dependent files or modules to handle the new parameter, ensuring backward compatibility where possible.

## Traceability
- Code Owners: Not specified
```