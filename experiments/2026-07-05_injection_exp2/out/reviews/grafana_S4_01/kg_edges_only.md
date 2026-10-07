```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming conventions in the types file of the Grafana data package.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` may affect external dependencies if this class is used outside of its intended internal scope.
2. Lack of clear documentation or comments explaining the rationale behind the renaming, which could lead to confusion for future maintainers.

## Evidence
- `packages/grafana-data/src/events/types.ts:41`: The class `BusEventWithPayload` is renamed to `BusEventWithPayloadInternal`.

## Impact
- If `BusEventWithPayload` is used in external packages or by other teams, this change could break their code, leading to runtime errors or compilation issues.
- Without proper documentation, the intent behind the change is unclear, which could lead to further misnaming or misuse in future updates.

## Recommendation (Fix / Tests / Risks)
1. Verify that `BusEventWithPayload` is not used externally or update all external references to use the new name.
2. Add comments or documentation explaining the purpose of the renaming to guide future developers.
3. Consider adding a deprecation warning for the old name if it is used externally, to provide a smoother transition.

## Traceability
- Code ownership: Not specified
```