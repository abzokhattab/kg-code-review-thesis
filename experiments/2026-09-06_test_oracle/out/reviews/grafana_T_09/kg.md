```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the internal naming of a function in the valueFormats module.

## Problem
1. The function `formattedValueToStringInternal` is still being used externally, which contradicts the intention of marking it as internal.
2. The change may affect dependent files that rely on the original function name, potentially causing runtime errors or unexpected behavior.

## Evidence
- `packages/grafana-data/src/valueFormats/valueFormats.ts:16`: The function `formattedValueToString` is renamed to `formattedValueToStringInternal`.
- `packages/grafana-data/src/field/getFieldDisplayValuesProxy.ts`: This file imports and uses the `formattedValueToString` function.
- `packages/grafana-data/src/utils/csv.ts`: This file also imports and uses the `formattedValueToString` function.

## Impact
- Renaming the function without updating its usage in dependent files can lead to `undefined` errors at runtime.
- Any external module or script that relies on this function will break, potentially causing data display issues or crashes in the application.

## Recommendation (Fix / Tests / Risks)
1. Update all references to `formattedValueToString` in dependent files to use the new name `formattedValueToStringInternal`.
2. Ensure that the function is truly intended for internal use only. If it is used externally, consider reverting the name change or providing a public-facing alias.
3. Add unit tests to verify that the function works as expected in all contexts where it is used.

## Traceability
- Code Owners: Not specified
```