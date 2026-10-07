```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming in the types file of the Grafana data package.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` might break existing imports or usage in dependent files.
2. There is no indication of updated test cases to reflect or verify the impact of this renaming.

## Evidence
- `packages/grafana-data/src/events/types.ts:41`: The class `BusEventWithPayload` is renamed to `BusEventWithPayloadInternal`.
- Dependent files: `packages/grafana-data/src/events/common.ts`, `packages/grafana-data/src/types/legacyEvents.ts`, `packages/grafana-data/src/types/logs.ts` may have references to the old class name.
- Related tests: `packages/grafana-data/src/events/EventBus.test.ts` does not show changes to accommodate the renaming.

## Impact
- The renaming could lead to runtime errors if any dependent files still reference the old class name.
- Lack of updated tests could mean that the change is not verified, potentially leading to untested code paths and undetected issues.

## Recommendation (Fix / Tests / Risks)
1. Verify and update all dependent files to use the new class name `BusEventWithPayloadInternal`.
2. Update existing tests or add new tests in `packages/grafana-data/src/events/EventBus.test.ts` to ensure that the renaming does not affect functionality.
3. Consider backward compatibility or provide a migration path if this change affects external usage.

## Traceability
- Code ownership: Not specified
```