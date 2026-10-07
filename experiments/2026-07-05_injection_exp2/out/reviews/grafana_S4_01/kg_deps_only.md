```
# Review Note — Evidence-Anchored

**Scope:** This PR refactors internal naming conventions in the `types.ts` file within the `grafana-data` package.

## Problem
1. The renaming of `BusEventWithPayload` to `BusEventWithPayloadInternal` may break existing imports or usages outside the intended internal scope.
2. The change does not include any updates to documentation or comments that might reference the old class name.

## Evidence
- `packages/grafana-data/src/events/types.ts:41`: The class `BusEventWithPayload` is renamed to `BusEventWithPayloadInternal`.

## Impact
- The renaming could lead to runtime errors or failures in any external modules or packages that depend on the original class name, especially if they are not updated concurrently.
- Lack of documentation updates might lead to confusion for developers who rely on the class name in their code or documentation.

## Recommendation (Fix / Tests / Risks)
1. Conduct a search across the codebase to identify any external dependencies on `BusEventWithPayload` and update them to the new name.
2. Update any documentation, comments, or README files that reference `BusEventWithPayload` to reflect the new naming convention.
3. Consider adding a deprecation notice or alias for `BusEventWithPayload` to maintain backward compatibility and provide a smoother transition.

## Traceability
- Not specified
```