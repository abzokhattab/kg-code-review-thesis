```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming conventions in the `types.ts` file of the `grafana-data` package.

## Problem
1. Inconsistent naming conventions with existing codebase patterns.
2. Potential confusion due to the introduction of "Internal" suffix without clear documentation or usage context.

## Evidence
- `packages/grafana-data/src/events/types.ts:41`: The class `BusEventWithPayload` was renamed to `BusEventWithPayloadInternal`.
- Similar classes in `packages/grafana-data/src/events/EventBus.ts` do not use the "Internal" suffix, e.g., `EventBusSrv` (lines 1-72).

## Impact
- **Technical Impact:** The introduction of an "Internal" suffix may lead to confusion among developers regarding the intended usage of the class. It is unclear if this class should be used differently than other event-related classes without the suffix.
- **Risk:** Misalignment with existing naming conventions could lead to inconsistencies in the codebase, making it harder to maintain and understand.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Align the naming convention with existing patterns unless there is a specific reason for the "Internal" suffix. If the suffix is necessary, provide documentation explaining its purpose and intended use.
2. **Tests:** Ensure that any changes in class names are reflected in related test cases to prevent any breakage.
3. **Risks:** Consider the potential for increased cognitive load on developers due to inconsistent naming conventions, and address this through documentation or training if necessary.

## Traceability
Not specified
```