```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming within the types file for events in the Grafana data package.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` might break existing imports if not all references are updated.
2. Lack of test coverage for the renamed class could lead to undetected issues in dependent modules.

## Evidence
- `packages/grafana-data/src/events/types.ts:42`: The class `BusEventWithPayload` is renamed to `BusEventWithPayloadInternal`.

## Impact
- The renaming could cause runtime errors in any module that imports `BusEventWithPayload` if those imports are not updated accordingly. This can lead to failures in event handling where this class is used.
- Without adequate test coverage, any issues arising from this change might not be caught until runtime, increasing the risk of bugs in production.

## Recommendation (Fix / Tests / Risks)
1. Conduct a thorough search for all imports of `BusEventWithPayload` across the codebase and update them to `BusEventWithPayloadInternal`.
2. Add or update existing tests to ensure that the functionality of `BusEventWithPayloadInternal` is verified, especially focusing on modules that depend on this class.
3. Consider adding a deprecation warning for `BusEventWithPayload` if it is still used externally, to inform developers of the change.

## Traceability
- Code ownership: Grafana Data Team (assumed based on file path)
```