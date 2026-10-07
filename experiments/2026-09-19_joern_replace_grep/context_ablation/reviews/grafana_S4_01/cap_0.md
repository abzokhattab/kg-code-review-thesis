```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming conventions in the types for events.

## Problem
1. The renaming of the class `BusEventWithPayload` to `BusEventWithPayloadInternal` may not align with the intended usage or visibility scope.
2. The change might affect other parts of the codebase that rely on the original class name, potentially causing integration issues.

## Evidence
- `packages/grafana-data/src/events/types.ts:41`: The class `BusEventWithPayload` is renamed to `BusEventWithPayloadInternal`.

## Impact
- The renaming could lead to broken imports or references in other parts of the codebase if they are not updated accordingly. This can cause runtime errors or failures during compilation.
- If the class is part of a public API or used externally, changing its name could break backward compatibility for users relying on the previous name.

## Recommendation (Fix / Tests / Risks)
1. Conduct a thorough search across the codebase to identify and update all references to `BusEventWithPayload` to ensure consistency and prevent integration issues.
2. If the class is part of a public API, consider maintaining the original name or providing a deprecation path to avoid breaking changes for external users.
3. Add or update tests to verify that the renaming does not introduce any regressions or integration issues.

## Traceability
Not specified
```