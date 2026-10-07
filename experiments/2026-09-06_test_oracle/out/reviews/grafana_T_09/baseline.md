```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming within the valueFormats module by renaming a function.

## Problem
1. The renaming of the function to `formattedValueToStringInternal` might impact other modules or components that rely on the previous function name.
2. There is no evidence of updated documentation or comments reflecting the change in function name.

## Evidence
- `packages/grafana-data/src/valueFormats/valueFormats.ts:16`: The function `formattedValueToString` is renamed to `formattedValueToStringInternal`.

## Impact
- The renaming could lead to runtime errors if other parts of the codebase are still calling the function using its old name, potentially breaking functionality.
- Lack of documentation updates may lead to confusion for future developers who are unaware of the internal nature of the function.

## Recommendation (Fix / Tests / Risks)
1. Conduct a search across the codebase to ensure that all references to `formattedValueToString` are updated to `formattedValueToStringInternal`.
2. Update any relevant documentation or comments to reflect the change in function name and clarify its intended internal use.
3. Consider adding unit tests to ensure that the function behaves as expected with the new name, especially if its usage context has changed.

## Traceability
Not specified
```