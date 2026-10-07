```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming within the types file of the Grafana data package.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` might break dependencies in other files that import this class.
2. There is no evidence of updated import statements in dependent files, which could lead to runtime errors.

## Evidence
- `packages/grafana-data/src/events/types.ts:41`: The class `BusEventWithPayload` is renamed to `BusEventWithPayloadInternal`.
- Dependent files: `packages/grafana-data/src/events/common.ts`, `packages/grafana-data/src/types/legacyEvents.ts`, `packages/grafana-data/src/types/logs.ts` are not updated in this PR.

## Impact
- The renaming could lead to import errors in files that depend on the original class name, causing runtime failures.
- Without updating the dependent files, the application may not compile, or it might throw errors when attempting to use the renamed class.

## Recommendation (Fix / Tests / Risks)
1. Update all import statements in the dependent files to use the new class name `BusEventWithPayloadInternal`.
2. Run the existing test suite to ensure that no tests fail due to the renaming.
3. Consider adding a test case specifically for the instantiation and usage of `BusEventWithPayloadInternal` to ensure it behaves as expected.

## Traceability
- Code ownership: Not specified
```