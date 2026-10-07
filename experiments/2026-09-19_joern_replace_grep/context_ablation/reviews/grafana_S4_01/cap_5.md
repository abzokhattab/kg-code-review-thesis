```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming conventions in the types file of the Grafana data package.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` may affect external dependencies if this class is used outside its intended scope.
2. Lack of test coverage to ensure that the renaming does not break any existing functionality or integrations.

## Evidence
- `packages/grafana-data/src/events/types.ts:42`: The class `BusEventWithPayload` is renamed to `BusEventWithPayloadInternal`.

## Impact
- The renaming could potentially break any external code or plugins that rely on the original class name `BusEventWithPayload`. If this class is intended for internal use only, it should be verified that no external dependencies are affected.
- Without adequate test coverage, there is a risk of introducing regressions or integration issues that may not be immediately apparent.

## Recommendation (Fix / Tests / Risks)
1. Verify that `BusEventWithPayload` is not used outside of internal modules or document the change clearly if it is a breaking change.
2. Add or update unit tests to cover the renamed class to ensure that its behavior remains consistent.
3. Consider adding a deprecation warning for the original class name if external use is possible, to give users time to adjust.

## Traceability
- Code ownership: Likely owned by the Grafana data team, but specific owners are not specified.
```