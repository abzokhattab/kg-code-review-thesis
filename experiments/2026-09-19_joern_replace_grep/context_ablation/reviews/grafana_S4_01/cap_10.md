```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming conventions in the types file of the Grafana data package.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` could affect external dependencies if not properly encapsulated.
2. Lack of corresponding updates in documentation or comments that might reference the old class name.

## Evidence
- `packages/grafana-data/src/events/types.ts:41`: The class `BusEventWithPayload` is renamed to `BusEventWithPayloadInternal`.

## Impact
- The renaming might break any external modules or plugins that rely on the previous class name if it was exposed beyond internal use. This could lead to runtime errors or failures in dependent systems.
- If the class is part of a public API, consumers of the API might face integration issues due to the change in the class name.

## Recommendation (Fix / Tests / Risks)
1. Verify that `BusEventWithPayload` is not exposed in any public API or used in external modules. If it is, consider maintaining backward compatibility or updating all dependent modules.
2. Update any relevant documentation or inline comments to reflect the new class name to prevent confusion.
3. Ensure that existing tests cover the renamed class and add new tests if necessary to validate the changes.

## Traceability
- Code ownership: Not specified
```