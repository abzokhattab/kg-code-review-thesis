```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming within the `types.ts` file by renaming `BusEventWithPayload` to `BusEventWithPayloadInternal`.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` may affect external dependencies if this class is used outside the intended internal scope.
2. The change lacks corresponding updates in documentation or comments that explain the rationale behind the renaming, which could lead to confusion for future maintainers.

## Evidence
- `packages/grafana-data/src/events/types.ts:41`: The class `BusEventWithPayload` is renamed to `BusEventWithPayloadInternal`.

## Impact
- **Technical Impact:** If `BusEventWithPayload` is used in external modules or by third-party plugins, this change could break those integrations unless they are updated simultaneously. The lack of documentation updates may lead to misunderstandings about the intended use of the class.
- **Risk:** There is a risk of runtime errors if external code attempts to instantiate or extend the renamed class without being updated.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Conduct a thorough search to ensure that `BusEventWithPayload` is not used externally. If it is, coordinate with those dependencies to update their references.
2. **Documentation:** Update the documentation to reflect the change and provide context for why the renaming was necessary.
3. **Testing:** Ensure that all unit and integration tests that involve `BusEventWithPayload` are updated to use the new class name and verify that they pass successfully.

## Traceability
Not specified
```