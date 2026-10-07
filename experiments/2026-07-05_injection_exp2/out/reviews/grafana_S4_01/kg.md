```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming within the types file of the Grafana data package.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` may affect external code that relies on this class if it is not truly internal.
2. Lack of clarity on whether the change is reflected in all dependent files and if tests cover this modification.

## Evidence
- `packages/grafana-data/src/events/types.ts:43`: The class `BusEventWithPayload` is renamed to `BusEventWithPayloadInternal`.

## Impact
- If `BusEventWithPayload` is used outside of its intended internal scope, renaming it could break external integrations or dependent modules.
- There is a risk of runtime errors if dependent code is not updated to reflect this change, potentially leading to application crashes or incorrect behavior.

## Recommendation (Fix / Tests / Risks)
1. Verify if `BusEventWithPayload` is used outside the internal scope and ensure all references are updated to `BusEventWithPayloadInternal`.
2. Ensure that there are adequate tests covering this class and its usage to catch any integration issues post-refactor.
3. Consider adding documentation or comments to clarify the intended internal use of `BusEventWithPayloadInternal`.

## Traceability
- Not specified
```