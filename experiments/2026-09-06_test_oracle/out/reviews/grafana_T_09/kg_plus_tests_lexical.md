```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors the `formattedValueToString` function by renaming it to `formattedValueToStringInternal`.

## Problem
1. The renaming of `formattedValueToString` to `formattedValueToStringInternal` may break external dependencies if this function is used outside its intended internal scope.
2. Lack of clarity on whether the function is adequately covered by tests after the renaming, potentially leading to undetected issues.

## Evidence
- `packages/grafana-data/src/valueFormats/valueFormats.ts:16`: The function `formattedValueToString` is renamed to `formattedValueToStringInternal`.
- `packages/grafana-data/src/field/getFieldDisplayValuesProxy.ts`: This file depends on the changed function, which may lead to integration issues if the function is used externally.
- `packages/grafana-data/src/utils/csv.ts`: Another dependent file that could be affected by the renaming.

## Impact
- The renaming could lead to runtime errors or broken functionality in parts of the application that rely on the original function name if they are not updated accordingly.
- If the function is used outside of its intended internal scope, it could cause unexpected behavior in other modules or third-party integrations.

## Recommendation (Fix / Tests / Risks)
1. Verify and update all internal and external references to `formattedValueToString` to ensure they point to `formattedValueToStringInternal`.
2. Ensure that the related test file `packages/grafana-data/src/valueFormats/valueFormats.test.ts` covers the renamed function adequately.
3. Consider adding documentation or comments to clarify the intended internal use of `formattedValueToStringInternal` to prevent misuse.

## Traceability
- Code Owners: Not specified
```