```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming conventions within the types used in the event system.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` may break external dependencies if this class is used outside of the intended internal scope.
2. Lack of clarity on whether all dependent files and tests have been updated to reflect the new naming, which could lead to runtime errors or test failures.

## Evidence
- `packages/grafana-data/src/events/types.ts:41`: The class `BusEventWithPayload` is renamed to `BusEventWithPayloadInternal`.
- `packages/grafana-data/src/events/EventBus.test.ts`: This test file depends on the `BusEventWithPayload` class.
- `packages/grafana-data/src/events/common.ts`: This file imports `BusEventWithPayload`.
- `packages/grafana-data/src/types/legacyEvents.ts`: This file imports `BusEventWithPayload`.
- `packages/grafana-data/src/types/logs.ts`: This file imports `BusEventWithPayload`.

## Impact
- If the renamed class is used outside the intended internal scope, it could lead to breaking changes in other parts of the codebase or in external projects that rely on this class.
- Tests and dependent files may fail if they are not updated to reflect the new class name, leading to potential runtime errors and decreased reliability of the event system.

## Recommendation (Fix / Tests / Risks)
1. Verify that all internal and external references to `BusEventWithPayload` have been updated to `BusEventWithPayloadInternal`.
2. Ensure that all test cases in `packages/grafana-data/src/events/EventBus.test.ts` are updated and passing with the new class name.
3. Consider adding documentation or comments to clarify the intended internal use of `BusEventWithPayloadInternal` to prevent misuse.

## Traceability
- Code Owners: Grafana Data Team (assumed based on file path)
```