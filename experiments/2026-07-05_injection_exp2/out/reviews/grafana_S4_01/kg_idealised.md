```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming within the types file, specifically renaming the `BusEventWithPayload` class to `BusEventWithPayloadInternal`.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` could break dependencies if external modules rely on the original class name.
2. There is a risk of insufficient test coverage to ensure that the renaming does not affect existing functionality.

## Evidence
- `packages/grafana-data/src/events/EventBus.test.ts` calls `types.BusEventWithPayload`, which may not reflect the updated class name.
- `packages/grafana-data/src/events/common.ts` imports `types.BusEventWithPayload`, potentially leading to import errors.
- `packages/grafana-data/src/types/legacyEvents.ts` and `packages/grafana-data/src/types/logs.ts` also depend on `types.BusEventWithPayload`.

## Impact
- Technical impact includes potential runtime errors or failing imports in modules that have not been updated to use the new class name.
- There is a risk of breaking changes if the class is used externally and the renaming is not communicated or documented properly.

## Recommendation (Fix / Tests / Risks)
1. Ensure all dependent files are updated to use the new class name `BusEventWithPayloadInternal`.
2. Add or update tests in `packages/grafana-data/src/events/EventBus.test.ts` to verify that the refactor does not introduce regressions.
3. Document the change in any relevant documentation or changelogs to inform other developers of the renaming.

## Traceability
- Code ownership or relevant teams: Not specified
```