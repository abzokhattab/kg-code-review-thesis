```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming conventions in the types file of the Grafana data package.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` may affect external dependencies if this class is used outside the intended internal scope.
2. Lack of documentation or comments explaining the rationale for the renaming, which may lead to confusion for future maintainers.

## Evidence
- `packages/grafana-data/src/events/types.ts: line 44`: The class name change from `BusEventWithPayload` to `BusEventWithPayloadInternal`.

## Impact
- The renaming could potentially break external code that relies on `BusEventWithPayload` if it is not truly internal, leading to runtime errors or compilation issues.
- Without proper documentation, future developers might not understand the purpose of the change, leading to potential rework or misinterpretation of the code's intent.

## Recommendation (Fix / Tests / Risks)
1. Verify that `BusEventWithPayload` is not used outside the intended internal scope. If it is, consider maintaining backward compatibility or providing a migration path.
2. Add comments or documentation explaining the purpose of the renaming to clarify its intent for future maintainers.
3. Run integration tests to ensure that no external dependencies are broken by this change.

## Traceability
Not specified
```