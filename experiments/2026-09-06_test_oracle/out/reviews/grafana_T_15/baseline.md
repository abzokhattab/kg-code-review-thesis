```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming within the DataFrameJSON module.

## Problem
1. The function `dataFrameFromJSONInternal` is now named with "Internal" suffix, which may imply restricted usage, but there is no visibility control or documentation indicating its intended scope.
2. The refactor does not include any updates to documentation or comments that might help other developers understand the reason for the naming change.

## Evidence
- `packages/grafana-data/src/dataframe/DataFrameJSON.ts:166`: The function name change from `dataFrameFromJSON` to `dataFrameFromJSONInternal` without additional context or documentation.

## Impact
- The lack of clarity around the function's intended usage scope could lead to misuse or confusion among developers, potentially causing integration issues if the function is used externally without proper understanding.
- Without documentation, future maintenance may be hindered, as developers may not understand the rationale behind the naming convention.

## Recommendation (Fix / Tests / Risks)
1. Add comments or documentation explaining the purpose of the "Internal" suffix and any intended usage restrictions.
2. Consider adding TypeScript access modifiers (e.g., `private`, `protected`) if the function is intended for limited internal use.
3. Review and update any related documentation or usage examples to reflect the new function name and its intended use.

## Traceability
Not specified
```