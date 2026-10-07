```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming conventions in the types file for event handling.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` may break external dependencies if this class is used outside the intended internal scope.
2. Lack of test updates or additions to ensure that the renaming does not affect functionality or external integrations.

## Evidence
- `packages/grafana-data/src/events/types.ts:41`: The class `BusEventWithPayload` is renamed to `BusEventWithPayloadInternal`.
- Dependency files: `packages/grafana-data/src/events/common.ts`, `packages/grafana-data/src/types/legacyEvents.ts`, `packages/grafana-data/src/types/logs.ts` may rely on the original class name.

## Impact
- The renaming could lead to runtime errors if external modules or plugins rely on the original class name, potentially causing failures in event handling.
- Without corresponding test updates, there is a risk that the change could introduce unnoticed bugs or regressions in the system.

## Recommendation (Fix / Tests / Risks)
1. Conduct a thorough search for any external usage of `BusEventWithPayload` to ensure that the renaming does not break any dependencies.
2. Update existing tests or add new tests to cover the renamed class to ensure that functionality remains intact.
3. Consider adding a deprecation notice or alias for `BusEventWithPayload` if it is widely used externally, to provide a smoother transition.

## Traceability
- Code Ownership: Not specified
```