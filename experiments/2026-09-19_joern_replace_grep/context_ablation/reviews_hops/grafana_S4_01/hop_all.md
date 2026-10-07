```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming within the types file of the Grafana data package.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` may affect external code that relies on this class.
2. Lack of corresponding updates in documentation or comments that explain the rationale behind the renaming.

## Evidence
- `packages/grafana-data/src/events/types.ts:43`: The class `BusEventWithPayload` has been renamed to `BusEventWithPayloadInternal`.

## Impact
- The renaming could break any external dependencies or integrations that expect the original class name, leading to runtime errors or failures in dependent systems.
- Without updated documentation, developers may be confused about the purpose of the renaming and whether it impacts the public API.

## Recommendation (Fix / Tests / Risks)
1. Verify if `BusEventWithPayload` is used externally and ensure that all references are updated accordingly.
2. Update documentation to reflect the change in naming and clarify the intended scope of `BusEventWithPayloadInternal`.
3. Consider adding a deprecation warning for `BusEventWithPayload` if it is part of the public API, providing a transition period for external users.

## Traceability
- Code ownership is likely with the Grafana data team, but specific owners are not specified.
```