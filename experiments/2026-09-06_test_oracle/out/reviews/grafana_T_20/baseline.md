```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming conventions in the `types.ts` file of the `grafana-data` package.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` may not be consistent with other naming conventions in the codebase.
2. The change might impact other parts of the codebase that depend on the original class name, potentially leading to integration issues.

## Evidence
- `packages/grafana-data/src/events/types.ts:44`: The class `BusEventWithPayload` was renamed to `BusEventWithPayloadInternal`.

## Impact
- The renaming could cause runtime errors if other modules or components reference the old class name, leading to potential application crashes or malfunction.
- If this class is part of a public API or used across different packages, it could break backward compatibility, affecting users relying on the previous naming.

## Recommendation (Fix / Tests / Risks)
1. Conduct a thorough search across the codebase to identify all references to `BusEventWithPayload` and update them to the new name.
2. Ensure that any public documentation or API references are updated to reflect the new class name.
3. Add tests to verify that the renamed class does not introduce any integration issues, especially if it is used in multiple modules.

## Traceability
Not specified
```