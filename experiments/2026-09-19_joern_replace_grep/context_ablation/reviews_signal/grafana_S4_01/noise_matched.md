```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming within the types file of the Grafana data package.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` may affect external references if not properly encapsulated.
2. Lack of test coverage to verify that the renaming does not break existing functionality or integrations.

## Evidence
- `packages/grafana-data/src/events/types.ts:44`: The class `BusEventWithPayload` is renamed to `BusEventWithPayloadInternal`.

## Impact
- The renaming could lead to integration issues if other parts of the codebase or external plugins rely on the original class name. This could result in runtime errors or unexpected behavior if not all references are updated.
- Without appropriate test coverage, it is difficult to ensure that the change does not introduce regressions or break existing functionality.

## Recommendation (Fix / Tests / Risks)
1. Conduct a thorough search across the codebase to ensure all references to `BusEventWithPayload` are updated to `BusEventWithPayloadInternal`.
2. Add or update existing tests to cover the renamed class, ensuring that its functionality remains intact and that no external dependencies are broken.
3. Consider adding a deprecation warning for the old class name if it is used externally, to provide a transition period for external users.

## Traceability
- Code ownership: Not specified
```