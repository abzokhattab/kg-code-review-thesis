```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming conventions in the types file of the Grafana data package.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` may affect external modules or tests that rely on the original class name.
2. There is no evidence of corresponding updates in documentation or test cases to reflect this change.

## Evidence
- `packages/grafana-data/src/events/types.ts:44`: The class `BusEventWithPayload` is renamed to `BusEventWithPayloadInternal`.

## Impact
- **Technical Impact:** If external modules or other parts of the codebase rely on the original class name, this change could lead to runtime errors or broken functionality. Additionally, without updating documentation or tests, the change may lead to confusion among developers and potential misuse of the class.

## Recommendation (Fix / Tests / Risks)
1. **Fix:** Ensure that all references to `BusEventWithPayload` are updated across the codebase, including any external modules that might use this class.
2. **Tests:** Verify that existing tests cover the usage of this class and update them to use the new class name. Add new tests if necessary to ensure comprehensive coverage.
3. **Documentation:** Update any relevant documentation to reflect the new class name to prevent confusion and ensure proper usage.

## Traceability
- Code Owner: Grafana Data Team
```