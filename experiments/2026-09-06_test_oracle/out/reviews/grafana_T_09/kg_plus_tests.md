```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of a function in the valueFormats module.

## Problem
1. The renaming of `formattedValueToString` to `formattedValueToStringInternal` may impact external modules or scripts that rely on this function.
2. The function is used in other files, but it is unclear if all dependencies have been updated to reflect the new name.

## Evidence
- `packages/grafana-data/src/valueFormats/valueFormats.ts:16`: The function `formattedValueToString` is renamed to `formattedValueToStringInternal`.
- `packages/grafana-data/src/field/getFieldDisplayValuesProxy.ts`: This file imports `formattedValueToString`, but the import statement is not updated to reflect the new function name.
- `packages/grafana-data/src/utils/csv.ts`: This file also imports `formattedValueToString`, but the import statement is not updated to reflect the new function name.

## Impact
- If the function name is not updated in all dependent files, it could lead to runtime errors where the function is called but not found, breaking functionality where this function is used.
- The risk of missing updates in dependent files increases maintenance overhead and potential bugs in production.

## Recommendation (Fix / Tests / Risks)
1. Update all import statements in dependent files (`getFieldDisplayValuesProxy.ts`, `csv.ts`) to use the new function name `formattedValueToStringInternal`.
2. Run all related tests (`valueFormats.test.ts`, `arithmeticFormatters.test.ts`, `dateTimeFormatters.test.ts`) to ensure that the changes do not break existing functionality.
3. Consider adding a deprecation warning for the old function name if it was previously part of a public API, to inform users of the change.

## Traceability
- Code Owners: Not specified
```