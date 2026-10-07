```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming in the types file by renaming a class.

## Problem
1. The renaming of the class from `BusEventWithPayload` to `BusEventWithPayloadInternal` might break existing references if not all usages are updated.
2. The change does not appear to include updates to documentation or comments that might reference the old class name.

## Evidence
- `packages/grafana-data/src/events/types.ts:44`: The class `BusEventWithPayload` is renamed to `BusEventWithPayloadInternal`.

## Impact
- The renaming could lead to runtime errors or broken functionality if there are existing references to `BusEventWithPayload` elsewhere in the codebase that are not updated.
- Lack of updated documentation or comments can lead to confusion for developers who are familiar with the old class name.

## Recommendation (Fix / Tests / Risks)
1. Conduct a thorough search across the codebase to ensure all references to `BusEventWithPayload` are updated to `BusEventWithPayloadInternal`.
2. Update any documentation or inline comments that reference `BusEventWithPayload` to reflect the new name.
3. Consider adding tests to verify that the refactoring does not introduce any regressions, particularly if this class is widely used.

## Traceability
Not specified
```